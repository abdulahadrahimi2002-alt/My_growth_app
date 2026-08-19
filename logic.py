import hashlib
import json
import secrets
import sqlite3
from datetime import date, datetime, timedelta

DB_FILE = "mygrowth.db"

TRANSLATIONS = {
    "dari": {
        "title": "🚀 سیستم مدیریت رشد شخصی",
        "login": "ورود به حساب",
        "register": "ساخت حساب جدید",
        "username": "نام کاربری",
        "password": "رمز عبور",
        "email": "ایمیل",
        "login_btn": "ورود",
        "reg_btn": "ثبت‌نام",
        "logout": "🚪 خروج از حساب",
        "lang_select": "🌐 تغییر زبان / Language",
        "dashboard": "🏠 داشبورد",
        "daily_record": "📅 ثبت امروز",
        "habits": "🔁 مدیریت عادت‌ها",
        "tasks": "📝 لیست کارها",
        "goals": "🎯 اهداف",
        "growth": "📈 روند رشد",
        "achievements": "🏆 دستاوردها",
        "smart_analysis": "🧠 تحلیل هوشمند",
        "journal": "🙂 ژورنال روزانه",
        "sleep": "😴 پایش خواب",
        "settings": "⚙️ تنظیمات",
        "streak": "تداوم فعلی",
        "today_perf": "عملکرد امروز",
        "avg_30": "میانگین ۳۰ روز",
        "status": "ارزیابی وضعیت",
        "save": "💾 ذخیره",
        "excellent": "🟢 عالی",
        "good": "🔵 خوب",
        "medium": "🟡 متوسط",
        "poor": "🔴 ضعیف",
    },
    "en": {
        "title": "🚀 Personal Growth System",
        "login": "Login",
        "register": "Register",
        "username": "Username",
        "password": "Password",
        "email": "Email",
        "login_btn": "Login",
        "reg_btn": "Sign Up",
        "logout": "🚪 Logout",
        "lang_select": "🌐 Language / تغییر زبان",
        "dashboard": "🏠 Dashboard",
        "daily_record": "📅 Daily Record",
        "habits": "🔁 Habits Management",
        "tasks": "📝 Tasks List",
        "goals": "🎯 Goals",
        "growth": "📈 Growth Chart",
        "achievements": "🏆 Achievements",
        "smart_analysis": "🧠 Smart Analysis",
        "journal": "🙂 Daily Journal",
        "sleep": "😴 Sleep Tracker",
        "settings": "⚙️ Settings",
        "streak": "Current Streak",
        "today_perf": "Today's Performance",
        "avg_30": "30-Day Average",
        "status": "Status Evaluation",
        "save": "💾 Save",
        "excellent": "🟢 Excellent",
        "good": "🔵 Good",
        "medium": "🟡 Medium",
        "poor": "🔴 Poor",
    },
}


def get_status_info(percent, lang="dari"):
    t = TRANSLATIONS.get(lang, TRANSLATIONS["dari"])
    if percent >= 85:
        return t["excellent"]
    elif percent >= 70:
        return t["good"]
    elif percent >= 50:
        return t["medium"]
    else:
        return t["poor"]


def db():
    con = sqlite3.connect(DB_FILE)
    con.execute("PRAGMA foreign_keys = ON")
    return con


def hash_password(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 210_000)
    return salt.hex() + ":" + digest.hex()


def verify_password(password, stored):
    try:
        salt_hex, digest_hex = stored.split(":")
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), 210_000
        )
        return secrets.compare_digest(digest.hex(), digest_hex)
    except Exception:
        return False


