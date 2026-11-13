# AI Film Studio

## 完整 AI 電影製作、自動化剪輯與多模型協作平台

**版本：4.0**\
**文件類型：系統架構與完整開發規格**

------------------------------------------------------------------------

## 1. 專案目標

AI Film Studio 是一套完整的 AI
電影製作平台，涵蓋主題發想、劇本、人物與場景設計、分鏡、圖片與影片生成、配音、音樂、音效、字幕、剪輯、審稿及上映準備。

核心要求：

1.  支援使用者上傳照片、影片、音訊及其他素材。
2.  支援輸入主題、故事或完整劇本，自動製作電影。
3.  支援素材製作、劇本自動製作及混合模式。
4.  支援任意數量人物角色及角色資料庫。
5.  透過參考圖、角色設定及生成後審核，盡可能維持人物一致性。
6.  每個製作階段可選擇主要模型及備用模型。
7.  模型點數、額度或服務不可用時，可切換模型並接續任務。
8.  所有外部 AI 服務及影音工具必須能由程式直接調用。
9.  支援跨設備、分散式 Worker、任務保存及恢復。
10. 支援自動剪輯、配音、音樂、字幕、品質檢查及輸出。

## 2. 核心設計原則

-   **模組化：** 各功能獨立開發，透過標準介面整合。
-   **模型與工具分離：** 模型負責理解與生成；工具負責實際執行。
-   **使用者控制：** 使用者可選模型、工具、品質、預算及切換方式。
-   **可追蹤及可恢復：** 每項任務都有 ID、狀態、版本及 Checkpoint。
-   **真實可執行：** 未接入 API 或未通過測試的功能不得標示為已完成。

## 3. 製作模式

### A. 使用者素材模式

使用者上傳人物照片、影片、場景、音樂或音訊；AI
分析素材、建立角色與場景資料、規劃分鏡、生成或延伸影片，再進行配音、字幕、審稿及剪輯。

### B. 劇本自動製作模式

使用者輸入主題、故事概念或劇本，AI
自動完成故事開發、角色設計、場景設計、分鏡、圖片、影片、配音、音樂、音效、字幕及剪輯。

### C. 混合模式

同一專案可混用使用者素材與 AI 生成素材，例如使用者提供人物照片、AI
生成場景、使用者提供音樂、AI 補充音效。

## 4. 六大電影製作階段

### Stage 1 --- Development

主題發想、市場及觀眾定位、故事概念、大綱、故事結構、劇本、對白、角色關係及敘事風格。

輸出：Project Concept、Synopsis、Treatment、Screenplay、Character
List、Creative Bible。

### Stage 2 --- Pre-production

角色與服裝設計、場景設計、Character Bible、Scene Bible、分鏡、Shot
List、鏡頭運動、錨點圖、預算及模型配置。

輸出：Character Bible、Costume Bible、Scene Bible、Storyboard、Shot
List、Anchor Images、Production Plan。

### Stage 3 --- Production

人物及場景圖片生成、文生圖、圖生影片、文生影片、影片延伸、多鏡頭生成，以及人物與場景一致性檢查。

輸出：Character Images、Scene Images、Generated Videos、Shot
Assets、Production Reports。

### Stage 4 --- Post-production

素材整理、鏡頭選擇、時間軸、剪輯、轉場、特效、配音、音樂、音效、語音辨識、字幕、音量、調色及品質檢查。

輸出：Edited Timeline、Voice Tracks、Music Tracks、Sound
Effects、Subtitle Files、Master Video。

### Stage 5 --- Distribution Preparation

解析度、比例、FPS、音訊、字幕、編碼、封裝、版權資料、海報、預告片及發行格式檢查。

### Stage 6 --- Exhibition & Release

最終預覽、人工審核、版本確認、輸出、發布及專案歸檔。

## 5. AI Agent 架構

### 五大核心 Agent

1.  **Material Analysis Agent：**
    分析照片、影片、人物、場景、音訊、鏡頭及素材標籤。
2.  **Director Agent：** 故事、劇本、場景、分鏡、鏡頭、對白及視覺風格。
3.  **Prompt Agent：**
    文生圖、圖生影片、文生影片提示詞及模型專屬格式轉換。
4.  **Review Agent：**
    劇情、人物一致性、場景、畫面、音訊、字幕及生成品質審核。
