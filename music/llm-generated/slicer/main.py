#!/usr/bin/env python3
"""slice2xrni — slice an audio file into a Renoise .xrni instrument.

Usage examples:
    python main.py loop.wav
    python main.py loop.wav --output my_instrument.xrni
    python main.py loop.wav --min 2 --max 4
    python main.py loop.wav --glitchy --min 50 --max 200
"""

import argparse
import sys
from pathlib import Path

import audio
import onsets
import xrni_builder


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="slice2xrni",
        description="Slice an audio file into a pop-free Renoise .xrni instrument.",
    )
    parser.add_argument("input_file", help="Audio file to slice (WAV, FLAC, MP3, AIFF, ...)")
    parser.add_argument(
        "--output", "-o",
        help="Output .xrni path (default: <input_stem>.xrni in the current directory)",
    )
    parser.add_argument(
        "--min", type=float, dest="min_val", metavar="N",
        help=(
            "Minimum slice size in onset intervals (default mode) "
            "or milliseconds (--glitchy mode)."
        ),
    )
    parser.add_argument(
        "--max", type=float, dest="max_val", metavar="N",
        help=(
            "Maximum slice size in onset intervals (default mode) "
            "or milliseconds (--glitchy mode)."
        ),
    )
    parser.add_argument(
        "--glitchy", action="store_true",
        help=(
            "Generate time-based slices ignoring waveform transitions. "
            "--min and --max are interpreted as milliseconds. "
            "Boundaries are NOT snapped to zero-crossings (clicks are intentional)."
        ),
    )
    parser.add_argument(
        "--bpm", type=int, default=120,
        help="BPM stored in instrument metadata (default: 120).",
    )
    parser.add_argument(
        "--zero-crossing-window", type=float, default=12.0, metavar="MS",
        dest="zc_window",
        help="Search window in ms for zero-crossing snapping (default: 12 ms).",
    )
    parser.add_argument(
        "--name",
        help="Instrument name (default: derived from input filename).",
    )

    args = parser.parse_args(argv)

    # Validate
    if args.glitchy:
        if args.min_val is not None and args.min_val <= 0:
            parser.error("--min must be a positive number of milliseconds in --glitchy mode.")
        if args.max_val is not None and args.max_val <= 0:
            parser.error("--max must be a positive number of milliseconds in --glitchy mode.")

    if args.min_val is not None and args.max_val is not None:
        if args.min_val > args.max_val:
            parser.error("--min must not be greater than --max.")

    if not args.glitchy:
        if args.min_val is not None and args.min_val < 1:
            parser.error("--min must be >= 1 in normal mode (it represents onset intervals).")
        if args.max_val is not None and args.max_val < 1:
            parser.error("--max must be >= 1 in normal mode.")

    return args


def main(argv=None):
    args = parse_args(argv)

    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    instrument_name = args.name or input_path.stem

    output_path = args.output or str(input_path.with_suffix(".xrni").name)
    if not output_path.endswith(".xrni"):
        output_path += ".xrni"

    # ---- Load audio ----
    print(f"Loading {input_path} ...")
    data, sr = audio.load(str(input_path))
    mono = audio.to_mono(data)
    total_samples = len(mono)
    duration_s = total_samples / sr
    print(f"  {sr} Hz, {data.shape[1] if data.ndim > 1 else 1} ch, "
          f"{total_samples} samples ({duration_s:.2f} s)")

    # ---- Detect / generate slice markers ----
    min_intervals = int(args.min_val) if (args.min_val is not None and not args.glitchy) else None
    max_intervals = int(args.max_val) if (args.max_val is not None and not args.glitchy) else None

    print("Detecting slice markers ...")
    markers = onsets.detect(
        mono=mono,
        sr=sr,
        min_intervals=min_intervals,
        max_intervals=max_intervals,
        glitchy=args.glitchy,
        min_ms=args.min_val if args.glitchy else None,
        max_ms=args.max_val if args.glitchy else None,
        zero_crossing_window_ms=args.zc_window,
    )

    if not markers:
        print("Warning: no slice markers found; the output will be a single-sample instrument.")
    else:
        print(f"  {len(markers)} slice marker(s) → {len(markers) + 1} slice(s)")

    # ---- Build .xrni ----
    print(f"Writing {output_path} ...")
    xrni_builder.build(
        output_path=output_path,
        audio_data=data,
        sr=sr,
        markers=markers,
        instrument_name=instrument_name,
        bpm=args.bpm,
    )
    print("Done.")


if __name__ == "__main__":
    main()
