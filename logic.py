import hashlib
import json
import sqlite3
from datetime import date, timedelta

DB_FILE = "growth_app.db"

TRANSLATIONS = {
    "dari": {
        "title": "🚀 سیستم مدیریت رشد شخصی",
        "login": "ورود",
        "register": "ثبت‌نام",
        "username": "نام کاربری",
        "password": "رمز عبور",
        "email": "ایمیل",
        "login_btn": "ورود به حساب",
        "reg_btn": "ایجاد حساب",
        "dashboard": "📊 داشبورد",
        "daily_record": "📅 ثبت امروز",
        "habits": "🛠️ مدیریت عادت‌ها",
        "tasks": "📋 لیست کارها",
        "goals": "🎯 اهداف",
        "growth": "📈 روند رشد",
        "achievements": "🏆 دستاوردها",
        "smart_analysis": "🧠 تحلیل هوشمند",
        "journal": "😐 ژورنال روزانه",
        "sleep": "😴 پایش خواب",
        "settings": "⚙️ تنظیمات",
        "logout": "🚪 خروج از حساب",
        "lang_select": "🌐 تغییر زبان",
        "streak": "تداوم ثبت (روز)",
        "today_perf": "عملکرد امروز",
        "avg_30": "میانگین ۳۰ روز",
        "status": "وضعیت",
        "save": "💾 ذخیره‌سازی",
    },
    "en": {
        "title": "🚀 Personal Growth System",
        "login": "Login",
        "register": "Register",
        "username": "Username",
        "password": "Password",
        "email": "Email",
        "login_btn": "Login",
        "reg_btn": "Register",
        "dashboard": "📊 Dashboard",
        "daily_record": "📅 Daily Record",
        "habits": "🛠️ Manage Habits",
        "tasks": "📋 Tasks",
        "goals": "🎯 Goals",
        "growth": "📈 Growth Trend",
        "achievements": "🏆 Achievements",
        "smart_analysis": "🧠 Smart Analysis",
        "journal": "😐 Daily Journal",
        "sleep": "😴 Sleep Tracker",
        "settings": "⚙️ Settings",
        "logout": "🚪 Logout",
        "lang_select": "🌐 Language Select",
        "streak": "Current Streak",
        "today_perf": "Today Performance",
        "avg_30": "30-Day Avg",
        "status": "Status",
        "save": "💾 Save Record",
    },
    "zh": {
        "title": "🚀 个人成长管理系统",
        "login": "登录",
        "register": "注册",
        "username": "用户名",
        "password": "密码",
        "email": "电子邮件",
        "login_btn": "登录",
        "reg_btn": "注册",
        "dashboard": "📊 仪表板",
        "daily_record": "📅 今日打卡",
        "habits": "🛠️ 习惯管理",
        "tasks": "📋 任务列表",
        "goals": "🎯 目标规划",
        "growth": "📈 成长趋势",
        "achievements": "🏆 成就徽章",
        "smart_analysis": "🧠 智能分析",
        "journal": "😐 每日日志",
        "sleep": "😴 睡眠监测",
        "settings": "⚙️ 设置",
        "logout": "🚪 退出登录",
        "lang_select": "🌐 选择语言",
        "streak": "连续打卡 (天)",
        "today_perf": "今日表现",
        "avg_30": "30天平均",
        "status": "状态",
        "save": "💾 保存记录",
    },
}


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def init_db():
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute(
        """CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        email TEXT,
        password TEXT,
        language TEXT DEFAULT 'dari'
    )"""
    )
    cur.execute(
        """CREATE TABLE IF NOT EXISTS habits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT,
        category TEXT,
        weight INTEGER,
        active INTEGER DEFAULT 1
    )"""
    )
    cur.execute(
        """CREATE TABLE IF NOT EXISTS records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        date TEXT,
        percent REAL,
        details TEXT
    )"""
    )
    cur.execute(
        """CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        date TEXT,
        title TEXT,
        priority TEXT,
        completed INTEGER DEFAULT 0
    )"""
    )
    cur.execute(
        """CREATE TABLE IF NOT EXISTS goals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT,
        description TEXT,
        deadline TEXT,
        progress INTEGER DEFAULT 0,
        category TEXT
    )"""
    )
    cur.execute(
        """CREATE TABLE IF NOT EXISTS journal (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        date TEXT,
        mood TEXT,
        note TEXT
    )"""
    )
    cur.execute(
        """CREATE TABLE IF NOT EXISTS sleep (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        date TEXT,
        hours REAL,
        quality INTEGER
    )"""
    )
    con.commit()
    con.close()


