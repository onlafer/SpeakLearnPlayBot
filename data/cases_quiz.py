CASES_QUESTIONS = [
    # --- Блок 1: Кого? Что? (Direct Object) ---
    {
        "level": "case_block_1",
        "text": "1. Я читаю интересную ... .",
        "options": ["книгой", "книге", "книгу"],
        "correct_answer": "книгу",
        "explanation": {"en": "Accusative feminine singular: 'а' changes to 'у' (книга -> книгу)."}
    },
    {
        "level": "case_block_1",
        "text": "2. Он любит свою ... .",
        "options": ["работу", "работе", "работой"],
        "correct_answer": "работу",
        "explanation": {"en": "Direct object (what?). Feminine singular: работа -> работу."}
    },
    {
        "level": "case_block_1",
        "text": "3. Мы ждём ... .",
        "options": ["гостем", "гостям", "гостей"],
        "correct_answer": "гостей",
        "explanation": {"en": "Direct object (whom?). Animate plural: гости -> гостей (same as Genitive)."}
    },
    {
        "level": "case_block_1",
        "text": "4. Ты видишь этот ... ?",
        "options": ["домой", "дом", "домом"],
        "correct_answer": "дом",
        "explanation": {"en": "Direct object. Inanimate masculine singular does not change (дом = дом)."}
    },
    {
        "level": "case_block_1",
        "text": "5. Дети слушают ... .",
        "options": ["сказку", "сказкой", "сказке"],
        "correct_answer": "сказку",
        "explanation": {"en": "Feminine singular: сказка -> сказку."}
    },
    {
        "level": "case_block_1",
        "text": "6. Он знает этого ... .",
        "options": ["человеком", "человеку", "человека"],
        "correct_answer": "человека",
        "explanation": {"en": "Animate masculine singular: changes like Genitive (человек -> человека)."}
    },
    {
        "level": "case_block_1",
        "text": "7. Она пишет ... .",
        "options": ["письма", "письмо", "письмом"],
        "correct_answer": "письмо",
        "explanation": {"en": "Inanimate neuter singular does not change (письмо = письмо)."}
    },
    {
        "level": "case_block_1",
        "text": "8. Я анализирую ... .",
        "options": ["данные", "данных", "данными"],
        "correct_answer": "данные",
        "explanation": {"en": "Inanimate plural does not change in Accusative (данные = данные)."}
    },
    {
        "level": "case_block_1",
        "text": "9. Мы на вокзале встречаем ... .",
        "options": ["друга", "другу", "другом"],
        "correct_answer": "друга",
        "explanation": {"en": "Animate masculine: друг -> друга."}
    },
    {
        "level": "case_block_1",
        "text": "10. Ты покупаешь новую ... ?",
        "options": ["колбасе", "колбасу", "колбасой"],
        "correct_answer": "колбасу",
        "explanation": {"en": "Feminine singular: колбаса -> колбасу."}
    },

    # --- Блок 2: Куда? (Direction) ---
    {
        "level": "case_block_2",
        "text": "1. Я кладу ключи ... (в + сумка).",
        "options": ["в сумку", "в сумке", "в сумку"], # Исправлено на уникальные
        "correct_answer": "в сумку",
        "explanation": {"en": "Direction (Where to?). 'В' + Accusative feminine: сумка -> сумку."}
    },
    {
        "level": "case_block_2",
        "text": "2. Он переводит текст ... (в + тетрадь).",
        "options": ["в тетрадь", "в тетради", "тетрадь"],
        "correct_answer": "в тетрадь",
        "explanation": {"en": "Direction. Feminine ending in 'ь' does not change in Accusative (тетрадь -> в тетрадь)."}
    },
    {
        "level": "case_block_2",
        "text": "3. Мы покупаем молоко ... (в + магазин).",
        "options": ["в магазин", "в магазине", "магазин"],
        "correct_answer": "в магазин",
        "explanation": {"en": "Motion into a place. Masculine inanimate: магазин -> в магазин."}
    },
    {
        "level": "case_block_2",
        "text": "4. Ты положишь письмо ... (на + стол)?",
        "options": ["на стол", "на столе", "стол"],
        "correct_answer": "на стол",
        "explanation": {"en": "Motion onto a surface. 'На' + Accusative masculine."}
    },
    {
        "level": "case_block_2",
        "text": "5. Она отправляет посылку ... (в + Москва).",
        "options": ["в Москва", "в Москве", "в Москву"],
        "correct_answer": "в Москву",
        "explanation": {"en": "Direction to a city. Feminine: Москва -> в Москву."}
    },
    {
        "level": "case_block_2",
        "text": "6. Мы ставим телевизор ... (в + угол).",
        "options": ["в угол", "в углу", "угол"],
        "correct_answer": "в угол",
        "explanation": {"en": "Direction. Masculine inanimate: угол -> в угол."}
    },
    {
        "level": "case_block_2",
        "text": "7. Я приглашаю друзей ... (в + театр).",
        "options": ["в театр", "в театре", "театр"],
        "correct_answer": "в театр",
        "explanation": {"en": "Direction. Masculine inanimate: театр -> в театр."}
    },
    {
        "level": "case_block_2",
        "text": "8. Ты везешь книги ... (в + библиотека)?",
        "options": ["в библиотека", "в библиотеке", "в библиотеку"],
        "correct_answer": "в библиотеку",
        "explanation": {"en": "Direction. Feminine: библиотека -> в библиотеку."}
    },
    {
        "level": "case_block_2",
        "text": "9. Он посылает документы ... (в + офис).",
        "options": ["в офис", "в офисе", "офис"],
        "correct_answer": "в офис",
        "explanation": {"en": "Direction. Masculine inanimate."}
    },
    {
        "level": "case_block_2",
        "text": "10. Мы кладём газету ... (на + полка).",
        "options": ["на полка", "на полке", "на полку"],
        "correct_answer": "на полку",
        "explanation": {"en": "Direction onto surface. Feminine: полка -> на полку."}
    },

    # --- Блок 3: Когда? (Time) ---
    {
        "level": "case_block_3",
        "text": "1. Я изучаю новые слова ... .",
        "options": ["каждый вечер", "каждым вечером", "каждого вечера"],
        "correct_answer": "каждый вечер",
        "explanation": {"en": "Frequency. 'Каждый' + Accusative masculine (вечер is inanimate)."}
    },
    {
        "level": "case_block_3",
        "text": "2. Мы слушаем радио ... .",
        "options": ["каждое утро", "каждым утром", "каждого утра"],
        "correct_answer": "каждое утро",
        "explanation": {"en": "Frequency. 'Каждое' + Accusative neuter (утро)."}
    },
    {
        "level": "case_block_3",
        "text": "3. Ты читаешь газету ... ?",
        "options": ["каждую субботу", "каждой субботой", "каждой субботы"],
        "correct_answer": "каждую субботу",
        "explanation": {"en": "Frequency. 'Каждую' + Accusative feminine (суббота -> субботу)."}
    },
    {
        "level": "case_block_3",
        "text": "4. Он получает письмо ... .",
        "options": ["каждый понедельник", "каждым понедельником", "каждого понедельника"],
        "correct_answer": "каждый понедельник",
        "explanation": {"en": "Frequency. Masculine inanimate."}
    },
    {
        "level": "case_block_3",
        "text": "5. Я готовлю ужин ... .",
        "options": ["каждый день", "каждым днём", "каждого дня"],
        "correct_answer": "каждый день",
        "explanation": {"en": "Frequency. Masculine inanimate."}
    },
    
    # --- Блок 4: Похож на (Similar to) ---
    {
        "level": "case_block_4",
        "text": "1. Этот твой друг похож на ... из моего двора.",
        "options": ["сосед", "соседе", "соседа"],
        "correct_answer": "соседа",
        "explanation": {"en": "'Похож на' requires Accusative. Animate masculine: сосед -> соседа."}
    },
    {
        "level": "case_block_4",
        "text": "2. Новая песня очень похожа на ... из детства.",
        "options": ["старая песня", "старой песне", "старую песню"],
        "correct_answer": "старую песню",
        "explanation": {"en": "'Похожа на' + Accusative feminine: старую песню."}
    },
    {
        "level": "case_block_4",
        "text": "5. Внук очень похож на своего ... .",
        "options": ["дедушка", "дедушке", "дедушку"],
        "correct_answer": "дедушку",
        "explanation": {"en": "'Похож на' + Accusative. Дедушка (Grandfather) is grammatically feminine/masculine but ends in 'а', so it changes to 'у' (дедушку)."}
    },

    # --- Блок 5: Прилагательные (Adjectives) ---
    {
        "level": "case_block_5",
        "text": "1. Я ищу ... .",
        "options": ["свой чёрный портфель", "своего чёрного портфеля", "своём чёрном портфеле"],
        "correct_answer": "свой чёрный портфель",
        "explanation": {"en": "Direct object. Inanimate masculine adjectives do not change."}
    },
    {
        "level": "case_block_5",
        "text": "5. Она ждёт ... .",
        "options": ["наш китайский гость", "нашего китайского гостя", "нашем китайском госте"],
        "correct_answer": "нашего китайского гостя",
        "explanation": {"en": "Direct object. Animate masculine: Adjectives take Genitive endings (-ого/-его)."}
    },
    {
        "level": "case_block_5",
        "text": "6. Мы читаем ... .",
        "options": ["интересная книга", "интересной книги", "интересную книгу"],
        "correct_answer": "интересную книгу",
        "explanation": {"en": "Direct object. Feminine adjectives change -ая to -ую."}
    }
]
