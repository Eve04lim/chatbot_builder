# app/routes/admin.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.api_key import APIKey
from app.models.chatbot import Chatbot
from app.models.conversation import Conversation
from app import db
from datetime import datetime, timedelta
from sqlalchemy import func

from app.models.user import User

bp = Blueprint('admin', __name__, url_prefix='/admin')

@bp.route('/dashboard')
@login_required
def dashboard():
    # ユーザーのチャットボット一覧を取得
    chatbots = Chatbot.query.filter_by(user_id=current_user.id).order_by(Chatbot.created_at.desc()).all()
    
    # 今月の会話数を計算
    start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    total_conversations = Conversation.query.join(Chatbot).filter(
        Chatbot.user_id == current_user.id,
        Conversation.timestamp >= start_of_month
    ).count()
    
    return render_template('admin/dashboard.html',
                         chatbots=chatbots,
                         total_conversations=total_conversations)

@bp.route('/chatbot/new', methods=['GET', 'POST'])
@login_required
def create_chatbot():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        language = request.form.get('language', 'ja')
        
        if not name:
            flash('チャットボット名は必須です。', 'danger')
            return redirect(url_for('admin.create_chatbot'))
            
        chatbot = Chatbot(
            name=name,
            description=description,
            language=language,
            user_id=current_user.id,
            settings={
                'system_prompt': request.form.get('system_prompt', ''),
                'temperature': float(request.form.get('temperature', 0.7)),
                'max_tokens': int(request.form.get('max_tokens', 150))
            },
            is_active=True
        )
        
        try:
            db.session.add(chatbot)
            db.session.commit()
            flash('チャットボットを作成しました。', 'success')
            return redirect(url_for('admin.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('チャットボットの作成に失敗しました。', 'danger')
            return redirect(url_for('admin.create_chatbot'))
        
    return render_template('admin/create_chatbot.html')

@bp.route('/chatbot/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_chatbot(id):
    chatbot = Chatbot.query.get_or_404(id)
    
    if chatbot.user_id != current_user.id:
        flash('このチャットボットを編集する権限がありません。', 'danger')
        return redirect(url_for('admin.dashboard'))
        
    if request.method == 'POST':
        chatbot.name = request.form.get('name')
        chatbot.description = request.form.get('description')
        chatbot.language = request.form.get('language', 'ja')
        chatbot.is_active = request.form.get('is_active') == 'true'
        chatbot.settings = {
            'system_prompt': request.form.get('system_prompt', ''),
            'temperature': float(request.form.get('temperature', 0.7)),
            'max_tokens': int(request.form.get('max_tokens', 150))
        }
        
        try:
            db.session.commit()
            flash('チャットボットを更新しました。', 'success')
            return redirect(url_for('admin.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('チャットボットの更新に失敗しました。', 'danger')
            
    return render_template('admin/edit_chatbot.html', chatbot=chatbot)

@bp.route('/chatbot/<int:id>/delete', methods=['POST'])
@login_required
def delete_chatbot(id):
    chatbot = Chatbot.query.get_or_404(id)
    
    if chatbot.user_id != current_user.id:
        flash('このチャットボットを削除する権限がありません。', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    try:
        db.session.delete(chatbot)
        db.session.commit()
        flash('チャットボットを削除しました。', 'success')
    except Exception as e:
        db.session.rollback()
        flash('チャットボットの削除に失敗しました。', 'danger')
        
    return redirect(url_for('admin.dashboard'))

# app/routes/admin.py に以下を追加

@bp.route('/settings', methods=['GET'])
@login_required
def settings():
    """ユーザー設定ページを表示"""
    return render_template('admin/settings.html')

@bp.route('/settings/profile', methods=['POST'])
@login_required
def update_profile():
    """プロフィール情報の更新"""
    try:
        username = request.form.get('username')
        email = request.form.get('email')

        if not username or not email:
            flash('ユーザー名とメールアドレスは必須です。', 'danger')
            return redirect(url_for('admin.settings'))

        # メールアドレスの重複チェック
        if email != current_user.email and User.query.filter_by(email=email).first():
            flash('このメールアドレスは既に使用されています。', 'danger')
            return redirect(url_for('admin.settings'))

        current_user.username = username
        current_user.email = email
        db.session.commit()

        flash('プロフィールを更新しました。', 'success')
    except Exception as e:
        db.session.rollback()
        flash('プロフィールの更新に失敗しました。', 'danger')

    return redirect(url_for('admin.settings'))

@bp.route('/settings/password', methods=['POST'])
@login_required
def update_password():
    """パスワードの更新"""
    try:
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if not all([current_password, new_password, confirm_password]):
            flash('すべての項目を入力してください。', 'danger')
            return redirect(url_for('admin.settings'))

        if not current_user.check_password(current_password):
            flash('現在のパスワードが正しくありません。', 'danger')
            return redirect(url_for('admin.settings'))

        if new_password != confirm_password:
            flash('新しいパスワードが一致しません。', 'danger')
            return redirect(url_for('admin.settings'))

        current_user.set_password(new_password)
        db.session.commit()

        flash('パスワードを更新しました。', 'success')
    except Exception as e:
        db.session.rollback()
        flash('パスワードの更新に失敗しました。', 'danger')

    return redirect(url_for('admin.settings'))

@bp.route('/settings/api', methods=['POST'])
@login_required
def update_api_settings():
    """API設定の更新"""
    try:
        api_key = request.form.get('openai_api_key')
        if api_key:
            current_user.api_key = api_key
            db.session.commit()
            flash('API設定を更新しました。', 'success')
        else:
            flash('APIキーを入力してください。', 'danger')
    except Exception as e:
        db.session.rollback()
        flash('API設定の更新に失敗しました。', 'danger')

    return redirect(url_for('admin.settings'))

@bp.route('/settings/notifications', methods=['POST'])
@login_required
def update_notifications():
    """通知設定の更新"""
    try:
        email_notifications = request.form.get('email_notifications') == 'on'
        web_notifications = request.form.get('web_notifications') == 'on'

        current_user.email_notifications = email_notifications
        current_user.web_notifications = web_notifications
        db.session.commit()

        flash('通知設定を更新しました。', 'success')
    except Exception as e:
        db.session.rollback()
        flash('通知設定の更新に失敗しました。', 'danger')

    return redirect(url_for('admin.settings'))

@bp.route('/api-keys')
@login_required
def api_keys():
    """APIキー管理ページを表示"""
    api_keys = APIKey.query.filter_by(user_id=current_user.id).all()
    return render_template('admin/api_keys.html', api_keys=api_keys)

@bp.route('/api-keys/create', methods=['POST'])
@login_required
def create_api_key():
    """新しいAPIキーを生成"""
    try:
        name = request.form.get('name', 'My API Key')
        api_key = APIKey(
            user_id=current_user.id,
            key=APIKey.generate_key(),
            name=name
        )
        db.session.add(api_key)
        db.session.commit()
        flash('新しいAPIキーを生成しました。このキーは再表示できないので、必ず保存してください。', 'success')
        return render_template('admin/api_key_created.html', api_key=api_key)
    except Exception as e:
        db.session.rollback()
        flash('APIキーの生成に失敗しました。', 'danger')
        return redirect(url_for('admin.api_keys'))

@bp.route('/api-keys/<int:key_id>/deactivate', methods=['POST'])
@login_required
def deactivate_api_key(key_id):
    """APIキーを無効化"""
    api_key = APIKey.query.get_or_404(key_id)
    if api_key.user_id != current_user.id:
        flash('無効な操作です。', 'danger')
        return redirect(url_for('admin.api_keys'))
    
    api_key.is_active = False
    db.session.commit()
    flash('APIキーを無効化しました。', 'success')
    return redirect(url_for('admin.api_keys'))