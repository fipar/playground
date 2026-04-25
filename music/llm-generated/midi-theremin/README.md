# MIDI Theremin

Arduino Uno-based theremin-style MIDI controller. Uses an HC-SR04 ultrasonic
sensor for pitch control and a GY-521 (MPU-6050) for expressive modulation.
MIDI is sent over serial and bridged to a virtual MIDI port on the host computer.

## Branches

- `midi-poc` — Sends a C major diatonic scale in a loop at 120 BPM. Use this
  to confirm that serial MIDI is working before connecting sensors.
- `theremin` — Full controller: distance → note, tilt → modulation (CC1).

## Hardware (both branches)

- Arduino Uno R3
- USB cable to computer

Additional hardware for `theremin` branch:

| Component | Uno Pin |
|-----------|---------|
| HC-SR04 VCC | 5V |
| HC-SR04 GND | GND |
| HC-SR04 Trig | D9 |
| HC-SR04 Echo | D10 |
| GY-521 VCC | 3.3V |
| GY-521 GND | GND |
| GY-521 SDA | A4 |
| GY-521 SCL | A5 |

## Software setup (both branches)

1. Flash the sketch to the Uno via Arduino IDE.
2. Close the Arduino IDE serial monitor (it will conflict with Hairless MIDI).
3. Download [Hairless MIDI](https://projectgus.github.io/hairless-midiserial/).
4. In Hairless MIDI:
   - Serial port: your Arduino's port
   - Baud rate: **115200**
   - MIDI out: **IAC Driver Bus 1** (macOS) or a loopMIDI port (Windows)
5. macOS: IAC Driver is built-in — enable it in
   *Audio MIDI Setup → Window → Show MIDI Studio → IAC Driver → Device is online*.
6. Open your DAW or software synth and select the IAC / loopMIDI port as MIDI input.