5.  **Editing Agent：**
    素材排序、時間軸、剪接、轉場、配音、音樂、音效、字幕及輸出。

可擴充 Script、Character、Scene、Storyboard、Image Generation、Video
Generation、Voice、Music、Subtitle、Continuity、Color Grading、Trailer
及 Distribution Agent。

所有 Agent 必須透過統一任務介面及 Tool Execution Engine
工作，不可各自任意執行系統命令。

## 6. Character Studio --- 多角色管理

支援任意數量角色，每位角色有獨立 Character ID。

角色資料包括：姓名、角色背景、年齡設定、臉型、五官、髮型、膚色、身材、主要特徵、聲音設定、照片、參考圖、影片、服裝及版本。

支援新增、修改、刪除、複製角色，上傳多張照片及影片，建立多角度參考圖，設定不同服裝及角色出現的
Scene。

### Identity / Appearance / Costume 分離

-   **Identity：** 臉部特徵、五官比例、年齡特徵及基本辨識特徵。
-   **Appearance：** 髮型、膚色、身材、體態及外觀特徵。
-   **Costume：** 服裝、顏色、材質、配件及不同 Scene 的服裝版本。

### 人物一致性引擎

依模型能力使用 Character
Reference、Image-to-Video、多角度參考圖、IP-Adapter、LoRA
等方法。生成後抽取影格並比對人物特徵。

審核狀態：PASS、WARNING、FAIL、REVIEW。

**限制：**
不同模型的參考能力與生成方式不同，不能保證百分之百一致；必須保留人工審核及重新生成機制。

## 7. Model Hub --- AI 模型中心

模型不得寫死在 Agent 或工作流程中，所有模型透過 Model Registry 管理。

### 模型類別與候選

  -----------------------------------------------------------------------------------------------------------------------
  類別                    候選方向                                                       用途
  ----------------------- -------------------------------------------------------------- --------------------------------
  文字／推理              OpenAI、Gemini、Claude、MiniMax、OpenRouter、Ollama、Hugging   故事、劇本、分鏡、提示詞、審稿
                          Face                                                           

  圖片                    GPT Image、Gemini Image、FLUX、Seedream                        人物、場景、海報、錨點圖

  影片                    MiniMax、Kling、Seedance、Veo、Runway、Wan                     文生影片、圖生影片、影片延伸

  語音                    ElevenLabs、OpenAI TTS、MiniMax Audio、Whisper、WhisperX       配音、旁白、辨識、對齊

  音樂／音效              Suno、Udio、ElevenLabs Music／SFX 等                           配樂、環境音及音效
  -----------------------------------------------------------------------------------------------------------------------

以上是候選方向；實際型號、API、商用授權、費用及功能必須在接入時重新驗證。

### 各階段模型配置建議

  製作階段   主要模型候選                備用模型候選
  ---------- --------------------------- --------------------------
  主題發想   GPT、Gemini                 Claude、MiniMax
  劇本開發   GPT、Claude                 Gemini、MiniMax
  角色設計   GPT、Gemini                 Claude
  場景設計   Gemini、GPT                 Claude
  分鏡設計   GPT、Gemini                 Claude
  角色圖片   GPT Image、Gemini Image     FLUX、Seedream
  場景圖片   Gemini Image、FLUX          GPT Image、Seedream
  影片生成   MiniMax、Kling              Seedance、Veo、Runway
  影片分析   Gemini、GPT                 其他多模態模型
  配音       ElevenLabs、MiniMax Audio   OpenAI TTS
  音樂       ElevenLabs Music、Suno      其他可用服務
  音效       ElevenLabs SFX              其他可用服務
  字幕       Whisper                     WhisperX、其他轉錄模型
  審稿       GPT、Gemini                 Claude
  剪輯       FFmpeg                      Blender、DaVinci Resolve
  輸出檢查   FFprobe、MediaInfo          自訂品質檢查工具

### 使用者選擇與備援

每個階段提供主要模型、備用模型清單、排序、啟用狀態、API
設定、模型測試、費用估算及自動切換選項。使用者可自行新增供應商及模型。

### 點數不足及任務接續

遇到額度不足、Token／速率限制、服務故障或維護時：

