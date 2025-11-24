import sys
import json
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ai.llm_client import QwenLLM,QwenGM
from configs.persona_config import persona

class Executor:
    """
    - post something on tweet
    - generate cover
    """
    def __init__(self, unity_bridge, api_key=None, base_url=None, model=None):
        self.llm = QwenLLM(api_key, base_url, model)
        self.gm = QwenGM(api_key, base_url, model)
        self.unity_bridge = unity_bridge
    
    def post_preview(self, tweet_task):
        print("\n[Tweet] Post today's stream preview...\n")
        self.unity_bridge.send_tweet_show()
        content = tweet_task.get("content","")
        template_path = project_root / "configs" / "prompt_templates" / "tweet.txt"
        p = template_path.read_text(encoding="utf-8")

        final_prompt = ""
        final_prompt += (
            f"主播名字：{persona['name']}\n"
            f"説話風格：{persona['style']}\n"
            f"行爲特徵：{persona['behavior_traits']}\n"
            "\n"
        )

        final_prompt += p
        final_prompt += f"\n[使用者輸入]\n{content}\n"
        print(f"\n[Tweet] Using prompt as \n{final_prompt}\n")
        response = self.llm.ask_json(final_prompt)
        tweet_content = response.get("tweet","")
        self.unity_bridge.send_tweet_update(tweet_content)
        print(f"\n[Tweet] Get prompt as \n{tweet_content}\n")

    def post_communication(self, tweet_task):
        print("\n[Tweet] Post communication tag...\n")
        content = tweet_task.get("content","")
        template_path = project_root / "configs" / "prompt_templates" / "tweet.txt"
        p = template_path.read_text(encoding="utf-8")

        final_prompt = ""
        final_prompt += (
            f"主播名字：{persona['name']}\n"
            f"説話風格：{persona['style']}\n"
            f"行爲特徵：{persona['behavior_traits']}\n"
            "\n"
        )

        final_prompt += p
        final_prompt += f"\n[使用者輸入]\n{content}\n"
        print(f"\n[Tweet] Using prompt as \n{final_prompt}\n")
        response = self.llm.ask_json(final_prompt)
        print(f"\n[Tweet] Get tweet as \n{response}\n")

    def generate_cover(self, cover_task):
        print("\n[Cover] Generate stream's cover...\n")
        content = cover_task.get("content","")
        
        final_prompt = f"請生成一張圖片，要求如下\n {content}\n"
        print(f"\n[Cover] Using prompt as \n {final_prompt}\n")
        img_link = self.gm.ask_json(final_prompt)
        print(f"\n[Cover] Get image link as \n{img_link}\n")

    def post_project(self, project_task, game_time):
        print("\n[Project] Thinking of new project...\n")
        # generate project content...
        content = project_task.get("content","")
        template_path = project_root / "configs" / "prompt_templates" / "project.txt"
        p = template_path.read_text(encoding="utf-8")
        
        final_prompt = ""
        final_prompt += p
        final_prompt += f"\n[使用者輸入]\n{content}\n"

        print(f"\n[Project] Using prompt as\n{final_prompt}\n")
        project_json = self.llm.ask_json(final_prompt)
        project_json_str = json.dumps(project_json, indent=2, ensure_ascii=False)
        print(f"\n[Project] Get project as\n{project_json}\n")

        # generate project email...
        print("\n[Project] Writing email to company...\n")
        template_path = project_root / "configs" / "prompt_templates" / "p2c_email.txt"
        p = template_path.read_text(encoding="utf-8")

        p.replace("{vtuber_name}", persona['name'])
        p.replace("{company_name}", "2333")
        p.replace("{project_json}", project_json_str)

        print(f"\n[Project] Using prompt as\n{p}\n")
        response = self.llm.ask_json(p)
        print(f"\n[Project] Get email as\n{response}\n")

        # send project email to company's mailbox
        mail_content = response.get("email","")
        mail_dir = project_root / "data" / "Company_Mailbox"
        mail_dir.mkdir(parents=True, exist_ok=True)
        file_date = game_time.strftime("P%Y-%m-%d.txt")
        file_path = mail_dir / file_date
        counter = 1
        original_path = file_path
        while file_path.exists():
            file_name = f"{original_path.stem}_{counter}{original_path.suffix}"
            file_path = original_path.parent / file_name
            counter += 1
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(mail_content)

        print(f"\n[Project] Email saved to: {file_path}\n")


 

        

