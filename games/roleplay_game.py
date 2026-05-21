import io
from aiogram import Bot, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    BufferedInputFile,
)

from .base import BaseGame, GameSession, GameStatus
from .game_registry import game_registry
from .session_manager import session_manager
from utils.bot_helpers import safe_edit_message
from utils.localization import translator
from database.user_manager import user_manager
from utils.ollama_ai import get_ollama_response
from utils.voice_recognition import recognize_speech_from_bytes
from utils.hf_tts import async_text_to_speech_f5

SCENARIOS = {
    "family": "Наша семья",
    "home": "Дом и квартира",
    "day": "Мой день",
    "work": "Марина едет на работу",
    "city": "Прогулка в город",
    "grocery": "В продовольственном магазине",
    "mall": "В универмаге",
    "restaurant": "В ресторане",
    "post": "На почте",
    "hotel": "В гостинице",
    "phone": "Разговор по телефону",
    "doctor": "Визит к врачу",
    "sports": "Спорт, или идеальная семья",
    "theater": "В театре",
    "vacation": "Летний отдых",
    "msu": "Московский государственный университет",
    "tour": "Экскурсия по Москве",
}

class RoleplayGame(BaseGame):
    def __init__(self):
        super().__init__(game_id="roleplay_game")

    def get_display_name(self, lang: str) -> str:
        return translator.get_text("game_roleplay_name", lang) or "🎭 Говорение по ролям"

    async def start_game(self, bot: Bot, user_id: int, message: Message) -> GameSession:
        user = await user_manager.get_user(user_id)
        lang = user.language if user else "en"

        session = GameSession(
            user_id=user_id,
            chat_id=message.chat.id,
            message_id=message.message_id,
            game_id=self.game_id,
            status=GameStatus.IN_PROGRESS,
            current_question=0,
            score=0,
            game_state={"ui_lang": lang, "scenario": None, "history": []}
        )
        
        await self._send_scenario_selection(bot, session)
        return session

    async def resume_game(self, bot: Bot, session: GameSession):
        ui_lang = session.game_state.get("ui_lang", "en")
        scenario = session.game_state.get("scenario")

        if not scenario:
            await self._send_scenario_selection(bot, session, as_new_message=True)
        else:
            resume_text = translator.get_text("game_roleplay_resume", ui_lang) or "Продолжаем ролевую игру! Жду вашего ответа."
            await bot.send_message(session.chat_id, resume_text)

    async def _send_scenario_selection(self, bot: Bot, session: GameSession, as_new_message: bool = False):
        ui_lang = session.game_state.get("ui_lang", "en")
        
        buttons = []
        # Create buttons in pairs for the scenarios
        row = []
        for key, name in SCENARIOS.items():
            row.append(InlineKeyboardButton(text=name, callback_data=f"set_rp_scene:{key}"))
            if len(row) == 2:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)

        btn_menu_text = translator.get_text("game_speech_practice_button_menu", ui_lang)
        if not btn_menu_text or btn_menu_text.startswith("game_"):
            btn_menu_text = "Menu"
            
        buttons.append([InlineKeyboardButton(text=btn_menu_text, callback_data="finish_roleplay")])

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        text = translator.get_text("game_roleplay_select_scene", ui_lang) or "Выберите сюжет для ролевой игры:"

        if as_new_message:
            sent_message = await bot.send_message(
                chat_id=session.chat_id, text=text, reply_markup=keyboard
            )
            session.message_id = sent_message.message_id
        else:
            new_message_id = await safe_edit_message(
                bot=bot,
                chat_id=session.chat_id,
                message_id=session.message_id,
                text=text,
                reply_markup=keyboard,
            )
            session.message_id = new_message_id

    async def _get_game_keyboard(self, translator, ui_lang: str) -> InlineKeyboardMarkup:
        """Returns the main game keyboard (e.g. for Finish)."""
        btn_menu_text = translator.get_text("game_speech_practice_button_menu", ui_lang)
        if not btn_menu_text or btn_menu_text.startswith("game_"):
            btn_menu_text = "Menu"
            
        buttons = [[InlineKeyboardButton(text=btn_menu_text, callback_data="finish_roleplay")]]
        return InlineKeyboardMarkup(inline_keyboard=buttons)

    async def handle_callback(
        self, bot: Bot, session: GameSession, callback: CallbackQuery
    ) -> GameSession:
        await callback.answer()
        ui_lang = session.game_state.get("ui_lang", "en")
        action, *data = callback.data.split(":")

        if action == "set_rp_scene":
            scene_key = data[0]
            scenario_name = SCENARIOS.get(scene_key, "Неизвестный сюжет")
            
            # Logic to assign a default voice gender based on scenario
            female_scenarios = ["grocery", "mall", "hotel", "restaurant", "city"]
            default_voice = "female" if scene_key in female_scenarios else "male"
            
            session.game_state["scenario"] = scene_key
            session.game_state["voice"] = default_voice
            
            # 0. SAVE IMMEDIATELY to prevent race conditions with incoming messages
            await session_manager.update_session(session.user_id, session)
            
            # Setup prompt for Ollama
            system_prompt = (
                f"### IDENTITY:\n"
                f"You are a native Russian speaker in a realistic roleplay. "
                f"Your gender: {'Woman/Girl (Женщина)' if default_voice == 'female' else 'Man (Мужчина)'}. "
                f"You are the conversation partner in the scenario: '{scenario_name}'.\n\n"
                
                f"### CHARACTER RULES:\n"
                f"- NEVER act as an AI assistant. NEVER offer help or ask 'How can I assist you?'.\n"
                f"- You are a REAL PERSON in this situation. Stay fully in character.\n"
                f"- Use natural, conversational Russian. No robotic or overly formal language.\n"
                f"- IMPORTANT: Use the correct grammatical gender (feminine/masculine) for yourself.\n"
                f"- Keep responses short (1-2 sentences).\n"
                f"- You MUST respond ONLY in Russian.\n"
                f"- ENSURE your Russian is natural and perfect, avoiding any translational artifacts.\n\n"
                
                f"### CONTEXT:\n"
                f"Scenario: {scenario_name}. Start the conversation as your character immediately."
            )
            session.game_state["history"] = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Начни диалог как твой персонаж."} # Force AI to start
            ]
            
            # 1. UPDATE HEADER IMMEDIATELY
            menu_hint = translator.get_text("menu_hint", ui_lang)
            await safe_edit_message(
                bot=bot,
                chat_id=session.chat_id,
                message_id=session.message_id,
                text=f"🎭 *{scenario_name}*\n\n_{menu_hint}_",
                parse_mode="Markdown",
                reply_markup=None
            )

            # 2. SEND INTERMEDIATE "THINKING" MESSAGE (Consistent with _process_user_reply)
            loading_text = translator.get_text("game_russian_tutor_thinking", ui_lang) or "Thinking"
            loading_msg = await bot.send_message(
                chat_id=session.chat_id,
                text=f"⏳ _{loading_text}..._",
                parse_mode="Markdown"
            )

            session.game_state["is_thinking"] = True
            await session_manager.update_session(session.user_id, session)

            try:
                # 3. GENERATE AI MOVE (takes time)
                response_text = await get_ollama_response(session.game_state["history"])
                
                if not response_text or not response_text.strip() or response_text == "No response from model.":
                    response_text = "..."

                # Add AI response to history
                session.game_state["history"].append({"role": "assistant", "content": response_text})

                menu_hint = translator.get_text("menu_hint", ui_lang)
                
                # 4. GENERATE TTS (takes more time)
                await bot.send_chat_action(chat_id=session.chat_id, action="record_voice")
                voice_id = session.game_state.get("voice", "male")
                audio_stream = await async_text_to_speech_f5(response_text, voice=voice_id)

                # 5. DELETE LOADING MESSAGE (only now, when everything is ready)
                try:
                    await bot.delete_message(session.chat_id, loading_msg.message_id)
                except Exception:
                    pass
                
                if audio_stream:
                    voice_file = BufferedInputFile(audio_stream.getvalue(), filename="response.ogg")
                    await bot.send_voice(session.chat_id, voice=voice_file, caption=f"{response_text}\n\n_{menu_hint}_", parse_mode="Markdown")
                else:
                    # Fallback to text message if TTS fails, since we removed it from the header
                    await bot.send_message(session.chat_id, f"{response_text}\n\n_{menu_hint}_", parse_mode="Markdown")
                
            finally:
                session.game_state["is_thinking"] = False
                await session_manager.update_session(session.user_id, session)
            
        elif action == "finish_roleplay":
            session.status = GameStatus.FINISHED
            await self.end_game(bot, session)

        return session

    async def handle_message(self, bot: Bot, session: GameSession, message: Message) -> GameSession:
        ui_lang = session.game_state.get("ui_lang", "en")
        scenario = session.game_state.get("scenario")

        if message.text and message.text.startswith("/"):
            return session

        if not scenario:
            await self._send_scenario_selection(bot, session, as_new_message=True)
            return session
            
        if not message.text:
            return session
            
        if session.game_state.get("is_thinking"):
            wait_text = translator.get_text("wait_thinking", ui_lang) or "⏳ Please wait, I'm still processing the previous message!"
            await message.reply(wait_text)
            return session
            
        return await self._process_user_reply(bot, session, message, message.text, ui_lang)

    async def handle_voice_message(self, bot: Bot, session: GameSession, message: Message) -> GameSession:
        ui_lang = session.game_state.get("ui_lang", "en")
        scenario = session.game_state.get("scenario")

        if not scenario:
            await self._send_scenario_selection(bot, session, as_new_message=True)
            return session
            
        await bot.send_chat_action(chat_id=session.chat_id, action="typing")
        file_id = message.voice.file_id
        file = await bot.get_file(file_id)
        cached_file = await bot.download_file(file.file_path, io.BytesIO())
        user_input_text = await recognize_speech_from_bytes(cached_file, language="ru-RU")

        if not user_input_text:
            error_msg = translator.get_text("game_speech_practice_feedback_unrecognized", ui_lang) or "Извините, не удалось распознать голос."
            await message.reply(error_msg, parse_mode="Markdown")
            return session
            
        if session.game_state.get("is_thinking"):
            wait_text = translator.get_text("wait_thinking", ui_lang) or "⏳ Please wait, I'm still processing the previous message!"
            await message.reply(wait_text)
            return session
            
        return await self._process_user_reply(bot, session, message, user_input_text, ui_lang)

    async def _process_user_reply(self, bot: Bot, session: GameSession, message: Message, user_text: str, ui_lang: str) -> GameSession:
        session.game_state["history"].append({"role": "user", "content": user_text})
        
        await bot.send_chat_action(chat_id=session.chat_id, action="typing")
        
        # Send intermediate "Thinking" message
        loading_text = translator.get_text("game_russian_tutor_thinking", ui_lang) or "Thinking"
        loading_msg = await bot.send_message(
            chat_id=session.chat_id,
            text=f"⏳ _{loading_text}..._",
            parse_mode="Markdown"
        )
        
        session.game_state["is_thinking"] = True
        await session_manager.update_session(session.user_id, session)

        try:
            # Get AI response
            ai_response = await get_ollama_response(session.game_state["history"])
            
            if not ai_response or not ai_response.strip() or ai_response == "No response from model.":
                ai_response = "..."
                
            session.game_state["history"].append({"role": "assistant", "content": ai_response})
            
            await bot.send_chat_action(chat_id=session.chat_id, action="record_voice")
            voice_id = session.game_state.get("voice", "male")
            audio_stream = await async_text_to_speech_f5(ai_response, voice=voice_id)
            
            menu_hint = translator.get_text("menu_hint", ui_lang)
            final_caption = f"{ai_response}\n\n_{menu_hint}_"

            # Delete loading message
            try:
                await bot.delete_message(session.chat_id, loading_msg.message_id)
            except Exception:
                pass

            if audio_stream:
                voice_file = BufferedInputFile(audio_stream.getvalue(), filename="response.ogg")
                await message.reply_voice(voice=voice_file, caption=final_caption, parse_mode="Markdown")
            else:
                await message.reply(final_caption, parse_mode="Markdown")

        finally:
            session.game_state["is_thinking"] = False
            await session_manager.update_session(session.user_id, session)

        return session


    async def end_game(self, bot: Bot, session: GameSession, send_message: bool = True):
        if send_message:
            ui_lang = session.game_state.get("ui_lang", "en")
            
            end_text = translator.get_text("game_roleplay_end", ui_lang) or "✅ Игра 'Говорение по ролям' завершена. Для возврата в меню используйте /menu."
            
            await safe_edit_message(
                bot=bot,
                chat_id=session.chat_id,
                message_id=session.message_id,
                text=end_text,
                parse_mode="Markdown",
                reply_markup=None
            )

game_registry.register(RoleplayGame())
