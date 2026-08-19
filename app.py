from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st
from logic import (
    TRANSLATIONS,
    add_goal,
    add_habit,
    add_task,
    authenticate,
    calculate_streak,
    create_user,
    ensure_user_habits,
    get_goals,
    get_habits,
    get_journal,
    get_records,
    get_sleep,
    get_status_info,
    get_tasks,
    save_journal,
    save_record,
    save_sleep,
    toggle_task,
    update_goal_progress,
    update_user_lang,
)

st.set_page_config(page_title="MyGrowth Pro", page_icon="🚀", layout="wide")

if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    st.title("🚀 سیستم مدیریت رشد شخصی | Growth System")
    tab_login, tab_reg = st.tabs(["ورود | Login", "ثبت‌نام | Register"])

    with tab_login:
        u = st.text_input("نام کاربری / Username", key="l_u")
        p = st.text_input("رمز عبور / Password", type="password", key="l_p")
        if st.button("ورود / Login"):
            if u and p:
                usr = authenticate(u, p)
                if usr:
                    st.session_state.user = usr
                    ensure_user_habits(usr["id"])
                    st.success("ورود موفقیت‌آمیز بود!")
                    st.rerun()
                else:
                    st.error("نام کاربری یا رمز عبور اشتباه است.")

    with tab_reg:
        ru = st.text_input("نام کاربری جدید / Username", key="r_u")
        re = st.text_input("ایمیل / Email", key="r_e")
        rp = st.text_input("رمز عبور جدید / Password", type="password", key="r_p")
        if st.button("ثبت‌نام / Register"):
            success, message = create_user(ru, re, rp)
            if success:
                st.success(message)
            else:
                st.error(message)

