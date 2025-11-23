### 項目目標
- 本項目旨在打造一個「具備完整日常行為」的虛擬主播智能體（VTuber Agent）。
- 主體由 Qwen3-Max 作為核心大模型，搭配多個子 Agent（公司、遊戲商城、廣告商、直播平台）。
- 整個系統透過 Unity 前端 + Python 後端 + TCP 通訊整合，模擬一個完整虛擬主播的工作/生活流程。

### 智能體
#### Vtuber Agent (主智能體)
- 自動生成每日行程：拍攝、直播、剪輯、企劃等
- 自動製作直播封面、預告推文
- 決策邏輯：公司安排 > 個人安排
- 行為樹控制直播、剪輯、寫企劃、逛遊戲商城等
- 睡前會自動分析數據發送給公司

#### 子 Agent
- **公司 Agent**：審核企劃、安排拍攝、發送素材、聯係廣告商
- **遊戲商城 Agent**：生成每日遊戲清單，供主播挑選
- **廣告商 Agent**：根據主播數據判斷是否投廣告、聯係公司
- **直播平台 Agent**：推流並回傳直播數據

##### Company Agent
- **任務定位**：
	- 作為虛擬主播的經紀公司
	- 審核企劃、安排拍攝、分派廣告、管理官方任務
	- 主要負責：**控制主播的工作內容與大方向**
- **行爲規則**：
	- 每天在主播睡覺時運作（After vtuber sleep），在新的一天開始之前要將任務以郵件的形式發送到主播的個人郵箱（Personal_Mailbox）裏面。
	- 檢查公司郵箱（Company_Mailbox）裏面是否有主播前一天發送的企劃方案。如果主播的企劃案通過，就通知主播拍攝時間；如果沒有通過，就不做處理
	- 檢查公司郵箱裏面是否有廣告的郵件，有的話就轉發給主播
- **郵件示例**
	```
	寄件人：Production Team <studio@company.jp>
    收件人：星野雫 <vtuber@agency.jp>
	主旨：【廣告】

	親愛的星野雫：

	您好！我們接到品牌方「NEO ENERGY」的宣傳合作項目，品牌方希望將其作爲您今天的直播内容。建議時長30min。

	如有任何疑問，請回覆本郵件。  
	祝工作順利、拍攝愉快！

	Production Team  
	Creative Studio
	```
##### Gamestore Agent
- **任務定位**：
	- 當主播打開商城時才被呼叫
	- 生成「每日熱門遊戲列表」
- **行爲規則**：
	- 只有當主播執行「逛遊戲商城」行為時啟動
	- 輸入為game_list.py内的game_list，要給出不同於game_list列表内的游戲，給vtuber agent的游戲庫增刪機制選擇。
	- 必須包含：游戲名字，游戲類別，游戲描述，直播建議。
- **游戲列表示例**：
	```
	game_list = {
	  "games": [
	    {
	      "title": "Silent Hill f",
	      "genre": ["Horror", "Adventure"],
	      "description": "一款心理恐怖冒險遊戲，具有日式恐怖元素與強故事敘事。",
	      "stream_recommendation": {
	        "peak_hours": ["night"],
	        "ideal_duration_min": 120
	      },
	    },
	    {
	      "title": "Stardew Valley",
	      "genre": ["Simulation", "Relax"],
	      "description": "溫馨的農場模擬與社交遊戲，適合長期系列直播。",
	      "stream_recommendation": {
	        "peak_hours": ["afternoon", "evening"],
	        "ideal_duration_min": 180
	      },
	    }
	  ]
	}
	```
另外兩個如果來不及寫可以在展示之後再補全。
### 項目結構
之後還會增改
```
root/
│
├── agents/                               # 所有子智能體（多 Agent 系統）
│   ├── vtuber_agent.py                   # 虛擬主播主體 Agent（核心邏輯與行為決策）
│   ├── gamestore_agent.py                # 遊戲商城 Agent（生成遊戲列表、推薦遊戲）
│   ├── company_agent.py                  # 公司 Agent（審核企劃、安排拍攝、派送素材/廣告）
│   ├── add_agent.py                      # 廣告商 Agent（決定是否投放廣告）
│   └── stream_agent.py                   # 直播平台 Agent（推流、傳遞直播數據）
│
├── ai/
│   └── llm_client.py                     # 大模型 API 封裝（Qwen3-max 調用、統一請求格式）
│
├── behavior/
│   ├── executor.py                       # 行為執行器（根據 planner 的輸出執行具體任務）
│   └── planner.py                        # 行為/日程規劃器（LLM-based 計畫生成）
│
├── configs/
│   ├── prompt_templates/                 # 所有 prompt 模板（txt 格式便於調整）
│   │   ├── todolist.txt                  # 用於生成代辦清單的 prompt
│   │   └── tweet.txt                     # 用於生成推特預告/貼文的 prompt
│   ├── persona_config.py                 # 主播人格設定（背景、說話風格、偏好）
│   └── settings.py                       # 全域設定（路徑、端口、API Keys、參數）
│
├── data/
│   ├── assets/                           # 各種素材（拍攝素材、封面、圖片等）
│   ├── Company_Mailbox/                  # 公司寄給主播的郵箱（企劃結果、拍攝通知、廣告）
│   ├── Diary/                            # 主播日記（AI 寫入的每日總結）
│   ├── Personal_Mailbox/                 # 主播個人郵箱（接收公司與廣告商的信件）
│   ├── TodoList/                         # 代辦事項儲存（按天整理）
│   ├── game_list.py                      # 遊戲池（商城每日更新用的固定遊戲清單）
│   └── game_time.json                    # 虛擬遊戲內時間/日程設定（如時間倍率）
│
├── src/
│   └── main.py                           # 主入口：啟動所有 Agent、行為循環、時間控制
│
└── utils/
    ├── gametime.py                       # 虛擬時間系統（現實時間 → 遊戲時間轉換）
    └── loader.py                         # 通用數據讀取器（JSON / TXT / CSV 等）


```
### Todolist格式
主體為：
```
{
"date": "%Y-%m-%d",
“tasks": [
		{
			task1
		},
		{
			task2
		}
		...
	]
}
```
其中每個task的結構為：

```
{
"type": 
"category":
"start_time":
"end_time":
"content":
}
```

- 其中"type"表示平臺類型，必填，只能從下面幾個選項中選擇："stream","company","cover","store","tweet","rest","project"（其中project是想企劃案）
- "category"表示平臺下的任務細分，其中"stream","cover","store"沒有這一項；"tweet"下可選參數："preview","communication"；"company"下可選參數："shoot"（shoot表示拍攝）
-  "start_time" 和 "end_time"表示開始和結束的時間
-  "content"就是任務的具體内容。如果有直播，那麽推特和封面的content和直播主題吻合（推特的content最好包括直播的時間和内容概括即可，不需要很具體）。