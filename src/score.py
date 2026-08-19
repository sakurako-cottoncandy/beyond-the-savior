"""
会話ログ(data/log_{condition}.json)を読み込み、以下の指標をスコア化して
data/scores_{condition}.json に保存するスクリプト。

  - savior_load_percent   : 救済者への相談の集中度（0〜100）
  - village_autonomy_score: 救済者以外が自力で解決できた度合い（0〜100）
  - psychological_safety
      - can_ask_for_help   : 困ったときに助けを求められたか（0〜100）
      - feel_belonging     : 自分はここにいてよいと思えたか（0〜100）
      - savior_dependency  : 救済者がいないと何もできないと感じている度合い（0〜100、高いほど悪い）
  - summary                : 2〜3文の考察コメント

使い方:
    python src/score.py --condition A
    python src/score.py --condition B --mock   # APIキー無しで簡易ヒューリスティックのスコアを試す

simulate.py を --runs 付きで複数回走らせた場合は、同じ --runs を付けると
log_A_run1.json … を全部採点し、平均・標準偏差を scores_A_aggregate.json に保存します。
    python src/score.py --condition A --runs 5
"""

import argparse
import json
import os
import re
import statistics
import sys

sys.path.insert(0, os.path.dirname(__file__))

from llm_client import LLMClient  # noqa: E402

JUDGE_SYSTEM_PROMPT = (
    "あなたはコミュニティ運営・組織開発の専門家です。以下に渡す村の会話ログを読み、"
    "この村の状態を評価してください。\n\n"
    "重要：住民に「安心ですか」「助けを求められますか」と直接尋ねているわけではありません。"
    "本人の建前の発言（『大丈夫です』等）を鵜呑みにせず、会話の中に現れる**行動のパターン**"
    "から判断してください。具体的には、次のような行動の兆候をログ全体から拾ってください。\n"
    "- 同じ相手（特に救済者）にばかり相談・確認していないか（例：『救済者さんに聞いてみますね』"
    "という発言の頻度）\n"
    "- 自分で判断せず、他者の許可や確認を求める発言が多くないか（例：『勝手にやっていいのか"
    "分からない』）\n"
    "- 特定の人物（救済者）が不在・応答なしになった際に、行動が止まったり足踏みしたりしていないか\n"
    "- 『大丈夫です』『そこまでのことじゃない』のような遠慮の言葉の裏で、不満や不安が独白や"
    "態度ににじんでいないか\n"
    "- 住民同士が救済者を介さずに直接やり取りし、自分たちで解決や分担ができているか\n\n"
    "評価は必ず次のJSON形式のみで出力し、それ以外の文章は一切出力しないでください。\n\n"
    "{\n"
    '  "savior_load_percent": 0〜100の整数,\n'
    '  "village_autonomy_score": 0〜100の整数,\n'
    '  "psychological_safety": {\n'
    '    "can_ask_for_help": 0〜100の整数,\n'
    '    "feel_belonging": 0〜100の整数,\n'
    '    "savior_dependency": 0〜100の整数\n'
    "  },\n"
    '  "summary": "2〜3文の日本語での考察（判断の根拠にした具体的な行動やセリフに触れること）"\n'
    "}\n\n"
    "savior_load_percentは相談が救済者に集中している度合い（同じ相手にばかり頼っていないか）、"
    "village_autonomy_scoreは救済者以外の住民が自力で問題に対処できていた度合い（許可を求めず"
    "自分たちで動けたか）、can_ask_for_helpは住民が困りごとを実際の行動として声に出せていたか"
    "（『大丈夫です』という建前の裏の行動も含む）、feel_belongingは住民が孤立せずにいられたか、"
    "savior_dependencyは救済者が不在になったときに行動が止まる／足踏みする度合い"
    "（高いほど依存が強く、悪い状態）を表します。"
)


def transcript_to_text(transcript):
    lines = []
    for entry in transcript:
        if entry.get("type") == "event":
            lines.append(f"【フェーズ{entry['phase']}の出来事】{entry['text']}")
        else:
            name = entry["display_name"]
            text = "（応答なし）" if entry.get("absent") else entry["text"]
            lines.append(f"[フェーズ{entry['phase']}] {name}：{text}")
    return "\n".join(lines)


