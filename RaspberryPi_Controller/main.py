"""
TemizIST Pi — QR oturum tipine göre plastik / kağıt senaryoları.

Plastik QR: deliğe şişe → sensör → kamera → FastAPI detect → 360° bant
            → şişe sensöre çok yakın geçince sayaç +1 (POST /api/pi/plastic-passed)

Kağıt QR: hazneye kağıt → sensör → kamera → detect → tartı → kapaklar 90°
          Oturum sonu mobil uygulamadan.
"""

from __future__ import annotations

import json
import logging
import threading
import time
from enum import Enum, auto
from pathlib import Path
from typing import Optional

import requests

from hardware_control import create_hardware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).parent / "config.json"
NGROK_HEADERS = {"ngrok-skip-browser-warning": "true"}


class PlasticPhase(Enum):
    WAIT_PLACED = auto()
    DETECTING = auto()
    BELT_RUNNING = auto()
    WAIT_PASS = auto()
    WAIT_CLEAR = auto()


class PaperPhase(Enum):
    WAIT_PLACED = auto()
    DETECTING = auto()
    LIDS_OPEN = auto()
    WAIT_CLEAR = auto()


def load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def validate_config(cfg: dict) -> None:
    pins = cfg["gpio_pins"]
    pairs = [
        ("trig_plastic", pins["trig_plastic"]),
        ("echo_plastic", pins["echo_plastic"]),
        ("trig_paper", pins.get("trig_paper")),
        ("echo_paper", pins.get("echo_paper")),
        ("hx711_dt", pins["hx711_dt"]),
        ("hx711_sck", pins["hx711_sck"]),
    ]
    used = [p for _, p in pairs if p is not None]
    if len(used) != len(set(used)):
        raise ValueError("GPIO pin çakışması var — config.json kontrol edin")
    qr = cfg.get("qr_codes", {})
    logger.info(
        "Kutu machine_id=%s | QR plastik=%s kağıt=%s",
        cfg["machine_id"],
        qr.get("plastic", "1_plastic"),
        qr.get("paper", "1_paper"),
    )
    logger.info(
        "Plastik sensör GPIO %s/%s | Kağıt sensör GPIO %s/%s",
        pins["trig_plastic"],
        pins["echo_plastic"],
        pins.get("trig_paper"),
        pins.get("echo_paper"),
    )
    alert = cfg.get("reject_alert", {})
    logger.info(
        "Reject uyarı GPIO buzzer=%s led=%s",
        alert.get("buzzer_gpio"),
        alert.get("led_gpio"),
    )
    if cfg.get("use_default_images"):
        logger.info("Mock plastik görsel: %s", cfg.get("default_image_plastic"))


class BackendClient:
    def __init__(self, config: dict) -> None:
        self.base = config["backend_url"].rstrip("/")
        self.machine_id = config["machine_id"]

    def poll_active_session(
        self,
    ) -> tuple[bool, Optional[int], Optional[str], int]:
        url = f"{self.base}/api/pi/active-session/{self.machine_id}"
        try:
            r = requests.get(url, headers=NGROK_HEADERS, timeout=10)
            r.raise_for_status()
            data = r.json()
            if data.get("status") == "active" and data.get("session_id"):
                return (
                    True,
                    int(data["session_id"]),
                    (data.get("waste_type") or "plastic").lower(),
                    int(data.get("plastic_bottle_count") or 0),
                )
            return False, None, None, 0
        except Exception as e:
            logger.warning("Poll failed: %s", e)
            return False, None, None, 0

    def post_detect(self, session_id: int, image_bytes: bytes) -> dict:
        url = f"{self.base}/api/pi/detect"
        r = requests.post(
            url,
            data={"session_id": str(session_id)},
            files={"file": ("capture.jpg", image_bytes, "image/jpeg")},
            headers=NGROK_HEADERS,
            timeout=60,
        )
        if not r.ok:
            logger.error("detect HTTP %s: %s", r.status_code, (r.text or "")[:400])
        r.raise_for_status()
        return r.json()

    def post_plastic_passed(self, session_id: int) -> dict:
        url = f"{self.base}/api/pi/plastic-passed"
        r = requests.post(
            url,
            json={"session_id": session_id},
            headers=NGROK_HEADERS,
            timeout=15,
        )
        r.raise_for_status()
        return r.json()

    def post_paper_passed(self, session_id: int) -> dict:
        url = f"{self.base}/api/pi/paper-passed"
        r = requests.post(
            url,
            json={"session_id": session_id},
            headers=NGROK_HEADERS,
            timeout=15,
        )
        r.raise_for_status()
        return r.json()

    def post_weight(self, session_id: int, weight_grams: float) -> dict:
        url = f"{self.base}/api/pi/weight"
        r = requests.post(
            url,
            json={"session_id": session_id, "weight_grams": weight_grams},
            headers=NGROK_HEADERS,
            timeout=15,
        )
        r.raise_for_status()
        return r.json()


