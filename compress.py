"""
compress.py — Payload compression & framing for SwarSetu

This is the piece that actually makes "low bitrate" work: instead of sending
raw audio (64-256 kbps for basic speech codecs), we send compressed TEXT,
which for a typical spoken sentence is a few hundred bits — several orders
of magnitude smaller.

Pipeline: UTF-8 text -> zlib (DEFLATE) -> base85 (safe for text-mode radio
links) -> length-prefixed frame with a language tag, so the receiver knows
which TTS voice/language to synthesize with.

For a real ISRO-grade link you'd replace zlib with something tuned to short
Indic-language utterances (e.g. a small learned entropy coder / arithmetic
coder trained on transcript statistics) — zlib is a solid, dependency-free
baseline for the hackathon prototype.
"""

import base64
import struct
import zlib

FRAME_MAGIC = b"SWST"   # 4-byte magic so the receiver can sanity-check frames


def compress_text(text: str, language: str = "hi") -> bytes:
    """Compress `text` (in `language`) into a compact binary frame."""
    raw = text.encode("utf-8")
    compressed = zlib.compress(raw, level=9)
    lang_bytes = language.encode("ascii")[:8].ljust(8, b"\x00")

    frame = (
        FRAME_MAGIC
        + lang_bytes
        + struct.pack(">H", len(compressed))  # 2-byte length prefix
        + compressed
    )
    return frame


def decompress_frame(frame: bytes) -> dict:
    """Reverse of compress_text. Returns {"text": str, "language": str}."""
    if frame[:4] != FRAME_MAGIC:
        raise ValueError("Not a valid SwarSetu frame (bad magic bytes)")

    lang_bytes = frame[4:12]
    language = lang_bytes.rstrip(b"\x00").decode("ascii")

    (payload_len,) = struct.unpack(">H", frame[12:14])
    compressed = frame[14:14 + payload_len]
    text = zlib.decompress(compressed).decode("utf-8")
    return {"text": text, "language": language}


def to_wire_format(frame: bytes) -> str:
    """Encode a binary frame as base85 text — safe for text-only radio channels."""
    return base64.b85encode(frame).decode("ascii")


def from_wire_format(wire_str: str) -> bytes:
    return base64.b85decode(wire_str.encode("ascii"))


def bits_required(frame: bytes) -> int:
    """How many bits this frame needs — the number you'd compare against link bitrate."""
    return len(frame) * 8


if __name__ == "__main__":
    sample = "आज मौसम बहुत अच्छा है और बारिश होने की संभावना है"
    frame = compress_text(sample, language="hi")
    wire = to_wire_format(frame)

    print(f"Original text bytes : {len(sample.encode('utf-8'))}")
    print(f"Compressed frame     : {len(frame)} bytes ({bits_required(frame)} bits)")
    print(f"Wire (base85)        : {wire}")

    recovered = decompress_frame(from_wire_format(wire))
    print(f"Recovered            : {recovered}")
    assert recovered["text"] == sample
    print("Round-trip OK ✅")
