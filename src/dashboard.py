"""
救済者×ガバナンス シミュレーション・ダッシュボード

使い方:
    streamlit run src/dashboard.py

data/log_A.json, log_B.json, log_C.json / scores_A.json, scores_B.json, scores_C.json
（simulate.py と score.py をA/B/C全条件で実行した後の出力）を読み込んで表示します。
"""

import json
import os

import plotly.graph_objects as go
import streamlit as st

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

# dataviz skillの検証済みカテゴリカル配色（先頭3色は全ペアでCVDセーフ）をA/B/Cに固定割り当て
CONDITION_COLORS = {
    "A": "#2a78d6",  # blue
    "B": "#eb6834",  # orange
    "C": "#1baf7a",  # aqua
}
CONDITION_LABELS = {
    "A": "A：救済者集中型",
    "B": "B：救済者が消える村",
    "C": "C：分散ガバナンス型",
}

STATUS_COLORS = {
    "good": "#0ca30c",
    "warning": "#fab219",
    "serious": "#ec835a",
    "critical": "#d03b3b",
}

SURFACE = "#fcfcfb"
GRID = "#e1e0d9"
TEXT_SECONDARY = "#52514e"
TEXT_MUTED = "#898781"

PHASE_NAMES = {1: "平常運転", 2: "摩擦", 3: "危機"}


def load_json(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_all():
    logs, scores = {}, {}
    for cond in ("A", "B", "C"):
        logs[cond] = load_json(f"log_{cond}.json")
        scores[cond] = load_json(f"scores_{cond}.json")
    return logs, scores


def status_for_load(value):
    if value is None:
        return STATUS_COLORS["warning"], "不明"
    if value < 40:
        return STATUS_COLORS["good"], "低負荷"
    if value < 70:
        return STATUS_COLORS["warning"], "要注意"
    return STATUS_COLORS["critical"], "高負荷"


def base_layout(title, height=360):
    return dict(
        title=dict(text=title, font=dict(color="#0b0b0b", size=16)),
        plot_bgcolor=SURFACE,
        paper_bgcolor=SURFACE,
        font=dict(color=TEXT_SECONDARY),
        height=height,
        margin=dict(l=40, r=20, t=50, b=40),
    )


def render_savior_load(scores):
    st.subheader("救済者の負荷メーター")
    cols = st.columns(3)
    for col, cond in zip(cols, ("A", "B", "C")):
        s = scores.get(cond)
        value = s["savior_load_percent"] if s else None
        color, label = status_for_load(value)
        with col:
            st.markdown(f"**{CONDITION_LABELS[cond]}**")
            if value is None:
                st.caption("データなし（simulate.py / score.py を実行してください）")
                continue
            fig = go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=value,
                    number={"suffix": "%", "font": {"color": "#0b0b0b"}},
                    gauge={
                        "axis": {"range": [0, 100], "tickcolor": TEXT_MUTED},
                        "bar": {"color": color},
                        "bgcolor": SURFACE,
                        "borderwidth": 1,
                        "bordercolor": GRID,
                    },
                )
            )
            fig.update_layout(**base_layout("", height=220))
            st.plotly_chart(fig, use_container_width=True, key=f"savior_load_{cond}")
            st.markdown(f"状態：**{label}**")


def render_autonomy_comparison(scores):
    st.subheader("村の自律度スコア（救済者以外が自力で解決できた度合い）")
    conditions = [c for c in ("A", "B", "C") if scores.get(c)]
    if not conditions:
        st.caption("データがありません。")
        return
    values = [scores[c]["village_autonomy_score"] for c in conditions]
    colors = [CONDITION_COLORS[c] for c in conditions]
    labels = [CONDITION_LABELS[c] for c in conditions]

    fig = go.Figure(
        go.Bar(
            x=labels,
            y=values,
            marker=dict(color=colors, line=dict(width=0)),
            text=[f"{v}" for v in values],
            textposition="outside",
            hovertemplate="%{x}<br>自律度スコア: %{y}<extra></extra>",
        )
    )
    fig.update_yaxes(range=[0, 100], gridcolor=GRID, zerolinecolor=GRID)
    fig.update_xaxes(showgrid=False)
    fig.update_layout(**base_layout(""))
    st.plotly_chart(fig, use_container_width=True)


def render_psychological_safety(scores):
    st.subheader("関係性・心理的安全性（3条件比較）")
    categories = ["助けを求められるか", "ここにいてよいと思えるか", "救済者依存度（高いほど依存）"]

    fig = go.Figure()
    any_data = False
    for cond in ("A", "B", "C"):
        s = scores.get(cond)
        if not s:
            continue
        any_data = True
        ps = s["psychological_safety"]
        values = [ps["can_ask_for_help"], ps["feel_belonging"], ps["savior_dependency"]]
        fig.add_trace(
            go.Scatterpolar(
                r=values + [values[0]],
                theta=categories + [categories[0]],
                fill="toself",
                name=CONDITION_LABELS[cond],
                line=dict(color=CONDITION_COLORS[cond], width=2),
                opacity=0.7,
                hovertemplate="%{theta}: %{r}<extra>" + CONDITION_LABELS[cond] + "</extra>",
            )
        )

    if not any_data:
        st.caption("データがありません。")
        return

    fig.update_layout(
        polar=dict(
            bgcolor=SURFACE,
            radialaxis=dict(visible=True, range=[0, 100], gridcolor=GRID, color=TEXT_MUTED),
            angularaxis=dict(gridcolor=GRID, color=TEXT_SECONDARY),
        ),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.15),
        **base_layout("", height=420),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_summaries(scores):
    for cond in ("A", "B", "C"):
        s = scores.get(cond)
        if s and s.get("summary"):
            st.markdown(f"**{CONDITION_LABELS[cond]}**：{s['summary']}")


def render_timeline(logs):
    st.subheader("会話ログ・タイムライン")
    cond = st.selectbox(
        "条件を選択", options=[c for c in ("A", "B", "C") if logs.get(c)], format_func=lambda c: CONDITION_LABELS[c]
    )
    transcript = logs.get(cond)
    if not transcript:
        st.caption("この条件のログはまだありません。")
        return

    for entry in transcript:
        if entry.get("type") == "event":
            st.markdown(
                f"---\n##### フェーズ{entry['phase']}（{PHASE_NAMES.get(entry['phase'], '')}）の出来事\n"
                f"> {entry['text']}"
            )
        else:
            absent = entry.get("absent")
            name = entry["display_name"]
            text = "（応答なし）" if absent else entry["text"]
            if absent:
                st.markdown(f"🔇 **{name}**：*{text}*")
            else:
                st.markdown(f"🗣️ **{name}**：{text}")


def main():
    st.set_page_config(page_title="救済者×ガバナンス ダッシュボード", layout="wide")
    st.title("救済者 × ガバナンス — シミュレーション・ダッシュボード")
    st.caption("神が降りなくても、村は回るか？ A/B/C 3条件の比較結果")

    logs, scores = load_all()

    if not any(scores.values()):
        st.warning(
            "まだデータがありません。先に以下を実行してください：\n\n"
            "```\npython src/simulate.py --condition A\npython src/score.py --condition A\n"
            "（B, Cも同様に）\n```"
        )

    render_savior_load(scores)
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        render_autonomy_comparison(scores)
    with col2:
        render_psychological_safety(scores)
    st.divider()
    render_summaries(scores)
    st.divider()
    render_timeline(logs)


if __name__ == "__main__":
    main()
