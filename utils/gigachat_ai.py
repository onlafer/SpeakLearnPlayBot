import os

from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole

GIGACHAT_CREDENTIALS = os.getenv("GIGACHAT_CREDENTIALS")


async def get_ai_tutor_response(history: list) -> str:
    """
    Asynchronously sends a request to the GigaChat API.
    """
    if not GIGACHAT_CREDENTIALS:
        return (
            "Error: GigaChat API credentials not found. "
            "Please check your environment variables."
        )
    try:
        async with GigaChat(
            credentials=GIGACHAT_CREDENTIALS, verify_ssl_certs=False
        ) as giga:
            response = await giga.achat(
                Chat(
                    messages=[
                        Messages(role=msg["role"], content=msg["content"])
                        for msg in history
                    ],
                    model="GigaChat-Pro",
                )
            )
            return response.choices[0].message.content
    except Exception as e:
        print(f"Error calling GigaChat API: {e}")
        return "Sorry, an error occurred while trying to contact the AI assistant. Please try again later."
