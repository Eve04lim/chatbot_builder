from app import db
from datetime import datetime

class Chatbot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.Text)
    language = db.Column(db.String(10), default='ja')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    settings = db.Column(db.JSON)
    is_active = db.Column(db.Boolean, default=True)

    def update_settings(self, new_settings):
        if self.settings is None:
            self.settings = {}
        self.settings.update(new_settings)