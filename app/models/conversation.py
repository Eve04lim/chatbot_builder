# app/models/conversation.py
from app import db
from datetime import datetime

class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chatbot_id = db.Column(db.Integer, db.ForeignKey('chatbot.id'), nullable=False)
    user_input = db.Column(db.Text, nullable=False)
    bot_response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    language = db.Column(db.String(10))
    conversation_metadata = db.Column(db.JSON)  # metadataをconversation_metadataに変更
    feedback_score = db.Column(db.Integer)
    is_flagged = db.Column(db.Boolean, default=False)