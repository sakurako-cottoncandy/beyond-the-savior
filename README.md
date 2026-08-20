# 救済者 × ガバナンス ― 神が降りなくても、村は回るか

AIエージェント社会シミュレーションハッカソン Vol.2 提出プロジェクト（ソロ参加）

コミュニティに必ずいる「肩書きのない救済者」がいなくなったとき、村は自力で立ち直れるのか？
LLMマルチエージェントで4人の村をシミュレーションし、3つのガバナンス条件（A/B/C）で
同じ危機イベントに対する反応の違いを観測します。

## 分かったこと

> **キーパーソン本人を変えることと、集団全体を変えることは、別問題だった。**

同じ介入を加えたとき、キーパーソン本人の変わり方はほぼ同じだったのに、
村全体の結果は大きく分かれました（自律度 +18.0 と −1.2）。
分かれ目に対応していたのは介入の精度ではなく、
**その変化が周囲の住民にどれだけ伝わったか**でした。

ここから、救済者への一点集中には
「その人を動かすと実際に集団が動く」という構造的な合理性が生じうる、
という見方につながります。詳細と根拠は [`RESULTS.md`](RESULTS.md) に、
企画の詳細は [`docs/CONCEPT.md`](docs/CONCEPT.md)、エージェントの人格設計は
[`docs/PROMPT_DESIGN.md`](docs/PROMPT_DESIGN.md) を参照してください。

---

## これは何をするツールか

1. `simulate.py` … 4体のAIエージェント（救済者・世話好きな住民・声を上げにくい住民・村長）に、
   指定したガバナンス条件（A/B/C）のもとで会話させ、ログをJSONで保存する
2. `score.py` … 保存された会話ログをAIに読ませて、「救済者の負荷」「村の自律度」
   「心理的安全性（助けを求められるか／ここにいてよいと思えるか／救済者依存度）」をスコア化する
3. `dashboard.py` … A/B/C 3条件のスコアと会話ログを、ブラウザ上のダッシュボードで比較できるようにする

---

## セットアップ手順（初めての方向け）

### 1. Pythonがインストールされているか確認する

ターミナル（Macなら「ターミナル」、Windowsなら「コマンドプロンプト」または「PowerShell」）を開き、
次のコマンドを実行します。

```
python3 --version
```

