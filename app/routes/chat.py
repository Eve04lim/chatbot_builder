# app/routes/chat.py
from flask import Blueprint, request, jsonify, render_template, current_app
from flask_login import login_required
from app.services.openai_service import OpenAIService
from app.models.chatbot import Chatbot
from app.models.conversation import Conversation
from app import db
from datetime import datetime

bp = Blueprint('chat', __name__, url_prefix='/chat')

@bp.route('/<int:chatbot_id>')
def chat_window(chatbot_id):
    """チャットウィンドウを表示"""
    try:
        chatbot = Chatbot.query.get_or_404(chatbot_id)
        # 過去の会話履歴を取得（最新の10件）
        history = (Conversation.query
                  .filter_by(chatbot_id=chatbot_id)
                  .order_by(Conversation.timestamp.desc())
                  .limit(10)
                  .all())
        history.reverse()  # 古い順に表示
        
        return render_template('chat/chat_window.html', 
                             chatbot=chatbot, 
                             history=history)
    except Exception as e:
        current_app.logger.error(f"Error in chat_window: {str(e)}")
        return jsonify({'error': 'チャットの読み込みに失敗しました'}), 500

@bp.route('/<int:chatbot_id>/send', methods=['POST'])
def send_message(chatbot_id):
    """メッセージを送信して応答を取得"""
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'メッセージが必要です'}), 400

        # チャットボットの取得
        chatbot = Chatbot.query.get_or_404(chatbot_id)
        if not chatbot.is_active:
            return jsonify({'error': 'このチャットボットは現在無効です'}), 400

        # OpenAI APIを使用して応答を生成
        openai_service = OpenAIService()
        response = openai_service.generate_response(
            data['message'],
            chatbot.settings or {}
        )

        # 会話履歴を保存
        conversation = Conversation(
            chatbot_id=chatbot_id,
            user_input=data['message'],
            bot_response=response,
            language=chatbot.language,
            conversation_metadata={
                'ip': request.remote_addr,
                'user_agent': request.user_agent.string,
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        db.session.add(conversation)
        db.session.commit()

        return jsonify({
            'response': response,
            'conversation_id': conversation.id
        })

    except Exception as e:
        current_app.logger.error(f"Error in send_message: {str(e)}")
        return jsonify({'error': 'メッセージの送信に失敗しました'}), 500

@bp.route('/<int:chatbot_id>/history')
def get_history(chatbot_id):
    """会話履歴を取得"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        chatbot = Chatbot.query.get_or_404(chatbot_id)
        conversations = (Conversation.query
                       .filter_by(chatbot_id=chatbot_id)
                       .order_by(Conversation.timestamp.desc())
                       .paginate(page=page, per_page=per_page))
        
        return jsonify({
            'messages': [{
                'id': conv.id,
                'user_input': conv.user_input,
                'bot_response': conv.bot_response,
                'timestamp': conv.timestamp.isoformat(),
                'metadata': conv.conversation_metadata
            } for conv in conversations.items],
            'has_next': conversations.has_next,
            'next_page': conversations.next_num if conversations.has_next else None,
            'total_pages': conversations.pages
        })

    except Exception as e:
        current_app.logger.error(f"Error in get_history: {str(e)}")
        return jsonify({'error': '履歴の取得に失敗しました'}), 500

@bp.route('/<int:chatbot_id>/feedback', methods=['POST'])
def submit_feedback(chatbot_id):
    """会話へのフィードバックを送信"""
    try:
        data = request.get_json()
        if not data or 'conversation_id' not in data or 'score' not in data:
            return jsonify({'error': '必要なパラメータが不足しています'}), 400

        conversation = Conversation.query.get_or_404(data['conversation_id'])
        if conversation.chatbot_id != chatbot_id:
            return jsonify({'error': '無効なリクエストです'}), 400

        # フィードバックを保存
        conversation.feedback_score = data['score']
        if conversation.conversation_metadata is None:
            conversation.conversation_metadata = {}
            
        conversation.conversation_metadata.update({
            'feedback_timestamp': datetime.utcnow().isoformat(),
            'feedback_comment': data.get('comment', '')
        })

        db.session.commit()
        return jsonify({'success': True})

    except Exception as e:
        current_app.logger.error(f"Error in submit_feedback: {str(e)}")
        return jsonify({'error': 'フィードバックの送信に失敗しました'}), 500

@bp.route('/<int:chatbot_id>/settings', methods=['POST'])
def update_settings(chatbot_id):
    """チャットボットの設定を更新"""
    try:
        chatbot = Chatbot.query.get_or_404(chatbot_id)
        data = request.get_json()

        # 設定を更新
        if chatbot.settings is None:
            chatbot.settings = {}
            
        chatbot.settings.update({
            'theme': data.get('theme', 'light'),
            'voice_enabled': data.get('voice_enabled', False),
            'notification_sound': data.get('notification_sound', True)
        })

        db.session.commit()
        return jsonify({'success': True})

    except Exception as e:
        current_app.logger.error(f"Error in update_settings: {str(e)}")
        return jsonify({'error': '設定の更新に失敗しました'}), 500