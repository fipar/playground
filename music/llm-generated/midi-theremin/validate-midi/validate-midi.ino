/*
 * validate-midi.ino
 *
 * Loops a single C2 note (MIDI note 36) on channel 1 at 115200 baud.
 * Use this to confirm the serial → MIDI bridge and DAW routing work
 * before connecting any sensors.
 *
 * Note: Logic Pro labels MIDI note 36 as C1. If you want the note
 * labelled C2 in Logic, change NOTE_C2 to 48.
 */

#define MIDI_CHANNEL  1
#define NOTE_C2       36   // C2 in standard convention (C-1=0, C0=12, C1=24, C2=36)
#define VELOCITY      100
#define NOTE_ON_MS    500
#define NOTE_OFF_MS   500

void setup() {
  Serial.begin(115200);
}

void loop() {
  // Note On
  Serial.write(0x90 | (MIDI_CHANNEL - 1));
  Serial.write(NOTE_C2);
  Serial.write(VELOCITY);
  delay(NOTE_ON_MS);

  // Note Off
  Serial.write(0x80 | (MIDI_CHANNEL - 1));
  Serial.write(NOTE_C2);
  Serial.write(0x00);
  delay(NOTE_OFF_MS);
}
