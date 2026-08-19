"""
「世話好きな住民の自律性レベル」を0〜4まで変えたときに、
村の状態がどこで切り替わるか（＝分岐の閾値）を集計するスクリプト。

5回実行の結果、条件Cは「自律した村」と「依存に戻った村」の2つに分岐した。
その分岐点が世話好きな住民の一歩目だったため、そこだけを段階的に変えて
「どこまで背中を押せば村が変わるのか」を調べる。

使い方:
    python src/analyze_threshold.py
    python src/analyze_threshold.py --condition C

前提: 先に各レベルでシミュレーションと採点を済ませておくこと。
    python src/simulate.py --condition C --runs 5 --autonomy-level 3
    python src/score.py    --condition C --runs 5 --autonomy-level 3
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from personas import AUTONOMY_LEVELS, DEFAULT_AUTONOMY_LEVEL  # noqa: E402

# 「自律した村」と判定する境目。5回実行で観測された2つの状態
# （自律=自律度75前後 / 依存=自律度35前後）の中間に置く。
AUTONOMY_THRESHOLD = 60


def load_level(data_dir: str, condition: str, level: int):
    """あるレベルの集計結果を読む。L1(初期設定)はレベル指定なしのファイルにも対応。"""
    candidates = [f"scores_{condition}_L{level}_aggregate.json"]
    if level == DEFAULT_AUTONOMY_LEVEL:
        # 自律性レベルを導入する前に回した分（レベル指定なし）を初期設定として扱う
        candidates.append(f"scores_{condition}_aggregate.json")

    for name in candidates:
        path = os.path.join(data_dir, name)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f), name
    return None, None


def classify(autonomy_values):
    """各回を「自律した」「依存に戻った」に振り分け、自律できた回数を数える"""
    autonomous = [v for v in autonomy_values if v >= AUTONOMY_THRESHOLD]
    return len(autonomous), len(autonomy_values)


def main():
    parser = argparse.ArgumentParser(description="自律性レベルごとの分岐を集計する")
    parser.add_argument("--condition", default="C", choices=["A", "B", "C"])
    parser.add_argument("--data-dir", default=os.path.join(os.path.dirname(__file__), "..", "data"))
    args = parser.parse_args()

    rows = []
    for level in sorted(AUTONOMY_LEVELS):
        agg, source = load_level(args.data_dir, args.condition, level)
        if not agg:
            continue
        m = agg["metrics"]
        auto_values = m["village_autonomy_score"]["values"]
        n_auto, n_total = classify(auto_values)
        rows.append({
            "level": level,
            "label": AUTONOMY_LEVELS[level]["label"],
            "n_autonomous": n_auto,
            "n_total": n_total,
            "load": m["savior_load_percent"]["mean"],
            "autonomy": m["village_autonomy_score"]["mean"],
            "autonomy_values": auto_values,
            "can_ask": m["can_ask_for_help"]["mean"],
            "belonging": m["feel_belonging"]["mean"],
            "dependency": m["savior_dependency"]["mean"],
            "source": source,
        })

    if not rows:
        print("集計対象が見つかりません。先に simulate.py / score.py を各レベルで実行してください。")
        return

    print(f"\n===== 条件{args.condition}：世話好きな住民の自律性レベル別 =====\n")
    header = (
        f"{'Lv':<4}{'設定':<18}{'自律した回':>12}"
        f"{'救済者負荷':>12}{'村の自律度':>12}{'助けを求める':>14}{'依存度':>10}"
    )
    print(header)
    print("-" * len(header))
    for r in rows:
        ratio = f"{r['n_autonomous']}/{r['n_total']}"
        print(
            f"{r['level']:<4}{r['label']:<18}{ratio:>12}"
            f"{r['load']:>12.1f}{r['autonomy']:>12.1f}{r['can_ask']:>14.1f}{r['dependency']:>10.1f}"
        )

    # 分岐がどこで起きたかを探す
    print("\n----- 各回の村の自律度（自律=" + str(AUTONOMY_THRESHOLD) + "以上）-----")
    for r in rows:
        marks = "".join("●" if v >= AUTONOMY_THRESHOLD else "○" for v in r["autonomy_values"])
        print(f"  L{r['level']} {r['label']:<18} {marks}  {r['autonomy_values']}")
    print("  （●=自律した回 / ○=依存に戻った回）")

    # 閾値の判定：自律が過半数になった最初のレベル
    tipping = next((r for r in rows if r["n_autonomous"] * 2 > r["n_total"]), None)
    print()
    if tipping:
        below = [r for r in rows if r["level"] < tipping["level"]]
        print(f"■ 自律が過半数を超えた最初のレベル：L{tipping['level']}（{tipping['label']}）"
              f" … {tipping['n_autonomous']}/{tipping['n_total']}回")
        if below:
            last = below[-1]
            print(f"  その一つ下のL{last['level']}（{last['label']}）は "
                  f"{last['n_autonomous']}/{last['n_total']}回")
            print(f"  → 分岐点は L{last['level']} と L{tipping['level']} の間にある")
    else:
        print("■ どのレベルでも自律が過半数に届かなかった。")

    # 最適点：村の自律度が最も高かったレベル
    peak = max(rows, key=lambda r: r["autonomy"])
    print(f"\n■ 村の自律度が最も高かったのは L{peak['level']}（{peak['label']}）… "
          f"{peak['autonomy']:.1f}点 / 自律{peak['n_autonomous']}/{peak['n_total']}回")

    # 最適点より上のレベルで悪化していないか（＝上げすぎの害があるか）を見る
    above = [r for r in rows if r["level"] > peak["level"]]
    if above:
        worst_above = min(above, key=lambda r: r["autonomy"])
        drop = peak["autonomy"] - worst_above["autonomy"]
        if drop > 0:
            print(f"■ さらに上げると悪化する：L{worst_above['level']}（{worst_above['label']}）で "
                  f"{worst_above['autonomy']:.1f}点（ピークから{drop:.1f}点低下）")
            print("  → 自律性は「上げれば上げるほど良い」ではなく、最適点がある")
    else:
        print("■ 最も高いレベルがそのままピークだった（上げすぎの害は観測されず）")

    # ばらつきが最も小さい＝結果が最も安定したレベル
    stable = min(rows, key=lambda r: max(r["autonomy_values"]) - min(r["autonomy_values"]))
    spread = max(stable["autonomy_values"]) - min(stable["autonomy_values"])
    print(f"■ 結果が最も安定したのは L{stable['level']}（{stable['label']}）… "
          f"自律度の幅が{spread}点しかない")

    out_path = os.path.join(args.data_dir, f"threshold_{args.condition}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"condition": args.condition, "threshold": AUTONOMY_THRESHOLD, "levels": rows},
                  f, ensure_ascii=False, indent=2)
    print(f"\n集計を保存しました: {out_path}")


if __name__ == "__main__":
    main()
