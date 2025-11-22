import os
from pathlib import Path
import json
from datetime import datetime

class TodoListLoader:
    def __init__(self, root_path=None):
        self.root_path = root_path
        if not self.root_path:
            parent_dir = Path(__file__).parent.parent
            self.list_dir = parent_dir / "data" / "TodoList"
            self.list_dir.mkdir(exist_ok=True)
        else:
            self.list_dir = Path(root_path) / "data" / "TodoList"     
        self.list_dir.mkdir(parents=True, exist_ok=True)

    def load(self,game_date):
        date_str = game_date.strftime("%Y-%m-%d")
        self.todo_file = self.list_dir / f"{date_str}.json"
        if not self.todo_file.exists():
            raise FileNotFoundError(f"TodoList file not found: {self.todo_file}")
        
        with open(self.todo_file, "r", encoding="utf-8") as f:
            data = f.read()

        return data
    
class MailLoader:
    def __init__(self, root_path=None):
        self.root_path = root_path
        if not self.root_path:
            parent_dir = Path(__file__).parent.parent
            self.list_dir = parent_dir / "data"
        else:
            self.list_dir = Path(root_path) / "data"
        self.list_dir.mkdir(parents=True, exist_ok=True)
    def load(self, type, game_date):
        date_str = game_date.strftime("%Y-%m-%d")
        self.mail_file = self.list_dir/ type / f"{date_str}.txt"
        if not self.mail_file.exists():
            raise FileNotFoundError(f"e-Mail not found: {self.mail_file}")
        
        with open(self.mail_file, "r", encoding="utf-8") as f:
            data = f.read()

        return data

if __name__ == "__main__":
    game_date = datetime(2077, 1, 1, 8, 0, 0)
    loader = TodoListLoader()
    todolist = loader.load(game_date)

    print("=== 今日 TodoList ===")
    print(json.dumps(todolist, indent=2, ensure_ascii=False))
    print(todolist.get("tasks"))