import asyncio
import io
import soundfile as sf
from utils.hf_tts import async_text_to_speech_f5

async def test_tts():
    print("Testing local F5-TTS...")
    text = "Привет! Я твой новый партнер по ролевой игре. Рад познакомиться!"
    
    # Test Male
    print("\nTesting MALE voice...")
    buffer_male = await async_text_to_speech_f5(text, voice="male")
    if buffer_male:
        with open("test_tts_male.ogg", "wb") as f:
            f.write(buffer_male.getvalue())
        print("Success! Saved to test_tts_male.ogg")

    # Test Female
    print("\nTesting FEMALE voice...")
    buffer_female = await async_text_to_speech_f5(text, voice="female")
    if buffer_female:
        with open("test_tts_female.ogg", "wb") as f:
            f.write(buffer_female.getvalue())
        print("Success! Saved to test_tts_female.ogg")

if __name__ == "__main__":
    asyncio.run(test_tts())
