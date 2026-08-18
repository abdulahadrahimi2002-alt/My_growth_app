import streamlit as st
import sqlite3
import hashlib
import secrets
import json
import io
from datetime import datetime, date, timedelta

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# ============================================================
# CONFIG & CSS
# ============================================================

st.set_page_config(
    page_title="MyGrowth Pro Max",
    page_icon="💗",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_FILE = "mygrowth.db"

st.markdown(
    """
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
        padding-bottom: 3rem;
    }

    .stButton > button {
        width: 100%;
        border-radius: 10px;
        font-weight: 600;
        background-color: #4f46e5;
        color: white;
    }

    div[data-testid="stMetric"] {
        background: rgba(128,128,128,.08);
        border-radius: 14px;
        padding: 12px;
        border: 1px solid rgba(255,255,255,0.1);
    }

    .hero {
        padding: 25px;
        border-radius: 20px;
        background: linear-gradient(
            135deg,
            rgba(255,75,120,.15),
            rgba(80,120,255,.12)
        );
        margin-bottom: 20px;
    }

    .badge {
        padding: 14px;
        border-radius: 14px;
        background: rgba(255,193,7,.10);
        border: 1px solid rgba(255,193,7,.25);
        margin-bottom: 10px;
    }

    [data-testid="stSidebar"] {
        direction: rtl;
        background-color: #111827;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# TRANSLATIONS
# ============================================================

TEXT = {
    "dari": {
        "title": "MyGrowth Pro Max",
        "subtitle": "سیستم کامل مدیریت رشد، عادت‌ها، اهداف و زندگی شخصی",
        "login": "ورود",
        "register": "ثبت‌نام",
        "username": "نام کاربری",
        "email": "ایمیل",
        "password": "رمز عبور",
        "login_btn": "ورود به حساب",
        "register_btn": "ساخت حساب",
        "logout": "خروج از حساب",
        "dashboard": "🏠 داشبورد",
        "today": "📅 امروز",
        "habits": "🔁 عادت‌ها",
        "tasks": "📝 کارها",
        "goals": "🎯 اهداف",
        "growth": "📈 رشد من",
        "badges": "🏆 دستاوردها",
        "insights": "🧠 تحلیل هوشمند",
        "journal": "🙂 ژورنال و حال",
        "sleep": "😴 خواب",
        "settings": "⚙️ تنظیمات",
        "save": "💾 ذخیره",
        "add": "➕ افزودن",
        "performance": "عملکرد",
        "streak": "🔥 تداوم",
        "xp": "⭐ امتیاز XP",
        "days": "روز",
        "average": "میانگین",
        "no_data": "هنوز اطلاعاتی ثبت نشده است.",
        "wrong_login": "نام کاربری یا رمز عبور نادرست است.",
        "exists": "نام کاربری یا ایمیل قبلاً ثبت شده است.",
        "success": "با موفقیت ذخیره شد.",
    }
}

def tr(key):
    return TEXT["dari"].get(key, key)

# ============================================================
# DATABASE & SECURITY
# ============================================================

def db():
    con = sqlite3.connect(DB_FILE)
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
            category TEXT DEFAULT 'عمومی',
            weight REAL DEFAULT 10,
            active INTEGER DEFAULT 1,
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
            category TEXT DEFAULT 'عمومی',
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS journal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            note_date TEXT NOT NULL,
            mood TEXT,
            wins TEXT,
            lesson TEXT,
            tomorrow TEXT,
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
            bedtime TEXT,
            wake_time TEXT,
            note TEXT DEFAULT '',
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(user_id, sleep_date)
        )
    """)
    con.commit()
    con.close()

init_db()

def hash_password(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 210_000)
    return salt.hex() + ":" + digest.hex()

def verify_password(password, stored):
    try:
        salt_hex, digest_hex = stored.split(":")
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), 210_000)
        return secrets.compare_digest(digest.hex(), digest_hex)
    except Exception:
        return False

