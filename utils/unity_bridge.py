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

    def send_tweet_show(self):
        message = {
            "event": "tweet",
            "action": "show"
        }
        self.send(message)

    def send_tweet_update(self, text: str):
        message = {
            "event": "tweet",
            "action": "update",
            "text": text
        }
        self.send(message)

    def send_tweet_hide(self):
        message = {
            "event": "tweet",
            "action": "hide"
        }
        self.send(message)

    def send_cover_image(self, url:str, game_time):
        game_time_str = game_time.strftime("%Y-%m-%d")
        self.send({
        "event": "cover_image",
        "url": url,
        "game_time": game_time_str
        })

    def send_stream_start(self,game_time):
        game_time_str = game_time.strftime("%Y-%m-%d")
        self.send({
            "event": "stream",
            "action": "start",
            "game_time": game_time_str
        })

    def send_stream_talk(self,talk):
        self.send({
            "event": "stream",
            "action": "talk",
            "talk": talk
        })

    def send_stream_end(self):
        self.send({
            "event": "stream",
            "action": "end"
        })

    def update_background(self, game_datetime, weather):
        hour = game_datetime.hour

        if weather == "sunshine":
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
                    "mode": mode,
                })
                print(f"[Python] Background changed to: {mode}")

        else:
            if hour >= 19 or hour < 7:
                mode = "rainnight"
            else:
                mode = "rainday"

            if mode != self.last_background_state:
                self.last_background_state = mode
                self.send({
                    "event": "background",
                    "mode": mode,
                })
                print(f"[Python] Background changed to: {mode}")
