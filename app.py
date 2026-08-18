import streamlit as st
import sqlite3
from datetime import date

# 1. Page Configuration
st.set_page_config(
    page_title="MyGrowth Pro Max",
    page_icon="🚀",
    layout="wide"
)

# 2. Database Initialization
def init_db():
    conn = sqlite3.connect("growth.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS sleep (
            uid TEXT,
            date TEXT,
            hours REAL,
            quality INTEGER,
            PRIMARY KEY (uid, date)
        )
    """)
    conn.commit()
    conn.close()

init_db()

def save_sleep(uid, s_date, hours, quality):
    conn = sqlite3.connect("growth.db")
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO sleep (uid, date, hours, quality)
        VALUES (?, ?, ?, ?)
    """, (uid, s_date, hours, quality))
    conn.commit()
    conn.close()

def get_sleep(uid, s_date):
    conn = sqlite3.connect("growth.db")
    c = conn.cursor()
    c.execute("SELECT hours, quality FROM sleep WHERE uid=? AND date=?", (uid, s_date))
    row = c.fetchone()
    conn.close()
    if row:
        return {"hours": row[0], "quality": row[1]}
    return None

# 3. User Setup
uid = "default_user"

# 4. Clean Custom CSS (Fixes UI and Tab Display Issues)
st.markdown("""
<style>
.stApp {
    background-color: #0e1117;
}
.block-container {
    padding-top: 1.5rem !important;
    max-width: 1200px;
}
div[data-baseweb="tab-list"] {
    gap: 6px !important;
    flex-wrap: wrap !important;
}
button[data-baseweb="tab"] {
    background-color: rgba(255, 255, 255, 0.05) !important;
    border-radius: 6px !important;
    padding: 6px 12px !important;
    color: #ffffff !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    background-color: #ff4b4b !important;
    color: #ffffff !important;
}
</style>
""", unsafe_allow_html=True)

# 5. Define Navigation Tabs
tabs = st.tabs([
    "🏠 داشبورد",
    "📅 امروز",
    "🔄 عادت‌ها",
    "📝 کارها",
    "🎯 اهداف",
    "📅 تقویم",
    "📈 رشد من",
    "🏆 دستاوردها",
    "🧠 تحلیل هوشمند",
    "📖 ژورنال",
    "😴 خواب",
    "⚙️ تنظیمات"
])

# 6. Content for Each Tab
with tabs[0]:
    st.title("🏠 داشبورد اصلی")
    st.info("به برنامه رشد فردی خوش آمدید! وضعیت کلی شما در اینجا نمایش داده می‌شود.")

with tabs[1]:
    st.title("📅 ثبت وضعیت امروز")
    st.write("عادت‌ها و فعالیت‌های امروز خود را ثبت کنید.")

with tabs[2]:
    st.title("🔄 مدیریت عادت‌ها")
    st.write("عادت‌های جدید اضافه کنید یا وزن آن‌ها را تنظیم کنید.")

with tabs[3]:
    st.title("📝 مدیریت کارها (Tasks)")
    st.write("کارهای روزانه و اولویت‌بندی آن‌ها.")

with tabs[4]:
    st.title("🎯 اهداف (Goals)")
    st.write("اهداف کوتاه مدت و بلند مدت خود را دنبال کنید.")

with tabs[5]:
    st.title("📅 تقویم عملکرد")
    st.write("نمایش عملکرد ماهانه.")

with tabs[6]:
    st.title("📈 نمودار رشد")
    st.write("پیشرفت ۷، ۳۰ و ۹۰ روزه خود را مشاهده کنید.")

with tabs[7]:
    st.title("🏆 مدال‌ها و دستاوردها")
    st.write("مدال‌های کسب‌شده بر اساس عملکرد.")

with tabs[8]:
    st.title("🧠 تحلیل هوشمند")
    st.write("تحلیل وضعیت بر اساس الگوریتم‌ها.")

with tabs[9]:
    st.title("📖 ژورنال روزانه")
    st.write("یادداشت‌های روزانه و افکار خود را بنویسید.")

with tabs[10]:
    st.title("😴 پیگیری خواب")
    sleep_date = st.date_input("تاریخ", date.today(), key="sleep_date")
    sd = str(sleep_date)
    old_sleep = get_sleep(uid, sd) or {}

    hours = st.number_input(
        "ساعت خواب",
        0.0, 24.0,
        float(old_sleep.get("hours", 8)),
        0.5
    )
    quality = st.slider(
        "کیفیت خواب (۱ تا ۵)",
        1, 5,
        int(old_sleep.get("quality", 3))
    )

    if st.button("💾 ذخیره خواب", key="save_sleep"):
        save_sleep(uid, sd, hours, quality)
        st.success("اطلاعات خواب با موفقیت ذخیره شد!")
        st.rerun()

with tabs[11]:
    st.title("⚙️ تنظیمات")
    st.write("تنظیمات حساب کاربری و برنامه.")
    
