import io
import asyncio
from pydub import AudioSegment
from faster_whisper import WhisperModel
import torch

# Global WhisperModel singleton instance
_whisper_model = None

def get_whisper_model():
    """
    Returns a singleton instance of the WhisperModel.
    Loads the model on the first call.
    """
    global _whisper_model
    if _whisper_model is None:
        # Determine device (cuda or cpu)
        device = "cuda" if torch.cuda.is_available() else "cpu"
        # Determine compute type (float16 for GPU, int8/float32 for CPU)
        # Note: CUDA with float16 is fastest. CPU is best with int8.
        compute_type = "float16" if device == "cuda" else "int8"
        
        print(f"Loading local faster-whisper model ('small') on {device} ({compute_type})...")
        _whisper_model = WhisperModel(
            "small",
            device=device,
            compute_type=compute_type
        )
    return _whisper_model


async def recognize_speech_from_bytes(audio_bytes: io.BytesIO, language: str = "en-US") -> str | None:
    """
    Распознает речь из байтового потока аудио с помощью локальной модели faster-whisper на GPU/CPU.
    """
    try:
        # 1. Prepare WAV audio from OGG using pydub
        audio_bytes.seek(0)
        audio = AudioSegment.from_ogg(audio_bytes)
        
        wav_audio_bytes = io.BytesIO()
        audio.export(wav_audio_bytes, format="wav")
        wav_audio_bytes.seek(0)

        # 2. Get language code (faster-whisper expects 2-letter codes like 'ru', 'en')
        lang_code = language.split("-")[0].lower() if language else "en"

        # 3. Define the synchronous transcription function to run in a separate thread
        def _transcribe():
            model = get_whisper_model()
            segments, info = model.transcribe(
                wav_audio_bytes,
                language=lang_code,
                beam_size=5
            )
            # Combine segment texts
            text = "".join(segment.text for segment in segments)
            return text.strip().lower()

        # Run transcription in a separate thread to keep asyncio event loop responsive
        text = await asyncio.to_thread(_transcribe)
        return text if text else None
        
    except Exception as e:
        print(f"An error occurred during local voice processing: {e}")
        import traceback
        traceback.print_exc()
        return None
