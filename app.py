from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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

# استایل‌دهی سفارشی
st.markdown(
    """
    <style>
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 14px 18px;
        border-right: 5px solid #6366f1;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    div[data-testid="stMetricLabel"] {
        font-weight: bold;
        color: #64748b;
    }
    div[data-testid="stMetricValue"] {
        color: #1e1b4b;
        font-weight: bold;
    }
    </style>
""",
    unsafe_allow_html=True,
)


def create_gauge_chart(percent, title_text="میزان رشد امروز"):
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=percent,
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": title_text, "font": {"size": 18, "color": "#1e1b4b"}},
            number={"suffix": "%", "font": {"size": 26, "color": "#4f46e5"}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1},
                "bar": {"color": "#6366f1"},
                "bgcolor": "#f1f5f9",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 50], "color": "#fee2e2"},
                    {"range": [50, 75], "color": "#fef3c7"},
                    {"range": [75, 100], "color": "#dcfce7"},
                ],
            },
        )
    )
    fig.update_layout(height=220, margin=dict(l=20, r=20, t=30, b=20))
    return fig


def get_performance_color(score):
    """تعیین رنگ داینامیک بر اساس درصد عملکرد"""
    if score >= 80:
        return "#22c55e"  # سبز قوی
    elif score >= 60:
        return "#84cc16"  # سبز روشن
    elif score >= 45:
        return "#f59e0b"  # زرد / نارنجی
    else:
        return "#ef4444"  # سرخ ضعیف


def create_thin_bar_chart(df, title="📈 روند رشد روزانه"):
    """ساخت نمودار میله‌ای بسیار باریک (شبیه به خط) و متراکم کنار هم"""
    colors = [get_performance_color(p) for p in df["Performance (%)"]]

    fig = go.Figure(
        data=[
            go.Bar(
                x=df["X_Label"],
                y=df["Performance (%)"],
                marker_color=colors,
                width=0.25,  # بسیار باریک مثل خط
                text=df["Performance (%)"].astype(str) + "%",
                textposition="outside",
                hovertemplate="<b>%{x}</b><br>عملکرد: %{y}%<extra></extra>",
            )
        ]
    )

    fig.update_layout(
        title={"text": title, "font": {"size": 18, "color": "#1e1b4b"}},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        bargap=0.8,  # ایجاد فاصله و باریک کردن میله‌ها
        xaxis=dict(
            showgrid=False,
            tickfont=dict(color="#64748b", size=11),
            title="روزها",
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="#f1f5f9",
            range=[0, 115],
            tickfont=dict(color="#64748b"),
            title="فیصدی عملکرد",
        ),
        margin=dict(l=20, r=20, t=40, b=20),
        height=380,
    )
    return fig


if "temp_lang" not in st.session_state:
    st.session_state.temp_lang = "dari"

