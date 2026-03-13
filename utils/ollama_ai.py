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
        # Convert GigaChat format to Ollama format
        messages = []
        system_content = None
        
        # Limit history size - keep system + last N messages
        limited_history = history
        if len(history) > max_history + 1:
            # Keep system prompt + last max_history messages
            system_msg = [h for h in history if h.get("role") == "system"]
            other_msgs = [h for h in history if h.get("role") != "system"]
            limited_history = system_msg + other_msgs[-max_history:]
        
        for msg in limited_history:
            role = msg.get("role", "").lower()
            content = msg.get("content", "")
            
            if role == "system":
                system_content = content
            elif role == "user":
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
        
        if system_content:
            payload["system"] = system_content
        
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
