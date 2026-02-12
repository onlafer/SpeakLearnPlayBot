"""
Перенос всех данных из /data в БД.
Запуск: из корня проекта
  python -m scripts.seed_data
  или: uv run python -m scripts.seed_data

Перед запуском: таблицы должны существовать (alembic upgrade head или init_db).
При повторном запуске скрипт проверяет наличие данных и при необходимости пропускает таблицы.
"""

import asyncio
import sys
from pathlib import Path

# корень проекта в PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.base import async_session_maker
from database.models import (
    FileModel,
    PositiveFeedbackModel,
    RussianCaseQuestionModel,
    RussianTutorPromptModel,
    SingAlongSongModel,
    SpeechPracticeCategoryModel,
    SpeechPracticeItemModel,
    TranslateWordCategoryModel,
    TranslateWordModel,
    VerbAspectQuestionModel,
    VerbTenseQuestionModel,
    WatchVideoModel,
)


def _lyrics_to_str(lyrics) -> str:
    """lyrics в данных может быть строкой или кортежем строк."""
    if isinstance(lyrics, str):
        return lyrics
    if isinstance(lyrics, (list, tuple)):
        return "\n".join(str(x) for x in lyrics)
    return str(lyrics)


async def seed_watch_videos(session: AsyncSession) -> None:
    from data.watch_video_data import VIDEO_LIST

    r = await session.execute(select(WatchVideoModel).limit(1))
    if r.scalar_one_or_none():
        print("  watch_videos: уже есть данные, пропуск")
        return

    for i, item in enumerate(VIDEO_LIST):
        key = f"watch_video_{i}"
        file_row = FileModel(
            key=key,
            storage_path=f"telegram_cache/{key}",
            file_id=item["video_id"],
            file_type="video",
        )
        session.add(file_row)
        await session.flush()
        session.add(
            WatchVideoModel(
                title=item["title"],
                file_id=file_row.id,
                sort_order=i,
            )
        )
    print(f"  watch_videos: {len(VIDEO_LIST)} записей")


async def seed_positive_feedbacks(session: AsyncSession) -> None:
    from data.positive_feedback import POSITIVE_FEEDBACKS

    r = await session.execute(select(PositiveFeedbackModel).limit(1))
    if r.scalar_one_or_none():
        print("  positive_feedbacks: уже есть данные, пропуск")
        return

    n = 0
    for lang, texts in POSITIVE_FEEDBACKS.items():
        for i, text in enumerate(texts):
            session.add(
                PositiveFeedbackModel(
                    language=lang,
                    text=text,
                    sort_order=i,
                )
            )
            n += 1
    print(f"  positive_feedbacks: {n} записей")


CASE_QUESTIONS_SOURCES = [
    ("accusative", "ACCUSATIVE_CASE_QUESTIONS"),
    ("prepositional", "PREPOSITIONAL_CASE_QUESTIONS"),
    ("dative", "DATIVE_CASE_QUESTIONS"),
    ("genitive", "GENITIVE_CASE_QUESTIONS"),
    ("instrumental", "INSTRUMENTAL_CASE_QUESTIONS"),
    ("nominative", "NOMINATIVE_CASE_QUESTIONS"),
]


async def seed_russian_case_questions(session: AsyncSession) -> None:
    from data import russian_cases_quiz_data

    r = await session.execute(select(RussianCaseQuestionModel).limit(1))
    if r.scalar_one_or_none():
        print("  russian_case_questions: уже есть данные, пропуск")
        return

    n = 0
    for case_type, attr in CASE_QUESTIONS_SOURCES:
        questions = getattr(russian_cases_quiz_data, attr)
        for i, q in enumerate(questions):
            session.add(
                RussianCaseQuestionModel(
                    case_type=case_type,
                    level=q["level"],
                    text=q["text"],
                    options=q["options"],
                    correct_answer=q["correct_answer"],
                    explanation=q["explanation"],
                    sort_order=i,
                )
            )
            n += 1
    print(f"  russian_case_questions: {n} записей")


async def seed_russian_tutor_prompts(session: AsyncSession) -> None:
    from data.russian_tutor import SYSTEM_PROMPT

    r = await session.execute(
        select(RussianTutorPromptModel).where(
            RussianTutorPromptModel.key == "system_prompt"
        )
    )
    if r.scalar_one_or_none():
        print("  russian_tutor_prompts: уже есть данные, пропуск")
        return

    session.add(
        RussianTutorPromptModel(key="system_prompt", value=SYSTEM_PROMPT)
    )
    print("  russian_tutor_prompts: 1 запись")


