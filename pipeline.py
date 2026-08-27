"""
pipeline.py — SwarSetu end-to-end demo

    [Mic audio] --STT--> text --compress--> bits --channel--> bits
        --decompress--> text --TTS--> [Speaker audio]

Run:
    python pipeline.py path/to/input.wav --lang hi --bitrate 300

This wires together every module in the repo and prints stats at each hop
so you can show judges exactly where the bitrate savings come from.
"""

import argparse
import time

from stt import SpeechToText
from compress import compress_text, decompress_frame, to_wire_format, from_wire_format, bits_required
from channel_sim import LowBitrateChannel


def run_pipeline(audio_path: str, language: str | None, bitrate: int,
                  packet_loss: float, synthesize: bool):
    print("=" * 60)
    print("SwarSetu — Voice-over-Low-Bitrate Pipeline")
    print("=" * 60)

    # 1. TRANSMITTER: Speech -> Text
    t0 = time.time()
    stt = SpeechToText()
    result = stt.transcribe(audio_path, language=language)
    stt_time = time.time() - t0

    text = result["text"]
    lang = result["language"]
    print(f"\n[TX] STT ({stt_time:.2f}s) — detected language: {lang}")
    print(f"[TX] Transcript: {text}")

    if not text:
        print("No speech detected — aborting.")
        return

    # 2. TRANSMITTER: Text -> Compressed frame -> Wire format
    frame = compress_text(text, language=lang)
    wire = to_wire_format(frame)
    print(f"\n[TX] Compressed payload: {len(frame)} bytes "
          f"({bits_required(frame)} bits) vs "
          f"{len(text.encode('utf-8'))} raw text bytes")

    # 3. CHANNEL: simulate the actual low-bitrate radio hop
    channel = LowBitrateChannel(bitrate_bps=bitrate, packet_loss=packet_loss)
    stats = channel.send(wire)
    print(f"\n[LINK] {bitrate} bps channel — estimated transmit time: "
          f"{stats['estimated_seconds']:.3f}s "
          f"({stats['n_packets']} packets, {stats['packets_dropped']} dropped)")

    # 4. RECEIVER: Wire format -> decompress -> Text
    try:
        recovered = decompress_frame(from_wire_format(stats["received_wire"]))
        rx_text, rx_lang = recovered["text"], recovered["language"]
        print(f"\n[RX] Recovered transcript: {rx_text}")
    except Exception as e:
        print(f"\n[RX] Frame corrupted (packet loss too high): {e}")
        return

    # 5. RECEIVER: Text -> Speech
    if synthesize:
        from tts import TextToSpeech
        tts = TextToSpeech()
        out_path = tts.synthesize(rx_text, rx_lang, out_path="received_output.wav")
        print(f"\n[RX] Synthesized speech written to: {out_path}")
    else:
        print("\n[RX] (skipping TTS synthesis — pass --synthesize to enable)")

    print("\n" + "=" * 60)
    print("Pipeline complete.")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SwarSetu end-to-end demo")
    parser.add_argument("audio_path", help="Path to input WAV/MP3 file (spoken sentence)")
    parser.add_argument("--lang", default=None, help="Language code (hi, ta, bn, ...); auto-detect if omitted")
    parser.add_argument("--bitrate", type=int, default=300, help="Simulated link bitrate in bps")
    parser.add_argument("--packet-loss", type=float, default=0.0, help="Simulated packet loss probability 0-1")
    parser.add_argument("--synthesize", action="store_true", help="Run TTS synthesis at the receiver")
    args = parser.parse_args()

    run_pipeline(args.audio_path, args.lang, args.bitrate, args.packet_loss, args.synthesize)
