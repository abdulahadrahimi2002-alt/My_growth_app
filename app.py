import streamlit as st
import json
import os
from datetime import date
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

# ---------------- Load Data ----------------
habits = load_json(HABITS_FILE, ["ورزش", "مطالعه چینی", "برنامه‌نویسی"])
records = load_json(RECORDS_FILE, {})
goals = load_json(GOALS_FILE, [])
notes = load_json(NOTES_FILE, {})

# ---------------- UI Setup ----------------
st.set_page_config(page_title="MyGrowth", page_icon="💖", layout="wide")

st.title("💖 MyGrowth")
st.caption("پلنر شخصی برای برنامه‌ریزی، عادت‌ها و دیدن رشد واقعی زندگی")

# Dictionary Translation
translations = {
    "dashboard": "داشبورد",
    "today": "برنامه امروز",
    "habits": "عادت‌ها",
    "goals": "اهداف",
    "growth": "رشد من",
    "notes": "یادداشت روزانه",
    "settings": "تنظیمات",
    "growth_title": "رشد من",
    "empty": "هنوز داده‌ای برای نمایش وجود ندارد."
}

def tr(key):
    return translations.get(key, key)

# ---------------- Tabs Layout ----------------
tabs = st.tabs([
    tr("dashboard"),
    tr("today"),
    tr("habits"),
    tr("goals"),
    tr("growth"),
    tr("notes"),
    tr("settings")
])

# ---------------- Tab 1: Dashboard ----------------
with tabs[0]:
    st.subheader(tr("dashboard"))
    c1, c2, c3 = st.columns(3)
    c1.metric("کل ثبت‌ها / Total Records", len(records))
    avg_p = sum(r["percent"] for r in records.values()) / len(records) if records else 0
    c2.metric("میانگین عملکرد / Avg", f"{avg_p:.1f}%")
    c3.metric("تعداد عادت‌ها / Active Habits", len(habits))
    
    st.markdown("---")
    if records:
        latest_k = sorted(records.keys())[-1]
        st.write(f"**آخرین ثبت ({latest_k}):** {records[latest_k]['percent']}%")

# ---------------- Tab 2: Today ----------------
with tabs[1]:
    st.subheader(tr("today"))
    today_str = str(date.today())
    st.write(f"📅 **تاریخ امروز / Today:** {today_str}")
    
    done_count = 0
    total_habits = len(habits)
    
    if total_habits == 0:
        st.warning("هنوز عادتی ثبت نکرده‌اید. از تب 'عادت‌ها' اضافه کنید.")
    else:
        st.write("عادت‌های امروز را علامت بزنید:")
        for h in habits:
            chk = st.checkbox(h, key=f"chk_{today_str}_{h}")
            if chk:
                done_count += 1
        
        calc_pct = int((done_count / total_habits) * 100) if total_habits > 0 else 0
        st.progress(calc_pct / 100)
        st.write(f"عملکرد امروز: **{calc_pct}%**")
        
        if st.button("ذخیره عملکرد امروز / Save Today"):
            records[today_str] = {"percent": calc_pct}
            save_json(RECORDS_FILE, records)
            st.success("با موفقیت ذخیره شد!")

# ---------------- Tab 3: Habits ----------------
with tabs[2]:
    st.subheader(tr("habits"))
    new_h = st.text_input("نام عادت جدید / New Habit:")
    if st.button("افزودن عادت / Add Habit"):
        if new_h and new_h not in habits:
            habits.append(new_h)
            save_json(HABITS_FILE, habits)
            st.success("عادت اضافه شد.")
            st.rerun()
            
    st.markdown("---")
    st.write("عادت‌های فعلی:")
    for h in habits:
        col1, col2 = st.columns([4, 1])
        col1.write(f"• {h}")
        if col2.button("حذف", key=f"del_{h}"):
            habits.remove(h)
            save_json(HABITS_FILE, habits)
            st.rerun()

# ---------------- Tab 4: Goals ----------------
with tabs[3]:
    st.subheader(tr("goals"))
    g_text = st.text_input("هدف جدید / New Goal:")
    if st.button("افزودن هدف / Add Goal"):
        if g_text:
            goals.append({"text": g_text, "done": False})
            save_json(GOALS_FILE, goals)
            st.rerun()
            
    for i, g in enumerate(goals):
        chk = st.checkbox(g["text"], value=g["done"], key=f"goal_{i}")
        if chk != g["done"]:
            goals[i]["done"] = chk
            save_json(GOALS_FILE, goals)

# ---------------- Tab 5: Growth ----------------
with tabs[4]:
    st.subheader(tr("growth_title"))
    keys = sorted(records.keys())
    if keys:
        period = st.selectbox("Range / بازه", ["7", "14", "30", "All"])
        n = len(keys) if period == "All" else int(period)
        ck = keys[-n:]
        vals = [records[k]["percent"] for k in ck]

        fig = go.Figure(go.Scatter(
            x=[k[5:] for k in ck],
            y=vals,
            mode="lines+markers+text",
            text=[f"{v:g}%" for v in vals],
            textposition="top center",
            line=dict(width=3),
            marker=dict(size=9)
        ))
        fig.add_hline(y=75, line_dash="dash", annotation_text="75%")
        fig.update_layout(
            yaxis=dict(range=[0, 105]),
            height=480,
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
                "Date / تاریخ": k,
                "Performance / عملکرد": f"{v:g}%",
                "Change / تغییر": diff,
                "Status / وضعیت": status(v)
            })
        st.dataframe(pd.DataFrame(history), use_container_width=True, hide_index=True)
    else:
        st.info(tr("empty"))

# ---------------- Tab 6: Notes ----------------
with tabs[5]:
    st.subheader(tr("notes"))
    note_in = st.text_area("یادداشت امروز / Daily Note:")
    if st.button("ذخیره یادداشت / Save Note"):
        notes[str(date.today())] = note_in
        save_json(NOTES_FILE, notes)
        st.success("یادداشت ذخیره شد.")

# ---------------- Tab 7: Settings ----------------
with tabs[6]:
    st.subheader(tr("settings"))
    st.write("تنظیمات برنامه در حال حاضر فعال است.")
