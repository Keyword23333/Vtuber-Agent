import time
from datetime import datetime
import sys
import os
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.game_time import GameTime
from utils.loader import TodoListLoader
from utils.unity_bridge import UnityBridge
from behavior.planner import Planner
import random

class VtuberAgent:
    """
    Main agent: Control complete behavior of Vtuber
    - Short Term Memory
    - Long Term Memory
    - Dialog
    - Unity Tcp
    - LLM decision
    """
    def __init__(self):
        self.game_time = GameTime(speed_ratio=1) # initialize gametime 
        self.todolist_loader = TodoListLoader() # update everyday
        self.day_started = False
        self.weather = "sunshine"
        self.unity = UnityBridge()
        self.planner = Planner(self.unity)
        
    def start_daily_loop(self):
        # Time Controller(CPU Clock mitai)
        print("\n[Agent] Daily loop started!")
        while True:
            self.game_time.update()
            current_hour = self.game_time.get_hour()
            current_game_time = self.game_time.now()
            current_time_str = current_game_time.strftime("%H:%M")
            current_hours, current_minutes = current_time_str.split(":")
            current_total_minutes = int(current_hours) * 60 + int(current_minutes)
            print(f"[时间测试] 游戏时间: {current_game_time.strftime('%Y-%m-%d %H:%M:%S')} | ")
            self.unity.send_time(current_time_str)
            self.unity.update_background(current_game_time, self.weather)
            # Work start from 8:00 am every day(includeing weekends)
            if self.day_started == False and current_hour == 8:
                """
                initialize the day
                - check email
                - generate todolist
                """
                self.start_new_day()
                self.day_started = True
            
            if self.schedule:
                next_task = self.schedule[0]

                start_h, start_m = next_task["start_time"].split(":")
                end_h, end_m = next_task["end_time"].split(":")

                start_minutes = int(start_h) * 60 + int(start_m)
                end_minutes   = int(end_h) * 60 + int(end_m)

                if (not next_task.get("started", False)) and current_total_minutes >= start_minutes:
                    next_task["started"] = True
                    self.planner.classifier(next_task, current_game_time, True)

                if current_total_minutes >= end_minutes:
                    self.planner.classifier(next_task, current_game_time, False)
                    self.schedule.pop(0)
            # end the day at 3:00 am
            if current_hour == 3:
                self.day_started = False

            time.sleep(1)

    def start_new_day(self):
        print("\n===== New Day Started =====")
        current_date = self.game_time.now()
        """
        self.todolist = self.todolist_loader.load(current_date)
        print(self.todolist.get("tasks"))
        self.tasks = self.todolist.get("tasks","")
        
        self.planner.classifier(self.todolist)
        """
        self.todolist = self.planner.generate_todolist(current_date)
        self.schedule = self.planner.normalize(self.todolist)
        print(self.todolist)
        self.weather = "sunshine" if random.random() < 0.6 else "rain"

        print(f"\n[Weather] Today's weather: {self.weather}\n")

if __name__ == "__main__":
    vtuber = VtuberAgent()
    vtuber.unity.wait_for_unity()
    vtuber.start_daily_loop()






