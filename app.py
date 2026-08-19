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
    init_db,
    save_journal,
    save_record,
    save_sleep,
    toggle_task,
    update_goal_progress,
    update_user_lang,
)

init_db()

st.set_page_config(page_title="MyGrowth Pro", page_icon="🚀", layout="wide")

if "temp_lang" not in st.session_state:
    st.session_state.temp_lang = "dari"

if "user" not in st.session_state:
    st.sidebar.title("🌐 Language / زبان")
    lang_map = {"دری (Dari)": "dari", "English": "en", "中文 (Chinese)": "zh"}
    selected_l = st.sidebar.selectbox(
        "Select / انتخاب کنید", list(lang_map.keys()), index=0
    )
    st.session_state.temp_lang = lang_map[selected_l]

    t = TRANSLATIONS[st.session_state.temp_lang]

    st.title(t["title"])
    tab_login, tab_reg = st.tabs([t["login"], t["register"]])

    with tab_login:
        u = st.text_input(t["username"], key="l_u")
        p = st.text_input(t["password"], type="password", key="l_p")
        if st.button(t["login_btn"]):
            if u and p:
                usr = authenticate(u, p)
                if usr:
                    st.session_state.user = usr
                    ensure_user_habits(usr["id"])
                    st.success("OK")
                    st.rerun()
                else:
                    st.error("Error!")

    with tab_reg:
        ru = st.text_input(t["username"], key="r_u")
        re = st.text_input(t["email"], key="r_e")
        rp = st.text_input(t["password"], type="password", key="r_p")
        if st.button(t["reg_btn"]):
            success, message = create_user(
                ru, re, rp, st.session_state.temp_lang
            )
            if success:
                st.success(message)
            else:
                st.error(message)

else:
    user = st.session_state.user
    uid = user["id"]
    curr_lang = user.get("language", "dari")
    if curr_lang not in TRANSLATIONS:
        curr_lang = "dari"
    t = TRANSLATIONS[curr_lang]

    st.sidebar.title(f"👤 {user['username']}")
    lang_map_rev = {"dari": 0, "en": 1, "zh": 2}
    lang_choice = st.sidebar.selectbox(
        t["lang_select"],
        ["دری (Dari)", "English", "中文 (Chinese)"],
        index=lang_map_rev.get(curr_lang, 0),
    )
    selected_lang_code = "dari"
    if "English" in lang_choice:
        selected_lang_code = "en"
    elif "中文" in lang_choice:
        selected_lang_code = "zh"

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
    page = st.sidebar.radio("Menu", menu)

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
        sel_date = st.date_input("Date", date.today())
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
            st.success("OK")

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
        h_name = st.text_input("Name")
        h_cat = st.selectbox("Category", ["Health", "Learning", "Skill", "General"])
        h_weight = st.number_input("Weight (%)", 1, 100, 20)
        if st.button("Add"):
            if add_habit(uid, h_name, h_cat, h_weight):
                st.success("OK")
                st.rerun()

    elif page == t["tasks"]:
        st.header(t["tasks"])
        t_date = st.date_input("Date", date.today())
        tasks = get_tasks(uid, t_date)
        if tasks:
            for task in tasks:
                chk = st.checkbox(
                    f"{task[1]} ({task[2]})", value=bool(task[3]), key=f"t_{task[0]}"
                )
                if chk != bool(task[3]):
                    toggle_task(task[0], chk)
                    st.rerun()
        t_title = st.text_input("Title")
        t_prio = st.selectbox("Priority", ["High", "Medium", "Low"])
        if st.button("Add Task"):
            if t_title:
                add_task(uid, t_date, t_title, t_prio)
                st.rerun()

    elif page == t["goals"]:
        st.header(t["goals"])
        goals = get_goals(uid)
        if goals:
            for g in goals:
                st.subheader(f"{g[1]} ({g[5]})")
                prog = st.slider("Progress", 0, 100, g[4], key=f"g_{g[0]}")
                if prog != g[4]:
                    update_goal_progress(g[0], prog)
                st.divider()
        g_title = st.text_input("Goal Title")
        g_desc = st.text_area("Description")
        g_dl = st.date_input("Deadline", date.today() + timedelta(days=30))
        g_cat = st.selectbox("Category", ["Work", "Study", "Finance", "Personal"])
        if st.button("Add Goal"):
            if g_title:
                add_goal(uid, g_title, g_desc, g_dl, g_cat)
                st.rerun()

    elif page == t["growth"]:
        st.header(t["growth"])
        records = get_records(uid)
        if records:
            data = []
            for d_str, v in records.items():
                p = v["percent"]
                c = "#28a745" if p >= 70 else ("#ffc107" if p >= 50 else "#dc3545")
                data.append(
                    {
                        "Date": d_str,
                        "Performance (%)": p,
                        "Status": get_status_info(p, curr_lang),
                        "Color": c,
                    }
                )

            df = pd.DataFrame(data)

            st.dataframe(
                df.sort_values(by="Date", ascending=False)[
                    ["Date", "Performance (%)", "Status"]
                ],
                use_container_width=True,
                hide_index=True,
            )

            # گراف کامل با عرض کامل صفحه
            fig = px.line(
                df,
                x="Date",
                y="Performance (%)",
                text="Performance (%)",
                markers=True,
                title="Growth Trend",
            )
            fig.update_traces(
                textposition="top center",
                line=dict(width=3, color="#0068C9"),
                marker=dict(size=12, color=df["Color"].tolist()),
            )
            fig.update_xaxes(type="category")
            fig.update_yaxes(range=[0, 105])
            fig.update_layout(height=400, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available.")

    elif page == t["achievements"]:
        st.header(t["achievements"])
        records = get_records(uid)
        streak = calculate_streak(records)
        st.write(f"**Day 1:** {'✅' if len(records) >= 1 else '❌'}")
        st.write(f"**7 Days:** {'✅' if streak >= 7 else '❌'}")
        st.write(f"**30 Days:** {'✅' if streak >= 30 else '❌'}")

    elif page == t["smart_analysis"]:
        st.header(t["smart_analysis"])
        records = get_records(uid)
        if records:
            avg_all = round(
                sum([v["percent"] for v in records.values()]) / len(records), 1
            )
            st.info(f"Average: {avg_all}%")

    elif page == t["journal"]:
        st.header(t["journal"])
        j_date = st.date_input("Date", date.today())
        curr_j = get_journal(uid, j_date)
        mood_options = ["😃", "🙂", "😐", "😔", "😡"]
        mood = st.selectbox(
            "Mood",
            mood_options,
            index=0,
        )
        note = st.text_area("Note", value=curr_j[1] if curr_j else "")
        if st.button(t["save"]):
            save_journal(uid, j_date, mood, note)
            st.success("Saved!")

    elif page == t["sleep"]:
        st.header(t["sleep"])
        s_date = st.date_input("Date", date.today())
        curr_s = get_sleep(uid, s_date)
        hours = st.number_input(
            "Hours", 0.0, 24.0, curr_s[0] if curr_s else 7.0, step=0.5
        )
        quality = st.slider("Quality (1-10)", 1, 10, curr_s[1] if curr_s else 7)
        if st.button(t["save"]):
            save_sleep(uid, s_date, hours, quality)
            st.success("Saved!")

    elif page == t["settings"]:
        st.header(t["settings"])
        st.write(f"**Username:** {user['username']}")
        st.write(f"**Email:** {user['email']}")
        st.write(f"**Language:** {curr_lang.upper()}")
        
