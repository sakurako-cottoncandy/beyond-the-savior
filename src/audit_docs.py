"""
提出物（RESULTS.md / README.md / スライド本文）を別のモデルに読ませて監査させるスクリプト。

なぜ必要か:
  文書を書いた本人（あるいは書いたAI）が自分で見直すと、思い込みが残ったまま
  「一致している」と判断してしまう。実際、実行回数を二重計上していた誤りは
  自分の点検では見つからず、別の切り口から数え直して初めて見つかった。
  そこで、経緯を一切知らないモデルに白紙の状態で読ませ、
  データから導いた真値と突き合わせてもらう。

特徴:
  - 数値の真値は data/ から機械的に算出して一緒に渡す。
    モデルに数えさせるのではなく「この真値と文書が合っているか」を照合させる。
  - 監査するモデルと、シミュレーションで使ったモデルは別でよい（既定は Fable 5）。

使い方:
    python src/audit_docs.py
    python src/audit_docs.py --model claude-opus-5   # 別のモデルで監査する
    python src/audit_docs.py --dry-run               # 送る内容だけ確認してAPIは呼ばない
"""

import argparse
import glob
import io
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

ROOT = os.path.join(os.path.dirname(__file__), "..")
DATA = os.path.join(ROOT, "data")

SYSTEM_PROMPT = """あなたは研究成果物の査読者です。ハッカソン提出前の最終監査を行います。

渡されるもの:
  1. データから機械的に算出した「真値」
  2. 提出物の全文（RESULTS.md / README.md / 発表スライドの本文）

あなたの仕事は、以下の観点で問題を洗い出すことです。

【A】数値の誤り
  真値と文書の数値が食い違っていないか。
  複数の文書の間で同じ数値が違って書かれていないか。
  数え方の誤り（重複して数えている、母数が違う、定義がずれている）がないか。

【B】観測・解釈・仮説の混同
  データで示せる範囲を超えた断定をしていないか。
  「AだからB」という因果を、相関しか示せていないのに主張していないか。
  n数が小さいのに一般化していないか。
  2条件しか比べていないのに「モデル一般」の性質として語っていないか。

【C】定義の不整合
  同じ指標が、場所によって違う定義で計算されていないか。
  比較している数値どうしの定義が揃っているか。

【D】文書間の矛盾
  RESULTS.md・README・スライドで、結論や強調点が食い違っていないか。

【E】読み手を誤解させる表現
  厳密には正しいが、誤読されやすい書き方になっていないか。

出力の形式:
  重要度（高／中／低）ごとに、次の形で列挙してください。
    - 該当箇所（ファイル名と、原文の引用）
    - 何が問題か
    - どう直すべきか（具体的な修正文案）
  問題が見つからない観点については「問題なし」と明記してください。
  忖度は不要です。厳しく指摘してください。
  逆に、根拠なく問題を作り出すこともしないでください。"""


def ground_truth():
    """data/ から機械的に真値を算出する。モデルに数えさせないための材料。"""
    out = []
    logs = sorted(glob.glob(os.path.join(DATA, "log_*.json")))
    out.append(f"会話ログの実ファイル数: {len(logs)} 本")
    out.append("  内訳（ファイル名パターン別、重複あり得るので注意）:")
    for label, pat in [
        ("条件A/B/C比較", "log_[ABC]_run*.json"),
        ("自律性レベル L0/L2/L3/L4", "log_C_L[0234]_run*.json"),
        ("自律性レベル L1（条件Cと同一ファイル）", "log_C_run*.json"),
        ("追試 Opus5", "log_C_L*_opus5_run*.json"),
    ]:
        n = len(glob.glob(os.path.join(DATA, pat)))
        out.append(f"    {label}: {n} 本")
    out.append("  ※ 条件Cの5本は自律性レベルL1としても使い回しているため、"
               "上の内訳を単純に足すと二重計上になる")

    out.append("\n採点結果（村の自律度スコア）:")
    files = [
        ("条件A", "scores_A_aggregate.json"), ("条件B", "scores_B_aggregate.json"),
        ("条件C = レベルL1", "scores_C_aggregate.json"),
        ("Sonnet L0", "scores_C_L0_aggregate.json"),
        ("Sonnet L2", "scores_C_L2_aggregate.json"),
        ("Sonnet L3", "scores_C_L3_aggregate.json"),
        ("Sonnet L4", "scores_C_L4_aggregate.json"),
        ("Opus L1", "scores_C_L1_opus5_aggregate.json"),
        ("Opus L3", "scores_C_L3_opus5_aggregate.json"),
        ("Opus L4", "scores_C_L4_opus5_aggregate.json"),
    ]
    for label, fn in files:
        p = os.path.join(DATA, fn)
        if not os.path.exists(p):
            continue
        d = json.load(io.open(p, encoding="utf-8"))
        m = d["metrics"]
        v = m["village_autonomy_score"]
        n_auto = sum(1 for x in v["values"] if x >= 60)
        out.append(
            f"  {label:<18} n={d['n_runs']}  自律度 平均{v['mean']:.1f} 標準偏差{v['stdev']:.1f} "
            f"各回{v['values']}  自律(60以上){n_auto}/{len(v['values'])}回  "
            f"負荷{m['savior_load_percent']['mean']:.1f}  依存{m['savior_dependency']['mean']:.1f}"
        )
        if d.get("judge_model"):
            out.append(f"      採点モデル: {d['judge_model']}")

    # 鎖の値（analyze_chain.py と同じ計算）
    try:
        from analyze_chain import MODELS, log_pattern, rates, total_shift, village_mean
        from analyze_compliance import MARKERS, caretaker_lines
        from analyze_propagation import DEFER, ENGAGE, quiet_lines
        qg = {"乗った": ENGAGE, "引いた": DEFER}
        out.append("\n同一の介入差で揃えた鎖の値（analyze_chain.py の計算）:")
        for model in MODELS:
            for lo, hi in [(1, 3), (3, 4), (1, 4)]:
                a = total_shift(rates(caretaker_lines(DATA, log_pattern(model, lo)), MARKERS),
                                rates(caretaker_lines(DATA, log_pattern(model, hi)), MARKERS))
                b = total_shift(rates(quiet_lines(DATA, log_pattern(model, lo)), qg),
                                rates(quiet_lines(DATA, log_pattern(model, hi)), qg))
                v = village_mean(DATA, model, hi) - village_mean(DATA, model, lo)
                out.append(f"  {model:<12} L{lo}→L{hi}: A={a:.1f}  B={b:.1f}  村={v:+.1f}")
    except Exception as e:
        out.append(f"\n（鎖の値の算出に失敗: {e}）")

    return "\n".join(out)


