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
        self.planner = Planner()
        self.unity = UnityBridge()

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
            self.unity.update_background(current_game_time)
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
                task_start_time = next_task.get("start_time","")
                task_hours, task_minutes = task_start_time.split(":")
                task_total_minutes = int(task_hours) * 60 + int(task_minutes)
                if current_total_minutes >= task_total_minutes:
                    self.planner.classifier(next_task, current_game_time)
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



if __name__ == "__main__":
    vtuber = VtuberAgent()
    vtuber.unity.wait_for_unity()
    vtuber.start_daily_loop()






