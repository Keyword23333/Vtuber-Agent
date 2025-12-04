import sys
import json
import time
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ai.llm_client import QwenLLM,QwenGM,DeepseekVtuber
from configs.persona_config import persona

class Executor:
    """
    - post something on tweet
    - generate cover
    """
    def __init__(self, unity_bridge, api_key=None, base_url=None, model=None):
        self.llm = QwenLLM(api_key, base_url, model)
        self.gm = QwenGM(api_key, base_url, model)
        #self.dk = DeepseekVtuber()
        self.unity_bridge = unity_bridge
    
    def post_preview(self, tweet_task):
        print("\n[Tweet] Post today's stream preview...\n")
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

    def generate_cover(self, cover_task, game_time):
        print("\n[Cover] Generate stream's cover...\n")
        content = cover_task.get("content","")
        
        final_prompt = f"你是一隻三花貓虛擬主播，請生成一張圖片，要求如下\n {content}\n"
        print(f"\n[Cover] Using prompt as \n {final_prompt}\n")
        img_link = self.gm.ask_json(final_prompt)
        print(f"\n[Cover] Get image link as \n{img_link}\n")
        self.unity_bridge.send_cover_image(img_link,game_time)

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

        p = p.replace("{vtuber_name}", persona['name'])
        p = p.replace("{company_name}", "2333")
        p = p.replace("{project_json}", project_json_str)

        
        print(f"\n[Project] Using prompt as\n{p}\n")
        time.sleep(10)
        response = self.llm.ask_json(p)
        print(f"\n[Project] Get email as\n{response}\n")

        # send project email to company's mailbox
        if isinstance(response, dict):
            mail_content = response.get("email", "")
        else:
        # LLM 回傳純文字，當作 email 全文
            mail_content = response
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


    def shoot_task(self):

        pass

    def stream_task(self, stream_task):
        print("\n[Stream] Stream Starting...\n")
        content = stream_task.get("content","")
        final_prompt = ""
        final_prompt += "請根據content説一段直播開場白，不要超過20字，要求返回json{'talk':'str'}格式："
        final_prompt += content

        print(f"\n[Stream] Using prompt as: \n{final_prompt}\n")
        # 調試的時候先用大模型
        resp = self.llm.ask_json(final_prompt)

        print(f"\n[Stream] Say something as :\n {resp}\n")
        self.unity_bridge.send_stream_talk(resp.get("talk",""))

        time.sleep(5)
        resp = self.llm.ask_json("你是一位三花貓虛擬主播，名字叫苞米。現在有觀衆問你，你喜歡喝什麽飲料，請回答不要超過20字，要求返回json{'talk':'str'}格式")

        print(f"\n[Stream] Say something as :\n {resp}\n")
        self.unity_bridge.send_stream_talk(resp.get("talk",""))


