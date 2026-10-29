import os
import json
import logging
import io
import asyncio
import requests
import uuid
import base64
from collections import Counter
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

# ===================== НОВЫЙ ТЕСТ: СТИЛЬ ДОСТИЖЕНИЯ ЦЕЛЕЙ =====================
QUESTIONS_GOAL = [
    {"text": "1. Как ты обычно начинаешь новый проект или цель?", "options": [("Сначала всё продумываю: план, этапы, ресурсы", "A"), ("Загораюсь и сразу начинаю действовать", "B"), ("Долго взвешиваю, читаю, присматриваюсь, прежде чем сделать первый шаг", "C"), ("Сажусь и делаю качественно, по порядку, без суеты", "D")]},
    {"text": "2. Что для тебя «хороший результат»?", "options": [("Когда всё прошло по плану", "A"), ("Когда было ярко и быстро", "B"), ("Когда не было рисков и ошибок", "C"), ("Когда результат выдержит любую проверку", "D")]},
    {"text": "3. Что чаще всего тебя останавливает?", "options": [("План ещё не идеален — страшно начинать раньше времени", "A"), ("Если не получилось сразу — пропадает смысл продолжать", "B"), ("А вдруг не получится и я буду выглядеть глупо", "C"), ("Я ещё недостаточно хорошо подготовлена", "D")]},
    {"text": "4. Как ты реагируешь на ошибку в процессе?", "options": [("Пересобираю план, иногда по кругу", "A"), ("Теряю запал, хочется всё бросить", "B"), ("Воспринимаю как подтверждение, что не стоило начинать", "C"), ("Корю себя и стараюсь переделать идеально", "D")]},
    {"text": "5. Что говорят о тебе окружающие?", "options": [("«Ты всё просчитываешь наперёд»", "A"), ("«С тобой не соскучишься, у тебя столько идей»", "B"), ("«Ты осторожная, семь раз отмеришь»", "C"), ("«На тебя можно положиться, ты всё делаешь качественно»", "D")]},
    {"text": "6. Твои отношения с отдыхом во время движения к цели?", "options": [("Отдыхаю, только когда весь план выполнен", "A"), ("Отдыхаю рывками — то марафон, то полный штиль", "B"), ("Отдыхаю много, потому что не решаюсь начать", "C"), ("Отдых — это почти всегда с чувством вины", "D")]},
    {"text": "7. Какая мысль звучит у тебя чаще всего?", "options": [("«Надо продумать ещё раз, вдруг я что-то упустила»", "A"), ("«Либо сейчас на максимум, либо вообще не стоит»", "B"), ("«Лучше ничего не менять, чем ошибиться»", "C"), ("«Это недостаточно хорошо, надо доделать»", "D")]},
    {"text": "8. Что бы ты хотела изменить в своём подходе к целям?", "options": [("Начинать раньше, не доводя план до идеала", "A"), ("Не сдуваться после первого препятствия", "B"), ("Разрешить себе пробовать, даже не будучи готовой на 100%", "C"), ("Перестать требовать от себя идеала с первого раза", "D")]},
]

RESULTS_GOAL = {
    "A": {"title": "🧭 Стратег", "desc": "Ты продумываешь всё до мелочей и любишь, когда есть чёткий план. Это сильная сторона — ты редко действуешь вслепую. Но есть слепая зона: ты не начинаешь, пока план не станет идеальным. А значит, план готов — а действия всё ещё нет."},
    "B": {"title": "⚡ Спринтер", "desc": "Ты загораешься быстро и ярко, умеешь стартовать без раскачки. Это редкий дар — большинство людей месяцами не могут решиться. Слепая зона: для тебя либо всё сразу и по максимуму, либо «зачем вообще». Первое препятствие — и запал гаснет."},
    "C": {"title": "🔍 Наблюдатель", "desc": "Ты осторожна и умеешь оценивать риски — это защищает тебя от необдуманных решений. Слепая зона: первый неидеальный опыт пугает так сильно, что проще вообще не начинать, чем допустить ошибку на глазах у всех."},
    "D": {"title": "📐 Отличница", "desc": "Ты делаешь качественно, стабильно, на тебя можно положиться. Слепая зона: результат есть, а лёгкости и удовольствия от процесса — нет, потому что планка растёт быстрее, чем твои достижения."},
}

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