def init_db():
    con = db()
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            language TEXT DEFAULT 'dari',
            created_at TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            category TEXT DEFAULT 'General',
            weight REAL DEFAULT 10,
            active INTEGER DEFAULT 1,
            created_at TEXT,
            UNIQUE(user_id, name),
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            record_date TEXT NOT NULL,
            percent REAL NOT NULL,
            details TEXT DEFAULT '{}',
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(user_id, record_date)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            task_date TEXT NOT NULL,
            title TEXT NOT NULL,
            priority TEXT DEFAULT 'normal',
            done INTEGER DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            deadline TEXT,
            progress INTEGER DEFAULT 0,
            category TEXT DEFAULT 'General',
            created_at TEXT DEFAULT '',
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS journal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            note_date TEXT NOT NULL,
            mood TEXT,
            note TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(user_id, note_date)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sleep (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            sleep_date TEXT NOT NULL,
            hours REAL DEFAULT 0,
            quality INTEGER DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(user_id, sleep_date)
        )
    """)
    con.commit()
    con.close()


def authenticate(username, password):
    con = db()
    con.row_factory = sqlite3.Row
    row = con.execute(
        "SELECT * FROM users WHERE LOWER(username)=LOWER(?)", (username.strip(),)
    ).fetchone()
    con.close()
    if row and verify_password(password, row["password_hash"]):
        return dict(row)
    return None


def create_user(username, email, password, language="dari"):
    username_clean = username.strip()
    email_clean = email.strip().lower()

    if not username_clean or not email_clean or not password:
        return False, "لطفاً تمامی فیلدها را پر کنید / Please fill all fields."

    con = db()
    cur = con.cursor()

    existing = cur.execute(
        "SELECT id FROM users WHERE LOWER(username)=? OR LOWER(email)=?",
        (username_clean.lower(), email_clean),
    ).fetchone()

    if existing:
        con.close()
        return False, "این نام کاربری یا ایمیل قبلاً ثبت شده است."

    try:
        now_iso = datetime.now().isoformat()
        cur.execute(
            "INSERT INTO users (username,email,password_hash,language,created_at)"
            " VALUES(?,?,?,?,?)",
            (username_clean, email_clean, hash_password(password), language, now_iso),
        )
        user_id = cur.lastrowid

        default_habits = [
            ("مطالعه / Reading", "یادگیری", 30),
            ("ورزش / Workout", "سلامت", 30),
            ("مطالعه چینی / Chinese", "یادگیری", 20),
            ("کدنویسی پایتون / Python", "مهارت", 20),
        ]
        for name, category, weight in default_habits:
            cur.execute(
                "INSERT INTO habits (user_id,name,category,weight,created_at)"
                " VALUES(?,?,?,?,?)",
                (user_id, name, category, weight, now_iso),
            )

        con.commit()
        return True, "حساب با موفقیت ساخته شد!"
    except Exception as e:
        con.rollback()
        return False, f"خطا: {str(e)}"
    finally:
        con.close()


def ensure_user_habits(user_id):
    con = db()
    cur = con.cursor()
    cnt = cur.execute(
        "SELECT COUNT(*) FROM habits WHERE user_id=?", (user_id,)
    ).fetchone()[0]
    if cnt == 0:
        now_iso = datetime.now().isoformat()
        default_habits = [
            ("مطالعه / Reading", "یادگیری", 30),
            ("ورزش / Workout", "سلامت", 30),
            ("مطالعه چینی / Chinese", "یادگیری", 20),
            ("کدنویسی پایتون / Python", "مهارت", 20),
        ]
        for name, category, weight in default_habits:
            cur.execute(
                "INSERT INTO habits (user_id,name,category,weight,created_at)"
                " VALUES(?,?,?,?,?)",
                (user_id, name, category, weight, now_iso),
            )
        con.commit()
    con.close()


def get_records(user_id):
    con = db()
    rows = con.execute(
        "SELECT record_date,percent,details FROM records WHERE user_id=? ORDER BY"
        " record_date ASC",
        (user_id,),
    ).fetchall()
    con.close()
    result = {}
    for d, percent, details in rows:
        try:
            details_dict = json.loads(details or "{}")
        except Exception:
            details_dict = {}
        result[d] = {"percent": percent, "details": details_dict}
    return result


def get_habits(user_id):
    ensure_user_habits(user_id)
    con = db()
    rows = con.execute(
        "SELECT id,name,category,weight,active FROM habits WHERE user_id=? ORDER BY id",
        (user_id,),
    ).fetchall()
    con.close()
    return rows


def add_habit(user_id, name, category, weight):
    con = db()
    try:
        now_iso = datetime.now().isoformat()
        con.execute(
            "INSERT INTO habits (user_id,name,category,weight,created_at)"
            " VALUES(?,?,?,?,?)",
            (user_id, name.strip(), category.strip(), weight, now_iso),
        )
        con.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        con.close()


def save_record(user_id, record_date, percent, details):
    con = db()
    details_json = json.dumps(details, ensure_ascii=False)
    con.execute(
        """
        INSERT INTO records (user_id,record_date,percent,details) VALUES(?,?,?,?)
        ON CONFLICT(user_id,record_date) DO UPDATE SET percent=excluded.percent, details=excluded.details
    """,
        (user_id, record_date, percent, details_json),
    )
    con.commit()
    con.close()


def calculate_streak(records):
    if not records:
        return 0
    dates = sorted([date.fromisoformat(x) for x in records.keys()], reverse=True)
    today = date.today()
    if dates[0] < today - timedelta(days=1):
        return 0
    check = today if dates[0] == today else today - timedelta(days=1)
    streak = 0
    for d in dates:
        if d == check:
            streak += 1
            check -= timedelta(days=1)
        elif d < check:
            break
    return streak


def get_tasks(user_id, task_date):
    con = db()
    rows = con.execute(
        "SELECT id, title, priority, done FROM tasks WHERE user_id=? AND"
        " task_date=?",
        (user_id, str(task_date)),
    ).fetchall()
    con.close()
    return rows


def add_task(user_id, task_date, title, priority):
    con = db()
    con.execute(
        "INSERT INTO tasks (user_id, task_date, title, priority) VALUES"
        " (?,?,?,?)",
        (user_id, str(task_date), title.strip(), priority),
    )
    con.commit()
    con.close()


def toggle_task(task_id, done_status):
    con = db()
    con.execute(
        "UPDATE tasks SET done=? WHERE id=?", (1 if done_status else 0, task_id)
    )
    con.commit()
    con.close()


def get_goals(user_id):
    con = db()
    rows = con.execute(
        "SELECT id, title, description, deadline, progress, category FROM"
        " goals WHERE user_id=? ORDER BY id DESC",
        (user_id,),
    ).fetchall()
    con.close()
    return rows


def add_goal(user_id, title, description, deadline, category):
    con = db()
    now_iso = datetime.now().isoformat()
    con.execute(
        "INSERT INTO goals (user_id, title, description, deadline, category,"
        " created_at) VALUES (?,?,?,?,?,?)",
        (
            user_id,
            title.strip(),
            description.strip(),
            str(deadline),
            category,
            now_iso,
        ),
    )
    con.commit()
    con.close()


def update_goal_progress(goal_id, progress):
    con = db()
    con.execute("UPDATE goals SET progress=? WHERE id=?", (progress, goal_id))
    con.commit()
    con.close()


def get_journal(user_id, note_date):
    con = db()
    row = con.execute(
        "SELECT mood, note FROM journal WHERE user_id=? AND note_date=?",
        (user_id, str(note_date)),
    ).fetchone()
    con.close()
    return row


def save_journal(user_id, note_date, mood, note):
    con = db()
    con.execute(
        """
        INSERT INTO journal (user_id, note_date, mood, note) VALUES (?,?,?,?)
        ON CONFLICT(user_id, note_date) DO UPDATE SET mood=excluded.mood, note=excluded.note
    """,
        (user_id, note_date, mood, note),
    )
    con.commit()
    con.close()


def get_sleep(user_id, sleep_date):
    con = db()
    row = con.execute(
        "SELECT hours, quality FROM sleep WHERE user_id=? AND sleep_date=?",
        (user_id, str(sleep_date)),
    ).fetchone()
    con.close()
    return row


def save_sleep(user_id, sleep_date, hours, quality):
    con = db()
    con.execute(
        """
        INSERT INTO sleep (user_id, sleep_date, hours, quality) VALUES (?,?,?,?)
        ON CONFLICT(user_id, sleep_date) DO UPDATE SET hours=excluded.hours, quality=excluded.quality
    """,
        (user_id, sleep_date, hours, quality),
    )
    con.commit()
    con.close()


def update_user_lang(user_id, lang):
    con = db()
    con.execute("UPDATE users SET language=? WHERE id=?", (lang, user_id))
    con.commit()
    con.close()


init_db()
        
