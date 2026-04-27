from sqlalchemy import Integer, String, Text, JSON, BIGINT, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from games.base import GameStatus


class UserModel(Base):
    """Модель для хранения пользователей в БД."""
    
    __tablename__ = "users"
    
    user_id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    language: Mapped[str] = mapped_column(String, nullable=False, default="en")
    created_at: Mapped[int] = mapped_column(Integer, nullable=False)
    streak_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_activity_date: Mapped[str | None] = mapped_column(String, nullable=True) # "YYYY-MM-DD"
    activity_history: Mapped[list] = mapped_column(JSON, default=list, nullable=False) # ["2026-04-25", ...]


class GameSessionModel(Base):
    """Модель для хранения игровых сессий в БД."""
    
    __tablename__ = "game_sessions"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BIGINT, nullable=False, index=True)
    chat_id: Mapped[int] = mapped_column(BIGINT, nullable=False)
    message_id: Mapped[int] = mapped_column(BIGINT, nullable=False)
    game_id: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default=GameStatus.IN_PROGRESS.value
    )
    current_question: Mapped[int] = mapped_column(Integer, default=0)
    score: Mapped[int] = mapped_column(Integer, default=0)
    game_state: Mapped[dict] = mapped_column(JSON, default=dict)


class FileModel(Base):
    """Общие файлы для всех пользователей. Файл на диске + Telegram file_id для кеша."""

    __tablename__ = "files"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)  # ключ для поиска (напр. intro_video)
    storage_path: Mapped[str] = mapped_column(String, nullable=False)  # путь в хранилище (напр. videos/intro.mp4)
    file_id: Mapped[str | None] = mapped_column(String, nullable=True)  # Telegram file_id — после первой отправки, для кеша
    file_type: Mapped[str] = mapped_column(String, nullable=False)  # video, document, audio, voice


# --- Модели для данных из /data (все данные теперь в БД) ---


class WatchVideoModel(Base):
    """Видео для игры «Смотри видео» (data/watch_video_data)."""

    __tablename__ = "watch_videos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    file_id: Mapped[int] = mapped_column(ForeignKey("files.id"), nullable=False)  # ссылка на FileModel (Telegram file_id берём оттуда)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class PositiveFeedbackModel(Base):
    """Фразы одобрения по языкам (data/positive_feedback)."""

    __tablename__ = "positive_feedbacks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    language: Mapped[str] = mapped_column(String, nullable=False, index=True)
    text: Mapped[str] = mapped_column(String, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class RussianCaseQuestionModel(Base):
    """Вопросы квиза по падежам (data/russian_cases_quiz_data)."""

    __tablename__ = "russian_case_questions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    case_type: Mapped[str] = mapped_column(String, nullable=False, index=True)  # accusative, prepositional, dative, genitive, instrumental, nominative
    level: Mapped[str] = mapped_column(String, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[list] = mapped_column(JSON, nullable=False)  # ["вариант1", "вариант2", ...]
    correct_answer: Mapped[str] = mapped_column(String, nullable=False)
    explanation: Mapped[dict] = mapped_column(JSON, nullable=False)  # {"en": "...", "ru": "...", ...}
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class RussianTutorPromptModel(Base):
    """Промпты для русского тьютора (data/russian_tutor). Один ключ — одно значение."""

    __tablename__ = "russian_tutor_prompts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)


class SingAlongSongModel(Base):
    """Песни для «Пой со мной» (data/sing_along_data)."""

    __tablename__ = "sing_along_songs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    artist: Mapped[str] = mapped_column(String, nullable=False)
    full_audio_file_id: Mapped[int] = mapped_column(ForeignKey("files.id"), nullable=False)  # ссылка на FileModel
    minus_audio_file_id: Mapped[int] = mapped_column(ForeignKey("files.id"), nullable=False)  # ссылка на FileModel
    lyrics: Mapped[str] = mapped_column(Text, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class SpeechPracticeCategoryModel(Base):
    """Категории для практики речи (data/speech_practice_quiz_data)."""

    __tablename__ = "speech_practice_categories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    category_key: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    category_icon: Mapped[str] = mapped_column(String, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class SpeechPracticeItemModel(Base):
    """Фразы/слова внутри категории практики речи."""

    __tablename__ = "speech_practice_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("speech_practice_categories.id"), nullable=False, index=True)
    text: Mapped[str] = mapped_column(String, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class TranslateWordCategoryModel(Base):
    """Категории слов для квиза «Переведи слово» (data/translate_word_quiz)."""

    __tablename__ = "translate_word_categories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    category_key: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    category_icon: Mapped[str] = mapped_column(String, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class TranslateWordModel(Base):
    """Слово и переводы по языкам."""

    __tablename__ = "translate_words"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("translate_word_categories.id"), nullable=False, index=True)
    russian_word: Mapped[str] = mapped_column(String, nullable=False)
    translations: Mapped[dict] = mapped_column(JSON, nullable=False)  # {"en": "Apple", "es": "Manzana", ...}
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class VerbAspectQuestionModel(Base):
    """Вопросы квиза по виду глагола (data/verb_aspect_quiz)."""

    __tablename__ = "verb_aspect_questions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    level: Mapped[str] = mapped_column(String, nullable=False, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[list] = mapped_column(JSON, nullable=False)
    correct_answer: Mapped[str] = mapped_column(String, nullable=False)
    explanation: Mapped[dict] = mapped_column(JSON, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class VerbTenseQuestionModel(Base):
    """Вопросы квиза по времени глагола (data/verb_tense_quiz)."""

    __tablename__ = "verb_tense_questions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    level: Mapped[str] = mapped_column(String, nullable=False, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[list] = mapped_column(JSON, nullable=False)
    correct_answer: Mapped[str] = mapped_column(String, nullable=False)
    explanation: Mapped[dict] = mapped_column(JSON, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
