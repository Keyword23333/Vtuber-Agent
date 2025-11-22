import json
import os
import dashscope
from dashscope import MultiModalConversation

from pathlib import Path
import sys
import os
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


from configs.settings import (
    QWEN_API_KEY,
    QWEN_API_URL,
    QWEN_TEXT_MODEL,
    QWEN_IMAGE_MODEL,
    DEFAULT_RESPONSE_FORMAT,
)
from configs.persona_config import persona

class QwenLLM:
    """
    text2text: 
    """
    def __init__(self, api_key=None, base_url=None, model=None):
        self.api_key = api_key or QWEN_API_KEY
        self.base_url = base_url or QWEN_API_URL
        self.model = model or QWEN_TEXT_MODEL
        self.project_root = Path(__file__).resolve().parent.parent  # chat/
        self.template_dir = self.project_root / "configs" / "prompt_templates"

        dashscope.base_http_api_url = self.base_url

    def load_template(self, template_path: str):
        p = self.template_dir / template_path
        print(p)
        if p.exists():
            return p.read_text(encoding="utf-8")
        return ""

    def build_prompt(
            self,
            user_input_prompt: str = "",
            include_persona: bool = True,
            output_format: dict = None,
            template_path: str = None,
            file_prompts: str = None,
    ):
        final_prompt = ""

        if include_persona:
            final_prompt += (
                f"主播名字：{persona['name']}\n"
                f"說話風格：{persona['style']}\n"
                f"行為特徵：{persona['behavior_traits']}\n"
                "\n"
            )
        
        if template_path:
            template = self.load_template(template_path)
            final_prompt += template + "\n\n"

        if file_prompts:
            for file_path in file_prompts:
                path = Path(file_path)
                if path.exists():
                    final_prompt += f"\n[文件內容: {path.name}]\n"
                    final_prompt += path.read_text(encoding="utf-8") + "\n"
        
        if user_input_prompt:
            final_prompt += f"\n[使用者輸入]\n{user_input_prompt}\n"

        if output_format:
            final_prompt = final_prompt.replace("{output_format}", json.dumps(output_format))
        else:
            final_prompt = final_prompt.replace("{output_format}", json.dumps(DEFAULT_RESPONSE_FORMAT))

        return final_prompt

    def chat(self, prompt:str, response_format:dict=None):
        messages = [
            {"role": "user", "content": prompt}
        ]

        try:
            return dashscope.Generation.call(
                api_key=self.api_key,
                model=self.model,
                messages=messages,
                response_format={"type": "json_object"},
                result_format="text"    
            )

        except Exception as e:
            print("[QwenLLM.chat] ERROR:", e)
            return None
        
    def ask_json(self, prompt: str):
        resp = self.chat(prompt, response_format={"type": "json_object"})
        try:
            content = resp["output"]["text"]
            return json.loads(content)
        except:
            print("[QwenLLM.ask_json] JSON decode error:", resp)
            return {}
        

class QwenGM:
    """
    text2img:
    """
    def __init__(self, api_key=None, base_url=None, model=None):
        self.api_key = api_key or QWEN_API_KEY
        self.base_url = base_url or QWEN_API_URL
        self.model = model or QWEN_IMAGE_MODEL

    def chat(self, prompt:str, response_format:dict=None):
        messages = [
            {"role": "user", "content": [{"text":prompt}]}
        ]

        try:
            return MultiModalConversation.call(
                api_key=self.api_key,
                model=self.model,
                messages=messages,
                result_format='message',
                stream=False,
                watermark=False,
                prompt_extend=True,
                negative_prompt='',
                size='1664*928'
            )

        except Exception as e:
            print("[QwenLLM.chat] ERROR:", e)
            return None
        
    def ask_json(self, prompt: str):
        resp = self.chat(prompt, response_format={"type": "json_object"})
        try:
            content = resp["output"]["choices"][0]["message"]["content"][0]["image"]
            return content
        except:
            print("[QwenLLM.ask_json] JSON decode error:", resp)
            return {}


# for test, please ignore...
if __name__ == "__main__":
    gm = QwenGM()
    content = gm.ask_json("製作[Silent Hill f]直播封面。")
    print(content)





        
    