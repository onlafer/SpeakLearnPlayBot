import asyncio
import io
from gtts import gTTS

async def text_to_speech(text: str, lang: str = "en") -> io.BytesIO:
    """
    Генерирует голосовое сообщение из текста.
    Возвращает объект BytesIO, готовый к отправке.
    """
    def _generate():
        mp3_fp = io.BytesIO()
        tts = gTTS(text=text, lang=lang)
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        return mp3_fp

    return await asyncio.to_thread(_generate)
