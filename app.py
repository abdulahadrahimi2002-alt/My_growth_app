import streamlit as st
import sqlite3
import hashlib
import secrets
import json
from datetime import datetime, date, timedelta

import pandas as pd
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

    [data-testid="stSidebar"] {
        direction: rtl;
        background-color: #111827;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

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
    con.row_factory = sqlite3.Row
    row = con.execute("SELECT * FROM users WHERE LOWER(username)=LOWER(?)", (username.strip(),)).fetchone()
    con.close()
    if row and verify_password(password, row["password_hash"]):
        return dict(row)
    return None

def create_user(username, email, password, language="dari"):
    username_clean = username.strip()
    email_clean = email.strip().lower()
    
    if not username_clean or not email_clean or not password:
        return False, "لطفاً تمامی فیلدها را پر کنید."
        
    con = db()
    cur = con.cursor()
    
    existing = cur.execute(
        "SELECT id FROM users WHERE LOWER(username)=? OR LOWER(email)=?", 
        (username_clean.lower(), email_clean)
    ).fetchone()
    
    if existing:
        con.close()
        return False, "این نام کاربری یا ایمیل قبلاً ثبت شده است. لطفاً نام دیگری انتخاب کنید."
        
    try:
        cur.execute(
            "INSERT INTO users (username,email,password_hash,language,created_at) VALUES(?,?,?,?,?)",
            (username_clean, email_clean, hash_password(password), language, datetime.now().isoformat())
        )
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
        return True, "حساب با موفقیت ساخته شد!"
    except Exception as e:
        con.rollback()
        return False, f"خطا در ساخت حساب: {str(e)}"
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

# ============================================================
# INTERFACE
# ============================================================

if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    st.title("🚀 MyGrowth Pro Max")
    st.caption("سیستم پیشرفته مدیریت رشد شخصی و عادت‌ها")
    
    tab_login, tab_reg = st.tabs(["ورود به حساب", "ساخت حساب جدید"])
    
    with tab_login:
        u = st.text_input("نام کاربری", key="l_u")
        p = st.text_input("رمز عبور", type="password", key="l_p")
        if st.button("ورود"):
            if u and p:
                usr = authenticate(u, p)
                if usr:
                    st.session_state.user = usr
                    st.success("ورود موفقیت‌آمیز بود!")
                    st.rerun()
                else:
                    st.error("نام کاربری یا رمز عبور اشتباه است.")
            else:
                st.warning("لطفاً نام کاربری و رمز عبور را وارد کنید.")

    with tab_reg:
        ru = st.text_input("نام کاربری جدید", key="r_u")
        re = st.text_input("ایمیل", key="r_e")
        rp = st.text_input("رمز عبور جدید", type="password", key="r_p")
        
        if st.button("ثبت‌نام و ساخت حساب"):
            success, message = create_user(ru, re, rp)
            if success:
                st.success(message)
                st.info("اکنون می‌توانید از تب 'ورود به حساب' وارد شوید.")
            else:
                st.error(message)

else:
    user = st.session_state.user
    uid = user["id"]
    
    st.sidebar.markdown(f"### 👤 {user['username']}")
    menu = [
        "🏠 داشبورد",
        "📅 ثبت امروز",
        "🔁 مدیریت عادت‌ها",
        "📈 روند رشد",
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
        st.metric("میانگین عملکرد روزانه", f"{avg_score}%")
        
        if st.button("💾 ذخیره عملکرد"):
            save_record(uid, d_str, avg_score, details)
            st.success(f"اطلاعات تاریخ {d_str} ذخیره شد.")

    # 3. Habits
    elif page == "🔁 مدیریت عادت‌ها":
        st.header("🔁 عادت‌های من")
        habits = get_habits(uid)
        if habits:
            df_h = pd.DataFrame(habits, columns=['کد', 'نام عادت', 'دسته‌بندی', 'وزن (%)', 'فعال'])
            st.dataframe(df_h[['نام عادت', 'دسته‌بندی', 'وزن (%)']], use_container_width=True)

        st.subheader("➕ افزودن عادت جدید")
        h_name = st.text_input("نام عادت")
        h_cat = st.selectbox("دسته‌بندی", ["سلامت", "یادگیری", "مهارت", "عمومی"])
        h_weight = st.number_input("وزن (%)", 1, 100, 20)
        if st.button("افزودن عادت"):
            if add_habit(uid, h_name, h_cat, h_weight):
                st.success("عادت جدید اضافه شد.")
                st.rerun()

    # 4. Growth
    elif page == "📈 روند رشد":
        st.header("📈 روند رشد")
        records = get_records(uid)
        if records:
            data = [{"تاریخ": d, "عملکرد (%)": v['percent']} for d, v in records.items()]
            df = pd.DataFrame(data).sort_values("تاریخ")
            fig = px.line(df, x="تاریخ", y="عملکرد (%)", markers=True)
            st.plotly_chart(fig, use_container_width=True)

    # 5. Settings
    elif page == "⚙️ تنظیمات":
        st.header("⚙️ تنظیمات")
        st.write(f"**نام کاربری:** {user['username']}")
        st.write(f"**ایمیل:** {user['email']}")
