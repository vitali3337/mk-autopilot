"""
MK-GRUPP AI Autopilot - Engine
Agents: ContentWriter, Publisher, CRM, LeadBot, Scheduler
"""
import os
import json
import asyncio
import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import httpx

log = logging.getLogger("autopilot")

# ── Business data ────────────────────────────────────────────────────────────
BUSINESS_NAME    = "МК-ГРУПП"
BUSINESS_CITY    = "Тирасполь, ПМР"
BUSINESS_SERVICES = "металлопластиковые окна, входные двери, межкомнатные двери, балконы, тамбуры"
BUSINESS_PHONES  = "+373 777 2-65-36 (Сергей) | +373 777 7-54-73 (Виталий)"
BUSINESS_ADDRESS = "г. Тирасполь, ул. Энергетиков 54/6"
BUSINESS_SITE    = "mk-grupp.netlify.app"
BUSINESS_USP     = "бесплатный замер · монтаж за 1 день · гарантия · вся ПМР"

# ── Topics & styles ──────────────────────────────────────────────────────────
TOPIC_MAP = {
    "windows":      "металлопластиковые окна — замена старых, теплоизоляция, шумоизоляция",
    "doors":        "входные металлические двери — безопасность, утепление, красота",
    "interior":     "межкомнатные двери — дизайн, качество, ассортимент",
    "balcony":      "остекление и утепление балкона",
    "tambour":      "тамбур под ключ — тепло, тихо, безопасно",
    "promo":        "акция — скидка при заказе 2+ позиций",
    "review":       "реальный отзыв довольного клиента из Тирасполя",
    "before_after": "трансформация до/после замены окон или дверей",
    "faq":          "ответы на частые вопросы об окнах и дверях",
    "seasonal":     "подготовка к зиме, утепление квартиры",
}

STYLE_MAP = {
    "selling":     "продающий: выгода, конкретный оффер, CTA",
    "emotional":   "эмоциональный: боль клиента, решение",
    "educational": "образовательный: полезные факты, экспертность",
    "urgent":      "срочность: ограниченное предложение",
}

# ── Weekly schedule (weekday 0=Mon) ──────────────────────────────────────────
WEEKLY_PLAN = {
    0: [
        {"hour": 10, "minute": 0,  "topic": "windows",     "style": "emotional"},
        {"hour": 18, "minute": 0,  "topic": "promo",       "style": "urgent"},
    ],
    1: [
        {"hour": 11, "minute": 0,  "topic": "before_after","style": "selling"},
    ],
    2: [
        {"hour": 10, "minute": 0,  "topic": "review",      "style": "emotional"},
        {"hour": 17, "minute": 0,  "topic": "doors",       "style": "selling"},
    ],
    3: [
        {"hour": 10, "minute": 0,  "topic": "promo",       "style": "urgent"},
    ],
    4: [
        {"hour": 11, "minute": 0,  "topic": "balcony",     "style": "selling"},
        {"hour": 16, "minute": 0,  "topic": "faq",         "style": "educational"},
    ],
    5: [
        {"hour": 11, "minute": 0,  "topic": "tambour",     "style": "emotional"},
    ],
    6: [
        {"hour": 12, "minute": 0,  "topic": "windows",     "style": "selling"},
    ],
}

# ── Stats ─────────────────────────────────────────────────────────────────────
STATS_FILE = "stats.json"


def load_stats():
    try:
        with open(STATS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {
            "posts_sent": 0,
            "leads": 0,
            "errors": 0,
            "last_post": None,
            "history": [],
        }


def save_stats(s):
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=2, default=str)


STATS = load_stats()


# ── Agent 1: Content Generator (Claude API) ───────────────────────────────────
async def generate_post(topic: str, style: str) -> dict:
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY не задан")

    system_prompt = (
        "Ты — SMM-копирайтер для строительного рынка ПМР (Приднестровье).\n"
        "Пишешь ТОЛЬКО на русском языке. Простой язык, конкретные выгоды.\n"
        "Бизнес: " + BUSINESS_NAME + " | " + BUSINESS_CITY + "\n"
        "Услуги: " + BUSINESS_SERVICES + "\n"
        "УТП: " + BUSINESS_USP + "\n"
        "Контакты: " + BUSINESS_PHONES + "\n"
        "Сайт: " + BUSINESS_SITE + "\n"
        "Тема: " + TOPIC_MAP.get(topic, topic) + "\n"
        "Стиль: " + STYLE_MAP.get(style, style) + "\n"
        "Каждый пост ПРОДАЁТ. Минимум воды. Максимум конкретики.\n"
        "Отвечай ТОЛЬКО валидным JSON без markdown."
    )

    user_prompt = (
        "Создай продающий Telegram-пост.\n"
        "Верни JSON строго такого формата:\n"
        "{\n"
        '  "text": "полный текст поста с эмодзи, 150-250 слов",\n'
        '  "cta_button_text": "текст кнопки до 5 слов",\n'
        '  "preview_text": "первые 3-4 слова"\n'
        "}"
    )

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 900,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_prompt}],
    }

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=payload,
        )
        resp.raise_for_status()
        raw = resp.json()["content"][0]["text"]
        clean = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(clean)


