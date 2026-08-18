import streamlit as st
import sqlite3
import hashlib
import secrets
import json
from datetime import datetime, date, timedelta
import pandas as pd
import plotly.graph_objects as go

# ============================================================
# MyGrowth — Multi-user Planner
# Login/Register + SQLite database + Dari/English
# ============================================================

st.set_page_config(
    page_title="MyGrowth",
    page_icon="💗",
    layout="wide",
    initial_sidebar_state="collapsed",
)

DB_FILE = "mygrowth.db"

DEFAULT_ACTIVITIES = [
    "نماز پنج‌گانه",
    "تلاوت قرآن",
    "ورزش روزانه",
    "مطالعه انگلیسی",
    "مطالعه چینی",
    "کارهای شخصی",
]

TEXT = {
    "dari": {
        "name": "دری",
        "title": "MyGrowth",
        "subtitle": "پلنر شخصی برای برنامه‌ریزی، عادت‌ها و دیدن رشد واقعی زندگی",
        "login": "ورود",
        "register": "ثبت‌نام",
        "logout": "خروج",
        "username": "نام کاربری",
        "email": "ایمیل",
        "password": "رمز عبور",
        "confirm_password": "تکرار رمز عبور",
        "login_btn": "ورود به حساب",
        "register_btn": "ساخت حساب",
        "dashboard": "🏠 داشبورد",
        "today": "📅 برنامه امروز",
        "habits": "🔁 عادت‌ها",
        "goals": "🎯 اهداف",
        "growth": "📊 رشد من",
        "notes": "📝 یادداشت روزانه",
        "settings": "⚙️ تنظیمات",
        "today_performance": "💗 عملکرد امروز",
        "growth_vs_previous": "📈 تغییر نسبت به قبل",
        "weekly_average": "📊 میانگین ۷ روز",
        "streak": "🔥 زنجیره",
        "best": "🏆 بهترین عملکرد",
        "tasks_today": "📝 کارهای امروز",
        "add_task": "افزودن کار",
        "new_task": "کار جدید",
        "priority": "اولویت",
        "high": "بالا 🔴",
        "medium": "متوسط 🟡",
        "normal": "عادی 🔵",
        "save": "💾 ذخیره",
        "add_activity": "افزودن فعالیت",
        "new_activity": "فعالیت جدید",
        "performance": "عملکرد",
        "goals_title": "هدف جدید",
        "deadline": "مهلت هدف",
        "progress": "درصد پیشرفت",
        "add_goal": "🎯 افزودن هدف",
        "delete": "🗑️ حذف",
        "language": "🌐 زبان",
        "dari": "🇦🇫 دری",
        "english": "🇬🇧 English",
        "welcome": "به MyGrowth خوش آمدید",
        "wrong_login": "نام کاربری یا رمز عبور نادرست است.",
        "user_exists": "این نام کاربری یا ایمیل قبلاً ثبت شده است.",
        "password_short": "رمز عبور باید حداقل ۶ حرف باشد.",
        "password_mismatch": "رمزهای عبور یکسان نیستند.",
        "register_success": "حساب شما ساخته شد. حالا وارد شوید.",
        "empty": "هنوز اطلاعاتی ثبت نشده است.",
        "note_wins": "🌱 امروز چه چیزی خوب پیش رفت؟",
        "note_lesson": "🧠 امروز چه چیزی یاد گرفتم؟",
        "note_tomorrow": "🌅 فردا مهم‌ترین کار من چیست؟",
        "mood": "🙂 حال امروز",
        "save_note": "💾 ذخیره یادداشت",
        "backup": "⬇️ دریافت نسخه پشتیبان",
        "backup_info": "اطلاعات شما در دیتابیس محلی برنامه ذخیره می‌شود.",
    },
    "en": {
        "name": "English",
        "title": "MyGrowth",
        "subtitle": "Your personal planner for planning, habits and real growth",
        "login": "Login",
        "register": "Register",
        "logout": "Logout",
        "username": "Username",
        "email": "Email",
        "password": "Password",
        "confirm_password": "Confirm password",
        "login_btn": "Log in",
        "register_btn": "Create account",
        "dashboard": "🏠 Dashboard",
        "today": "📅 Today",
        "habits": "🔁 Habits",
        "goals": "🎯 Goals",
        "growth": "📊 My Growth",
        "notes": "📝 Daily Note",
        "settings": "⚙️ Settings",
        "today_performance": "💗 Latest Performance",
        "growth_vs_previous": "📈 Change",
        "weekly_average": "📊 7-Day Average",
        "streak": "🔥 Streak",
        "best": "🏆 Best",
        "tasks_today": "📝 Today's Tasks",
        "add_task": "Add task",
        "new_task": "New task",
        "priority": "Priority",
        "high": "High 🔴",
        "medium": "Medium 🟡",
        "normal": "Normal 🔵",
        "save": "💾 Save",
        "add_activity": "Add activity",
        "new_activity": "New activity",
        "performance": "Performance",
        "goals_title": "New goal",
        "deadline": "Deadline",
        "progress": "Progress",
        "add_goal": "🎯 Add goal",
        "delete": "🗑️ Delete",
        "language": "🌐 Language",
        "dari": "🇦🇫 Dari",
        "english": "🇬🇧 English",
        "welcome": "Welcome to MyGrowth",
        "wrong_login": "Incorrect username or password.",
        "user_exists": "Username or email already exists.",
        "password_short": "Password must be at least 6 characters.",
        "password_mismatch": "Passwords do not match.",
        "register_success": "Your account was created. You can now log in.",
        "empty": "No information yet.",
        "note_wins": "🌱 What went well today?",
        "note_lesson": "🧠 What did I learn today?",
        "note_tomorrow": "🌅 What is my most important task tomorrow?",
        "mood": "🙂 Today's mood",
        "save_note": "💾 Save note",
        "backup": "⬇️ Download backup",
        "backup_info": "Your information is stored in the app's database.",
    },
}