# ===================== ТОВАР 2: ЛЕКЦИЯ =====================
LECTURE_PRICE = 2599.00
LECTURE_VIDEO_FILE_ID = "BAACAgIAAxkBAAIO4WrbODWfFLUS8q7ABa8Sl_COT5PxAALkowACCuvZSl9S7W8BJTwCPQQ"

LECTURE_DESCRIPTION = """
🎥 *Лекция «Либо идеально, либо никак»*

*Как выйти из порочного круга мечт перед сном, но ничего-не-делания в реальности?*

Если вы счастливый обладатель нарциссической травмы, которая проявляется так:

— Перед сном фантазируете, как всё могло бы быть по-другому, но утром мотивация испаряется.
— Чувствуете в себе огромный потенциал, но до действий в реальности так и не доходит.
— Не обладаете искусством маленьких шагов.
— Имеете талант к прокрастинации.
— Боитесь, что если начнёте что-то делать, получите осуждение других.

*На лекции мы разберём:*
• Откуда берётся этот механизм
• Как перестать ждать идеального момента
• Как начать закрывать свои цели уже прям после просмотра лекции

✨ Ссылка на лекцию ждет вас в шапке профиля через бот.

💰 *Стоимость:* 2599 ₽

После оплаты лекция придёт в этом чате.
"""

# ===================== ПРИВЕТСТВИЕ =====================
WELCOME_TEXT = """Выбери, что тебе интересно:

🧠 *Тест: твой стиль достижения и преграды*
🎥 *Лекция «Либо идеально, либо никак»*
🤖 *Промт «Ментальный помощник»*"""

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

# ===================== ОБРАБОТЧИКИ БОТА =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    user = update.effective_user
    user_name = user.first_name or "Без имени"
    user_username = f"@{user.username}" if user.username else "без юзернейма"
    logger.info(f"📊 НОВЫЙ ПОЛЬЗОВАТЕЛЬ: {user_name} ({user_username}) | ID: {user.id}")

    keyboard = [
        [InlineKeyboardButton("🧠 Тест: твой стиль достижения и преграды", callback_data="start_goal_test")],
        [InlineKeyboardButton("🎥 Лекция «Либо идеально, либо никак»", callback_data="show_lecture")],
        [InlineKeyboardButton("🤖 Промт «Ментальный помощник»", callback_data="show_prompt")]
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

    # ===== НОВЫЙ ТЕСТ: ВСТУПЛЕНИЕ =====
    if data == "start_goal_test":
        logger.info(f"📊 ПРОСМОТР ТЕСТА: {user_name} ({user_username})")
        
        intro_text = (
            "🎯 *Тест на стиль достижения целей*\n\n"
            "Ты ставишь цели, но что-то постоянно сбивает с курса? За 2 минуты узнай свой стиль движения к целям — и ту единственную вещь, которая мешает именно тебе доходить до результата.\n\n"
            "Погнали!"
        )
        
        # Создаем кнопку для запуска
        keyboard = [[InlineKeyboardButton("Начать тест", callback_data="goal_start")]]
        
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            intro_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return

    # ===== НОВЫЙ ТЕСТ: ЗАПУСК ПЕРВОГО ВОПРОСА =====
    if data == "goal_start":
        context.user_data["goal_answers"] = []
        context.user_data["goal_q"] = 0
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            QUESTIONS_GOAL[0]["text"],
            reply_markup=get_goal_question_keyboard(0)
        )
        return

    if data.startswith("goal_"):
        parts = data.split("_")
        q_idx = int(parts[1])
        opt_idx = int(parts[2])
        
        # Сохраняем выбранную букву
        answer_letter = QUESTIONS_GOAL[q_idx]["options"][opt_idx][1]
        context.user_data["goal_answers"].append(answer_letter)
        
        next_q = q_idx + 1
        context.user_data["goal_q"] = next_q
        
        if next_q < len(QUESTIONS_GOAL):
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(
                QUESTIONS_GOAL[next_q]["text"],
                reply_markup=get_goal_question_keyboard(next_q)
            )
        else:
            await show_goal_result(update, context)
        return

