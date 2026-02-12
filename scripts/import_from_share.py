"""
Импорт данных из папки, созданной scripts.export_for_share.
Заполняет таблицы контента (files, watch_videos, ...) из JSON.
Папку storage из архива нужно скопировать в свой проект вручную.

Запуск: uv run python -m scripts.import_from_share <путь к export_...>
Пример: uv run python -m scripts.import_from_share ./export_20250108_120000
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import delete

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

# Порядок обратный экспорту: сначала удаляем зависимые, потом файлы
IMPORT_TABLES = [
    (VerbTenseQuestionModel, "verb_tense_questions"),
    (VerbAspectQuestionModel, "verb_aspect_questions"),
    (TranslateWordModel, "translate_words"),
    (TranslateWordCategoryModel, "translate_word_categories"),
    (SpeechPracticeItemModel, "speech_practice_items"),
    (SpeechPracticeCategoryModel, "speech_practice_categories"),
    (SingAlongSongModel, "sing_along_songs"),
    (RussianTutorPromptModel, "russian_tutor_prompts"),
    (RussianCaseQuestionModel, "russian_case_questions"),
    (PositiveFeedbackModel, "positive_feedbacks"),
    (WatchVideoModel, "watch_videos"),
    (FileModel, "files"),
]

# Порядок вставки (сначала файлы, потом остальное)
INSERT_ORDER = [
    (FileModel, "files"),
    (WatchVideoModel, "watch_videos"),
    (PositiveFeedbackModel, "positive_feedbacks"),
    (RussianCaseQuestionModel, "russian_case_questions"),
    (RussianTutorPromptModel, "russian_tutor_prompts"),
    (SingAlongSongModel, "sing_along_songs"),
    (SpeechPracticeCategoryModel, "speech_practice_categories"),
    (SpeechPracticeItemModel, "speech_practice_items"),
    (TranslateWordCategoryModel, "translate_word_categories"),
    (TranslateWordModel, "translate_words"),
    (VerbAspectQuestionModel, "verb_aspect_questions"),
    (VerbTenseQuestionModel, "verb_tense_questions"),
]


async def import_from_folder(export_path: Path) -> None:
    data_dir = export_path / "data"
    if not data_dir.is_dir():
        print(f"Папка data не найдена: {data_dir}")
        sys.exit(1)

    async with async_session_maker() as session:
        # 1. Очистка таблиц (в порядке зависимостей)
        for model, name in IMPORT_TABLES:
            await session.execute(delete(model))
        await session.commit()
        print("Таблицы очищены.")

        # 2. Вставка из JSON (в порядке FK)
        for model, name in INSERT_ORDER:
            path = data_dir / f"{name}.json"
            if not path.exists():
                print(f"  {name}: файл не найден, пропуск")
                continue
            with open(path, encoding="utf-8") as f:
                items = json.load(f)
            if not items:
                print(f"  {name}: 0 записей")
                continue
            for row_dict in items:
                row = model(**row_dict)
                session.add(row)
            await session.flush()
            print(f"  {name}: {len(items)} записей")
        await session.commit()

    print("\nГотово. Скопируйте папку storage из архива в свой проект (в STORAGE_PATH).")


def main() -> None:
    if len(sys.argv) < 2:
        print("Использование: uv run python -m scripts.import_from_share <путь к export_...>")
        sys.exit(1)
    export_path = Path(sys.argv[1]).resolve()
    if not export_path.is_dir():
        print(f"Папка не найдена: {export_path}")
        sys.exit(1)
    asyncio.run(import_from_folder(export_path))


if __name__ == "__main__":
    main()