# ── Agent 2: Publisher (Telegram) ────────────────────────────────────────────
async def publish_telegram(post: dict) -> bool:
    token   = os.getenv("TELEGRAM_BOT_TOKEN", "")
    channel = os.getenv("TELEGRAM_CHANNEL_ID", "")
    if not token or not channel:
        log.warning("Telegram не настроен")
        return False

    keyboard = {
        "inline_keyboard": [[
            {
                "text": post.get("cta_button_text", "📞 Позвонить"),
                "url": "https://t.me/Tirplast_bot",
            },
            {
                "text": "🌐 Сайт",
                "url": "https://mk-grupp.netlify.app",
            },
        ]]
    }

    payload = {
        "chat_id":      channel,
        "text":         post.get("text", ""),
        "parse_mode":   "HTML",
        "reply_markup": keyboard,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            "https://api.telegram.org/bot" + token + "/sendMessage",
            json=payload,
        )
        data = resp.json()
        if data.get("ok"):
            log.info("Telegram OK: " + str(post.get("preview_text", "")))
            return True
        log.error("Telegram error: " + str(data))
        return False


# ── Agent 3: CRM (Make.com -> Google Sheets) ─────────────────────────────────
async def crm_save_lead(lead: dict) -> bool:
    url = os.getenv("SHEETS_WEBHOOK_URL", "")
    if not url:
        log.warning("SHEETS_WEBHOOK_URL не задан")
        return False

    payload = {
        "timestamp": datetime.now().isoformat(),
        "source":    lead.get("source", "Telegram"),
        "name":      lead.get("name", ""),
        "phone":     lead.get("phone", ""),
        "message":   lead.get("message", ""),
        "status":    "Новый",
    }

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(url, json=payload)
        if resp.status_code < 300:
            log.info("CRM OK: " + str(payload["name"]) + " " + str(payload["phone"]))
            STATS["leads"] += 1
            save_stats(STATS)
            return True
        log.error("CRM error " + str(resp.status_code))
        return False


async def crm_notify_manager(lead: dict):
    token   = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("LEAD_NOTIFY_CHAT_ID", "")
    if not token or not chat_id:
        return

    phone   = lead.get("phone", "")
    clean   = phone.replace(" ", "").replace("-", "")
    wa_url  = "https://wa.me/" + clean.lstrip("+")

    text = (
        "🔔 <b>НОВЫЙ ЛИД — МК-ГРУПП</b>\n\n"
        "👤 <b>" + lead.get("name", "Неизвестно") + "</b>\n"
        "📞 <b>" + phone + "</b>\n"
        "🔧 Услуга: " + lead.get("message", "—") + "\n"
        "📡 Источник: " + lead.get("source", "Telegram") + "\n"
        "🕐 " + datetime.now().strftime("%d.%m.%Y %H:%M") + "\n\n"
        "⚡ <b>Перезвони в течение 30 минут!</b>"
    )

    keyboard = {
        "inline_keyboard": [[
            {"text": "📞 Позвонить", "url": "tel:" + clean},
            {"text": "💬 WhatsApp",  "url": wa_url},
        ]]
    }

    async with httpx.AsyncClient(timeout=15) as client:
        await client.post(
            "https://api.telegram.org/bot" + token + "/sendMessage",
            json={
                "chat_id":      chat_id,
                "text":         text,
                "parse_mode":   "HTML",
                "reply_markup": keyboard,
            },
        )


# ── Agent 4: Lead Bot ─────────────────────────────────────────────────────────
SESSIONS = {}

TRIGGERS = {
    "замер":     "Бесплатный замер",
    "цена":      "Расчёт стоимости",
    "стоимость": "Расчёт стоимости",
    "окно":      "Металлопластиковые окна",
    "дверь":     "Входные двери",
    "балкон":    "Остекление балкона",
    "тамбур":    "Тамбур под ключ",
    "сетка":     "Москитные сетки",
    "привет":    "Общий запрос",
    "/start":    "Общий запрос",
    "хочу":      "Общий запрос",
    "сколько":   "Расчёт стоимости",
}


