import os
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, PreCheckoutQueryHandler, MessageHandler, filters

# Настройка логирования для Railway
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ========== ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ ==========
BOT_TOKEN = os.getenv("BOT_TOKEN")
PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN")

if not BOT_TOKEN:
    logger.critical("❌ ОШИБКА: BOT_TOKEN не найден в переменных окружения!")
    exit(1)

logger.info("✅ Бот запущен")
logger.info("🛒 PAYMENT_PROVIDER_TOKEN: " + ("Установлен" if PAYMENT_PROVIDER_TOKEN else "НЕ УСТАНОВЛЕН (оплата работать не будет)"))

# ===================== ТЕСТ: ТИП ОТДЫХА =====================
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

ARTICLE_URL = "https://teletype.in/@ps.darya/sCSxNEl0d-9"

# ===================== ПРОМТ МЕНТАЛЬНЫЙ ПОМОЩНИК =====================
PROMPT_DESCRIPTION = """
🤖 *Промт «Ментальный помощник»*

Это не просто промт. Это инструкция для твоего ИИ — быть твоим ментальным ассистентом.

Я обучила его не шаблонным фразам «отдохни» и «будь позитивнее», а реальным психологическим практикам, которые использую со своими клиентами.

*Что он умеет:*

🎯 Движение к целям без выгорания — разобрать, чья это цель, и найти шаг без надрыва

💛 Слова поддержки для каждого дня — по одной фразе, сколько нужно

😴 Микроотдых в моменте — тест из 4 вопросов и подбор отдыха под состояние

🌙 Вечерняя рефлексия — 3 вопроса, чтобы завершить день с опорой

🧠 Работа с тревогой здесь и сейчас — 7 вопросов, чтобы разобрать тревогу и найти опору

Копируешь, вставляешь в любой ИИ — и готово.

Оплата одноразовая. Без подписки.

💰 *Стоимость:* 1599 ₽ / $20

📄 [Ознакомиться с договором оферты](https://docs.google.com/document/d/144wZHLVpBC5VPDbo2oudvVaVZt3B-thGIqQieg5jNC8/edit?usp=drivesdk)
"""

PROMPT_FULL = """Ты — мой личный ментальный ассистент. Твоя задача — заботиться о моём состоянии в моменте. Ты не психотерапевт, ты — поддерживающий инструмент самопомощи.

Твои принципы:
— Ты никогда не говоришь «ты должна», «тебе нужно». Ты говоришь мягко: «возможно», «попробуй», «если хочешь».
— Ты не даёшь жёстких диагнозов и предписаний.
— Ты всегда сначала уточняешь моё состояние, а потом предлагаешь варианты.

Сразу после этого сообщения покажи меню из 5 пунктов с превью. Вот они — скопируй их в точности:

🎯 1 — Движение к целям без выгорания
→ Сюда, когда хочешь идти к мечте, но без надрыва и насилия над собой

💛 2 — Слова поддержки для каждого дня
→ Сюда, когда тебя некому поддержать, а внутри неуверенность

😴 3 — Микроотдых в моменте  
→ Сюда, когда ты устала, нет сил, но времени на большой отдых нет

🌙 4 — Вечерняя рефлексия
→ Сюда, чтобы завершить день с опорой и осознанностью

🧠 5 — Работа с тревогой здесь и сейчас
→ Сюда, когда тревожно, страшно, мысли бегут, а ты не знаешь, что делать

После этого напиши: "Выбери номер (1–5) — и я начну работать".

НЕ используй "✅". Используй только эти эмодзи: 🎯 💛 😴 🌙 🧠

Теперь алгоритмы по каждой вкладке:

[ВСТАВЬ СЮДА ПОЛНЫЙ ТЕКСТ АЛГОРИТМОВ ДЛЯ ВСЕХ 5 ВКЛАДОК]
"""

