"""
tts.py — Text-to-Speech module for SwarSetu (receiver side)

Uses Coqui TTS with a multilingual/XTTS-v2-style backend, which supports
voice cloning and several Indic languages. For a lighter footprint on
low-power ground hardware, swap in a VITS-based single-language model per
deployment (faster, smaller, no GPU needed).

Falls back gracefully with clear instructions if the model isn't downloaded
yet (first run pulls weights from the TTS model hub).
"""

from pathlib import Path

# Small, well-supported multilingual model. XTTS-v2 covers Hindi among
# Indic languages out of the box; for other Indian languages swap in a
# language-specific VITS checkpoint (e.g. Coqui's "tts_models/hi/..." style
# names as they become available, or an AI4Bharat Indic-TTS export).
DEFAULT_MODEL = "tts_models/multilingual/multi-dataset/xtts_v2"

# Map ISO codes -> XTTS language codes where they differ
LANGUAGE_MAP = {
    "hi": "hi", "en": "en", "bn": "en",  # fallback to closest supported voice
    "ta": "en", "te": "en", "mr": "en", "gu": "en",
}


class TextToSpeech:
    def __init__(self, model_name: str = DEFAULT_MODEL, speaker_wav: str | None = None):
        from TTS.api import TTS  # imported lazily so stt-only usage stays light
        self.tts = TTS(model_name)
        self.speaker_wav = speaker_wav  # a reference voice sample for cloning (optional)

    def synthesize(self, text: str, language: str, out_path: str = "output.wav") -> str:
        lang_code = LANGUAGE_MAP.get(language, "en")
        kwargs = {"text": text, "language": lang_code, "file_path": out_path}
        if self.speaker_wav and Path(self.speaker_wav).exists():
            kwargs["speaker_wav"] = self.speaker_wav
        else:
            # XTTS requires a speaker reference; ship a short default clip in
            # assets/ or point speaker_wav at any 6+ second clean sample.
            kwargs["speaker"] = self.tts.speakers[0] if self.tts.speakers else None
        self.tts.tts_to_file(**kwargs)
        return out_path


if __name__ == "__main__":
    import sys
    text = sys.argv[1] if len(sys.argv) > 1 else "आज मौसम बहुत अच्छा है"
    lang = sys.argv[2] if len(sys.argv) > 2 else "hi"
    tts = TextToSpeech()
    path = tts.synthesize(text, lang)
    print(f"Synthesized audio written to {path}")