init_db()


def create_user(username, email, password, lang="dari"):
    init_db()
    valid_lang = lang if lang in TRANSLATIONS else "dari"
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    try:
        cur.execute(
            "INSERT INTO users (username, email, password, language) VALUES"
            " (?, ?, ?, ?)",
            (username, email, hash_password(password), valid_lang),
        )
        con.commit()
        con.close()
        return True, "حساب کاربری ساخته شد."
    except sqlite3.IntegrityError:
        con.close()
        return False, "این نام کاربری قبلاً ثبت شده است."


def authenticate(username, password):
    init_db()
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute(
        "SELECT id, username, email, language FROM users WHERE username=? AND"
        " password=?",
        (username, hash_password(password)),
    )
    user = cur.fetchone()
    con.close()
    if user:
        lang = user[3] if user[3] in TRANSLATIONS else "dari"
        return {
            "id": user[0],
            "username": user[1],
            "email": user[2],
            "language": lang,
        }
    return None


def update_user_lang(user_id, lang):
    init_db()
    valid_lang = lang if lang in TRANSLATIONS else "dari"
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute("UPDATE users SET language=? WHERE id=?", (valid_lang, user_id))
    con.commit()
    con.close()


def ensure_user_habits(user_id):
    init_db()
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute("SELECT COUNT(*) FROM habits WHERE user_id=?", (user_id,))
    if cur.fetchone()[0] == 0:
        defaults = [
            ("ورزش", "سلامت", 25),
            ("مطالعه انگلیسی", "یادگیری", 25),
            ("مطالعه چینی", "یادگیری", 25),
            ("برنامه‌نویسی پایتون", "مهارت", 25),
        ]
        for name, cat, w in defaults:
            cur.execute(
                "INSERT INTO habits (user_id, name, category, weight) VALUES"
                " (?, ?, ?, ?)",
                (user_id, name, cat, w),
            )
        con.commit()
    con.close()


def get_habits(user_id):
    init_db()
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute(
        "SELECT id, name, category, weight, active FROM habits WHERE user_id=?"
        " AND active=1",
        (user_id,),
    )
    res = cur.fetchall()
    con.close()
    return res


def add_habit(user_id, name, cat, weight):
    init_db()
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute(
        "INSERT INTO habits (user_id, name, category, weight) VALUES (?, ?,"
        " ?, ?)",
        (user_id, name, cat, weight),
    )
    con.commit()
    con.close()
    return True


def save_record(user_id, d_str, percent, details):
    init_db()
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    details_json = json.dumps(details, ensure_ascii=False)
    cur.execute(
        "SELECT id FROM records WHERE user_id=? AND date=?", (user_id, d_str)
    )
    row = cur.fetchone()
    if row:
        cur.execute(
            "UPDATE records SET percent=?, details=? WHERE id=?",
            (percent, details_json, row[0]),
        )
    else:
        cur.execute(
            "INSERT INTO records (user_id, date, percent, details) VALUES (?, ?,"
            " ?, ?)",
            (user_id, d_str, percent, details_json),
        )
    con.commit()
    con.close()


def get_records(user_id):
    init_db()
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute(
        "SELECT date, percent, details FROM records WHERE user_id=? ORDER BY"
        " date ASC",
        (user_id,),
    )
    rows = cur.fetchall()
    con.close()
    records = {}
    for r in rows:
        records[r[0]] = {
            "percent": r[1],
            "details": json.loads(r[2]) if r[2] else {},
        }
    return records


