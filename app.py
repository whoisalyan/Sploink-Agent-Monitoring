from flask import Flask, request, jsonify, render_template, redirect, url_for
from models import db, Session, Event
from detection import analyze_session
import json
import asyncio
from datetime import datetime
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sploink.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

@app.template_filter('from_json')
def from_json_filter(value):
    return json.loads(value) if value else {}

db.init_app(app)

# Initialize database
with app.app_context():
    db.create_all()
    # Enable WAL mode for better concurrency in SQLite
    db.session.execute(db.text("PRAGMA journal_mode=WAL;"))

@app.route('/')
def index():
    sessions = Session.query.order_by(Session.last_updated.desc()).all()
    return render_template('index.html', sessions=sessions)

@app.route('/session/<session_id>')
def session_detail(session_id):
    session_obj = Session.query.get_or_404(session_id)
    events = Event.query.filter_by(session_id=session_id).order_by(Event.step, Event.timestamp).all()
    
    # Run detection
    status = analyze_session(events)
    if status != session_obj.status:
        session_obj.status = status
        db.session.commit()
    
    # Calculate stats
    success_count = 0
    for e in events:
        meta = json.loads(e.metadata_json) if e.metadata_json else {}
        if meta.get('status') == 'success':
            success_count += 1
    success_rate = (success_count / len(events) * 100) if events else 0
    
    return render_template('session_detail.html', session=session_obj, events=events, success_rate=success_rate)

@app.route('/events', methods=['POST'])
async def ingest_event():
    """
    Async endpoint for high-concurrency event ingestion.
    """
    data = request.json
    if not data:
        return jsonify({"error": "Invalid data"}), 400

    session_id = data.get('session_id')
    if not session_id:
        return jsonify({"error": "Missing session_id"}), 400

    # Ensure session exists
    # We do this in a thread-safe way or just handle the error
    try:
        # Wrap sync DB operations in to_thread to keep the event loop non-blocking
        await asyncio.to_thread(_save_event, data)
        return jsonify({"status": "received"}), 201
    except IntegrityError:
        # Handle duplicates gracefully
        return jsonify({"status": "already_received"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def _save_event(data):
    """
    Helper to save event to DB (run in a separate thread).
    """
    with app.app_context():
        session_id = data.get('session_id')
        session_obj = Session.query.get(session_id)
        if not session_obj:
            session_obj = Session(id=session_id)
            db.session.add(session_obj)
        
        event = Event(
            session_id=session_id,
            timestamp=data.get('timestamp'),
            step=data.get('step'),
            action=data.get('action'),
            input_data=data.get('input'),
            output_data=data.get('output'),
            metadata_json=json.dumps(data.get('metadata', {}))
        )
        db.session.add(event)
        session_obj.last_updated = datetime.utcnow()
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
