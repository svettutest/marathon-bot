"""
Telegram-бот «100 раз за раз» — Марафон приседаний от Утка Лав
14 дней • 5 режимов • Баллы • Лидерборд • Админ-панель
"""

import os
import json
import logging
import random
import asyncio
from datetime import datetime, timedelta, time as dtime
from pathlib import Path

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    WebAppInfo, ReplyKeyboardMarkup, KeyboardButton
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)
from aiohttp import web

# ── Logging ──
logging.basicConfig(format="%(asctime)s [%(levelname)s] %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ══════════════════════════════════════
# CONFIG
# ══════════════════════════════════════

BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
WEBAPP_URL = os.environ.get("WEBAPP_URL", "https://YOUR_WEBAPP_URL_HERE")
DATA_FILE = Path("data/users.json")

# Админы (Telegram ID)
ADMINS = [1375356950, 687943669]

# Ссылки бренда
BRAND = {
    "name": "Утка Лав",
    "instagram": "https://www.instagram.com/ytka___love/",
    "instagram_handle": "@ytka___love",
    "telegram": "https://t.me/privivka_zozh",
    "website": "https://ytka-health.online/chistoe_telo",
}

# ══════════════════════════════════════
# MODES
# ══════════════════════════════════════

MODES = {
    "10x10": {"sets": 10, "reps": 10, "label": "10 × 10", "emoji": "🌿", "difficulty": "Новичок"},
    "5x20":  {"sets": 5,  "reps": 20, "label": "5 × 20",  "emoji": "🌱", "difficulty": "Лёгкий"},
    "4x25":  {"sets": 4,  "reps": 25, "label": "4 × 25",  "emoji": "💪", "difficulty": "Средний"},
    "2x50":  {"sets": 2,  "reps": 50, "label": "2 × 50",  "emoji": "🔥", "difficulty": "Сложный"},
    "1x100": {"sets": 1,  "reps": 100,"label": "1 × 100", "emoji": "⚡", "difficulty": "Профи"},
}

# ══════════════════════════════════════
# DAILY CONTENT (14 дней)
# ══════════════════════════════════════

DAILY_CONTENT = [
    {"day": 1, "text": "Привет, красотка! Ты только что включила в работу более 200 мышц одновременно! Квадрицепсы, ягодицы, бицепс бедра, пресс - всё проснулось. Твоя попа получила первый мощный сигнал: «Пора подтягиваться!» Внешне пока ничего не видно, но внутри уже запущены процессы регенерации, которые тебя удивят."},
    {"day": 2, "text": "Если мышцы немного ноют - поздравляю, это значит, что мышцы реально работали! Крепатура - это микроповреждения волокон, после которых мышцы восстанавливаются и становятся ещё сильнее и более упругими. Кровообращение в тазу усилилось - это полезно для гормонального фона, кожи и женского здоровья."},
    {"day": 3, "text": "Тело начинает привыкать - движения более уверенные, приседать становится легче. Мозг выстраивает нейромышечные связи с ягодицами, а значит, с каждым днём ты активируешь их всё лучше. Улучшается микроциркуляция в коже бёдер и попы, клетки получают больше питания. Это фундамент для гладкой и упругой кожи."},
    {"day": 4, "text": "Связки и суставы укрепляются. Метаболизм становится быстрее - ты сжигаешь больше калорий, даже когда просто сидишь, так как мышечная ткань требует много энергии на восстановление. Потрогай свои ягодицы - они уже ощущаются плотнее и упругее, чем 4 дня назад! Так мышцы приходят в тонус."},
    {"day": 5, "text": "Организм вырабатывает больше гормона роста и эндорфинов - ты чувствуешь себя бодрее и счастливее. Мышцы ягодиц тонизируются и буквально «подтягивают» всё вверх. Первые комплименты могут прилететь уже скоро."},
    {"day": 6, "text": "Осанка выравнивается - ты стоишь ровнее и выглядишь стройнее. Ноги в зеркале кажутся более подтянутыми - не потому что ушёл жир, а потому что мышцы пришли в тонус и «собрали» силуэт. Даже привычные джинсы могут сесть по-другому!"},
    {"day": 7, "text": "Неделя! Ты большая умница! Тазобедренные суставы стали более подвижнее, баланс у тела лучше. А вот что видно в зеркале: внутренняя поверхность бёдер подтянулась, ягодицы округлились. Кожа на ногах выглядит более гладкой - усиленный кровоток и лимфодренаж делают своё дело. Целлюлит начинает сдавать позиции."},
    {"day": 8, "text": "Тот же объём приседаний даётся легче - это значит, что мышцы окрепли! Попа начинает выглядеть более «круглой» - это та самая форма, когда ягодицы визуально отделяются от задней поверхности бедра. Линия бедра сбоку стала более рельефной."},
    {"day": 9, "text": "Твоё тело теперь сжигает калории активнее даже в покое - мышечная ткань требует больше энергии. Окружающие начинают замечать изменения: «Ты что-то делаешь? Выглядишь свежее!» Приятно, правда?"},
    {"day": 10, "text": "Стресс снижается, энергии больше, настроение стабильно хорошее - спасибо эндорфинам! Кожа на бёдрах и ягодицах заметно более упругая и гладкая. Укреплённые мышцы создают ровную основу под кожей - бугорки целлюлита визуально сглаживаются."},
    {"day": 11, "text": "Отёчность ног уменьшается - лимфоток работает мощнее. Ноги выглядят «суше» и стройнее, щиколотки тоньше. Сердце натренировалось - пульс при нагрузке ниже. А твоя попа уже заметно отличается от той, что была 11 дней назад - она круглее, выше и плотнее."},
    {"day": 12, "text": "Ягодицы заметно приподнялись и округлились - это видно и в зеркале, и в одежде. Брюки и юбки сидят совсем иначе. Костная ткань стала плотнее - ты инвестируешь в здоровье на годы вперёд. Талия кажется тоньше, потому что бёдра и попа стали рельефнее - красивая пропорция!"},
    {"day": 13, "text": "Предпоследний день! Вспомни, как тяжело было в день 1, а сейчас это лёгкая разминка. Сила ног выросла минимум на 20%! Твоё тело в зеркале - более подтянутое, стройное, с красивым рельефом. Ты буквально лепишь себя приседаниями."},
    {"day": 14, "text": "ТЫ СДЕЛАЛА ЭТО! 1400 приседаний за 14 дней. Посмотри на себя: подтянутые ноги, приподнятая округлая попа, гладкая кожа на бёдрах, ровная осанка, стройный силуэт. Внутри - ускоренный метаболизм, крепкие кости, здоровый гормональный фон и железная сила воли. Ты - другой человек.\nСегодня ты обязательно сделаешь свой личный рекорд 100 раз за раз.\nТвоё тело готово!"},
]

REMINDER_MESSAGES = [
    "⏰ Подход {current} из {total} ждёт тебя! Твоя попа скажет спасибо 🍑",
    "🔔 Не забудь — подход {current} из {total}! Каждый раз — шаг к идеальной форме 💪",
    "💪 Пора приседать! Подход {current} из {total}. Ты справишься!",
    "🚀 Напоминалка! Подход {current} из {total}. Пару минут — и готово!",
    "⚡ Время подхода {current} из {total}! Давай, красотка! 🏋️",
]

# ══════════════════════════════════════
# DATA MANAGEMENT
# ══════════════════════════════════════

def load_data() -> dict:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data: dict):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_user(uid: str) -> dict | None:
    return load_data().get(str(uid))

