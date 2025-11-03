import speech_recognition as sr
from pydub import AudioSegment
import io

async def recognize_speech_from_bytes(audio_bytes: io.BytesIO) -> str | None:
    """
    Распознает речь из байтового потока аудио.
    """
    recognizer = sr.Recognizer()

    try:
        audio_bytes.seek(0)
        audio = AudioSegment.from_ogg(audio_bytes)
        
        wav_audio_bytes = io.BytesIO()
        audio.export(wav_audio_bytes, format="wav")
        wav_audio_bytes.seek(0)

        with sr.AudioFile(wav_audio_bytes) as source:
            audio_data = recognizer.record(source)

        text = recognizer.recognize_google(audio_data, language='ru-RU')
        return text.lower()
    
    except sr.UnknownValueError:
        print("Speech Recognition could not understand audio")
        return None
    except sr.RequestError as e:
        print(f"Could not request results from Speech Recognition service; {e}")
        return None
    except Exception as e:
        print(f"An error occurred during voice processing: {e}")
        return None
