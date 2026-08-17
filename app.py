import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
import os
from datetime import datetime

st.set_page_config(page_title="💓 برنامه مدیریت رشد روزانه", layout="centered")

st.markdown("<h2 style='text-align: center; color: #00FF66;'>💓 برنامه هوشمند مدیریت فعالیت‌ها و رشد روزانه</h2>", unsafe_allow_html=True)

DATA_FILE = "tracker_data.json"
ACT_FILE = "activities.json"

# بارگیری فعالیت‌ها
if os.path.exists(ACT_FILE):
    try:
        with open(ACT_FILE, "r", encoding="utf-8") as f:
            activities = json.load(f)
    except:
        activities = ["نماز پنج‌گانه", "تلاوت قرآن", "ورزش روزانه", "مطالعه انگلیسی", "مطالعه چینی", "کارهای شخصی"]
else:
    activities = ["نماز پنج‌گانه", "تلاوت قرآن", "ورزش روزانه", "مطالعه انگلیسی", "مطالعه چینی", "کارهای شخصی"]

# بارگیری داده‌ها
if os.path.exists(DATA_FILE):
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        data = {}
else:
    data = {}

# تابع تعیین وضعیت و رنگ بر اساس درصد
def get_status_and_color(val):
    if val >= 75:
        return "✨ عالی", "#00FF66"  # سبز فسفری درخشان
    elif val >= 50:
        return "🟢 خوب", "#33CC66"   # سبز
    elif val >= 30:
        return "🟠 بد", "#FF9900"    # نارنجی
    else:
        return "🔴 خیلی بد", "#FF3333" # قرمز پررنگ

tab1, tab2, tab3 = st.tabs(["📝 ثبت عملکرد امروز", "💓 گراف رشد و عملکرد", "⚙️ مدیریت فعالیت‌ها"])

with tab1:
    st.subheader("ثبت فعالیت‌های امروز")
    today = st.date_input("تاریخ ثبت", value=datetime.today())
    today_str = today.strftime("%Y-%m-%d")
    
    scores = {}
    for act in activities:
        scores[act] = st.slider(f"📌 {act}", 0, 100, 50, key=act)
    
    if st.button("💾 ثبت نهایی عملکرد امروز", use_container_width=True):
        avg = round(sum(scores.values()) / len(activities), 1) if activities else 0
        data[today_str] = {"total_acts": len(activities), "percent": avg}
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
        status_msg, _ = get_status_and_color(avg)
        st.success(f"عملکرد امروز ({today_str}) ثبت شد: {avg}% ({status_msg})")

with tab2:
    st.subheader("💓 گراف روند رشد بر اساس سطح عملکرد")
    st.caption("🔴 ۱۰-۳۰٪: خیلی بد | 🟠 ۳۰-۵۰٪: بد | 🟢 ۵۰-۷۵٪: خوب | ✨ ۷۵-۱۰۰٪: عالی")
    
    if data:
        sorted_dates = sorted(data.keys())
        total_days = len(sorted_dates)
        
        display_range = max(10, total_days + 2)
        days_labels = [f"روز {i+1}" for i in range(display_range)]
        y_values = [None] * display_range
        colors = []

        for idx, d in enumerate(sorted_dates):
            val = data[d]["percent"]
            y_values[idx] = val
            days_labels[idx] = f"روز {idx+1}<br>({d[-5:]})"
            _, color = get_status_and_color(val)
            colors.append(color)

        fig = go.Figure()

        # خط اصلی متصل‌کننده نقاط
        fig.add_trace(go.Scatter(
            x=days_labels[:total_days],
            y=y_values[:total_days],
            mode='lines+markers+text',
            name='روند عملکرد',
            line=dict(color='#888888', width=2),
            marker=dict(
                size=12,
                color=colors,
                line=dict(width=2, color='white')
            ),
            text=[f"{v}%" for v in y_values[:total_days]],
            textposition="top center"
        ))

        fig.update_layout(
            title="نمودار پیوسته و هوشمند عملکرد",
            xaxis=dict(title="روزهای استفاده", tickangle=0, type='category'),
            yaxis=dict(title="درصد رشد", range=[0, 110], dtick=20),
            paper_bgcolor="#0e1117",
            plot_bgcolor="#050d08",
            font=dict(color="#FFFFFF"),
            height=500,
            showlegend=False,
            margin=dict(l=20, r=20, t=50, b=50)
        )

        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#1e2621')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#1e2621')

        st.plotly_chart(fig, use_container_width=True)

        st.write("📋 **جدول کل جزئیات ثبت شده:**")
        df_list = []
        for i, d in enumerate(sorted_dates):
            val = data[d]["percent"]
            status_text, _ = get_status_and_color(val)
            df_list.append({"روز": f"روز {i+1} ({d})", "درصد رشد": f"{val}%", "وضعیت": status_text})
        
        df = pd.DataFrame(df_list)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("هنوز هیچ داده‌ای ثبت نشده است. اولین ثبت شما به عنوان «روز ۱» محاسبه خواهد شد.")

with tab3:
    st.subheader("افزودن فعالیت جدید")
    new_act = st.text_input("نام فعالیت جدید:")
    if st.button("افزودن به لیست"):
        if new_act and new_act not in activities:
            activities.append(new_act)
            with open(ACT_FILE, "w", encoding="utf-8") as f:
                json.dump(activities, f, ensure_ascii=False, indent=4)
            st.success(f"فعالیت '{new_act}' اضافه شد.")
            st.rerun()

    st.write("---")
    st.write("📋 **فعالیت‌های فعلی:**")
    for a in activities:
        st.write(f"- {a}")