import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

print("✅ Бот запущен")

QUESTIONS = [
    {"text": "1. В конце дня ты чаще всего чувствуешь...", "options": [("🧠 Голова гудит, мысли не останавливаются", {"mental": 2}), ("💔 Эмоционально выжата", {"emotional": 2}), ("🔊 Раздражение от шума", {"sensory": 2}), ("🌫️ Скуку и пустоту", {"creative": 2})]},
    {"text": "2. Идеальные выходные...", "options": [("🤫 Тишина и покой", {"mental": 2}), ("💬 Время с близкими", {"emotional": 2}), ("🌿 Природа без телефона", {"sensory": 2}), ("🎨 Заниматься творчеством", {"creative": 2})]},
    {"text": "3. Сложнее всего позволить себе...", "options": [("😌 Просто расслабиться", {"mental": 2}), ("🫂 Показывать свою уязвимость", {"emotional": 2}), ("📱 Не контролировать входящие сообщения на телефоне", {"sensory": 2}), ("⚡ Быть не эффективной", {"creative": 2})]},
    {"text": "4. Без отдыха ты...", "options": [("🌀 Чувствуешь себя рассеянной", {"mental": 2}), ("😭 Плачешь в конце рабочего дня", {"emotional": 2}), ("💢 Чувствуешь напряжение в теле", {"sensory": 2}), ("🕳️ Чувствуешь опустошенность", {"spiritual": 2})]},
    {"text": "5. Последний раз ты чувствовала себя отдохнувшей и удовлетворенной когда...", "options": [("🧘‍♀️ Была наедине с собой", {"mental": 2}), ("💕 Проводила время с близкими", {"emotional": 2}), ("🌲 Отдыхала на природе", {"sensory": 2}), ("🎨 Что-то творила своими руками", {"creative": 2})]},
    {"text": "6. Отдохнуть мешает...", "options": [("💭 Мысли о делах", {"mental": 2}), ("😣 Чувство вины", {"emotional": 2}), ("🔇 Напрягает тишина", {"sensory": 2}), ("🤔 Не знаю, чем хочу заняться", {"spiritual": 2})]},
    {"text": "7. В окружении людей ты...", "options": [("😓 Устаешь и хочешь побыть одна", {"mental": 2}), ("🎭 Держишь лицо и играешь определенную роль", {"emotional": 2}), ("💔 Скучаешь по теплу", {"social": 2}), ("🧸 Чувствуешь себя чужой", {"spiritual": 2})]},
    {"text": "8. Какая фраза про тебя...", "options": [("🔌 Надо выключить голову", {"mental": 2}), ("🫂 Хочу выдохнуть и побыть собой", {"emotional": 2}), ("🏝️ Хочу туда где нет людей", {"sensory": 2}), ("✨ Хочу делать красивое", {"creative": 2})]},
]

RESULTS = {
    "mental": {"title": "🧠 Ментальный отдых", "desc": "Твой мозг перегружен. Нужна пауза без задач.", "tips": ["🚶‍♀️ Прогулка без телефона", "🧘‍♀️ Медитация 5 минут", "🛌 Лечь и ничего не делать", "✨ Рутинная приятная деятельность"]},
    "emotional": {"title": "💖 Эмоциональный отдых", "desc": "Ты долго держишься. Нужно место где можно снять маску.", "tips": ["💬 Разговор о чувствах", "🎬 Фильм который разрешает поплакать", "📔 Дневник без цели", "🧑‍⚕️ Визит к психологу"]},
    "sensory": {"title": "🌿 Сенсорный отдых", "desc": "Органы чувств перегружены. Нужна настоящая тишина.", "tips": ["📵 Час без экранов", "🌲 Природа без наушников", "🛁 Ванна при свечах", "💆‍♀️ Массаж"]},
    "creative": {"title": "🎨 Творческий отдых", "desc": "Давно ничего не делала просто так. Нужна игра.", "tips": ["✏️ Рисовать без цели", "🍳 Готовить новое", "💃 Танцевать дома", "🧶 Лепить или вышивать"]},
    "social": {"title": "👭 Социальный отдых", "desc": "Нужен контакт с людьми которые принимают тебя.", "tips": ["☕ Встреча с подругой", "🍽️ Свидание с партнером вне дома", "🚫 Меньше времени с теми кто забирает энергию", "👥 Сообщество по интересу"]},
    "spiritual": {"title": "🙏 Духовный отдых", "desc": "Потеряла ощущение смысла. Нужно соединение с чем-то большим.", "tips": ["🤫 Время в тишине", "✍️ Записать что важно", "🏡 Отдых в загородном доме или отеле", "🧒 Диалог с внутренним ребенком"]},
}

