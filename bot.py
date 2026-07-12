import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

print("✅ Бот запущен")

# ===================== ТЕСТ 1: ТИП ОТДЫХА =====================
QUESTIONS_REST = [
    {"text": "1. В конце дня ты чаще всего чувствуешь...", "options": [("🧠 Голова гудит, мысли не останавливаются", {"mental": 2}), ("💔 Эмоционально выжата", {"emotional": 2}), ("🔊 Раздражение от шума", {"sensory": 2}), ("🌫️ Скуку и пустоту", {"creative": 2})]},
    {"text": "2. Идеальные выходные...", "options": [("🤫 Тишина и покой", {"mental": 2}), ("💬 Время с близкими", {"emotional": 2}), ("🌿 Природа без телефона", {"sensory": 2}), ("🎨 Заниматься творчеством", {"creative": 2})]},
    {"text": "3. Сложнее всего позволить себе...", "options": [("😌 Просто расслабиться", {"mental": 2}), ("🫂 Показывать свою уязвимость", {"emotional": 2}), ("📱 Не контролировать входящие сообщения на телефоне", {"sensory": 2}), ("⚡ Быть не эффективной", {"creative": 2})]},
    {"text": "4. Без отдыха ты...", "options": [("🌀 Чувствуешь себя рассеянной", {"mental": 2}), ("😭 Плачешь в конце рабочего дня", {"emotional": 2}), ("💢 Чувствуешь напряжение в теле", {"sensory": 2}), ("🕳️ Чувствуешь опустошенность", {"spiritual": 2})]},
    {"text": "5. Последний раз ты чувствовала себя отдохнувшей и удовлетворенной когда...", "options": [("🧘‍♀️ Была наедине с собой", {"mental": 2}), ("💕 Проводила время с близкими", {"emotional": 2}), ("🌲 Отдыхала на природе", {"sensory": 2}), ("🎨 Что-то творила своими руками", {"creative": 2})]},
    {"text": "6. Отдохнуть мешает...", "options": [("💭 Мысли о делах", {"mental": 2}), ("😣 Чувство вины", {"emotional": 2}), ("🔇 Напрягает тишина", {"sensory": 2}), ("🤔 Не знаю, чем хочу заняться", {"spiritual": 2})]},
    {"text": "7. В окружении людей ты...", "options": [("😓 Устаешь и хочешь побыть одна", {"mental": 2}), ("🎭 Держишь лицо и играешь определенную роль", {"emotional": 2}), ("💔 Скучаешь по теплу", {"social": 2}), ("🧸 Чувствуешь себя чужой", {"spiritual": 2})]},
    {"text": "8. Какая фраза про тебя...", "options": [("🔌 Надо выключить голову", {"mental": 2}), ("🫂 Хочу выдохнуть и побыть собой", {"emotional": 2}), ("🏝️ Хочу туда где нет людей", {"sensory": 2}), ("✨ Хочу делать красивое", {"creative": 2})]},
]

RESULTS_REST = {
    "mental": {"title": "🧠 Ментальный отдых", "desc": "Твой мозг перегружен. Нужна пауза без задач.", "tips": ["🚶‍♀️ Прогулка без телефона", "🧘‍♀️ Медитация 5 минут", "🛌 Лечь и ничего не делать", "✨ Рутинная приятная деятельность"]},
    "emotional": {"title": "💖 Эмоциональный отдых", "desc": "Ты долго держишься. Нужно место где можно снять маску.", "tips": ["💬 Разговор о чувствах", "🎬 Фильм который разрешает поплакать", "📔 Дневник без цели", "🧑‍⚕️ Визит к психологу"]},
    "sensory": {"title": "🌿 Сенсорный отдых", "desc": "Органы чувств перегружены. Нужна настоящая тишина.", "tips": ["📵 Час без экранов", "🌲 Природа без наушников", "🛁 Ванна при свечах", "💆‍♀️ Массаж"]},
    "creative": {"title": "🎨 Творческий отдых", "desc": "Давно ничего не делала просто так. Нужна игра.", "tips": ["✏️ Рисовать без цели", "🍳 Готовить новое", "💃 Танцевать дома", "🧶 Лепить или вышивать"]},
    "social": {"title": "👭 Социальный отдых", "desc": "Нужен контакт с людьми которые принимают тебя.", "tips": ["☕ Встреча с подругой", "🍽️ Свидание с партнером вне дома", "🚫 Меньше времени с теми кто забирает энергию", "👥 Сообщество по интересу"]},
    "spiritual": {"title": "🙏 Духовный отдых", "desc": "Потеряла ощущение смысла. Нужно соединение с чем-то большим.", "tips": ["🤫 Время в тишине", "✍️ Записать что важно", "🏡 Отдых в загородном доме или отеле", "🧒 Диалог с внутренним ребенком"]},
}