async def _tg_send(chat_id: str, text: str):
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        return
    async with httpx.AsyncClient(timeout=15) as client:
        await client.post(
            "https://api.telegram.org/bot" + token + "/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
        )


async def handle_update(update: dict):
    msg = update.get("message")
    if not msg:
        return

    chat_id = str(msg["chat"]["id"])
    text    = msg.get("text", "").strip()
    fn      = msg["chat"].get("first_name", "")
    session = SESSIONS.get(chat_id, {})

    # Check triggers
    service = None
    for kw, svc in TRIGGERS.items():
        if kw in text.lower():
            service = svc
            break

    if service and not session:
        SESSIONS[chat_id] = {
            "step":    "ask_phone",
            "name":    fn or "Клиент",
            "service": service,
            "msg":     text,
        }
        greeting = ", " + fn if fn else ""
        await _tg_send(
            chat_id,
            "👋 Привет" + greeting + "!\n\n"
            "Услуга: <b>" + service + "</b>\n"
            "Мастер приедет бесплатно и всё замерит.\n\n"
            "📞 Оставьте номер телефона — перезвоним за <b>30 минут</b>:",
        )
        return

    if session.get("step") == "ask_phone":
        digits = "".join(c for c in text if c.isdigit())
        if len(digits) >= 7:
            lead = {
                "name":    session["name"],
                "phone":   text,
                "message": session["service"],
                "source":  "Telegram Bot @Tirplast_bot",
            }
            SESSIONS.pop(chat_id, None)
            await crm_save_lead(lead)
            await crm_notify_manager(lead)
            await _tg_send(
                chat_id,
                "✅ <b>Заявка принята!</b>\n\n"
                "Перезвоним на " + text + " в течение 30 минут.\n\n"
                "📍 " + BUSINESS_ADDRESS + "\n"
                "📞 " + BUSINESS_PHONES,
            )
        else:
            await _tg_send(chat_id, "Пожалуйста, введите корректный номер телефона 📞")
        return

    await _tg_send(
        chat_id,
        "🏠 <b>МК-ГРУПП — Окна · Двери · Балконы · Тамбуры</b>\n\n"
        "Напишите <b>«замер»</b> или <b>«цена»</b> — рассчитаем бесплатно!\n\n"
        "📞 " + BUSINESS_PHONES,
    )


# ── Agent 5: Telegram Polling ─────────────────────────────────────────────────
_last_update_id = 0


async def poll():
    global _last_update_id
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        return
    try:
        async with httpx.AsyncClient(timeout=35) as client:
            resp = await client.get(
                "https://api.telegram.org/bot" + token + "/getUpdates",
                params={
                    "offset":          _last_update_id + 1,
                    "timeout":         25,
                    "allowed_updates": ["message"],
                },
            )
            data = resp.json()
            if not data.get("ok"):
                return
            for upd in data.get("result", []):
                _last_update_id = upd["update_id"]
                await handle_update(upd)
    except Exception as e:
        log.debug("Poll error: " + str(e))


# ── Scheduler task ────────────────────────────────────────────────────────────
async def run_scheduled_post(topic: str, style: str):
    log.info("Scheduled post | " + topic + " | " + style)
    try:
        post = await generate_post(topic, style)
        ok   = await publish_telegram(post)

        if ok:
            STATS["posts_sent"] += 1
        else:
            STATS["errors"] += 1

        STATS["last_post"] = datetime.now().isoformat()
        STATS.setdefault("history", []).append({
            "time":    datetime.now().isoformat(),
            "topic":   topic,
            "style":   style,
            "preview": post.get("preview_text", ""),
            "ok":      ok,
        })
        STATS["history"] = STATS["history"][-100:]
        save_stats(STATS)

    except Exception as e:
        log.error("Post error: " + str(e))
        STATS["errors"] += 1
        save_stats(STATS)


async def start_scheduler():
    sch = AsyncIOScheduler(timezone="Europe/Chisinau")
    day_names = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

    for weekday, tasks in WEEKLY_PLAN.items():
        for t in tasks:
            sch.add_job(
                run_scheduled_post,
                CronTrigger(
                    day_of_week=day_names[weekday],
                    hour=t["hour"],
                    minute=t["minute"],
                ),
                args=[t["topic"], t["style"]],
                replace_existing=True,
            )

    sch.add_job(poll, "interval", seconds=3, id="tg_poll")
    sch.start()

    total = sum(len(v) for v in WEEKLY_PLAN.values())
    log.info("Scheduler: " + str(total) + " posts/week + polling every 3s")
    return sch
