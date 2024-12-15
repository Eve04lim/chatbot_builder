from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # 拡張機能の初期化
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    with app.app_context():
        # Blueprintの登録
        from app.routes import auth, admin, chat
        app.register_blueprint(auth.bp)
        app.register_blueprint(admin.bp)
        app.register_blueprint(chat.bp)
        
        # モデルのインポートとテーブルの作成
        from app.models import user, chatbot, conversation
        db.create_all()
        
        # エラーハンドラーの登録
        from app.routes import errors
        app.register_blueprint(errors.bp)
        
        from app.routes import docs
        app.register_blueprint(docs.bp)
        
        # Swagger UIの登録
        from app.swagger import swagger_ui_blueprint, SWAGGER_URL
        app.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)

    return app

