import base64
import logging
import math
import os
import random
from pathlib import Path
from typing import Optional
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import httpx

from backend.model_adapters.image_generation_adapter import ImageGenerationAdapter
from backend.model_hub.models import ModelModality, ModelRequest
from backend.tool_adapters.ffmpeg_adapter import FFmpegAdapter
from backend.tool_engine.models import ToolExecutionResult
from backend.tool_engine.security import ToolSecurityManager

logger = logging.getLogger(__name__)


class VisualGenerator:
    """
    Produces high-fidelity cinematic imagery and animates them into dynamic video shots.
    Supports both AI Cloud Text-to-Image (DALL-E / Imagen) and rich procedural rendering.
    """

    def __init__(self, ffmpeg_adapter: Optional[FFmpegAdapter] = None):
        sec = ToolSecurityManager()
        self.ffmpeg = ffmpeg_adapter or FFmpegAdapter(security_manager=sec)

    def generate_visual_still(
        self,
        prompt: str,
        character_name: str,
        shot_number: int,
        shot_type: str,
        output_image_path: str,
        width: int = 1280,
        height: int = 720
    ) -> str:
        """
        Generates a rich visual cinematic still.
        Attempts AI Cloud Generation if API keys are set, otherwise procedural cinematic rendering.
        """
        output_path = Path(output_image_path).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 1. Try Cloud AI image generation if OPENAI_API_KEY is available
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key and len(openai_key) > 10:
            try:
                logger.info(f"Generating AI image via OpenAI DALL-E 3 for shot {shot_number}...")
                adapter = ImageGenerationAdapter(api_key=openai_key, provider="openai")
                req = ModelRequest(
                    task_id=f"img_shot_{shot_number}",
                    modality=ModelModality.IMAGE,
                    prompt=prompt
                )
                res = adapter.generate(req)
                if res.success and res.media_urls:
                    img_data = httpx.get(res.media_urls[0], timeout=30.0).content
                    with open(output_path, "wb") as f:
                        f.write(img_data)
                    logger.info(f"AI image successfully generated: {output_path}")
                    return str(output_path)
            except Exception as e:
                logger.warning(f"Cloud AI image generation failed: {e}. Falling back to procedural visual engine.")

        # 2. Rich Procedural Cinematic Visual Engine (Guaranteed High-Quality Visuals)
        self._render_procedural_cinematic_scene(
            output_path=output_path,
            character_name=character_name,
            shot_number=shot_number,
            shot_type=shot_type,
            prompt=prompt,
            width=width,
            height=height
        )
        return str(output_path)

    def _render_procedural_cinematic_scene(
        self,
        output_path: Path,
        character_name: str,
        shot_number: int,
        shot_type: str,
        prompt: str,
        width: int,
        height: int
    ) -> None:
        """
        Draws a multi-layered cyberpunk / cinematic visual scene:
        - Layer 1: Atmospheric twilight/neon sky gradient with stars and moon/hologram
        - Layer 2: Distant skyscraper silhouettes with illuminated windows
        - Layer 3: Mid-ground futuristic structures with glowing neon signs
        - Layer 4: Reflective wet asphalt road with cyan & magenta light reflections
        - Layer 5: Character silhouette (trench coat, glowing cyber eye / visor)
        - Layer 6: Film grain, anamorphic cinematic letterbox bars, and camera HUD metadata
        """
        img = Image.new("RGB", (width, height), color=(10, 15, 26))
        draw = ImageDraw.Draw(img)

        # --- Layer 1: Gradient Sky ---
        # Deep blue to vibrant violet/magenta gradient
        for y in range(int(height * 0.65)):
            ratio = y / (height * 0.65)
            r = int(12 + ratio * 35)
            g = int(15 + ratio * 15)
            b = int(35 + ratio * 60)
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        # Distant moon / giant planetary sphere
        moon_x, moon_y, moon_r = int(width * 0.75), int(height * 0.22), 65
        draw.ellipse(
            [moon_x - moon_r, moon_y - moon_r, moon_x + moon_r, moon_y + moon_r],
            fill=(220, 240, 255),
            outline=(100, 200, 255)
        )

        # Ambient stars / dust motes
        random.seed(shot_number * 42)
        for _ in range(80):
            sx = random.randint(0, width)
            sy = random.randint(0, int(height * 0.5))
            draw.point((sx, sy), fill=(200, 230, 255))

        # --- Layer 2 & 3: Layered City Skyline ---
        # Far buildings
        x = 0
        while x < width:
            bw = random.randint(40, 90)
            bh = random.randint(int(height * 0.35), int(height * 0.6))
            draw.rectangle([x, height * 0.65 - bh, x + bw, height * 0.65], fill=(20, 28, 48))
            # Glowing windows
            for wy in range(int(height * 0.65 - bh + 15), int(height * 0.65 - 10), 18):
                for wx in range(x + 8, x + bw - 8, 14):
                    if random.random() > 0.4:
                        win_color = (0, 220, 255) if random.random() > 0.5 else (255, 180, 50)
                        draw.rectangle([wx, wy, wx + 4, wy + 6], fill=win_color)
            x += bw + random.randint(5, 15)

        # Foreground structures & neon signs
        x = 0
        while x < width:
            bw = random.randint(60, 120)
            bh = random.randint(int(height * 0.25), int(height * 0.5))
            draw.rectangle([x, height * 0.68 - bh, x + bw, height * 0.68], fill=(12, 18, 30))
            # Neon billboard
            if random.random() > 0.6:
                draw.rectangle([x + 15, height * 0.68 - bh + 20, x + bw - 15, height * 0.68 - bh + 45], fill=(244, 63, 94))
            x += bw + random.randint(10, 25)

        # --- Layer 4: Reflective Street Ground ---
        ground_top = int(height * 0.65)
        for y in range(ground_top, height):
            ratio = (y - ground_top) / (height - ground_top)
            # Wet road color
            draw.line([(0, y), (width, y)], fill=(int(10 + ratio * 15), int(14 + ratio * 20), int(22 + ratio * 30)))

        # Neon light streaks / reflections on wet asphalt
        for _ in range(25):
            rx = random.randint(100, width - 100)
            ry = random.randint(ground_top + 10, height - 20)
            rw = random.randint(40, 160)
            rcolor = (0, 240, 255, 120) if random.random() > 0.5 else (255, 0, 128, 120)
            draw.line([(rx, ry), (rx + rw, ry)], fill=(rcolor[0], rcolor[1], rcolor[2]), width=2)

        # --- Layer 5: Character Silhouette ---
        # Center or rule of thirds positioning
        char_x = int(width * 0.42 if shot_number % 2 == 1 else width * 0.58)
        char_base_y = int(height * 0.88)

        if "CLOSE_UP" in shot_type.upper():
            # Bust / Close-up view
            head_r = 55
            head_y = char_base_y - 220
            # Shoulders
            draw.polygon([
                (char_x - 120, char_base_y),
                (char_x + 120, char_base_y),
                (char_x + 70, head_y + 40),
                (char_x - 70, head_y + 40)
            ], fill=(5, 8, 15))
            # Head
            draw.ellipse([char_x - head_r, head_y - head_r, char_x + head_r, head_y + head_r], fill=(5, 8, 15))
            # Glowing Cyber Eye
            eye_x = char_x - 12 if shot_number % 2 == 1 else char_x + 12
            draw.ellipse([eye_x - 6, head_y - 8, eye_x + 6, head_y + 4], fill=(0, 255, 240))
        else:
            # Full body / Medium Shot
            head_r = 22
            head_y = char_base_y - 170
            # Coat / Body
            draw.polygon([
                (char_x - 35, char_base_y),
                (char_x + 35, char_base_y),
                (char_x + 22, head_y + 30),
                (char_x - 22, head_y + 30)
            ], fill=(6, 10, 18))
            # Head
            draw.ellipse([char_x - head_r, head_y - head_r, char_x + head_r, head_y + head_r], fill=(6, 10, 18))
            # Glowing cyber visor rim
            draw.line([(char_x - 10, head_y - 2), (char_x + 10, head_y - 2)], fill=(0, 255, 240), width=3)

        # --- Layer 6: Cinematic Letterboxing (Cinemascope 2.39:1) ---
        bar_height = int(height * 0.08)
        draw.rectangle([0, 0, width, bar_height], fill=(0, 0, 0))
        draw.rectangle([0, height - bar_height, width, height], fill=(0, 0, 0))

        # Cinematic Camera HUD / Telemetry Overlay
        hud_text = f"AI FILM STUDIO // SCENE 01 / SHOT {shot_number:02d} // {shot_type} // {character_name.upper()}"
        draw.text((25, bar_height + 15), hud_text, fill=(0, 240, 255))
        draw.text((25, height - bar_height - 25), f"PROMPT: {prompt[:80]}...", fill=(180, 190, 210))

        # Save finalized high-res frame
        img.save(str(output_path), quality=95)
        logger.info(f"Rendered cinematic frame to: {output_path}")

    def animate_still_to_video(
        self,
        image_path: str,
        output_video_path: str,
        duration: float = 2.0,
        camera_movement: str = "DOLLY_IN",
        resolution: str = "1280x720",
        fps: int = 24
    ) -> ToolExecutionResult:
        """
        Uses FFmpeg's zoompan filter to create cinematic camera movement from the image still.
        """
        val_img = Path(image_path).resolve()
        val_out = Path(output_video_path).resolve()
        val_out.parent.mkdir(parents=True, exist_ok=True)

        frames = int(duration * fps)

        # Determine zoompan parameters based on camera movement
        if "PAN_RIGHT" in camera_movement.upper():
            # Pan from left to right
            vf = (
                f"zoompan=z='1.2':"
                f"x='(on/{frames})*(iw-iw/1.2)':"
                f"y='(ih-ih/1.2)/2':"
                f"d={frames}:s={resolution}:fps={fps}"
            )
        elif "PAN_LEFT" in camera_movement.upper():
            # Pan from right to left
            vf = (
                f"zoompan=z='1.2':"
                f"x='(1-on/{frames})*(iw-iw/1.2)':"
                f"y='(ih-ih/1.2)/2':"
                f"d={frames}:s={resolution}:fps={fps}"
            )
        elif "DOLLY_IN" in camera_movement.upper() or "ZOOM" in camera_movement.upper():
            # Smooth optical zoom into the center
            vf = (
                f"zoompan=z='min(zoom+0.002,1.35)':"
                f"x='iw/2-(iw/zoom/2)':"
                f"y='ih/2-(ih/zoom/2)':"
                f"d={frames}:s={resolution}:fps={fps}"
            )
        else:
            # Subtle breathing motion
            vf = (
                f"zoompan=z='min(zoom+0.0008,1.15)':"
                f"x='iw/2-(iw/zoom/2)':"
                f"y='ih/2-(ih/zoom/2)':"
                f"d={frames}:s={resolution}:fps={fps}"
            )

        args = [
            "-y",
            "-loop", "1",
            "-i", str(val_img),
            "-f", "lavfi",
            "-i", "anullsrc=r=44100:cl=stereo",
            "-vf", vf,
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-t", str(duration),
            str(val_out)
        ]

        res = self.ffmpeg.run_command(args, timeout=60)
        if res.success and val_out.exists():
            res.output_files = [str(val_out)]
        return res
