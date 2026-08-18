# ============================================================
# MyGrowth Pro Max - Fixed UI & Tabs
# ============================================================

import streamlit as st
import sqlite3
import hashlib
import secrets
import json
from datetime import date, datetime, timedelta
import pandas as pd

# ============================================================
# CONFIG & ENHANCED CSS
# ============================================================

st.set_page_config(
    page_title="MyGrowth Pro Max",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_FILE = "mygrowth.db"

# CSS اختصاصی برای اصلاح کامل تب‌ها و کادرها
st.markdown("""
<style>
@import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');

html, body, [class*="css"] {
    font-family: 'Vazirmatn', sans-serif !important;
}

.main {
    direction: rtl;
    text-align: right;
}

.block-container {
    padding-top: 1.5rem;
    max-width: 1400px;
}

/* اصلاح استایل تب‌ها (Tabs) */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background-color: #1e2130;
    padding: 8px;
    border-radius: 12px;
    border: 1px solid #2e344d;
    overflow-x: auto;
    white-space: nowrap;
}

.stTabs [data-baseweb="tab"] {
    height: 45px;
    background-color: #262c40;
    border-radius: 8px;
    color: #e0e6ed !important;
    font-weight: 600;
    font-size: 14px;
    padding: 0px 16px;
    border: 1px solid transparent;
    transition: all 0.2s ease-in-out;
}

.stTabs [data-baseweb="tab"]:hover {
    background-color: #323a54;
    color: #ffffff !important;
    border-color: #4a5578;
}

.stTabs [aria-selected="true"] {
    background-color: #4f46e5 !important;
    color: #ffffff !important;
    border-color: #6366f1 !important;
    box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
}

/* کارت‌های داشبورد */
[data-testid="stMetric"] {
    background: #1e2130;
    border: 1px solid #2e344d;
    border-radius: 14px;
    padding: 15px;
    box-shadow: 0 4px 10px rgba(0,0,0,0.15);
}

.stButton > button {
    border-radius: 8px;
    font-weight: 600;
    background-color: #4f46e5;
    color: white;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# TRANSLATION
# ============================================================

TEXT = {
    "dari": {
        "title": "MyGrowth Pro Max",
        "login": "ورود",
        "register": "ثبت‌نام",
        "username": "نام کاربری",
        "email": "ایمیل",
        "password": "رمز عبور",
        "login_btn": "ورود به حساب",
        "register_btn": "ساخت حساب",
        "logout": "خروج",
        "dashboard": "🏠 داشبورد",
        "today": "📅 ثبت امروز",
        "habits": "🔁 مدیریت عادت‌ها",
        "tasks": "📝 لیست کارها",
        "goals": "🎯 اهداف",
        "growth": "📈 روند رشد",
        "badges": "🏆 دستاوردها",
        "insights": "🧠 تحلیل هوشمند",
        "journal": "🙂 ژورنال روزانه",
        "sleep": "😴 پایش خواب",
        "settings": "⚙️ تنظیمات",
        "save": "💾 ذخیره اطلاعات",
        "add": "افزودن",
        "weight": "وزن (%)",
        "priority": "اولویت",
        "deadline": "مهلت انجام",
        "records": "روزهای ثبت‌شده",
        "streak": "تداوم فعلی",
        "xp": "امتیاز XP",
        "new_habit": "عادت جدید",
        "habit_name": "نام عادت",
        "new_task": "کار جدید",
        "goal_title": "عنوان هدف",
        "mood": "حالت روحی امروز",
        "sleep_hours": "ساعات خواب",
        "success": "با موفقیت انجام شد.",
    }
}

def tr(key):
    return TEXT["dari"].get(key, key)

# ============================================================
# DATABASE & INIT
# ============================================================

def db():
    con = sqlite3.connect(DB_FILE)
    con.row_factory = sqlite3.Row
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
            UNIQUE(user_id, name)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            record_date TEXT NOT NULL,
            percent REAL NOT NULL,
            details TEXT NOT NULL,
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
            created_at TEXT NOT NULL
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
            created_at TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS journal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            journal_date TEXT NOT NULL,
            mood INTEGER DEFAULT 3,
            note TEXT DEFAULT '',
            UNIQUE(user_id, journal_date)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sleep (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            sleep_date TEXT NOT NULL,
            hours REAL DEFAULT 0,
            quality INTEGER DEFAULT 3,
            UNIQUE(user_id, sleep_date)
        )
    """)
    con.commit()
    con.close()

init_db()

# ============================================================
# HELPER FUNCTIONS
# ============================================================

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

def create_user(username, email, password):
    con = db()
    try:
        cur = con.cursor()
        cur.execute("""
            INSERT INTO users (username,email,password_hash,language,created_at)
            VALUES(?,?,?,'dari',?)
        """, (username.strip(), email.strip().lower(), hash_password(password), datetime.now().isoformat()))
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

def get_tasks(uid):
    con = db()
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

# ============================================================
# APP INTERFACE
# ============================================================

if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    st.title("🚀 MyGrowth Pro Max")
    tab_login, tab_reg = st.tabs([tr("login"), tr("register")])
    with tab_login:
        u = st.text_input(tr("username"), key="l_u")
        p = st.text_input(tr("password"), type="password", key="l_p")
        if st.button(tr("login_btn")):
            usr = authenticate(u, p)
            if usr:
                st.session_state.user = usr
                st.rerun()
            else:
                st.error("نام کاربری یا رمز عبور اشتباه است.")
    with tab_reg:
        ru = st.text_input(tr("username"), key="r_u")
        re = st.text_input(tr("email"), key="r_e")
        rp = st.text_input(tr("password"), type="password", key="r_p")
        if st.button(tr("register_btn")):
            if create_user(ru, re, rp):
                st.success("حساب ساخته شد. اکنون وارد شوید.")
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
    
    tabs = st.tabs(menu)

    # 1. Dashboard
    with tabs[0]:
        st.header(tr("dashboard"))
        records = get_records(uid)
        col1, col2, col3 = st.columns(3)
        col1.metric(tr("records"), len(records))
        col2.metric(tr("streak"), "🔥 3 روز")
        col3.metric(tr("xp"), "⭐ 150 XP")

    # 2. Today
    with tabs[1]:
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
    with tabs[2]:
        st.header(tr("habits"))
        habits = get_habits(uid)
        if habits:
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
    with tabs[3]:
        st.header(tr("tasks"))
        t_title = st.text_input(tr("new_task"))
        t_prio = st.selectbox(tr("priority"), ["مهم و فوری", "مهم", "عادی"])
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
    with tabs[4]:
        st.header(tr("goals"))
        g_title = st.text_input(tr("goal_title"))
        g_dl = st.date_input(tr("deadline"), date.today() + timedelta(days=30))
        if st.button(tr("add") + " هدف"):
            add_goal(uid, g_title, "", str(date.today()), str(g_dl), "normal")
            st.rerun()
            
        goals = get_goals(uid)
        if goals:
            st.dataframe(pd.DataFrame(goals)[['id', 'title', 'deadline', 'progress', 'done']], use_container_width=True)

    # 6. Growth
    with tabs[5]:
        st.header(tr("growth"))
        records = get_records(uid)
        if records:
            df = pd.DataFrame([{"date": k, "percent": v["percent"]} for k, v in records.items()])
            st.line_chart(df.set_index("date"))
        else:
            st.info("داده‌ای ثبت نشده است.")

    # 7. Badges
    with tabs[6]:
        st.header(tr("badges"))
        st.success("🥇 اولین قدم: ثبت موفق اولین روز")

    # 8. Insights
    with tabs[7]:
        st.header(tr("insights"))
        st.info("روند فعالیت‌های شما بسیار امیدوارکننده است!")

    # 9. Journal
    with tabs[8]:
        st.header(tr("journal"))
        st.write("ثبت احساسات و یادداشت‌های روزانه")

    # 10. Sleep
    with tabs[9]:
        st.header(tr("sleep"))
        st.write("پایش ساعات خواب و استراحت")

    # 11. Settings
    with tabs[10]:
        st.header(tr("settings"))
        st.write(f"نام کاربری: {user['username']}")
    
