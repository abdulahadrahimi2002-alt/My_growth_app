import streamlit as st
import json
import os
from datetime import date, timedelta
import pandas as pd
import plotly.graph_objects as go

# ---------------- File Paths ----------------
HABITS_FILE = "habits.json"
RECORDS_FILE = "records.json"
GOALS_FILE = "goals.json"
NOTES_FILE = "notes.json"

# ---------------- Helper Functions ----------------
def load_json(filepath, default):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    return default

def save_json(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def status(p):
    if p >= 85:
        return "عالی / Excellent"
    elif p >= 70:
        return "خوب / Good"
    elif p >= 50:
        return "متوسط / Average"
    return "نیاز به تلاش / Needs Effort"

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

def get_badges(records, streak):
    badges = []
    total_records = len(records)
    
    if streak >= 3:
        badges.append("🔥 ۳ روز متوالی (شروع قوی)")
    if streak >= 7:
        badges.append("⚡ ۱ هفته تداوم (استاد عادت)")
    if streak >= 30:
        badges.append("👑 ۳۰ روز تداوم (اسطوره نظم)")
        
    hundreds = sum(1 for r in records.values() if r.get("percent", 0) >= 100)
    if hundreds >= 1:
        badges.append("🎯 اولین ۱۰۰٪ (عملکرد کامل)")
    if hundreds >= 10:
        badges.append("🌟 ۱۰ روز ۱۰۰٪ (قهرمان تمرکز)")
        
    if total_records >= 30:
        badges.append("📚 ثبت ۳۰ روز داده (تحلیل‌گر برتر)")
        
    return badges

# ---------------- Load Data ----------------
default_habits = {
    "نماز / عبادات": 40,
    "ورزش": 30,
    "مطالعه": 30
}
habits_data = load_json(HABITS_FILE, default_habits)

if isinstance(habits_data, list):
    equal_weight = round(100 / len(habits_data)) if habits_data else 100
    habits_data = {h: equal_weight for h in habits_data}

records = load_json(RECORDS_FILE, {})
goals = load_json(GOALS_FILE, [])
notes = load_json(NOTES_FILE, {})

# ---------------- UI Setup ----------------
st.set_page_config(page_title="MyGrowth Ultra", page_icon="💖", layout="wide")

st.title("💖 MyGrowth")
st.caption("پلنر شخصی هوشمند برای برنامه‌ریزی، ثبت درصدی عادت‌ها و رشد واقعی")

# ---------------- Tabs Layout ----------------
tabs = st.tabs([
    "📊 داشبورد",
    "📅 برنامه امروز",
    "⚡ عادت‌ها و وزن‌ها",
    "🏆 دستاوردها",
    "🎯 اهداف",
    "📈 رشد من",
    "📝 یادداشت روزانه",
    "⚙️ تنظیمات و خروجی"
])

# ---------------- Tab 1: Dashboard ----------------
with tabs[0]:
    st.subheader("داشبورد و آمار کلی")
    current_streak = calculate_streak(records)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("کل ثبت‌ها", len(records))
    avg_p = sum(r["percent"] for r in records.values()) / len(records) if records else 0
    c2.metric("میانگین عملکرد", f"{avg_p:.1f}%")
    c3.metric("عادت‌های فعال", len(habits_data))
    c4.metric("تسلسل ثبت (Streak) 🔥", f"{current_streak} روز")
    
    st.markdown("---")
    if records:
        latest_k = sorted(records.keys())[-1]
        st.write(f"**آخرین ثبت ({latest_k}):** {records[latest_k]['percent']}%")

# ---------------- Tab 2: Today (Percentage Sliders) ----------------
with tabs[1]:
    st.subheader("برنامه امروز")
    today_str = str(date.today())
    st.write(f"📅 **تاریخ امروز:** {today_str}")
    
    if not habits_data:
        st.warning("هنوز عادتی ثبت نکرده‌اید. از تب 'عادت‌ها' اضافه کنید.")
    else:
        st.write("درصد انجام هر عادت را مشخص کنید:")
        
        total_weighted_score = 0
        total_possible_weight = sum(habits_data.values())
        
        for h, weight in habits_data.items():
            st.markdown(f"**{h}** (سهم کل: {weight}٪)")
            # اسلایدر درصد انجام از ۰ تا ۱۰۰
            completion_pct = st.slider(
                f"میزان انجام {h}",
                min_value=0,
                max_value=100,
                value=0,
                step=5,
                key=f"slider_{today_str}_{h}",
                label_visibility="collapsed"
            )
            # محاسبه سهم این درصد در کل عملکرد
            weighted_val = (completion_pct / 100) * weight
            total_weighted_score += weighted_val
            st.caption(f"امتیاز کسب‌شده: {weighted_val:.1f}٪ از {weight}٪")
            st.markdown("---")
        
        calc_pct = int((total_weighted_score / total_possible_weight) * 100) if total_possible_weight > 0 else 0
        
        st.progress(calc_pct / 100)
        st.subheader(f"مجموع کل عملکرد امروز: **{calc_pct}%**")
        
        if st.button("ذخیره عملکرد امروز"):
            records[today_str] = {"percent": calc_pct}
            save_json(RECORDS_FILE, records)
            st.success("عملکرد امروز با موفقیت ذخیره شد!")
            st.rerun()

# ---------------- Tab 3: Habits ----------------
with tabs[2]:
    st.subheader("مدیریت عادت‌ها و تعیین وزن (درصد ارزش)")
    
    col_a, col_b = st.columns([3, 2])
    with col_a:
        new_h = st.text_input("نام عادت جدید:")
    with col_b:
        new_w = st.number_input("ارزش/وزن عادت در کل روز (درصد):", min_value=5, max_value=100, value=20, step=5)
        
    if st.button("افزودن عادت"):
        if new_h and new_h not in habits_data:
            habits_data[new_h] = new_w
            save_json(HABITS_FILE, habits_data)
            st.success(f"عادت '{new_h}' با وزن {new_w}٪ اضافه شد.")
            st.rerun()
            
    st.markdown("---")
    st.write("📋 **فهرست عادت‌های فعلی:**")
    total_w = sum(habits_data.values())
    st.info(f"مجموع سهم وزن عادت‌ها: **{total_w}%** (پیشنهاد می‌شود مجموع ۱۰۰٪ باشد)")
    
    for h, w in list(habits_data.items()):
        col1, col2, col3 = st.columns([3, 2, 1])
        col1.write(f"• **{h}**")
        col2.write(f"وزن: {w}٪")
        if col3.button("حذف", key=f"del_{h}"):
            del habits_data[h]
            save_json(HABITS_FILE, habits_data)
            st.rerun()

# ---------------- Tab 4: Badges ----------------
with tabs[3]:
    st.subheader("🏆 مدال‌ها و دستاوردهای شما")
    user_badges = get_badges(records, calculate_streak(records))
    if user_badges:
        for b in user_badges:
            st.success(f"### {b}")
    else:
        st.info("هنوز نشان جدیدی باز نکرده‌اید. با ادامه ثبت عملکرد و افزایش Streak مدال‌ها باز می‌شوند!")

# ---------------- Tab 5: Goals ----------------
with tabs[4]:
    st.subheader("اهداف شخصی")
    g_text = st.text_input("هدف جدید:")
    if st.button("افزودن هدف"):
        if g_text:
            goals.append({"text": g_text, "done": False})
            save_json(GOALS_FILE, goals)
            st.rerun()
            
    st.markdown("---")
    for i, g in enumerate(goals):
        chk = st.checkbox(g["text"], value=g["done"], key=f"goal_{i}")
        if chk != g["done"]:
            goals[i]["done"] = chk
            save_json(GOALS_FILE, goals)

# ---------------- Tab 6: Growth ----------------
with tabs[5]:
    st.subheader("رشد و نمودار پیشرفت")
    keys = sorted(records.keys())
    if keys:
        period = st.selectbox("بازه زمانی نمایش", ["7", "14", "30", "All"])
        n = len(keys) if period == "All" else int(period)
        ck = keys[-n:]
        vals = [records[k]["percent"] for k in ck]

        fig = go.Figure(go.Scatter(
            x=[k[5:] for k in ck],
            y=vals,
            mode="lines+markers+text",
            text=[f"{v:g}%" for v in vals],
            textposition="top center",
            line=dict(width=3, color="#FF4B4B"),
            marker=dict(size=9)
        ))
        fig.add_hline(y=75, line_dash="dash", annotation_text="هدف (75%)", line_color="green")
        fig.update_layout(
            yaxis=dict(range=[0, 105]),
            height=450,
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
                "تاریخ": k,
                "عملکرد": f"{v:g}%",
                "تغییر": diff,
                "وضعیت": status(v)
            })
        st.dataframe(pd.DataFrame(history), use_container_width=True, hide_index=True)
    else:
        st.info("هنوز داده‌ای برای نمایش وجود ندارد.")

# ---------------- Tab 7: Notes ----------------
with tabs[6]:
    st.subheader("یادداشت روزانه")
    note_in = st.text_area("یادداشت و خاطره امروز:")
    if st.button("ذخیره یادداشت"):
        notes[str(date.today())] = note_in
        save_json(NOTES_FILE, notes)
        st.success("یادداشت ذخیره شد.")

# ---------------- Tab 8: Settings & Export ----------------
with tabs[7]:
    st.subheader("تنظیمات و دانلود گزارش‌ها")
    st.write("📥 **خروجی داده‌های پیشرفت:**")
    
    if records:
        df_export = pd.DataFrame([
            {"تاریخ": k, "عملکرد (درصد)": v["percent"], "وضعیت": status(v["percent"])}
            for k, v in records.items()
        ])
        
        csv_data = df_export.to_csv(index=False, encoding='utf-8-sig')
            
        st.download_button(
            label="📊 دانلود فایل CSV (قابل باز شدن در Excel)",
            data=csv_data,
            file_name=f"MyGrowth_Report_{date.today()}.csv",
            mime="text/csv"
        )
    else:
        st.info("داده‌ای برای خروجی وجود ندارد.")
        