1.  辨識錯誤類型。
2.  保存任務狀態、提示詞、參數及已完成結果。
3.  記錄最後成功完成的工作單元。
4.  暫停任務並檢查備用模型。
5.  檢查新模型輸入格式及功能相容性。
6.  顯示替代模型及費用資訊。
7.  由使用者選擇，或依授權設定自動切換。
8.  轉換提示詞及輸入格式。
9.  從最後成功的工作單元接續。
10. 記錄切換歷程。

對非冪等 API
呼叫，必須先查詢原任務狀態，避免重複扣費或重複生成。並非所有供應商都提供即時餘額查詢，需結合成本估算、使用紀錄及
API 錯誤回應。

## 8. Tool Execution Engine --- 外部工具直接調用引擎

**所有外部工具必須能由程式直接調用；不能只提供人工操作說明。**

### 支援的調用方式

-   **API Adapter：** HTTP API 呼叫雲端模型及服務。
-   **CLI Adapter：** 命令列執行 FFmpeg、Blender、Whisper
    CLI、SoX、MediaInfo 等。
-   **SDK Adapter：** Python／JavaScript SDK，例如
    OpenCV、Whisper、PyTorch。
-   **Service Adapter：** Docker、HTTP、WebSocket
    或工作佇列呼叫常駐服務及遠端 Worker。

### 核心影音工具

  工具              調用方式               功能                                 優先級
  ----------------- ---------------------- ------------------------------------ --------
  FFmpeg            CLI                    剪輯、合併、轉場、轉檔、字幕、音訊   必備
  FFprobe           CLI                    影音規格及媒體資訊                   必備
  OpenCV            Python SDK             影格分析、品質檢查                   必備
  Whisper           SDK／CLI               語音辨識                             必備
  MoviePy           Python SDK             時間軸及簡易編排                     選配
  WhisperX          Python SDK             字詞時間對齊                         選配
  Blender           Python API／CLI        3D、動畫、合成                       選配
  DaVinci Resolve   Scripting API          專業剪輯及調色                       選配
  Natron            CLI／Python 工作流程   影像合成                             選配
  SoX               CLI                    音訊處理                             選配
  Rubber Band       CLI／SDK               音訊變速及音調調整                   選配
  MediaInfo         CLI／SDK               媒體規格檢查                         選配

工具實際能力須依版本、作業系統、授權及安裝環境驗證。DaVinci Resolve
不得假設所有功能都能透過 API 無人值守操作。

### 統一工具註冊規格

每個工具提供：

-   `tool_id`
-   `tool_name`
-   `tool_type`
-   `version`
-   `provider`
-   `capabilities`
-   `input_schema`
-   `output_schema`
-   `health_check`
-   `execute`
-   `timeout`
-   `retry_policy`
-   `installation_check`
-   `license`
-   `execution_location`

### FFmpeg 自動剪輯能力

支援影片合併、裁切、分段、轉場、排序、變速、比例及解析度調整、字幕燒錄、音訊混合、音量標準化、淡入淡出、多音軌、編碼及輸出品質檢查。

以標準化 EDL 或 Timeline JSON 表示剪輯決策，再由 Adapter
轉成各工具的實際命令或腳本。

### 工具執行流程

1.  接收 Agent 任務。
2.  查詢工具註冊資料。
3.  檢查安裝、版本及健康狀態。
4.  驗證參數及檔案路徑。
5.  建立執行任務。
6.  呼叫工具並監控進度。
7.  收集標準輸出及錯誤輸出。
8.  驗證輸出檔案。
9.  儲存執行紀錄。
10. 回傳結果。

### 工具安全

-   只允許呼叫已註冊工具。
-   不允許 Agent 任意執行 Shell 命令。
-   CLI 使用參數陣列，不拼接未驗證的 Shell 字串。
-   限制輸入／輸出目錄、時間及檔案大小。
-   保護 API Key。
-   保留執行紀錄。
-   不覆蓋原始素材。
-   刪除、覆蓋及發布等重要操作須經確認。

## 9. Device Manager --- 設備管理中心

支援 Windows、Linux、Raspberry Pi、Synology NAS、Docker 主機及雲端 GPU。

### 設備角色

-   **Control Node：** 任務調度、Agent、模型、工具、使用者介面及權限。
-   **Worker Node：** 影片生成、剪輯、圖片／音訊處理及 AI 推理。
-   **Storage Node：** 原始素材、生成檔案、字幕、專案及備份。

### 設備自動偵測

