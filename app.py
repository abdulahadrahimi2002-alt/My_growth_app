# ============================================================
# MyGrowth Pro Max - Complete Personal Growth OS
# ============================================================

import streamlit as st
import sqlite3
import hashlib
import secrets
import json
import io
from datetime import date, datetime, timedelta
import pandas as pd
import plotly.graph_objects as go

# ============================================================
# CONFIG & CSS
# ============================================================

st.set_page_config(
    page_title="MyGrowth Pro Max",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_FILE = "mygrowth.db"

st.markdown("""
<style>
html, body, [class*="css"] { font-family: Arial, sans-serif; }
.main { direction: rtl; }
.block-container { padding-top: 1.2rem; max-width: 1500px; }
.stButton > button { width: 100%; border-radius: 10px; font-weight: 600; }
[data-testid="stMetric"] { background: rgba(255,255,255,.045); border: 1px solid rgba(255,255,255,.08); border-radius: 15px; padding: 12px; }
.hero { padding: 28px; border-radius: 20px; margin-bottom: 20px; background: linear-gradient(135deg, rgba(255,75,120,.18), rgba(100,80,255,.10)); border: 1px solid rgba(255,255,255,.08); }
.card { padding: 18px; border-radius: 16px; background: rgba(255,255,255,.035); border: 1px solid rgba(255,255,255,.07); margin-bottom: 12px; }
.badge { padding: 16px; border-radius: 15px; background: rgba(255,255,255,.04); border: 1px solid rgba(255,255,255,.08); margin: 8px 0; }
.muted { color: #9ca3af; }
.big-number { font-size: 34px; font-weight: 800; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# TRANSLATION
# ============================================================

TEXT = {
    "dari": {
        "language": "زبان",
        "title": "MyGrowth Pro Max",
        "subtitle": "سیستم شخصی مدیریت رشد، عادت‌ها، اهداف و زندگی روزانه",
        "login": "ورود",
        "register": "ثبت‌نام",
        "username": "نام کاربری",
        "email": "ایمیل",
        "password": "رمز عبور",
        "confirm": "تکرار رمز عبور",
        "login_btn": "ورود به حساب",
        "register_btn": "ساخت حساب",
        "logout": "خروج",
        "dashboard": "🏠 داشبورد",
        "today": "📅 امروز",
        "habits": "🔁 عادت‌ها",
        "tasks": "📝 کارها",
        "goals": "🎯 اهداف",
        "calendar": "🗓️ تقویم",
        "growth": "📈 رشد من",
        "badges": "🏆 دستاوردها",
        "insights": "🧠 تحلیل هوشمند",
        "journal": "🙂 ژورنال",
        "sleep": "😴 خواب",
        "settings": "⚙️ تنظیمات",
        "save": "💾 ذخیره",
        "add": "افزودن",
        "delete": "🗑️ حذف",
        "edit": "ویرایش",
        "done": "انجام شد",
        "cancel": "لغو",
        "weight": "وزن",
        "priority": "اولویت",
        "high": "مهم و فوری",
        "medium": "مهم",
        "normal": "عادی",
        "deadline": "مهلت",
        "progress": "پیشرفت",
        "today_performance": "عملکرد امروز",
        "average": "میانگین عملکرد",
        "weekly_average": "میانگین ۷ روز",
        "monthly_average": "میانگین ۳۰ روز",
        "records": "روزهای ثبت‌شده",
        "streak": "تداوم",
        "best": "بهترین عملکرد",
        "xp": "امتیاز XP",
        "level": "سطح",
        "tasks_today": "کارهای امروز",
        "active_goals": "اهداف فعال",
        "new_habit": "عادت جدید",
        "habit_name": "نام عادت",
        "new_task": "کار جدید",
        "new_goal": "هدف جدید",
        "goal_title": "عنوان هدف",
        "journal_title": "یادداشت امروز",
        "mood": "حال امروز",
        "energy": "انرژی",
        "focus": "تمرکز",
        "stress": "استرس",
        "sleep_hours": "ساعات خواب",
        "backup": "دانلود پشتیبان",
        "restore": "بازیابی پشتیبان",
        "export": "خروجی CSV",
        "excellent": "عالی",
        "good": "خوب",
        "average_status": "متوسط",
        "needs_effort": "نیاز به تلاش",
        "success": "با موفقیت ذخیره شد.",
    },
    "en": {
        "language": "Language",
        "title": "MyGrowth Pro Max",
        "subtitle": "Your personal growth, habits, goals and life management system",
        "login": "Login",
        "register": "Register",
        "username": "Username",
        "email": "Email",
        "password": "Password",
        "confirm": "Confirm password",
        "login_btn": "Log in",
        "register_btn": "Create account",
        "logout": "Logout",
        "dashboard": "🏠 Dashboard",
        "today": "📅 Today",
        "habits": "🔁 Habits",
        "tasks": "📝 Tasks",
        "goals": "🎯 Goals",
        "calendar": "🗓️ Calendar",
        "growth": "📈 My Growth",
        "badges": "🏆 Achievements",
        "insights": "🧠 Smart Insights",
        "journal": "🙂 Journal",
        "sleep": "😴 Sleep",
        "settings": "⚙️ Settings",
        "save": "💾 Save",
        "add": "Add",
        "delete": "🗑️ Delete",
        "edit": "Edit",
        "done": "Done",
        "cancel": "Cancel",
        "weight": "Weight",
        "priority": "Priority",
        "high": "High",
        "medium": "Medium",
        "normal": "Normal",
        "deadline": "Deadline",
        "progress": "Progress",
        "today_performance": "Today's performance",
        "average": "Average performance",
        "weekly_average": "7-Day average",
        "monthly_average": "30-Day average",
        "records": "Recorded days",
        "streak": "Streak",
        "best": "Best performance",
        "xp": "XP",
        "level": "Level",
        "tasks_today": "Today's tasks",
        "active_goals": "Active goals",
        "new_habit": "New habit",
        "habit_name": "Habit name",
        "new_task": "New task",
        "new_goal": "New goal",
        "goal_title": "Goal title",
        "journal_title": "Today's journal",
        "mood": "Today's mood",
        "energy": "Energy",
        "focus": "Focus",
        "stress": "Stress",
        "sleep_hours": "Sleep hours",
        "backup": "Download backup",
        "restore": "Restore backup",
        "export": "CSV export",
        "excellent": "Excellent",
        "good": "Good",
        "average_status": "Average",
        "needs_effort": "Needs effort",
        "success": "Saved successfully.",
    }
}

def tr(key):
    lang = st.session_state.get("lang", "dari")
    return TEXT.get(lang, TEXT["dari"]).get(key, key)

# ============================================================
# DATABASE & BACKEND FUNCTIONS
# ============================================================

def db():
    con = sqlite3.connect(DB_FILE)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con

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
            created_at TEXT NOT NULL,
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
            details TEXT NOT NULL,
            UNIQUE(user_id, record_date),
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
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
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            start_date TEXT,
            deadline TEXT,
            progress INTEGER DEFAULT 0,
            priority TEXT DEFAULT 'normal',
            done INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS journal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            journal_date TEXT NOT NULL,
            mood INTEGER DEFAULT 3,
            energy INTEGER DEFAULT 3,
            focus INTEGER DEFAULT 3,
            stress INTEGER DEFAULT 3,
            wins TEXT DEFAULT '',
            lesson TEXT DEFAULT '',
            tomorrow TEXT DEFAULT '',
            note TEXT DEFAULT '',
            UNIQUE(user_id, journal_date),
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sleep (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            sleep_date TEXT NOT NULL,
            hours REAL DEFAULT 0,
            quality INTEGER DEFAULT 3,
            UNIQUE(user_id, sleep_date),
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    con.commit()
    con.close()

init_db()

def hash_password(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 150000)
    return salt.hex() + ":" + digest.hex()

def verify_password(password, stored):
    try:
        salt, digest = stored.split(":")
        new_digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 150000)
        return secrets.compare_digest(new_digest.hex(), digest)
    except Exception:
        return False

def create_user(username, email, password, language):
    con = db()
    try:
        cur = con.cursor()
        cur.execute("""
            INSERT INTO users (username,email,password_hash,language,created_at)
            VALUES(?,?,?,?,?)
        """, (username.strip(), email.strip().lower(), hash_password(password), language, datetime.now().isoformat()))
        uid = cur.lastrowid
        defaults = [
            ("مطالعه", "Learning", 30),
            ("ورزش", "Health", 30),
            ("مطالعه چینی", "Learning", 20),
            ("کدنویسی پایتون", "Skill", 20),
        ]
        for name, category, weight in defaults:
            cur.execute("""
                INSERT INTO habits (user_id,name,category,weight,created_at)
                VALUES(?,?,?,?,?)
            """, (uid, name, category, weight, datetime.now().isoformat()))
        con.commit()
        return True
    except sqlite3.IntegrityError:
        con.rollback()
        return False
    finally:
        con.close()

def authenticate(username, password):
    con = db()
    row = con.execute("SELECT * FROM users WHERE username=?", (username.strip(),)).fetchone()
    con.close()
    if row and verify_password(password, row["password_hash"]):
        return row
    return None

def get_habits(uid):
    con = db()
    rows = con.execute("SELECT * FROM habits WHERE user_id=? AND active=1 ORDER BY id", (uid,)).fetchall()
    con.close()
    return [dict(r) for r in rows]

def add_habit(uid, name, category, weight):
    con = db()
    try:
        con.execute("INSERT INTO habits (user_id,name,category,weight,created_at) VALUES(?,?,?,?,?)",
                    (uid, name.strip(), category, weight, datetime.now().isoformat()))
        con.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        con.close()

def delete_habit(uid, hid):
    con = db()
    con.execute("UPDATE habits SET active=0 WHERE id=? AND user_id=?", (hid, uid))
    con.commit()
    con.close()

def get_records(uid):
    con = db()
    rows = con.execute("SELECT record_date,percent,details FROM records WHERE user_id=? ORDER BY record_date", (uid,)).fetchall()
    con.close()
    res = {}
    for r in rows:
        try: details = json.loads(r["details"])
        except: details = {}
        res[r["record_date"]] = {"percent": r["percent"], "details": details}
    return res

def save_record(uid, d, percent, details):
    con = db()
    con.execute("""
        INSERT INTO records (user_id,record_date,percent,details) VALUES(?,?,?,?)
        ON CONFLICT(user_id,record_date) DO UPDATE SET percent=excluded.percent, details=excluded.details
    """, (uid, d, percent, json.dumps(details, ensure_ascii=False)))
    con.commit()
    con.close()

def get_tasks(uid, task_date=None):
    con = db()
    if task_date:
        rows = con.execute("SELECT * FROM tasks WHERE user_id=? AND task_date=? ORDER BY done, id", (uid, task_date)).fetchall()
    else:
        rows = con.execute("SELECT * FROM tasks WHERE user_id=? ORDER BY task_date DESC, done, id", (uid,)).fetchall()
    con.close()
    return [dict(r) for r in rows]

def add_task(uid, d, title, priority):
    con = db()
    con.execute("INSERT INTO tasks (user_id,task_date,title,priority,created_at) VALUES(?,?,?,?,?)",
                (uid, d, title, priority, datetime.now().isoformat()))
    con.commit()
    con.close()

def toggle_task(uid, tid, done):
    con = db()
    con.execute("UPDATE tasks SET done=? WHERE id=? AND user_id=?", (int(done), tid, uid))
    con.commit()
    con.close()

def get_goals(uid):
    con = db()
    rows = con.execute("SELECT * FROM goals WHERE user_id=? ORDER BY done, deadline", (uid,)).fetchall()
    con.close()
    return [dict(r) for r in rows]

def add_goal(uid, title, description, start, deadline, priority):
    con = db()
    con.execute("INSERT INTO goals (user_id,title,description,start_date,deadline,priority,created_at) VALUES(?,?,?,?,?,?,?)",
                (uid, title, description, start, deadline, priority, datetime.now().isoformat()))
    con.commit()
    con.close()

def update_goal(uid, gid, progress, done):
    con = db()
    con.execute("UPDATE goals SET progress=?,done=? WHERE id=? AND user_id=?", (progress, int(done), gid, uid))
    con.commit()
    con.close()

def save_sleep(uid, d, hours, quality):
    con = db()
    con.execute("""
        INSERT INTO sleep (user_id,sleep_date,hours,quality) VALUES(?,?,?,?)
        ON CONFLICT(user_id,sleep_date) DO UPDATE SET hours=excluded.hours, quality=excluded.quality
    """, (uid, d, hours, quality))
    con.commit()
    con.close()

def save_journal(uid, d, mood, energy, focus, stress, note):
    con = db()
    con.execute("""
        INSERT INTO journal (user_id,journal_date,mood,energy,focus,stress,note) VALUES(?,?,?,?,?,?,?)
        ON CONFLICT(user_id,journal_date) DO UPDATE SET mood=excluded.mood, energy=excluded.energy, focus=excluded.focus, stress=excluded.stress, note=excluded.note
    """, (uid, d, mood, energy, focus, stress, note))
    con.commit()
    con.close()

# ============================================================
# INTERFACE LOGIC
# ============================================================

if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    st.title("🚀 MyGrowth Pro Max")
    tab1, tab2 = st.tabs([tr("login"), tr("register")])
    with tab1:
        u = st.text_input(tr("username"), key="l_u")
        p = st.text_input(tr("password"), type="password", key="l_p")
        if st.button(tr("login_btn")):
            usr = authenticate(u, p)
            if usr:
                st.session_state.user = usr
                st.session_state.lang = usr["language"]
                st.rerun()
            else:
                st.error("نام کاربری یا رمز عبور اشتباه است.")
    with tab2:
        ru = st.text_input(tr("username"), key="r_u")
        re = st.text_input(tr("email"), key="r_e")
        rp = st.text_input(tr("password"), type="password", key="r_p")
        rl = st.selectbox(tr("language"), ["dari", "en"], key="r_l")
        if st.button(tr("register_btn")):
            if create_user(ru, re, rp, rl):
                st.success("حساب با موفقیت ساخته شد. اکنون وارد شوید.")
            else:
                st.error("نام کاربری یا ایمیل تکراری است.")
else:
    user = st.session_state.user
    uid = user["id"]
    
    st.sidebar.title(f"👤 {user['username']}")
    if st.sidebar.button(tr("logout")):
        st.session_state.user = None
        st.rerun()

    menu = [
        tr("dashboard"), tr("today"), tr("habits"), tr("tasks"),
        tr("goals"), tr("growth"), tr("badges"), tr("insights"),
        tr("journal"), tr("sleep"), tr("settings")
    ]
    
    selected_tab = st.tabs(menu)

    # 1. Dashboard
    with selected_tab[0]:
        st.header(tr("dashboard"))
        records = get_records(uid)
        col1, col2, col3 = st.columns(3)
        col1.metric(tr("records"), len(records))
        col2.metric(tr("streak"), "🔥 3 روز")
        col3.metric(tr("xp"), "⭐ 150 XP")

    # 2. Today
    with selected_tab[1]:
        st.header(tr("today"))
        today_str = str(date.today())
        habits = get_habits(uid)
        tot_weight = sum([h['weight'] for h in habits]) or 1
        
        details = {}
        total_score = 0
        st.subheader("ثبت عملکرد عادت‌ها:")
        for h in habits:
            val = st.slider(f"{h['name']} (وزن: {h['weight']}%)", 0, 100, 50, key=f"today_{h['id']}")
            details[h['name']] = val
            total_score += (val * h['weight']) / tot_weight

        if st.button(tr("save")):
            save_record(uid, today_str, round(total_score, 1), details)
            st.success(tr("success"))

    # 3. Habits
    with selected_tab[2]:
        st.header(tr("habits"))
        habits = get_habits(uid)
        st.dataframe(pd.DataFrame(habits)[['id', 'name', 'category', 'weight']], use_container_width=True)
        
        st.subheader(tr("new_habit"))
        h_name = st.text_input(tr("habit_name"))
        h_cat = st.selectbox("دسته‌بندی", ["Learning", "Health", "Skill", "Spiritual"])
        h_weight = st.number_input(tr("weight"), 1, 100, 10)
        if st.button(tr("add")):
            if add_habit(uid, h_name, h_cat, h_weight):
                st.success(tr("success"))
                st.rerun()

    # 4. Tasks
    with selected_tab[3]:
        st.header(tr("tasks"))
        t_title = st.text_input(tr("new_task"))
        t_prio = st.selectbox(tr("priority"), [tr("high"), tr("medium"), tr("normal")])
        if st.button(tr("add") + " کار"):
            add_task(uid, str(date.today()), t_title, t_prio)
            st.rerun()
            
        tasks = get_tasks(uid)
        for t in tasks:
            col1, col2 = st.columns([0.8, 0.2])
            done = col1.checkbox(f"{t['title']} ({t['priority']})", value=bool(t['done']), key=f"t_{t['id']}")
            if done != bool(t['done']):
                toggle_task(uid, t['id'], done)
                st.rerun()

    # 5. Goals
    with selected_tab[4]:
        st.header(tr("goals"))
        g_title = st.text_input(tr("goal_title"))
        g_dl = st.date_input(tr("deadline"), date.today() + timedelta(days=30))
        if st.button(tr("add") + " هدف"):
            add_goal(uid, g_title, "", str(date.today()), str(g_dl), "normal")
            st.rerun()
            
        goals = get_goals(uid)
        st.dataframe(pd.DataFrame(goals), use_container_width=True)

    # 6. My Growth
  
