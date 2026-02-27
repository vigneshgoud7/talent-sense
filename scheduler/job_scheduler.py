"""
Job Scheduler — Manages periodic scraping and monitoring tasks.
"""
from datetime import datetime
import threading
import time

class SimpleScheduler:
    """Simple scheduler for periodic job scraping."""
    
    def __init__(self):
        self.running = False
        self.thread = None
        self.interval_minutes = 60
        self.last_run = None
        self.next_run = None
        self.status = 'stopped'
        self.callbacks = []
    
    def add_callback(self, fn):
        """Add a function to call on each scheduled run."""
        self.callbacks.append(fn)
    
    def start(self, interval_minutes=60):
        """Start the scheduler."""
        self.interval_minutes = interval_minutes
        self.running = True
        self.status = 'running'
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        print(f"[Scheduler] Started with {interval_minutes}min interval")
    
    def stop(self):
        """Stop the scheduler."""
        self.running = False
        self.status = 'stopped'
        print("[Scheduler] Stopped")
    
    def _run_loop(self):
        while self.running:
            self.last_run = datetime.utcnow().isoformat()
            for cb in self.callbacks:
                try:
                    cb()
                except Exception as e:
                    print(f"[Scheduler] Callback error: {e}")
            
            self.next_run = datetime.utcnow().isoformat()
            time.sleep(self.interval_minutes * 60)
    
    def get_status(self):
        return {
            'status': self.status,
            'interval_minutes': self.interval_minutes,
            'last_run': self.last_run,
            'next_run': self.next_run,
            'callbacks_count': len(self.callbacks)
        }

# Global scheduler instance
scheduler = SimpleScheduler()
