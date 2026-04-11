from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class Session(db.Model):
    __tablename__ = 'sessions'
    id = db.Column(db.String(255), primary_key=True)
    status = db.Column(db.String(50), default='healthy')  # healthy, looping, drifting, failing
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    events = db.relationship('Event', backref='session', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'status': self.status,
            'last_updated': self.last_updated.isoformat()
        }

class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(255), db.ForeignKey('sessions.id'), nullable=False)
    timestamp = db.Column(db.Float, nullable=False)
    step = db.Column(db.Integer, nullable=False)
    action = db.Column(db.String(100), nullable=False)
    input_data = db.Column(db.Text)
    output_data = db.Column(db.Text)
    metadata_json = db.Column(db.Text) # Stored as JSON string
    
    # Unique constraint to handle duplicate ingestion
    __table_args__ = (
        db.UniqueConstraint('session_id', 'step', 'timestamp', name='_session_step_time_uc'),
    )

    def to_dict(self):
        return {
            'session_id': self.session_id,
            'timestamp': self.timestamp,
            'step': self.step,
            'action': self.action,
            'input': self.input_data,
            'output': self.output_data,
            'metadata': json.loads(self.metadata_json) if self.metadata_json else {}
        }
