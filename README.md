# 救済者 × ガバナンス ― 神が降りなくても、村は回るか

AIエージェント社会シミュレーションハッカソン Vol.2 提出プロジェクト（ソロ参加）

コミュニティに必ずいる「肩書きのない救済者」がいなくなったとき、村は自力で立ち直れるのか？
LLMマルチエージェントで4人の村をシミュレーションし、3つのガバナンス条件（A/B/C）で
同じ危機イベントに対する反応の違いを観測します。

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

## 実行手順

### ステップ1：シミュレーションを回す（A/B/C 3条件それぞれ）

```
python src/simulate.py --condition A
python src/simulate.py --condition B
python src/simulate.py --condition C
```

実行すると、村の会話がターミナルに表示されながら `data/log_A.json` などに保存されます。
1条件あたり数十回API呼び出しが発生するので、実行には数分・多少のAPI利用料がかかります。

APIキーをまだ設定していない場合は、`--mock` を付けるとダミーの会話で動作だけ確認できます。

```
python src/simulate.py --condition A --mock
```

### ステップ2：スコアを計算する（A/B/C それぞれ）

```
python src/score.py --condition A
python src/score.py --condition B
python src/score.py --condition C
```

こちらも `--mock` を付けると、簡易ロジックによる仮スコアで動作確認できます。

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
- [ ] プレゼンテーション資料
- [x] README（このファイル：目的・実行環境・使い方）
- [ ] RESULTS.md（A/B/Cの比較結果・観測されたこと・考察 ─ ダッシュボードを見ながらまとめる）

---

## フォルダ構成

```
hackathon_project/
├── README.md              このファイル
├── requirements.txt        必要なライブラリ一覧
├── .env.example             APIキー設定のテンプレート
├── docs/
│   ├── CONCEPT.md           企画・実験設計の詳細
│   └── PROMPT_DESIGN.md     エージェントの人格設計
├── src/
│   ├── personas.py          4体の人格プロンプト
│   ├── governance.py        A/B/C条件ごとのルール・危機イベント
│   ├── llm_client.py        Claude APIラッパー（--mock対応）
│   ├── simulate.py          シミュレーション実行スクリプト
│   ├── score.py              スコアリングスクリプト
│   └── dashboard.py          Streamlitダッシュボード
└── data/                     実行結果（会話ログ・スコア）が保存される場所
```