# ПРЯМАЯ ССЫЛКА НА СТАТЬЮ В TELETYPE
ARTICLE_URL = "https://teletype.in/@ps.darya/sCSxNEl0d-9"

# ТЕКСТ ПРИВЕТСТВИЯ
WELCOME_TEXT = """✨ *Мы все думаем, что умеем отдыхать, пока не сваливаемся с выгоранием.*

Иногда нам нужно просто полежать дома, а иногда — что-то более захватывающее.

Пройди тест и узнай, что нужно именно тебе 💛"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    
    # Логируем нового пользователя
    user = update.effective_user
    user_name = user.first_name or "Без имени"
    user_username = f"@{user.username}" if user.username else "без юзернейма"
    print(f"📊 НОВЫЙ ПОЛЬЗОВАТЕЛЬ: {user_name} ({user_username}) | ID: {user.id}")
    
    keyboard = [[InlineKeyboardButton("🎯 Начать тест", callback_data="start_test")]]
    
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
    
    if data == "start_test":
        context.user_data["scores"] = {k: 0 for k in RESULTS}
        context.user_data["question"] = 0
        print(f"📝 НАЧАЛ ТЕСТ: {user_name} ({user_username})")
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("🌸 *Погнали! 8 вопросов, выбирай честно.*\n\n" + QUESTIONS[0]["text"], 
                                                       reply_markup=get_question_keyboard(0),
                                                       parse_mode="Markdown")
        return
    
    if data.startswith("a"):
        parts = data[1:].split("_")
        qi, oi = int(parts[0]), int(parts[1])
        
        if qi != context.user_data.get("question", 0):
            await update.callback_query.answer("Уже отвечено")
            return
        
        _, sd = QUESTIONS[qi]["options"][oi]
        for k, v in sd.items():
            context.user_data["scores"][k] = context.user_data["scores"].get(k, 0) + v
        
        nq = qi + 1
        context.user_data["question"] = nq
        
        if nq < len(QUESTIONS):
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(
                QUESTIONS[nq]["text"],
                reply_markup=get_question_keyboard(nq)
            )
        else:
            await show_result(update, context)
        return

def get_question_keyboard(q_idx):
    q = QUESTIONS[q_idx]
    keyboard = [[InlineKeyboardButton(t, callback_data="a" + str(q_idx) + "_" + str(i))] for i, (t, _) in enumerate(q["options"])]
    return InlineKeyboardMarkup(keyboard)

async def show_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sc = context.user_data.get("scores", {})
    w = max(sc, key=sc.get)
    r = RESULTS[w]
    tips = "\n".join(t for t in r["tips"])
    
    # Логируем результат
    user = update.effective_user
    user_name = user.first_name or "Без имени"
    user_username = f"@{user.username}" if user.username else "без юзернейма"
    print(f"🎯 ТЕСТ ЗАВЕРШЕН: {user_name} ({user_username}) | РЕЗУЛЬТАТ: {r['title']}")
    
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
        "Эта статья — для тех, кто устал быть «эффективной» и хочет вернуться к себе.\n\n"
        "Внутри — приглашение в группу «Я есть», если захочешь пойти глубже 💛\n\n"
        "Спасибо, что прошла тест!"
    )
    
    keyboard = [
        [InlineKeyboardButton("📖 Читать статью", url=ARTICLE_URL)],
        [InlineKeyboardButton("🔄 Пройти еще раз", callback_data="start_test")]
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
