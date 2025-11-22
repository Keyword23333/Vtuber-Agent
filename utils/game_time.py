import time
from datetime import datetime, timedelta
import json
import os
from pathlib import Path

class GameTime:
    """
    GametimeSystem:
    - first start: first day's 8:00 am
    - real time acceleration: 1s = 20min(gametime)
    - save to json
    """

    def __init__(self, speed_ratio=5, root_dir=None):
        self.speed_ratio = speed_ratio
        self.root_dir = root_dir
        
        if not self.root_dir:
            parent_dir = Path(__file__).parent.parent
            data_dir = parent_dir / "data"
            data_dir.mkdir(exist_ok=True)
            self.SAVE_FILE = data_dir / "game_time.json"
        else:
            data_dir = Path(root_dir) / "data"
            data_dir.mkdir(exist_ok=True)
            self.SAVE_FILE = data_dir / "game_time.json"

        # first start
        self.SAVE_FILE.parent.mkdir(exist_ok=True)
        if not os.path.exists(self.SAVE_FILE):
            self.game_datetime = datetime(2077, 1, 1, 8, 0, 0)
            self.save()
        else:
            self.load()
        
        # record realtime at start time
        self.last_real_time = time.time()

    def save(self):
        data = {
            "datetime": self.game_datetime.isoformat()
        }
        with open(self.SAVE_FILE, "w") as f:
            json.dump(data, f)

    def load(self):
        with open(self.SAVE_FILE, "r") as f:
            data = json.load(f)
            self.game_datetime = datetime.fromisoformat(data["datetime"])

    def update(self):
        now = time.time()
        real_delta = now - self.last_real_time
        self.last_real_time = now
        game_minuts = real_delta * self.speed_ratio
        self.game_datetime += timedelta(minutes=game_minuts)

    def now(self):
        return self.game_datetime
    
    def get_hour(self):
        return self.game_datetime.hour
    
    def get_minutes(self):
        return self.game_datetime.minute



# for test, please ignore.
import socket
HOST = "127.0.0.1"
PORT = 50007

def run_demo():
    game_time = GameTime(speed_ratio=1)
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(1)

    print(f"[Python] GameTime Server started on {HOST}:{PORT}")
    print("[Python] Waiting for Unity to connect...")

    conn, addr = server.accept()
    print(f"[Python] Unity Connected from {addr}")

    try:
        while True:
            game_time.update()
            current_time = game_time.now().strftime("%H:%M")
            msg = json.dumps({"time": current_time}) + "\n"
            conn.sendall(msg.encode("utf-8"))
            print(f"[Python] Send time to Unity: {current_time}")
            time.sleep(1)

    except KeyboardInterrupt:
        # interrupted by Ctrl + C
        print("\n[Python] Exiting, saving time...")

    finally:
        # valid or invalid quit.
        game_time.save()
        conn.close()
        server.close()
        print("[Python] GameTime saved.")


if __name__ == "__main__":
    run_demo()
