import os 
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

import os
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    print("ОШИБКА: Токен не найден в переменных окружения!")
    exit(1)
print("Токен загружен успешно")

QUESTIONS = [
    {"text": "1. В конце дня ты чаще всего чувствуешь...", "options": [("Голова гудит, мысли не останавливаются", {"mental": 2}), ("Эмоционально выжата", {"emotional": 2}), ("Раздражение от шума", {"sensory": 2}), ("Скуку и пустоту", {"creative": 2})]},
    {"text": "2. Идеальные выходные...", "options": [("Тишина и покой", {"mental": 2}), ("Разговор с близким", {"emotional": 2}), ("Природа без телефона", {"sensory": 2}), ("Творить руками", {"creative": 2})]},
    {"text": "3. Сложнее всего позволить себе...", "options": [("Просто сидеть и молчать", {"mental": 2}), ("Показать слабость", {"emotional": 2}), ("Выключить телефон", {"sensory": 2}), ("Делать бесполезное", {"creative": 2})]},
    {"text": "4. Без отдыха это проявляется как...", "options": [("Рассеянность", {"mental": 2}), ("Слезы на ровном месте", {"emotional": 2}), ("Напряжение в теле", {"sensory": 2}), ("Пустота внутри", {"spiritual": 2})]},
    {"text": "5. Последний раз чувствовала себя живой когда...", "options": [("Побыла в тишине", {"mental": 2}), ("Говорила с близким", {"emotional": 2}), ("Была на природе", {"sensory": 2}), ("Что-то создавала", {"creative": 2})]},
    {"text": "6. Отдохнуть мешает...", "options": [("Мысли о делах", {"mental": 2}), ("Чувство вины", {"emotional": 2}), ("Не могу вынести тишину", {"sensory": 2}), ("Не знаю что нравится", {"spiritual": 2})]},
    {"text": "7. В окружении людей...", "options": [("Устаю, хочу одна", {"mental": 2}), ("Держу маску", {"emotional": 2}), ("Скучаю по теплу", {"social": 2}), ("Чувствую себя чужой", {"spiritual": 2})]},
    {"text": "8. Какая фраза про тебя...", "options": [("Надо выключить голову", {"mental": 2}), ("Хочу выдохнуть и побыть собой", {"emotional": 2}), ("Хочу туда где нет людей", {"sensory": 2}), ("Хочу делать красивое", {"creative": 2})]},
]

RESULTS = {
    "mental": {"title": "Ментальный отдых", "desc": "Твой мозг перегружен. Нужна пауза без задач.", "tips": ["Прогулка без телефона", "Медитация 5 минут", "Лечь и ничего не делать", "Новости раз в день"]},
    "emotional": {"title": "Эмоциональный отдых", "desc": "Ты долго держишься. Нужно место где можно снять маску.", "tips": ["Разговор о чувствах", "Фильм который разрешает поплакать", "Дневник без цели", "Время без маски"]},
    "sensory": {"title": "Сенсорный отдых", "desc": "Органы чувств перегружены. Нужна настоящая тишина.", "tips": ["Час без экранов", "Природа без наушников", "Ванна при свечах", "Массаж"]},
    "creative": {"title": "Творческий отдых", "desc": "Давно ничего не делала просто так. Нужна игра.", "tips": ["Рисовать без цели", "Готовить новое", "Танцевать дома", "Лепить или вышивать"]},
    "social": {"title": "Социальный отдых", "desc": "Нужен контакт с людьми которые принимают тебя.", "tips": ["Встреча с подругой", "Позвонить близкому", "Меньше времени с теми кто забирает энергию", "Сообщество по интересу"]},
    "spiritual": {"title": "Духовный отдых", "desc": "Потеряла ощущение смысла. Нужно соединение с чем-то большим.", "tips": ["Время в тишине", "Записать что важно", "Природа", "Помочь кому-то"]},
}

CONSENT = "Прежде чем начать, мне нужно твое согласие. Я собираю обезличенные данные о результатах теста. Личные данные не сохраняются."

async def start(update, context):
    context.user_data.clear()
    keyboard = [[InlineKeyboardButton("Согласна", callback_data="cy")], [InlineKeyboardButton("Не согласна", callback_data="cn")]]
    await update.message.reply_text(CONSENT, reply_markup=InlineKeyboardMarkup(keyboard))

async def send_question(update, context):
    q_idx = context.user_data.get("question", 0)
    q = QUESTIONS[q_idx]
    keyboard = [[InlineKeyboardButton(t, callback_data="a" + str(q_idx) + "_" + str(i))] for i, (t, _) in enumerate(q["options"])]
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=q["text"], reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_answer(update, context):
    data = update.callback_query.data
    if data == "cy":
        context.user_data["scores"] = {k: 0 for k in RESULTS}
        context.user_data["question"] = 0
        keyboard = [[InlineKeyboardButton("Начать тест", callback_data="sq")]]
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("Отлично! 8 вопросов, выбирай честно. Готова?", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    if data == "cn":
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("Хорошо. Если передумаешь напиши /start")
        return
    if data == "sq":
        context.user_data["scores"] = {k: 0 for k in RESULTS}
        context.user_data["question"] = 0
        await send_question(update, context)
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
            await send_question(update, context)
        else:
            await show_result(update, context)

async def show_result(update, context):
    sc = context.user_data.get("scores", {})
    w = max(sc, key=sc.get)
    r = RESULTS[w]
    tips = "\n".join("- " + t for t in r["tips"])
    text = "Тест завершен!\n\nТебе нужен: " + r["title"] + "\n\n" + r["desc"] + "\n\nС чего начать:\n" + tips
    keyboard = [[InlineKeyboardButton("Пройти еще раз", callback_data="sq")]]
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_answer))
    print("Бот запущен")
    app.run_polling()

if __name__ == "__main__":
    main()
