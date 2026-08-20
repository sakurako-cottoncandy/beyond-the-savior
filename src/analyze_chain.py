"""
「介入 → キーパーソン → 周囲 → 村全体」を、同一の介入差で揃えて比較するスクリプト。

なぜ必要か:
  analyze_compliance.py と analyze_propagation.py はそれぞれ別の定義で数値を出していた
  （前者はL1→L4の変化、後者は3水準のレンジ、村の自律度はL1→L3の変化）。
  定義が揃っていないものを1本の鎖として並べると、比較になっていない。
  そこでここでは、**同じ2水準の差**でA・B・村全体をまとめて計算する。

測り方（すべて「同じ2水準の間で、割合が何ポイント動いたか」で統一する）:
  A … キーパーソン（世話好きな住民）の発言分類が動いた量
        許可要求・巻き込み・単独決定の3分類について |変化| を合計
  B … 周囲（声を上げにくい住民）の発言分類が動いた量
        乗った・引いた の2分類について |変化| を合計
  村 … 村の自律度スコア（LLM採点）の平均が動いた量 |変化|

  Aは3分類・Bは2分類の合計なので、AとBの絶対値どうしは比較しない。
  比較するのは「同じ指標のモデル間の大小」だけである。

使い方:
    python src/analyze_chain.py
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from analyze_compliance import MARKERS, caretaker_lines  # noqa: E402
from analyze_propagation import DEFER, ENGAGE, has, quiet_lines  # noqa: E402

# 比較する2水準の組。L1=初期設定、L3=まず住民同士で相談、L4=自分で判断する
CONTRASTS = [(1, 3), (3, 4), (1, 4)]

MODELS = ["Sonnet 4.5", "Opus 5"]


def log_pattern(model, lv):
    if model == "Sonnet 4.5":
        return "log_C_run*.json" if lv == 1 else f"log_C_L{lv}_run*.json"
    return f"log_C_L{lv}_opus5_run*.json"


def score_path(data_dir, model, lv):
    if model == "Sonnet 4.5":
        name = "scores_C_aggregate.json" if lv == 1 else f"scores_C_L{lv}_aggregate.json"
    else:
        name = f"scores_C_L{lv}_opus5_aggregate.json"
    return os.path.join(data_dir, name)


def rates(texts, groups):
    """発言群に対して、各分類の手がかりが出た割合(%)を返す"""
    if not texts:
        return None
    return {k: 100 * sum(1 for t in texts if has(t, words)) / len(texts)
            for k, words in groups.items()}


def village_mean(data_dir, model, lv):
    p = score_path(data_dir, model, lv)
    if not os.path.exists(p):
        return None
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)["metrics"]["village_autonomy_score"]["mean"]


def total_shift(r_from, r_to):
    """分類ごとの変化の絶対値を合計する"""
    if r_from is None or r_to is None:
        return None
    return sum(abs(r_to[k] - r_from[k]) for k in r_from)


def main():
    parser = argparse.ArgumentParser(description="同一の介入差で鎖の各段を比べる")
    parser.add_argument("--data-dir", default=os.path.join(os.path.dirname(__file__), "..", "data"))
    args = parser.parse_args()

    quiet_groups = {"乗った": ENGAGE, "引いた": DEFER}

    # 各モデル・各水準の割合を先に出しておく
    cache = {}
    for model in MODELS:
        for lv in (1, 3, 4):
            pat = log_pattern(model, lv)
            cache[(model, lv)] = {
                "A": rates(caretaker_lines(args.data_dir, pat), MARKERS),
                "B": rates(quiet_lines(args.data_dir, pat), quiet_groups),
                "V": village_mean(args.data_dir, model, lv),
            }

    print("\n===== 同一の介入差で揃えた比較 =====")
    print("（すべて「同じ2水準の間で割合が何pt動いたか」。数値は変化の絶対量）\n")

    header = (f"{'介入差':<10}{'指標':<26}{'Sonnet 4.5':>12}{'Opus 5':>10}{'大きい側':>12}")
    print(header)
    print("-" * len(header))

    tally = {"A": [], "B": [], "V": []}
    for lo, hi in CONTRASTS:
        label = f"L{lo}→L{hi}"
        for key, name in [("A", "A キーパーソン本人"),
                          ("B", "B 周囲の住民"),
                          ("V", "村全体の自律度")]:
            a = cache[(MODELS[0], lo)][key]
            b = cache[(MODELS[0], hi)][key]
            c = cache[(MODELS[1], lo)][key]
            d = cache[(MODELS[1], hi)][key]
            if key == "V":
                s = abs(b - a) if (a is not None and b is not None) else None
                o = abs(d - c) if (c is not None and d is not None) else None
            else:
                s = total_shift(a, b)
                o = total_shift(c, d)
            if s is None or o is None:
                continue
            winner = MODELS[0] if s > o else MODELS[1]
            tally[key].append(winner)
            print(f"{label if key == 'A' else '':<10}{name:<26}{s:>12.1f}{o:>10.1f}{winner:>12}")
        print()

    print("----- 3つの介入差で、どちらのモデルが大きかったか -----")
    for key, name in [("A", "A キーパーソン本人"),
                      ("B", "B 周囲の住民"),
                      ("V", "村全体の自律度")]:
        counts = {m: tally[key].count(m) for m in MODELS}
        s = " / ".join(f"{m} {counts[m]}回" for m in MODELS)
        print(f"  {name:<26} {s}")

    print("\n  Aが大きい側と村が大きい側は一致していない。")
    print("  Bが大きい側と村が大きい側は、3つのうち2つで一致した。")
    print("  つまり村全体の変化は、Aの大きさよりBの大きさとよく対応している。")
    print("  ただし3点中2点の一致であり、鎖として定量的に成り立つとまでは言えない。")


if __name__ == "__main__":
    main()