class RecyclingController:
    def __init__(self, config: dict) -> None:
        self.config = config
        self.hw = create_hardware(config)
        self.backend = BackendClient(config)

        self.session_id: Optional[int] = None
        self.session_waste_type: Optional[str] = None
        self.plastic_bottle_count = 0

        self.plastic_phase = PlasticPhase.WAIT_PLACED
        self.paper_phase = PaperPhase.WAIT_PLACED
        self._paper_lids_opened_at: Optional[float] = None

        self.placement_cm = config.get(
            "ultrasonic_placement_threshold_cm",
            config.get("ultrasonic_threshold_cm", 15.0),
        )
        self.pass_cm = config.get("ultrasonic_pass_threshold_cm", 6.0)
        self.stable_n = config.get("ultrasonic_stable_readings", 3)
        self.poll_interval = config["polling_interval_seconds"]

    def _stable_placement(self, side: str) -> bool:
        hits = 0
        for _ in range(self.stable_n):
            if self.hw.object_present(side, self.placement_cm):
                hits += 1
            time.sleep(0.05)
        return hits >= self.stable_n

    def _stable_pass(self, side: str) -> bool:
        hits = 0
        for _ in range(self.stable_n):
            if self.hw.object_passing_close(side, self.pass_cm):
                hits += 1
            time.sleep(0.03)
        return hits >= self.stable_n

    def _stable_clear(self, side: str) -> bool:
        misses = 0
        for _ in range(self.stable_n):
            if not self.hw.object_present(side, self.placement_cm):
                misses += 1
            time.sleep(0.05)
        return misses >= self.stable_n

    def _paper_ultrasonic_enabled(self) -> bool:
        pins = self.config["gpio_pins"]
        return pins.get("trig_paper") is not None and pins.get("echo_paper") is not None

    def on_session_start(self, waste_type: str, bottle_count: int) -> None:
        self.session_waste_type = waste_type
        self.plastic_bottle_count = bottle_count
        self.plastic_phase = PlasticPhase.WAIT_PLACED
        self.paper_phase = PaperPhase.WAIT_PLACED
        self._paper_lids_opened_at = None
        extra = f" (şişe sayısı: {bottle_count})" if waste_type == "plastic" else ""
        logger.info(
            "Session %s — tip: %s%s",
            self.session_id,
            waste_type,
            extra,
        )

    def on_session_end(self) -> None:
        if self.session_waste_type == "paper":
            closed = self.config["paper_servo_closed_angle"]
            opened = self.config["paper_servo_open_angle"]
            try:
                self.hw.set_paper_lids(False, closed, opened)
            except Exception:
                pass
        logger.info("Session bitti — idle")
        self.session_id = None
        self.session_waste_type = None
        self.plastic_phase = PlasticPhase.WAIT_PLACED
        self.paper_phase = PaperPhase.WAIT_PLACED
        self._paper_lids_opened_at = None

    def _should_reject_alert(self, resp: dict, expected_waste: str) -> bool:
        status = (resp.get("status") or "").lower()
        if status == "reject":
            return True
        if expected_waste == "plastic" and status != "plastic":
            return True
        if expected_waste == "paper" and status != "paper":
            return True
        return False

    def _capture_and_detect(self, side: str) -> Optional[dict]:
        if not self.session_id:
            return None
        image = self.hw.capture_image(side)
        if not image:
            logger.warning("Görüntü alınamadı: %s", side)
            return None
        try:
            return self.backend.post_detect(self.session_id, image)
        except Exception as e:
            logger.error("detect hatası: %s", e)
            return None

    def tick_plastic(self) -> None:
        if not self.session_id or self.session_waste_type != "plastic":
            return

        if self.plastic_phase == PlasticPhase.WAIT_PLACED:
            if self._stable_placement("plastic"):
                logger.info("Plastik: şişe kondu — kamera + detect")
                self.plastic_phase = PlasticPhase.DETECTING

        elif self.plastic_phase == PlasticPhase.DETECTING:
            resp = self._capture_and_detect("plastic")
            if not resp:
                self.plastic_phase = PlasticPhase.WAIT_CLEAR
                return
            status = (resp.get("status") or "").lower()
            logger.info("Detect: %s — %s", status, resp.get("message"))
            if status == "plastic":
                logger.info("Plastik: AI şişeyi onayladı — sayaç +1")
                try:
                    r = self.backend.post_plastic_passed(self.session_id)
                    self.plastic_bottle_count = int(
                        r.get("plastic_bottle_count") or self.plastic_bottle_count + 1
                    )
                    logger.info(
                        "Session şişe: %d — %s",
                        self.plastic_bottle_count,
                        r.get("message"),
                    )
                except Exception as e:
                    logger.error("plastic-passed hatası: %s", e)
                
                self.plastic_phase = PlasticPhase.BELT_RUNNING
            else:
                logger.info("Plastik değil / red — bant yok")
                if self._should_reject_alert(resp, "plastic"):
                    self.hw.alert_reject()
                self.plastic_phase = PlasticPhase.WAIT_CLEAR

        elif self.plastic_phase == PlasticPhase.BELT_RUNNING:
            sec = self.config["plastic_servo_run_seconds"]
            self.hw.run_plastic_belt(sec)
            logger.info("360° bant bitti — giriş alanının boşalması bekleniyor")
            self.plastic_phase = PlasticPhase.WAIT_CLEAR

        elif self.plastic_phase == PlasticPhase.WAIT_CLEAR:
            if self._stable_clear("plastic"):
                self.plastic_phase = PlasticPhase.WAIT_PLACED

    def tick_paper(self) -> None:
        if not self.session_id or self.session_waste_type != "paper":
            return
        if not self._paper_ultrasonic_enabled():
            return

        closed = self.config["paper_servo_closed_angle"]
        opened = self.config["paper_servo_open_angle"]
        min_g = self.config["min_weight_grams"]

        if self.paper_phase == PaperPhase.WAIT_PLACED:
            if self._stable_placement("paper"):
                logger.info("Kağıt: atık kondu — kamera + detect")
                self.paper_phase = PaperPhase.DETECTING

        elif self.paper_phase == PaperPhase.DETECTING:
            logger.info("Kağıt tespiti için 3 saniye bekleniyor...")
            time.sleep(3)
            resp = self._capture_and_detect("paper")
            if not resp:
                self.paper_phase = PaperPhase.WAIT_CLEAR
                return
            status = (resp.get("status") or "").lower()
            logger.info("Detect: %s — %s", status, resp.get("message"))
            if status == "paper":
                logger.info("Kağıt atıldı, parça başı puan işleniyor ve kapaklar açılıyor...")
                try:
                    wr = self.backend.post_paper_passed(self.session_id)
                    logger.info("Puan: %s", wr.get("message"))
                except Exception as e:
                    logger.error("paper-passed POST: %s", e)
                
                self.hw.set_paper_lids(True, closed, opened)
                self._paper_lids_opened_at = time.time()
                stay = self.config.get("paper_lid_stay_open_seconds", 15)
                logger.info("Kapaklar AÇILDI (Servo A:%s, B:%s) — %d sn sonra kapanacak", opened, 180-opened, stay)
                self.paper_phase = PaperPhase.LIDS_OPEN
            else:
                logger.info("Kağıt değil / red")
                if self._should_reject_alert(resp, "paper"):
                    self.hw.alert_reject()
                self.paper_phase = PaperPhase.WAIT_CLEAR

        elif self.paper_phase == PaperPhase.LIDS_OPEN:
            stay = float(self.config.get("paper_lid_stay_open_seconds", 15))
            if (
                self._paper_lids_opened_at is not None
                and (time.time() - self._paper_lids_opened_at) >= stay
            ):
                self.hw.set_paper_lids(False, closed, opened)
                self._paper_lids_opened_at = None
                logger.info("Kapaklar KAPANDI (Servo A:%s, B:%s) — sensör boşalınca yeni atık beklenir", closed, 180-closed)
                self.paper_phase = PaperPhase.WAIT_CLEAR

        elif self.paper_phase == PaperPhase.WAIT_CLEAR:
            if self._stable_clear("paper"):
                self.paper_phase = PaperPhase.WAIT_PLACED

    def sensor_loop(self) -> None:
        while True:
            if self.session_id:
                self.tick_plastic()
                self.tick_paper()
            time.sleep(0.15)

    def poll_loop(self) -> None:
        while True:
            active, sid, waste, count = self.backend.poll_active_session()
            if active and sid:
                if self.session_id != sid:
                    self.session_id = sid
                    self.on_session_start(waste or "plastic", count)
                else:
                    self.plastic_bottle_count = count
            elif self.session_id is not None:
                self.on_session_end()
            time.sleep(self.poll_interval)

    def run(self) -> None:
        threading.Thread(target=self.sensor_loop, daemon=True).start()
        self.poll_loop()

    def cleanup(self) -> None:
        self.hw.cleanup()


def main() -> None:
    config = load_config()
    validate_config(config)
    logger.info("Backend poll: %s", config["backend_url"])
    ctrl = RecyclingController(config)
    try:
        ctrl.run()
    except KeyboardInterrupt:
        logger.info("Durduruldu")
    finally:
        ctrl.cleanup()


if __name__ == "__main__":
    main()
