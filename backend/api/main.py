import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.device_manager.manager import DeviceManager
from backend.editing.editor import EditingStudio
from backend.model_hub.models import ModelModality, ModelRegistration, ModelRequest
from backend.model_hub.registry import ModelRegistry
from backend.model_hub.router import ModelRouter
from backend.models.asset import AssetType, MediaAsset
from backend.models.character import Character, CharacterAppearance, CharacterIdentity
from backend.models.scene import Scene
from backend.models.storyboard import Storyboard
from backend.services.asset_manager import AssetManager
from backend.services.character_studio import CharacterStudio
from backend.services.pipeline import FilmProductionPipeline, FilmProductionResult
from backend.services.review_engine import ReviewEngine
from backend.services.scene_studio import SceneStudio
from backend.services.storyboard_studio import StoryboardStudio
from backend.task_manager.manager import TaskManager
from backend.tool_adapters.ffmpeg_adapter import FFmpegAdapter
from backend.tool_adapters.ffprobe_adapter import FFprobeAdapter
from backend.tool_engine.engine import ToolExecutionEngine
from backend.tool_engine.registry import ToolRegistry
from backend.tool_engine.security import ToolSecurityManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai_film_studio")

app = FastAPI(
    title="AI Film Studio Core API",
    version="4.0.0",
    description="Unified API for multi-model autonomous film production, automated editing, and worker orchestration."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Core Subsystems
sec_manager = ToolSecurityManager()
tool_registry = ToolRegistry()
tool_registry.register_adapter(FFmpegAdapter(security_manager=sec_manager))
tool_registry.register_adapter(FFprobeAdapter(security_manager=sec_manager))
tool_engine = ToolExecutionEngine(registry=tool_registry, security_manager=sec_manager)

model_registry = ModelRegistry()
model_router = ModelRouter(registry=model_registry)

device_manager = DeviceManager()
task_manager = TaskManager()
asset_manager = AssetManager()
character_studio = CharacterStudio()
scene_studio = SceneStudio()
storyboard_studio = StoryboardStudio()
editing_studio = EditingStudio(tool_engine=tool_engine)
review_engine = ReviewEngine()

pipeline = FilmProductionPipeline(
    tool_engine=tool_engine,
    model_router=model_router,
    task_manager=task_manager,
    asset_manager=asset_manager,
    character_studio=character_studio,
    scene_studio=scene_studio,
    storyboard_studio=storyboard_studio,
    editing_studio=editing_studio,
    review_engine=review_engine
)


# Ensure storage and static paths exist
STORAGE_DIR = Path("./storage").resolve()
STATIC_DIR = Path("./frontend/static").resolve()
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)

# Mount storage directory for direct video/media streaming in browser
app.mount("/storage", StaticFiles(directory=str(STORAGE_DIR)), name="storage")

# Root route serving the Interactive Film Studio Web Terminal
@app.get("/", response_class=FileResponse)
def get_terminal_dashboard():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    raise HTTPException(status_code=404, detail="Terminal UI not found.")


# --- Health & System ---
@app.get("/api/health")
def get_health():
    return {
        "status": "healthy",
        "version": "4.0.0",
        "local_device_id": device_manager.local_device_id
    }


# --- Device Manager ---
@app.get("/api/devices")
def list_devices():
    return device_manager.list_devices()


# --- Tool Engine ---
@app.get("/api/tools")
def list_tools():
    return tool_registry.list_tools()


@app.post("/api/tools/health_check")
def check_tools():
    return tool_registry.check_all_tools()


# --- Model Hub ---
@app.get("/api/models")
def list_models(modality: Optional[ModelModality] = None):
    return model_registry.list_models(modality=modality)


@app.post("/api/models/generate")
def generate_model_content(req: ModelRequest):
    res = model_router.execute(req)
    if not res.success:
        raise HTTPException(status_code=500, detail=res.error_message)
    return res


# --- Asset Manager ---
@app.get("/api/projects/{project_id}/assets")
def list_project_assets(project_id: str, asset_type: Optional[AssetType] = None):
    return asset_manager.list_assets(project_id=project_id, asset_type=asset_type)


# --- Character Studio ---
class CreateCharacterPayload(BaseModel):
    name: str
    role_description: str
    identity: CharacterIdentity
    appearance: CharacterAppearance


@app.post("/api/projects/{project_id}/characters")
def create_character(project_id: str, payload: CreateCharacterPayload):
    return character_studio.create_character(
        project_id=project_id,
        name=payload.name,
        role_description=payload.role_description,
        identity=payload.identity,
        appearance=payload.appearance
    )


@app.get("/api/projects/{project_id}/characters")
def list_characters(project_id: str):
    return character_studio.list_characters(project_id)


# --- Task Manager ---
@app.get("/api/tasks")
def list_tasks(project_id: Optional[str] = None):
    return task_manager.list_tasks(project_id=project_id)


@app.get("/api/tasks/{task_id}")
def get_task(task_id: str):
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.post("/api/tasks/{task_id}/resume")
def resume_task(task_id: str):
    return task_manager.resume_task(task_id)


# --- Production Pipeline ---
class PipelineRunPayload(BaseModel):
    story_prompt: str
    character_name: str = "Elena"
    num_shots: int = 2


@app.post("/api/projects/{project_id}/produce", response_model=FilmProductionResult)
def run_film_pipeline(project_id: str, payload: PipelineRunPayload):
    res = pipeline.run_production(
        project_id=project_id,
        story_prompt=payload.story_prompt,
        character_name=payload.character_name,
        num_shots=payload.num_shots
    )
    if not res.success:
        raise HTTPException(status_code=500, detail=res.error_message)
    return res