def authenticate(username, password):
    con = db()
    row = con.execute("SELECT id, username, email, password_hash, language FROM users WHERE username=?", (username.strip(),)).fetchone()
    con.close()
    if row and verify_password(password, row[3]):
        return row
    return None

def create_user(username, email, password, language="dari"):
    con = db()
    try:
        cur = con.cursor()
        cur.execute("INSERT INTO users (username,email,password_hash,language,created_at) VALUES(?,?,?,?,?)",
                    (username.strip(), email.strip(), hash_password(password), language, datetime.now().isoformat()))
        user_id = cur.lastrowid
        default_habits = [
            ("مطالعه", "یادگیری", 30),
            ("ورزش", "سلامت", 30),
            ("مطالعه چینی", "یادگیری", 20),
            ("کدنویسی پایتون", "مهارت", 20),
        ]
        for name, category, weight in default_habits:
            cur.execute("INSERT INTO habits (user_id,name,category,weight) VALUES(?,?,?,?)", (user_id, name, category, weight))
        con.commit()
        return True
    except sqlite3.IntegrityError:
        con.rollback()
        return False
    finally:
        con.close()

# ============================================================
# CRUD FUNCTIONS
# ============================================================

def get_habits(user_id):
    con = db()
    rows = con.execute("SELECT id,name,category,weight,active FROM habits WHERE user_id=? ORDER BY id", (user_id,)).fetchall()
    con.close()
    return rows

def add_habit(user_id, name, category, weight):
    con = db()
    try:
        con.execute("INSERT INTO habits (user_id,name,category,weight) VALUES(?,?,?,?)", (user_id, name.strip(), category.strip(), weight))
        con.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        con.close()

def delete_habit(user_id, habit_id):
    con = db()
    con.execute("DELETE FROM habits WHERE id=? AND user_id=?", (habit_id, user_id))
    con.commit()
    con.close()

def get_records(user_id):
    con = db()
    rows = con.execute("SELECT record_date,percent,details FROM records WHERE user_id=? ORDER BY record_date DESC", (user_id,)).fetchall()
    con.close()
    result = {}
    for d, percent, details in rows:
        try: details = json.loads(details or "{}")
        except Exception: details = {}
        result[d] = {"percent": percent, "details": details}
    return result

def save_record(user_id, record_date, percent, details):
    con = db()
    con.execute("""
        INSERT INTO records (user_id,record_date,percent,details) VALUES(?,?,?,?)
        ON CONFLICT(user_id,record_date) DO UPDATE SET percent=excluded.percent, details=excluded.details
    """, (user_id, record_date, percent, json.dumps(details, ensure_ascii=False)))
    con.commit()
    con.close()

def get_tasks(user_id):
    con = db()
    rows = con.execute("SELECT id,title,priority,done,task_date FROM tasks WHERE user_id=? ORDER BY task_date DESC, id", (user_id,)).fetchall()
    con.close()
    return [{"id": r[0], "title": r[1], "priority": r[2], "done": bool(r[3]), "date": r[4]} for r in rows]

def add_task(user_id, task_date, title, priority):
    con = db()
    con.execute("INSERT INTO tasks (user_id,task_date,title,priority,done) VALUES(?,?,?,?,0)", (user_id, task_date, title, priority))
    con.commit()
    con.close()

def update_task(user_id, task_id, done):
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
    rows = con.execute("SELECT id,title,description,deadline,progress,category FROM goals WHERE user_id=? ORDER BY deadline", (user_id,)).fetchall()
    con.close()
    return [{"id": r[0], "title": r[1], "description": r[2], "deadline": r[3], "progress": r[4], "category": r[5]} for r in rows]

def add_goal(user_id, title, description, deadline, progress, category):
    con = db()
    con.execute("INSERT INTO goals (user_id,title,description,deadline,progress,category,created_at) VALUES(?,?,?,?,?,?,?)",
                (user_id, title, description, deadline, progress, category, datetime.now().isoformat()))
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

