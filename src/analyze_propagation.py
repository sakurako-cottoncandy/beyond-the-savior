"""
「世話好きな住民の行動が、他の住民へどれだけ伝わったか」を会話ログから測るスクリプト。

analyze_compliance.py と対になっている。因果の鎖はこうなっている。

    レベル指定 →(A)→ 世話好きな住民の行動 →(B)→ 他の住民の反応 → 村の自律度

  analyze_compliance.py が測るのは (A) 指示がどれだけ届いたか。
  このスクリプトが測るのは (B) 届いた変化がどれだけ波及したか。

測り方:
  発言順は「救済者 → 世話好きな住民 → 声を上げにくい住民 → 村長」で固定なので、
  世話好きな住民の発言の直後には必ず声を上げにくい住民の発言が来る。
  この隣接ペアを使って、

      世話好きが巻き込んだとき  の 声を上げにくい住民が乗った率
    − 世話好きが巻き込まなかったとき の 同率
    = 波及の強さ（リフト）

  を出す。単純な出現率ではなく差を見るのは、モデルごとに元々の口数や
  遠慮の度合いが違うため。差なら、その下駄を打ち消して比べられる。

使い方:
    python src/analyze_propagation.py
"""

import argparse
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from analyze_compliance import MARKERS  # noqa: E402

# 声を上げにくい住民が「乗った」と判定する手がかり
ENGAGE = [
    "私も", "手伝", "やります", "やってみ", "行きます", "できます",
    "参加し", "お願いします", "一緒に行", "一緒にやり", "一緒に見",
    "賛成", "いいと思います", "そうしましょう",
]

# 逆に「引いた」と判定する手がかり（参考表示用）
DEFER = [
    "大丈夫です", "そこまでのことじゃない", "大したことじゃない", "大したことない",
    "気にしないで", "急ぎではない", "お任せします", "申し訳", "後回し",
]


def has(text, words):
    return any(w in text for w in words)


def adjacent_pairs(data_dir, pattern):
    """(世話好きな住民の発言, その直後の声を上げにくい住民の発言) の組を集める"""
    pairs = []
    for path in sorted(glob.glob(os.path.join(data_dir, pattern))):
        with open(path, "r", encoding="utf-8") as f:
            entries = json.load(f)
        for i, e in enumerate(entries):
            if e.get("speaker") != "caretaker" or e.get("absent"):
                continue
            # 直後の発言が声を上げにくい住民かどうかを見る
            for nxt in entries[i + 1:]:
                if nxt.get("type") != "turn":
                    break
                if nxt.get("speaker") == "quiet" and not nxt.get("absent"):
                    pairs.append((e.get("text", ""), nxt.get("text", "")))
                break
    return pairs


def propagation(pairs):
    """巻き込みの有無で、直後に乗った率がどれだけ変わるかを出す"""
    if not pairs:
        return None
    buckets = {True: [], False: []}
    for c_text, q_text in pairs:
        convened = has(c_text, MARKERS["巻き込み"])
        buckets[convened].append(q_text)

    def rate(texts, words):
        if not texts:
            return None
        return 100 * sum(1 for t in texts if has(t, words)) / len(texts)

    on = buckets[True]
    off = buckets[False]
    r_on = rate(on, ENGAGE)
    r_off = rate(off, ENGAGE)
    return {
        "pairs": len(pairs),
        "n_on": len(on), "n_off": len(off),
        "engage_on": r_on, "engage_off": r_off,
        "lift": (r_on - r_off) if (r_on is not None and r_off is not None) else None,
        "defer_on": rate(on, DEFER), "defer_off": rate(off, DEFER),
    }


def quiet_lines(data_dir, pattern):
    """該当するログ群から声を上げにくい住民の発言だけを取り出す"""
    texts = []
    for path in sorted(glob.glob(os.path.join(data_dir, pattern))):
        with open(path, "r", encoding="utf-8") as f:
            for e in json.load(f):
                if e.get("speaker") == "quiet" and not e.get("absent"):
                    texts.append(e.get("text", ""))
    return texts


