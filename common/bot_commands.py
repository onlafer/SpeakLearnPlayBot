from aiogram.types import BotCommand

__all__ = ("bot_private_commands",)

def command(name: str, description: str) -> BotCommand:
    return BotCommand(command=name, description=description)

bot_private_commands = [
    command("start", "Запуск"),
    command("menu", "Меню"),
    command("cancel", "Отмена действия"),
]
