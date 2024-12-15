# app/routes/api.py
from flask import Blueprint, request, jsonify
from app.models.api_key import APIKey
from app.models.chatbot import Chatbot
from app.models.conversation import Conversation
from app.services.openai_service import OpenAIService
from app import db
from datetime import datetime
from functools import wraps

bp = Blueprint('api', __name__, url_prefix='/api/v1')

def verify_api_key():
    """APIキーの検証"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    
    key = auth_header.split(' ')[1]
    api_key = APIKey.query.filter_by(key=key, is_active=True).first()
    
    if api_key:
        api_key.last_used_at = datetime.utcnow()
        db.session.commit()
        
    return api_key

def require_api_key(f):
    """APIキーを要求するデコレータ"""
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = verify_api_key()
        if not api_key:
            return jsonify({'error': '有効なAPIキーが必要です'}), 401
        return f(*args, **kwargs)
    return decorated

@bp.route('/chatbots', methods=['GET'])
@require_api_key
def get_chatbots():
    """利用可能なチャットボット一覧を取得"""
    try:
        api_key = verify_api_key()
        chatbots = Chatbot.query.filter_by(
            user_id=api_key.user_id,
            is_active=True
        ).all()
        
        return jsonify({
            'chatbots': [{
                'id': bot.id,
                'name': bot.name,
                'description': bot.description,
                'language': bot.language
            } for bot in chatbots]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/chat/<int:chatbot_id>/send', methods=['POST'])
@require_api_key
def send_message(chatbot_id):
    """チャットボットにメッセージを送信"""
    try:
        api_key = verify_api_key()
        chatbot = Chatbot.query.get_or_404(chatbot_id)
        
        # チャットボットの所有者確認
        if chatbot.user_id != api_key.user_id:
            return jsonify({'error': 'アクセス権限がありません'}), 403
        
        # リクエストボディの検証
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'メッセージが必要です'}), 400
        
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
                'api_key_id': api_key.id,
                'ip': request.remote_addr,
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
        return jsonify({'error': str(e)}), 500

@bp.route('/chat/<int:chatbot_id>/history', methods=['GET'])
@require_api_key
def get_history(chatbot_id):
    """会話履歴を取得"""
    try:
        api_key = verify_api_key()
        chatbot = Chatbot.query.get_or_404(chatbot_id)
        
        # チャットボットの所有者確認
        if chatbot.user_id != api_key.user_id:
            return jsonify({'error': 'アクセス権限がありません'}), 403
        
        # ページネーションパラメータ
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)
        
        # 会話履歴の取得
        conversations = Conversation.query.filter_by(
            chatbot_id=chatbot_id
        ).order_by(
            Conversation.timestamp.desc()
        ).paginate(
            page=page,
            per_page=per_page
        )
        
        return jsonify({
            'conversations': [{
                'id': conv.id,
                'user_input': conv.user_input,
                'bot_response': conv.bot_response,
                'timestamp': conv.timestamp.isoformat(),
                'language': conv.language
            } for conv in conversations.items],
            'pagination': {
                'current_page': conversations.page,
                'total_pages': conversations.pages,
                'total_items': conversations.total,
                'has_next': conversations.has_next,
                'has_prev': conversations.has_prev
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# エラーハンドラー
@bp.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'リソースが見つかりません'}), 404

@bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'サーバーエラーが発生しました'}), 500