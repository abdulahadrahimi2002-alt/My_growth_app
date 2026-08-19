import hashlib
import json
import secrets
import sqlite3
from datetime import date, datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

# ============================================================
# 1. تنظیمات صفحه و فونت
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
# 2. توابع کمکی (استایل ایموجی به‌جای رنگ کل باکس)
# ============================================================


def get_status_info(percent):
    """بازگرداندن نام وضعیت همراه با ایموجی دایره‌ای رنگی"""
    if percent >= 85:
        return "🟢 عالی"
    elif percent >= 70:
        return "🔵 خوب"
    elif percent >= 50:
        return "🟡 متوسط"
    else:
        return "🔴 ضعیف"


# ============================================================
# 3. پایگاه داده و امنیت
# ============================================================


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
            category TEXT DEFAULT 'عمومی',
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

    # کاربر رحیمی
    now_iso = datetime.now().isoformat()
    admin_exists = cur.execute(
        "SELECT id FROM users WHERE LOWER(username)='rahimi'"
    ).fetchone()
    if not admin_exists:
        cur.execute(
            "INSERT INTO users (username,email,password_hash,language,created_at)"
            " VALUES(?,?,?,?,?)",
            (
                "Rahimi",
                "abdulahad.rahimi2002@gmail.com",
                hash_password("Rahimi2002"),
                "dari",
                now_iso,
            ),
        )
        user_id = cur.lastrowid
        default_habits = [
            ("مطالعه", "یادگیری", 30),
            ("ورزش", "سلامت", 30),
            ("مطالعه چینی", "یادگیری", 20),
            ("کدنویسی پایتون", "مهارت", 20),
        ]
        for name, category, weight in default_habits:
            cur.execute(
                "INSERT INTO habits (user_id,name,category,weight,created_at)"
                " VALUES(?,?,?,?,?)",
                (user_id, name, category, weight, now_iso),
            )
        con.commit()

    con.close()


init_db()


# ============================================================
# 4. توابع مدیریت داده‌ها
# ============================================================


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
        return False, "لطفاً تمامی فیلدها را پر کنید."

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
            ("مطالعه", "یادگیری", 30),
            ("ورزش", "سلامت", 30),
            ("مطالعه چینی", "یادگیری", 20),
            ("کدنویسی پایتون", "مهارت", 20),
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
        return False, f"خطا در ساخت حساب: {str(e)}"
    finally:
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
            details = json.loads(details or "{}")
        except Exception:
            details = {}
        result[d] = {"percent": percent, "details": details}
    return result


