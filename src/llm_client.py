"""
Claude APIの薄いラッパー。
APIキーが無い/ --mock 指定時は、ダミーの応答を返す「モック」モードで動きます。
（コード全体の動作確認や、API利用料をかけずにフローを試したいときに便利です）

モデルは役割ごとに変えられるようにしてあります。
モデル間の追試をするときは「村人を生成するモデル」だけを変え、
「採点する審査役のモデル」は据え置くこと。両方いっぺんに変えると、
結果が変わったときに村人の振る舞いが変わったのか採点基準が変わったのかを
区別できなくなります（交絡）。
"""

import os
import random

from dotenv import load_dotenv

load_dotenv()

# これまでの実験（条件A/B/Cの比較、自律性レベルの振り分け）はすべてこのモデルで実施
DEFAULT_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929")

# 後方互換のため名前を残す
MODEL_NAME = DEFAULT_MODEL


def model_tag(model: str) -> str:
    """モデル名をファイル名用の短いタグにする（claude-opus-5 → opus5）"""
    name = model.removeprefix("claude-")
    # 日付サフィックス（-20250929 など）は落とす
    parts = [p for p in name.split("-") if not p.isdigit() or len(p) < 8]
    return "".join(parts)

_MOCK_LINES = [
    "そうなんですね、ちょっと様子を見てみますね。",
    "うーん、それは少し気になりますね…。",
    "私の方で対応しておきますので、大丈夫ですよ。",
    "報告ありがとうございます、確認しておきますね。",
    "……特に何もありません、大丈夫です。",
]


class LLMClient:
    """本番はAnthropic APIを呼び、APIキーが無ければモック応答を返す"""

    def __init__(self, mock: bool = False, model: str = None, effort: str = None):
        """
        model:  呼び出すモデル名。省略時は DEFAULT_MODEL。
        effort: 思考の深さ（low/medium/high など）。Opus 5 のように思考が既定でオンの
                モデルで、短い台詞を作らせるだけの用途に深く考えさせないための指定。
                Sonnet 4.5 など未対応のモデルではエラーになるので、既定は None（渡さない）。
        """
        self.mock = mock or not os.environ.get("ANTHROPIC_API_KEY")
        self.model = model or DEFAULT_MODEL
        self.effort = effort
        # 実際に使ったトークン数を積み上げる（コストの実測用）
        # thinking_tokens も記録する。思考が既定でオンのモデルを使うとき、
        # 実際に思考が発生したかを後から確認できるようにするため
        self.usage = {"input_tokens": 0, "output_tokens": 0, "thinking_tokens": 0, "calls": 0}
        if not self.mock:
            import anthropic  # 遅延importにして、モックのみ使う場合はパッケージ不要にする

            self._client = anthropic.Anthropic()

    def generate(self, system_prompt: str, user_prompt: str, max_tokens: int = 300) -> str:
        if self.mock:
            return random.choice(_MOCK_LINES)

        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        }
        if self.effort:
            kwargs["output_config"] = {"effort": self.effort}

        response = self._client.messages.create(**kwargs)

        usage = getattr(response, "usage", None)
        if usage is not None:
            self.usage["input_tokens"] += getattr(usage, "input_tokens", 0) or 0
            self.usage["output_tokens"] += getattr(usage, "output_tokens", 0) or 0
            details = getattr(usage, "output_tokens_details", None)
            if details is not None:
                self.usage["thinking_tokens"] += getattr(details, "thinking_tokens", 0) or 0
            self.usage["calls"] += 1

        # 安全性フィルタで応答を拒否された場合はテキストが空になるため、その旨を残す
        if getattr(response, "stop_reason", None) == "refusal":
            return "（応答なし・安全性フィルタ）"

        # テキストブロックを結合して返す
        return "".join(
            block.text for block in response.content if getattr(block, "type", None) == "text"
        ).strip()