def save_journal(user_id, note_date, mood, note):
    con = db()
    con.execute("""
        INSERT INTO journal (user_id,note_date,mood,note) VALUES(?,?,?,?)
        ON CONFLICT(user_id,note_date) DO UPDATE SET mood=excluded.mood, note=excluded.note
    """, (user_id, note_date, mood, note))
    con.commit()
    con.close()

def save_sleep(user_id, sleep_date, hours, quality):
    con = db()
    con.execute("""
        INSERT INTO sleep (user_id,sleep_date,hours,quality) VALUES(?,?,?,?)
        ON CONFLICT(user_id,sleep_date) DO UPDATE SET hours=excluded.hours, quality=excluded.quality
    """, (user_id, sleep_date, hours, quality))
    con.commit()
    con.close()

# ============================================================
# STATS CALCULATIONS
# ============================================================

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

def get_status_label(score):
    if score < 50: return "ضعیف 🔴", "error"
    elif score < 70: return "متوسط 🟡", "warning"
    elif score < 90: return "خوب 🟢", "info"
    else: return "عالی 🌟", "success"

# ============================================================
# INTERFACE
# ============================================================

if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    st.title("🚀 MyGrowth Pro Max")
    st.caption("سیستم پیشرفته مدیریت رشد شخصی و عادت‌ها")
    tab_login, tab_reg = st.tabs(["ورود", "ثبت‌نام"])
    with tab_login:
        u = st.text_input("نام کاربری", key="l_u")
        p = st.text_input("رمز عبور", type="password", key="l_p")
        if st.button("ورود به حساب"):
            usr = authenticate(u, p)
            if usr:
                st.session_state.user = usr
                st.rerun()
            else:
                st.error(tr("wrong_login"))
    with tab_reg:
        ru = st.text_input("نام کاربری جدید", key="r_u")
        re = st.text_input("ایمیل", key="r_e")
        rp = st.text_input("رمز عبور", type="password", key="r_p")
        if st.button("ساخت حساب"):
            if create_user(ru, re, rp):
                st.success("حساب با موفقیت ساخته شد. اکنون وارد شوید.")
            else:
                st.error(tr("exists"))
