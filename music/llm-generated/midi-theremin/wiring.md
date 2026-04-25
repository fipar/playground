# Wiring

## HC-SR04 (Ultrasonic — controls pitch)

The sensor has 4 pins labeled on its face:

| HC-SR04 pin | Arduino pin |
|-------------|-------------|
| VCC | 5V |
| GND | GND |
| Trig | D9 |
| Echo | D10 |

## GY-521 / MPU-6050 (Accelerometer — controls velocity)

| GY-521 pin | Arduino pin |
|------------|-------------|
| VCC | 3.3V (not 5V — the chip is 3.3V) |
| GND | GND |
| SDA | A4 |
| SCL | A5 |

## Tips

- **GND is shared** — both sensors' GND pins can go to the same GND rail on the breadboard, then one wire from that rail to any Arduino GND pin.
- **Point the HC-SR04 away from you** — the two silver cylinders (transmitter + receiver) should face the space where your hand will be, 5–60 cm away.
- **Orient the GY-521 flat** for minimum velocity, tilted for maximum. The X-axis (long axis of the board) is what the sketch reads.
