import asyncio
import io
from gtts import gTTS

async def text_to_speech(text: str, lang: str = "en") -> io.BytesIO:
    """
    Генерирует голосовое сообщение из текста.
    Возвращает объект BytesIO, готовый к отправке.
    """
    def _generate():
        # Создаем буфер в памяти
        mp3_fp = io.BytesIO()
        # Генерируем речь (lang='ru' или 'en')
        # gTTS делает запрос к Google API
        tts = gTTS(text=text, lang=lang)
        tts.write_to_fp(mp3_fp)
        # Перематываем буфер в начало
        mp3_fp.seek(0)
        return mp3_fp

    # Запускаем синхронную функцию gTTS в отдельном потоке, 
    # чтобы не блокировать основного бота
    return await asyncio.to_thread(_generate)
