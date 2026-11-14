"""
AI Film Studio - 快速啟動伺服器腳本
"""
import uvicorn

if __name__ == "__main__":
    print("=" * 60)
    print(" 🎬 AI Film Studio Core API 啟動中...")
    print(" 📍 介面位址: http://localhost:8000")
    print(" 📖 API 文件 (Swagger UI): http://localhost:8000/docs")
    print("=" * 60)
    uvicorn.run("backend.api.main:app", host="127.0.0.1", port=8000, reload=True)
