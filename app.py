import streamlit as st
import sqlite3
from datetime import date

# 1. تنظیمات صفحه
st.set_page_config(
    page_title="MyGrowth Pro Max",
    page_icon="🚀",
    layout="wide"
)

# 2. پایگاه داده
def init_db():
    conn = sqlite3.connect("growth.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS daily_log (
            uid TEXT,
            entry_date TEXT,
            habit_name TEXT,
            progress INTEGER,
            PRIMARY KEY (uid, entry_date, habit_name)
        )
    """)
    conn.commit()
    conn.close()

init_db()

def save_log(uid, entry_date, habit_name, progress):
    conn = sqlite3.connect("growth.db")
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO daily_log (uid, entry_date, habit_name, progress)
        VALUES (?, ?, ?, ?)
    """, (uid, entry_date, habit_name, progress))
    conn.commit()
    conn.close()

uid = "default_user"

# 3. استایل CSS اصلاح‌شده (رفع کامل مشکل ظاهر تب‌ها و فونت‌ها)
st.markdown("""
<style>
.stApp {
    background-color: #0e1117;
}
.block-container {
    padding-top: 2rem !important;
    max-width: 1200px;
}
div[data-baseweb="tab-list"] {
    gap: 10px !important;
    flex-wrap: wrap !important;
}
button[data-baseweb="tab"] {
    background-color: #1e2530 !important;
    border-radius: 8px !important;
    padding: 8px 16px !important;
    color: #ffffff !important;
    font-size: 15px !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    background-color: #ff4b4b !important;
    color: #ffffff !important;
    font-weight: bold !important;
}
</style>
""", unsafe_allow_html=True)

# 4. تعریف تب‌ها
tabs = st.tabs([
    "🏠 داشبورد",
    "📅 ثبت امروز",
    "🔄 عادت‌ها",
    "📝 کارها",
    "🎯 اهداف",
    "⚙️ تنظیمات"
])

# 5. محتوای تب‌ها
with tabs[0]:
    st.header("🏠 داشبورد اصلی")
    st.success("به برنامه رشد فردی خوش آمدید!")

with tabs[1]:
    st.header("📅 ثبت وضعیت و فعالیت‌های امروز")
    
    selected_date = st.date_input("انتخاب تاریخ", date.today())
    
    st.subheader("ورود اطلاعات عادت‌ها:")
    study_prog = st.slider("مطالعه (درصد):", 0, 100, 50)
    exercise_prog = st.slider("ورزش (درصد):", 0, 100, 0)
    chinese_prog = st.slider("مطالعه چینی (درصد):", 0, 100, 0)
    
    if st.button("💾 ذخیره اطلاعات امروز"):
        save_log(uid, str(selected_date), "مطالعه", study_prog)
        save_log(uid, str(selected_date), "ورزش", exercise_prog)
        save_log(uid, str(selected_date), "چینی", chinese_prog)
        st.success("اطلاعات با موفقیت ذخیره شد!")

with tabs[2]:
    st.header("🔄 مدیریت عادت‌ها")
    st.write("در این بخش می‌توانید عادت‌های جدید تعریف کنید.")

with tabs[3]:
    st.header("📝 لیست کارها")
    st.text_input("کار جدید:")

with tabs[4]:
    st.header("🎯 اهداف")
    st.write("پیگیری اهداف ماهانه و سالانه.")

with tabs[5]:
    st.header("⚙️ تنظیمات")
    st.write("تنظیمات برنامه.")
    
