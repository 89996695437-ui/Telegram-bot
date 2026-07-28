import os
import json
import logging
import io
import asyncio
import requests
import hashlib
import uuid
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ========== ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ ==========
BOT_TOKEN = os.getenv("BOT_TOKEN")
SHOP_ID = os.getenv("SHOP_ID")
SECRET_KEY = os.getenv("SECRET_KEY")

if not BOT_TOKEN:
    logger.critical("❌ ОШИБКА: BOT_TOKEN не найден в переменных окружения!")
    exit(1)

logger.info("✅ Бот запущен")
logger.info("🛒 SHOP_ID: " + (SHOP_ID if SHOP_ID else "НЕ УСТАНОВЛЕН"))
logger.info("🔑 SECRET_KEY: " + ("Установлен" if SECRET_KEY else "НЕ УСТАНОВЛЕН"))

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

💰 *Стоимость:* 1599 ₽

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

[ВСТАВЬ СЮДА ПОЛНЫЙ ТЕКСТ АЛГОРИТМОВ ДЛЯ ВСЕХ 5 ВКЛАДОК — Я СОКРАТИЛА ДЛЯ КОДА]
"""

# ===================== ПРИВЕТСТВИЕ (без цены) =====================
WELCOME_TEXT = """👋 *Привет! На связи бот психолога Дарьи.*

