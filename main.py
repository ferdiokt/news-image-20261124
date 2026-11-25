"""Write the committed day-sheet image to $MAKEFUN_OUTPUT_DIR/entry.png (offline, stdlib only).

entry.png is drawn by render.py from the ledger in SOURCES.md and committed; this program only
checks it against the contest's gate and copies the exact bytes, so both runs write the same file.
"""
import os
import struct
from pathlib import Path

MAX_BYTES = 1048576   # gate: at most 1 MiB
MAX_SIDE = 1024       # gate: at most 1024 x 1024
SIG = b"\x89PNG\r\n\x1a\n"


def checked_png(path):
    data = path.read_bytes()
    if len(data) > MAX_BYTES:
        raise SystemExit(f"{path.name}: {len(data)} bytes > {MAX_BYTES}")
    if data[:8] != SIG or data[12:16] != b"IHDR":
        raise SystemExit(f"{path.name}: not a PNG")
    width, height = struct.unpack(">II", data[16:24])
    if not (0 < width <= MAX_SIDE and 0 < height <= MAX_SIDE):
        raise SystemExit(f"{path.name}: {width}x{height} exceeds {MAX_SIDE}x{MAX_SIDE}")
    if not data.endswith(b"IEND\xaeB`\x82"):
        raise SystemExit(f"{path.name}: truncated (no IEND chunk)")
    return data


def main():
    data = checked_png(Path(__file__).resolve().parent / "entry.png")
    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "entry.png").write_bytes(data)


if __name__ == "__main__":
    main()
