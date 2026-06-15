import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

print("✅ Бот запущен")

QUESTIONS = [
    {"text": "1️⃣ В конце дня ты чаще всего чувствуешь...", "options": [("🧠 Голова гудит, мысли не останавливаются", {"mental": 2}), ("💔 Эмоционально выжата", {"emotional": 2}), ("🔊 Раздражение от шума", {"sensory": 2}), ("🌫️ Скуку и пустоту", {"creative": 2})]},
    {"text": "2️⃣ Идеальные выходные...", "options": [("🤫 Тишина и покой", {"mental": 2}), ("💬 Разговор с близким", {"emotional": 2}), ("🌿 Природа без телефона", {"sensory": 2}), ("🎨 Творить руками", {"creative": 2})]},
    {"text": "3️⃣ Сложнее всего позволить себе...", "options": [("🪑 Просто сидеть и молчать", {"mental": 2}), ("😢 Показать слабость", {"emotional": 2}), ("📵 Выключить телефон", {"sensory": 2}), ("🎭 Делать бесполезное", {"creative": 2})]},
    {"text": "4️⃣ Без отдыха это проявляется как...", "options": [("🌀 Рассеянность", {"mental": 2}), ("😭 Слёзы на ровном месте", {"emotional": 2}), ("💢 Напряжение в теле", {"sensory": 2}), ("🕳️ Пустота внутри", {"spiritual": 2})]},
    {"text": "5️⃣ Последний раз чувствовала себя живой когда...", "options": [("🌙 Побыла в тишине", {"mental": 2}), ("💞 Говорила с близким", {"emotional": 2}), ("🏔️ Была на природе", {"sensory": 2}), ("🎨 Что-то создавала", {"creative": 2})]},
    {"text": "6️⃣ Отдохнуть мешает...", "options": [("📋 Мысли о делах", {"mental": 2}), ("😔 Чувство вины", {"emotional": 2}), ("🔇 Не могу вынести тишину", {"sensory": 2}), ("❓ Не знаю что нравится", {"spiritual": 2})]},
    {"text": "7️⃣ В окружении людей...", "options": [("🏠 Устаю, хочу одна", {"mental": 2}), ("🎭 Держу маску", {"emotional": 2}), ("🤝 Скучаю по теплу", {"social": 2}), ("👽 Чувствую себя чужой", {"spiritual": 2})]},
    {"text": "8️⃣ Какая фраза про тебя...", "options": [("🔌 Надо выключить голову", {"mental": 2}), ("🫂 Хочу выдохнуть и побыть собой", {"emotional": 2}), ("🏝️ Хочу туда где нет людей", {"sensory": 2}), ("✨ Хочу делать красивое", {"creative": 2})]},
]

RESULTS = {
    "mental": {"title": "🧠 Ментальный отдых", "desc": "Твой мозг перегружен. Нужна пауза без задач.", "emoji": "📚", "tips": ["🚶‍♀️ Прогулка без телефона", "🧘‍♀️ Медитация 5 минут", "🛌 Лечь и ничего не делать", "📰 Новости раз в день"]},
    "emotional": {"title": "💖 Эмоциональный отдых", "desc": "Ты долго держишься. Нужно место где можно снять маску.", "emoji": "🎭", "tips": ["💬 Разговор о чувствах", "🎬 Фильм который разрешает поплакать", "📔 Дневник без цели", "😌 Время без маски"]},
    "sensory": {"title": "🌿 Сенсорный отдых", "desc": "Органы чувств перегружены. Нужна настоящая тишина.", "emoji": "🕯️", "tips": ["📵 Час без экранов", "🌲 Природа без наушников", "🛁 Ванна при свечах", "💆‍♀️ Массаж"]},
    "creative": {"title": "🎨 Творческий отдых", "desc": "Давно ничего не делала просто так. Нужна игра.", "emoji": "🖌️", "tips": ["✏️ Рисовать без цели", "🍳 Готовить новое", "💃 Танцевать дома", "🧶 Лепить или вышивать"]},
    "social": {"title": "👭 Социальный отдых", "desc": "Нужен контакт с людьми которые принимают тебя.", "emoji": "💞", "tips": ["☕ Встреча с подругой", "📞 Позвонить близкому", "🚫 Меньше времени с теми кто забирает энергию", "👥 Сообщество по интересу"]},
    "spiritual": {"title": "🙏 Духовный отдых", "desc": "Потеряла ощущение смысла. Нужно соединение с чем-то большим.", "emoji": "🌅", "tips": ["🤫 Время в тишине", "✍️ Записать что важно", "🌳 Природа", "🤲 Помочь кому-то"]},
}

# ССЫЛКА НА АНКЕТУ ПРЕДЗАПИСИ
SURVEY_URL = "https://docs.google.com/forms/d/e/1FAIpQLSdGGevDQLwvd46EtPyT50pCAQUo0OXdr-PH9SfQ3NG6IVXnIA/viewform?usp=sharing&ouid=109680719714569214826"

# ТЕКСТ ПРИВЕТСТВИЯ
WELCOME_TEXT = """✨ *Мы все думаем, что умеем отдыхать, пока не сваливаемся с выгоранием.*

Иногда нам нужно просто полежать дома, а иногда — что-то более захватывающее.

Пройди тест и узнай, что нужно именно тебе 💛"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    
    keyboard = [[InlineKeyboardButton("🎯 Начать тест", callback_data="start_test")]]
    
    await update.message.reply_text(
        WELCOME_TEXT,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.callback_query.data
    
    if data == "start_test":
        context.user_data["scores"] = {k: 0 for k in RESULTS}
        context.user_data["question"] = 0
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("🌸 *Погнали! 8 вопросов, выбирай честно.*\n\n" + QUESTIONS[0]["text"], 
                                                       reply_markup=get_question_keyboard(0, 0),
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
                reply_markup=get_question_keyboard(nq, 0)
            )
        else:
            await show_result(update, context)
        return

def get_question_keyboard(q_idx, _):
    q = QUESTIONS[q_idx]
    keyboard = [[InlineKeyboardButton(t, callback_data="a" + str(q_idx) + "_" + str(i))] for i, (t, _) in enumerate(q["options"])]
    return InlineKeyboardMarkup(keyboard)

async def show_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sc = context.user_data.get("scores", {})
    w = max(sc, key=sc.get)
    r = RESULTS[w]
    tips = "\n".join(t for t in r["tips"])
    
    text = (
        "🏆 *Тест завершен!*\n\n"
        f"✨ *Тебе нужен:* *{r['title']}*\n\n"
        f"{r['desc']}\n\n"
        f"💡 *С чего начать:*\n{tips}\n\n"
        "🌸 *Приглашение в группу «Я есть»*\n\n"
        "Если для тебя проблема трудоголизма и тревожной эффективности особенно актуальна, "
        "приглашаю тебя в группу «Я есть», которая будет стартовать в сентябре, "
        "где будем исследовать твои потребности помимо работы и разъединять цепочку «Я = Мои достижения».\n\n"
        "📝 *Заполни анкету предзаписи, и я свяжусь с тобой:*\n"
        f"[Открыть анкету]({SURVEY_URL})\n\n"
        "💛 Спасибо, что прошла тест!"
    )
    
    keyboard = [[InlineKeyboardButton("🔄 Пройти еще раз", callback_data="start_test")]]
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text=text, 
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
        disable_web_page_preview=True
    )

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    print("🚀 Бот запущен и готов к работе")
    app.run_polling()

if __name__ == "__main__":
    main()
