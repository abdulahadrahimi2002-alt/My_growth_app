import streamlit as st
import pandas as pd
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
    st.subheader("💓 گراف ۳۰ روزه روند رشد")
    if data:
        sorted_dates = sorted(data.keys())
        chart_data = []
        for idx, d in enumerate(sorted_dates):
            chart_data.append({
                "روز": f"روز {idx+1} ({d[-5:]})",
                "درصد رشد": data[d]["percent"]
            })
        
        df = pd.DataFrame(chart_data)
        st.line_chart(df.set_index("روز"))
        st.write("📋 **جدول جزئیات ثبت شده:**")
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