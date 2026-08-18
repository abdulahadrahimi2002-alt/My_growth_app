# ============================================================
# MyGrowth Pro Max - Fully Functional Version
# ============================================================

import streamlit as st
import sqlite3
import hashlib
import secrets
import json
from datetime import date, datetime, timedelta
import pandas as pd
import plotly.express as px

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
    max-width: 1300px;
}

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

[data-testid="stSidebar"] {
    direction: rtl;
    background-color: #111827;
}

div[role="radiogroup"] > label {
    background-color: #1f2937;
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 6px;
    border: 1px solid #374151;
    color: #f3f4f6 !important;
    transition: all 0.2s;
}

div[role="radiogroup"] > label:hover {
    background-color: #374151;
    border-color: #4b5563;
}

div[role="radiogroup"] [aria-checked="true"] {
    background-color: #4f46e5 !important;
    border-color: #6366f1 !important;
}
</style>
""", unsafe_allow_html=True)

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
            mood TEXT DEFAULT 'معمولی',
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
            quality TEXT DEFAULT 'خوب',
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
    rows = con.execute("SELECT record_date,percent,details FROM records WHERE user_id=? ORDER BY record_date DESC", (uid,)).fetchall()
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

def get_status_label(score):
    if score < 50:
        return "ضعیف 🔴", "error"
    elif score < 70:
        return "متوسط 🟡", "warning"
    elif score < 90:
        return "خوب 🟢", "info"
    else:
        return "عالی 🌟", "success"

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
                st.error("نام کاربری یا رمز عبور اشتباه است.")
    with tab_reg:
        ru = st.text_input("نام کاربری", key="r_u")
        re = st.text_input("ایمیل", key="r_e")
        rp = st.text_input("رمز عبور", type="password", key="r_p")
        if st.button("ساخت حساب"):
            if create_user(ru, re, rp):
                st.success("حساب ساخته شد. اکنون وارد شوید.")
            else:
                st.error("نام کاربری یا ایمیل تکراری است.")
else:
    user = st.session_state.user
    uid = user["id"]
    
    st.sidebar.markdown(f"### 👤 {user['username']}")
    
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
    
    page = st.sidebar.radio("منوی اصلی", menu, label_visibility="collapsed")
    
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 خروج از حساب"):
        st.session_state.user = None
        st.rerun()

    # 1. Dashboard
    if page == "🏠 داشبورد":
        st.header("🏠 داشبورد")
        records = get_records(uid)
        col1, col2, col3 = st.columns(3)
        col1.metric("روزهای ثبت‌شده", len(records))
        col2.metric("تداوم فعلی", f"🔥 {len(records)} روز")
        total_xp = len(records) * 50
        col3.metric("امتیاز XP", f"⭐ {total_xp} XP")

    # 2. Today (With Average Calculation & Dynamic Status Evaluation)
    elif page == "📅 ثبت امروز":
        st.header("📅 ثبت عملکرد روزانه")
        selected_date = st.date_input("تاریخ ثبت", date.today())
        date_str = str(selected_date)
        
        habits = get_habits(uid)
        tot_weight = sum([h['weight'] for h in habits]) or 1
        
        details = {}
        total_score = 0
        st.subheader("درصد انجام فعالیت‌ها:")
        for h in habits:
            val = st.slider(f"{h['name']} (وزن: {h['weight']}%)", 0, 100, 0, key=f"today_{h['id']}")
            details[h['name']] = val
            total_score += (val * h['weight']) / tot_weight

        avg_score = round(total_score, 1)
        status_label, status_type = get_status_label(avg_score)
        
        st.markdown("---")
        st.subheader("📊 خلاصه ارزیابی روز:")
        col_avg, col_stat = st.columns(2)
        col_avg.metric("میانگین/فیصدی عمومی روزانه", f"{avg_score}%")
        col_stat.metric("وضعیت عملکرد", status_label)
        
        if st.button("💾 ذخیره اطلاعات امروز"):
            save_record(uid, date_str, avg_score, details)
            st.success(f"اطلاعات تاریخ {date_str} با درصد کل {avg_score}% ({status_label}) ثبت شد.")

    # 3. Habits
    elif page == "🔁 مدیریت عادت‌ها":
        st.header("🔁 مدیریت عادت‌ها")
        habits = get_habits(uid)
        if habits:
            st.dataframe(pd.DataFrame(habits)[['id', 'name', 'category', 'weight']], use_container_width=True)
        
        st.subheader("عادت جدید")
        h_name = st.text_input("نام عادت")
        h_cat = st.selectbox("دسته‌بندی", ["Learning", "Health", "Skill", "Spiritual"])
        h_weight = st.number_input("وزن (%)", 1, 100, 10)
        if st.button("افزودن"):
            if add_habit(uid, h_name, h_cat, h_weight):
                st.success("اضافه شد.")
                st.rerun()

    # 4. Tasks
    elif page == "📝 لیست کارها":
        st.header("📝 لیست کارها")
        t_title = st.text_input("کار جدید")
        t_prio = st.selectbox("اولویت", ["مهم و فوری", "مهم", "عادی"])
        if st.button("افزودن کار"):
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
    elif page == "🎯 اهداف":
        st.header("🎯 اهداف")
        g_title = st.text_input("عنوان هدف")
        g_dl = st.date_input("مهلت انجام", date.today() + timedelta(days=30))
        if st.button("افزودن هدف"):
            add_goal(uid, g_title, "", str(date.today()), str(g_dl), "normal")
            st.rerun()
            
        goals = get_goals(uid)
        if goals:
            st.dataframe(pd.DataFrame(goals)[['id', 'title', 'deadline', 'progress', 'done']], use_container_width=True)

    # 6. Growth
    elif page == "📈 روند رشد":
        st.header("📈 سابقه و روند رشد پیشرفت")
        records = get_records(uid)
        if records:
            st.subheader("📋 جدول کامل تمامی روزهای ثبت‌شده")
            table_data = []
            for d, val in records.items():
                lbl, _ = get_status_label(val['percent'])
                row = {"تاریخ": d, "میانگین روزانه (%)": f"{val['percent']}%", "وضعیت": lbl}
                if isinstance(val['details'], dict):
                    for h_name, h_val in val['details'].items():
                        row[h_name] = f"{h_val}%"
                table_data.append(row)
            
            df_table = pd.DataFrame(table_data)
            st.dataframe(df_table, use_container_width=True)
            
            st.subheader("📊 نمودار خطی روند پیشرفت")
            df_chart = pd.DataFrame([{"تاریخ": k, "پیشرفت (%)": v["percent"]} for k, v in records.items()])
            df_chart = df_chart.sort_values("تاریخ")
            
            fig = px.line(df_chart, x="تاریخ", y="پیشرفت (%)", markers=True, title="نمودار موفقیت روزانه")
            fig.update_layout(
                xaxis_title="تاریخ",
                yaxis_title="درصد (%)",
                yaxis=dict(range=[0, 105]),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white", family="Vazirmatn"),
                xaxis=dict(type='category')
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("هنوز داده‌ای ثبت نشده است.")

    # 7. Badges
    elif page == "🏆 دستاوردها":
        st.header("🏆 دستاوردها")
        records = get_records(uid)
        if len(records) > 0:
            st.success("🥇 اولین قدم: ثبت موفق اولین روز عملکرد")
            if any(r['percent'] >= 90 for r in records.values()):
                st.success("🌟 فوق‌العاده: دستیابی به میانگین بالای ۹۰٪ در یک روز")
        else:
            st.info("با ثبت اطلاعات روزانه، دستاوردهای خود را باز کنید.")

    # 8. Intelligent Insights (Fully Operational)
    elif page == "🧠 تحلیل هوشمند":
        st.header("🧠 تحلیل هوشمند عملکرد")
        records = get_records(uid)
        if records:
            scores = [v['percent'] for v in records.values()]
            avg = sum(scores) / len(scores)
            st.write(f"**میانگین کل عملکرد شما:** {round(avg, 1)}%")
            if avg >= 80:
                st.success("عملکرد کلی شما بسیار عالی است! تداوم این روند شما را به اهدافتان می‌رساند.")
            elif avg >= 50:
                st.warning("عملکرد متوسطی دارید. تلاش کنید تمرکز بیشتری روی عادت‌های با وزن بالاتر بگذارید.")
            else:
                st.error("میزان پیشرفت پایین است. پیشنهاد می‌شود اهداف کوچک‌تری برای شروع انتخاب کنید.")
        else:
            st.info("برای دریافت تحلیل هوشمند ابتدا چند روز اطلاعات ثبت کنید.")

    # 9. Daily Journal (Fully Operational)
    elif page == "🙂 ژورنال روزانه":
        st.header("🙂 ژورنال روزانه")
        j_date = st.date_input("تاریخ یادداشت", date.today())
        j_mood = st.selectbox("حالت روحی امروز", ["عالی 😃", "خوب 🙂", "معمولی 😐", "خسته 😫", "بد ☹️"])
        j_note = st.text_area("یادداشت روزانه / احساسات امروز")
        
        if st.button("💾 ثبت ژورنال"):
            con = db()
            con.execute("""
                INSERT INTO journal (user_id, journal_date, mood, note) VALUES (?,?,?,?)
                ON CONFLICT(user_id, journal_date) DO UPDATE SET mood=excluded.mood, note=excluded.note
            """, (uid, str(j_date), j_mood, j_note))
            con.commit()
            con.close()
            st.success("یادداشت روزانه با موفقیت ثبت شد.")

    # 10. Sleep Tracker (Fully Operational)
    elif page == "😴 پایش خواب":
        st.header("😴 پایش خواب و استراحت")
        s_date = st.date_input("تاریخ خواب", date.today())
        s_hours = st.number_input("ساعات خواب (ساعت)", 0.0, 24.0, 7.5, step=0.5)
        s_qual = st.select_slider("کیفیت خواب", options=["خیلی بد ❌", "بد ⚠️", "متوسط 😐", "خوب 🟢", "عالی 🌟"])
        
        if st.button("💾 ثبت اطلاعات خواب"):
            con = db()
            con.execute("""
                INSERT INTO sleep (user_id, sleep_date, hours, quality) VALUES (?,?,?,?)
                ON CONFLICT(user_id, sleep_date) DO UPDATE SET hours=excluded.hours, quality=excluded.quality
            """, (uid, str(s_date), s_hours, s_qual))
            con.commit()
            con.close()
            st.success("اطلاعات خواب ذخیره شد.")

    # 11. Settings (Fully Operational)
    elif page == "⚙️ تنظیمات":
        st.header("⚙️ تنظیمات حساب کاربری")
        st.write(f"**نام کاربری:** {user['username']}")
        st.write(f"**ایمیل:** {user['email']}")
        st.write(f"**تاریخ ساخت حساب:** {user['created_at'][:10]}")
        
