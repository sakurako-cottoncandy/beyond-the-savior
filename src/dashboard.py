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
    """会話ログ・単発スコア・複数回の集計結果をまとめて読み込む。

    集計結果（scores_X_aggregate.json）があればそちらを優先して平均値を使い、
    無ければ従来どおり単発のスコア（scores_X.json）を使う。
    """
    logs, scores, aggregates = {}, {}, {}
    for cond in ("A", "B", "C"):
        agg = load_json(f"scores_{cond}_aggregate.json")
        aggregates[cond] = agg

        if agg:
            # 集計結果を、単発スコアと同じ形に変換して使い回す
            m = agg["metrics"]
            scores[cond] = {
                "savior_load_percent": m["savior_load_percent"]["mean"],
                "village_autonomy_score": m["village_autonomy_score"]["mean"],
                "psychological_safety": {
                    "can_ask_for_help": m["can_ask_for_help"]["mean"],
                    "feel_belonging": m["feel_belonging"]["mean"],
                    "savior_dependency": m["savior_dependency"]["mean"],
                },
                "summary": (agg.get("run_summaries") or [""])[0],
                "condition": cond,
            }
        else:
            scores[cond] = load_json(f"scores_{cond}.json")

        # タイムライン表示用のログ。複数回実行していれば全回分を読み込む
        runs = []
        run_index = 1
        while True:
            log = load_json(f"log_{cond}_run{run_index}.json")
            if log is None:
                break
            runs.append(log)
            run_index += 1
        if not runs:
            single = load_json(f"log_{cond}.json")
            if single:
                runs = [single]
        logs[cond] = runs

    return logs, scores, aggregates


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


def render_autonomy_comparison(scores, aggregates=None):
    st.subheader("村の自律度スコア（救済者以外が自力で解決できた度合い）")
    conditions = [c for c in ("A", "B", "C") if scores.get(c)]
    if not conditions:
        st.caption("データがありません。")
        return
    values = [scores[c]["village_autonomy_score"] for c in conditions]
    colors = [CONDITION_COLORS[c] for c in conditions]
    labels = [CONDITION_LABELS[c] for c in conditions]

    # 複数回実行していれば、標準偏差をエラーバーとして重ねる
    error_y = None
    aggregates = aggregates or {}
    stdevs = [
        aggregates[c]["metrics"]["village_autonomy_score"]["stdev"]
        if aggregates.get(c)
        else None
        for c in conditions
    ]
    if any(s is not None for s in stdevs):
        error_y = dict(
            type="data",
            array=[s if s is not None else 0 for s in stdevs],
            visible=True,
            color=TEXT_MUTED,
            thickness=1.5,
            width=6,
        )

    fig = go.Figure(
        go.Bar(
            x=labels,
            y=values,
            marker=dict(color=colors, line=dict(width=0)),
            error_y=error_y,
            text=[f"{v}" for v in values],
            textposition="outside",
            hovertemplate="%{x}<br>自律度スコア: %{y}<extra></extra>",
        )
    )
    fig.update_yaxes(range=[0, 100], gridcolor=GRID, zerolinecolor=GRID)
    fig.update_xaxes(showgrid=False)
    fig.update_layout(**base_layout(""))
    st.plotly_chart(fig, use_container_width=True, key="autonomy_bar")


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
    st.plotly_chart(fig, use_container_width=True, key="psych_radar")


METRIC_LABELS = {
    "savior_load_percent": "救済者の負荷（%）",
    "village_autonomy_score": "村の自律度スコア",
    "can_ask_for_help": "助けを求められるか",
    "feel_belonging": "ここにいてよいと思えるか",
    "savior_dependency": "救済者依存度（高いほど悪い）",
}


def render_run_scatter(aggregates):
    """1回ごとの実測値を点で並べ、条件Cの「分岐」が目で見えるようにする"""
    available = [c for c in ("A", "B", "C") if aggregates.get(c)]
    if not available:
        return

    st.subheader("1回ごとの実測値 ― 依存は安定し、自律は分岐する")
    metric_key = st.selectbox(
        "指標を選択",
        options=list(METRIC_LABELS.keys()),
        format_func=lambda k: METRIC_LABELS[k],
        key="scatter_metric",
    )

    fig = go.Figure()
    for cond in available:
        stats = aggregates[cond]["metrics"][metric_key]
        values = stats["values"]
        fig.add_trace(
            go.Scatter(
                x=[CONDITION_LABELS[cond]] * len(values),
                y=values,
                mode="markers",
                name=CONDITION_LABELS[cond],
                marker=dict(color=CONDITION_COLORS[cond], size=14, opacity=0.75,
                            line=dict(width=1, color=SURFACE)),
                hovertemplate="%{x}<br>" + METRIC_LABELS[metric_key] + ": %{y}<extra></extra>",
            )
        )
        # 平均を横線で示す
        fig.add_trace(
            go.Scatter(
                x=[CONDITION_LABELS[cond]],
                y=[stats["mean"]],
                mode="markers",
                marker=dict(color=CONDITION_COLORS[cond], size=22, symbol="line-ew-open",
                            line=dict(width=3, color=CONDITION_COLORS[cond])),
                showlegend=False,
                hovertemplate="平均: %{y}<extra></extra>",
            )
        )

    fig.update_yaxes(range=[0, 100], gridcolor=GRID, zerolinecolor=GRID,
                     title=dict(text=METRIC_LABELS[metric_key], font=dict(color=TEXT_SECONDARY)))
    fig.update_xaxes(showgrid=False)
    fig.update_layout(showlegend=False, **base_layout("", height=380))
    st.plotly_chart(fig, use_container_width=True, key="run_scatter")

    st.caption(
        "点が1回の実行。A・Bは点が重なってほぼ一直線＝毎回同じ結果になる（依存は安定した状態）。"
        "一方Cは点が上下に散らばる＝同じルールでも「自律できた回」と「依存に戻った回」に分かれた。"
    )


