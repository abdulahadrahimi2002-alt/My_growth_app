import streamlit as st
import json
import os
import hashlib
from datetime import date, datetime, timedelta
import pandas as pd
import plotly.graph_objects as go

# ----------------- Configuration & CSS -----------------
st.set_page_config(page_title="MyGrowth Pro", page_icon="🚀", layout="wide")

st.markdown("""
<style>
    .main { direction: rtl; text-align: right; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    .stMetric { background-color: #1e222d; padding: 10px; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

USER_DIR = "users_data"
if not os.path.exists(USER_DIR):
    os.makedirs(USER_DIR)

# ----------------- Translations -----------------
TRANSLATIONS = {
    "Dari": {
        "title": "🚀 MyGrowth Pro - سیستم مدیریت رشد و عادت‌ها",
        "login": "ورود به حساب",
        "register": "ثبت‌نام کاربر جدید",
        "username": "نام کاربری",
        "password": "رمز عبور",
        "logout": "خروج از حساب",
        "dash": "🏠 داشبورد",
        "today": "📅 ثبت روزانه",
        "habits": "🔁 مدیریت عادت‌ها",
        "tasks": "📝 کارهای روزانه",
        "goals": "🎯 اهداف با ددلاین",
        "calendar": "📅 تقویم ماهانه",
        "charts": "📈 نمودارهای پیشرفت",
        "badges": "🏆 مدال‌ها و Streak",
        "insights": "🧠 تحلیل هوشمند",
        "journal": "🙂 حس‌وحال و یادداشت",
        "settings": "💾 پشتیبان‌گیری و خروجی",
        "save": "ذخیره تغییرات",
        "success": "با موفقیت ذخیره شد!"
    },
    "English": {
        "title": "🚀 MyGrowth Pro - Personal Growth Tracker",
        "login": "Login",
        "register": "Register New Account",
        "username": "Username",
        "password": "Password",
        "logout": "Logout",
        "dash": "🏠 Dashboard",
        "today": "📅 Daily Entry",
        "habits": "🔁 Habits & Weights",
        "tasks": "📝 Daily Tasks",
        "goals": "🎯 Goals & Deadlines",
        "calendar": "📅 Monthly Calendar",
        "charts": "📈 Growth Charts",
        "badges": "🏆 Badges & Streak",
        "insights": "🧠 Smart Insights",
        "journal": "🙂 Mood & Journal",
        "settings": "💾 Backup & Export",
        "save": "Save Changes",
        "success": "Saved Successfully!"
    }
}

# ----------------- Helper Functions -----------------
def hash_pass(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_user_path(username, filename):
    u_folder = os.path.join(USER_DIR, hash_pass(username)[:16])
    if not os.path.exists(u_folder):
        os.makedirs(u_folder)
    return os.path.join(u_folder, filename)

def load_user_json(username, filename, default):
    path = get_user_path(username, filename)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    return default

def save_user_json(username, filename, data):
    path = get_user_path(username, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def calculate_streak(records):
    if not records:
        return 0
    dates = sorted([date.fromisoformat(k) for k in records.keys()], reverse=True)
    today = date.today()
    streak = 0
    check_date = today
    if today not in dates and (today - timedelta(days=1)) in dates:
        check_date = today - timedelta(days=1)
    while check_date in dates:
        streak += 1
        check_date -= timedelta(days=1)
    return streak

# ----------------- Authentication -----------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "lang" not in st.session_state:
    st.session_state.lang = "Dari"

lang_choice = st.sidebar.radio("🌐 Language / زبان", ["🇦🇫 دری", "🇬🇧 English"])
st.session_state.lang = "Dari" if "دری" in lang_choice else "English"
T = TRANSLATIONS[st.session_state.lang]

users_db = load_user_json("system", "users.json", {})

if not st.session_state.authenticated:
    st.title(T["title"])
    auth_mode = st.radio("انتخاب کنید / Choose", [T["login"], T["register"]])
    
    u_in = st.text_input(T["username"])
    p_in = st.text_input(T["password"], type="password")
    
    if auth_mode == T["login"]:
        if st.button(T["login"]):
            if u_in in users_db and users_db[u_in] == hash_pass(p_in):
                st.session_state.authenticated = True
                st.session_state.username = u_in
                st.success("ورود موفقیت‌آمیز بود!")
                st.rerun()
            else:
                st.error("نام کاربری یا رمز عبور اشتباه است.")
    else:
        if st.button(T["register"]):
            if u_in in users_db:
                st.error("این نام کاربری قبلاً ثبت شده است.")
            elif u_in and p_in:
                users_db[u_in] = hash_pass(p_in)
                save_user_json("system", "users.json", users_db)
                st.success("ثبت‌نام با موفقیت انجام شد! اکنون وارد شوید.")
            else:
                st.warning("لطفاً همه فیلدها را پر کنید.")
    st.stop()

# ----------------- Authenticated User Space -----------------
user = st.session_state.username
st.sidebar.title(f"👤 {user}")
if st.sidebar.button(T["logout"]):
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.rerun()

# Load User Specific Data
habits_data = load_user_json(user, "habits.json", {"نماز / عبادات": 40, "ورزش": 30, "مطالعه": 30})
records = load_user_json(user, "records.json", {})
tasks = load_user_json(user, "tasks.json", [])
goals = load_user_json(user, "goals.json", [])
journal = load_user_json(user, "journal.json", {})

# Main Navigation
tabs = st.tabs([
    T["dash"], T["today"], T["habits"], T["tasks"], 
    T["goals"], T["calendar"], T["charts"], T["badges"], 
    T["insights"], T["journal"], T["settings"]
])

# ---------------- Tab 1: Dashboard ----------------
with tabs[0]:
    st.subheader(T["dash"])
    streak = calculate_streak(records)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("کل روزهای ثبت‌شده", len(records))
    avg_p = sum(r.get("percent", 0) for r in records.values()) / len(records) if records else 0
    c2.metric("میانگین عملکرد", f"{avg_p:.1f}%")
    c3.metric("تعداد عادت‌ها", len(habits_data))
    c4.metric("تسلسل (Streak) 🔥", f"{streak} روز")
    
    st.markdown("---")
    st.write("📌 **خلاصه وضعیت امروز:**")
    today_str = str(date.today())
    if today_str in records:
        st.success(f"عملکرد امروز ذخیره شده است: {records[today_str]['percent']}%")
    else:
        st.info("عملکرد امروز هنوز ثبت نشده است.")

# ---------------- Tab 2: Daily Entry ----------------
with tabs[1]:
    st.subheader(T["today"])
    today_str = str(date.today())
    st.write(f"📅 **تاریخ:** {today_str}")
    
    if not habits_data:
        st.warning("لطفاً ابتدا از تب عادت‌ها، عادت‌های خود را تعریف کنید.")
    else:
        scores = {}
        total_possible = sum(habits_data.values())
        total_earned = 0
        
        for h, w in habits_data.items():
            st.write(f"**{h}** (وزن: {w}٪)")
            val = st.slider(f"درصد انجام {h}", 0, 100, 0, step=5, key=f"today_{h}")
            earned = (val / 100) * w
            scores[h] = val
            total_earned += earned
            st.caption(f"امتیاز کسب شده: {earned:.1f}٪ از {w}٪")
            st.markdown("---")
            
        final_pct = int((total_earned / total_possible) * 100) if total_possible > 0 else 0
        st.progress(final_pct / 100)
        st.subheader(f"مجموع امتیاز امروز: **{final_pct}%**")
        
        if st.button(T["save"]):
            records[today_str] = {"percent": final_pct, "details": scores}
            save_user_json(user, "records.json", records)
            st.success(T["success"])

# ---------------- Tab 3: Habits & Weights ----------------
with tabs[2]:
    st.subheader(T["habits"])
    col1, col2 = st.columns([3, 2])
    with col1:
        new_h = st.text_input("نام عادت جدید:")
    with col2:
        new_w = st.number_input("وزن/ارزش (درصد):", 5, 100, 20, step=5)
        
    if st.button("افزودن عادت"):
        if new_h:
            habits_data[new_h] = new_w
            save_user_json(user, "habits.json", habits_data)
            st.rerun()
            
    total_w = sum(habits_data.values())
    st.info(f"مجموع وزن فعلی: **{total_w}%** (پیشنهاد: مجموع دقیقاً ۱۰۰٪ باشد)")
    
    for h, w in list(habits_data.items()):
        c_a, c_b, c_c = st.columns([3, 2, 1])
        c_a.write(f"• **{h}**")
        c_b.write(f"وزن: {w}٪")
        if c_c.button("حذف", key=f"del_h_{h}"):
            del habits_data[h]
            save_user_json(user, "habits.json", habits_data)
            st.rerun()

# ---------------- Tab 4: Tasks ----------------
with tabs[3]:
    st.subheader(T["tasks"])
    t_input = st.text_input("کار جدید:")
    t_prio = st.selectbox("اولویت", ["مهم و فوری", "مهم", "عادی"])
    if st.button("افزودن کار"):
        if t_input:
            tasks.append({"text": t_input, "prio": t_prio, "done": False})
            save_user_json(user, "tasks.json", tasks)
            st.rerun()
            
    for i, t in enumerate(tasks):
        chk = st.checkbox(f"[{t['prio']}] {t['text']}", value=t["done"], key=f"task_{i}")
        if chk != t["done"]:
            tasks[i]["done"] = chk
            save_user_json(user, "tasks.json", tasks)

# ---------------- Tab 5: Goals & Deadlines ----------------
with tabs[4]:
    st.subheader(T["goals"])
    g_title = st.text_input("عنوان هدف:")
    g_date = st.date_input("تاریخ مهلت (Deadline):")
    if st.button("افزودن هدف"):
        if g_title:
            goals.append({"title": g_title, "deadline": str(g_date), "progress": 0})
            save_user_json(user, "goals.json", goals)
            st.rerun()
            
    for i, g in enumerate(goals):
        st.write(f"🎯 **{g['title']}** (مهلت: {g['deadline']})")
        prog = st.slider("درصد پیشرفت", 0, 100, g.get("progress", 0), key=f"goal_prog_{i}")
        if prog != g.get("progress", 0):
            goals[i]["progress"] = prog
            save_user_json(user, "goals.json", goals)

# ---------------- Tab 6: Calendar ----------------
with tabs[5]:
    st.subheader(T["calendar"])
    if records:
        df_cal = pd.DataFrame([{"Date": k, "Percent": v["percent"]} for k, v in records.items()])
        st.dataframe(df_cal, use_container_width=True)
    else:
        st.info("داده‌ای ثبت نشده است.")

# ---------------- Tab 7: Charts ----------------
with tabs[6]:
    st.subheader(T["charts"])
    if records:
        keys = sorted(records.keys())
        period = st.selectbox("بازه زمانی", ["7", "30", "90", "All"])
        n = len(keys) if period == "All" else int(period)
        ck = keys[-n:]
        vals = [records[k]["percent"] for k in ck]

        fig = go.Figure(go.Scatter(x=ck, y=vals, mode="lines+markers", line=dict(color="#00FF7F", width=3)))
        fig.update_layout(yaxis=dict(range=[0, 105]), height=400)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("داده‌ای موجود نیست.")

# ---------------- Tab 8: Badges & Streak ----------------
with tabs[7]:
    st.subheader(T["badges"])
    st.write(f"🔥 **تسلسل فعلی شما:** {streak} روز")
    if streak >= 3:
        st.success("🏆 مدال ۳ روز تداوم")
    if streak >= 7:
        st.success("👑 مدال ۱ هفته تداوم")
    if streak >= 30:
        st.success("🌟 مدال اسطوره تداوم (۳۰ روز)")

# ---------------- Tab 9: Smart Insights ----------------
with tabs[8]:
    st.subheader(T["insights"])
    if records:
        avg_score = sum(r["percent"] for r in records.values()) / len(records)
        if avg_score >= 80:
            st.success("🧠 **تحلیل:** عملکرد شما فوق‌العاده است! تداوم خود را حفظ کنید.")
        elif avg_score >= 50:
            st.info("🧠 **تحلیل:** روند شما خوب است، اما با کمی برنامه‌ریزی روی عادت‌های با وزن بالا می‌توانید به ممتاز برسید.")
        else:
            st.warning("🧠 **تحلیل:** عملکرد پایین‌تر از حد انتظار است. پیشنهاد می‌شود اهداف روزانه را کوچک‌تر کنید.")
    else:
        st.info("پس از چند روز ثبت اطلاعات، تحلیل هوشمند فعال می‌شود.")

# ---------------- Tab 10: Journal & Mood ----------------
with tabs[9]:
    st.subheader(T["journal"])
    mood = st.select_slider("حس و حال امروز شما:", options=["😢 بد", "😐 معمولی", "🙂 خوب", "🚀 عالی"])
    j_text = st.text_area("یادداشت روزانه:")
    if st.button("ذخیره یادداشت"):
        journal[str(date.today())] = {"mood": mood, "text": j_text}
        save_user_json(user, "journal.json", journal)
        st.success(T["success"])

# ---------------- Tab 11: Settings, Backup & Export ----------------
with tabs[10]:
    st.subheader(T["settings"])
    
    st.write("📥 **خروجی داده‌ها به CSV:**")
    if records:
        df_exp = pd.DataFrame([{"Date": k, "Percent": v["percent"]} for k, v in records.items()])
        st.download_button("دانلود گزارش CSV", df_exp.to_csv(index=False), "MyGrowth_Data.csv", "text/csv")
        
    st.markdown("---")
    st.write("💾 **پشتیبان‌گیری و بازیابی داده‌ها (Backup / Restore):**")
    
    # Backup
    user_all_data = {
        "habits": habits_data,
        "records": records,
        "tasks": tasks,
        "goals": goals,
        "journal": journal
    }
    st.download_button("دانلود فایل پشتیبان (JSON)", json.dumps(user_all_data, ensure_ascii=False, indent=2), f"{user}_backup.json", "application/json")
    
    # Restore
    uploaded_file = st.file_uploader("بازیابی فایل پشتیبان (Restore JSON)", type=["json"])
    if uploaded_file is not None:
        try:
            restored_data = json.load(uploaded_file)
            if "habits" in restored_data:
                save_user_json(user, "habits.json", restored_data["habits"])
                save_user_json(user, "records.json", restored_data.get("records", {}))
                save_user_json(user, "tasks.json", restored_data.get("tasks", []))
                save_user_json(user, "goals.json", restored_data.get("goals", []))
                save_user_json(user, "journal.json", restored_data.get("journal", {}))
                st.success("اطلاعات با موفقیت بازیابی شد! برنامه را دوباره بارگذاری کنید.")
        except Exception as e:
            st.error("خطا در بازیابی فایل.")
    
