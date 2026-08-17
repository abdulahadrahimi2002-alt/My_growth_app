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

tab1, tab2, tab3 = st.tabs(["📝 ثبت عملکرد امروز", "💓 گراف ۳۰ روزه رشد", "⚙️ مدیریت فعالیت‌ها"])

with tab1:
    st.subheader("ثبت فعالیت‌های امروز")
    today = st.date_input("تاریخ", value=datetime.today())
    today_str = today.strftime("%Y-%m-%d")
    
    scores = {}
    for act in activities:
        scores[act] = st.slider(f"📌 {act}", 0, 100, 50, key=act)
    
    if st.button("💾 ثبت نهایی عملکرد امروز", use_container_width=True):
        avg = round(sum(scores.values()) / len(activities), 1) if activities else 0
        data[today_str] = {"total_acts": len(activities), "percent": avg}
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        st.success(f"عملکرد امروز ({today_str}) با موفقیت ثبت شد: {avg}%")

with tab2:
    st.subheader("💓 گراف ۳۰ روزه روند رشد و عملکرد (۰ تا ۱۰۰٪)")
    
    # ساخت لیست ۳۰ روزه
    days_labels = [f"روز {i}" for i in range(1, 31)]
    y_values = [None] * 30
    
    sorted_dates = sorted(data.keys())
    for idx, d in enumerate(sorted_dates):
        if idx < 30:
            y_values[idx] = data[d]["percent"]
            days_labels[idx] = f"روز {idx+1}<br>({d[-5:]})"

    # ساخت نمودار حرفه‌ای Plotly
    fig = go.Figure()

    # اضافه کردن خط و نقاط گراف
    fig.add_trace(go.Scatter(
        x=days_labels,
        y=y_values,
        mode='lines+markers+text',
        name='درصد رشد',
        line=dict(color='#00FF66', width=3),
        marker=dict(size=10, color='#00FF66', line=dict(width=2, color='white')),
        text=[f"{v}%" if v is not None else "" for v in y_values],
        textposition="top center",
        connectgaps=True
    ))

    # تنظیمات محورها و تم مشکی نوار قلب
    fig.update_layout(
        title="نمودار ضربانی رشد روزانه",
        xaxis=dict(title="روزهای ماه (۱ تا ۳۰)", tickangle=0),
        yaxis=dict(title="درصد رشد", range=[0, 105], dtick=20),
        paper_bgcolor="#0e1117",
        plot_bgcolor="#050d08",
        font=dict(color="#00FF66"),
        height=500,
        margin=dict(l=20, r=20, t=50, b=50)
    )

    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#0f2617')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#0f2617')

    st.plotly_chart(fig, use_container_width=True)

    if data:
        st.write("📋 **جدول جزئیات ثبت شده:**")
        df = pd.DataFrame([{"روز": f"روز {i+1} ({d[-5:]})", "درصد رشد": data[d]["percent"]} for i, d in enumerate(sorted_dates)])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("هنوز هیچ داده‌ای ثبت نشده است. از تب اول عملکرد امروز را ثبت کنید.")

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