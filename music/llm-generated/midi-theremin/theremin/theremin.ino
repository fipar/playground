/*
 * theremin.ino
 *
 * Theremin-style MIDI controller:
 *   - HC-SR04 distance  → continuous pitch via note + pitch bend
 *   - GY-521 (MPU-6050) → note velocity (tilt more = louder)
 *
 * Pitch works by mapping distance to a floating-point MIDI note number,
 * then splitting it into the nearest semitone (note on/off) and the
 * fractional offset (pitch bend). This gives smooth, continuous glide
 * across the full chromatic range — no scale quantisation.
 *
 * IMPORTANT: set your synth's pitch bend range to match BEND_RANGE
 * (default 2 semitones). In Logic: open the instrument, find Pitch Bend
 * Range and set it to 2.
 *
 * Wiring:
 *   HC-SR04  Trig → D9,  Echo → D10,  VCC → 5V,   GND → GND
 *   GY-521   SDA  → A4,  SCL  → A5,   VCC → 3.3V, GND → GND
 *
 * Use with serial_midi_bridge.py at 115200 baud.
 */

#include <Wire.h>

// --- HC-SR04 ---
#define TRIG_PIN      9
#define ECHO_PIN      10
#define MIN_DIST      5      // cm — closer than this = silence
#define MAX_DIST      60     // cm — farther than this  = silence
#define ECHO_TIMEOUT  30000UL

// --- MPU-6050 ---
#define MPU_ADDR      0x68
#define ACCEL_XOUT_H  0x3B

// --- MIDI ---
#define MIDI_CHANNEL  1
#define LOW_NOTE      48     // C3  — closest hand position
#define HIGH_NOTE     72     // C5  — farthest hand position
#define BEND_RANGE    2      // semitones — must match synth pitch bend range setting
#define MIN_VELOCITY  30

// ---- MIDI helpers -------------------------------------------------------

void midiNoteOn(byte note, byte velocity) {
  Serial.write(0x90 | (MIDI_CHANNEL - 1));
  Serial.write(note & 0x7F);
  Serial.write(velocity & 0x7F);
}

void midiNoteOff(byte note) {
  Serial.write(0x80 | (MIDI_CHANNEL - 1));
  Serial.write(note & 0x7F);
  Serial.write(0x00);
}

// value: 0..16383, centre = 8192 (no bend)
void midiPitchBend(int value) {
  value = constrain(value, 0, 16383);
  Serial.write(0xE0 | (MIDI_CHANNEL - 1));
  Serial.write(value & 0x7F);         // LSB
  Serial.write((value >> 7) & 0x7F);  // MSB
}

// ---- Sensor helpers -----------------------------------------------------

int readDistance() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  unsigned long duration = pulseIn(ECHO_PIN, HIGH, ECHO_TIMEOUT);
  if (duration == 0) return 0;
  return (int)(duration / 58UL);
}

int16_t mpuRead16(byte reg) {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(reg);
  Wire.endTransmission(false);
  Wire.requestFrom((uint8_t)MPU_ADDR, (uint8_t)2, (uint8_t)true);
  return ((int16_t)Wire.read() << 8) | Wire.read();
}

// ---- Setup --------------------------------------------------------------

void setup() {
  Serial.begin(115200);

  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

  Wire.begin();
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x6B);  // PWR_MGMT_1
  Wire.write(0x00);  // wake up
  Wire.endTransmission(true);
}

// ---- State --------------------------------------------------------------

byte activeNote  = 0;
bool playingNote = false;

// ---- Main loop ----------------------------------------------------------

void loop() {
  // --- Accelerometer → velocity ---
  int16_t ax = mpuRead16(ACCEL_XOUT_H);
  byte velocity = (byte)map(constrain(abs((int)ax), 0, 16384), 0, 16384, MIN_VELOCITY, 127);

  // --- Distance → continuous pitch ---
  int dist = readDistance();
  bool inRange = (dist >= MIN_DIST && dist <= MAX_DIST);

  if (inRange) {
    // Continuous MIDI note number (e.g. 60.7 = between C4 and C#4)
    float pitch = (float)(dist - MIN_DIST) / (float)(MAX_DIST - MIN_DIST)
                  * (HIGH_NOTE - LOW_NOTE) + LOW_NOTE;

    // Nearest semitone and fractional offset (-0.5 .. +0.5 semitones)
    byte  targetNote = (byte)constrain((int)round(pitch), LOW_NOTE, HIGH_NOTE);
    float offset     = pitch - (float)targetNote;   // semitones

    // Pitch bend: centre=8192, ±8191 = ±BEND_RANGE semitones
    int bend = 8192 + (int)(offset / (float)BEND_RANGE * 8191.0f);
    midiPitchBend(bend);

    if (!playingNote) {
      midiNoteOn(targetNote, velocity);
      activeNote  = targetNote;
      playingNote = true;
    } else if (targetNote != activeNote) {
      // Legato: new note-on before note-off to avoid gaps
      midiNoteOn(targetNote, velocity);
      midiNoteOff(activeNote);
      activeNote = targetNote;
    }
  } else {
    if (playingNote) {
      midiPitchBend(8192);  // reset bend to centre before releasing
      midiNoteOff(activeNote);
      playingNote = false;
    }
  }

  delay(20);  // ~50 Hz
}
