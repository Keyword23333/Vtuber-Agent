import sys
import json
from pathlib import Path
from datetime import datetime
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ai.llm_client import QwenLLM
from configs.persona_config import persona
from data.game_list import game_list 
from utils.loader import MailLoader
from behavior.executor import Executor

class Planner:
    """
    schedule refine: no time conflction...
    todolist generation...
    task execution
    """
    def __init__(self, unity_bridge, api_key=None, base_url=None, model=None):
        self.llm = QwenLLM(api_key, base_url, model)
        self.mail_loader = MailLoader()
        self.unity_bridge = unity_bridge
        self.executor = Executor(unity_bridge,api_key, base_url, model)


    def classifier(self, task, game_time):
        print(task)
        type = task.get("type","")
        if type == "tweet":
            category = task.get("category","")
            if category == "preview":
                self.executor.post_preview(task)
            elif category == "communication":
                self.executor.post_communication(task)
        if type == "cover":
            self.executor.generate_cover(task)
        if type == "project":
            self.executor.post_project(task, game_time)
        
    def normalize(self, todolist):
        tasks = todolist.get("tasks",[])
        """
        tasks_schedule = {}
        for i, task in enumerate(tasks):
            start_time = task.get("start_time","")
            if start_time:
                tasks_schedule[start_time] = {
                    "index": i,
                    "task": task
                }
        """
        sorted_tasks = sorted(tasks, key=lambda x: 
                int(x.get("start_time", "00:00").split(":")[0]) * 60 + 
                int(x.get("start_time", "00:00").split(":")[1]))
        tasks_schedule = sorted_tasks 
        print(f"[Tasks] Today has {len(tasks_schedule)} tasks...")
        return tasks_schedule

    def generate_todolist(self, game_date):
        print("\n[Todolist] Generate todolist...\n")
        template_path = project_root / "configs" / "prompt_templates" / "todolist.txt"
        p = template_path.read_text(encoding="utf-8")
        final_prompt = ""

        # add date
        final_prompt += f"[date] {game_date.strftime('%Y-%m-%d')}\n"

        # add game_list
        gl = game_list 
        if isinstance(gl, dict) and gl.get("games") == []:
            gl = None
            p = p.replace("{game_list}", "None")
        else:
            p = p.replace("{game_list}", json.dumps(gl, ensure_ascii=False))

        # add company tasks
        email = self.mail_loader.load("Personal_MailBox", game_date)
        p = p.replace("{company_tasks}", email)

        final_prompt += p
        content = self.llm.ask_json(final_prompt)
        return content
    


# for test, please ignore...
if __name__ == "__main__":
    planner = Planner()
    game_date = datetime(2077, 1, 1, 8, 0, 0)

    planner.generate_todolist(game_date)
        

        



        

        
