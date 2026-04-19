"errors"] += 1
        STATS["last_post"] = datetime.now().isoformat()
        STATS.setdefault("history",[]).append({
            "time":datetime.now().isoformat(),"topic":topic,"style":style,
            "preview":post.get("preview_text",""),"ok":ok
        })
        STATS["history"] = STATS["history"][-100:]
        save_stats(STATS)
    except Exception as e:
        log.error(f"❌ Пост не отправлен: {e}")
        STATS["errors"] += 1
        save_stats(STATS)

async def start_scheduler():
    tz  = "Europe/Chisinau"
    sch = AsyncIOScheduler(timezone=tz)
    day_names = ["mon","tue","wed","thu","fri","sat","sun"]

    for weekday, tasks in WEEKLY_PLAN.items():
        for t in tasks:
            sch.add_job(
                run_scheduled_post,
                CronTrigger(day_of_week=day_names[weekday], hour=t["hour"], minute=t["minute"]),
                args=[t["topic"], t["style"]],
                replace_existing=True,
            )

    sch.add_job(poll, "interval", seconds=3, id="tg_poll")
    sch.start()

    posts_week = sum(len(v) for v in WEEKLY_PLAN.values())
    log.info(f"📅 Scheduler: {posts_week} постов/нед + polling каждые 3с")
    return sch