# ===================== ПРИВЕТСТВИЕ =====================
WELCOME_TEXT = """👋 *Привет! На связи бот психолога Дарьи.*

🧠 *Тест на тип отдыха* — узнай, что нужно именно тебе
🤖 *Промт «Ментальный помощник»* — готовый инструмент для самоподдержки (1599 ₽)"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    user = update.effective_user
    user_name = user.first_name or "Без имени"
    user_username = f"@{user.username}" if user.username else "без юзернейма"
    logger.info(f"📊 НОВЫЙ ПОЛЬЗОВАТЕЛЬ: {user_name} ({user_username}) | ID: {user.id}")

    keyboard = [
        [InlineKeyboardButton("🧠 Тест на тип отдыха", callback_data="start_rest")],
        [InlineKeyboardButton("🤖 Промт «Ментальный помощник»", callback_data="show_prompt")]
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

    # ===== ПОКАЗАТЬ ОПИСАНИЕ ПРОМТА =====
    if data == "show_prompt":
        keyboard = [[InlineKeyboardButton("💳 Купить 1599 ₽", callback_data="start_payment")]]
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            PROMPT_DESCRIPTION,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
        return

    # ===== ЗАПУСК ПЛАТЕЖА =====
    if data == "start_payment":
        if not PAYMENT_PROVIDER_TOKEN:
            await update.callback_query.answer("⚠️ Оплата временно недоступна. Пожалуйста, попробуйте позже.", show_alert=True)
            return

        await update.callback_query.answer()
        logger.info(f"💳 ЗАПРОС ОПЛАТЫ: {user_name} ({user_username})")

        try:
            await update.callback_query.message.reply_invoice(
                title="Промт «Ментальный помощник»",
                description="Инструкция для вашего ИИ — быть ментальным ассистентом. Готовый инструмент для самоподдержки.",
                payload="promt_mentor_" + str(update.effective_user.id),
                provider_token=PAYMENT_PROVIDER_TOKEN,
                currency="RUB",
                prices=[LabeledPrice(label="Промт", amount=159900)],
                need_email=False,
                need_phone_number=False,
                start_parameter="mentor_prompt"
            )
        except Exception as e:
            logger.error(f"❌ Ошибка при создании платежа: {e}")
            await update.callback_query.message.reply_text("⚠️ Произошла ошибка при создании платежа. Попробуйте позже.")
        return

    # ===== ТЕСТ НА ТИП ОТДЫХА =====
    if data == "start_rest":
        context.user_data["scores"] = {k: 0 for k in RESULTS_REST}
        context.user_data["question"] = 0
        logger.info(f"📝 НАЧАЛ ТЕСТ: {user_name} ({user_username}) - ТЕСТ: Тип отдыха")
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "🌸 *Тест на тип отдыха! 8 вопросов, выбирай честно.*\n\n" + QUESTIONS_REST[0]["text"],
            reply_markup=get_question_keyboard_rest(0),
            parse_mode="Markdown"
        )
        return

    # ===== ОТВЕТЫ НА ТЕСТ =====
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
            await show_result(update, context)
        return

def get_question_keyboard_rest(q_idx):
    q = QUESTIONS_REST[q_idx]
    keyboard = [[InlineKeyboardButton(t, callback_data="rest_" + str(q_idx) + "_" + str(i))] for i, (t, _) in enumerate(q["options"])]
    return InlineKeyboardMarkup(keyboard)

def get_final_keyboard():
    """Клавиатура для финала теста — только статья и промт"""
    return [
        [InlineKeyboardButton("📖 Читать статью", url=ARTICLE_URL)],
        [InlineKeyboardButton("🤖 Промт «Ментальный помощник»", callback_data="show_prompt")]
    ]

async def show_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sc = context.user_data.get("scores", {})
    w = max(sc, key=sc.get)
    r = RESULTS_REST[w]
    tips = "\n".join(t for t in r["tips"])

    user = update.effective_user
    user_name = user.first_name or "Без имени"
    user_username = f"@{user.username}" if user.username else "без юзернейма"
    logger.info(f"🎯 ТЕСТ ЗАВЕРШЕН: {user_name} ({user_username}) - РЕЗУЛЬТАТ: {r['title']}")

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
        "🌸 *Кстати!*\n\n"
        "У меня есть промт «Ментальный помощник» — готовый инструмент, который будет поддерживать тебя каждый день.\n\n"
        "Оплата одноразовая. Без подписки.\n\n"
        "Спасибо, что прошла тест!"
    )

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(get_final_keyboard()),
        parse_mode="Markdown",
        disable_web_page_preview=False
    )

# ===================== ОБРАБОТКА ПЛАТЕЖЕЙ =====================
async def pre_checkout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение платежа — должно быть быстро (до 10 секунд)"""
    query = update.pre_checkout_query
    user = update.effective_user
    logger.info(f"💳 ПЛАТЕЖ: pre_checkout от {user.first_name} (@{user.username}), ID: {query.id}")

    if "promt_mentor_" not in query.invoice_payload:
        logger.warning(f"❌ НЕВЕРНЫЙ ПЛАТЕЖ: payload: {query.invoice_payload}")
        await query.answer(ok=False, error_message="Неверный товар. Попробуйте снова.")
        return

    await query.answer(ok=True)
    logger.info(f"✅ ПЛАТЕЖ: pre_checkout подтвержден для {user.first_name} (@{user.username})")

async def successful_payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выдача промта после успешной оплаты"""
    message = update.message
    user = update.effective_user
    user_name = user.first_name or "Без имени"
    user_username = f"@{user.username}" if user.username else "без юзернейма"

    payment = message.successful_payment
    logger.info(f"🎉 ОПЛАТА УСПЕШНА: {user_name} ({user_username}) | ID: {payment.telegram_payment_charge_id} | Сумма: {payment.total_amount} {payment.currency}")

    await message.reply_text(
        "🎉 *Оплата прошла успешно!*\n\n"
        "Вот твой промт «Ментальный помощник». Сохрани его и используй в любой момент.\n\n"
        f"{PROMPT_FULL}\n\n"
        "❤️ Спасибо за доверие! Если появятся вопросы — пиши, я всегда рядом.",
        parse_mode="Markdown"
    )

# ===================== ВЫДАЧА ПРОМТА ПО КОМАНДЕ (ДЛЯ ТЕСТА) =====================
async def get_prompt_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Временная команда для тестовой выдачи промта"""
    await update.message.reply_text(
        "🤖 *Вот твой промт «Ментальный помощник»:*\n\n" + PROMPT_FULL,
        parse_mode="Markdown"
    )

# ===================== ЗАПУСК =====================
def main():
    if not PAYMENT_PROVIDER_TOKEN:
        logger.warning("⚠️ ВНИМАНИЕ: PAYMENT_PROVIDER_TOKEN не установлен! Оплата не будет работать.")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("get_prompt", get_prompt_command))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(PreCheckoutQueryHandler(pre_checkout_handler))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_handler))

    logger.info("🚀 Бот запущен и готов к работе")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