class SlideExtractionError(RuntimeError):
    """スライド本文を取り出せなかったときに投げる。

    本文が欠けたまま監査すると「スライドには問題なし」という誤った結論が出るため、
    黙って続行させず必ず止める。
    """


def slide_text():
    """発表スライドの本文をテキストで取り出す。失敗したら例外にする。"""
    pptx = os.path.join(ROOT, "docs", "Beyond_the_Savior.pptx")
    if not os.path.exists(pptx):
        raise SlideExtractionError(f"スライドが見つかりません: {pptx}")

    try:
        r = subprocess.run(["markitdown", pptx], capture_output=True,
                           text=True, encoding="utf-8", errors="replace")
    except FileNotFoundError:
        raise SlideExtractionError(
            "markitdown が見つかりません。監査にはスライド本文が必要です。\n"
            "  pip install -r requirements.txt を実行してください。"
        )

    if r.returncode != 0:
        raise SlideExtractionError(
            f"markitdown がスライドの読み取りに失敗しました（終了コード {r.returncode}）。\n"
            f"  {(r.stderr or '').strip()[:300]}"
        )

    text = (r.stdout or "").strip()
    # 22枚ぶんの本文があれば数千文字になる。極端に短いときは抽出に失敗している
    if len(text) < 1000:
        raise SlideExtractionError(
            f"スライド本文が短すぎます（{len(text)}文字）。抽出に失敗した可能性があります。"
        )
    return text


def main():
    parser = argparse.ArgumentParser(description="提出物を別モデルに監査させる")
    parser.add_argument("--model", default="claude-fable-5")
    parser.add_argument("--dry-run", action="store_true", help="APIを呼ばず送信内容だけ表示")
    parser.add_argument("--max-tokens", type=int, default=48000,
                        help="出力の上限。思考トークンも含まれるので大きめに取る")
    parser.add_argument("--out", default=os.path.join(ROOT, "audit_report.md"))
    args = parser.parse_args()

    truth = ground_truth()
    try:
        slides = slide_text()
    except SlideExtractionError as e:
        print(f"エラー: {e}", file=sys.stderr)
        print("\nスライド本文を含めずに監査すると、スライドの問題を見落としたまま"
              "「問題なし」と報告されてしまうため、ここで中止します。", file=sys.stderr)
        sys.exit(1)

    docs = {
        "RESULTS.md": io.open(os.path.join(ROOT, "RESULTS.md"), encoding="utf-8").read(),
        "README.md": io.open(os.path.join(ROOT, "README.md"), encoding="utf-8").read(),
        "発表スライドの本文": slides,
    }
    print(f"スライド本文: {len(slides):,} 文字を取得")

    user = ["# データから算出した真値\n", truth, "\n\n# 提出物の全文\n"]
    for name, body in docs.items():
        user.append(f"\n## ===== {name} =====\n\n{body}\n")
    user_prompt = "".join(user)

    print(f"監査モデル: {args.model}")
    print(f"送信する文字数: {len(user_prompt):,}")
    if args.dry_run:
        print("\n--- 真値の部分 ---")
        print(truth)
        return

    import anthropic
    client = anthropic.Anthropic()
    print("監査中...（数分かかります）\n")

    # 思考トークンも max_tokens に含まれる。監査は思考量が多いので上限を大きく取る
    # （16000だと思考だけで使い切ってしまい、本文が1文字も返らなかった）
    with client.messages.stream(
        model=args.model,
        max_tokens=args.max_tokens,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    ) as stream:
        msg = stream.get_final_message()

    if getattr(msg, "stop_reason", None) == "refusal":
        print("安全性フィルタにより応答が拒否されました。")
        return

    report = "".join(b.text for b in msg.content if getattr(b, "type", None) == "text")

    u = msg.usage
    details = getattr(u, "output_tokens_details", None)
    think = getattr(details, "thinking_tokens", 0) if details else 0
    print(f"stop_reason: {msg.stop_reason}")
    print(f"消費: 入力 {u.input_tokens:,} / 出力 {u.output_tokens:,}（うち思考 {think:,}）トークン\n")

    if not report.strip():
        print("本文が空でした。max_tokens を増やして再実行してください"
              f"（現在 {args.max_tokens:,}、うち思考が {think:,} を消費）。")
        return

    print(report)
    io.open(args.out, "w", encoding="utf-8").write(
        f"# 提出物の外部監査レポート\n\n"
        f"- 監査モデル: `{args.model}`\n"
        f"- 入力 {u.input_tokens:,} トークン / 出力 {u.output_tokens:,} トークン"
        f"（うち思考 {think:,}）\n\n---\n\n{report}\n"
    )
    print(f"\n\n保存しました: {args.out}")


if __name__ == "__main__":
    main()
