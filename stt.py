"""
stt.py — Speech-to-Text module for SwarSetu

Uses faster-whisper's "small" model (multilingual, ~244M params, CTranslate2
backend so it runs fast even on CPU). Whisper's multilingual checkpoints cover
Hindi, Bengali, Tamil, Telugu, Marathi, Gujarati, Urdu, Punjabi, Malayalam,
Kannada, Odia and more out of the box — a reasonable "small model" starting
point for a low-bitrate transceiver prototype.

Swap MODEL_SIZE to "tiny" for an even smaller footprint on constrained
ground-station hardware, or point WhisperModel at a fine-tuned Indic
checkpoint (e.g. an IndicWhisper CTranslate2 export) for better accuracy.
"""

from faster_whisper import WhisperModel

MODEL_SIZE = "small"          # tiny | base | small | medium | large-v3
DEVICE = "cpu"                 # switch to "cuda" if a GPU is available
COMPUTE_TYPE = "int8"          # int8 quantization keeps this light on CPU


class SpeechToText:
    def __init__(self, model_size: str = MODEL_SIZE, device: str = DEVICE,
                 compute_type: str = COMPUTE_TYPE):
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def transcribe(self, audio_path: str, language: str | None = None) -> dict:
        """
        Transcribe an audio file to text.

        language: ISO 639-1 code (e.g. "hi", "ta", "bn"). Leave None to
        auto-detect — useful when the transmitting end doesn't know the
        speaker's language in advance.

        Returns: {"text": str, "language": str, "segments": [...]}
        """
        segments, info = self.model.transcribe(
            audio_path,
            language=language,
            beam_size=5,
            vad_filter=True,          # strips silence, cuts payload size further
        )
        segments = list(segments)
        full_text = " ".join(seg.text.strip() for seg in segments)
        return {
            "text": full_text.strip(),
            "language": info.language,
            "language_probability": info.language_probability,
            "segments": [
                {"start": s.start, "end": s.end, "text": s.text.strip()}
                for s in segments
            ],
        }


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python stt.py <audio_file> [language_code]")
        sys.exit(1)
    lang = sys.argv[2] if len(sys.argv) > 2 else None
    stt = SpeechToText()
    result = stt.transcribe(sys.argv[1], language=lang)
    print(f"Detected language: {result['language']} ({result['language_probability']:.2f})")
    print(f"Text: {result['text']}")
