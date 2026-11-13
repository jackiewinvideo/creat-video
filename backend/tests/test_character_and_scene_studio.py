import os
import shutil
import tempfile
import pytest

from backend.models.character import (
    CharacterAppearance,
    CharacterCostume,
    CharacterIdentity,
    ConsistencyReviewStatus,
)
from backend.models.storyboard import Shot
from backend.services.character_studio import CharacterStudio
from backend.services.scene_studio import SceneStudio
from backend.services.storyboard_studio import StoryboardStudio


@pytest.fixture
def temp_workspace():
    d = tempfile.mkdtemp(prefix="ai_film_studios_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


def test_character_studio_lifecycle(temp_workspace):
    studio = CharacterStudio(storage_root=temp_workspace)

    char = studio.create_character(
        project_id="proj_neo_01",
        name="Elena Cross",
        role_description="Rebel Hacker",
        identity=CharacterIdentity(facial_features="Cybernetic scar on left eye", age=26, gender="female"),
        appearance=CharacterAppearance(hair_style="Undercut", hair_color="Neon Purple", skin_tone="Fair", body_build="Slim"),
        costumes=[
            CharacterCostume(top="Leather jacket with fiber optic seams", bottom="Cargo pants")
        ]
    )

    assert char.character_id.startswith("char_")
    assert char.name == "Elena Cross"

    # Bible generation
    bible = studio.generate_project_character_bible("proj_neo_01")
    assert "Elena Cross" in bible
    assert "Neon Purple" in bible["Elena Cross"]["appearance_prompt"]

    # Consistency review test
    res_pass = studio.evaluate_consistency(char.character_id, {"hair_color": "Neon Purple", "gender": "female"})
    assert res_pass == ConsistencyReviewStatus.PASS

    res_fail = studio.evaluate_consistency(char.character_id, {"gender": "male", "hair_color": "Blonde"})
    assert res_fail in (ConsistencyReviewStatus.FAIL, ConsistencyReviewStatus.REVIEW)


def test_scene_and_storyboard_studios(temp_workspace):
    scene_studio = SceneStudio(storage_root=temp_workspace)
    sb_studio = StoryboardStudio(storage_root=temp_workspace)

    scene = scene_studio.create_scene(
        project_id="proj_neo_01",
        name="The Undercity Bar",
        description="Smoky neon underground club",
        location_type="INT",
        time_of_day="NIGHT",
        lighting="Moody red and cyan backlighting"
    )

    sb = sb_studio.create_storyboard(project_id="proj_neo_01", title="Intro Sequence")
    shot = Shot(
        project_id="proj_neo_01",
        scene_id=scene.scene_id,
        shot_number=1,
        shot_type="MEDIUM",
        camera_movement="PAN_RIGHT",
        visual_description="Protagonist sips a glowing synthetic cocktail",
        estimated_duration=3.5
    )
    sb_studio.add_shot(sb.storyboard_id, shot)

    reloaded_sb = sb_studio.get_storyboard(sb.storyboard_id)
    assert len(reloaded_sb.shots) == 1
    assert reloaded_sb.total_duration() == 3.5

    # Test prompt compilation
    char_bibles = {
        "Elena": {
            "identity_prompt": "26yo female, cyber scar",
            "costume_prompt": "leather jacket"
        }
    }
    prompts = sb_studio.compile_shot_prompts(shot, char_bibles, scene.to_scene_bible())
    assert "MEDIUM" in prompts["image_prompt"]
    assert "PAN_RIGHT" in prompts["video_prompt"]