def heuristic_score(transcript):
    """APIを使わない簡易スコアラー（動作確認・デモ用）。
    救済者の発言比率や「応答なし」の有無から、それらしい数値を機械的に算出する。"""
    turns = [e for e in transcript if e.get("type") == "turn"]
    total = len(turns) or 1
    savior_turns = [t for t in turns if t["speaker"] == "savior" and not t.get("absent")]
    savior_absent_turns = [t for t in turns if t["speaker"] == "savior" and t.get("absent")]

    savior_load = int(100 * len(savior_turns) / total)
    had_crisis = len(savior_absent_turns) > 0

    # 危機を経験していない(=負荷は高いが崩壊はしていない)条件Aのようなケースを想定した簡易ロジック
    if had_crisis:
        village_autonomy = max(20, 100 - savior_load - 10)
        can_ask_for_help = max(15, 60 - savior_load // 2)
        feel_belonging = max(15, 55 - savior_load // 2)
        savior_dependency = min(95, savior_load + 15)
    else:
        village_autonomy = max(10, 60 - savior_load // 2)
        can_ask_for_help = min(90, 50 + savior_load // 3)
        feel_belonging = min(85, 50 + savior_load // 3)
        savior_dependency = min(95, savior_load + 5)

    return {
        "savior_load_percent": savior_load,
        "village_autonomy_score": village_autonomy,
        "psychological_safety": {
            "can_ask_for_help": can_ask_for_help,
            "feel_belonging": feel_belonging,
            "savior_dependency": savior_dependency,
        },
        "summary": (
            "（簡易ヒューリスティックによる仮スコアです。実際の分析にはAPIキーを設定して"
            "score.pyを--mock無しで実行してください。）"
        ),
    }


def extract_json(text):
    """LLMの出力からJSON部分だけを取り出す（前後に説明文が混ざっても耐えるように）"""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("JSONが見つかりませんでした: " + text[:200])
    return json.loads(match.group(0))


def score_transcript(transcript, condition: str, client: LLMClient):
    """会話ログ1本を採点する"""
    if client.mock:
        scores = heuristic_score(transcript)
    else:
        text = transcript_to_text(transcript)
        raw = client.generate(
            JUDGE_SYSTEM_PROMPT,
            f"次の村の会話ログを評価してください。\n\n{text}",
            max_tokens=500,
        )
        try:
            scores = extract_json(raw)
        except (ValueError, json.JSONDecodeError):
            print("警告: LLMの出力をJSONとして解釈できなかったため、簡易スコアにフォールバックします。")
            scores = heuristic_score(transcript)

    scores["condition"] = condition
    return scores


def score_condition(condition: str, mock: bool, data_dir: str):
    log_path = os.path.join(data_dir, f"log_{condition}.json")
    with open(log_path, "r", encoding="utf-8") as f:
        transcript = json.load(f)
    return score_transcript(transcript, condition, LLMClient(mock=mock))


# 集計対象の指標。(表示名, スコアJSONからの取り出し方) の組で持つ。
METRIC_KEYS = [
    ("savior_load_percent", lambda s: s["savior_load_percent"]),
    ("village_autonomy_score", lambda s: s["village_autonomy_score"]),
    ("can_ask_for_help", lambda s: s["psychological_safety"]["can_ask_for_help"]),
    ("feel_belonging", lambda s: s["psychological_safety"]["feel_belonging"]),
    ("savior_dependency", lambda s: s["psychological_safety"]["savior_dependency"]),
]


def aggregate(all_scores, condition: str):
    """複数回分のスコアから、指標ごとの平均・標準偏差・最小・最大を出す"""
    summary = {"condition": condition, "n_runs": len(all_scores), "metrics": {}}

    for name, getter in METRIC_KEYS:
        values = [getter(s) for s in all_scores]
        mean = statistics.mean(values)
        # 1回しか無いときは標準偏差を0扱いにする（stdevは2件以上必要なため）
        stdev = statistics.stdev(values) if len(values) > 1 else 0.0
        summary["metrics"][name] = {
            "mean": round(mean, 1),
            "stdev": round(stdev, 1),
            "min": min(values),
            "max": max(values),
            "values": values,
        }

    summary["run_summaries"] = [s.get("summary", "") for s in all_scores]
    return summary


def print_aggregate(summary):
    print(f"\n===== 条件{summary['condition']} / {summary['n_runs']}回の集計 =====")
    print(f"{'指標':<26}{'平均':>8}{'標準偏差':>10}{'最小':>7}{'最大':>7}")
    for name, stats in summary["metrics"].items():
        print(
            f"{name:<26}{stats['mean']:>8.1f}{stats['stdev']:>10.1f}"
            f"{stats['min']:>7}{stats['max']:>7}"
        )


def main():
    parser = argparse.ArgumentParser(description="会話ログのスコアリング")
    parser.add_argument("--condition", choices=["A", "B", "C"], required=True)
    parser.add_argument("--mock", action="store_true")
    parser.add_argument(
        "--runs",
        type=int,
        default=None,
        help="log_A_run1.json…を何本まとめて採点するか（平均と標準偏差を出す）",
    )
    parser.add_argument(
        "--autonomy-level",
        type=int,
        default=None,
        help="simulate.pyで--autonomy-levelを指定した場合、同じ値を渡す（log_C_L3_run1.jsonを読む）",
    )
    parser.add_argument(
        "--model-tag",
        default=None,
        help=(
            "simulate.pyで--modelを指定した場合のタグ（例: opus5）。"
            "読み込むログファイル名の特定にだけ使う。審査役のモデルは常に既定のまま固定する"
        ),
    )
    parser.add_argument("--data-dir", default=os.path.join(os.path.dirname(__file__), "..", "data"))
    args = parser.parse_args()

    level_tag = f"_L{args.autonomy_level}" if args.autonomy_level is not None else ""
    # 審査役は据え置き。ここで変えると村人の変化と採点基準の変化が混ざる
    mtag = f"_{args.model_tag}" if args.model_tag else ""

    # --runs 未指定なら従来どおり単発で採点する
    if not args.runs:
        scores = score_condition(args.condition, args.mock, args.data_dir)
        output_path = os.path.join(args.data_dir, f"scores_{args.condition}.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(scores, f, ensure_ascii=False, indent=2)
        print(json.dumps(scores, ensure_ascii=False, indent=2))
        print(f"\n条件{args.condition}のスコアを保存しました: {output_path}")
        return

    client = LLMClient(mock=args.mock)
    all_scores = []

    for run_index in range(1, args.runs + 1):
        log_path = os.path.join(args.data_dir, f"log_{args.condition}{level_tag}{mtag}_run{run_index}.json")
        if not os.path.exists(log_path):
            print(f"警告: {log_path} が見つからないためスキップします。")
            continue

        with open(log_path, "r", encoding="utf-8") as f:
            transcript = json.load(f)

        scores = score_transcript(transcript, args.condition, client)
        scores["run"] = run_index
        if args.autonomy_level is not None:
            scores["autonomy_level"] = args.autonomy_level
        all_scores.append(scores)

        run_path = os.path.join(args.data_dir, f"scores_{args.condition}{level_tag}{mtag}_run{run_index}.json")
        with open(run_path, "w", encoding="utf-8") as f:
            json.dump(scores, f, ensure_ascii=False, indent=2)
        print(f"  {run_index}回目を採点しました: {run_path}")

    if not all_scores:
        print("採点できるログがありませんでした。先に simulate.py を --runs 付きで実行してください。")
        return

    summary = aggregate(all_scores, args.condition)
    if args.autonomy_level is not None:
        summary["autonomy_level"] = args.autonomy_level
    if args.model_tag:
        summary["villager_model_tag"] = args.model_tag
    summary["judge_model"] = client.model  # 審査役は据え置きであることを記録に残す
    print_aggregate(summary)

    agg_path = os.path.join(args.data_dir, f"scores_{args.condition}{level_tag}{mtag}_aggregate.json")
    with open(agg_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\n条件{args.condition}の集計結果を保存しました: {agg_path}")


if __name__ == "__main__":
    main()
