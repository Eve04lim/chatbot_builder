import openai
from flask import current_app
import logging
import os
import random

class OpenAIService:
    def __init__(self):
        self.is_dummy = os.getenv('USE_DUMMY_RESPONSE', 'true').lower() == 'true'
        if not self.is_dummy:
            openai.api_key = current_app.config['OPENAI_API_KEY']
        self.logger = logging.getLogger(__name__)

    def _get_dummy_response(self, user_input):
        """開発用のダミーレスポンスを生成"""
        dummy_responses = [
            f"申し訳ありません。開発モードでの応答です。あなたの質問「{user_input}」について、実際のAPIを使用せずにテスト応答を返しています。",
            "こんにちは！開発モードでの応答です。本番環境では、より適切な応答が返される予定です。",
            f"「{user_input}」についてのご質問ですね。開発中のため、このようなテスト応答を返しています。",
            "開発モードでの応答: チャットボットは正常に動作しています。",
            "テスト応答: この返信は開発用のダミーレスポンスです。本番環境では実際のAIが応答します。"
        ]
        return random.choice(dummy_responses)

    def generate_response(self, user_input, chatbot_settings):
        """
        チャットボットの応答を生成します。
        開発モードの場合はダミーレスポンスを返します。
        
        Args:
            user_input (str): ユーザーからの入力テキスト
            chatbot_settings (dict): チャットボットの設定
        
        Returns:
            str: 生成された応答テキスト
        """
        if self.is_dummy:
            return self._get_dummy_response(user_input)

        try:
            system_prompt = chatbot_settings.get('system_prompt', '')
            temperature = float(chatbot_settings.get('temperature', 0.7))
            max_tokens = int(chatbot_settings.get('max_tokens', 150))
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ]

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            return response.choices[0].message.content

        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            return f"申し訳ありません。エラーが発生しました: {str(e)}"