def save_user(uid: str, u: dict):
    d = load_data(); d[str(uid)] = u; save_data(d)

def get_all_users() -> dict:
    return load_data()

def get_current_day(u: dict) -> int:
    start = datetime.strptime(u["start_date"], "%Y-%m-%d").date()
    return (datetime.now().date() - start).days + 1

def calc_streak(u: dict) -> int:
    day = min(get_current_day(u), 14)
    s = 0
    for d in range(day, 0, -1):
        if u["days"].get(str(d), {}).get("completed"): s += 1
        else: break
    return s

def calc_points(u: dict) -> dict:
    """Считает баллы: за приседания + за инстаграм"""
    squat_pts = sum(1 for d in u["days"].values() if d.get("completed"))
    insta_pts = u.get("instagram_points", 0)
    return {"squats": squat_pts, "instagram": insta_pts, "total": squat_pts + insta_pts}

# ══════════════════════════════════════
# HANDLERS: ONBOARDING
# ══════════════════════════════════════

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    user = get_user(uid)

    if user and user.get("setup_step") == "done":
        await show_main_menu(update, ctx, user)
        return

    await update.message.reply_text(
        f"🏋️ *Добро пожаловать в марафон «100 раз за раз»!*\n"
        f"от {BRAND['name']} 🦆\n\n"
        f"14 дней приседаний, которые изменят твоё тело!\n\n"
        f"Как тебя зовут?",
        parse_mode="Markdown"
    )
    ctx.user_data["step"] = "name"