if "user" not in st.session_state:
    st.sidebar.title("🌐 Language / زبان")
    lang_map = {"دری (Dari)": "dari", "English": "en", "中文 (Chinese)": "zh"}
    selected_l = st.sidebar.selectbox(
        "Select / انتخاب کنید", list(lang_map.keys()), index=0
    )
    st.session_state.temp_lang = lang_map.get(selected_l, "dari")

    t = TRANSLATIONS.get(st.session_state.temp_lang, TRANSLATIONS["dari"])

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
                    st.rerun()
                else:
                    st.error("نام کاربری یا رمز عبور اشتباه است!")

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

    menu_keys = [
        ("dashboard", t["dashboard"]),
        ("daily_record", t["daily_record"]),
        ("habits", t["habits"]),
        ("tasks", t["tasks"]),
        ("goals", t["goals"]),
        ("growth", t["growth"]),
        ("achievements", t["achievements"]),
        ("smart_analysis", t["smart_analysis"]),
        ("journal", t["journal"]),
        ("sleep", t["sleep"]),
        ("settings", t["settings"]),
    ]

    menu_display_to_key = {v: k for k, v in menu_keys}
    page_display = st.sidebar.radio(
        "Menu", [v for k, v in menu_keys], key="nav_menu"
    )
    page_key = menu_display_to_key.get(page_display, "dashboard")

    if st.sidebar.button(t["logout"]):
        st.session_state.user = None
        st.rerun()

    # 1. Dashboard Page
    if page_key == "dashboard":
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

        st.divider()
        st.plotly_chart(
            create_gauge_chart(today_score, t["today_perf"]),
            use_container_width=True,
        )

    # 2. Daily Record Page
    elif page_key == "daily_record":
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
                f"{h[1]} ({h[3]}%)",
                0,
                100,
                int(init_val),
                key=f"h_{h[0]}_{d_str}",
            )
            details[h[1]] = val
            total_score += (val * h[3]) / tot_weight
        avg_score = round(total_score, 1)

        c1, c2 = st.columns(2)
        c1.metric(t["today_perf"], f"{avg_score}%")
        c2.metric(t["status"], get_status_info(avg_score, curr_lang))

        st.plotly_chart(
            create_gauge_chart(avg_score, t["today_perf"]),
            use_container_width=True,
        )

        if st.button(t["save"]):
            save_record(uid, d_str, avg_score, details)
            st.success("ثبت گردید!")

    # 3. Habits Page
    elif page_key == "habits":
        st.header(t["habits"])
        habits = get_habits(uid)
        if habits:
            df_h = pd.DataFrame(
                habits,
                columns=["ID", "Name", "Category", "Weight (%)", "Active"],
            )
            st.dataframe(
                df_h[["Name", "Category", "Weight (%)"]],
                use_container_width=True,
            )
        h_name = st.text_input("Name")
        h_cat = st.selectbox(
            "Category", ["Health", "Learning", "Skill", "General"]
        )
        h_weight = st.number_input("Weight (%)", 1, 100, 20)
        if st.button("Add"):
            if add_habit(uid, h_name, h_cat, h_weight):
                st.success("عادت اضافه شد.")
                st.rerun()

    # 4. Tasks Page
    elif page_key == "tasks":
        st.header(t["tasks"])
        t_date = st.date_input("Date", date.today())
        tasks = get_tasks(uid, t_date)
        if tasks:
            for task in tasks:
                chk = st.checkbox(
                    f"{task[1]} ({task[2]})",
                    value=bool(task[3]),
                    key=f"t_{task[0]}",
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

    # 5. Goals Page
    elif page_key == "goals":
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
        g_cat = st.selectbox(
            "Category", ["Work", "Study", "Finance", "Personal"]
        )
        if st.button("Add Goal"):
            if g_title:
                add_goal(uid, g_title, g_desc, g_dl, g_cat)
                st.rerun()

    # 6. Growth Page (نمودار میله‌ای باریک)
    elif page_key == "growth":
        st.header(t["growth"])
        records = get_records(uid)
        if records:
            data = []
            sorted_dates = sorted(records.keys())
            for idx, d_str in enumerate(sorted_dates, 1):
                p = records[d_str]["percent"]
                day_label = f"روز {idx}"
                data.append(
                    {
                        "X_Label": day_label,
                        "Date": d_str,
                        "Performance (%)": p,
                        "Status": get_status_info(p, curr_lang),
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

            # فراخوانی نمودار میله‌ای باریک (خطی)
            fig = create_thin_bar_chart(df)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("هیچ داده‌ای موجود نیست.")

    # 7. Achievements Page
    elif page_key == "achievements":
        st.header(t["achievements"])
        records = get_records(uid)
        streak = calculate_streak(records)
        scores = [v["percent"] for v in records.values()] if records else []
        avg_score = sum(scores) / len(scores) if scores else 0

        a1, a2, a3 = st.columns(3)
        with a1:
            if streak >= 1:
                st.success("🥉 **شروع مسیر**\n\nاولین روز ثبت موفقانه انجام شد!")
            else:
                st.info("🔒 **شروع مسیر**\n\nبرای باز کردن، ۱ روز ثبت کنید.")

        with a2:
            if streak >= 7:
                st.success("🥈 **مداوم و منظم**\n\n۷ روز ثبت مداوم!")
            else:
                st.info("🔒 **مداوم و منظم**\n\nنیازمند ۷ روز ثبت مداوم.")

        with a3:
            if avg_score >= 80 and len(scores) >= 3:
                st.success("🥇 **قهرمان رشد**\n\nکسب میانگین عملکرد بالای ۸۰٪!")
            else:
                st.info("🔒 **قهرمان رشد**\n\nنیازمند میانگین عملکرد بالای ۸۰٪.")

    # 8. Smart Analysis Page (ژورنال و تحلیل هوشمند)
    elif page_key == "smart_analysis":
        st.header("🧠 ژورنال و تحلیل هوشمند عملکرد")
        records = get_records(uid)

        if records:
            scores = [v["percent"] for v in records.values()]
            avg_all = round(sum(scores) / len(scores), 1)

            max_date = max(records, key=lambda k: records[k]["percent"])
            min_date = min(records, key=lambda k: records[k]["percent"])
            max_score = records[max_date]["percent"]
            min_score = records[min_date]["percent"]

            c1, c2, c3 = st.columns(3)
            c1.metric("📊 میانگین کل عملکرد", f"{avg_all}%")
            c2.metric("🌟 بهترین روز", f"{max_score}%", f"تاریخ: {max_date}")
            c3.metric(
                "⚠️ ضعیف‌ترین روز",
                f"{min_score}%",
                f"تاریخ: {min_date}",
                delta_color="inverse",
            )

            st.divider()

            st.subheader("📖 گزارش ژورنال هوشمند")

            if avg_all >= 80:
                st.success(
                    f"🟢 **وضعیت: عالی**\n\nمیانگین عملکرد شما **{avg_all}%**"
                    f" است. بهترین روز شما تاریخ **{max_date}** با امتیاز"
                    f" **{max_score}%** ثبت شده است. روند انضباطی شما بسار قوی"
                    " است!"
                )
            elif avg_all >= 60:
                st.warning(
                    f"🟡 **وضعیت: متوسط و رو به رشد**\n\nمیانگین شما"
                    f" **{avg_all}%** است. کمترین عملکرد مربوط به تاریخ"
                    f" **{min_date}** با امتیاز **{min_score}%** بوده است. با"
                    " تمرکز روی عادات روزانه می‌توانید عملکرد را به بالای ۸۰٪"
                    " برسانید."
                )
            else:
                st.error(
                    f"🔴 **وضعیت: نیازمند توجه**\n\nمیانگین عملکرد **{avg_all}%**"
                    " است. پیشنهاد می‌شود اهداف روزانه را سبک‌تر کنید تا ثبات"
                    " بیشتری ایجاد شود."
                )

            st.subheader("💡 راهکارهای پیشنهادی")
            col_a, col_b = st.columns(2)
            with col_a:
                st.info(
                    "**نقاط قوت:**\n* تداوم در ثبت اطلاعات\n* آگاهی از روند رشد"
                )
            with col_b:
                st.info(
                    "**اقدام بعدی:**\n* تمرکز روی عادات اصلی با وزن بالا\n*"
                    " تنظیم منظم ساعات خواب"
                )
        else:
            st.info(
                "هنوز داده‌ای ثبت نشده است. پس از ثبت داده‌ها در Daily Record،"
                " تحلیل هوشمند فعال می‌شود."
            )

    # 9. Journal Page (صفحه یادداشت روزانه)
    elif page_key == "journal":
        st.header("📝 ژورنال و یادداشت‌های روزانه")
        j_date = st.date_input("تاریخ یادداشت", date.today())
        curr_j = get_journal(uid, j_date)
        mood_options = [
            "😃 عالی",
            "🙂 خوب",
            "😐 معمولی",
            "😔 بی انگیزه",
            "😡 خسته/عصبانی",
        ]
        saved_mood = curr_j[0] if curr_j else "😐 معمولی"
        m_index = 2
        for idx, m_opt in enumerate(mood_options):
            if saved_mood in m_opt:
                m_index = idx
                break

        mood = st.selectbox("حالت روحی امروز (Mood)", mood_options, index=m_index)
        note = st.text_area(
            "یادداشت و احساسات امروز",
            value=curr_j[1] if curr_j else "",
            height=150,
        )
        if st.button("ذخیره ژورنال"):
            save_journal(uid, j_date, mood.split()[0], note)
            st.success("یادداشت ژورنال با موفقیت ذخیره گردید!")

    # 10. Sleep Tracker Page
    elif page_key == "sleep":
        st.header(t["sleep"])
        s_date = st.date_input("Date", date.today())
        curr_s = get_sleep(uid, s_date)
        hours = st.number_input(
            "Hours", 0.0, 24.0, curr_s[0] if curr_s else 7.0, step=0.5
        )
        quality = st.slider("Quality (1-10)", 1, 10, curr_s[1] if curr_s else 7)
        if st.button(t["save"]):
            save_sleep(uid, s_date, hours, quality)
            st.success("اطلاعات خواب ثبت شد!")

    # 11. Settings Page
    elif page_key == "settings":
        st.header(t["settings"])
        st.write(f"**Username:** {user['username']}")
        st.write(f"**Email:** {user['email']}")
        st.write(f"**Language:** {curr_lang.upper()}")
        
