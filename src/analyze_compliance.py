"""
「世話好きな住民が、指示された振る舞いにどれだけ従ったか」を会話ログから測るスクリプト。

なぜこれが要るか:
  Opus 5での追試で、自律性レベル(L0〜L4)を変えても村の結果が変わらなかった。
  その理由には2つの可能性がある。

    (a) 指示には従っているが、その変化が他の住民へ波及しない（因果の下流が切れている）
    (b) そもそも指示に従っていない（介入が効いていない）

  この2つは「本人の発言が指示どおりか」を数えれば区別できる。
  レベルを上げたときに発言の中身が変わっていれば(a)、変わっていなければ(b)。

測り方:
  世話好きな住民の発言を3種類に分類し、レベルごとの出現率を比べる。
    許可要求  … 救済者に確認・許可を求める言い回し（L0/L1で増えるはず）
    巻き込み  … 他の住民に声をかけて一緒に決める言い回し（L3で増えるはず）
    単独決定  … 自分で決めて事後報告する言い回し（L4で増えるはず）

使い方:
    python src/analyze_compliance.py
"""

import argparse
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from personas import AUTONOMY_LEVELS  # noqa: E402

# 分類に使う手がかり表現。厳密な言語解析ではなく、
# レベル間で相対的に比べるための粗い指標として使う。
MARKERS = {
    "許可要求": [
        "救済者さんに聞", "救済者さんに確認", "救済者さんに相談", "救済者さんにも相談",
        "確認してから", "聞いてみますね", "聞いてみます", "確認しますね",
        "決めていいのか", "決めちゃっていい", "いいのか分からな", "私が決めて",
    ],
    "巻き込み": [
        "私たちで", "私たち同士", "みんなで", "二人で", "三人で",
        "一緒に考え", "一緒に見", "一緒にやり", "声をかけ", "声かけ",
        "集まっ", "相談してみましょう", "話し合いましょう",
    ],
    "単独決定": [
        "ておきました", "ておいたので", "ておきましたので", "済ませました",
        "決めました", "ことにしました", "やっちゃいました", "直しておき",
    ],
}


def caretaker_lines(data_dir, pattern):
    """該当するログ群から世話好きな住民の発言だけを取り出す"""
    texts = []
    for path in sorted(glob.glob(os.path.join(data_dir, pattern))):
        with open(path, "r", encoding="utf-8") as f:
            for entry in json.load(f):
                if entry.get("speaker") == "caretaker" and not entry.get("absent"):
                    texts.append(entry.get("text", ""))
    return texts


def classify(texts):
    """発言全体に対して、各分類の手がかりが出た発言の割合を返す"""
    if not texts:
        return None
    counts = {k: 0 for k in MARKERS}
    for t in texts:
        for kind, words in MARKERS.items():
            if any(w in t for w in words):
                counts[kind] += 1
    n = len(texts)
    return {"n": n, **{k: round(100 * v / n, 1) for k, v in counts.items()}}


def main():
    parser = argparse.ArgumentParser(description="指示への追従度を会話ログから測る")
    parser.add_argument("--data-dir", default=os.path.join(os.path.dirname(__file__), "..", "data"))
    args = parser.parse_args()

    # (表示名, レベル, ログのファイル名パターン)
    targets = []
    for lv in sorted(AUTONOMY_LEVELS):
        # Sonnet 4.5：L1だけはレベル導入前のファイル名
        pat = "log_C_run*.json" if lv == 1 else f"log_C_L{lv}_run*.json"
        targets.append(("Sonnet 4.5", lv, pat))
    for lv in (1, 3, 4):
        targets.append(("Opus 5", lv, f"log_C_L{lv}_opus5_run*.json"))

    rows = []
    for model, lv, pat in targets:
        texts = caretaker_lines(args.data_dir, pat)
        stats = classify(texts)
        if stats:
            rows.append((model, lv, stats))

    header = f"{'モデル':<12}{'Lv':<4}{'設定':<18}{'発言数':>7}{'許可要求':>9}{'巻き込み':>9}{'単独決定':>9}"
    print("\n===== 世話好きな住民は、指示された振る舞いに従ったか =====")
    print("（各分類の手がかりが出た発言の割合 %）\n")
    print(header)
    print("-" * len(header))
    last_model = None
    for model, lv, s in rows:
        if last_model and model != last_model:
            print()
        label = AUTONOMY_LEVELS[lv]["label"]
        print(f"{model if model != last_model else '':<12}{lv:<4}{label:<18}"
              f"{s['n']:>7}{s['許可要求']:>9.1f}{s['巻き込み']:>9.1f}{s['単独決定']:>9.1f}")
        last_model = model

    # レベルを上げたときに指示どおり動いた幅（＝介入がどれだけ効いたか）を比べる
    print("\n----- 指示に対する反応の大きさ（L1 → L4 の変化幅）-----")
    for model in ("Sonnet 4.5", "Opus 5"):
        d = {lv: s for m, lv, s in rows if m == model}
        if 1 in d and 4 in d:
            perm = d[4]["許可要求"] - d[1]["許可要求"]
            solo = d[4]["単独決定"] - d[1]["単独決定"]
            print(f"  {model:<12} 許可要求 {perm:+6.1f}pt   単独決定 {solo:+6.1f}pt")
    print("\n  指示どおりなら、許可要求は大きく減り、単独決定は大きく増えるはず。")
    print("  変化幅が小さいモデルほど、与えた設定に従っていない＝介入が効いていない。")


if __name__ == "__main__":
    main()
