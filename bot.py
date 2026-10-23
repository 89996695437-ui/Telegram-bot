import os
import json
import logging
import io
import asyncio
import requests
import uuid
import base64
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)

# ========== ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ ==========
BOT_TOKEN = os.getenv("BOT_TOKEN")
SHOP_ID = os.getenv("SHOP_ID")
SECRET_KEY = os.getenv("SECRET_KEY")

if not BOT_TOKEN:
    logger.critical("❌ ОШИБКА: BOT_TOKEN не найден!")
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

# ===================== ТОВАР 1: ПРОМТ =====================
PROMPT_PRICE = 1599.00
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

PROMPT_FULL = """Ты — мой личный ментальный ассистент. Ты поддерживаешь меня в моменте, задаёшь вопросы и предлагаешь варианты. Ты не ставишь диагнозов, не интерпретируешь и не анализируешь. Ты просто помогаешь мне разобраться в себе и найти опору.

Твои принципы:
— Ты говоришь мягко: «возможно», «попробуй», «если хочешь».
— Ты никогда не говоришь «ты должна» или «тебе нужно».
— Ты не даёшь интерпретаций и не называешь части психики. Ты просто задаёшь вопросы и предлагаешь варианты.

Сразу после этого сообщения ты показываешь меню из 5 пунктов. Скопируй его в точности:

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

После меню напиши: "Выбери номер (1–5) — и я начну работать".

Никаких дополнительных объяснений, вопросов или комментариев. Только меню и эта фраза.

Когда я выберу номер, ты работаешь по следующему алгоритму:

ВКЛАДКА 1 — ДВИЖЕНИЕ К ЦЕЛЯМ БЕЗ ВЫГОРАНИЯ (🎯)

Начни с этих слов:
"Давай посмотрим на твою цель. Ты — молодец, что идёшь к своей мечте. Но давай проверим, не забываешь ли ты про себя по пути."

Задай вопросы по очереди. Жди ответа на каждый:

1. Какая у тебя сейчас цель? Это действительно твоё желание или то, что тебе навязали?
2. Если бы никто не узнал о твоём результате — ты бы всё равно хотела этого?
3. Как ты себя чувствуешь прямо сейчас по пути к этой цели?
4. Какие сигналы усталости ты замечаешь в теле?
5. А ты сейчас себя не ругаешь за то, что делаешь что-то не идеально? Что у тебя не получается сразу и красиво?

После ответов скажи мягко:

"Ты не обязана делать идеально. Ты не обязана сразу получаться. Ты имеешь право делать плохо, пробовать, ошибаться и переделывать.

А теперь скажи честно. Ты часто откладываешь что-то до идеального момента?"

Когда я отвечу, скажи:

"А что если начать делать на троечку?
— начать блог без идеального света и микрофона
— сходить на свидание, даже если не в лучшей форме
— начать петь, танцевать, рисовать, даже если нет опыта
— не слушать токсичный перфекционизм, а сделать, как получится

Представь: ты делаешь что-то на троечку. Мир не рухнет. Ты просто сделаешь шаг."

Потом спроси:
"Что из того, что ты давно откладывала, ты можешь сделать на троечку сегодня?"

Когда я отвечу, скажи:
"Отлично. Это твой шаг. Не идеальный. Просто твой."

Затем задай вопрос:
"Если бы ты сейчас посмотрела на свой путь как на приготовление салата — как бы ты его готовила? Быстро покрамсала или с любовью выбирала овощи и наслаждалась процессом?"

После этого напомни:
"К цели можно идти красиво, анализируя по пути. А можно загнать себя так, что цели и рад не будешь.

Правила:
— получай удовольствие от процесса
— проверяй, туда ли ты движешься
— достижение происходит постепенно
— это марафон, а не спринт
— если цель большая — разбей на мини-цели
— не обесценивай себя по пути"

Спроси:
"Какой самый маленький шаг ты можешь сделать сегодня, чтобы приблизиться к своей цели, но не сгореть?"

Поддержи меня и скажи, что я молодец.


ВКЛАДКА 2 — СЛОВА ПОДДЕРЖКИ ДЛЯ КАЖДОГО ДНЯ (💛)

Начни с этих слов: "Я здесь, чтобы поддержать тебя. Я буду давать тебе по одной фразе. После каждой фразы я буду спрашивать: «Могу тебя ещё поддержать?» Ты можешь ответить «да» или «нет»."

Выдавай фразы по одной из этого списка. После каждой спрашивай: «Могу тебя ещё поддержать?» и жди моего ответа «да» или «нет». Если «да» — дай следующую фразу. Если «нет» — заверши.

Список фраз:
— Ты очень сильная, ты со всем справишься. А если не справишься сегодня — справишься потом.
— Я тобой очень горжусь.
— Ты — 10 из 10.
— Миру повезло, что ты в нём есть.
— Ты не обязана быть идеальной, ты обязана быть живой.
— Ты делаешь лучше, чем думаешь.
— Ты имеешь право чувствовать всё, что чувствуешь.
— Ты не одна.
— Твой отдых — это не слабость, это топливо.
— Ты уже достаточно хорошая. Просто так.

Если я отвечу «нет» — скажи: "Я всегда рядом, если захочешь вернуться. Береги себя ❤️"


ВКЛАДКА 3 — МИКРООТДЫХ В МОМЕНТЕ (😴)

Скажи: «Давай разберёмся, какой отдых тебе нужен прямо сейчас. Я задам тебе 4 вопроса. Отвечай честно, как есть. В конце я подберу тебе отдых на 5–15 минут».

Задай вопросы по одному. Жди ответа на каждый.

Вопрос 1. Как ты сейчас себя чувствуешь?
а) Я истощена. Нет сил ни на что.
б) Я тревожусь. Мысли скачут.
в) Я в ступоре. Я не знаю, что я чувствую.
г) Я просто устала, но жить можно.

Вопрос 2. Сколько у тебя времени на отдых прямо сейчас?
а) 5 минут
б) 10 минут
в) 15 минут
г) больше, но я не знаю, что делать

Вопрос 3. Что тебе сейчас хочется?
а) Чтобы никто не трогал
б) Чтобы кто-то был рядом
в) Чтобы отвлечься
г) Не знаю, я запуталась

Вопрос 4. Что бы ты сейчас выбрала?
а) Тишину и покой
б) Тёплый разговор
в) Действие, которое переключит голову
г) Просто лечь и не думать

После ответов подсчитай результат и предложи:
— Если больше А: отдых от людей и шума. Закрыть глаза и подышать 5 минут, выпить тёплый чай в тишине.
— Если больше Б: отдых с переключением. Выйти на улицу на 5 минут, посмотреть в окно, послушать одну песню.
— Если больше В: отдых для тела. Сделать простую растяжку, походить босиком по полу.
— Если больше Г: микроотдых без правил. Выпить кофе, просто полежать, посмотреть в стену 2 минуты.

Скажи: «Вот что я предлагаю тебе сделать прямо сейчас на [время]. Попробуй. Я подожду. А когда вернёшься — напиши, как ты себя чувствуешь».


ВКЛАДКА 4 — ВЕЧЕРНЯЯ РЕФЛЕКСИЯ (🌙)

Начни с этих слов: 
"Завершим день с опорой и осознанностью.

Я задам тебе три вопроса. Никуда не торопись. Отвечай так, как чувствуешь — честно и без оценок. Я подожду столько, сколько нужно."

Задай мне три вопроса по очереди. Жди ответа на каждый.

Вопрос 1.
"Чем этот день был полезен для тебя? Даже если кажется, что ничего не случилось — возможно, ты просто была, или заметила что-то важное, или сделала крошечный шаг. Это уже польза."

Вопрос 2.
"Куда ты сегодня двигалась?"

Вопрос 3.
"За что ты благодарна себе и этому дню?"

Когда я отвечу на все вопросы, скажи:
"Ты молодец. День завершён. Иди отдыхай с чистой головой 🌙"


ВКЛАДКА 5 — РАБОТА С ТРЕВОГОЙ ЗДЕСЬ И СЕЙЧАС (🧠)

Задай мне эти вопросы строго по порядку, по одному. Жди моего ответа на каждый:

1. Что ты сейчас чувствуешь?
2. Где это в теле?
3. Как эта эмоция выглядит?
4. Давай переведём тревогу в страх. Чего именно я боюсь?
5. Реален ли этот страх или это мысль, которую я накручиваю?
6. Кто может поддержать меня в этом моменте?

Когда я отвечу на все вопросы, скажи:

"А теперь давай посмотрим, что ты можешь сделать прямо сейчас. Мир вокруг может быть нестабильным. Это правда. Но у тебя всегда есть зона, которую ты можешь контролировать.

Это твоя подконтрольная зона. Вот что в неё входит:
— твоё здоровье, физическая активность, еда
— твой дом, быт, красота вокруг
— твои задачи, которые зависят только от тебя
— твои мысли и психо-эмоциональное состояние

Чтобы чувствовать себя устойчивее, можно обратиться к этой зоне. Сделай что-то маленькое, но реальное. Например:
— выпей стакан воды
— убери одну вещь на место
— напиши одно сообщение, которое давно откладывала
— просто подыши 2 минуты

А теперь скажи: какое одно маленькое действие из твоей подконтрольной зоны ты можешь сделать прямо сейчас?"

Когда я отвечу, скажи:

"Отлично. Это твой шаг. Ты не меняешь весь мир — ты просто делаешь то, что в твоих силах. И этого уже достаточно.

А теперь ещё вопрос. У тебя есть что-то, что ты давно хотела попробовать, но откладывала? Может быть, начать проект, купить курс или просто сделать что-то для себя? И ты боишься, что сейчас не время?

Я скажу тебе так. Твоя подконтрольная зона — это твои действия. Ты можешь делать маленькие шаги. Не идеально. Не красиво. Просто делать.

Какой маленький шаг в сторону того, что ты давно хотела, ты можешь сделать сегодня?"

Затем спроси:
"Какие 2 простых действия из нашей беседы ты можешь сделать прямо сейчас, чтобы снизить тревогу?"

Теперь покажи меню. Только меню и фраза. Без лишнего текста."""

