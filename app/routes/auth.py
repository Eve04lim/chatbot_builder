from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User
from app import db

bp = Blueprint('auth', __name__)

@bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
    return redirect(url_for('auth.login'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        
        # バリデーション
        error = None
        if not username:
            error = 'ユーザー名は必須です。'
        elif not email:
            error = 'メールアドレスは必須です。'
        elif not password:
            error = 'パスワードは必須です。'
        elif password != password_confirm:
            error = 'パスワードが一致しません。'
        elif User.query.filter_by(email=email).first():
            error = 'このメールアドレスは既に登録されています。'
        
        if error is None:
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('登録が完了しました。ログインしてください。')
            return redirect(url_for('auth.login'))
        
        flash(error)
    
    return render_template('auth/register.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember', False) == 'true'
        
        error = None
        user = User.query.filter_by(email=email).first()
        
        if user is None:
            error = 'メールアドレスが正しくありません。'
        elif not user.check_password(password):
            error = 'パスワードが正しくありません。'
            
        if error is None:
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            if not next_page:
                next_page = url_for('admin.dashboard')
            return redirect(next_page)
            
        flash(error)
    
    return render_template('auth/login.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('ログアウトしました。')
    return redirect(url_for('auth.login'))