首次啟動時檢查作業系統、CPU、RAM、GPU、磁碟空間、Docker、Python、FFmpeg、FFprobe、Blender、Whisper
等工具，建立設備能力清單。

### 遠端 Worker

透過安全 API 或佇列派送任務。Worker 回傳設備 ID、任務
ID、狀態、進度、輸出位置及錯誤訊息。遠端 Worker
不應直接暴露管理介面至公網。

## 10. Media Asset Manager --- 素材管理

分類包括 Character、Scene、Image、Video、Audio、Music、Sound
Effects、Subtitle、Generated Assets 及 Final Deliverables。

每項素材記錄 Asset ID、Project
ID、類型、路徑、格式、大小、長度、解析度、FPS、版本、來源模型／工具、提示詞及關聯角色／場景／鏡頭。

支援上傳、預覽、搜尋、標籤、分類、版本管理、替換、比對及備份。

## 11. Editing Studio --- 自動剪輯工作室

支援 Video、Audio、Music、Subtitle、Effects、Transition 等軌道。

AI 剪輯流程：

1.  分析影片。
2.  擷取鏡頭資訊。
3.  分析故事順序。
4.  選擇片段。
5.  建立時間軸。
6.  加入轉場。
7.  加入配音、音樂及音效。
8.  加入字幕。
9.  調整音量及畫面。
10. 品質審核。
11. 輸出影片。

採用內部標準化 Timeline JSON／EDL，再由 Adapter 轉換為 FFmpeg、Blender
或其他工具格式。

## 12. Subtitle Studio --- 字幕中心

支援中文、台灣閩南語、英文、日文、韓文及其他模型可辨識語言。

流程：語音辨識 → 逐字稿 → 使用者確認及修正 → 時間對齊 → SRT／VTT／ASS →
可選擇燒錄。

支援逐字字幕、逐句字幕、KTV 逐字變色、多語言字幕、樣式及時間微調。

## 13. Music & Sound Studio

支援主題音樂、背景音樂、情緒配樂、環境音、動作音效、轉場音效、角色聲音及旁白。

每項生成素材保存模型、提示詞、生成時間、授權資訊及檔案版本。使用前須確認供應商授權及商用條款。

## 14. Review & Quality Control

-   劇本：故事連貫性、人物設定、對白、場景邏輯及節奏。
-   影像：人物與場景一致性、清晰度、鏡頭連續性及生成錯誤。
-   音訊：配音清晰度、音量、音樂比例、音效及音畫同步。
-   成品：影片完整性、黑畫面、損壞影格、音訊、字幕及輸出規格。

## 15. Model Adapter

統一模型呼叫方式，轉換提示詞、圖片輸入及影片參數，檢查解析度、長度、參考圖能力及費用，並統一結果與錯誤格式。

原始 Prompt、Character Bible、Scene Bible、Shot Bible
必須保留，不得因切換模型而遺失。

## 16. Task Manager --- 任務管理及恢復

任務狀態：

`PENDING`、`QUEUED`、`RUNNING`、`PAUSED`、`WAITING_USER`、`WAITING_MODEL`、`WAITING_TOOL`、`RETRYING`、`COMPLETED`、`FAILED`、`CANCELLED`。

每個 Checkpoint 保存 Task ID、Project
ID、完成項目、輸入、輸出、模型、工具、參數、版本、時間及狀態。

中斷恢復時重新檢查輸出、素材、模型及工具，從最後成功完成的工作單元接續。

## 17. 前端架構

技術：Next.js、React、TypeScript、Tailwind CSS。

主要頁面：

1.  Dashboard
2.  Project Manager
3.  New Project
4.  Production Workflow
5.  Character Studio
6.  Scene Studio
7.  Storyboard Studio
8.  Prompt Studio
9.  Model Hub
10. Tool Manager
11. Device Manager
12. Asset Manager
13. Editing Studio
14. Subtitle Studio
15. Music Studio
16. Review Studio
17. Task Monitor
18. Usage & Budget
19. Settings

Dashboard 顯示專案數、執行中及等待處理任務、模型用量、費用、工具及
Worker 狀態、最近輸出。

Model Hub 可新增供應商／模型、測試
API、設定主要與備用模型、查看費用及設定自動切換。

Tool Manager
顯示工具安裝狀態、版本、設備位置、能力、健康狀態、調用方式及執行紀錄。

## 18. 後端架構

技術：

