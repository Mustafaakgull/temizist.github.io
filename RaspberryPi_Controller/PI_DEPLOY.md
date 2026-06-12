# Pi kurulum — Windows PowerShell

| | |
|--|--|
| Pi IP | `192.168.1.194` |
| Kullanıcı | `temizist` |
| Hedef klasör | `/home/temizist/TemizIST/RaspberryPi_Controller` |

---

## 0) OpenSSH (bir kez)

PowerShell **Yönetici**:

```powershell
Get-WindowsCapability -Online | Where-Object Name -like 'OpenSSH.Client*'
Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0
```

`ssh` ve `scp` tanınmıyorsa bunu kurun.

---

## 1) Pi erişilebilir mi?

```powershell
Test-NetConnection 192.168.1.194 -Port 22
```

`TcpTestSucceeded : True` olmalı (Pi açık, aynı Wi‑Fi).

---

## 2) SSH ile bağlan

```powershell
ssh temizist@192.168.1.194
```

İlk sefer: `Are you sure...` → `yes` → şifre.

Pi’de klasör (bir kez):

```bash
mkdir -p /home/temizist/TemizIST
exit
```

---

## 3) Klasörü PC’den Pi’ye at (`scp`)

PowerShell’de (SSH kapalı veya **ikinci pencere**):

```powershell
scp -r "c:\Users\gokha\Masaüstü\Graduation Project\RaspberryPi_Controller" temizist@192.168.1.194:/home/temizist/TemizIST/
```

Şifre sorulur → `temizist` kullanıcı şifresi.

**Tek komut script:**

```powershell
cd "c:\Users\gokha\Masaüstü\Graduation Project\RaspberryPi_Controller"
.\deploy-to-pi.ps1
```

---

## 4) Tekrar SSH — kurulum ve çalıştırma

```powershell
ssh temizist@192.168.1.194
```

Pi terminalinde (Linux komutları):

```bash
ls /home/temizist/TemizIST/RaspberryPi_Controller
cd /home/temizist/TemizIST/RaspberryPi_Controller
chmod +x install_pi.sh
./install_pi.sh
source venv/bin/activate
python3 main.py
```

`Ctrl+C` ile durdurursunuz.

---

## 5) Otomatik başlatma (isteğe bağlı)

Pi SSH oturumunda:

```bash
cd /home/temizist/TemizIST/RaspberryPi_Controller
sudo cp temizist-pi.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now temizist-pi
sudo systemctl status temizist-pi
```

---

## Kurulum hatası: `libatlas-base-dev` / `venv` yok

Eski `install_pi.sh` Trixie'de duruyordu. Güncel script'i tekrar atın veya Pi'de:

```bash
cd /home/temizist/TemizIST/RaspberryPi_Controller
chmod +x install_pi.sh
./install_pi.sh
source venv/bin/activate
python3 main.py
```

`hx711 package not installed` → `./install_pi.sh` bitince kaybolmalı.

---

## Sorun giderme (PowerShell)

| Hata | Çözüm |
|------|--------|
| `scp` bulunamadı | OpenSSH Client kur (adım 0) |
| Connection timed out | Pi IP, Wi‑Fi, SSH açık mı |
| Permission denied | Kullanıcı/şifre: `temizist` |
| Host key changed | `ssh-keygen -R 192.168.1.194` |

---

## PC tarafı (Pi testi öncesi)

1. Docker FastAPI + Postgres (`docker compose up -d` — DB port **5433**)
2. `docker compose up -d --build web` (kod değişince)
3. AI `:9000` PC’de çalışsın
4. ngrok → `http://localhost:8000` — URL = `config.json` → `backend_url`
5. Mobil güncel (`waste_type` gönderimi)

## QR test

- `1_plastic` → şişe → bant → geçiş sayacı
- `1_paper` → tartı → kapak 90° → 15 sn → kapanır
- QR yokken sensör → tepki yok

---

## 360° plastik servo dönmüyorsa

Log’da `Plastic 360 belt running` görünüp motor dönmüyorsa yazılım komut veriyor; sorun genelde **güç, kablo veya servo tipi**dir.

### 1) Donanım kontrolü

| Kontrol | Açıklama |
|--------|----------|
| Servo tipi | **Sürekli dönüş (360° CR)** olmalı; normal 180° kapak servosu `throttle` ile dönmez |
| PCA9685 kanal | Plastik sinyal kablosu **kanal 0** (config: `servo_plastic_360`) |
| Güç | Servo **harici 5V** (≥1A); sadece Pi USB/PCA yetmez |
| Toprak | PCA9685 GND ↔ servo GND ↔ Pi GND ortak |
| Sinyal | Turuncu kablo → PCA OUT, kırmızı 5V, kahverengi/siyah GND |

### 2) Pi’de doğrudan test

PC’den güncel dosyaları atın (`hardware_control.py`, `config.json`, `test_plastic_servo.py`), sonra Pi SSH:

```bash
cd /home/temizist/TemizIST/RaspberryPi_Controller
source venv/bin/activate
python3 test_plastic_servo.py
```

Dönmezse darbe genişliğini deneyin:

```bash
python3 test_plastic_servo.py --pulse 1700
python3 test_plastic_servo.py --pulse 1300
python3 test_plastic_servo.py --throttle 0.9
```

### 3) `config.json` ayarları

| Alan | Varsayılan | Anlamı |
|------|------------|--------|
| `plastic_servo_control` | `pulse` | `pulse` = µs PWM (çoğu 360° servo); `throttle` = ServoKit sürekli mod |
| `plastic_servo_pulse_us_stop` | 1500 | Dur |
| `plastic_servo_pulse_us_run` | 1700 | İleri dön (hızlı) |
| `plastic_servo_pulse_us_run_reverse` | 1300 | Geri dön |
| `plastic_servo_direction` | 1 | `-1` → ters yön |
| `plastic_servo_run_throttle` | 0.75 | Sadece `throttle` modunda |

Motor **dönüyor ama durmuyorsa** (sık görülen):

1. Güncel `hardware_control.py` + `config.json` atın (`plastic_servo_stop_cut_pwm: true` → durunca PWM kesilir).
2. Pi’de: `python3 test_plastic_servo.py` — artık durmalı.
3. Hâlâ yavaş dönüyorsa: `python3 test_plastic_servo.py --calibrate` → tam duran µs değerini `plastic_servo_pulse_us_stop` olarak kaydedin.
4. Veya `python3 test_plastic_servo.py --hold-stop` + servodaki **kalibrasyon vidası** (1500µs sinyali varken).

### 4) Güncel kodu Pi’ye atmak (PowerShell, PC)

```powershell
cd "c:\Users\gokha\Masaüstü\Graduation Project\RaspberryPi_Controller"
scp config.json hardware_control.py test_plastic_servo.py temizist@192.168.1.194:/home/temizist/TemizIST/RaspberryPi_Controller/
ssh temizist@192.168.1.194 "sudo systemctl restart temizist-pi"
```
