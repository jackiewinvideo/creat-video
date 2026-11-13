import os
import shutil
import tempfile
import pytest

from backend.models.asset import AssetSourceType, AssetType
from backend.services.asset_manager import AssetManager
from backend.tool_adapters.ffmpeg_adapter import FFmpegAdapter
from backend.tool_adapters.ffprobe_adapter import FFprobeAdapter
from backend.tool_engine.security import ToolSecurityManager


@pytest.fixture
def temp_storage():
    d = tempfile.mkdtemp(prefix="ai_film_storage_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


def test_asset_ingest_and_ffprobe_metadata(temp_storage):
    sec = ToolSecurityManager(allowed_directories=[temp_storage, os.getcwd()])
    ffmpeg = FFmpegAdapter(security_manager=sec)
    ffprobe = FFprobeAdapter(security_manager=sec)

    # 1. Generate a 2-second real test video file
    raw_video = os.path.join(temp_storage, "sample_character_shot.mp4")
    res_gen = ffmpeg.generate_test_pattern(
        output_file=raw_video,
        duration=2.0,
        resolution="640x360",
        fps=24,
        color="green"
    )
    assert res_gen.success is True

    # 2. Ingest the video via AssetManager
    mgr = AssetManager(storage_root=temp_storage, ffprobe_adapter=ffprobe)
    asset = mgr.ingest_asset(
        source_file_path=raw_video,
        project_id="proj_matrix_01",
        asset_type=AssetType.VIDEO,
        source_type=AssetSourceType.AI_GENERATED,
        source_model_or_tool="ffmpeg",
        tags=["character_test", "matrix"],
        associated_character_id="char_neo_01"
    )

    assert asset.asset_id.startswith("asset_")
    assert asset.project_id == "proj_matrix_01"
    assert asset.asset_type == AssetType.VIDEO
    assert asset.resolution == "640x360"
    assert asset.fps == 24.0
    assert abs(asset.duration_seconds - 2.0) < 0.5
    assert len(asset.checksum_sha256) == 64
    assert os.path.exists(asset.file_path)

    # 3. Querying & Filtering
    neo_assets = mgr.list_assets(project_id="proj_matrix_01", character_id="char_neo_01")
    assert len(neo_assets) == 1
    assert neo_assets[0].asset_id == asset.asset_id

    tag_assets = mgr.list_assets(project_id="proj_matrix_01", tag="matrix")
    assert len(tag_assets) == 1

    # 4. Version increment test
    updated_video = os.path.join(temp_storage, "sample_character_shot_v2.mp4")
    ffmpeg.generate_test_pattern(
        output_file=updated_video,
        duration=3.0,
        resolution="640x360",
        fps=24,
        color="red"
    )

    v2_asset = mgr.create_new_version(
        asset_id=asset.asset_id,
        new_source_path=updated_video,
        source_model_or_tool="ffmpeg_v2"
    )
    assert v2_asset.version == 2
    assert v2_asset.source_model_or_tool == "ffmpeg_v2"
    assert os.path.exists(v2_asset.file_path)

    # 5. Persistence reload test
    new_mgr = AssetManager(storage_root=temp_storage, ffprobe_adapter=ffprobe)
    reloaded = new_mgr.get_asset(asset.asset_id)
    assert reloaded is not None
    assert reloaded.version == 2
    assert reloaded.associated_character_id == "char_neo_01"
