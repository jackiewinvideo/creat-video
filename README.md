# AI Film Studio (v4.0)

> 完整 AI 電影製作、自動化剪輯與多模型協作平台

本專案詳細系統架構、Agent 設計、模型中心（Model Hub）、工具調用引擎（Tool Execution Engine）與完整開發規範，請參閱：
👉 **[README_AI_Film_Studio_v4.0.md](./README_AI_Film_Studio_v4.0.md)**

---

## 目錄結構概覽

```text
auto-creat-video/
├── frontend/               # Next.js 前端 (App, Components, Hooks, Services)
├── backend/                # FastAPI 後端 (Core, Models, Adapters, Tool Engine, Task Manager)
├── n8n/                    # n8n 工作流 (Workflows)
├── workers/                # 分散式節點 (Windows, Linux, Raspberry Pi, Cloud)
├── tools/                  # 本地工具整合 (FFmpeg, Blender, Whisper, Scripts)
├── projects/               # 電影專案實體檔案與資料
├── storage/                # 原始素材、生成檔案、字幕與快取
├── configs/                # 系統設定
├── docker/                 # Dockerfile 與容器化設定
├── docs/                   # 開發文件與 API 規範
├── scripts/                # 維運與安裝腳本
└── tests/                  # 全域整合測試
```