🧠 *Тест на тип отдыха* — узнай, что нужно именно тебе
🤖 *Промт «Ментальный помощник»* — готовый инструмент для самоподдержки"""

# ===================== ФУНКЦИИ ДЛЯ РАБОТЫ С ЮKASSA =====================
def create_payment(amount, description, user_id):
    """Создаёт платёж в ЮKassa и возвращает ссылку для оплаты"""
    idempotence_key = str(uuid.uuid4())
    url = "https://api.yookassa.ru/v3/payments"
    
    headers = {
        "Content-Type": "application/json",
        "Idempotence-Key": idempotence_key
    }
    
    # Авторизация через Basic Auth
    auth_string = f"{SHOP_ID}:{SECRET_KEY}"
    import base64
    auth_header = base64.b64encode(auth_string.encode()).decode()
    headers["Authorization"] = f"Basic {auth_header}"
    
    # Данные для платежа
    payload = {
        "amount": {
            "value": str(amount),
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://t.me/psdarya_bot"
        },
        "capture": True,
        "description": description,
        "metadata": {
            "user_id": str(user_id)
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        confirmation_url = data["confirmation"]["confirmation_url"]
        payment_id = data["id"]
        return confirmation_url, payment_id
    except Exception as e:
        logger.error(f"❌ Ошибка при создании платежа: {e}")
        return None, None

def get_payment_status(payment_id):
    """Проверяет статус платежа в ЮKassa"""
    url = f"https://api.yookassa.ru/v3/payments/{payment_id}"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    auth_string = f"{SHOP_ID}:{SECRET_KEY}"
    import base64
    auth_header = base64.b64encode(auth_string.encode()).decode()
    headers["Authorization"] = f"Basic {auth_header}"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data.get("status")
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке статуса платежа: {e}")
        return None

# ===================== ОБРАБОТЧИКИ БОТА =====================
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
        # Логируем просмотр промта
        logger.info(f"📊 ПРОСМОТР ПРОМТА: {user_name} ({user_username})")
        
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
        if not SHOP_ID or not SECRET_KEY:
            await update.callback_query.answer("⚠️ Оплата временно недоступна. Пожалуйста, попробуйте позже.", show_alert=True)
            return

        await update.callback_query.answer()
        logger.info(f"💳 ЗАПРОС ОПЛАТЫ: {user_name} ({user_username})")

        try:
            amount = 1599.00
            description = "Промт «Ментальный помощник»"
            user_id = update.effective_user.id
            payment_url, payment_id = create_payment(amount, description, user_id)

            if payment_url and payment_id:
                context.user_data["payment_id"] = payment_id
                context.user_data["payment_created"] = True

                keyboard = [[InlineKeyboardButton("💳 Перейти к оплате", url=payment_url)]]
                await update.callback_query.message.reply_text(
                    "🔗 *Ссылка на оплату*\n\n"
                    "Нажми на кнопку ниже, чтобы перейти к оплате.\n"
                    "Доступны все способы: СБП, T‑Банк Пей, карты, SberPay, ЮMoney.\n\n"
                    "После оплаты нажми кнопку *«Проверить оплату»*.",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )

                check_keyboard = [[InlineKeyboardButton("🔄 Проверить оплату", callback_data="check_payment")]]
                await update.callback_query.message.reply_text(
                    "Нажми *«Проверить оплату»* после того, как завершишь оплату.",
                    reply_markup=InlineKeyboardMarkup(check_keyboard),
                    parse_mode="Markdown"
                )
            else:
                await update.callback_query.message.reply_text("⚠️ Произошла ошибка при создании платежа. Попробуйте позже.")
        except Exception as e:
            logger.error(f"❌ Ошибка при создании платежа: {e}")
            await update.callback_query.message.reply_text("⚠️ Произошла ошибка при создании платежа. Попробуйте позже.")
        return

    # ===== ПРОВЕРКА ОПЛАТЫ =====
    if data == "check_payment":
        payment_id = context.user_data.get("payment_id")

        if not payment_id:
            await update.callback_query.answer("⚠️ Платёж не найден. Попробуйте создать новый.", show_alert=True)
            return

        logger.info(f"🔄 ПРОВЕРКА ОПЛАТЫ: {user_name} ({user_username}), payment_id: {payment_id}")

        status = get_payment_status(payment_id)

        if status == "succeeded":
            await update.callback_query.answer("✅ Оплата подтверждена! Сейчас отправлю промт.", show_alert=True)
            await send_prompt_file(update, context)
        elif status == "pending":
            await update.callback_query.answer("⏳ Платёж ещё обрабатывается. Попробуйте через несколько минут.", show_alert=True)
        elif status == "canceled":
            await update.callback_query.answer("❌ Платёж был отменён. Попробуйте снова.", show_alert=True)
        else:
            await update.callback_query.answer("⚠️ Не удалось проверить статус. Попробуйте позже.", show_alert=True)
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

# ===================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====================
def get_question_keyboard_rest(q_idx):
    q = QUESTIONS_REST[q_idx]
    keyboard = [[InlineKeyboardButton(t, callback_data="rest_" + str(q_idx) + "_" + str(i))] for i, (t, _) in enumerate(q["options"])]
    return InlineKeyboardMarkup(keyboard)

def get_final_keyboard():
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

# ===================== ВЫДАЧА ПРОМТА ФАЙЛОМ =====================
async def send_prompt_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет файл с промтом пользователю"""
    message = update.callback_query.message
    user = update.effective_user
    user_name = user.first_name or "Без имени"
    user_username = f"@{user.username}" if user.username else "без юзернейма"

    try:
        # СООБЩЕНИЕ 1: Благодарность
        await message.reply_text(
            "🎉 *Оплата прошла успешно!*\n\n"
            "Спасибо за доверие! 💛\n"
            "Твой промт «Ментальный помощник» уже готов.",
            parse_mode="Markdown"
        )
        logger.info(f"✅ Отправлено сообщение 1 для {user_name}")

        await asyncio.sleep(0.5)

        # СООБЩЕНИЕ 2: Инструкция перед файлом
        await message.reply_text(
            "Скопируй этот текст в любого своего ИИ (ChatGPT, DeepSeek, YandexGPT и др.) "
            "и пользуйся, чтобы:\n"
            "— достигать своих целей без насилия над собой\n"
            "— меньше тревожиться\n"
            "— вовремя замечать усталость и отдыхать\n"
            "— порефлексировать вечером и получить поддержку, когда нужно"
        )
        logger.info(f"✅ Отправлена инструкция для {user_name}")

        await asyncio.sleep(0.5)

        # === ОТПРАВКА ПРОМТА ФАЙЛОМ (только промт) ===
        file_content = PROMPT_FULL
        file_bytes = file_content.encode('utf-8')
        file_like = io.BytesIO(file_bytes)
        file_like.name = "mental_prompt.txt"

        await message.reply_document(
            document=file_like,
            filename="mental_prompt.txt",
            caption="📄 Сохрани файл и используй в любой момент."
        )
        logger.info(f"✅ Отправлен файл с промтом для {user_name}")

    except Exception as e:
        logger.error(f"❌ Ошибка при отправке промта: {e}")

# ===================== ЗАПУСК =====================
def main():
    if not SHOP_ID or not SECRET_KEY:
        logger.warning("⚠️ ВНИМАНИЕ: SHOP_ID или SECRET_KEY не установлены! Оплата не будет работать.")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))

    logger.info("🚀 Бот запущен и готов к работе")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
