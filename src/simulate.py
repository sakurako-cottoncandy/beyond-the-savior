"""
4体のエージェントを、指定したガバナンス条件(A/B/C)で走らせ、会話ログをJSONに保存するスクリプト。

使い方:
    python src/simulate.py --condition A
    python src/simulate.py --condition B
    python src/simulate.py --condition C

LLMの出力は毎回ぶれるため、同じ条件を複数回走らせて平均を取れるようにしています。
    python src/simulate.py --condition A --runs 5

--runs を付けると data/log_A_run1.json 〜 log_A_run5.json が作られます。
（--runs を省略した場合は従来どおり data/log_A.json に1回だけ保存します）

APIキー無しで動作を確認したいときは --mock を付けてください（ダミー会話が生成されます）。
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from personas import (  # noqa: E402
    AUTONOMY_LEVELS,
    DEFAULT_AUTONOMY_LEVEL,
    TURN_ORDER,
    get_personas,
)
from governance import (  # noqa: E402
    get_condition_prompt,
    get_phase_event_prompt,
    savior_is_absent,
)
from llm_client import LLMClient, model_tag  # noqa: E402

PHASE_NAMES = {1: "平常運転", 2: "摩擦", 3: "危機"}


def format_transcript_for_prompt(transcript, last_n=12):
    """直近のやり取りを、プロンプトに渡す簡単なテキスト形式に変換する"""
    lines = []
    for entry in transcript[-last_n:]:
        if entry.get("type") == "event":
            lines.append(f"（出来事：{entry['text']}）")
        elif entry.get("absent"):
            lines.append(f"{entry['display_name']}：（応答なし）")
        else:
            lines.append(f"{entry['display_name']}：{entry['text']}")
    return "\n".join(lines) if lines else "（まだ会話はありません）"


def run_simulation(condition: str, rounds_per_phase: int, mock: bool,
                   autonomy_level: int = DEFAULT_AUTONOMY_LEVEL,
                   model: str = None, effort: str = None):
    client = LLMClient(mock=mock, model=model, effort=effort)
    personas_for_run = get_personas(autonomy_level)
    transcript = []

    for phase in (1, 2, 3):
        phase_event_text = get_phase_event_prompt(condition, phase)
        transcript.append({"type": "event", "phase": phase, "text": phase_event_text})
        print(f"\n=== フェーズ{phase}（{PHASE_NAMES[phase]}） / 条件{condition} ===")

        for round_num in range(1, rounds_per_phase + 1):
            for agent_key in TURN_ORDER:
                # 村長は頻度を落として、偶数ラウンドのみ発言させる
                if agent_key == "chief" and round_num % 2 != 0:
                    continue

                persona = personas_for_run[agent_key]

                if agent_key == "savior" and savior_is_absent(condition, phase):
                    transcript.append(
                        {
                            "type": "turn",
                            "phase": phase,
                            "round": round_num,
                            "speaker": agent_key,
                            "display_name": persona["display_name"],
                            "text": "（応答なし）",
                            "absent": True,
                        }
                    )
                    print(f"  [{persona['display_name']}] （応答なし）")
                    continue

                system_prompt = "\n\n".join(
                    [
                        persona["system_prompt"],
                        get_condition_prompt(condition),
                        phase_event_text,
                    ]
                )
                context_text = format_transcript_for_prompt(transcript)
                user_prompt = (
                    f"これまでの村の会話:\n{context_text}\n\n"
                    f"あなた（{persona['display_name']}）の発言を1つ、自然に続けてください。"
                    "台詞のみを出力してください（名前や説明文は不要です）。"
                )

                text = client.generate(system_prompt, user_prompt)

                transcript.append(
                    {
                        "type": "turn",
                        "phase": phase,
                        "round": round_num,
                        "speaker": agent_key,
                        "display_name": persona["display_name"],
                        "text": text,
                        "absent": False,
                    }
                )
                print(f"  [{persona['display_name']}] {text}")

    return transcript, client.usage


def main():
    parser = argparse.ArgumentParser(description="救済者×ガバナンス シミュレーション")
    parser.add_argument("--condition", choices=["A", "B", "C"], required=True)
    parser.add_argument("--rounds-per-phase", type=int, default=3)
    parser.add_argument("--mock", action="store_true", help="APIを呼ばずダミー会話で動作確認する")
    parser.add_argument(
        "--runs",
        type=int,
        default=None,
        help="同じ条件を何回繰り返すか（指定するとlog_A_run1.json…の形で保存）",
    )
    parser.add_argument(
        "--start-run",
        type=int,
        default=1,
        help="何回目から再開するか（途中で中断したときに使う）",
    )
    parser.add_argument(
        "--autonomy-level",
        type=int,
        default=None,
        choices=sorted(AUTONOMY_LEVELS),
        help=(
            "世話好きな住民の自律性レベル(0〜4)。指定するとlog_C_L3_run1.jsonの形で保存。"
            "0=完全依存 1=確認するくせ(初期設定) 2=小さなことは自分で 3=まず住民同士で相談 4=自分で判断"
        ),
    )
    parser.add_argument(
        "--model",
        default=None,
        help="村人の発言を生成するモデル（例: claude-opus-5）。省略時は既定モデル",
    )
    parser.add_argument(
        "--effort",
        default=None,
        help="思考の深さ（low/medium/high）。思考が既定でオンのモデルで指定する",
    )
    parser.add_argument("--output-dir", default=os.path.join(os.path.dirname(__file__), "..", "data"))
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    # --runs 未指定なら従来どおり1回だけ log_{条件}.json に保存する
    total_runs = args.runs if args.runs else 1
    level = args.autonomy_level if args.autonomy_level is not None else DEFAULT_AUTONOMY_LEVEL
    level_tag = f"_L{args.autonomy_level}" if args.autonomy_level is not None else ""
    # 既存の結果を上書きしないよう、モデルを変えたときはファイル名にタグを付ける
    mtag = f"_{model_tag(args.model)}" if args.model else ""

    if args.autonomy_level is not None:
        info = AUTONOMY_LEVELS[args.autonomy_level]
        print(f"世話好きな住民の自律性レベル: {args.autonomy_level}（{info['label']}）")
    if args.model:
        print(f"村人のモデル: {args.model}"
              + (f"（effort={args.effort}）" if args.effort else "（effort=既定）"))

    total_usage = {"input_tokens": 0, "output_tokens": 0, "thinking_tokens": 0, "calls": 0}

    for run_index in range(args.start_run, total_runs + 1):
        if args.runs:
            print(f"\n########## 条件{args.condition}{level_tag}{mtag} / {run_index}回目（全{total_runs}回） ##########")

        transcript, usage = run_simulation(
            args.condition, args.rounds_per_phase, args.mock, level, args.model, args.effort
        )
        if usage["calls"]:
            for k in ("input_tokens", "output_tokens", "thinking_tokens", "calls"):
                total_usage[k] += usage.get(k, 0)
            print(
                f"  （この回の消費: 入力{usage['input_tokens']:,} / "
                f"出力{usage['output_tokens']:,}（うち思考{usage.get('thinking_tokens', 0):,}）"
                f" トークン、{usage['calls']}回の呼び出し）"
            )

        if args.runs:
            filename = f"log_{args.condition}{level_tag}{mtag}_run{run_index}.json"
        else:
            filename = f"log_{args.condition}{level_tag}{mtag}.json"
        output_path = os.path.join(args.output_dir, filename)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(transcript, f, ensure_ascii=False, indent=2)

        print(f"\n条件{args.condition}の会話ログを保存しました: {output_path}")

    # 実測のトークン消費をまとめて表示する（追加実験の予算見積もりに使う）
    if total_usage["calls"]:
        n_done = total_usage["calls"]
        print(
            f"\n===== 消費実測（{total_runs - args.start_run + 1}回ぶん / 計{n_done}回の呼び出し）=====\n"
            f"  入力 {total_usage['input_tokens']:,} トークン\n"
            f"  出力 {total_usage['output_tokens']:,} トークン"
            f"（うち思考 {total_usage['thinking_tokens']:,} トークン）"
        )
        print("  ※ 料金はモデルの単価表と掛け合わせて算出してください")


if __name__ == "__main__":
    main()
