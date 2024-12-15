from app import db
from datetime import datetime
import secrets

class APIKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    key = db.Column(db.String(64), unique=True, nullable=False)
    name = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)

    @staticmethod
    def generate_key():
        """ユニークなAPIキーを生成"""
        return f"sk_{secrets.token_urlsafe(32)}"