def get_habits(user_id):
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
    con.execute(
        """
        INSERT INTO records (user_id,record_date,percent,details) VALUES(?,?,?,?)
        ON CONFLICT(user_id,record_date) DO UPDATE SET percent=excluded.percent, details=excluded.details
    """,
        (user_id, record_date, percent, json.dumps(details, ensure_ascii=False)),
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
    try:
        con = db()
        rows = con.execute(
            "SELECT id, title, description, deadline, progress, category FROM"
            " goals WHERE user_id=? ORDER BY id DESC",
            (user_id,),
        ).fetchall()
        con.close()
        return rows
    except Exception:
        return []


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
    try:
        con = db()
        row = con.execute(
            "SELECT mood, note FROM journal WHERE user_id=? AND note_date=?",
            (user_id, str(note_date)),
        ).fetchone()
        con.close()
        return row
    except Exception:
        return None


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
    try:
        con = db()
        row = con.execute(
            "SELECT hours, quality FROM sleep WHERE user_id=? AND sleep_date=?",
            (user_id, str(sleep_date)),
        ).fetchone()
        con.close()
        return row
    except Exception:
        return None


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


# ============================================================
# 5. رابط کاربری (Streamlit UI)
# ============================================================

if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    st.title("🚀 MyGrowth Pro Max")
    st.caption("سیستم پیشرفته مدیریت رشد شخصی")

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

    with tab_reg:
        ru = st.text_input("نام کاربری جدید", key="r_u")
        re = st.text_input("ایمیل", key="r_e")
        rp = st.text_input("رمز عبور جدید", type="password", key="r_p")

        if st.button("ثبت‌نام و ساخت حساب"):
            success, message = create_user(ru, re, rp)
            if success:
                st.success(message)
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
        "📝 لیست کارها",
        "🎯 اهداف",
        "📈 روند رشد",
        "🏆 دستاوردها",
        "🧠 تحلیل هوشمند",
        "🙂 ژورنال روزانه",
        "😴 پایش خواب",
        "⚙️ تنظیمات",
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

        today_score = 0
        month_score = 0
        status_label = get_status_info(0)

        if records:
            today_str = str(date.today())
            if today_str in records:
                today_score = records[today_str]["percent"]
            else:
                last_record = list(records.values())[-1]
                today_score = last_record["percent"]

            status_label = get_status_info(today_score)

            recent_30 = [v["percent"] for v in list(records.values())[-30:]]
            month_score = round(sum(recent_30) / len(recent_30), 1)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("تداوم فعلی (Streak)", f"🔥 {streak} روز")
        col2.metric("عملکرد روزانه (امروز)", f"{today_score}%")
        col3.metric("میانگین ۳۰ روز اخیر (ماهانه)", f"{month_score}%")
        col4.metric("ارزیابی وضعیت", status_label)

    # 2. Daily Record
    elif page == "📅 ثبت امروز":
        st.header("📅 ثبت عملکرد روزانه")
        sel_date = st.date_input("تاریخ ثبت", date.today())
        d_str = str(sel_date)
        habits = get_habits(uid)
        tot_weight = sum([h[3] for h in habits]) or 1

        existing_record = get_records(uid).get(d_str, {}).get("details", {})

        details = {}
        total_score = 0
        for h in habits:
            init_val = existing_record.get(h[1], 0)
            val = st.slider(
                f"{h[1]} (وزن: {h[3]}%)",
                0,
                100,
                int(init_val),
                key=f"h_{h[0]}_{d_str}",
            )
            details[h[1]] = val
            total_score += (val * h[3]) / tot_weight

        avg_score = round(total_score, 1)
        status_label = get_status_info(avg_score)

        c1, c2 = st.columns(2)
        c1.metric("میانگین عملکرد این روز", f"{avg_score}%")
        c2.metric("ارزیابی وضعیت", status_label)

        if st.button("💾 ذخیره عملکرد"):
            save_record(uid, d_str, avg_score, details)
            st.success(f"عملکرد تاریخ {d_str} با موفقیت ذخیره شد!")

    # 3. Habits Management
    elif page == "🔁 مدیریت عادت‌ها":
        st.header("🔁 عادت‌های من")
        habits = get_habits(uid)
        if habits:
            df_h = pd.DataFrame(
                habits, columns=["کد", "نام عادت", "دسته‌بندی", "وزن (%)", "فعال"]
            )
            st.dataframe(
                df_h[["نام عادت", "دسته‌بندی", "وزن (%)"]], use_container_width=True
            )

        st.subheader("➕ افزودن عادت جدید")
        h_name = st.text_input("نام عادت")
        h_cat = st.selectbox("دسته‌بندی", ["سلامت", "یادگیری", "مهارت", "عمومی"])
        h_weight = st.number_input("وزن (%)", 1, 100, 20)
        if st.button("افزودن عادت"):
            if add_habit(uid, h_name, h_cat, h_weight):
                st.success("عادت جدید اضافه شد.")
                st.rerun()

    # 4. Tasks
    elif page == "📝 لیست کارها":
        st.header("📝 کارهای روزمره (تاریخ‌وار)")
        t_date = st.date_input("انتخاب تاریخ جهت ثبت یا مشاهده کارها", date.today())
        tasks = get_tasks(uid, t_date)

        st.subheader(f"📋 لیست کارهای تاریخ: {t_date}")
        if tasks:
            for t in tasks:
                chk = st.checkbox(
                    f"{t[1]} (اولویت: {t[2]})", value=bool(t[3]), key=f"t_{t[0]}"
                )
                if chk != bool(t[3]):
                    toggle_task(t[0], chk)
                    st.rerun()
        else:
            st.info("کاری برای این تاریخ ثبت نشده است.")

        st.subheader("➕ افزودن کار جدید برای این تاریخ")
        t_title = st.text_input("عنوان کار")
        t_prio = st.selectbox("اولویت", ["عالی/ضروری", "متوسط", "پایین"])
        if st.button("افزودن کار"):
            if t_title:
                add_task(uid, t_date, t_title, t_prio)
                st.success("کار اضافه شد.")
                st.rerun()

    # 5. Goals
    elif page == "🎯 اهداف":
        st.header("🎯 اهداف شخصی")
        goals = get_goals(uid)
        if goals:
            for g in goals:
                st.markdown(f"### {g[1]} ({g[5]})")
                st.write(f"توضیحات: {g[2]} | ددلاین: {g[3]}")
                prog = st.slider("درصد پیشرفت", 0, 100, g[4], key=f"g_{g[0]}")
             
