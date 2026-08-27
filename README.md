# SwarSetu (स्वर सेतु — "Voice Bridge")

**SIH 2026 · Problem Statement SIH26173 · ISRO — iTantra**
Indian Multilingual TTS & STT Aided Neural Transceiver Radio Access for low bitrate links

## Idea

Don't transmit audio — transmit **meaning**. A spoken sentence at 16kHz/16-bit
PCM is ~256 kbps. The same sentence as compressed text is a few hundred
**bits**, total — three to four orders of magnitude smaller. So:

```
[Speaker] --mic--> STT --> text --compress--> RADIO LINK --decompress--> text --TTS--> [Speaker]
   (Sender's ground station)          low-bitrate hop (HF/VHF/satellite)      (Receiver's ground station)
```

This repo is a working prototype of that pipeline, runnable end-to-end on a
laptop, with a simulated radio channel so you can demo bitrate/latency
trade-offs without SDR hardware.

## Architecture

| Module | Role |
|---|---|
| `stt.py` | Speech → text using `faster-whisper` (small, multilingual, runs on CPU) |
| `compress.py` | Text → compact binary frame (zlib + base85 framing with language tag) |
| `channel_sim.py` | Simulates a low-bitrate, lossy radio link (configurable bps + packet loss) |
| `tts.py` | Text → speech at the receiver (Coqui XTTS-v2, multilingual) |
| `pipeline.py` | Wires all four stages together; prints stats at every hop |

## Setup

```bash
pip install -r requirements.txt
```

First run downloads the Whisper "small" and XTTS-v2 model weights
(~500MB combined) — do this once, ahead of a live demo, on a machine with
internet.

## Usage

```bash
# Full pipeline: your voice -> text -> simulated 300bps link -> reconstructed voice
python pipeline.py sample_audio/hello.wav --lang hi --bitrate 300 --synthesize

# Just see the STT + compression + channel stats (no audio synthesis, faster demo loop)
python pipeline.py sample_audio/hello.wav --bitrate 300

# Stress-test the link with packet loss
python pipeline.py sample_audio/hello.wav --bitrate 100 --packet-loss 0.1
```

Each module also runs standalone for isolated testing/demoing:

```bash
python compress.py       # shows a compression round-trip with sample Hindi text
python channel_sim.py    # shows transmit time at several bitrates vs raw audio
python stt.py audio.wav hi
python tts.py "आज मौसम बहुत अच्छा है" hi
```

## Where this goes next (roadmap for the SIH pitch)

- **Swap zlib for a learned entropy coder** trained on Indic transcript
  statistics — should beat generic DEFLATE meaningfully on short utterances.
- **Add FEC (forward error correction)** in `channel_sim.py` / a real
  transceiver layer, since a dropped word in an emergency broadcast matters
  more than a dropped video frame.
- **Fine-tune STT on Indic accents/dialects** — swap `faster-whisper` for an
  IndicWhisper or AI4Bharat checkpoint exported to CTranslate2.
- **Voice identity preservation** — XTTS-v2 supports voice cloning from a
  short reference clip, so the receiver can hear the *sender's own voice*,
  not a generic TTS voice — valuable for disaster-response / defense
  comms where speaker identity carries trust signal.
- **On-device quantized models** for actual low-power ground terminals
  (int8/int4 ONNX export of both STT and TTS).

## Why "SwarSetu"

*Swar* (स्वर) = voice/tone, *Setu* (सेतु) = bridge — a bridge for voice
across a link too narrow for voice itself.
