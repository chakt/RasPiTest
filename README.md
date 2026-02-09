# Pi Servo Test (Pan/Tilt) - Raspberry Pi 4 + pigpio + CustomTkinter

## Hardware
- Raspberry Pi 4
- 2x Servo motors (Pan/Tilt)
- External 5V power for servos (recommended 2A)
- IMPORTANT: Common ground between Pi GND and external power GND

Wiring (BCM):
- Pan signal -> GPIO18 (Pin 12)
- Tilt signal -> GPIO19 (Pin 35)
- Servo GND -> Pi GND
- Servo VCC -> external 5V

## Install system deps
sudo apt update
sudo apt install pigpio python3-pigpio
sudo systemctl enable pigpiod
sudo systemctl start pigpiod
systemctl status pigpiod

## Python venv + deps
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt

## Run
python3 main.py

## Keyboard
- Arrow keys / WASD: move pan/tilt
- Space: Home (90,90)
- Esc: Quit

## Safety
- Default safe angles: 20..160 for both axes
- Pulse width is clamped to 700..2300 us
- Adjust safe ranges after calibration (avoid mechanical hard stops).
