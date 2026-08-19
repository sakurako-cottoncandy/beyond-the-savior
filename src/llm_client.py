"""
Claude APIの薄いラッパー。
APIキーが無い/ --mock 指定時は、ダミーの応答を返す「モック」モードで動きます。
（コード全体の動作確認や、API利用料をかけずにフローを試したいときに便利です）
"""

import os
import random

MODEL_NAME = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929")

_MOCK_LINES = [
    "そうなんですね、ちょっと様子を見てみますね。",
    "うーん、それは少し気になりますね…。",
    "私の方で対応しておきますので、大丈夫ですよ。",
    "報告ありがとうございます、確認しておきますね。",
    "……特に何もありません、大丈夫です。",
]


class LLMClient:
    """本番はAnthropic APIを呼び、APIキーが無ければモック応答を返す"""

    def __init__(self, mock: bool = False):
        self.mock = mock or not os.environ.get("ANTHROPIC_API_KEY")
        if not self.mock:
            import anthropic  # 遅延importにして、モックのみ使う場合はパッケージ不要にする

            self._client = anthropic.Anthropic()

    def generate(self, system_prompt: str, user_prompt: str, max_tokens: int = 300) -> str:
        if self.mock:
            return random.choice(_MOCK_LINES)

        response = self._client.messages.create(
            model=MODEL_NAME,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        # テキストブロックを結合して返す
        return "".join(
            block.text for block in response.content if getattr(block, "type", None) == "text"
        ).strip()