async def seed_sing_along_songs(session: AsyncSession) -> None:
    from data.sing_along_data import SING_ALONG_SONGS

    r = await session.execute(select(SingAlongSongModel).limit(1))
    if r.scalar_one_or_none():
        print("  sing_along_songs: уже есть данные, пропуск")
        return

    for i, song in enumerate(SING_ALONG_SONGS):
        full_key = f"sing_along_{i}_full"
        minus_key = f"sing_along_{i}_minus"
        full_file = FileModel(
            key=full_key,
            storage_path=f"telegram_cache/{full_key}",
            file_id=song["full_audio_id"],
            file_type="audio",
        )
        minus_file = FileModel(
            key=minus_key,
            storage_path=f"telegram_cache/{minus_key}",
            file_id=song["minus_audio_id"],
            file_type="audio",
        )
        session.add(full_file)
        session.add(minus_file)
        await session.flush()
        session.add(
            SingAlongSongModel(
                title=song["title"],
                artist=song["artist"],
                full_audio_file_id=full_file.id,
                minus_audio_file_id=minus_file.id,
                lyrics=_lyrics_to_str(song["lyrics"]),
                sort_order=i,
            )
        )
    print(f"  sing_along_songs: {len(SING_ALONG_SONGS)} записей")


async def seed_speech_practice(session: AsyncSession) -> None:
    from data.speech_practice_quiz_data import SPEECH_PRACTICE_DATA

    r = await session.execute(select(SpeechPracticeCategoryModel).limit(1))
    if r.scalar_one_or_none():
        print("  speech_practice: уже есть данные, пропуск")
        return

    for i, cat in enumerate(SPEECH_PRACTICE_DATA):
        category = SpeechPracticeCategoryModel(
            category_key=cat["category_key"],
            category_icon=cat["category_icon"],
            sort_order=i,
        )
        session.add(category)
        await session.flush()
        for j, item_text in enumerate(cat["items"]):
            session.add(
                SpeechPracticeItemModel(
                    category_id=category.id,
                    text=item_text,
                    sort_order=j,
                )
            )
    print(f"  speech_practice: {len(SPEECH_PRACTICE_DATA)} категорий, "
          f"{sum(len(c['items']) for c in SPEECH_PRACTICE_DATA)} фраз")


async def seed_translate_words(session: AsyncSession) -> None:
    from data.translate_word_quiz import WORD_DICTIONARIES

    r = await session.execute(select(TranslateWordCategoryModel).limit(1))
    if r.scalar_one_or_none():
        print("  translate_words: уже есть данные, пропуск")
        return

    for i, cat in enumerate(WORD_DICTIONARIES):
        category = TranslateWordCategoryModel(
            category_key=cat["category_key"],
            category_icon=cat["category_icon"],
            sort_order=i,
        )
        session.add(category)
        await session.flush()
        for j, w in enumerate(cat["words"]):
            session.add(
                TranslateWordModel(
                    category_id=category.id,
                    russian_word=w["russian_word"],
                    translations=w["translations"],
                    sort_order=j,
                )
            )
    n_cats = len(WORD_DICTIONARIES)
    n_words = sum(len(c["words"]) for c in WORD_DICTIONARIES)
    print(f"  translate_words: {n_cats} категорий, {n_words} слов")


async def seed_verb_aspect_questions(session: AsyncSession) -> None:
    from data.verb_aspect_quiz import VERB_ASPECT_QUESTIONS

    r = await session.execute(select(VerbAspectQuestionModel).limit(1))
    if r.scalar_one_or_none():
        print("  verb_aspect_questions: уже есть данные, пропуск")
        return

    for i, q in enumerate(VERB_ASPECT_QUESTIONS):
        session.add(
            VerbAspectQuestionModel(
                level=q["level"],
                text=q["text"],
                options=q["options"],
                correct_answer=q["correct_answer"],
                explanation=q["explanation"],
                sort_order=i,
            )
        )
    print(f"  verb_aspect_questions: {len(VERB_ASPECT_QUESTIONS)} записей")


async def seed_verb_tense_questions(session: AsyncSession) -> None:
    from data.verb_tense_quiz import VERB_TENSE_QUESTIONS

    r = await session.execute(select(VerbTenseQuestionModel).limit(1))
    if r.scalar_one_or_none():
        print("  verb_tense_questions: уже есть данные, пропуск")
        return

    for i, q in enumerate(VERB_TENSE_QUESTIONS):
        session.add(
            VerbTenseQuestionModel(
                level=q["level"],
                text=q["text"],
                options=q["options"],
                correct_answer=q["correct_answer"],
                explanation=q["explanation"],
                sort_order=i,
            )
        )
    print(f"  verb_tense_questions: {len(VERB_TENSE_QUESTIONS)} записей")


async def run_seed() -> None:
    print("Перенос данных из /data в БД...")
    async with async_session_maker() as session:
        try:
            await seed_watch_videos(session)
            await seed_positive_feedbacks(session)
            await seed_russian_case_questions(session)
            await seed_russian_tutor_prompts(session)
            await seed_sing_along_songs(session)
            await seed_speech_practice(session)
            await seed_translate_words(session)
            await seed_verb_aspect_questions(session)
            await seed_verb_tense_questions(session)
            await session.commit()
            print("Готово.")
        except Exception as e:
            await session.rollback()
            print(f"Ошибка: {e}", file=sys.stderr)
            raise


def main() -> None:
    asyncio.run(run_seed())


if __name__ == "__main__":
    main()
