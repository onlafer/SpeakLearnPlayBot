import os
import aiohttp

from dotenv import find_dotenv, load_dotenv

# Load environment variables from .env file
load_dotenv(find_dotenv("config\\.env"))


def get_ollama_config():
    """Read Ollama configuration from environment variables."""
    return {
        "host": os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        "model": os.getenv("OLLAMA_MODEL", "gemma3:12b"),
        "max_history": int(os.getenv("OLLAMA_MAX_HISTORY", "20")),
        "max_input": int(os.getenv("OLLAMA_MAX_INPUT", "2000")),
    }


async def get_ollama_response(history: list) -> str:
    """
    Asynchronously sends a request to the local Ollama API.
    """
    config = get_ollama_config()
    max_history = config["max_history"]
    max_input = config["max_input"]

    try:
        # Convert history format to Ollama format
        messages = []

        # 1. First, find and add system message if it exists
        system_msg = next((h for h in history if h.get("role") == "system"), None)
        if system_msg:
            messages.append({"role": "system", "content": system_msg.get("content", "")})

        # 2. Limit other history - keep last N messages
        other_msgs = [h for h in history if h.get("role") != "system"]
        if len(other_msgs) > max_history:
            other_msgs = other_msgs[-max_history:]

        for msg in other_msgs:
            role = msg.get("role", "").lower()
            content = msg.get("content", "")

            if role == "user":
                # Truncate long user messages
                if len(content) > max_input:
                    content = content[:max_input] + "... [truncated]"
                messages.append({"role": "user", "content": content})
            elif role == "assistant":
                messages.append({"role": "assistant", "content": content})

        payload = {
            "model": config["model"],
            "messages": messages,
            "stream": False,
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{config['host']}/api/chat",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    return f"Error: Ollama returned status {response.status}. {error_text}"

                data = await response.json()
                return data.get("message", {}).get("content", "No response from model.")

    except aiohttp.ClientError as e:
        return f"Error connecting to Ollama: {e}. Make sure Ollama is running on {config['host']}"
    except Exception as e:
        print(f"Error calling Ollama API: {e}")
        return "Sorry, an error occurred while trying to contact the AI assistant. Please try again later."


async def preprocess_russian_text_for_tts(text: str) -> str:
    """
    Uses Gemma (via Ollama) to expand numbers/dates only (stresses are handled by RUAccent).
    """
    prompt = (
        "Ты — эксперт по русскому языку. Подготовь текст для системы синтеза речи (TTS).\n"
        "1. ЧИСЛА И ДАТЫ: Все числа, даты и сокращения разверни в полные слова. Используй только РУССКУЮ традицию чтения дат "
        "(например, '1799 год' -> 'тысяча семьсот девяносто девятый год'). Соблюдай правильные падежи.\n"
        "2. ФОРМАТ: Верни ТОЛЬКО итоговый текст. Не добавляй никаких пояснений, знаков ударения или кавычек.\n\n"
        f"ТЕКСТ ДЛЯ ОБРАБОТКИ:\n{text}"
    )

    history = [{"role": "system", "content": "You are a helpful assistant that processes Russian text for TTS."},
               {"role": "user", "content": prompt}]

    response = await get_ollama_response(history)
    # Clean up response in case model adds quotes or extra text
    processed_text = response.strip().strip('"').strip("'")

    if "Error:" in processed_text or not processed_text:
        print(f"Ollama preprocessing failed: {processed_text}")
        return text

    return processed_text


async def is_answer_correct(question: str, user_answer: str, expected_answers: list) -> bool:
    """
    Checks if the user answer matches expected answers semantically using local Ollama model.
    """
    config = get_ollama_config()
    # Fallback if no model/host config? Just standard procedure.
    
    expected_str = ", ".join(f'"{a}"' for a in expected_answers[:3])  # limit to 3 variants

    prompt = f"""Ты — экзаменатор. Твоя задача — проверить правильность ответа студента.
Вопрос: "{question}"
Правильные (эталонные) ответы: {expected_str}
Ответ пользователя: "{user_answer}"

Верен ли ответ пользователя по смыслу, даже если сформулирован немного иначе?
Ответь ТОЛЬКО одним словом: "да" или "нет"."""

    history = [
        {"role": "system", "content": "You are an examiner validating user answers. Reply ONLY with 'да' or 'нет'."},
        {"role": "user", "content": prompt}
    ]

    try:
        response = await get_ollama_response(history)
        answer = response.strip().lower()
        return "да" in answer.split()[0] or answer.startswith("да")
    except Exception as e:
        print(f"Ollama error in is_answer_correct: {e}")
        # Fallback basic matching
        user_norm = user_answer.lower().strip()
        for ans in expected_answers:
            if ans.lower().strip() == user_norm:
                return True
        return False
