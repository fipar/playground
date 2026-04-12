"""Build a .xrni file from audio data and slice markers."""

import os
import zipfile
import tempfile
from pathlib import Path
from dataclasses import dataclass

import numpy as np
import soundfile as sf
from jinja2 import Environment, FileSystemLoader

# Maximum number of slices Renoise can hold in a single instrument.
# Master is at note 36; slices start at 37 and the highest MIDI note is 119.
MAX_SLICES = 119 - 37 + 1  # = 83


@dataclass
class SliceInfo:
    name: str
    note: int
    length: int  # in samples


def build(
    output_path: str,
    audio_data: np.ndarray,
    sr: int,
    markers: list[int],
    instrument_name: str,
    bpm: int = 120,
) -> None:
    """Write a .xrni file to output_path.

    audio_data: (num_samples, num_channels) float32 array
    markers: list of sample positions for slice boundaries (not including 0 or end)
    """
    total_samples = len(audio_data)

    # Cap slices
    if len(markers) > MAX_SLICES:
        print(
            f"Warning: {len(markers)} markers detected; capping at {MAX_SLICES} "
            f"(Renoise limit). Extra markers will be dropped."
        )
        markers = markers[:MAX_SLICES]

    # Build slice descriptors
    # Boundaries: [markers[0], markers[1], ..., markers[-1], total_samples]
    boundaries = markers + [total_samples]
    slices = []
    for i, (start, end) in enumerate(zip(boundaries, boundaries[1:])):
        slices.append(
            SliceInfo(
                name=f"{instrument_name} (S#{i + 1:02d})",
                note=37 + i,
                length=end - start,
            )
        )

    flac_filename = f"Sample00 ({instrument_name}).flac"

    xml = _render_xml(
        name=instrument_name,
        flac_filename=flac_filename,
        total_samples=total_samples,
        markers=markers,
        slices=slices,
        bpm=bpm,
    )

    with tempfile.NamedTemporaryFile(suffix=".flac", delete=False) as tmp:
        tmp_flac = tmp.name

    try:
        sf.write(tmp_flac, audio_data, sr, format="FLAC")

        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("Instrument.xml", xml)
            zf.write(tmp_flac, f"SampleData/{flac_filename}")
    finally:
        os.unlink(tmp_flac)


def _render_xml(
    name: str,
    flac_filename: str,
    total_samples: int,
    markers: list[int],
    slices: list[SliceInfo],
    bpm: int,
) -> str:
    template_dir = Path(__file__).parent / "templates"
    env = Environment(loader=FileSystemLoader(str(template_dir)), trim_blocks=True, lstrip_blocks=True)
    template = env.get_template("instrument.xml.j2")
    return template.render(
        name=name,
        flac_filename=flac_filename,
        total_samples=total_samples,
        markers=markers,
        slices=slices,
        bpm=bpm,
    )