async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    step = ctx.user_data.get("step")

    # ── Onboarding steps ──
    if step == "name":
        if len(text) < 1 or len(text) > 40:
            await update.message.reply_text("Введи имя покороче (1-40 символов) 😊")
            return
        uid = str(update.effective_user.id)
        u = {"name": text, "mode": None, "start_date": None, "reminder_times": [],
             "days": {}, "setup_step": "choose_mode", "instagram_points": 0,
             "tg_username": update.effective_user.username or ""}
        save_user(uid, u)
        ctx.user_data["step"] = None

        # Notify admins
        for admin_id in ADMINS:
            try:
                await ctx.bot.send_message(admin_id,
                    f"🆕 Новая участница!\n👤 {text}\n🆔 {uid}\nUsername: {u.get('tg_username') or 'нет'}")
            except: pass

        await update.message.reply_text(
            f"Привет, *{text}*! 🎉\nВыбери свой уровень:",
            parse_mode="Markdown", reply_markup=mode_keyboard())
        return

    if step == "set_time":
        await process_time_input(update, ctx, text)
        return

    # ── Main menu buttons ──
    if text == "📊 Мой прогресс":
        await cmd_progress(update, ctx)
    elif text == "✅ Отметить подход":
        await cmd_mark(update, ctx)
    elif text == "📸 Отправить скриншот":
        await update.message.reply_text(
            "📸 Отправь скриншот из Instagram с отметкой *@ytka___love*\n"
            "Просто пришли фото сюда в чат 👇",
            parse_mode="Markdown")
    elif text == "🏆 Лидерборд":
        await cmd_leaderboard(update, ctx)
    elif text == "⚙️ Настройки":
        await cmd_settings(update, ctx)
    elif text == "ℹ️ Помощь":
        await cmd_help(update, ctx)
    else:
        uid = str(update.effective_user.id)
        user = get_user(uid)
        if user and user.get("setup_step") == "done":
            await show_main_menu(update, ctx, user)
        else:
            await update.message.reply_text("Отправь /start чтобы начать марафон! 🏋️")

# ══════════════════════════════════════
# MODE SELECTION
# ══════════════════════════════════════

def mode_keyboard() -> InlineKeyboardMarkup:
    btns = []
    for mid, m in MODES.items():
        btns.append([InlineKeyboardButton(
            f"{m['emoji']} {m['label']} — {m['difficulty']}", callback_data=f"mode_{mid}")])
    return InlineKeyboardMarkup(btns)