-   Python、FastAPI、Pydantic、SQLAlchemy
-   PostgreSQL
-   Redis
-   Celery 或具備持久化及恢復能力的任務佇列
-   n8n
-   Docker

FastAPI 負責使用者、專案、角色、場景、分鏡、模型、工具、任務、素材及
Worker API。

n8n
負責工作流調度、憑證管理、模型呼叫、切換通知及跨服務整合。大型影片運算應派送至適合的
Worker，不應由 n8n 或 Raspberry Pi 承擔。

PostgreSQL 保存持久化資料；Redis 負責佇列、暫存、Worker
狀態及進度。重要任務狀態不可只存在 Redis。

## 19. 資料庫主要 Schema

  Table                  用途
  ---------------------- ----------------
  users                  使用者
  projects               電影專案
  characters             人物
  character_versions     人物版本
  character_assets       人物素材
  scenes                 場景
  scene_versions         場景版本
  shots                  鏡頭
  storyboards            分鏡
  assets                 素材
  prompts                提示詞
  model_registry         模型清單
  model_capabilities     模型能力
  model_credentials      憑證安全引用
  project_model_config   專案模型配置
  model_fallbacks        備用模型排序
  model_usage_logs       模型使用紀錄
  model_switch_logs      模型切換紀錄
  tools_registry         工具清單
  tool_capabilities      工具能力
  tool_execution_logs    工具執行紀錄
  devices                設備
  workers                執行節點
  tasks                  任務
  task_checkpoints       任務接續點
  timelines              剪輯時間軸
  subtitles              字幕
  audio_tracks           音訊
  project_versions       專案版本
  audit_logs             安全及操作紀錄

## 20. 專案目錄結構

``` text
ai-film-studio/
├── frontend/
│   ├── app/
│   ├── components/
│   ├── hooks/
│   └── services/
├── backend/
│   ├── api/
│   ├── core/
│   ├── database/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   ├── agents/
│   ├── model_hub/
│   ├── model_adapters/
│   ├── tool_engine/
│   ├── tool_adapters/
│   ├── device_manager/
│   ├── task_manager/
│   ├── workers/
│   ├── editing/
│   ├── subtitle/
│   ├── audio/
│   └── tests/
├── n8n/
│   └── workflows/
├── workers/
│   ├── windows/
│   ├── linux/
│   ├── raspberry_pi/
│   └── cloud/
├── tools/
│   ├── ffmpeg/
│   ├── blender/
│   ├── whisper/
│   └── scripts/
├── projects/
├── storage/
├── configs/
├── docker/
├── docs/
├── scripts/
├── tests/
├── .env.example
├── docker-compose.yml
└── README.md
```

## 21. 硬體及部署架構

### Raspberry Pi 4 / 8GB

作為控制及工作流主機，執行
Docker、n8n、FastAPI、Redis、輕量服務、任務調度及模型／工具管理。不建議執行大型影片生成或大量高解析度剪輯。

### Synology NAS

作為儲存主機，保存原始素材、人物與場景照片、生成影片、音訊、字幕、專案檔案及備份。

### Windows 工作站

作為本地影音 Worker，執行
FFmpeg、FFprobe、OpenCV、Blender、Whisper、DaVinci Resolve
等已安裝且通過檢查的工具。

### 雲端服務

負責文字、圖片、影片、配音、音樂、音效模型及雲端 GPU 工作。

## 22. 首次安裝與環境建置

首次啟動：

1.  偵測作業系統。
2.  偵測 CPU、RAM、GPU。
3.  讓使用者選擇安裝、環境、專案及輸出資料夾。
4.  檢查 Docker、Python、FFmpeg、FFprobe 及必要工具。
5.  建立環境及安裝必要套件。
6.  建立資料庫及設定。
7.  啟動服務。
8.  執行健康檢查。
9.  進入 Dashboard。

支援自動偵測、手動指定路徑、版本檢查、安裝失敗提示、重新安裝、更新、移除及環境備份。

大型模型不應在首次安裝時全部下載，由使用者選擇需要的模型及服務。

## 23. 安全與權限

實作使用者登入、角色與專案權限、API Key
加密、憑證管理、工具白名單、檔案路徑限制、任務執行權限、操作紀錄、備份及恢復。

外部 Worker 必須經身分驗證。NAS 不應直接暴露不必要服務至公網。

## 24. 開發 Roadmap