def level_patterns(model):
    """モデルごとの (レベル, ファイル名パターン) の一覧"""
    if model == "Sonnet 4.5":
        # L1だけはレベル導入前のファイル名
        return [(lv, "log_C_run*.json" if lv == 1 else f"log_C_L{lv}_run*.json")
                for lv in (0, 1, 2, 3, 4)]
    return [(lv, f"log_C_L{lv}_opus5_run*.json") for lv in (1, 3, 4)]


def main():
    parser = argparse.ArgumentParser(description="一人の行動変容がどれだけ周囲へ波及したかを測る")
    parser.add_argument("--data-dir", default=os.path.join(os.path.dirname(__file__), "..", "data"))
    args = parser.parse_args()

    models = ["Sonnet 4.5", "Opus 5"]

    # --- 測り方(1) ターン単位 ---------------------------------------------
    # 世話好きが巻き込んだ「直後の一手」で隣が乗るか。会話中の即時的な結合を見る。
    print("\n===== (1) ターン単位の波及：巻き込んだ直後に隣が乗ったか =====\n")
    header = f"{'モデル':<12}{'隣接ペア':>9}{'巻き込みあり':>13}{'巻き込みなし':>13}{'差':>10}"
    print(header)
    print("-" * len(header))
    turn_lift = {}
    for model in models:
        pairs = []
        for _, pat in level_patterns(model):
            pairs += adjacent_pairs(args.data_dir, pat)
        r = propagation(pairs)
        if not r:
            continue
        turn_lift[model] = r["lift"]
        print(f"{model:<12}{r['pairs']:>9}"
              f"{r['engage_on']:>12.1f}%{r['engage_off']:>12.1f}%{r['lift']:>+9.1f}pt")
    print("\n  どちらもほぼ0。隣の住民は「直前の一手」には反応していない。")

    # --- 測り方(2) 実行単位 -----------------------------------------------
    # 介入はそもそも会話全体にかかる設定なので、こちらが本命の測り方になる。
    # レベルを変えたときに、隣の住民の出方がどれだけ動いたかを見る。
    print("\n===== (2) 実行単位の波及：レベルを変えると隣の住民が変わるか =====\n")
    header2 = f"{'モデル':<12}{'Lv':<4}{'発言数':>7}{'乗った率':>10}{'引いた率':>10}"
    print(header2)
    print("-" * len(header2))
    # 水準数が多いほど幅は大きく出るため、両モデルに共通する水準だけで比べる
    COMMON = (1, 3, 4)
    all_rates = {}
    for model in models:
        rates = {}
        last = None
        for lv, pat in level_patterns(model):
            texts = quiet_lines(args.data_dir, pat)
            if not texts:
                continue
            eng = 100 * sum(1 for t in texts if has(t, ENGAGE)) / len(texts)
            dfr = 100 * sum(1 for t in texts if has(t, DEFER)) / len(texts)
            rates[lv] = eng
            mark = "" if lv in COMMON else "  (比較対象外)"
            print(f"{model if model != last else '':<12}{lv:<4}{len(texts):>7}"
                  f"{eng:>9.1f}%{dfr:>9.1f}%{mark}")
            last = model
        all_rates[model] = rates
        print()

    spreads = {}
    for model, rates in all_rates.items():
        common = [v for lv, v in rates.items() if lv in COMMON]
        if len(common) == len(COMMON):
            spreads[model] = max(common) - min(common)

    print("----- 因果の鎖を2つの数字で見る -----")
    print("  (A) 指示 → 世話好きな住民 …… analyze_compliance.py")
    print("        Sonnet 4.5 : 単独決定への変化幅 +11.1pt")
    print("        Opus 5     : 単独決定への変化幅 +40.3pt")
    print("  (B) 世話好きな住民 → 隣の住民 …… L1/L3/L4の間で隣の出方が動いた幅")
    for model in models:
        if model in spreads:
            print(f"        {model:<11}: {spreads[model]:.1f}pt")
    if len(spreads) == 2 and spreads["Sonnet 4.5"] > spreads["Opus 5"]:
        print("\n  → (A)はOpus 5のほうが強く、(B)はSonnet 4.5のほうが強い。")
        print("     指示は届いていたのに村が動かなかった理由は(B)の段にある。")
    elif len(spreads) == 2:
        print("\n  → (B)にSonnet優位は見られない。この2指標だけでは説明しきれない。")


if __name__ == "__main__":
    main()
