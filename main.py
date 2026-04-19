"""
МК-ГРУПП Autopilot — точка входа
Запускает автопилот + веб-дашборд параллельно
"""
import asyncio, logging, os
from aiohttp import web

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("autopilot.log", encoding="utf-8"),
    ],
)
log = logging.getLogger("autopilot")

async def main():
    log.info("═"*55)
    log.info("🚀 МК-ГРУПП AI AUTOPILOT v2 ЗАПУЩЕН")
    log.info(f"   Канал    : {os.getenv('TELEGRAM_CHANNEL_ID','⚠️ не задан')}")
    log.info(f"   CRM      : {'✅ Make.com' if os.getenv('SHEETS_WEBHOOK_URL') else '⚠️ не задан'}")
    log.info(f"   Notify   : {os.getenv('LEAD_NOTIFY_CHAT_ID','⚠️ не задан')}")
    log.info("═"*55)

    # Импортируем после настройки логгера
    from engine import start_scheduler
    from dashboard import create_app

    # Запускаем планировщик (постинг + polling)
    scheduler = await start_scheduler()

    # Запускаем веб-дашборд
    port = int(os.getenv("PORT", 8080))
    app  = create_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    log.info(f"🌐 Dashboard: http://0.0.0.0:{port}")

    # Держим процесс
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
