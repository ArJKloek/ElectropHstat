import time

class monoTimer:
    def __init__(self):
        self.start_time = None
        self.last_lap_time = None
        self.running = False

    def start(self):
        """Start or restart the timer."""
        now = time.monotonic()
        self.start_time = now
        self.last_lap_time = now
        self.running = True
        print("Timer started.")

    def stop(self):
        """Stop the timer and return the elapsed time in seconds."""
        if self.start_time is None:
            print("Warning: Timer was never started.")
            return 0
        if not self.running:
            print("Warning: Timer was already stopped.")
            return 0
        elapsed = time.monotonic() - self.start_time
        self.running = False
        print(f"Timer stopped. Elapsed: {elapsed:.4f} seconds")
        return elapsed

    def elapsed(self):
        """Get the current elapsed time without stopping."""
        if self.start_time is None:
            return 0
        if not self.running:
            return 0
        return time.monotonic() - self.start_time
    
    def lap(self):
        """Return time since last lap, and update lap time."""
        if not self.running:
            return 0
        now = time.monotonic()
        dt = now - self.last_lap_time
        self.last_lap_time = now
        return dt
    
    def reset(self):
        """Reset the timer."""
        self.start_time = None
        self.last_lap_time = None
        self.running = False
        print("Timer reset.")
