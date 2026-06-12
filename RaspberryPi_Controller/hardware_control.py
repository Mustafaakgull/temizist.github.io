"""
Raspberry Pi donanım kontrolü: PCA9685, ultrasonik, HX711, kamera, buzzer/LED.
Sadece gerçek Pi üzerinde çalışır.
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

_BASE_DIR = Path(__file__).resolve().parent

logger = logging.getLogger(__name__)

try:
    import RPi.GPIO as GPIO

    _HAS_GPIO = True
except ImportError:
    _HAS_GPIO = False

try:
    from adafruit_servokit import ServoKit

    _HAS_SERVOKIT = True
except ImportError:
    _HAS_SERVOKIT = False

try:
    from hx711 import HX711

    _HAS_HX711 = True
except ImportError:
    _HAS_HX711 = False

try:
    import cv2

    _HAS_CV2 = True
except ImportError:
    _HAS_CV2 = False


def _null_pin(pin: Optional[int]) -> bool:
    return pin is None


class HardwareController(ABC):
    @abstractmethod
    def read_distance_cm(self, side: str) -> float:
        pass

    @abstractmethod
    def object_present(self, side: str, threshold_cm: float) -> bool:
        pass

    def object_passing_close(self, side: str, pass_threshold_cm: float) -> bool:
        return self.read_distance_cm(side) < pass_threshold_cm

    @abstractmethod
    def run_plastic_belt(self, seconds: float) -> None:
        pass

    @abstractmethod
    def set_paper_lids(self, open_lids: bool, closed_angle: int, open_angle: int) -> None:
        pass

    @abstractmethod
    def read_weight_grams(self) -> float:
        pass

    @abstractmethod
    def capture_image(self, side: str) -> Optional[bytes]:
        """side: 'plastic' | 'paper'"""
        pass

    @abstractmethod
    def alert_reject(self) -> None:
        """Model reject veya yanlış atık: buzzer + LED."""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        pass


def _reject_alert_config(config: dict) -> dict:
    return config.get("reject_alert") or {}


def _encode_image_file_as_jpeg(path: Path) -> Optional[bytes]:
    if not path.is_file():
        return None
    if _HAS_CV2:
        data = path.read_bytes()
        import numpy as np

        arr = np.frombuffer(data, dtype=np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if frame is not None:
            ok, buf = cv2.imencode(".jpg", frame)
            if ok:
                return buf.tobytes()
    return path.read_bytes()


class PiHardwareController(HardwareController):
    def __init__(self, config: dict) -> None:
        self.config = config
        pins = config["gpio_pins"]
        pca = config["pca_channels"]

        self.trig_plastic = pins["trig_plastic"]
        self.echo_plastic = pins["echo_plastic"]
        self.trig_paper = pins.get("trig_paper")
        self.echo_paper = pins.get("echo_paper")
        self.hx711_dt = pins["hx711_dt"]
        self.hx711_sck = pins["hx711_sck"]

        self.ch_plastic = pca["servo_plastic_360"]
        self.ch_paper_1 = pca["servo_paper_1"]
        self.ch_paper_2 = pca["servo_paper_2"]

        self._paper_has_ultrasonic = not (
            _null_pin(self.trig_paper) or _null_pin(self.echo_paper)
        )

        alert = _reject_alert_config(config)
        self._buzzer_gpio = alert.get("buzzer_gpio")
        self._led_gpio = alert.get("led_gpio")
        self._reject_has_output = not (
            _null_pin(self._buzzer_gpio) and _null_pin(self._led_gpio)
        )

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        GPIO.setup(self.trig_plastic, GPIO.OUT)
        GPIO.setup(self.echo_plastic, GPIO.IN)
        GPIO.output(self.trig_plastic, GPIO.LOW)

        if self._paper_has_ultrasonic:
            GPIO.setup(self.trig_paper, GPIO.OUT)
            GPIO.setup(self.echo_paper, GPIO.IN)
            GPIO.output(self.trig_paper, GPIO.LOW)

        if not _null_pin(self._buzzer_gpio):
            GPIO.setup(self._buzzer_gpio, GPIO.OUT)
            GPIO.output(self._buzzer_gpio, GPIO.LOW)
        if not _null_pin(self._led_gpio):
            GPIO.setup(self._led_gpio, GPIO.OUT)
            GPIO.output(self._led_gpio, GPIO.LOW)

        if not _HAS_SERVOKIT:
            raise RuntimeError("adafruit_servokit required on Pi (pip install adafruit-circuitpython-servokit)")

        self.kit = ServoKit(channels=16, address=config.get("pca9685_address", 0x40))
        self._belt_control = (config.get("plastic_servo_control") or "throttle").lower()
        self._belt_direction = 1 if int(config.get("plastic_servo_direction", 1)) >= 0 else -1
        self._belt_run_throttle = float(config.get("plastic_servo_run_throttle", 0.5))
        stop_us = int(
            config.get("plastic_servo_stop_pulse_us")
            or config.get("plastic_servo_pulse_us_stop", 1650)
        )
        self._pulse_stop_us = stop_us
        if "plastic_servo_stop_throttle" in config:
            self._belt_stop_throttle = float(config["plastic_servo_stop_throttle"])
        else:
            self._belt_stop_throttle = (stop_us - 1500) / 500.0
        self._stop_cut_pwm = bool(config.get("plastic_servo_stop_cut_pwm", False))
        self._cut_pwm_on_exit = bool(config.get("plastic_servo_cut_pwm_on_exit", True))
        self._pulse_run_us = int(config.get("plastic_servo_pulse_us_run", 1700))
        self._pulse_run_rev_us = int(config.get("plastic_servo_pulse_us_run_reverse", 1300))
        self._pulse_min = int(config.get("plastic_servo_pulse_width_min", 1000))
        self._pulse_max = int(config.get("plastic_servo_pulse_width_max", 2000))
        self.kit.servo[self.ch_paper_1].set_pulse_width_range(500, 2500)
        self.kit.servo[self.ch_paper_2].set_pulse_width_range(500, 2500)
        self.kit.servo[self.ch_paper_1].actuation_range = 180
        self.kit.servo[self.ch_paper_2].actuation_range = 180
        self._init_plastic_continuous_servo()
        self._idle_plastic_belt()

        self._hx711: Optional[HX711] = None
        hx711_on = bool(self.config.get("hx711_enabled", True))
        if not hx711_on:
            logger.info("HX711 devre dışı (config: hx711_enabled=false) — plastik testi")
        elif _HAS_HX711:
            self._hx711 = HX711(self.hx711_dt, self.hx711_sck)
            if hasattr(self._hx711, "reset"):
                self._hx711.reset()
            time.sleep(1)
            logger.info("HX711 hazir (Sabit Kalibrasyon: BAZ=-326406, KAL=-82.49)")
        else:
            raise RuntimeError(
                "hx711 kurulu degil: pip install hx711 (venv icinde) veya config hx711_enabled=false"
            )

        self._idle_plastic_belt()
        logger.info(
            "Pi donanimi hazir (360 ch=%s throttle run=%.2f stop=%.2f)",
            self.ch_plastic,
            self._belt_run_throttle,
            self._belt_stop_throttle,
        )

    def _init_plastic_continuous_servo(self) -> None:
        """360° CR servo: set_pulse_width_range(1000,2000) + throttle (Pi testinde çalışan)."""
        ch = self.ch_plastic
        cs = self.kit.continuous_servo[ch]
        if hasattr(cs, "set_pulse_width_range"):
            cs.set_pulse_width_range(self._pulse_min, self._pulse_max)
            logger.info(
                "360 servo ch%s pulse range %s–%s µs",
                ch,
                self._pulse_min,
                self._pulse_max,
            )

    @staticmethod
    def _pulse_us_to_throttle(pulse_us: int) -> float:
        return (int(pulse_us) - 1500) / 500.0

    def _pulse_us_to_duty(self, pulse_us: int) -> int:
        """PCA9685 @ 50 Hz: darbe genişliği (µs) → duty_cycle (0–65535)."""
        pulse_us = max(1000, min(2000, int(pulse_us)))
        return int(65535 * pulse_us / 20000)

    def _set_plastic_pulse_us(self, pulse_us: int) -> None:
        ch = self.ch_plastic
        duty = self._pulse_us_to_duty(pulse_us)
        self.kit._pca.channels[ch].duty_cycle = duty

    def _cut_plastic_pwm(self) -> None:
        """Kanala sinyal göndermeyi kes (çoğu 360° servo böyle tam durur)."""
        try:
            self.kit._pca.channels[self.ch_plastic].duty_cycle = 0
        except Exception:
            pass

    def _idle_plastic_belt(self) -> None:
        """Boşta: sinyal yok (0.3 vermek bazı servolarda yavaş ters döndürür)."""
        self._cut_plastic_pwm()
        time.sleep(0.03)

    def _stop_plastic_belt(self) -> None:
        """360° bant: nötr darbe, gerekirse PWM kes."""
        ch = self.ch_plastic
        if self._belt_control == "pulse":
            self._set_plastic_pulse_us(self._pulse_stop_us)
            time.sleep(0.12)
            if self._stop_cut_pwm:
                self._cut_plastic_pwm()
        else:
            try:
                self.kit.continuous_servo[ch].throttle = max(
                    -1.0, min(1.0, self._belt_stop_throttle)
                )
            except Exception:
                pass
            time.sleep(0.12)
            if self._stop_cut_pwm:
                self._cut_plastic_pwm()
        time.sleep(0.05)

    def _shutdown_plastic_belt(self) -> None:
        """Program kapanırken: doğrudan PWM kes (0.3 önce verilirse ters yarım tur olabilir)."""
        if not self._cut_pwm_on_exit:
            self._stop_plastic_belt()
            return
        try:
            self._cut_plastic_pwm()
            logger.debug("360 servo shutdown: PWM kesildi (ch=%s)", self.ch_plastic)
        except Exception as e:
            logger.debug("360 servo shutdown: %s", e)

    def _measure_once(self, trig: int, echo: int) -> float:
        GPIO.output(trig, GPIO.HIGH)
        time.sleep(0.00001)
        GPIO.output(trig, GPIO.LOW)

        pulse_start = pulse_end = None
        timeout = time.time() + 0.04
        while GPIO.input(echo) == 0:
            pulse_start = time.time()
            if time.time() > timeout:
                return 999.0
        while GPIO.input(echo) == 1:
            pulse_end = time.time()
            if time.time() > timeout:
                return 999.0

        if pulse_start is None or pulse_end is None:
            return 999.0
        duration = pulse_end - pulse_start
        return (duration * 34300) / 2

    def read_distance_cm(self, side: str) -> float:
        if side == "plastic":
            return self._measure_once(self.trig_plastic, self.echo_plastic)
        if side == "paper" and self._paper_has_ultrasonic:
            return self._measure_once(self.trig_paper, self.echo_paper)
        return 999.0

    def object_present(self, side: str, threshold_cm: float) -> bool:
        d = self.read_distance_cm(side)
        return d < threshold_cm

    def run_plastic_belt(self, seconds: float) -> None:
        run_us = (
            self._pulse_run_us
            if self._belt_direction >= 0
            else self._pulse_run_rev_us
        )
        run_throttle = max(-1.0, min(1.0, self._belt_run_throttle * self._belt_direction))
        logger.info(
            "Plastic 360 belt %.1fs (mode=%s, ch=%s, run_throttle=%.2f, stop_throttle=%.2f)",
            seconds,
            self._belt_control,
            self.ch_plastic,
            run_throttle,
            self._belt_stop_throttle,
        )
        ch = self.ch_plastic
        try:
            if self._belt_control == "pulse":
                self._set_plastic_pulse_us(run_us)
            else:
                # Boştan doğrudan çalışma hızına (ara dur 0.3 ters çevirmesin)
                self.kit.continuous_servo[ch].throttle = run_throttle
            time.sleep(seconds)
        finally:
            # 0.3 bazı servolarda yavaş geri döndürür; boşta PWM kes
            self._idle_plastic_belt()
            logger.info("Plastic 360 belt stopped (idle PWM off)")

    def set_paper_lids(self, open_lids: bool, closed_angle: int, open_angle: int) -> None:
        angle1 = open_angle if open_lids else closed_angle
        # İkinci servo, birinci servonun tersi (simetrik) açıda çalışacak
        angle2 = 180 - angle1
        self.kit.servo[self.ch_paper_1].angle = angle1
        self.kit.servo[self.ch_paper_2].angle = angle2
        delay = self.config.get("paper_servo_move_seconds", 1.5)
        time.sleep(delay)

    def read_weight_grams(self) -> float:
        if not self._hx711:
            raise RuntimeError(
                "HX711 yok — tartı bağlayın ve config.json hx711_enabled=true yapın"
            )
        okuma = self._hx711.get_raw_data(times=15)
        if okuma:
            ortalama = sum(okuma) / len(okuma)
            BAZ = -326406
            KALIBRASYON = -82.49
            gram = (ortalama - BAZ) / KALIBRASYON
            logger.info("HX711 Debug: Ham=%s, Ort=%.1f, BAZ=%s, KAL=%s -> %.2f gram", okuma, ortalama, BAZ, KALIBRASYON, gram)
            return max(0.0, float(gram))
        logger.warning("HX711 Debug: okuma basarisiz (okuma bos geldi)")
        return 0.0

    def _default_image_path(self, side: str) -> Optional[Path]:
        key = f"default_image_{side}"
        rel = self.config.get(key)
        if not rel:
            return None
        return _BASE_DIR / str(rel)

    def _load_mock_image(self, side: str) -> Optional[bytes]:
        path = self._default_image_path(side)
        if not path:
            return None
        data = _encode_image_file_as_jpeg(path)
        if data:
            logger.info("Mock görsel kullanılıyor (%s): %s", side, path.name)
        return data

    def _capture_from_camera(self, side: str) -> Optional[bytes]:
        if not _HAS_CV2:
            return None
        cam_key = "camera_plastic" if side == "plastic" else "camera_paper"
        camera_path = self.config.get(cam_key, "/dev/video0")
        cap = cv2.VideoCapture(camera_path, cv2.CAP_V4L2)
        if not cap.isOpened():
            cap.release()
            return None
        ret, frame = cap.read()
        cap.release()
        if not ret:
            return None
        ok, buf = cv2.imencode(".jpg", frame)
        return buf.tobytes() if ok else None

    def capture_image(self, side: str) -> Optional[bytes]:
        if self.config.get("use_default_images", False):
            mock = self._load_mock_image(side)
            if mock:
                return mock

        image = self._capture_from_camera(side)
        if image:
            return image

        mock = self._load_mock_image(side)
        if mock:
            return mock

        logger.warning("Görüntü yok (%s): kamera ve mock dosya bulunamadı", side)
        return None

    def alert_reject(self) -> None:
        if not self._reject_has_output:
            logger.debug("Reject alert: buzzer/LED pinleri tanımlı değil")
            return
        alert = _reject_alert_config(self.config)
        duration = float(alert.get("alert_seconds", 2.0))
        beeps = int(alert.get("buzzer_beep_count", 3))
        on_ms = int(alert.get("buzzer_beep_on_ms", 200)) / 1000.0
        off_ms = int(alert.get("buzzer_beep_off_ms", 150)) / 1000.0

        logger.info("Reject uyarısı: buzzer=%s led=%s", self._buzzer_gpio, self._led_gpio)
        end = time.time() + duration
        if not _null_pin(self._led_gpio):
            GPIO.output(self._led_gpio, GPIO.HIGH)
        try:
            while time.time() < end:
                if not _null_pin(self._buzzer_gpio):
                    for _ in range(beeps):
                        if time.time() >= end:
                            break
                        GPIO.output(self._buzzer_gpio, GPIO.HIGH)
                        time.sleep(on_ms)
                        GPIO.output(self._buzzer_gpio, GPIO.LOW)
                        time.sleep(off_ms)
                else:
                    time.sleep(0.1)
        finally:
            if not _null_pin(self._buzzer_gpio):
                GPIO.output(self._buzzer_gpio, GPIO.LOW)
            if not _null_pin(self._led_gpio):
                GPIO.output(self._led_gpio, GPIO.LOW)

    def cleanup(self) -> None:
        try:
            self._shutdown_plastic_belt()
        except Exception:
            pass
        if not _null_pin(self._buzzer_gpio):
            GPIO.output(self._buzzer_gpio, GPIO.LOW)
        if not _null_pin(self._led_gpio):
            GPIO.output(self._led_gpio, GPIO.LOW)
        GPIO.cleanup()


def create_hardware(config: dict) -> PiHardwareController:
    if not _HAS_GPIO:
        raise RuntimeError(
            "RPi.GPIO bulunamadi. Bu yazilim yalnizca Raspberry Pi uzerinde calisir."
        )
    if not _HAS_SERVOKIT:
        raise RuntimeError(
            "adafruit_servokit kurulu degil: pip install adafruit-circuitpython-servokit"
        )
    return PiHardwareController(config)