else:
    user = st.session_state.user
    uid = user["id"]
    curr_lang = user.get("language", "dari")
    if curr_lang not in ["dari", "en"]:
        curr_lang = "dari"
    t = TRANSLATIONS[curr_lang]

    st.sidebar.title(f"👤 {user['username']}")
    lang_choice = st.sidebar.selectbox(
        t["lang_select"],
        ["دری (Dari)", "English"],
        index=0 if curr_lang == "dari" else 1,
    )
    selected_lang_code = "dari" if "دری" in lang_choice else "en"
    if selected_lang_code != curr_lang:
        update_user_lang(uid, selected_lang_code)
        st.session_state.user["language"] = selected_lang_code
        st.rerun()

    menu = [
        t["dashboard"],
        t["daily_record"],
        t["habits"],
        t["tasks"],
        t["goals"],
        t["growth"],
        t["achievements"],
        t["smart_analysis"],
        t["journal"],
        t["sleep"],
        t["settings"],
    ]
    page = st.sidebar.radio("منو / Menu", menu)

    if st.sidebar.button(t["logout"]):
        st.session_state.user = None
        st.rerun()

    if page == t["dashboard"]:
        st.header(t["dashboard"])
        records = get_records(uid)
        streak = calculate_streak(records)
        today_score, month_score = 0, 0
        status_label = get_status_info(0, curr_lang)
        if records:
            today_str = str(date.today())
            today_score = (
                records[today_str]["percent"]
                if today_str in records
                else list(records.values())[-1]["percent"]
            )
            status_label = get_status_info(today_score, curr_lang)
            recent_30 = [v["percent"] for v in list(records.values())[-30:]]
            month_score = round(sum(recent_30) / len(recent_30), 1)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(t["streak"], f"🔥 {streak}")
        c2.metric(t["today_perf"], f"{today_score}%")
        c3.metric(t["avg_30"], f"{month_score}%")
        c4.metric(t["status"], status_label)

    elif page == t["daily_record"]:
        st.header(t["daily_record"])
        sel_date = st.date_input("Date / تاریخ", date.today())
        d_str = str(sel_date)
        habits = get_habits(uid)
        tot_weight = sum([h[3] for h in habits]) or 1
        existing_record = get_records(uid).get(d_str, {}).get("details", {})
        details, total_score = {}, 0
        for h in habits:
            init_val = existing_record.get(h[1], 0)
            val = st.slider(
                f"{h[1]} ({h[3]}%)", 0, 100, int(init_val), key=f"h_{h[0]}_{d_str}"
            )
            details[h[1]] = val
            total_score += (val * h[3]) / tot_weight
        avg_score = round(total_score, 1)
        c1, c2 = st.columns(2)
        c1.metric(t["today_perf"], f"{avg_score}%")
        c2.metric(t["status"], get_status_info(avg_score, curr_lang))
        if st.button(t["save"]):
            save_record(uid, d_str, avg_score, details)
            st.success("ذخیره شد!")

    elif page == t["habits"]:
        st.header(t["habits"])
        habits = get_habits(uid)
        if habits:
            df_h = pd.DataFrame(
                habits, columns=["ID", "Name", "Category", "Weight (%)", "Active"]
            )
            st.dataframe(
                df_h[["Name", "Category", "Weight (%)"]], use_container_width=True
            )
        st.subheader("افزودن عادت")
        h_name = st.text_input("نام عادت")
        h_cat = st.selectbox(
            "دسته‌بندی", ["سلامت", "یادگیری", "مهارت", "عمومی"]
        )
        h_weight = st.number_input("وزن (%)", 1, 100, 20)
        if st.button("افزودن"):
            if add_habit(uid, h_name, h_cat, h_weight):
                st.success("عادت اضافه شد.")
                st.rerun()

    elif page == t["tasks"]:
        st.header(t["tasks"])
        t_date = st.date_input("تاریخ", date.today())
        tasks = get_tasks(uid, t_date)
        st.subheader(f"📋 کارهای تاریخ {t_date}:")
        if tasks:
            for task in tasks:
                chk = st.checkbox(
                    f"{task[1]} ({task[2]})", value=bool(task[3]), key=f"t_{task[0]}"
                )
                if chk != bool(task[3]):
                    toggle_task(task[0], chk)
                    st.rerun()
        else:
            st.info("هیچ کاری ثبت نشده است.")
        st.subheader("افزودن کار جدید")
        t_title = st.text_input("عنوان کار")
        t_prio = st.selectbox("اولویت", ["High", "Medium", "Low"])
        if st.button("ثبت کار"):
            if t_title:
                add_task(uid, t_date, t_title, t_prio)
                st.success("کار اضافه شد.")
                st.rerun()

    elif page == t["goals"]:
        st.header(t["goals"])
        goals = get_goals(uid)
        if goals:
            for g in goals:
                st.subheader(f"{g[1]} ({g[5]})")
                st.write(f"توضیحات: {g[2]} | مهلت: {g[3]}")
                prog = st.slider("درصد پیشرفت", 0, 100, g[4], key=f"g_{g[0]}")
                if prog != g[4]:
                    update_goal_progress(g[0], prog)
                st.divider()
        else:
            st.info("هیچ هدفی ثبت نشده است.")
        st.subheader("ایجاد هدف جدید")
        g_title = st.text_input("عنوان هدف")
        g_desc = st.text_area("توضیحات")
        g_dl = st.date_input("مهلت زمانی", date.today() + timedelta(days=30))
        g_cat = st.selectbox(
            "دسته‌بندی", ["شغلی", "تحصیلی", "مالی", "شخصی"]
        )
        if st.button("ثبت هدف"):
            if g_title:
                add_goal(uid, g_title, g_desc, g_dl, g_cat)
                st.success("هدف ایجاد شد.")
                st.rerun()

    elif page == t["growth"]:
        st.header(t["growth"])
        records = get_records(uid)
        if records:
            data = [
                {
                    "Date": d_str,
                    "Performance (%)": v["percent"],
                    "Status": get_status_info(v["percent"], curr_lang),
                }
                for d_str, v in records.items()
            ]
            df = pd.DataFrame(data)
            st.dataframe(
                df.sort_values(by="Date", ascending=False),
                use_container_width=True,
                hide_index=True,
            )
            fig = px.line(
                df,
                x="Date",
                y="Performance (%)",
                hover_data=["Status"],
                markers=True,
                title="نمودار روند رشد",
            )
            fig.update_xaxes(type="category")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("هنوز داده‌ای ثبت نشده است.")

    elif page == t["achievements"]:
        st.header(t["achievements"])
        records = get_records(uid)
        streak = calculate_streak(records)
        st.write(
            f"**مدال اولین ثبت:** {'✅' if len(records) >= 1 else '❌'} (حداقل ۱"
            " روز ثبت)"
        )
        st.write(
            f"**تداوم ۷ روزه:** {'✅' if streak >= 7 else '❌'} (۷ روز پشت سر"
            " هم)"
        )
        st.write(
            f"**استاد ۳۰ روزه:** {'✅' if streak >= 30 else '❌'} (۳۰ روز پشت"
            " سر هم)"
        )

    elif page == t["smart_analysis"]:
        st.header(t["smart_analysis"])
        records = get_records(uid)
        if records:
            avg_all = round(
                sum([v["percent"] for v in records.values()]) / len(records), 1
            )
            overall_status = get_status_info(avg_all, curr_lang)
            st.info(
                f"📊 میانگین کل عملکرد شما: **{avg_all}%** | وضعیت کلی:"
                f" **{overall_status}**"
            )
            if avg_all >= 85:
                st.success("🎉 **عملکرد شما فوق‌العاده است!**")
            elif avg_all >= 70:
                st.success("👍 **وضعیت خوبی دارید.**")
            elif avg_all >= 50:
                st.warning("⚠️ **عملکرد شما متوسط است.**")
            else:
                st.error("🔴 **عملکرد نیاز به بهبود جدی دارد.**")
        else:
            st.info("داده‌ای برای تحلیل وجود ندارد.")

    elif page == t["journal"]:
        st.header(t["journal"])
        j_date = st.date_input("تاریخ", date.today())
        curr_j = get_journal(uid, j_date)
        mood_options = [
            "😃 عالی / Excellent",
            "🙂 خوب / Good",
            "😐 معمولی / Normal",
            "😔 غمگین / Sad",
            "😡 عصبانی / Angry",
        ]
        mood = st.selectbox(
            "حالت روحی / Mood",
            mood_options,
            index=0 if not curr_j else 0,
        )
        note = st.text_area("یادداشت روزانه / Note", value=curr_j[1] if curr_j else "")
        if st.button(t["save"]):
            save_journal(uid, j_date, mood, note)
            st.success("ژورنال با موفقیت ذخیره شد!")

    elif page == t["sleep"]:
        st.header(t["sleep"])
        s_date = st.date_input("تاریخ", date.today())
        curr_s = get_sleep(uid, s_date)
        hours = st.number_input(
            "ساعات خواب", 0.0, 24.0, curr_s[0] if curr_s else 7.0, step=0.5
        )
        quality = st.slider(
            "کیفیت خواب (۱ تا ۱۰)", 1, 10, curr_s[1] if curr_s else 7
        )
        if st.button(t["save"]):
            save_sleep(uid, s_date, hours, quality)
            st.success("اطلاعات خواب ذخیره شد!")

    elif page == t["settings"]:
        st.header(t["settings"])
        st.write(f"**نام کاربری:** {user['username']}")
        st.write(f"**ایمیل:** {user['email']}")
        st.write(f"**زبان فعال:** {curr_lang.upper()}")
