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
"""

import argparse
import json
import os
import re
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


def score_condition(condition: str, mock: bool, data_dir: str):
    log_path = os.path.join(data_dir, f"log_{condition}.json")
    with open(log_path, "r", encoding="utf-8") as f:
        transcript = json.load(f)

    client = LLMClient(mock=mock)

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


def main():
    parser = argparse.ArgumentParser(description="会話ログのスコアリング")
    parser.add_argument("--condition", choices=["A", "B", "C"], required=True)
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--data-dir", default=os.path.join(os.path.dirname(__file__), "..", "data"))
    args = parser.parse_args()

    scores = score_condition(args.condition, args.mock, args.data_dir)

    output_path = os.path.join(args.data_dir, f"scores_{args.condition}.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(scores, f, ensure_ascii=False, indent=2)

    print(json.dumps(scores, ensure_ascii=False, indent=2))
    print(f"\n条件{args.condition}のスコアを保存しました: {output_path}")


if __name__ == "__main__":
    main()
