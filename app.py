import plotly.graph_objects as go
import pandas as pd


# ۱. تابع محاسبه وضعیت و رنگ برای جدول بالای نمودار
def get_status_info(percentage):
    if percentage >= 80:
        return "🟢 عالی", "#22c55e"
    elif percentage >= 60:
        return "🟡 خوب", "#84cc16"
    elif percentage >= 45:
        return "🟠 متوسط", "#f59e0b"
    else:
        return "🔴 ضعیف", "#ef4444"


# ۲. تابع ساخت نمودار میله‌ای باریک با ۴ رنگ
def create_thin_bar_chart(df, title="📈 روند رشد روزانه"):
    fig = go.Figure()

    # تعریف ۴ سطح عملکرد و رنگ‌های اختصاصی
    levels = [
        ("🟢 عالی (۸۰٪ - ۱۰۰٪)", 80, 100, "#22c55e"),
        ("🟡 خوب (۶۰٪ - ۷۹٪)", 60, 79.9, "#84cc16"),
        ("🟠 متوسط (۴۵٪ - ۵۹٪)", 45, 59.9, "#f59e0b"),
        ("🔴 ضعیف (۰٪ - ۴۴٪)", 0, 44.9, "#ef4444"),
    ]

    # رسم میله‌ها برای هر سطح (در صورت نبود داده، لایه خالی رسم می‌شود تا Legend فعال بماند)
    for label, min_val, max_val, color in levels:
        sub_df = df[
            (df["Performance (%)"] >= min_val)
            & (df["Performance (%)"] <= max_val)
        ]

        fig.add_trace(
            go.Bar(
                x=sub_df["X_Label"] if not sub_df.empty else [None],
                y=sub_df["Performance (%)"] if not sub_df.empty else [None],
                name=label,
                marker_color=color,
                width=0.1,  # عرض ثابت و بسیار باریک میله‌ها
                hovertemplate="<b>%{x}</b><br>عملکرد: %{y}%<extra></extra>",
            )
        )

    fig.update_layout(
        title={"text": title, "font": {"size": 18, "color": "#1e1b4b"}},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        barmode="group",
        bargap=0.8,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.35,
            xanchor="center",
            x=0.5,
            font=dict(size=12, color="#334155"),
        ),
        xaxis=dict(
            showgrid=False,
            tickfont=dict(color="#64748b", size=11),
            title="روزها",
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="#f1f5f9",
            range=[0, 105],
            tickfont=dict(color="#64748b"),
            title="فیصدی عملکرد",
        ),
        margin=dict(l=20, r=20, t=40, b=90),
        height=420,
    )
    return fig


# ۳. نحوه فراخوانی و ساخت صفحه در Streamlit
def show_growth_page(df_daily_data):
    st.title("📈 روند رشد")

    if df_daily_data.empty:
        st.info("هنوز داده‌ای برای نمایش ثبت نشده است.")
        return

    # پردازش داده‌ها برای جدول
    table_df = df_daily_data.copy()
    status_list = [
        get_status_info(p)[0] for p in table_df["Performance (%)"]
    ]
    table_df["Status"] = status_list

    # نمایش جدول بالای نمودار
    st.dataframe(
        table_df[["Date", "Performance (%)", "Status"]],
        use_container_width=True,
    )

    st.markdown("---")

    # آماده‌سازی لیبل محور افقی و نمایش نمودار
    table_df["X_Label"] = table_df["Date"].astype(str)
    fig = create_thin_bar_chart(table_df)
    st.plotly_chart(fig, use_container_width=True)
    