# ===================== ТЕСТ 2: ВЫГОРАНИЕ =====================
QUESTIONS_BURNOUT = [
    {"text": "1. Как часто ты говоришь фразу «Я просто хочу лечь и ничего не делать»?", "options": [("☕ Постоянно, и это не шутка", 3), ("🧠 Часто, но думаю, что это лень", 2), ("🤷‍♀️ Иногда, когда выпадаю из режима", 1), ("🚀 Редко, у меня всё под контролем", 0)]},
    {"text": "2. Твой выходной — это:", "options": [("📱 Спать до обеда и листать телефон", 2), ("📋 Список дел, которые не успела на неделе", 3), ("🌿 Найти час на себя и чувствовать вину", 2), ("🎯 Ничего не планировать — и кайфовать", 0)]},
    {"text": "3. Когда кто-то говорит «Ты слишком много работаешь», ты:", "options": [("😤 Раздражаюсь — никто не понимает", 3), ("😅 Смеюсь и перевожу тему", 2), ("😔 Грустно соглашаюсь, но ничего не меняю", 1), ("🧐 Задумываюсь и проверяю, правда ли это", 0)]},
    {"text": "4. Последний раз ты чувствовала радость, когда:", "options": [("🤗 Общалась с близкими", 0), ("🎉 Сделала что-то, что давно откладывала", 1), ("😌 Позволила себе просто быть", 0), ("😶 Уже не помню", 3)]},
    {"text": "5. Ты просыпаешься утром с мыслью:", "options": [("🔥 «Скорее вставать, нужно успеть всё!»", 3), ("😮‍💨 «Опять этот день...»", 2), ("☀️ «Посмотрю, что принесёт новый день»", 0), ("🤯 «Что я вообще делаю?»", 3)]},
    {"text": "6. Как ты справляешься с тревогой?", "options": [("📋 Планирую — так спокойнее", 2), ("🎬 Смотрю сериалы / скроллю соцсети", 1), ("💬 Говорю с близкими", 0), ("🙅‍♀️ Не справляюсь — она всегда со мной", 3)]},
    {"text": "7. Какая фраза звучит в твоей голове чаще всего?", "options": [("💔 «Я должна быть сильной»", 2), ("💭 «Мне нужен отдых, но я не могу остановиться»", 3), ("😔 «Меня никто не понимает»", 2), ("🌟 «Я справлюсь, всё будет хорошо»", 0)]},
]

RESULTS_BURNOUT = [
    {"min": 0, "max": 4, "title": "🌟 Ты в ресурсе", "desc": "Ты умеешь отдыхать и заботиться о себе. Продолжай в том же духе! Но не расслабляйся — выгорание наступает незаметно."},
    {"min": 5, "max": 10, "title": "⚠️ Звоночки", "desc": "Ты уже чувствуешь усталость и иногда теряешь радость. Самое время начать обращать внимание на себя и свои потребности."},
    {"min": 11, "max": 16, "title": "🔥 Высокий уровень выгорания", "desc": "Ты на пределе. Твоя нервная система истощена. Пора действовать. Обратись к психологу или начни работать с собой в группе «Я есть»."},
    {"min": 17, "max": 21, "title": "🚨 Критический уровень", "desc": "Ты давно не чувствуешь себя собой. Твоё тело и психика кричат о помощи. Пожалуйста, обратись к специалисту. Ты не одна. Есть выход."},
]