async def cb_mode(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    mid = q.data.replace("mode_", "")
    if mid not in MODES: return

    uid = str(q.from_user.id)
    u = get_user(uid)
    if not u: return

    mode = MODES[mid]
    old_mode = u.get("mode")
    u["mode"] = mid

    # If changing mode mid-marathon
    if u.get("setup_step") == "done" and old_mode:
        day = get_current_day(u)
        if 1 <= day <= 14:
            d = u["days"].get(str(day), {})
            if not d.get("completed"):
                u["days"][str(day)] = {"sets_done": [False]*mode["sets"], "completed": False}
            # Future days
            for dd in range(day+1, 15):
                if not u["days"].get(str(dd), {}).get("completed"):
                    u["days"][str(dd)] = {"sets_done": [False]*mode["sets"], "completed": False}
        save_user(uid, u)
        await q.edit_message_text(
            f"✅ Режим изменён на *{mode['label']}* {mode['emoji']}\n"
            f"Подходы сегодня обновлены!", parse_mode="Markdown")
        return

    # First-time setup
    u["setup_step"] = "choose_time"
    save_user(uid, u)
    ctx.user_data["step"] = "set_time"

    await q.edit_message_text(
        f"Отлично! Режим: *{mode['label']}* {mode['emoji']}\n\n"
        f"Тебе нужно *{mode['sets']}* подход(а/ов) по *{mode['reps']}* приседаний в день.\n\n"
        f"Теперь отправь время для напоминаний через пробел:\n"
        f"Например: `08:00 12:00 18:00`\n\n"
        f"Количество напоминаний = сколько хочешь (не обязательно равно подходам).",
        parse_mode="Markdown")

# ══════════════════════════════════════
# TIME SETUP
# ══════════════════════════════════════

async def process_time_input(update: Update, ctx: ContextTypes.DEFAULT_TYPE, text: str):
    uid = str(update.effective_user.id)
    u = get_user(uid)
    if not u: return

    parts = text.replace(",", " ").replace(";", " ").split()
    times = []
    for t in parts:
        try:
            p = t.replace(".", ":").split(":")
            h, m = int(p[0]), int(p[1]) if len(p) > 1 else 0
            if 0 <= h <= 23 and 0 <= m <= 59:
                times.append(f"{h:02d}:{m:02d}")
            else: raise ValueError
        except:
            await update.message.reply_text(f"❌ Не понимаю «{t}». Формат: HH:MM (например 08:00 14:30 20:00)")
            return

    if not times:
        await update.message.reply_text("Отправь хотя бы одно время, например: `09:00`", parse_mode="Markdown")
        return

    times.sort()
    mode = MODES[u["mode"]]

    # If updating existing times
    if u.get("setup_step") == "done":
        u["reminder_times"] = times
        save_user(uid, u)
        await schedule_user_jobs(ctx, uid, u)
        ctx.user_data["step"] = None
        await update.message.reply_text(
            f"✅ Напоминания обновлены: *{', '.join(times)}*", parse_mode="Markdown")
        return

    # First-time setup — initialize marathon
    u["reminder_times"] = times
    u["start_date"] = datetime.now().strftime("%Y-%m-%d")
    u["setup_step"] = "done"
    for day in range(1, 15):
        u["days"][str(day)] = {"sets_done": [False]*mode["sets"], "completed": False}
    save_user(uid, u)
    ctx.user_data["step"] = None

    await schedule_user_jobs(ctx, uid, u)

    await update.message.reply_text(
        f"🎉 *Марафон начался!*\n\n"
        f"📋 Режим: *{mode['label']}* ({mode['difficulty']})\n"
        f"⏰ Напоминания: *{', '.join(times)}*\n"
        f"📅 Старт: *сегодня!*\n\n"
        f"Нажимай кнопки ниже 👇",
        parse_mode="Markdown", reply_markup=main_keyboard())

    # Send day 1 content
    await send_daily_content(ctx.bot, uid, u, 1)

# ══════════════════════════════════════
# MAIN MENU
# ══════════════════════════════════════

def main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup([
        [KeyboardButton("✅ Отметить подход"), KeyboardButton("📊 Мой прогресс")],
        [KeyboardButton("📸 Отправить скриншот"), KeyboardButton("🏆 Лидерборд")],
        [KeyboardButton("🏋️ Открыть трекер", web_app=WebAppInfo(url=WEBAPP_URL))],
        [KeyboardButton("⚙️ Настройки"), KeyboardButton("ℹ️ Помощь")],
    ], resize_keyboard=True)

async def show_main_menu(update: Update, ctx, u: dict):
    day = min(get_current_day(u), 15)
    mode = MODES[u["mode"]]
    pts = calc_points(u)

    if day > 14:
        await update.message.reply_text(
            f"🎊 *{u['name']}, марафон завершён!*\n🏆 Баллов: *{pts['total']}*",
            parse_mode="Markdown", reply_markup=main_keyboard())
        return

    dd = u["days"].get(str(day), {})
    sets_done = sum(dd.get("sets_done", []))

    await update.message.reply_text(
        f"👋 *{u['name']}*, день *{day}/14*\n"
        f"{mode['emoji']} {mode['label']} • Подходы: *{sets_done}/{mode['sets']}*\n"
        f"⭐ Баллов: *{pts['total']}* (🏋️{pts['squats']} + 📸{pts['instagram']})",
        parse_mode="Markdown", reply_markup=main_keyboard())

# ══════════════════════════════════════
# MARK SET
# ══════════════════════════════════════

async def cmd_mark(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    u = get_user(uid)
    if not u or u.get("setup_step") != "done":
        await update.message.reply_text("Сначала /start 🏋️"); return

    day = get_current_day(u)
    if day > 14:
        await update.message.reply_text("🎊 Марафон завершён!"); return
    if day < 1:
        await update.message.reply_text("Марафон ещё не начался!"); return

    mode = MODES[u["mode"]]
    dd = u["days"].get(str(day), {"sets_done": [False]*mode["sets"], "completed": False})

    nxt = None
    for i, done in enumerate(dd["sets_done"]):
        if not done: nxt = i; break

    if nxt is None:
        await update.message.reply_text("✨ Все подходы на сегодня выполнены! 🏆"); return

    dd["sets_done"][nxt] = True
    sets_done = sum(dd["sets_done"])

    if sets_done == mode["sets"]:
        dd["completed"] = True

    u["days"][str(day)] = dd
    save_user(uid, u)

    if dd["completed"]:
        pts = calc_points(u)
        streak = calc_streak(u)
        msg = (f"🎉 *Подход {sets_done}/{mode['sets']} — ГОТОВО!*\n\n"
               f"🏆 *ДЕНЬ {day} ЗАВЕРШЁН!* (+1 балл)\n"
               f"🔥 Серия: *{streak}* дней\n"
               f"⭐ Баллов: *{pts['total']}*")
        if day == 14:
            msg += "\n\n🎊 *МАРАФОН ЗАВЕРШЁН! ТЫ ЛЕГЕНДА!*"
        await update.message.reply_text(msg, parse_mode="Markdown")
    else:
        await update.message.reply_text(
            f"✅ *Подход {sets_done}/{mode['sets']}!*\n"
            f"Осталось *{mode['sets'] - sets_done}* 💪",
            parse_mode="Markdown")

# ══════════════════════════════════════
# PROGRESS
# ══════════════════════════════════════

async def cmd_progress(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    u = get_user(uid)
    if not u or u.get("setup_step") != "done":
        await update.message.reply_text("Сначала /start 🏋️"); return

    day = min(get_current_day(u), 15)
    mode = MODES[u["mode"]]
    pts = calc_points(u)
    streak = calc_streak(u)
    total_done = pts["squats"]

    cal = ""
    for d in range(1, 15):
        dd = u["days"].get(str(d), {})
        if dd.get("completed"): cal += "🟢"
        elif d == min(day, 14):
            cal += "🟡" if sum(dd.get("sets_done", [])) > 0 else "🔵"
        elif d < day: cal += "🔴"
        else: cal += "⚪"
        if d == 7: cal += "\n"

    filled = int(total_done / 14 * 14)
    bar = "█" * filled + "░" * (14 - filled)

    await update.message.reply_text(
        f"📊 *{u['name']}*\n\n"
        f"📅 День: *{min(day,14)}/14*\n"
        f"{mode['emoji']} Режим: *{mode['label']}*\n"
        f"🔥 Серия: *{streak}* дней\n"
        f"🦵 Приседаний: *{total_done * 100}*\n"
        f"⭐ Баллов: *{pts['total']}* (🏋️{pts['squats']} + 📸{pts['instagram']})\n\n"
        f"{cal}\n🟢✅ 🟡сегодня 🔵впереди 🔴пропуск\n\n"
        f"[{bar}] {int(total_done/14*100)}%",
        parse_mode="Markdown")

# ══════════════════════════════════════
# INSTAGRAM PROOF
# ══════════════════════════════════════

async def handle_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    u = get_user(uid)
    if not u or u.get("setup_step") != "done":
        return

    photo = update.message.photo[-1]  # Highest resolution
    file_id = photo.file_id
    day = min(get_current_day(u), 14)

    await update.message.reply_text(
        "📸 Скриншот получен! Отправляю на проверку админам.\n"
        "Как только подтвердят — тебе начислится бонусный балл ⭐")

    # Send to admins with approve/reject buttons
    for admin_id in ADMINS:
        try:
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Подтвердить (+1 балл)", callback_data=f"approve_{uid}_{day}")],
                [InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{uid}_{day}")],
            ])
            await ctx.bot.send_photo(
                admin_id, file_id,
                caption=(f"📸 Скриншот от участницы\n"
                         f"👤 {u['name']} (username: {u.get('tg_username') or 'нет'})\n"
                         f"📅 День {day}\n"
                         f"⭐ Текущие баллы: {calc_points(u)['total']}"),
                parse_mode=None, reply_markup=kb)
        except Exception as e:
            logger.error(f"Failed to send to admin {admin_id}: {e}")

async def cb_approve_reject(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    admin_id = q.from_user.id
    if admin_id not in ADMINS: return

    parts = q.data.split("_")
    action = parts[0]  # approve or reject
    uid = parts[1]
    day = parts[2]

    u = get_user(uid)
    if not u: return

    if action == "approve":
        u["instagram_points"] = u.get("instagram_points", 0) + 1
        save_user(uid, u)
        pts = calc_points(u)

        await q.edit_message_caption(
            caption=f"✅ *ПОДТВЕРЖДЕНО*\n👤 {u['name']} • День {day}\n⭐ Баллов: {pts['total']}",
            parse_mode="Markdown")

        # Notify participant
        try:
            await ctx.bot.send_message(int(uid),
                f"🎉 Твой скриншот подтверждён! *+1 бонусный балл!*\n⭐ Всего баллов: *{pts['total']}*",
                parse_mode="Markdown")
        except: pass

    elif action == "reject":
        await q.edit_message_caption(
            caption=f"❌ *ОТКЛОНЕНО*\n👤 {u['name']} • День {day}",
            parse_mode="Markdown")
        try:
            await ctx.bot.send_message(int(uid),
                "😔 К сожалению, скриншот не подтверждён. Убедись, что есть отметка @ytka___love и попробуй ещё раз!")
        except: pass

# ══════════════════════════════════════
# LEADERBOARD
# ══════════════════════════════════════

async def cmd_leaderboard(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    users = get_all_users()
    board = []
    for uid, u in users.items():
        if u.get("setup_step") != "done": continue
        pts = calc_points(u)
        board.append({"name": u["name"], "total": pts["total"],
                       "squats": pts["squats"], "insta": pts["instagram"]})

    board.sort(key=lambda x: x["total"], reverse=True)
    medals = ["🥇", "🥈", "🥉"]

    text = "🏆 *Лидерборд марафона*\n\n"
    for i, p in enumerate(board[:20]):
        medal = medals[i] if i < 3 else f"{i+1}."
        text += f"{medal} *{p['name']}* — {p['total']} ⭐ (🏋️{p['squats']} + 📸{p['insta']})\n"

    if not board:
        text += "Пока пусто — будь первой! 💪"

    await update.message.reply_text(text, parse_mode="Markdown")

# ══════════════════════════════════════
# SETTINGS
# ══════════════════════════════════════

async def cmd_settings(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    u = get_user(uid)
    if not u or u.get("setup_step") != "done": return

    mode = MODES[u["mode"]]
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Сменить режим", callback_data="s_mode")],
        [InlineKeyboardButton("⏰ Изменить время напоминаний", callback_data="s_time")],
        [InlineKeyboardButton("🔄 Начать заново", callback_data="s_reset")],
    ])
    await update.message.reply_text(
        f"⚙️ *Настройки*\n\n"
        f"👤 {u['name']}\n"
        f"{mode['emoji']} Режим: *{mode['label']}*\n"
        f"⏰ Напоминания: *{', '.join(u.get('reminder_times', []))}*\n\n"
        f"🔗 *{BRAND['name']}*\n"
        f"📷 [{BRAND['instagram_handle']}]({BRAND['instagram']})\n"
        f"💬 [Telegram]({BRAND['telegram']})\n"
        f"🌐 [Сайт]({BRAND['website']})",
        parse_mode="Markdown", reply_markup=kb, disable_web_page_preview=True)

async def cb_settings(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    uid = str(q.from_user.id)

    if q.data == "s_mode":
        await q.edit_message_text("Выбери новый режим:", reply_markup=mode_keyboard())

    elif q.data == "s_time":
        u = get_user(uid)
        if u:
            u["setup_step"] = "done"  # Keep done status
            save_user(uid, u)
        ctx.user_data["step"] = "set_time"
        await q.edit_message_text(
            "Отправь новое время напоминаний:\n`08:00 12:00 18:00`", parse_mode="Markdown")

    elif q.data == "s_reset":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Да, сбросить", callback_data="s_confirm_reset")],
            [InlineKeyboardButton("❌ Отмена", callback_data="s_cancel")],
        ])
        await q.edit_message_text("⚠️ Весь прогресс будет удалён! Уверена?", reply_markup=kb)

    elif q.data == "s_confirm_reset":
        d = load_data()
        if uid in d: del d[uid]
        save_data(d)
        await q.edit_message_text("🔄 Данные сброшены. Отправь /start!")

    elif q.data == "s_cancel":
        await q.edit_message_text("👍 Продолжаем марафон!")

# ══════════════════════════════════════
# HELP
# ══════════════════════════════════════

async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"ℹ️ *Марафон «100 раз за раз»*\nот {BRAND['name']} 🦆\n\n"
        f"Каждый день — 100 приседаний. 14 дней.\n\n"
        f"*Режимы:*\n"
        f"🌿 10×10 — Новичок\n🌱 5×20 — Лёгкий\n💪 4×25 — Средний\n🔥 2×50 — Сложный\n⚡ 1×100 — Профи\n\n"
        f"*Баллы:*\n"
        f"🏋️ 1 балл за каждый выполненный день\n"
        f"📸 +1 бонус за скриншот из Instagram с отметкой {BRAND['instagram_handle']}\n"
        f"Максимум: 28 баллов за марафон!\n\n"
        f"*Кнопки:*\n"
        f"✅ Отметить подход — засчитать\n"
        f"📸 Скриншот — отправить доказательство\n"
        f"📊 Прогресс — твоя статистика\n"
        f"🏆 Лидерборд — рейтинг участниц\n"
        f"⚙️ Настройки — сменить режим/время\n\n"
        f"📷 [{BRAND['instagram_handle']}]({BRAND['instagram']})\n"
        f"💬 [Telegram-канал]({BRAND['telegram']})\n"
        f"🌐 [Курс «Чистое тело, чистое сознание»]({BRAND['website']})",
        parse_mode="Markdown", disable_web_page_preview=True)

# ══════════════════════════════════════
# ADMIN COMMANDS
# ══════════════════════════════════════

async def cmd_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS:
        await update.message.reply_text("⛔ Только для админов"); return

    users = get_all_users()
    active = [u for u in users.values() if u.get("setup_step") == "done"]

    if not active:
        await update.message.reply_text("Пока нет участниц"); return

    modes_count = {}
    total_points = 0
    completed_marathons = 0

    for u in active:
        m = u.get("mode", "?")
        modes_count[m] = modes_count.get(m, 0) + 1
        pts = calc_points(u)
        total_points += pts["total"]
        done_days = pts["squats"]
        if done_days >= 14: completed_marathons += 1

    modes_str = "\n".join(f"  {MODES.get(m,{}).get('emoji','?')} {m}: {c}" for m, c in modes_count.items())

    await update.message.reply_text(
        f"📊 *Статистика марафона*\n\n"
        f"👥 Участниц: *{len(active)}*\n"
        f"🏆 Завершили марафон: *{completed_marathons}*\n"
        f"⭐ Всего баллов: *{total_points}*\n\n"
        f"*Режимы:*\n{modes_str}",
        parse_mode="Markdown")

async def cmd_export(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Экспорт данных для админов"""
    if update.effective_user.id not in ADMINS:
        await update.message.reply_text("⛔ Только для админов"); return

    users = get_all_users()
    lines = ["Имя;Username;Режим;День;Выполнено_дней;Баллы_присед;Баллы_инста;Всего_баллов;Серия"]
    for uid, u in users.items():
        if u.get("setup_step") != "done": continue
        pts = calc_points(u)
        day = min(get_current_day(u), 15)
        streak = calc_streak(u)
        lines.append(f"{u['name']};@{u.get('tg_username','')};{u.get('mode','')};{day};"
                      f"{pts['squats']};{pts['squats']};{pts['instagram']};{pts['total']};{streak}")

    csv_text = "\n".join(lines)
    from io import BytesIO
    buf = BytesIO(csv_text.encode("utf-8-sig"))
    buf.name = "marathon_export.csv"
    await update.message.reply_document(buf, caption="📊 Экспорт данных участниц")

# ══════════════════════════════════════
# REMINDERS & DAILY CONTENT
# ══════════════════════════════════════

async def schedule_user_jobs(ctx: ContextTypes.DEFAULT_TYPE, uid: str, u: dict):
    # Remove existing jobs
    for job in ctx.job_queue.get_jobs_by_name(f"r_{uid}"):
        job.schedule_removal()
    for job in ctx.job_queue.get_jobs_by_name(f"d_{uid}"):
        job.schedule_removal()

    times = u.get("reminder_times", [])
    for i, ts in enumerate(times):
        h, m = map(int, ts.split(":"))
        ctx.job_queue.run_daily(
            job_reminder, time=dtime(hour=h, minute=m),
            data={"uid": uid, "set_num": i+1, "total": len(times)},
            name=f"r_{uid}")

    # Daily content 5 min before first reminder
    if times:
        h, m = map(int, times[0].split(":"))
        m2 = m - 5 if m >= 5 else m + 55
        h2 = h if m >= 5 else (h - 1 if h > 0 else 23)
    else:
        h2, m2 = 8, 0
    ctx.job_queue.run_daily(
        job_daily_content, time=dtime(hour=h2, minute=m2),
        data={"uid": uid}, name=f"d_{uid}")

async def job_reminder(ctx: ContextTypes.DEFAULT_TYPE):
    d = ctx.job.data; uid = d["uid"]
    u = get_user(uid)
    if not u or u.get("setup_step") != "done": return
    day = get_current_day(u)
    if day > 14 or day < 1: return

    dd = u["days"].get(str(day), {})
    if dd.get("completed"): return

    msg = random.choice(REMINDER_MESSAGES).format(current=d["set_num"], total=d["total"])
    try: await ctx.bot.send_message(int(uid), msg)
    except: pass

async def job_daily_content(ctx: ContextTypes.DEFAULT_TYPE):
    uid = ctx.job.data["uid"]
    u = get_user(uid)
    if not u or u.get("setup_step") != "done": return
    day = get_current_day(u)
    if day < 1 or day > 14: return
    await send_daily_content(ctx.bot, uid, u, day)

async def send_daily_content(bot, uid: str, u: dict, day: int):
    if day < 1 or day > 14: return
    content = DAILY_CONTENT[day - 1]
    mode = MODES[u["mode"]]
    try:
        await bot.send_message(int(uid),
            f"🌅 *День {day} из 14*\n\n"
            f"{content['text']}\n\n"
            f"Сегодня: *{mode['sets']}* подход(а/ов) по *{mode['reps']}* приседаний.\n"
            f"Удачи! 🏋️",
            parse_mode="Markdown")
    except: pass

# ══════════════════════════════════════
# RESTORE JOBS ON STARTUP
# ══════════════════════════════════════

async def post_init(app: Application):
    """Restore reminder jobs for all active users on bot restart"""
    users = get_all_users()
    count = 0
    for uid, u in users.items():
        if u.get("setup_step") == "done":
            day = get_current_day(u)
            if 1 <= day <= 14:
                await schedule_user_jobs(app, uid, u)
                count += 1
    logger.info(f"Restored jobs for {count} active users")

# ══════════════════════════════════════
# API FOR MINI APP
# ══════════════════════════════════════

async def api_get_user(request):
    uid = request.query.get("id")
    if not uid: return web.json_response({"error": "Missing id"}, status=400)
    u = get_user(uid)
    if not u: return web.json_response({"error": "Not found"}, status=404)
    day = get_current_day(u)
    mode = MODES.get(u.get("mode", "4x25"))
    pts = calc_points(u)
    return web.json_response({
        **u, "current_day": min(day, 15), "mode_info": mode,
        "daily_content": DAILY_CONTENT[min(day, 14)-1] if 1 <= day <= 14 else None,
        "streak": calc_streak(u), "points": pts,
        "total_days_done": pts["squats"], "total_squats": pts["squats"] * 100,
        "modes": MODES, "brand": BRAND,
    })

async def api_mark_set(request):
    try:
        data = await request.json()
        uid = str(data["user_id"]); day = data["day"]; si = data["set_index"]
        u = get_user(uid)
        if not u: return web.json_response({"error": "Not found"}, status=404)
        ds = str(day)
        if ds not in u["days"]: return web.json_response({"error": "Bad day"}, status=400)
        mode = MODES[u["mode"]]
        if si < 0 or si >= mode["sets"]: return web.json_response({"error": "Bad set"}, status=400)
        u["days"][ds]["sets_done"][si] = True
        if all(u["days"][ds]["sets_done"]): u["days"][ds]["completed"] = True
        save_user(uid, u)
        pts = calc_points(u)
        return web.json_response({"ok": True, "day_data": u["days"][ds],
            "streak": calc_streak(u), "points": pts})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

async def api_change_mode(request):
    try:
        data = await request.json()
        uid = str(data["user_id"]); new_mode = data["mode"]
        if new_mode not in MODES: return web.json_response({"error": "Bad mode"}, status=400)
        u = get_user(uid)
        if not u: return web.json_response({"error": "Not found"}, status=404)
        mode = MODES[new_mode]; u["mode"] = new_mode
        day = get_current_day(u)
        for d in range(max(day, 1), 15):
            if not u["days"].get(str(d), {}).get("completed"):
                u["days"][str(d)] = {"sets_done": [False]*mode["sets"], "completed": False}
        save_user(uid, u)
        return web.json_response({"ok": True, "mode_info": mode, "days": u["days"]})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

async def api_content(request):
    day = request.query.get("day")
    try:
        d = int(day)
        if 1 <= d <= 14: return web.json_response(DAILY_CONTENT[d-1])
    except: pass
    return web.json_response({"error": "Bad day"}, status=400)

async def run_web_server():
    app = web.Application()
    app.router.add_get("/api/user", api_get_user)
    app.router.add_post("/api/mark_set", api_mark_set)
    app.router.add_post("/api/change_mode", api_change_mode)
    app.router.add_get("/api/content", api_content)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    logger.info("Web server on :8080")

# ══════════════════════════════════════
# MAIN
# ══════════════════════════════════════

def main():
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    # Handlers
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("export", cmd_export))
    app.add_handler(CallbackQueryHandler(cb_mode, pattern=r"^mode_"))
    app.add_handler(CallbackQueryHandler(cb_approve_reject, pattern=r"^(approve|reject)_"))
    app.add_handler(CallbackQueryHandler(cb_settings, pattern=r"^s_"))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_web_server())
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
