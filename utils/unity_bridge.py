import socket
import json
import threading

class UnityBridge:
    def __init__(self, host="127.0.0.1", port=50007):
        self.host = host
        self.port = port
        self.conn = None
        self.last_background_state = None
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.host, self.port))
        self.server.listen(1)

        print(f"[Python] UnityBridge server started at {host}:{port}")
        #threading.Thread(target=self.wait_for_unity, daemon=True).start()

    def wait_for_unity(self):
        print("[Python] Waiting for Unity connection...")
        self.conn, addr = self.server.accept()
        print(f"[Python] Unity connected from: {addr}")

    def send(self, data:dict):
        if self.conn is None:
            return
        
        msg = json.dumps(data) + "\n"
        self.conn.sendall(msg.encode("utf-8"))

    def send_time(self, time_str:str):
        self.send({
            "event": "time_update",
            "time": time_str
        })

    def update_background(self, game_datetime):
        hour = game_datetime.hour

        if hour >= 20 or hour < 5:
            mode = "night"
        elif hour >= 17 and hour < 20:
            mode = "evening"
        else:
            mode = "day"

        if mode != self.last_background_state:
            self.last_background_state = mode
            self.send({
                "event": "background",
                "mode": mode
            })
            print(f"[Python] Background changed to: {mode}")

        
