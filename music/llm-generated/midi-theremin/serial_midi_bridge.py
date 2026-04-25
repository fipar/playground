#!/usr/bin/env python3
"""
serial_midi_bridge.py — Hairless MIDI replacement for Apple Silicon Macs.

Reads raw MIDI bytes from the Arduino over USB serial and forwards them
to a virtual MIDI port (IAC Driver Bus 1 on macOS).

Usage:
    python3 serial_midi_bridge.py [serial_port]

    serial_port — optional, e.g. /dev/cu.usbmodem11101
                  auto-detected when only one usbmodem/usbserial port is present

Requirements:
    pip install pyserial python-rtmidi
"""

import sys
import serial
import serial.tools.list_ports
import rtmidi

BAUD_RATE = 115200


def pick_serial_port():
    if len(sys.argv) > 1:
        return sys.argv[1]
    candidates = [
        p.device
        for p in serial.tools.list_ports.comports()
        if "usbmodem" in p.device or "usbserial" in p.device
    ]
    if len(candidates) == 1:
        return candidates[0]
    if candidates:
        print("Multiple serial ports found:")
        for i, p in enumerate(candidates):
            print(f"  [{i}] {p}")
        return candidates[int(input("Select index: "))]
    raise SystemExit(
        "No Arduino serial port found. Plug in the Uno and retry,\n"
        "or pass the port explicitly: python3 serial_midi_bridge.py /dev/cu.usbmodemXXXX"
    )


def pick_midi_port(midi_out):
    ports = midi_out.get_ports()
    if not ports:
        raise SystemExit(
            "No MIDI output ports found.\n"
            "Enable IAC Driver:\n"
            "  Audio MIDI Setup → Window → Show MIDI Studio\n"
            "  → double-click IAC Driver → check 'Device is online'"
        )
    # Prefer IAC Driver automatically
    for i, name in enumerate(ports):
        if "IAC" in name:
            return i
    print("MIDI output ports (no IAC port found automatically):")
    for i, name in enumerate(ports):
        print(f"  [{i}] {name}")
    return int(input("Select index: "))


def msg_len(status):
    """Total byte count (including status byte) for a MIDI status byte."""
    t = status & 0xF0
    if t in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
        return 3   # Note Off/On, AfterTouch, CC, Pitch Bend
    if t in (0xC0, 0xD0):
        return 2   # Program Change, Channel Pressure
    if status == 0xF2:
        return 3   # Song Position Pointer
    if status in (0xF1, 0xF3):
        return 2   # MTC / Song Select
    return 1       # realtime bytes (clock, start, stop …)


def run():
    serial_port = pick_serial_port()

    midi_out = rtmidi.MidiOut()
    midi_idx = pick_midi_port(midi_out)
    midi_out.open_port(midi_idx)

    print(f"Serial : {serial_port} @ {BAUD_RATE} baud")
    print(f"MIDI   : {midi_out.get_ports()[midi_idx]}")
    print("Bridging… Ctrl-C to quit.\n")

    buf = []
    expected = 0
    last_status = 0

    with serial.Serial(serial_port, BAUD_RATE, timeout=1) as ser:
        while True:
            data = ser.read(1)
            if not data:
                continue
            b = data[0]

            if b & 0x80:          # status byte — start a new message
                last_status = b
                expected = msg_len(b)
                buf = [b]
            else:                  # data byte
                if not buf:        # running status (Arduino doesn't use it, but handle anyway)
                    buf = [last_status]
                buf.append(b)

            if buf and expected and len(buf) == expected:
                midi_out.send_message(buf)
                buf = []


if __name__ == "__main__":
    run()