def calculate_streak(records):
    if not records:
        return 0
    dates = sorted([date.fromisoformat(d) for d in records.keys()])
    today = date.today()
    if today not in dates and (today - timedelta(days=1)) not in dates:
        return 0
    streak = 0
    check_date = dates[-1]
    while check_date in dates:
        streak += 1
        check_date -= timedelta(days=1)
    return streak


def get_status_info(score, lang="dari"):
    if score >= 85:
        return (
            "🟢 عالی"
            if lang == "dari"
            else ("🟢 Excellent" if lang == "en" else "🟢 优秀")
        )
    elif score >= 70:
        return (
            "🟡 خوب"
            if lang == "dari"
            else ("🟡 Good" if lang == "en" else "🟡 良好")
        )
    elif score >= 50:
        return (
            "🟠 متوسط"
            if lang == "dari"
            else ("🟠 Average" if lang == "en" else "🟠 一般")
        )
    else:
        return (
            "🔴 ضعیف"
            if lang == "dari"
            else ("🔴 Poor" if lang == "en" else "🔴 较差")
        )


def get_tasks(user_id, t_date):
    init_db()
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute(
        "SELECT id, title, priority, completed FROM tasks WHERE user_id=? AND"
        " date=?",
        (user_id, str(t_date)),
    )
    res = cur.fetchall()
    con.close()
    return res


def add_task(user_id, t_date, title, priority):
    init_db()
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute(
        "INSERT INTO tasks (user_id, date, title, priority) VALUES (?, ?, ?,"
        " ?)",
        (user_id, str(t_date), title, priority),
    )
    con.commit()
    con.close()


def toggle_task(task_id, completed):
    init_db()
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute(
        "UPDATE tasks SET completed=? WHERE id=?", (1 if completed else 0, task_id)
    )
    con.commit()
    con.close()


def get_goals(user_id):
    init_db()
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute(
        "SELECT id, title, description, deadline, progress, category FROM goals"
        " WHERE user_id=?",
        (user_id,),
    )
    res = cur.fetchall()
    con.close()
    return res


def add_goal(user_id, title, desc, deadline, category):
    init_db()
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute(
        "INSERT INTO goals (user_id, title, description, deadline, category)"
        " VALUES (?, ?, ?, ?, ?)",
        (user_id, title, desc, str(deadline), category),
    )
    con.commit()
    con.close()


def update_goal_progress(goal_id, progress):
    init_db()
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute("UPDATE goals SET progress=? WHERE id=?", (progress, goal_id))
    con.commit()
    con.close()


def save_journal(user_id, j_date, mood, note):
    init_db()
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute(
        "SELECT id FROM journal WHERE user_id=? AND date=?",
        (user_id, str(j_date)),
    )
    row = cur.fetchone()
    if row:
        cur.execute(
            "UPDATE journal SET mood=?, note=? WHERE id=?", (mood, note, row[0])
        )
    else:
        cur.execute(
            "INSERT INTO journal (user_id, date, mood, note) VALUES (?, ?, ?,"
            " ?)",
            (user_id, str(j_date), mood, note),
        )
    con.commit()
    con.close()


def get_journal(user_id, j_date):
    init_db()
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute(
        "SELECT mood, note FROM journal WHERE user_id=? AND date=?",
        (user_id, str(j_date)),
    )
    res = cur.fetchone()
    con.close()
    return res


def save_sleep(user_id, s_date, hours, quality):
    init_db()
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute(
        "SELECT id FROM sleep WHERE user_id=? AND date=?", (user_id, str(s_date))
    )
    row = cur.fetchone()
    if row:
        cur.execute(
            "UPDATE sleep SET hours=?, quality=? WHERE id=?",
            (hours, quality, row[0]),
        )
    else:
        cur.execute(
            "INSERT INTO sleep (user_id, date, hours, quality) VALUES (?, ?, ?,"
            " ?)",
            (user_id, str(s_date), hours, quality),
        )
    con.commit()
    con.close()


def get_sleep(user_id, s_date):
    init_db()
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute(
        "SELECT hours, quality FROM sleep WHERE user_id=? AND date=?",
        (user_id, str(s_date)),
    )
    res = cur.fetchone()
    con.close()
    return res
    
