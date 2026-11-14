"""
AI Film Studio - 示範快速產出一部微電影 (端到端管線)
"""
import sys
import os
from pathlib import Path

# 加入根目錄到 Python Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.services.pipeline import FilmProductionPipeline
from backend.tool_engine.engine import ToolExecutionEngine
from backend.tool_engine.registry import ToolRegistry
from backend.tool_engine.security import ToolSecurityManager
from backend.tool_adapters.ffmpeg_adapter import FFmpegAdapter
from backend.tool_adapters.ffprobe_adapter import FFprobeAdapter
from backend.model_hub.registry import ModelRegistry
from backend.model_hub.router import ModelRouter
from backend.model_adapters.mock_adapter import MockModelAdapter


def main():
    print("=" * 60)
    print(" 🎬 AI Film Studio - 端到端微電影全自動製作示範")
    print("=" * 60)

    # 1. 建立工具引擎
    sec = ToolSecurityManager(allowed_directories=[os.getcwd()])
    reg = ToolRegistry()
    ffmpeg = FFmpegAdapter(security_manager=sec)
    ffprobe = FFprobeAdapter(security_manager=sec)
    reg.register_adapter(ffmpeg)
    reg.register_adapter(ffprobe)
    engine = ToolExecutionEngine(registry=reg, security_manager=sec)

    # 2. 建立模型中心
    model_reg = ModelRegistry()
    model_reg.register_adapter(MockModelAdapter(response_text="Scene 1: Neon reflections on rainy pavement."))
    model_router = ModelRouter(registry=model_reg)

    # 3. 建立生產管線
    pipeline = FilmProductionPipeline(
        storage_root="./storage",
        tool_engine=engine,
        model_router=model_router
    )

    project_id = "demo_film_001"
    prompt = "A cyberpunk hacker eludes drones in a high-tech underground subway."

    print(f"\n[1/6] 啟動專案: {project_id}")
    print(f"      劇本發想: {prompt}")

    result = pipeline.run_production(
        project_id=project_id,
        story_prompt=prompt,
        character_name="Kaelen",
        num_shots=2
    )

    if result.success:
        print("\n" + "=" * 60)
        print(" 🎉 電影製作成功！")
        print("=" * 60)
        print(f" 📹 成品影片路徑 : {result.master_video_path}")
        print(f" ⏱️ 影片總長度   : {result.total_runtime_seconds:.2f} 秒")
        print(f" 🎬 總鏡頭數量   : {result.total_shots}")
        print(f" 💾 Checkpoint 數: {result.checkpoints_count}")
        print(f" 🔍 品質審核狀態 : {result.review_report.overall_status.value}")
        print(f" 📊 品質評分     : {result.review_report.score * 100:.0f} 分")
        print("\n各項檢查項目明細:")
        for check in result.review_report.checks:
            status_icon = "✅" if check.passed else "❌"
            print(f"   {status_icon} {check.check_name}: {check.details}")
        print("=" * 60)
    else:
        print(f"\n❌ 製作失敗: {result.error_message}")


if __name__ == "__main__":
    main()