# ===================== ТОВАР 2: ЛЕКЦИЯ (ЗАГЛУШКА) =====================
LECTURE_PRICE = 2599.00
LECTURE_VIDEO_FILE_ID = "СЮДА_ВСТАВИМ_FILE_ID_ПОЗЖЕ"  # Заглушка

LECTURE_DESCRIPTION = """
🎥 *Лекция «Либо идеально, либо никак»*

*Как выйти из порочного круга мечт перед сном, но ничего-не-делания в реальности?*

Если ты счастливый обладатель нарциссической травмы, которая проявляется так:

— Каждый день даёшь себе обещание начать с понедельника, но когда он наступает — воз и ныне там.
— Если не уверена на 100%, что получится идеально — даже не начинаешь.
— Требуешь от себя всегда идеального результата.
— Перед сном фантазируешь, как всё могло бы быть по-другому, но утром мотивация испаряется.
— Чувствуешь в себе огромный потенциал, но до действий в реальности так и не доходит.
— Не обладаешь искусством маленьких шагов.
— Имеешь талант к прокрастинации.
— Боишься, что если начнёшь что-то делать, получишь осуждение других.

*На лекции мы разберём:*
• Откуда берётся этот механизм
• Как перестать ждать идеального момента
• Как начать делать маленькие шаги без насилия над собой

💰 *Стоимость:* 2599 ₽

После оплаты лекция придёт в этом чате.
"""