def render_variability(aggregates):
    """複数回実行したときの、ばらつき（平均±標準偏差）を表で見せる"""
    available = [c for c in ("A", "B", "C") if aggregates.get(c)]
    if not available:
        return

    n_runs = aggregates[available[0]]["n_runs"]
    st.subheader(f"実行ごとのばらつき（各条件 {n_runs} 回の実測）")
    st.caption(
        "LLMの出力は毎回ぶれるため、同じ条件を複数回走らせて平均と標準偏差を算出しています。"
        "標準偏差が小さいほど、その条件で安定して同じ結果が出たことを意味します。"
    )

    rows = []
    for key, label in METRIC_LABELS.items():
        row = {"指標": label}
        for cond in available:
            stats = aggregates[cond]["metrics"][key]
            row[CONDITION_LABELS[cond]] = f"{stats['mean']:.1f} ± {stats['stdev']:.1f}"
        rows.append(row)

    st.table(rows)

    with st.expander("各回の生の数値を見る"):
        for cond in available:
            st.markdown(f"**{CONDITION_LABELS[cond]}**")
            detail = []
            for key, label in METRIC_LABELS.items():
                stats = aggregates[cond]["metrics"][key]
                detail.append({"指標": label, **{f"{i+1}回目": v for i, v in enumerate(stats["values"])}})
            st.table(detail)


def render_summaries(scores, aggregates=None):
    st.subheader("AI審査役による考察")
    aggregates = aggregates or {}

    for cond in ("A", "B", "C"):
        agg = aggregates.get(cond)
        if agg and agg.get("run_summaries"):
            summaries = agg["run_summaries"]
            st.markdown(f"**{CONDITION_LABELS[cond]}**（{len(summaries)}回分）")
            pick = st.selectbox(
                "何回目の考察を見るか",
                options=list(range(len(summaries))),
                format_func=lambda i: f"{i + 1}回目",
                key=f"summary_pick_{cond}",
                label_visibility="collapsed",
            )
            st.markdown(f"> {summaries[pick]}")
        else:
            s = scores.get(cond)
            if s and s.get("summary"):
                st.markdown(f"**{CONDITION_LABELS[cond]}**：{s['summary']}")


def render_timeline(logs):
    st.subheader("会話ログ・タイムライン")

    col1, col2 = st.columns([2, 1])
    with col1:
        cond = st.selectbox(
            "条件を選択",
            options=[c for c in ("A", "B", "C") if logs.get(c)],
            format_func=lambda c: CONDITION_LABELS[c],
        )
    runs = logs.get(cond) or []
    if not runs:
        st.caption("この条件のログはまだありません。")
        return

    with col2:
        run_index = st.selectbox(
            "何回目の実行を見るか",
            options=list(range(len(runs))),
            format_func=lambda i: f"{i + 1}回目",
            key="timeline_run",
        )
    transcript = runs[run_index]

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

    logs, scores, aggregates = load_all()

    if not any(scores.values()):
        st.warning(
            "まだデータがありません。先に以下を実行してください：\n\n"
            "```\npython src/simulate.py --condition A --runs 5\n"
            "python src/score.py --condition A --runs 5\n"
            "（B, Cも同様に）\n```"
        )

    if any(aggregates.values()):
        n_runs = next(a["n_runs"] for a in aggregates.values() if a)
        st.info(f"表示中のスコアは、各条件を {n_runs} 回ずつ実行した平均値です。")

    render_savior_load(scores)
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        render_autonomy_comparison(scores, aggregates)
    with col2:
        render_psychological_safety(scores)
    st.divider()
    render_run_scatter(aggregates)
    st.divider()
    render_variability(aggregates)
    st.divider()
    render_summaries(scores, aggregates)
    st.divider()
    render_timeline(logs)


if __name__ == "__main__":
    main()