`Python 3.10` のようにバージョンが表示されればOKです。表示されない場合は
[python.org](https://www.python.org/downloads/) からインストールしてください。

### 2. このプロジェクトのフォルダに移動する

```
cd hackathon_project
```

### 3. 必要なライブラリをインストールする

```
pip install -r requirements.txt
```

### 4. Claude APIキーを設定する

1. [Anthropic Console](https://console.anthropic.com/) でAPIキーを発行します（アカウント登録が必要です）
2. このフォルダにある `.env.example` を `.env` という名前でコピーします
3. `.env` を開き、`your-api-key-here` の部分を発行したAPIキーに書き換えて保存します

APIキーをまだ用意していなくても、後述の `--mock` オプションで動作確認だけ先に行えます。

---

## 提出時点の実験条件（再現用の記録）

[`RESULTS.md`](RESULTS.md) に載せた数値は、以下の条件で得たものです。

| 項目 | 設定 |
|---|---|
| 村人の発言を生成するモデル | `claude-sonnet-4-5-20250929`（`src/llm_client.py` の既定値） |
| 追試で使ったモデル | `claude-opus-5`（`--model` で指定、`--effort low`） |
| 採点する審査役のモデル | **常に** `claude-sonnet-4-5-20250929`（追試でも据え置き） |
| 1発言あたりの上限 | `max_tokens=300` |
| 構成 | 4エージェント・3フェーズ・各フェーズ3ラウンド |
| 実行回数 | 条件A/B/C比較 15回 ＋ 自律性レベル 25回 ＋ 追試 24回 ＝ **計64回** |

`.env` で `ANTHROPIC_MODEL` を設定すると村人・審査役の既定モデルが両方変わります。
**追試のように村人だけを変えたい場合は `.env` は触らず、`simulate.py --model` を使ってください。**
両方を同時に変えると、結果が変わったときに村人の振る舞いが変わったのか
採点基準が変わったのかを区別できなくなります。

## 実行手順

### ステップ1：シミュレーションを回す（A/B/C 3条件それぞれ）

LLMの出力は毎回ぶれるため、同じ条件を複数回走らせて平均を取ります（推奨は5回）。

```
python src/simulate.py --condition A --runs 5
python src/simulate.py --condition B --runs 5
python src/simulate.py --condition C --runs 5
```

実行すると、村の会話がターミナルに表示されながら `data/log_A_run1.json` 〜 `log_A_run5.json`
に保存されます。1回あたり約30回のAPI呼び出しが発生するので、3条件×5回で計450回程度、
実行には10分前後・数百円程度のAPI利用料がかかります。

`--runs` を省略すると、従来どおり1回だけ `data/log_A.json` に保存します（お試し用）。

APIキーをまだ設定していない場合は、`--mock` を付けるとダミーの会話で動作だけ確認できます。

```
python src/simulate.py --condition A --mock
```

### ステップ2：スコアを計算する（A/B/C それぞれ）

シミュレーションと同じ `--runs` を付けると、全実行分を採点して平均・標準偏差を出します。

```
python src/score.py --condition A --runs 5
python src/score.py --condition B --runs 5
python src/score.py --condition C --runs 5
```

各回のスコアが `data/scores_A_run1.json` 〜 に、集計結果（平均・標準偏差・最小・最大）が
`data/scores_A_aggregate.json` に保存されます。

こちらも `--mock` を付けると、簡易ロジックによる仮スコアで動作確認できます。

### ステップ2.5（発展）：分岐の条件を調べる

5回実行の結果、条件Cは「自律した村」と「依存に戻った村」に分岐しました。その分岐点が
「世話好きな住民が救済者への確認を飛ばして動くかどうか」だったため、そこだけを
0〜4の5段階で変えて、どこで村の運命が切り替わるかを調べられるようにしてあります。

```
python src/simulate.py --condition C --runs 5 --autonomy-level 3
python src/score.py    --condition C --runs 5 --autonomy-level 3
```

L0〜L4まで一通り実行したら、次のコマンドで閾値と最適点を集計します。

```
python src/analyze_threshold.py
```

（途中で止まってしまったときは `--start-run 3` のように指定すると続きから再開できます）

### ステップ3：ダッシュボードを開く

```
streamlit run src/dashboard.py
```

自動的にブラウザが開き、A/B/C の比較ダッシュボードが表示されます。
開かない場合は、ターミナルに表示される `http://localhost:8501` にアクセスしてください。

---

## 困ったときは

- **「ModuleNotFoundError」と出る** → `pip install -r requirements.txt` を再実行してください
- **「AuthenticationError」やAPIキー関連のエラーが出る** → `.env` のAPIキーが正しくコピーされているか確認してください
- **モデル名のエラーが出る** → `.env` の `ANTHROPIC_MODEL` を、[Anthropicのドキュメント](https://docs.claude.com)に載っている最新のモデル名に書き換えてください
- **会話がイメージと違う** → `docs/PROMPT_DESIGN.md` の性格設定を直接編集すればすぐ反映されます（`src/personas.py` を編集）

---

## ハッカソン提出物チェックリスト

- [x] GitHubリポジトリ（このプロジェクト）
- [x] プレゼンテーション資料（[`docs/Beyond_the_Savior.pptx`](docs/Beyond_the_Savior.pptx)）
- [x] README（このファイル：目的・実行環境・使い方）
- [x] RESULTS.md（A/B/Cの比較結果・観測されたこと・考察 ─ ダッシュボードを見ながらまとめる）

---

## フォルダ構成

```
hackathon_project/
├── README.md              このファイル
├── requirements.txt        必要なライブラリ一覧
├── .env.example             APIキー設定のテンプレート
├── RESULTS.md             A/B/Cの比較結果・観測されたこと・考察
├── docs/
│   ├── CONCEPT.md           企画・実験設計の詳細
│   ├── PROMPT_DESIGN.md     エージェントの人格設計
│   └── Beyond_the_Savior.pptx  プレゼンテーション資料
├── slides/                  プレゼン資料(pptx)を生成するスクリプト
├── src/
│   ├── personas.py          4体の人格プロンプト
│   ├── governance.py        A/B/C条件ごとのルール・危機イベント
│   ├── llm_client.py        Claude APIラッパー（--mock対応）
│   ├── simulate.py          シミュレーション実行スクリプト（--runsで複数回実行）
│   ├── score.py              スコアリングスクリプト（--runsで平均・標準偏差を集計）
│   ├── analyze_threshold.py  自律性レベル別の閾値・最適点を集計
│   └── dashboard.py          Streamlitダッシュボード
└── data/                     実行結果が保存される場所
    ├── log_A_run1.json 〜      各回の会話ログ
    ├── scores_A_run1.json 〜   各回のスコア
    └── scores_A_aggregate.json  平均・標準偏差の集計結果
```
