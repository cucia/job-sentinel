"""
WebSocket handler for real-time dashboard updates.
"""
import json
import time
from threading import Thread
from flask_socketio import SocketIO, emit
from src.core.storage import list_jobs, get_job


def init_socketio(app):
    """Initialize SocketIO with the Flask app."""
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

    @socketio.on('connect')
    def handle_connect():
        print('Client connected')
        emit('connection_response', {'status': 'connected'})

    @socketio.on('disconnect')
    def handle_disconnect():
        print('Client disconnected')

    @socketio.on('request_update')
    def handle_update_request():
        """Handle manual update requests from client."""
        emit('update_requested', {'timestamp': time.time()})

    return socketio


def broadcast_job_update(socketio, job_data):
    """Broadcast job status update to all connected clients."""
    socketio.emit('job_update', {
        'job': job_data,
        'timestamp': time.time()
    })


def broadcast_stats_update(socketio, stats_data):
    """Broadcast statistics update to all connected clients."""
    socketio.emit('stats_update', {
        'stats': stats_data,
        'timestamp': time.time()
    })


def broadcast_agent_activity(socketio, activity_data):
    """Broadcast agent activity to all connected clients."""
    socketio.emit('agent_activity', {
        'agent': activity_data.get('agent', 'Unknown'),
        'action': activity_data.get('action', ''),
        'result': activity_data.get('result', 'UNKNOWN'),
        'timestamp': time.time()
    })


def start_background_updates(socketio, db_path, interval=10):
    """
    Start background thread for periodic updates.

    Args:
        socketio: SocketIO instance
        db_path: Path to database
        interval: Update interval in seconds
    """
    def update_loop():
        from src.core.storage import init_db
        init_db(db_path)

        while True:
            try:
                # Get latest jobs
                recent_jobs = list_jobs(db_path, limit=5)

                # Broadcast to all clients
                socketio.emit('recent_jobs_update', {
                    'jobs': recent_jobs,
                    'timestamp': time.time()
                })

                time.sleep(interval)
            except Exception as e:
                print(f"Background update error: {e}")
                time.sleep(interval)

    thread = Thread(target=update_loop, daemon=True)
    thread.start()