ARTICLE_URL = "https://bit.ly/4aAONAj"

WELCOME_TEXT = """✨ *Мы все думаем, что умеем отдыхать, пока не сваливаемся с выгоранием.*

Выбери тест:

🧠 *Какой тип отдыха подходит именно тебе?*
🔥 *Тест на выгорание*"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    user = update.effective_user
    user_name = user.first_name or "Без имени"
    user_username = f"@{user.username}" if user.username else "без юзернейма"
    print(f"📊 НОВЫЙ ПОЛЬЗОВАТЕЛЬ: {user_name} ({user_username}) | ID: {user.id}")
    
    keyboard = [
        [InlineKeyboardButton("🧠 Тест на тип отдыха", callback_data="start_rest")],
        [InlineKeyboardButton("🔥 Тест на выгорание", callback_data="start_burnout")],
    ]
    
    await update.message.reply_text(
        WELCOME_TEXT,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.callback_query.data
    user = update.effective_user
    user_name = user.first_name or "Без имени"
    user_username = f"@{user.username}" if user.username else "без юзернейма"
    
    if data == "start_rest":
        context.user_data["test_type"] = "rest"
        context.user_data["scores"] = {k: 0 for k in RESULTS_REST}
        context.user_data["question"] = 0
        print(f"📝 НАЧАЛ ТЕСТ: {user_name} ({user_username}) - ТЕСТ: Тип отдыха")
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "🌸 *Тест на тип отдыха! 8 вопросов, выбирай честно.*\n\n" + QUESTIONS_REST[0]["text"],
            reply_markup=get_question_keyboard_rest(0),
            parse_mode="Markdown"
        )
        return
    
    if data == "start_burnout":
        context.user_data["test_type"] = "burnout"
        context.user_data["scores"] = 0
        context.user_data["question"] = 0
        print(f"📝 НАЧАЛ ТЕСТ: {user_name} ({user_username}) - ТЕСТ: Выгорание")
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "🔥 *Тест на выгорание! 7 вопросов, отвечай честно.*\n\n" + QUESTIONS_BURNOUT[0]["text"],
            reply_markup=get_question_keyboard_burnout(0),
            parse_mode="Markdown"
        )
        return
    
    if data.startswith("rest_"):
        parts = data[5:].split("_")
        qi, oi = int(parts[0]), int(parts[1])
        if qi != context.user_data.get("question", 0):
            await update.callback_query.answer("Уже отвечено")
            return
        _, sd = QUESTIONS_REST[qi]["options"][oi]
        for k, v in sd.items():
            context.user_data["scores"][k] = context.user_data["scores"].get(k, 0) + v
        nq = qi + 1
        context.user_data["question"] = nq
        if nq < len(QUESTIONS_REST):
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(
                QUESTIONS_REST[nq]["text"],
                reply_markup=get_question_keyboard_rest(nq)
            )
        else:
            await show_result_rest(update, context)
        return
    
    if data.startswith("burn_"):
        parts = data[5:].split("_")
        qi, oi = int(parts[0]), int(parts[1])
        if qi != context.user_data.get("question", 0):
            await update.callback_query.answer("Уже отвечено")
            return
        _, score = QUESTIONS_BURNOUT[qi]["options"][oi]
        context.user_data["scores"] += score
        nq = qi + 1
        context.user_data["question"] = nq
        if nq < len(QUESTIONS_BURNOUT):
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(
                QUESTIONS_BURNOUT[nq]["text"],
                reply_markup=get_question_keyboard_burnout(nq)
            )
        else:
            await show_result_burnout(update, context)
        return

def get_question_keyboard_rest(q_idx):
    q = QUESTIONS_REST[q_idx]
    keyboard = [[InlineKeyboardButton(t, callback_data="rest_" + str(q_idx) + "_" + str(i))] for i, (t, _) in enumerate(q["options"])]
    return InlineKeyboardMarkup(keyboard)

def get_question_keyboard_burnout(q_idx):
    q = QUESTIONS_BURNOUT[q_idx]
    keyboard = [[InlineKeyboardButton(t, callback_data="burn_" + str(q_idx) + "_" + str(i))] for i, (t, _) in enumerate(q["options"])]
    return InlineKeyboardMarkup(keyboard)

async def show_result_rest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sc = context.user_data.get("scores", {})
    w = max(sc, key=sc.get)
    r = RESULTS_REST[w]
    tips = "\n".join(t for t in r["tips"])
    
    user = update.effective_user
    user_name = user.first_name or "Без имени"
    user_username = f"@{user.username}" if user.username else "без юзернейма"
    print(f"🎯 ТЕСТ ЗАВЕРШЕН: {user_name} ({user_username}) - ТЕСТ: Тип отдыха | РЕЗУЛЬТАТ: {r['title']}")
    
    text = (
        "🏆 *Тест завершен!*\n\n"
        f"✨ *Тебе нужен:* *{r['title']}*\n\n"
        f"{r['desc']}\n\n"
        f"💡 *С чего начать:*\n{tips}\n\n"
        "🌱 *Статья для тебя*\n\n"
        "Я написала текст о том, как мы привыкаем работать, "
        "пока не перестаём замечать себя. О том, как разрешить себе "
        "остановиться и не чувствовать вину.\n\n"
        "В статье есть 2 упражнения, которые помогут начать отдыхать без тревоги 🎁\n\n"
        "Внутри — приглашение в группу «Я есть», если захочешь пойти глубже 💛\n\n"
        "Спасибо, что прошла тест!"
    )
    
    keyboard = [
        [InlineKeyboardButton("📖 Читать статью", url=ARTICLE_URL)],
        [InlineKeyboardButton("🔄 Пройти тест заново", callback_data="start_rest")],
        [InlineKeyboardButton("🔄 Пройти другой тест", callback_data="start_burnout")]
    ]
    
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
        disable_web_page_preview=False
    )

async def show_result_burnout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    score = context.user_data.get("scores", 0)
    result = None
    for r in RESULTS_BURNOUT:
        if r["min"] <= score <= r["max"]:
            result = r
            break
    
    user = update.effective_user
    user_name = user.first_name or "Без имени"
    user_username = f"@{user.username}" if user.username else "без юзернейма"
    print(f"🎯 ТЕСТ ЗАВЕРШЕН: {user_name} ({user_username}) - ТЕСТ: Выгорание | РЕЗУЛЬТАТ: {result['title']} (баллы: {score})")
    
    text = (
        "🏆 *Тест завершен!*\n\n"
        f"📊 *Твой результат:* *{result['title']}*\n\n"
        f"{result['desc']}\n\n"
        "🌱 *Статья для тебя*\n\n"
        "Я написала текст о том, как мы привыкаем работать, "
        "пока не перестаём замечать себя. О том, как разрешить себе "
        "остановиться и не чувствовать вину.\n\n"
        "В статье есть 2 упражнения, которые помогут начать отдыхать без тревоги 🎁\n\n"
        "Внутри — приглашение в группу «Я есть», если захочешь пойти глубже 💛\n\n"
        "Спасибо, что прошла тест!"
    )
    
    keyboard = [
        [InlineKeyboardButton("📖 Читать статью", url=ARTICLE_URL)],
        [InlineKeyboardButton("🔄 Пройти тест заново", callback_data="start_burnout")],
        [InlineKeyboardButton("🔄 Пройти другой тест", callback_data="start_rest")]
    ]
    
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
        disable_web_page_preview=False
    )

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    print("🚀 Бот запущен и готов к работе")
    app.run_polling()

if __name__ == "__main__":
    main()