# ===================== ПРИВЕТСТВИЕ =====================
WELCOME_TEXT = """👋 *Привет! На связи бот психолога Дарьи.*

Выбери, что тебе интересно:

🎥 *Лекция «Либо идеально, либо никак»*
🤖 *Промт «Ментальный помощник»*
🧠 *Тест на тип отдыха*"""

# ===================== ФУНКЦИИ ЮKASSA =====================
def create_payment(amount, description, user_id):
    idempotence_key = str(uuid.uuid4())
    url = "https://api.yookassa.ru/v3/payments"
    headers = {
        "Content-Type": "application/json",
        "Idempotence-Key": idempotence_key
    }
    auth_string = f"{SHOP_ID}:{SECRET_KEY}"
    auth_header = base64.b64encode(auth_string.encode()).decode()
    headers["Authorization"] = f"Basic {auth_header}"
    payload = {
        "amount": {"value": str(amount), "currency": "RUB"},
        "confirmation": {"type": "redirect", "return_url": "https://t.me/psdarya_bot"},
        "capture": True,
        "description": description,
        "metadata": {"user_id": str(user_id)}
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["confirmation"]["confirmation_url"], data["id"]
    except Exception as e:
        logger.error(f"❌ Ошибка создания платежа: {e}")
        return None, None

def get_payment_status(payment_id):
    url = f"https://api.yookassa.ru/v3/payments/{payment_id}"
    headers = {"Content-Type": "application/json"}
    auth_string = f"{SHOP_ID}:{SECRET_KEY}"
    auth_header = base64.b64encode(auth_string.encode()).decode()
    headers["Authorization"] = f"Basic {auth_header}"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json().get("status")
    except Exception as e:
        logger.error(f"❌ Ошибка проверки платежа: {e}")
        return None

# ===================== ВРЕМЕННАЯ ФУНКЦИЯ ДЛЯ FILE_ID =====================
async def get_video_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Временная функция для получения file_id (ловит ВСЁ)"""
    if update.message.video:
        await update.message.reply_text(f"Ваш file_id (видео): `{update.message.video.file_id}`", parse_mode="Markdown")
    elif update.message.document:
        await update.message.reply_text(f"Ваш file_id (файл): `{update.message.document.file_id}`", parse_mode="Markdown")
    elif update.message.text:
        await update.message.reply_text(f"Вы прислали текст: {update.message.text}")
    else:
        await update.message.reply_text("Я получил сообщение, но не вижу в нём видео или файла.")

# ===================== ОБРАБОТЧИКИ БОТА =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    user = update.effective_user
    user_name = user.first_name or "Без имени"
    user_username = f"@{user.username}" if user.username else "без юзернейма"
    logger.info(f"📊 НОВЫЙ ПОЛЬЗОВАТЕЛЬ: {user_name} ({user_username}) | ID: {user.id}")

    keyboard = [
        [InlineKeyboardButton("🎥 Лекция «Либо идеально, либо никак»", callback_data="show_lecture")],
        [InlineKeyboardButton("🤖 Промт «Ментальный помощник»", callback_data="show_prompt")],
        [InlineKeyboardButton("🧠 Тест на тип отдыха", callback_data="start_rest")]
    ]
    await update.message.reply_text(WELCOME_TEXT, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.callback_query.data
    user = update.effective_user
    user_name = user.first_name or "Без имени"
    user_username = f"@{user.username}" if user.username else "без юзернейма"

    # ===== ПОКАЗАТЬ ЛЕКЦИЮ =====
    if data == "show_lecture":
        logger.info(f"📊 ПРОСМОТР ЛЕКЦИИ: {user_name} ({user_username})")
        keyboard = [[InlineKeyboardButton(f"💳 Купить {int(LECTURE_PRICE)} ₽", callback_data="pay_lecture")]]
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            LECTURE_DESCRIPTION,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return

    # ===== ПОКАЗАТЬ ПРОМТ =====
    if data == "show_prompt":
        logger.info(f"📊 ПРОСМОТР ПРОМТА: {user_name} ({user_username})")
        keyboard = [[InlineKeyboardButton(f"💳 Купить {int(PROMPT_PRICE)} ₽", callback_data="pay_prompt")]]
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            PROMPT_DESCRIPTION,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
        return

    # ===== ОПЛАТА ЛЕКЦИИ =====
    if data == "pay_lecture":
        if not SHOP_ID or not SECRET_KEY:
            await update.callback_query.answer("⚠️ Оплата временно недоступна.", show_alert=True)
            return
        await update.callback_query.answer()
        logger.info(f"💳 ЗАПРОС ОПЛАТЫ (ЛЕКЦИЯ): {user_name} ({user_username})")
        try:
            payment_url, payment_id = create_payment(LECTURE_PRICE, "Лекция «Либо идеально, либо никак»", update.effective_user.id)
            if payment_url and payment_id:
                context.user_data["payment_id"] = payment_id
                context.user_data["payment_item"] = "lecture"
                keyboard = [[InlineKeyboardButton("💳 Перейти к оплате", url=payment_url)]]
                await update.callback_query.message.reply_text(
                    f"🔗 *Оплата лекции — {int(LECTURE_PRICE)} ₽*\n\nПосле оплаты нажми «Проверить оплату».",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
                await update.callback_query.message.reply_text(
                    "Нажми *«Проверить оплату»* после того, как оплатишь.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Проверить оплату", callback_data="check_payment")]]),
                    parse_mode="Markdown"
                )
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")
        return

    # ===== ОПЛАТА ПРОМТА =====
    if data == "pay_prompt":
        if not SHOP_ID or not SECRET_KEY:
            await update.callback_query.answer("⚠️ Оплата временно недоступна.", show_alert=True)
            return
        await update.callback_query.answer()
        logger.info(f"💳 ЗАПРОС ОПЛАТЫ (ПРОМТ): {user_name} ({user_username})")
        try:
            payment_url, payment_id = create_payment(PROMPT_PRICE, "Промт «Ментальный помощник»", update.effective_user.id)
            if payment_url and payment_id:
                context.user_data["payment_id"] = payment_id
                context.user_data["payment_item"] = "prompt"
                keyboard = [[InlineKeyboardButton("💳 Перейти к оплате", url=payment_url)]]
                await update.callback_query.message.reply_text(
                    f"🔗 *Оплата промта — {int(PROMPT_PRICE)} ₽*\n\nПосле оплаты нажми «Проверить оплату».",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
                await update.callback_query.message.reply_text(
                    "Нажми *«Проверить оплату»* после того, как оплатишь.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Проверить оплату", callback_data="check_payment")]]),
                    parse_mode="Markdown"
                )
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")
        return

    # ===== ПРОВЕРКА ОПЛАТЫ =====
    if data == "check_payment":
        payment_id = context.user_data.get("payment_id")
        item_type = context.user_data.get("payment_item")
        if not payment_id:
            await update.callback_query.answer("⚠️ Платёж не найден.", show_alert=True)
            return
        logger.info(f"🔄 ПРОВЕРКА ОПЛАТЫ ({item_type}): {user_name} ({user_username})")
        status = get_payment_status(payment_id)
        if status == "succeeded":
            await update.callback_query.answer("✅ Оплата подтверждена!", show_alert=True)
            if item_type == "lecture":
                await send_lecture(update, context)
            else:
                await send_prompt_file(update, context)
        elif status == "pending":
            await update.callback_query.answer("⏳ Ещё обрабатывается. Попробуй через минуту.", show_alert=True)
        else:
            await update.callback_query.answer("⚠️ Не удалось проверить. Попробуй позже.", show_alert=True)
        return

    # ===== ТЕСТ =====
    if data == "start_rest":
        context.user_data["scores"] = {k: 0 for k in RESULTS_REST}
        context.user_data["question"] = 0
        logger.info(f"📝 НАЧАЛ ТЕСТ: {user_name} ({user_username})")
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "🌸 *Тест на тип отдыха! 8 вопросов.*\n\n" + QUESTIONS_REST[0]["text"],
            reply_markup=get_question_keyboard_rest(0),
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
            await show_result(update, context)
        return

def get_question_keyboard_rest(q_idx):
    q = QUESTIONS_REST[q_idx]
    keyboard = [[InlineKeyboardButton(t, callback_data="rest_" + str(q_idx) + "_" + str(i))] for i, (t, _) in enumerate(q["options"])]
    return InlineKeyboardMarkup(keyboard)

def get_final_keyboard():
    return [
        [InlineKeyboardButton("🎥 Лекция «Либо идеально, либо никак»", callback_data="show_lecture")],
        [InlineKeyboardButton("🤖 Промт «Ментальный помощник»", callback_data="show_prompt")],
        [InlineKeyboardButton("🧩 Подписаться на Telegram-канал", url="https://t.me/psdaryatyping")]
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
        "Другие материалы:"
    )
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(get_final_keyboard()),
        parse_mode="Markdown",
        disable_web_page_preview=True
    )

# ===================== ВЫДАЧА ПРОМТА =====================
async def send_prompt_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.callback_query.message
    user = update.effective_user
    user_name = user.first_name or "Без имени"
    user_username = f"@{user.username}" if user.username else "без юзернейма"
    try:
        await message.reply_text("🎉 *Оплата прошла успешно!*\n\nСпасибо за доверие! 💛\nТвой промт уже готов.", parse_mode="Markdown")
        await asyncio.sleep(0.5)
        await message.reply_text(
            "Скопируй этот текст в любого своего ИИ и пользуйся, чтобы:\n"
            "— достигать целей без насилия над собой\n"
            "— меньше тревожиться\n"
            "— вовремя отдыхать\n"
            "— рефлексировать вечером и получать поддержку"
        )
        await asyncio.sleep(0.5)
        file_content = PROMPT_FULL
        file_bytes = file_content.encode('utf-8')
        file_like = io.BytesIO(file_bytes)
        file_like.name = "mental_prompt.txt"
        await message.reply_document(
            document=file_like,
            filename="mental_prompt.txt",
            caption="📄 Сохрани файл и используй в любой момент."
        )
        logger.info(f"✅ ПРОМТ ОТПРАВЛЕН: {user_name} ({user_username})")
        await asyncio.sleep(0.5)
        await message.reply_text(
            "Другие материалы:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎥 Лекция «Либо идеально, либо никак»", callback_data="show_lecture")],
                [InlineKeyboardButton("🧠 Тест на тип отдыха", callback_data="start_rest")],
                [InlineKeyboardButton("🧩 Подписаться на Telegram-канал", url="https://t.me/psdaryatyping")]
            ]),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"❌ Ошибка при отправке промта: {e}")

# ===================== ВЫДАЧА ЛЕКЦИИ =====================
async def send_lecture(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.callback_query.message
    user = update.effective_user
    user_name = user.first_name or "Без имени"
    user_username = f"@{user.username}" if user.username else "без юзернейма"
    try:
        await message.reply_text(
            "🎉 *Оплата прошла успешно!*\n\nСпасибо за доверие! 💛\nСейчас пришлю лекцию.",
            parse_mode="Markdown"
        )
        await asyncio.sleep(0.5)
        if LECTURE_VIDEO_FILE_ID == "СЮДА_ВСТАВИМ_FILE_ID_ПОЗЖЕ":
            await message.reply_text(
                "⚠️ Видео временно недоступно. Пожалуйста, свяжитесь с @daryashpilevskaya.",
                parse_mode="Markdown"
            )
            logger.warning(f"⚠️ FILE_ID лекции не установлен! Пользователь: {user_name}")
        else:
            await message.reply_video(
                video=LECTURE_VIDEO_FILE_ID,
                caption="🎥 *Лекция «Либо идеально, либо никак»*\n\nПриятного просмотра!",
                parse_mode="Markdown"
            )
            logger.info(f"✅ ЛЕКЦИЯ ОТПРАВЛЕНА: {user_name} ({user_username})")
        
        await asyncio.sleep(0.5)
        # Кнопка отзыва и другие материалы
        await message.reply_text(
            "Буду рада, если оставишь отзыв — это поможет делать материалы лучше.\n\n"
            "Другие материалы:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✍️ Оставить отзыв", callback_data="leave_review")],
                [InlineKeyboardButton("🤖 Промт «Ментальный помощник»", callback_data="show_prompt")],
                [InlineKeyboardButton("🧠 Тест на тип отдыха", callback_data="start_rest")],
                [InlineKeyboardButton("🧩 Подписаться на Telegram-канал", url="https://t.me/psdaryatyping")]
            ]),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"❌ Ошибка при отправке лекции: {e}")
        await message.reply_text("⚠️ Не удалось отправить видео. Напиши @daryashpilevskaya — пришлём вручную.")

# ===================== ОТЗЫВ =====================
async def leave_review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    context.user_data["waiting_for_review"] = True
    await update.callback_query.message.reply_text(
        "Напиши свой отзыв одним сообщением и я обязательно его прочитаю.",
        parse_mode="Markdown"
    )

async def handle_review_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("waiting_for_review"):
        user = update.effective_user
        user_name = user.first_name or "Без имени"
        user_username = f"@{user.username}" if user.username else "без юзернейма"
        review_text = update.message.text
        
        logger.info(f"📝 НОВЫЙ ОТЗЫВ от {user_name} (@{user_username}): {review_text}")
        
        # Пересылаем отзыв тебе
        try:
            await context.bot.send_message(
                chat_id=282241753,  # Твой ID
                text=f"📝 *Новый отзыв о лекции*\n\nОт: {user_name} (@{user_username})\n\n{review_text}",
                parse_mode="Markdown"
            )
            await update.message.reply_text(
                "Спасибо за отзыв! 💛 Очень ценю.",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"❌ Ошибка при пересылке отзыва: {e}")
            await update.message.reply_text(
                "Спасибо за отзыв! Я его сохраню.",
                parse_mode="Markdown"
            )
        
        context.user_data["waiting_for_review"] = False
        return

# ===================== ЗАПУСК =====================
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.ALL, get_video_id))  # ВРЕМЕННО ДЛЯ FILE_ID
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_review_text))  # ДЛЯ ОТЗЫВОВ
    logger.info("🚀 Бот запущен и готов к работе")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