def get_goal_question_keyboard(q_idx):
    q = QUESTIONS_GOAL[q_idx]
    keyboard = []
    for i, (text, _) in enumerate(q["options"]):
        # В callback_data передаем индексы вопроса и ответа
        keyboard.append([InlineKeyboardButton(text, callback_data=f"goal_{q_idx}_{i}")])
    return InlineKeyboardMarkup(keyboard)

def get_final_keyboard():
    return [
        [InlineKeyboardButton("🎥 Лекция «Либо идеально, либо никак»", callback_data="show_lecture")],
        [InlineKeyboardButton("🤖 Промт «Ментальный помощник»", callback_data="show_prompt")],
        [InlineKeyboardButton("🧩 Подписаться на Telegram-канал", url="https://t.me/psdaryatyping")]
    ]

async def show_goal_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answers = context.user_data.get("goal_answers", [])
    user = update.effective_user
    user_name = user.first_name or "Без имени"
    user_username = f"@{user.username}" if user.username else "без юзернейма"
    
    # Считаем, какой буквы больше всего
    counts = Counter(answers)
    max_count = max(counts.values())
    # Получаем все буквы, которые набрали максимум (на случай ничьей)
    top_letters = [letter for letter, count in counts.items() if count == max_count]
    
    # Формируем результат
    titles = []
    descs = []
    for letter in top_letters:
        res = RESULTS_GOAL[letter]
        titles.append(res["title"])
        descs.append(res["desc"])
        
    final_title = " и ".join(titles)
    final_desc = "\n\n".join(descs)
    
    logger.info(f"🎯 ТЕСТ ЗАВЕРШЕН: {user_name} ({user_username}) - РЕЗУЛЬТАТ: {final_title}")
    
    text = (
        f"🏆 *Твой результат:* *{final_title}*\n\n"
        f"{final_desc}\n\n"
        "— — —\n\n"
        "💡 *Интересный факт:* у всех четырёх типов слепая зона растёт из одного корня — страха неидеального результата. Он просто надевает разные маски: у кого-то это бесконечный план, у кого-то — выгорание после первого рывка, у кого-то — паралич перед стартом.\n\n"
        "На лекции «Либо идеально, либо никак» разберём, откуда растёт этот страх и что с ним делать — независимо от того, какой у тебя тип.\n\n"
        "Другие материалы:"
    )
    
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(get_final_keyboard()),
        parse_mode="Markdown"
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
                [InlineKeyboardButton("🧠 Тест: твой стиль достижения и преграды", callback_data="start_goal_test")],
                [InlineKeyboardButton("🎥 Лекция «Либо идеально, либо никак»", callback_data="show_lecture")],
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
        if LECTURE_VIDEO_FILE_ID == "BAACAgIAAxkBAAIO4WrbODWfFLUS8q7ABa8Sl_COT5PxAALkowACCuvZSl9S7W8BJTwCPQQ":
            await message.reply_video(
                video=LECTURE_VIDEO_FILE_ID,
                caption="🎥 *Лекция «Либо идеально, либо никак»*\n\nПриятного просмотра!",
                parse_mode="Markdown"
            )
            logger.info(f"✅ ЛЕКЦИЯ ОТПРАВЛЕНА: {user_name} ({user_username})")
        
        await asyncio.sleep(0.5)
        await message.reply_text(
            "Буду рада, если оставишь отзыв — это поможет делать материалы лучше.\n\n"
            "Другие материалы:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✍️ Оставить отзыв", callback_data="leave_review")],
                [InlineKeyboardButton("🧠 Тест: твой стиль достижения и преграды", callback_data="start_goal_test")],
                [InlineKeyboardButton("🤖 Промт «Ментальный помощник»", callback_data="show_prompt")],
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
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_review_text))
    logger.info("🚀 Бот запущен и готов к работе")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
