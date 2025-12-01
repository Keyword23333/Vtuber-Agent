import sys
import json
import random
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data.game_list import game_list
from ai.llm_client import QwenLLM

class GamestoreAgent:
    """
    游戏商城 Agent
    任务定位：当主播打开商城时才被呼叫，生成「每日热门游戏列表」
    """
    
    def __init__(self, api_key=None, base_url=None, model=None):
        self.llm = QwenLLM(api_key, base_url, model)
        self.base_game_list = game_list.get("games", [])
        self.available_games = self.base_game_list.copy()
        self.today_games = []
        
        # 游戏库增删记录
        self.game_library_changes = {
            "added": [],
            "removed": []
        }
        
    def activate(self, vtuber_action="browse_gamestore"):
        """
        只有当主播执行「逛游戏商城」行为时启动
        """
        if vtuber_action != "browse_gamestore":
            return None
            
        print("\n[GamestoreAgent] 检测到主播浏览游戏商城，生成今日推荐列表...")
        return self.generate_daily_game_list()
    
    def generate_daily_game_list(self):
        """
        生成每日热门游戏列表
        要求：给出不同于base_game_list列表内的游戏，给vtuber agent的游戏库增删机制选择
        """
        try:
            # 使用LLM生成新的游戏推荐
            prompt = self._build_recommendation_prompt()
            response = self.llm.ask_json(prompt)
            
            if response and "games" in response:
                new_games = response["games"]
                self.today_games = new_games
                
                # 更新可用游戏库（添加新游戏）
                self._update_game_library(new_games)
                
                print(f"[GamestoreAgent] 成功生成 {len(new_games)} 个游戏推荐")
                return {
                    "success": True,
                    "games": new_games,
                    "library_changes": self.game_library_changes,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                # 如果LLM调用失败，使用备用方案
                return self._generate_fallback_list()
                
        except Exception as e:
            print(f"[GamestoreAgent] 生成游戏列表时出错: {e}")
            return self._generate_fallback_list()
    
    def _build_recommendation_prompt(self):
        """
        构建游戏推荐提示词
        """
        base_games_sample = random.sample(
            self.base_game_list, 
            min(3, len(self.base_game_list))
        ) if self.base_game_list else []
        
        prompt = f"""
        你是一个游戏推荐专家，需要为虚拟主播生成今日热门游戏推荐列表。
        
        要求：
        1. 生成的游戏必须不同于以下基础游戏列表中的游戏：
        {json.dumps(base_games_sample, ensure_ascii=False, indent=2)}
        
        2. 每个游戏必须包含以下字段：
           - title: 游戏名称
           - genre: 游戏类型（数组）
           - description: 游戏描述
           - stream_recommendation: 直播建议
             - peak_hours: 推荐直播时段（数组，可选值: ["morning", "afternoon", "evening", "night"]）
             - ideal_duration_min: 理想直播时长（分钟）
        
        3. 生成3-5个游戏，涵盖不同类型（恐怖、模拟、角色扮演、动作、休闲等）
        4. 考虑虚拟主播的直播特点，选择适合直播的游戏
        5. 游戏描述要生动有趣，突出直播看点
        
        请按照以下JSON格式输出：
        {{
          "games": [
            {{
              "title": "游戏名称",
              "genre": ["类型1", "类型2"],
              "description": "游戏描述",
              "stream_recommendation": {{
                "peak_hours": ["时段1", "时段2"],
                "ideal_duration_min": 时长
              }}
            }}
          ]
        }}
        """
        return prompt
    
    def _generate_fallback_list(self):
        """
        LLM调用失败时的备用游戏列表
        """
        fallback_games = [
            {
                "title": "Cyberpunk 2077",
                "genre": ["RPG", "Action", "Sci-Fi"],
                "description": "一款开放世界科幻角色扮演游戏，具有深刻的剧情和丰富的角色定制系统。",
                "stream_recommendation": {
                    "peak_hours": ["evening", "night"],
                    "ideal_duration_min": 180
                }
            },
            {
                "title": "Animal Crossing: New Horizons",
                "genre": ["Simulation", "Social", "Relax"],
                "description": "温馨的岛屿生活模拟游戏，适合与观众互动和放松心情的直播。",
                "stream_recommendation": {
                    "peak_hours": ["afternoon", "evening"],
                    "ideal_duration_min": 120
                }
            },
            {
                "title": "Resident Evil Village",
                "genre": ["Horror", "Action"],
                "description": "紧张刺激的生存恐怖游戏，具有精美的画面和引人入胜的故事。",
                "stream_recommendation": {
                    "peak_hours": ["night"],
                    "ideal_duration_min": 150
                }
            }
        ]
        
        self.today_games = fallback_games
        self._update_game_library(fallback_games)
        
        return {
            "success": True,
            "games": fallback_games,
            "library_changes": self.game_library_changes,
            "timestamp": datetime.now().isoformat(),
            "note": "使用备用游戏列表"
        }
    
    def _update_game_library(self, new_games):
        """
        更新游戏库，实现增删机制
        """
        # 重置变化记录
        self.game_library_changes = {"added": [], "removed": []}
        
        # 添加新游戏到可用游戏库
        for game in new_games:
            if not self._is_game_in_library(game):
                self.available_games.append(game)
                self.game_library_changes["added"].append(game["title"])
        
        # 随机移除一些旧游戏（模拟游戏库更新）
        if len(self.available_games) > 10:  # 保持游戏库大小合理
            remove_count = random.randint(1, 3)
            removed_games = random.sample(
                [g for g in self.available_games if g not in new_games], 
                min(remove_count, len(self.available_games) - len(new_games))
            )
            
            for game in removed_games:
                self.available_games.remove(game)
                self.game_library_changes["removed"].append(game["title"])
    
    def _is_game_in_library(self, game):
        """
        检查游戏是否已在游戏库中
        """
        for existing_game in self.available_games:
            if existing_game["title"] == game["title"]:
                return True
        return False
    
    def get_current_library(self):
        """
        获取当前可用的游戏库
        """
        return {
            "total_games": len(self.available_games),
            "games": self.available_games
        }
    
    def get_today_recommendations(self):
        """
        获取今日推荐游戏列表
        """
        return self.today_games
    
    def vtuber_select_game(self, selected_game_title):
        """
        处理主播选择游戏的行为
        修改：只能从今日推荐列表中选择游戏
        """
        selected_game = None
        
        # 只从今日推荐列表中搜索
        for game in self.today_games:
            if game["title"] == selected_game_title:
                selected_game = game
                break
        
        if selected_game:
            print(f"[GamestoreAgent] 主播选择了今日推荐游戏: {selected_game_title}")
            return {
                "success": True,
                "selected_game": selected_game,
                "stream_recommendation": selected_game.get("stream_recommendation", {})
            }
        else:
            print(f"[GamestoreAgent] 选择失败: 游戏 '{selected_game_title}' 不在今日推荐列表中")
            return {
                "success": False,
                "error": f"游戏 '{selected_game_title}' 不在今日推荐列表中，请从今日推荐游戏中选择"
            }


# 测试代码
if __name__ == "__main__":
    # 测试GamestoreAgent
    gamestore = GamestoreAgent()
    
    print("=== 开始多日游戏商城测试 ===\n")
    
    # 模拟连续多天访问游戏商城
    for day in range(1, 8):  # 测试7天
        print(f"第{day}天")
        print("-" * 50)
        
        # 模拟主播浏览游戏商城
        result = gamestore.activate("browse_gamestore")
        
        if result and result["success"]:
            print("今日游戏推荐:")
            for i, game in enumerate(result["games"], 1):
                print(f"  {i}. {game['title']} - {', '.join(game['genre'])}")
                print(f"     描述: {game['description']}")
                print(f"     推荐时段: {', '.join(game['stream_recommendation']['peak_hours'])}")
                print(f"     建议时长: {game['stream_recommendation']['ideal_duration_min']}分钟")
                print()
            
            print("游戏库变化:")
            if result['library_changes']['added']:
                print(f"   新增游戏: {', '.join(result['library_changes']['added'])}")
            else:
                print("   新增游戏: 无")
                
            if result['library_changes']['removed']:
                print(f"   移除游戏: {', '.join(result['library_changes']['removed'])}")
            else:
                print("   移除游戏: 无")
            
            # 显示当前游戏库状态
            library = gamestore.get_current_library()
            print(f"当前游戏库总数: {library['total_games']}个游戏")
            
            # 测试游戏选择 - 只能选择今日推荐游戏
            if result["games"]:
                # 测试1: 选择今日推荐中的游戏（应该成功）
                valid_game = result["games"][0]["title"]
                selection_result = gamestore.vtuber_select_game(valid_game)
                if selection_result["success"]:
                    print(f"成功选择今日推荐游戏: {valid_game}")
                else:
                    print(f"选择游戏失败: {selection_result['error']}")
                
                # 测试2: 尝试选择被移除的游戏（应该失败）
                if result['library_changes']['removed']:
                    removed_game = result['library_changes']['removed'][0]
                    invalid_selection = gamestore.vtuber_select_game(removed_game)
                    if not invalid_selection["success"]:
                        print(f"正确阻止选择被移除游戏: {removed_game}")
                    else:
                        print(f"错误: 不应该能选择被移除的游戏: {removed_game}")
        else:
            print("游戏推荐生成失败")
        
        print("\n" + "=" * 50 + "\n")
    
    # 显示最终游戏库汇总
    print("=== 最终游戏库汇总 ===")
    final_library = gamestore.get_current_library()
    print(f"总游戏数量: {final_library['total_games']}")
    print("所有游戏列表:")
    for i, game in enumerate(final_library["games"], 1):
        print(f"  {i}. {game['title']} - {', '.join(game['genre'])}")