import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
import os
from datetime import datetime, date

st.set_page_config(
    page_title="💓 برنامه مدیریت رشد روزانه",
    page_icon="💓",
    layout="centered"
)

st.markdown(
    """
    <style>
    .metric-card {
        background: #171a22;
        border: 1px solid #30343f;
        border-radius: 14px;
        padding: 14px 10px;
        text-align: center;
        margin-bottom: 8px;
    }
    .metric-title { color: #aeb4c0; font-size: 14px; }
    .metric-value { font-size: 26px; font-weight: 700; margin-top: 4px; }
    .positive { color: #00e676; }
    .negative { color: #ff5252; }
    .neutral { color: #ffd54f; }
    .small-note { color: #9aa0aa; font-size: 13px; }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    "<h2 style='text-align:center;'>💓 برنامه هوشمند مدیریت فعالیت‌ها و رشد روزانه</h2>",
    unsafe_allow_html=True
)

DATA_FILE = "tracker_data.json"
ACT_FILE = "activities.json"

DEFAULT_ACTIVITIES = [
    "نماز پنج‌گانه",
    "تلاوت قرآن",
    "ورزش روزانه",
    "مطالعه انگلیسی",
    "مطالعه چینی",
    "کارهای شخصی"
]

# -----------------------------
# Load activities
# -----------------------------
if os.path.exists(ACT_FILE):
    try:
        with open(ACT_FILE, "r", encoding="utf-8") as f:
            activities = json.load(f)
        if not isinstance(activities, list):
            activities = DEFAULT_ACTIVITIES.copy()
    except Exception:
        activities = DEFAULT_ACTIVITIES.copy()
else:
    activities = DEFAULT_ACTIVITIES.copy()

# -----------------------------
# Load historical data
# -----------------------------
if os.path.exists(DATA_FILE):
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            data = {}
    except Exception:
        data = {}
else:
    data = {}


def get_status_and_color(val):
    if val >= 75:
        return "✨ عالی", "#00E676"
    elif val >= 50:
        return "🟢 خوب", "#33CC66"
    elif val >= 30:
        return "🟠 نیاز به تلاش", "#FF9900"
    else:
        return "🔴 ضعیف", "#FF3333"


def get_change(current, previous):
    if previous is None:
        return None
    return round(current - previous, 1)


def get_streak(sorted_dates):
    """Count consecutive calendar days ending at the latest recorded date."""
    if not sorted_dates:
        return 0

    parsed = sorted(date.fromisoformat(d) for d in sorted_dates)
    streak = 1

    for i in range(len(parsed) - 1, 0, -1):
        if (parsed[i] - parsed[i - 1]).days == 1:
            streak += 1
        else:
            break

    return streak


def metric_card(title, value, css_class=""):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">{title}</div>
            <div class="metric-value {css_class}">{value}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


tab1, tab2, tab3 = st.tabs(
    ["📝 ثبت عملکرد امروز", "💓 گراف رشد و عملکرد", "⚙️ مدیریت فعالیت‌ها"]
)

# ============================================================
# TAB 1 — Daily entry
# ============================================================
with tab1:
    st.subheader("ثبت فعالیت‌های امروز")

    today = st.date_input(
        "تاریخ ثبت",
        value=datetime.today().date()
    )
    today_str = today.strftime("%Y-%m-%d")

    # If the date already has saved activity-level scores, use them.
    existing_scores = data.get(today_str, {}).get("activities", {})

    scores = {}
    for act in activities:
        default_value = int(existing_scores.get(act, 0))
        scores[act] = st.slider(
            f"📌 {act}",
            min_value=0,
            max_value=100,
            value=max(0, min(100, default_value)),
            step=5,
            key=f"score_{today_str}_{act}"
        )

    st.caption("💡 برای جلوگیری از ثبت تصادفی، مقدار اولیه فعالیت جدید ۰٪ است.")

    if st.button(
        "💾 ثبت نهایی عملکرد امروز",
        use_container_width=True,
        type="primary"
    ):
        avg = round(sum(scores.values()) / len(activities), 1) if activities else 0

        data[today_str] = {
            "total_acts": len(activities),
            "percent": avg,
            "activities": scores
        }

        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        status_msg, _ = get_status_and_color(avg)
        st.success(
            f"عملکرد {today_str} ثبت شد: {avg}% ({status_msg})"
        )
        st.rerun()

# ============================================================
# TAB 2 — Growth dashboard
# ============================================================
with tab2:
    st.subheader("💓 داشبورد رشد و عملکرد")
    st.caption(
        "🔴 ۰–۲۹٪ ضعیف | 🟠 ۳۰–۴۹٪ نیاز به تلاش | "
        "🟢 ۵۰–۷۴٪ خوب | ✨ ۷۵–۱۰۰٪ عالی"
    )

    if data:
        sorted_dates = sorted(data.keys())
        values = [
            float(data[d].get("percent", 0))
            for d in sorted_dates
        ]

        total_days = len(sorted_dates)
        today_key = datetime.today().strftime("%Y-%m-%d")

        # Latest recorded day, not necessarily today's calendar date.
        latest_value = values[-1]
        previous_value = values[-2] if total_days >= 2 else None
        change = get_change(latest_value, previous_value)

        week_values = values[-7:]
        week_avg = round(sum(week_values) / len(week_values), 1)

        best_value = max(values)
        streak = get_streak(sorted_dates)

        # ---- KPI cards ----
        c1, c2 = st.columns(2)
        with c1:
            metric_card("💗 آخرین عملکرد", f"{latest_value}%")
        with c2:
            if change is None:
                metric_card("📈 تغییر نسبت به قبل", "—", "neutral")
            elif change > 0:
                metric_card("📈 رشد نسبت به قبل", f"+{change}%", "positive")
            elif change < 0:
                metric_card("📉 افت نسبت به قبل", f"{change}%", "negative")
            else:
                metric_card("➡️ تغییر نسبت به قبل", "0%", "neutral")

        c3, c4 = st.columns(2)
        with c3:
            metric_card("📊 میانگین ۷ روز اخیر", f"{week_avg}%")
        with c4:
            metric_card("🔥 رکورد روزهای متوالی", f"{streak} روز")

        st.markdown("---")

        # ---- Human-friendly comparison ----
        if change is not None:
            if change > 0:
                st.success(
                    f"🚀 آفرین! آخرین عملکردت {change}% بهتر از روز قبل ثبت‌شده بود."
                )
            elif change < 0:
                st.warning(
                    f"💪 آخرین عملکردت {abs(change)}% کمتر از روز قبل ثبت‌شده بود. "
                    "یک روز ضعیف، به معنی شکست نیست."
                )
            else:
                st.info("➡️ عملکردت نسبت به روز قبل ثبت‌شده تغییری نکرده است.")
        else:
            st.info("برای مقایسه با روز قبل، حداقل دو روز باید ثبت شده باشد.")

        status_text, _ = get_status_and_color(latest_value)
        st.markdown(
            f"**وضعیت آخرین ثبت:** {status_text}  |  "
            f"**بهترین عملکرد:** {best_value}%"
        )

        # ---- Main chart ----
        labels = [
            f"{i + 1}<br>{d[5:]}"
            for i, d in enumerate(sorted_dates)
        ]

        point_colors = [
            get_status_and_color(v)[1]
            for v in values
        ]

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=labels,
                y=values,
                mode="lines+markers+text",
                name="روند عملکرد",
                line=dict(color="#B0B6C0", width=3),
                marker=dict(
                    size=11,
                    color=point_colors,
                    line=dict(width=2, color="white")
                ),
                text=[f"{v:g}%" for v in values],
                textposition="top center",
                hovertemplate="روز %{x}<br>عملکرد: %{y}%<extra></extra>"
            )
        )

        # 75% reference line
        fig.add_hline(
            y=75,
            line_dash="dash",
            line_width=1,
            annotation_text="هدف عالی: ۷۵٪",
            annotation_position="top left"
        )

        fig.update_layout(
            title="📈 روند عملکرد روزانه",
            xaxis=dict(
                title="روز",
                type="category",
                showgrid=False
            ),
            yaxis=dict(
                title="درصد عملکرد",
                range=[0, 105],
                dtick=20,
                showgrid=True,
                gridcolor="#30343f"
            ),
            paper_bgcolor="#0e1117",
            plot_bgcolor="#11151c",
            font=dict(color="#FFFFFF"),
            height=500,
            showlegend=False,
            margin=dict(l=20, r=20, t=60, b=50)
        )

        st.plotly_chart(fig, use_container_width=True)

        # ---- Activity-level latest snapshot ----
        latest_record = data[sorted_dates[-1]]
        latest_activities = latest_record.get("activities", {})

        if latest_activities:
            st.markdown("### 📌 عملکرد فعالیت‌ها در آخرین ثبت")

            activity_rows = []
            for act in activities:
                val = latest_activities.get(act, 0)
                status, _ = get_status_and_color(val)
                activity_rows.append({
                    "فعالیت": act,
                    "درصد": f"{val}%",
                    "وضعیت": status
                })

            activity_df = pd.DataFrame(activity_rows)
            st.dataframe(
                activity_df,
                use_container_width=True,
                hide_index=True
            )

        # ---- History table ----
        st.markdown("### 📋 تاریخچه عملکرد")

        df_list = []
        for i, d in enumerate(sorted_dates):
            val = float(data[d].get("percent", 0))
            status_text, _ = get_status_and_color(val)

            if i == 0:
                diff_text = "—"
            else:
                diff = round(val - values[i - 1], 1)
                diff_text = f"+{diff}%" if diff > 0 else f"{diff}%"

            df_list.append({
                "روز": i + 1,
                "تاریخ": d,
                "عملکرد": f"{val:g}%",
                "تغییر": diff_text,
                "وضعیت": status_text
            })

        df = pd.DataFrame(df_list)
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info(
            "هنوز هیچ داده‌ای ثبت نشده است. "
            "اولین ثبت شما به عنوان «روز ۱» محاسبه خواهد شد."
        )

# ============================================================
# TAB 3 — Activity management
# ============================================================
with tab3:
    st.subheader("افزودن فعالیت جدید")

    new_act = st.text_input(
        "نام فعالیت جدید:",
        placeholder="مثلاً: مطالعه، زبان، پیاده‌روی..."
    )

    if st.button("➕ افزودن به لیست"):
        new_act = new_act.strip()

        if not new_act:
            st.warning("لطفاً نام فعالیت را وارد کنید.")
        elif new_act in activities:
            st.warning("این فعالیت قبلاً وجود دارد.")
        else:
            activities.append(new_act)

            with open(ACT_FILE, "w", encoding="utf-8") as f:
                json.dump(
                    activities,
                    f,
                    ensure_ascii=False,
                    indent=4
                )

            st.success(f"فعالیت «{new_act}» اضافه شد.")
            st.rerun()

    st.write("---")
    st.markdown("### 📋 فعالیت‌های فعلی")

    for i, activity in enumerate(activities, start=1):
        st.write(f"{i}. {activity}")

    st.caption(
        "نسخه فعلی حذف فعالیت را اضافه نکرده تا اطلاعات تاریخی قبلی شما ناخواسته از بین نرود."
    )
