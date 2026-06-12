#!/bin/bash
# TemizIST — Raspberry Pi kurulum (Debian / Raspberry Pi OS)
set -u

echo "=== TemizIST Pi kurulumu ==="

sudo apt-get update

# libatlas-base-dev Trixie'de yok; libopenblas-dev yeterli (opencv için)
sudo apt-get install -y \
  python3-pip \
  python3-venv \
  python3-dev \
  python3-rpi.gpio \
  i2c-tools \
  libopenblas-dev \
  libjpeg62-turbo-dev \
  zlib1g-dev \
  || echo "Uyari: bazi apt paketleri atlandi, pip ile devam..."

cd "$(dirname "$0")"

if [ ! -d venv ]; then
  python3 -m venv venv
fi

# shellcheck disable=SC1091
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements-pi.txt

if ! python3 -c "import hx711" 2>/dev/null; then
  echo "hx711 tekrar deneniyor..."
  pip install hx711 || pip install 'git+https://github.com/tatobari/hx711py.git'
fi

if ! python3 -c "from adafruit_servokit import ServoKit" 2>/dev/null; then
  echo "ServoKit tekrar deneniyor..."
  pip install adafruit-circuitpython-servokit
fi

# I2C (PCA9685)
if ! grep -q "^dtparam=i2c_arm=on" /boot/firmware/config.txt 2>/dev/null; then
  if ! grep -q "^dtparam=i2c_arm=on" /boot/config.txt 2>/dev/null; then
    echo "I2C: sudo raspi-config -> Interface Options -> I2C -> Enable"
  fi
fi

sudo usermod -a -G gpio,i2c,spi "$USER" 2>/dev/null || true

echo ""
echo "=== Kurulum bitti ==="
python3 -c "import RPi.GPIO; import hx711; from adafruit_servokit import ServoKit; print('OK: GPIO, HX711, ServoKit')" \
  || echo "Uyari: bazi moduller eksik — yukaridaki pip hatalarina bakin"
echo ""
echo "Calistirma:"
echo "  cd $(pwd) && source venv/bin/activate && python3 main.py"