else:
    user = st.session_state.user
    uid = user[0]
    
    st.sidebar.markdown(f"### 👤 {user[1]}")
    menu = [
        "🏠 داشبورد",
        "📅 ثبت امروز",
        "🔁 مدیریت عادت‌ها",
        "📝 لیست کارها",
        "🎯 اهداف",
        "📈 روند رشد",
        "🏆 دستاوردها",
        "🧠 تحلیل هوشمند",
        "🙂 ژورنال روزانه",
        "😴 پایش خواب",
        "⚙️ تنظیمات"
    ]
    page = st.sidebar.radio("منو", menu, label_visibility="collapsed")
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 خروج"):
        st.session_state.user = None
        st.rerun()

    # 1. Dashboard
    if page == "🏠 داشبورد":
        st.header("🏠 داشبورد رشد شخصی")
        records = get_records(uid)
        streak = calculate_streak(records)
        col1, col2, col3 = st.columns(3)
        col1.metric("کل روزهای ثبت‌شده", f"{len(records)} روز")
        col2.metric("تداوم فعلی (Streak)", f"🔥 {streak} روز")
        col3.metric("امتیاز کل XP", f"⭐ {len(records) * 50} XP")

    # 2. Today
    elif page == "📅 ثبت امروز":
        st.header("📅 ثبت عملکرد روزانه")
        sel_date = st.date_input("تاریخ ثبت", date.today())
        d_str = str(sel_date)
        habits = get_habits(uid)
        tot_weight = sum([h[3] for h in habits]) or 1
        
        details = {}
        total_score = 0
        st.subheader("فعالیت‌ها:")
        for h in habits:
            val = st.slider(f"{h[1]} (وزن: {h[3]}%)", 0, 100, 0, key=f"h_{h[0]}")
            details[h[1]] = val
            total_score += (val * h[3]) / tot_weight

        avg_score = round(total_score, 1)
        status_lbl, _ = get_status_label(avg_score)
        
        st.markdown("---")
        c1, c2 = st.columns(2)
        c1.metric("میزان/میانگین عملکرد روزانه", f"{avg_score}%")
        c2.metric("ارزیابی وضعیت", status_lbl)
        
        if st.button("💾 ذخیره عملکرد امروز"):
            save_record(uid, d_str, avg_score, details)
            st.success(f"اطلاعات تاریخ {d_str} با موفقیت ثبت شد.")

    # 3. Habits
    elif page == "🔁 مدیریت عادت‌ها":
        st.header("🔁 عادت‌های من")
        habits = get_habits(uid)
        if habits:
            df_h = pd.DataFrame(habits, columns=['کد', 'نام عادت', 'دسته‌بندی', 'وزن (%)', 'فعال'])
            st.dataframe(df_h[['نام عادت', 'دسته‌بندی', 'وزن (%)']], use_container_width=True)
            
            st.subheader("🗑️ حذف عادت")
            h_del = st.selectbox("انتخاب عادت برای حذف", options=[h[1] for h in habits])
            if st.button("حذف عادت"):
                h_id = [h[0] for h in habits if h[1] == h_del][0]
                delete_habit(uid, h_id)
                st.rerun()

        st.markdown("---")
        st.subheader("➕ افزودن عادت جدید")
        h_name = st.text_input("نام عادت")
        h_cat = st.selectbox("دسته‌بندی", ["سلامت", "یادگیری", "مهارت", "روحی", "عمومی"])
        h_weight = st.number_input("وزن (%)", 1, 100, 20)
        if st.button("افزودن عادت"):
            if add_habit(uid, h_name, h_cat, h_weight):
                st.success("عادت جدید اضافه شد.")
                st.rerun()

    # 4. Tasks
    elif page == "📝 لیست کارها":
        st.header("📝 لیست کارها (To-Do)")
        t_title = st.text_input("عنوان کار جدید")
        t_prio = st.selectbox("اولویت", ["فوری و مهم", "مهم", "عادی"])
        if st.button("افزودن کار"):
            add_task(uid, str(date.today()), t_title, t_prio)
            st.rerun()
            
        st.markdown("---")
        tasks = get_tasks(uid)
        for t in tasks:
            c1, c2 = st.columns([0.85, 0.15])
            chk = c1.checkbox(f"{t['title']} ({t['priority']}) - {t['date']}", value=t['done'], key=f"t_{t['id']}")
            if chk != t['done']:
                update_task(uid, t['id'], chk)
                st.rerun()
            if c2.button("حذف", key=f"del_t_{t['id']}"):
                delete_task(uid, t['id'])
                st.rerun()

    # 5. Goals
    elif page == "🎯 اهداف":
        st.header("🎯 اهداف شخصی")
        g_title = st.text_input("عنوان هدف")
        g_desc = st.text_area("توضیحات")
        g_dl = st.date_input("مهلت (Deadline)", date.today() + timedelta(days=30))
        if st.button("ثبت هدف"):
            add_goal(uid, g_title, g_desc, str(g_dl), 0, "عمومی")
            st.rerun()

        st.markdown("---")
        goals = get_goals(uid)
        for g in goals:
            st.subheader(f"📌 {g['title']}")
            st.write(f"مهلت: {g['deadline']} | توضیحات: {g['description']}")
            prog = st.slider("میزان پیشرفت (%)", 0, 100, g['progress'], key=f"g_{g['id']}")
            if prog != g['progress']:
                update_goal(uid, g['id'], prog)
            if st.button("حذف هدف", key=f"del_g_{g['id']}"):
                delete_goal(uid, g['id'])
                st.rerun()

    # 6. Growth
    elif page == "📈 روند رشد":
        st.header("📈 روند رشد و تاریخچه")
        records = get_records(uid)
        if records:
            data = []
            for d, v in records.items():
                lbl, _ = get_status_label(v['percent'])
                row = {"تاریخ": d, "میانگین (%)": v['percent'], "وضعیت": lbl}
                data.append(row)
            df = pd.DataFrame(data).sort_values("تاریخ")
            
            st.dataframe(df, use_container_width=True)
            
            fig = px.line(df, x="تاریخ", y="میانگین (%)", markers=True, title="نمودار روند عملکرد")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(tr("no_data"))

    # 7. Badges
    elif page == "🏆 دستاوردها":
        st.header("🏆 دستاوردها و نشان‌ها")
        records = get_records(uid)
        cnt = len(records)
        if cnt >= 1: st.success("🥇 اولین قدم: ثبت اولین روز عملکرد")
        if cnt >= 7: st.success("🔥 تداوم یک هفته‌ای: ثبت ۷ روز موفق")
        if cnt >= 30: st.success("⭐ قهرمان انضباط: ثبت ۳۰ روز عملکرد")
        if any(r['percent'] >= 90 for r in records.values()): st.success("🌟 عملکرد الماس: کسب درصد بالای ۹۰٪ در یک روز")

    # 8. Insights
    elif page == "🧠 تحلیل هوشمند":
        st.header("🧠 تحلیل هوشمند عملکرد")
        records = get_records(uid)
        if records:
            scores = [v['percent'] for v in records.values()]
            avg = sum(scores) / len(scores)
            st.write(f"**میانگین کل عملکرد شما:** {round(avg, 1)}%")
            if avg >= 80: st.success("عالی! روند فعلی خود را با همین کیفیت ادامه دهید.")
            elif avg >= 50: st.warning("متوسط. برای رسیدن به اهداف نیاز به تمرکز بر عادت‌های اصلی دارید.")
            else: st.error("نیاز به بهبود. عادت‌های کوچک‌تر انتخاب کنید تا تداوم حفظ شود.")
        else: st.info(tr("no_data"))

    # 9. Journal
    elif page == "🙂 ژورنال روزانه":
        st.header("🙂 ژورنال و حال روز")
        j_date = st.date_input("تاریخ", date.today())
        j_mood = st.selectbox("حالت روحی", ["عالی 😃", "خوب 🙂", "معمولی 😐", "خسته 😫", "بد ☹️"])
        j_note = st.text_area("یادداشت روزانه / یادگیری‌ها")
        if st.button("ثبت ژورنال"):
            save_journal(uid, str(j_date), j_mood, j_note)
            st.success("ژورنال ثبت شد.")

    # 10. Sleep
    elif page == "😴 پایش خواب":
        st.header("😴 پایش میزان خواب")
        s_date = st.date_input("تاریخ", date.today())
        s_hrs = st.number_input("ساعات خواب", 0.0, 24.0, 7.5, step=0.5)
        s_qual = st.slider("کیفیت خواب (1 تا 5)", 1, 5, 3)
        if st.button("ثبت خواب"):
            save_sleep(uid, str(s_date), s_hrs, s_qual)
            st.success("اطلاعات خواب ثبت شد.")

    # 11. Settings & CSV Export
    elif page == "⚙️ تنظیمات":
        st.header("⚙️ تنظیمات و خروجی داده‌ها")
        st.write(f"**نام کاربری:** {user[1]}")
        st.write(f"**ایمیل:** {user[2]}")
        
        st.markdown("---")
        st.subheader("📥 خروجی گرفتن از داده‌ها (CSV)")
        records = get_records(uid)
        if records:
            df_exp = pd.DataFrame([{"Date": k, "Percent": v["percent"]} for k, v in records.items()])
            csv = df_exp.to_csv(index=False).encode('utf-8')
            st.download_button("دانلود خروجی CSV عملکرد", csv, "mygrowth_data.csv", "text/csv")
