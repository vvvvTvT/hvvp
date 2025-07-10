from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Request(db.Model):
    __tablename__ = 'request'
    id = db.Column(db.Integer, primary_key=True)
    method = db.Column(db.String(10), nullable=False)
    url = db.Column(db.Text, nullable=False)
    headers = db.Column(db.Text)  # JSON字符串
    body = db.Column(db.Text)
    interval = db.Column(db.Integer, nullable=False, default=5)  # 分钟
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    results = db.relationship('Result', backref='request', lazy=True, cascade="all, delete-orphan")
    
class Result(db.Model):
    __tablename__ = 'result'
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('request.id'), nullable=False)
    status_code = db.Column(db.Integer)
    response_body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