1.  基礎平台：專案、登入、Dashboard、FastAPI、PostgreSQL、Redis、Docker、n8n。
2.  模型中心：Registry、Provider Adapter、憑證、測試、備援及費用。
3.  工具調用引擎：Tool Registry、API／CLI／SDK／Service
    Adapter、FFmpeg、FFprobe。
4.  設備及 Worker：Windows、Linux、Raspberry Pi、NAS、雲端 Worker。
5.  Character Studio：多角色、照片、Character Bible、一致性審核。
6.  前期製作：故事、劇本、場景、分鏡及 Prompt Studio。
7.  AI 生成：圖片、影片、分析、配音、音樂及音效。
8.  自動剪輯：Timeline、FFmpeg、字幕、音訊、轉場及品質審核。
9.  模型切換及任務恢復：額度偵測、備援、Prompt 轉換及 Checkpoint。
10. 完整電影製作：多 Agent、完整審核、輸出及發行準備。

## 25. MVP 第一個可執行版本

第一版優先完成：

1.  建立電影專案。
2.  新增多位角色及上傳照片。
3.  建立 Character Bible、Scene Bible 及 Shot List。
4.  Model Hub：至少接入一個實際文字模型及一個實際生成服務。
5.  Tool Execution Engine。
6.  FFmpeg 自動合併影片。
7.  FFprobe 檢查輸出。
8.  Whisper 產生字幕。
9.  任務進度及錯誤紀錄。
10. 專案保存及恢復。

MVP 必須可實際操作，不得以展示頁面或假資料取代功能。

功能狀態統一標示：`Planned`、`Not Configured`、`Mock`、`Connected`、`Tested`、`Available`。

## 26. 測試規格

### 模型測試

API Key、模型呼叫、能力相容性、額度不足偵測、備用模型及切換接續。

### 工具測試

安裝狀態、版本、CLI／SDK 執行、輸入檔案、輸出檔案及錯誤回報。

### 剪輯測試

多段影片合併、轉場、音樂混合、配音、字幕、解析度、FPS、格式及完整性。

### 恢復測試

模型點數用完、API 中斷、Worker 中斷、Raspberry Pi 重啟、Windows
關機、NAS 暫時離線及任務失敗。

## 27. 未來擴充

AI 預告片、電影海報、多語言配音及字幕、自動調色、角色聲音一致性、3D
人物、動作捕捉、虛擬攝影棚、多人協作、雲端 GPU
自動調度、成本最佳化及作品發布。

## 28. Codex 開發規範

1.  以本 README 作為主要開發規格。
2.  採用模組化架構。
3.  模型不得寫死在 Agent。
4.  工具執行方式不得寫死在 Agent。
5.  所有模型透過 Model Adapter。
6.  所有外部工具透過 Tool Adapter。
7.  所有任務有唯一 ID。
8.  重要任務可保存及恢復。
9.  模型及工具均須有測試。
10. API Key 必須安全管理。
11. 影音工具必須具備程式調用介面。
12. 不得以展示頁面取代實際功能。
13. 每階段完成測試並更新安裝文件、API 文件及資料庫 Schema。
14. 未實際測試的功能不得宣稱完成。

## 29. 最終系統目標

AI Film Studio
必須具備完整電影製作流程、多角色管理、人物一致性管理、多模型選擇、主要與備用模型、點數及預算管理、模型切換、任務接續、外部工具直接調用、自動剪輯、專業影音工具整合、多設備
Worker、NAS 儲存、n8n 工作流、多 Agent
協作、品質審核、版本管理及完整影片輸出。

核心不是把 AI
工具放在同一個網頁，而是建立一個能管理模型、調度設備、直接調用工具並持續完成電影製作任務的平台。

## 30. 第一階段實作優先順序

1.  Tool Execution Engine。
2.  Model Hub。
3.  Device Manager。
4.  Task Manager。
5.  Asset Manager。
6.  Character Studio。
7.  Scene Studio。
8.  Storyboard Studio。
9.  AI Generation。
10. Editing Studio。
11. Review Engine。
12. Complete Film Production Workflow。

先確保模型可以呼叫、工具可以執行、任務可以恢復，再逐步擴充電影製作能力。

**最終目標：使用者只需提供故事或素材，AI Film Studio
就能調度合適的模型、設備及外部工具，完成從劇本到最終電影成品的完整製作。**
