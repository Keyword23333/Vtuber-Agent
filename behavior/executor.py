import sys
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
    def __init__(self, api_key=None, base_url=None, model=None):
        self.llm = QwenLLM(api_key, base_url, model)
        self.gm = QwenGM(api_key, base_url, model)
    
    def post_preview(self, tweet_task):
        print("\n[Tweet] Post today's stream preview...\n")
        content = tweet_task.get("content","")
        print(tweet_task)
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
        print(final_prompt)
        response = self.llm.ask_json(final_prompt)
        print(response)



        

 

        

