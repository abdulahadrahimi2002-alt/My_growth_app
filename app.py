import streamlit as st
import json
import os
import hashlib
from datetime import date, timedelta
import pandas as pd
import plotly.graph_objects as go

# ============================================================
# MyGrowth Pro
# Personal Growth + Habits + Tasks + Goals + Journal
# ============================================================

st.set_page_config(
    page_title="MyGrowth Pro",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------- CSS ----------------
st.markdown("""
<style>
.main {
    direction: rtl;
    text-align: right;
}

.stButton > button {
    width: 100%;
    border-radius: 10px;
    font-weight: bold;
}

[data-testid="stMetric"] {
    border-radius: 12px;
    padding: 10px;
}

.block-container {
    padding-top: 2rem;
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# Configuration
# ============================================================

USER_DIR = "users_data"
os.makedirs(USER_DIR, exist_ok=True)

DEFAULT_HABITS = {
    "نماز / عبادات": 40,
    "ورزش": 30,
    "مطالعه": 30,
}


# ============================================================
# Translation
# ============================================================

TEXT = {
    "Dari": {
        "title": "🚀 MyGrowth Pro",
        "subtitle": "سیستم مدیریت رشد، عادت‌ها، اهداف و زندگی روزانه",
        "login": "ورود",
        "register": "ثبت‌نام",
        "username": "نام کاربری",
        "password": "رمز عبور",
        "confirm": "تکرار رمز عبور",
        "dashboard": "🏠 داشبورد",
        "today": "📅 ثبت روزانه",
        "habits": "🔁 عادت‌ها",
        "tasks": "📝 کارها",
        "goals": "🎯 اهداف",
        "calendar": "📅 تقویم",
        "charts": "📈 رشد من",
        "badges": "🏆 دستاوردها",
        "insights": "🧠 تحلیل هوشمند",
        "journal": "🙂 یادداشت و حس‌وحال",
        "settings": "⚙️ تنظیمات",
        "logout": "خروج",
        "save": "💾 ذخیره",
    },
    "English": {
        "title": "🚀 MyGrowth Pro",
        "subtitle": "Personal growth, habits, goals and daily life manager",
        "login": "Login",
        "register": "Register",
        "username": "Username",
        "password": "Password",
        "confirm": "Confirm password",
        "dashboard": "🏠 Dashboard",
        "today": "📅 Daily Entry",
        "habits": "🔁 Habits",
        "tasks": "📝 Tasks",
        "goals": "🎯 Goals",
        "calendar": "📅 Calendar",
        "charts": "📈 My Growth",
        "badges": "🏆 Achievements",
        "insights": "🧠 Smart Insights",
        "journal": "🙂 Journal & Mood",
        "settings": "⚙️ Settings",
        "logout": "Logout",
        "save": "💾 Save",
    },
}


# ============================================================
# Utility Functions
# ============================================================

def tr(key):
    lang = st.session_state.get("lang", "Dari")
    return TEXT.get(lang, TEXT["Dari"]).get(key, key)


def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def user_folder(username):
    folder_name = hash_password(username)[:20]
    path = os.path.join(USER_DIR, folder_name)
    os.makedirs(path, exist_ok=True)
    return path


def user_file(username, filename):
    return os.path.join(user_folder(username), filename)


def load_json(path, default):
    if not os.path.exists(path):
        return default

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )


def load_user(username, filename, default):
    return load_json(
        user_file(username, filename),
        default
    )


def save_user(username, filename, data):
    save_json(
        user_file(username, filename),
        data
    )


def calculate_streak(records):
    if not records:
        return 0

    available_dates = {
        date.fromisoformat(x)
        for x in records.keys()
    }

    check = date.today()

    if (
        check not in available_dates
        and check - timedelta(days=1) in available_dates
    ):
        check -= timedelta(days=1)

    streak = 0

    while check in available_dates:
        streak += 1
        check -= timedelta(days=1)

    return streak


def get_status(percent):
    if percent >= 85:
        return "🏆 عالی"
    if percent >= 70:
        return "✨ خوب"
    if percent >= 50:
        return "🟡 متوسط"
    if percent >= 30:
        return "🟠 نیاز به تلاش"

    return "🔴 ضعیف"


def get_badges(records):
    streak = calculate_streak(records)
    badges = []

    if streak >= 3:
        badges.append("🔥 ۳ روز تداوم")

    if streak >= 7:
        badges.append("⚡ یک هفته تداوم")

    if streak >= 30:
        badges.append("👑 ۳۰ روز تداوم")

    perfect_days = sum(
        1
        for record in records.values()
        if record.get("percent", 0) >= 100
    )

    if perfect_days >= 1:
        badges.append("🎯 اولین عملکرد ۱۰۰٪")

    if perfect_days >= 10:
        badges.append("🌟 ده روز عملکرد کامل")

    if len(records) >= 30:
        badges.append("📚 ثبت ۳۰ روز اطلاعات")

    return badges


# ============================================================
# Session
# ============================================================

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "username" not in st.session_state:
    st.session_state.username = ""

if "lang" not in st.session_state:
    st.session_state.lang = "Dari"


# ============================================================
# Language
# ============================================================

language = st.sidebar.radio(
    "🌐 Language / زبان",
    ["🇦🇫 دری", "🇬🇧 English"]
)

st.session_state.lang = (
    "Dari"
    if "دری" in language
    else "English"
)


# ============================================================
# Users Database
# ============================================================

users_file = os.path.join(
    USER_DIR,
    "users.json"
)

users = load_json(
    users_file,
    {}
)


# ============================================================
# Authentication
# ============================================================

if not st.session_state.authenticated:

    st.markdown(
        """
        <div style="
            text-align:center;
            padding:30px;
        ">
            <div style="font-size:60px;">🚀</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.title(tr("title"))
    st.caption(tr("subtitle"))

    auth_mode = st.radio(
        "Choose / انتخاب",
        [tr("login"), tr("register")],
        horizontal=True
    )

    username = st.text_input(
        tr("username")
    )

    password = st.text_input(
        tr("password"),
        type="password"
    )

    if auth_mode == tr("register"):

        confirm = st.text_input(
            tr("confirm"),
            type="password"
        )

        if st.button(
            tr("register"),
            type="primary"
        ):

            if not username.strip():
                st.warning("نام کاربری را وارد کنید.")

            elif len(password) < 6:
                st.warning(
                    "رمز عبور باید حداقل ۶ کاراکتر باشد."
                )

            elif password != confirm:
                st.warning(
                    "رمزهای عبور یکسان نیستند."
                )

            elif username in users:
                st.error(
                    "این نام کاربری قبلاً وجود دارد."
                )

            else:

                users[username] = hash_password(
                    password
                )

                save_json(
                    users_file,
                    users
                )

                # Create default user data
                save_user(
                    username,
                    "habits.json",
                    DEFAULT_HABITS
                )

                save_user(
                    username,
                    "records.json",
                    {}
                )

                save_user(
                    username,
                    "tasks.json",
                    []
                )

                save_user(
                    username,
                    "goals.json",
                    []
                )

                save_user(
                    username,
                    "journal.json",
                    {}
                )

                st.success(
                    "ثبت‌نام موفق شد. اکنون وارد شوید."
                )

    else:

        if st.button(
            tr("login"),
            type="primary"
        ):

            if (
                username in users
                and users[username]
                == hash_password(password)
            ):

                st.session_state.authenticated = True
                st.session_state.username = username

                st.rerun()

            else:

                st.error(
                    "نام کاربری یا رمز عبور اشتباه است."
                )

    st.stop()


# ============================================================
# User Data
# ============================================================

user = st.session_state.username

habits = load_user(
    user,
    "habits.json",
    DEFAULT_HABITS.copy()
)

records = load_user(
    user,
    "records.json",
    {}
)

tasks = load_user(
    user,
    "tasks.json",
    []
)

goals = load_user(
    user,
    "goals.json",
    []
)

journal = load_user(
    user,
    "journal.json",
    {}
)


# ============================================================
# Sidebar
# ============================================================

st.sidebar.markdown("---")
st.sidebar.markdown(
    f"### 👤 {user}"
)

if st.sidebar.button(
    tr("logout")
):

    st.session_state.authenticated = False
    st.session_state.username = ""

    st.rerun()


# ============================================================
# Main Header
# ============================================================

st.title(tr("title"))
st.caption(tr("subtitle"))


# ============================================================
# Navigation
# ============================================================

tabs = st.tabs([
    tr("dashboard"),
    tr("today"),
    tr("habits"),
    tr("tasks"),
    tr("goals"),
    tr("calendar"),
    tr("charts"),
    tr("badges"),
    tr("insights"),
    tr("journal"),
    tr("settings"),
])


today = str(date.today())


# ============================================================
# Dashboard
# ============================================================

with tabs[0]:

    st.subheader(tr("dashboard"))

    streak = calculate_streak(records)

    average = (
        sum(
            r.get("percent", 0)
            for r in records.values()
        )
        / len(records)
        if records
        else 0
    )

    best = max(
        [
            r.get("percent", 0)
            for r in records.values()
        ],
        default=0
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "📅 روزهای ثبت",
        len(records)
    )

    c2.metric(
        "📊 میانگین",
        f"{average:.1f}%"
    )

    c3.metric(
        "🔥 Streak",
        f"{streak} روز"
    )

    c4.metric(
        "🏆 بهترین",
        f"{best:.0f}%"
    )

    st.markdown("---")

    if today in records:

        current = records[today]["percent"]

        st.success(
            f"عملکرد امروز: **{current}%** — "
            f"{get_status(current)}"
        )

    else:

        st.info(
            "امروز هنوز عملکرد خود را ثبت نکرده‌اید."
        )

    if records:

        keys = sorted(records)

        recent = keys[-14:]

        values = [
            records[k]["percent"]
            for k in recent
        ]

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=recent,
                y=values,
                mode="lines+markers",
                line=dict(width=3),
                marker=dict(size=8)
            )
        )

        fig.add_hline(
            y=75,
            line_dash="dash",
            annotation_text="هدف 75%"
        )

        fig.update_layout(
            yaxis=dict(range=[0, 105]),
            height=350
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


# ============================================================
# Daily Entry
# ============================================================

with tabs[1]:

    st.subheader(tr("today"))

    st.write(
        f"📅 **تاریخ:** {today}"
    )

    if not habits:

        st.warning(
            "هنوز هیچ عادتی ندارید."
        )

    else:

        old_details = records.get(
            today,
            {}
        ).get(
            "details",
            {}
        )

        total_weight = sum(
            habits.values()
        )

        earned = 0
        scores = {}

        for habit, weight in habits.items():

            value = st.slider(
                f"{habit} — وزن {weight}٪",
                0,
                100,
                int(
                    old_details.get(
                        habit,
                        0
                    )
                ),
                5,
                key=f"daily_{habit}"
            )

            scores[habit] = value

            earned += (
                value / 100
            ) * weight

            st.caption(
                f"امتیاز این عادت: "
                f"{(value / 100) * weight:.1f}٪"
            )

        final_percent = (
            round(
                earned
                / total_weight
                * 100
            )
            if total_weight
            else 0
        )

        st.progress(
            final_percent / 100
        )

        st.subheader(
            f"💗 عملکرد امروز: **{final_percent}%**"
        )

        st.write(
            get_status(final_percent)
        )

        if st.button(
            tr("save"),
            type="primary",
            key="save_daily"
        ):

            records[today] = {
                "percent": final_percent,
                "details": scores
            }

            save_user(
                user,
                "records.json",
                records
            )

            st.success(
                "عملکرد امروز ذخیره شد."
            )

            st.rerun()


# ============================================================
# Habits
# ============================================================

with tabs[2]:

    st.subheader(tr("habits"))

    c1, c2 = st.columns([3, 2])

    with c1:

        new_habit = st.text_input(
            "نام عادت جدید"
        )

    with c2:

        new_weight = st.number_input(
            "وزن عادت",
            min_value=1,
            max_value=100,
            value=10,
            step=5
        )

    if st.button(
        "➕ افزودن عادت"
    ):

        if (
            new_habit.strip()
            and new_habit not in habits
        ):

            habits[new_habit] = new_weight

            save_user(
                user,
                "habits.json",
                habits
            )

            st.rerun()

    total = sum(
        habits.values()
    )

    if total == 100:

        st.success(
            "مجموع وزن‌ها دقیقاً ۱۰۰٪ است."
        )

    else:

        st.warning(
            f"مجموع وزن‌ها: {total}% — "
            f"بهتر است ۱۰۰٪ باشد."
        )

    for habit, weight in list(
        habits.items()
    ):

        c1, c2, c3 = st.columns(
            [4, 2, 1]
        )

        c1.write(
            f"**{habit}**"
        )

        c2.write(
            f"{weight}%"
        )

        if c3.button(
            "🗑️",
            key=f"delete_{habit}"
        ):

            del habits[habit]

            save_user(
                user,
                "habits.json",
                habits
            )

            st.rerun()


# ============================================================
# Tasks
# ============================================================

with tabs[3]:

    st.subheader(tr("tasks"))

    task_title = st.text_input(
        "کار جدید"
    )

    priority = st.selectbox(
        "اولویت",
        [
            "🔴 مهم و فوری",
            "🟡 مهم",
            "🔵 عادی"
        ]
    )

    if st.button(
        "➕ افزودن کار"
    ):

        if task_title.strip():

            tasks.append(
                {
                    "id": datetime.now().timestamp(),
                    "text": task_title,
                    "priority": priority,
                    "done": False,
                    "date": today
                }
            )

            save_user(
                user,
                "tasks.json",
                tasks
            )

            st.rerun()

    today_tasks = [
        t
        for t in tasks
        if t.get("date") == today
    ]

    done_count = 0

    for task in today_tasks:

        checked = st.checkbox(
            f"{task['priority']} — {task['text']}",
            value=task.get("done", False),
            key=f"task_{task['id']}"
        )

        if checked:

            done_count += 1

        if checked != task.get(
            "done",
            False
        ):

            task["done"] = checked

            save_user(
                user,
                "tasks.json",
                tasks
            )

    st.metric(
        "کارهای انجام‌شده",
        f"{done_count}/{len(today_tasks)}"
    )


# ============================================================
# Goals
# ============================================================

with tabs[4]:

    st.subheader(tr("goals"))

    goal_title = st.text_input(
        "عنوان هدف"
    )

    deadline = st.date_input(
        "مهلت هدف"
    )

    if st.button(
        "🎯 افزودن هدف"
    ):

        if goal_title.strip():

            goals.append(
                {
                    "title": goal_title,
                    "deadline": str(deadline),
                    "progress": 0,
                    "created": today
                }
            )

            save_user(
                user,
                "goals.json",
                goals
            )

            st.rerun()

    for index, goal in enumerate(
        goals
    ):

        st.markdown(
            f"### 🎯 {goal['title']}"
        )

        st.write(
            f"مهلت: {goal['deadline']}"
        )

        progress = st.slider(
            "پیشرفت",
            0,
            100,
            int(
                goal.get(
                    "progress",
                    0
                )
            ),
            key=f"goal_{index}"
        )

        st.progress(
            progress / 100
        )

        if progress != goal.get(
            "progress",
            0
        ):

            goal["progress"] = progress

            save_user(
                user,
                "goals.json",
                goals
            )

        if st.button(
            "🗑️ حذف هدف",
            key=f"delete_goal_{index}"
        ):

            goals.pop(index)

            save_user(
                user,
                "goals.json",
                goals
            )

            st.rerun()


# ============================================================
# Calendar
# ============================================================

with tabs[5]:

    st.subheader(tr("calendar"))

    if not records:

        st.info(
            "هنوز هیچ روزی ثبت نشده است."
        )

    else:

        rows = []

        for day, record in sorted(
            records.items