def tr(key):
    lang = st.session_state.get("lang", "dari")
    if lang not in TEXT:
        lang = "dari"
    return TEXT[lang].get(key, key)

def db():
    return sqlite3.connect(DB_FILE)

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
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            UNIQUE(user_id, name)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS daily_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            record_date TEXT NOT NULL,
            percent REAL NOT NULL,
            activities_json TEXT NOT NULL,
            UNIQUE(user_id, record_date)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            task_date TEXT NOT NULL,
            title TEXT NOT NULL,
            priority TEXT NOT NULL,
            done INTEGER DEFAULT 0
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            deadline TEXT,
            progress INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            note_date TEXT NOT NULL,
            wins TEXT,
            lesson TEXT,
            tomorrow TEXT,
            mood TEXT,
            UNIQUE(user_id, note_date)
        )
    """)
    con.commit()
    con.close()

def hash_password(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 120000)
    return salt.hex() + ":" + digest.hex()

def verify_password(password, stored):
    try:
        salt_hex, digest_hex = stored.split(":")
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt_hex), 120000
        )
        return secrets.compare_digest(digest.hex(), digest_hex)
    except Exception:
        return False

def get_user(username):
    con = db()
    row = con.execute(
        "SELECT id, username, email, language FROM users WHERE username=?",
        (username.strip(),)
    ).fetchone()
    con.close()
    return row

def authenticate(username, password):
    con = db()
    row = con.execute(
        "SELECT id, username, email, password_hash, language FROM users WHERE username=?",
        (username.strip(),)
    ).fetchone()
    con.close()
    if row and verify_password(password, row[3]):
        return row
    return None

def create_user(username, email, password, language):
    con = db()
    try:
        con.execute(
            "INSERT INTO users(username,email,password_hash,language,created_at) VALUES(?,?,?,?,?)",
            (username.strip(), email.strip(), hash_password(password), language, datetime.now().isoformat())
        )
        user_id = con.execute("SELECT last_insert_rowid()").fetchone()[0]
        for name in DEFAULT_ACTIVITIES:
            con.execute("INSERT OR IGNORE INTO activities(user_id,name) VALUES(?,?)", (user_id, name))
        con.commit()
        return True
    except sqlite3.IntegrityError:
        con.rollback()
        return False
    finally:
        con.close()

def set_language(user_id, language):
    con = db()
    con.execute("UPDATE users SET language=? WHERE id=?", (language, user_id))
    con.commit()
    con.close()

def get_activities(user_id):
    con = db()
    rows = con.execute(
        "SELECT id,name FROM activities WHERE user_id=? ORDER BY id",
        (user_id,)
    ).fetchall()
    con.close()
    return rows

def add_activity(user_id, name):
    con = db()
    try:
        con.execute("INSERT INTO activities(user_id,name) VALUES(?,?)", (user_id, name.strip()))
        con.commit()
        ok = True
    except sqlite3.IntegrityError:
        ok = False
    finally:
        con.close()
    return ok

def delete_activity(user_id, activity_id):
    con = db()
    con.execute("DELETE FROM activities WHERE id=? AND user_id=?", (activity_id, user_id))
    con.commit()
    con.close()

def get_record(user_id, record_date):
    con = db()
    row = con.execute(
        "SELECT percent, activities_json FROM daily_records WHERE user_id=? AND record_date=?",
        (user_id, record_date)
    ).fetchone()
    con.close()
    if not row:
        return None
    try:
        acts = json.loads(row[1])
    except Exception:
        acts = {}
    return {"percent": row[0], "activities": acts}

def save_record(user_id, record_date, percent, activities_data):
    con = db()
    con.execute("""
        INSERT INTO daily_records(user_id,record_date,percent,activities_json)
        VALUES(?,?,?,?)
        ON CONFLICT(user_id,record_date) DO UPDATE SET
        percent=excluded.percent,
        activities_json=excluded.activities_json
    """, (user_id, record_date, percent, json.dumps(activities_data, ensure_ascii=False)))
    con.commit()
    con.close()

def get_records(user_id):
    con = db()
    rows = con.execute(
        "SELECT record_date,percent,activities_json FROM daily_records WHERE user_id=? ORDER BY record_date",
        (user_id,)
    ).fetchall()
    con.close()
    result = {}
    for d, pct, raw in rows:
        try:
            acts = json.loads(raw)
        except Exception:
            acts = {}
        result[d] = {"percent": pct, "activities": acts}
    return result

def get_tasks(user_id, task_date):
    con = db()
    rows = con.execute(
        "SELECT id,title,priority,done FROM tasks WHERE user_id=? AND task_date=? ORDER BY id",
        (user_id, task_date)
    ).fetchall()
    con.close()
    return [{"id": r[0], "title": r[1], "priority": r[2], "done": bool(r[3])} for r in rows]

def add_task(user_id, task_date, title, priority):
    con = db()
    con.execute(
        "INSERT INTO tasks(user_id,task_date,title,priority,done) VALUES(?,?,?,?,0)",
        (user_id, task_date, title, priority)
    )
    con.commit()
    con.close()

def toggle_task(user_id, task_id, done):
    con = db()
    con.execute("UPDATE tasks SET done=? WHERE id=? AND user_id=?", (int(done), task_id, user_id))
    con.commit()
    con.close()

def delete_task(user_id, task_id):
    con = db()
    con.execute("DELETE FROM tasks WHERE id=? AND user_id=?", (task_id, user_id))
    con.commit()
    con.close()

def get_goals(user_id):
    con = db()
    rows = con.execute(
        "SELECT id,title,deadline,progress FROM goals WHERE user_id=? ORDER BY id DESC",
        (user_id,)
    ).fetchall()
    con.close()
    return [{"id":r[0],"title":r[1],"deadline":r[2],"progress":r[3]} for r in rows]

def add_goal(user_id, title, deadline, progress):
    con = db()
    con.execute(
        "INSERT INTO goals(user_id,title,deadline,progress,created_at) VALUES(?,?,?,?,?)",
        (user_id, title, deadline, progress, datetime.now().isoformat())
    )
    con.commit()
    con.close()

def update_goal(user_id, goal_id, progress):
    con = db()
    con.execute("UPDATE goals SET progress=? WHERE id=? AND user_id=?", (progress, goal_id, user_id))
    con.commit()
    con.close()

def delete_goal(user_id, goal_id):
    con = db()
    con.execute("DELETE FROM goals WHERE id=? AND user_id=?", (goal_id, user_id))
    con.commit()
    con.close()

def get_note(user_id, note_date):
    con = db()
    row = con.execute(
        "SELECT wins,lesson,tomorrow,mood FROM notes WHERE user_id=? AND note_date=?",
        (user_id, note_date)
    ).fetchone()
    con.close()
    if not row:
        return {}
    return {"wins":row[0] or "", "lesson":row[1] or "", "tomorrow":row[2] or "", "mood":row[3] or ""}

def save_note(user_id, note_date, wins, lesson, tomorrow, mood):
    con = db()
    con.execute("""
        INSERT INTO notes(user_id,note_date,wins,lesson,tomorrow,mood)
        VALUES(?,?,?,?,?,?)
        ON CONFLICT(user_id,note_date) DO UPDATE SET
        wins=excluded.wins, lesson=excluded.lesson,
        tomorrow=excluded.tomorrow, mood=excluded.mood
    """, (user_id,note_date,wins,lesson,tomorrow,mood))
    con.commit()
    con.close()

def streak(keys):
    if not keys:
        return 0
    dates = [date.fromisoformat(k) for k in sorted(keys)]
    count = 1
    for i in range(len(dates)-1,0,-1):
        if (dates[i] - dates[i-1]).days == 1:
            count += 1
        else:
            break
    return count

def status(v):
    if v >= 85: return "🏆 عالی"
    if v >= 70: return "✨ خوب"
    if v >= 50: return "🟡 متوسط"
    if v >= 30: return "🟠 نیاز به تلاش"
    return "🔴 ضعیف"

init_db()

# ============================================================
# Session / Authentication
# ============================================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "lang" not in st.session_state:
    st.session_state.lang = "dari"

if not st.session_state.logged_in:
    st.markdown(
        """
        <div style="max-width:650px;margin:50px auto 10px;text-align:center;">
        <div style="font-size:48px;">💗</div>
        <h1>MyGrowth</h1>
        <p style="color:#9ea6b3;">Your planner. Your habits. Your growth.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    lang_choice = st.selectbox(
        "🌐 Language / زبان",
        ["دری", "English"],
        index=0 if st.session_state.lang == "dari" else 1,
    )
    st.session_state.lang = "dari" if lang_choice == "دری" else "en"

    login_tab, register_tab = st.tabs([tr("login"), tr("register")])

    with login_tab:
        st.subheader(tr("welcome"))
        username = st.text_input(tr("username"), key="login_username")
        password = st.text_input(tr("password"), type="password", key="login_password")
        if st.button(tr("login_btn"), type="primary", use_container_width=True):
            user = authenticate(username, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.user_id = user[0]
                st.session_state.lang = user[4] or "dari"
                st.rerun()
            else:
                st.error(tr("wrong_login"))

    with register_tab:
        st.subheader(tr("register"))
        username = st.text_input(tr("username"), key="reg_username")
        email = st.text_input(tr("email"), key="reg_email")
        password = st.text_input(tr("password"), type="password", key="reg_password")
        confirm = st.text_input(tr("confirm_password"), type="password", key="reg_confirm")

        if st.button(tr("register_btn"), use_container_width=True):
            if len(password) < 6:
                st.warning(tr("password_short"))
            elif password != confirm:
                st.warning(tr("password_mismatch"))
            elif not username.strip() or not email.strip():
                st.warning("لطفاً همه معلومات را وارد کنید." if st.session_state.lang == "dari" else "Please fill all fields.")
            elif create_user(username, email, password, st.session_state.lang):
                st.success(tr("register_success"))
            else:
                st.error(tr("user_exists"))

    st.stop()

# ============================================================
# Logged-in app
# ============================================================
user_id = st.session_state.user_id
activities = get_activities(user_id)
records = get_records(user_id)

# Top bar
top1, top2, top3 = st.columns([5,2,1])
with top1:
    st.markdown("## 💗 MyGrowth")
with top2:
    lang = st.selectbox(
        tr("language"),
        ["دری", "English"],
        index=0 if st.session_state.lang == "dari" else 1,
        key="top_language"
    )
    new_lang = "dari" if lang == "دری" else "en"
    if new_lang != st.session_state.lang:
        st.session_state.lang = new_lang
        set_language(user_id, new_lang)
        st.rerun()
with top3:
    if st.button(tr("logout"), use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.rerun()

st.caption(tr("subtitle"))

tabs = st.tabs([
    tr("dashboard"), tr("today"), tr("habits"),
    tr("goals"), tr("growth"), tr("notes"), tr("settings")
])

today = date.today()
today_key = today.isoformat()

# ---------------- Dashboard ----------------
with tabs[0]:
    keys = sorted(records)
    latest = records[keys[-1]]["percent"] if keys else 0
    previous = records[keys[-2]]["percent"] if len(keys) >= 2 else None
    change = round(latest - previous, 1) if previous is not None else None
    week_vals = [records[k]["percent"] for k in keys[-7:]]
    week_avg = round(sum(week_vals)/len(week_vals),1) if week_vals else 0
    best = max([r["percent"] for r in records.values()], default=0)

    c1,c2,c3,c4 = st.columns(4)
    with c1: st.metric(tr("today_performance"), f"{latest:g}%")
    with c2: st.metric(tr("growth_vs_previous"), "—" if change is None else f"{change:+g}%")
    # ---------------- Growth ----------------
with tabs[4]:
    st.subheader(tr("growth"))
    keys = sorted(records)
    if keys:
        period = st.selectbox("Range / بازه", ["7", "14", "30", "All"])
        n = len(keys) if period == "All" else int(period)
        ck = keys[-n:]
        vals = [records[k]["percent"] for k in ck]

        fig = go.Figure(go.Scatter(
            x=[k[5:] for k in ck],
            y=vals,
            mode="lines+markers+text",
            text=[f"{v:g}%" for v in vals],
            textposition="top center",
            line=dict(width=3),
            marker=dict(size=9)
        ))
        fig.add_hline(y=75, line_dash="dash", annotation_text="75%")
        fig.update_layout(
            yaxis=dict(range=[0, 105]),
            height=480,
            paper_bgcolor="#0b0e13",
            plot_bgcolor="#11151c",
            font=dict(color="white")
        )
        st.plotly_chart(fig, use_container_width=True)

        history = []
        for i, k in enumerate(keys):
            v = records[k]["percent"]
            diff = "—" if i == 0 else f"{v-records[keys[i-1]]['percent']:+g}%"
            history.append({
                "Date / تاریخ": k,
                "Performance / عملکرد": f"{v:g}%",
                "Change / تغییر": diff,
                "Status / وضعیت": status(v)
            })
        st.dataframe(pd.DataFrame(history), use_container_width=True, hide_index=True)
    else:
        st.info(tr("empty"))
        
