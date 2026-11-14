import base64
import hashlib
import logging
import math
import os
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFilter
import httpx

from backend.model_adapters.image_generation_adapter import ImageGenerationAdapter
from backend.model_hub.models import ModelModality, ModelRequest
from backend.tool_adapters.ffmpeg_adapter import FFmpegAdapter
from backend.tool_engine.models import ToolExecutionResult
from backend.tool_engine.security import ToolSecurityManager

logger = logging.getLogger(__name__)


class VisualGenerator:
    """
    Produces dynamic, prompt-aware cinematic imagery and converts them into moving video shots.
    Supports:
    1. Cloud AI Image Generation (OpenAI DALL-E 3 / Gemini Imagen) when API Key is present.
    2. Dynamic Prompt-Driven Procedural Cinematic Engine when running locally.
       Analyzes prompt semantics (Space, Cyberpunk, Fantasy, Desert, Ocean, Medieval, Noir)
       and dynamically constructs corresponding environments, lighting, and focal elements.
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
                logger.warning(f"Cloud AI image generation failed: {e}. Falling back to prompt-driven visual engine.")

        # 2. Dynamic Prompt-Driven Procedural Engine
        self._render_dynamic_cinematic_scene(
            output_path=output_path,
            character_name=character_name,
            shot_number=shot_number,
            shot_type=shot_type,
            prompt=prompt,
            width=width,
            height=height
        )
        return str(output_path)

    def _detect_theme(self, prompt: str) -> str:
        p = prompt.lower()
        if any(w in p for w in ["space", "galaxy", "astronaut", "spaceship", "planet", "star", "cosmic", "orbit"]):
            return "SPACE"
        if any(w in p for w in ["forest", "tree", "nature", "jungle", "garden", "woods", "mountain", "river", "druid"]):
            return "NATURE"
        if any(w in p for w in ["desert", "sand", "dune", "wasteland", "pyramid", "ruins", "sahara", "post-apoc"]):
            return "DESERT"
        if any(w in p for w in ["ocean", "sea", "underwater", "water", "beach", "ship", "boat", "pirate", "wave"]):
            return "OCEAN"
        if any(w in p for w in ["castle", "medieval", "knight", "dragon", "sword", "palace", "throne", "kingdom"]):
            return "MEDIEVAL"
        if any(w in p for w in ["noir", "detective", "shadow", "fog", "rain", "black and white", "dark", "smoke"]):
            return "NOIR"
        # Default to futuristic cyberpunk / sci-fi city
        return "CYBERPUNK"

    def _render_dynamic_cinematic_scene(
        self,
        output_path: Path,
        character_name: str,
        shot_number: int,
        shot_type: str,
        prompt: str,
        width: int,
        height: int
    ) -> None:
        # Seed uniquely based on PROMPT content + shot number + character
        seed_str = f"{prompt}_{character_name}_{shot_number}"
        seed_val = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed_val)

        theme = self._detect_theme(prompt)
        logger.info(f"Rendering scene for shot {shot_number}: detected theme='{theme}' from prompt")

        img = Image.new("RGB", (width, height), color=(10, 10, 15))
        draw = ImageDraw.Draw(img)

        # -------------------------------------------------------------
        # THEME 1: SPACE & COSMOS
        # -------------------------------------------------------------
        if theme == "SPACE":
            # Deep cosmic gradient
            for y in range(height):
                r = int(5 + (y / height) * 25)
                g = int(2 + (y / height) * 10)
                b = int(20 + (y / height) * 50)
                draw.line([(0, y), (width, y)], fill=(r, g, b))

            # Distant luminous nebula
            nebula_color = rng.choice([(147, 51, 234), (6, 182, 212), (236, 72, 153), (59, 130, 246)])
            for _ in range(60):
                nx = rng.randint(int(width * 0.2), int(width * 0.8))
                ny = rng.randint(int(height * 0.1), int(height * 0.7))
                nr = rng.randint(40, 120)
                draw.ellipse([nx - nr, ny - nr, nx + nr, ny + nr], fill=(nebula_color[0] // 4, nebula_color[1] // 4, nebula_color[2] // 4))

            # Thousands of twinkling stars
            for _ in range(250):
                sx = rng.randint(0, width)
                sy = rng.randint(0, height)
                s_bright = rng.randint(180, 255)
                draw.point((sx, sy), fill=(s_bright, s_bright, 255))

            # Massive Ringed Planet or Moon
            px, py, pr = int(width * 0.75), int(height * 0.35), rng.randint(70, 110)
            draw.ellipse([px - pr, py - pr, px + pr, py + pr], fill=(220, 180, 120), outline=(255, 230, 180))
            draw.arc([px - pr * 1.6, py - pr * 0.4, px + pr * 1.6, py + pr * 0.4], start=0, end=360, fill=(200, 160, 100), width=3)

            # Spacecraft / Space Station silhouette
            ship_x, ship_y = int(width * 0.35), int(height * 0.6)
            draw.polygon([
                (ship_x - 120, ship_y),
                (ship_x + 80, ship_y - 30),
                (ship_x + 140, ship_y),
                (ship_x + 80, ship_y + 30)
            ], fill=(25, 30, 45))
            # Thruster glow
            draw.ellipse([ship_x - 145, ship_y - 12, ship_x - 110, ship_y + 12], fill=(0, 240, 255))

        # -------------------------------------------------------------
        # THEME 2: NATURE & FANTASY FOREST
        # -------------------------------------------------------------
        elif theme == "NATURE":
            # Golden hour / lush emerald mist gradient
            for y in range(int(height * 0.65)):
                ratio = y / (height * 0.65)
                r = int(245 - ratio * 180)
                g = int(180 - ratio * 100)
                b = int(120 - ratio * 90)
                draw.line([(0, y), (width, y)], fill=(r, g, b))

            # Distant mountain silhouettes
            for mx in range(0, width, 180):
                draw.polygon([
                    (mx - 80, height * 0.65),
                    (mx + 90, height * 0.35 + rng.randint(-30, 30)),
                    (mx + 260, height * 0.65)
                ], fill=(25, 45, 40))

            # Forest ground
            ground_y = int(height * 0.65)
            for y in range(ground_y, height):
                draw.line([(0, y), (width, y)], fill=(15, 30, 20))

            # Pine trees & ancient canopy
            for tx in range(0, width, 45):
                th = rng.randint(140, 260)
                draw.polygon([
                    (tx - 35, ground_y + 40),
                    (tx, ground_y - th),
                    (tx + 35, ground_y + 40)
                ], fill=(10, 25, 18))

            # Floating fireflies / magical glowing spores
            for _ in range(50):
                fx = rng.randint(0, width)
                fy = rng.randint(ground_y - 120, height - 30)
                draw.ellipse([fx - 3, fy - 3, fx + 3, fy + 3], fill=(163, 230, 53))

        # -------------------------------------------------------------
        # THEME 3: DESERT & WASTELAND
        # -------------------------------------------------------------
        elif theme == "DESERT":
            # Blazing sunset / amber wasteland sky
            for y in range(int(height * 0.6)):
                ratio = y / (height * 0.6)
                r = int(255 - ratio * 40)
                g = int(140 - ratio * 90)
                b = int(40 + ratio * 20)
                draw.line([(0, y), (width, y)], fill=(r, g, b))

            # Blazing sun
            draw.ellipse([width * 0.5 - 50, height * 0.25 - 50, width * 0.5 + 50, height * 0.25 + 50], fill=(255, 240, 180))

            # Sand dunes (layered curves)
            dune_y = int(height * 0.55)
            for d_idx, d_col in enumerate([(190, 100, 30), (160, 80, 25), (120, 60, 20)]):
                pts = [(0, height)]
                for x in range(0, width + 50, 50):
                    dy = dune_y + d_idx * 40 + int(math.sin(x * 0.005 + d_idx) * 35)
                    pts.append((x, dy))
                pts.append((width, height))
                draw.polygon(pts, fill=d_col)

        # -------------------------------------------------------------
        # THEME 4: OCEAN & SEASCAPE
        # -------------------------------------------------------------
        elif theme == "OCEAN":
            # Dramatic storm or twilight sky
            for y in range(int(height * 0.55)):
                ratio = y / (height * 0.55)
                r = int(40 + ratio * 20)
                g = int(60 + ratio * 30)
                b = int(100 + ratio * 60)
                draw.line([(0, y), (width, y)], fill=(r, g, b))

            # Ocean water & waves
            ocean_top = int(height * 0.55)
            for y in range(ocean_top, height):
                ratio = (y - ocean_top) / (height - ocean_top)
                draw.line([(0, y), (width, y)], fill=(int(10 + ratio * 15), int(30 + ratio * 40), int(60 + ratio * 60)))

            # Distant ship / vessel silhouette
            sx, sy = int(width * 0.65), ocean_top + 10
            draw.polygon([(sx - 40, sy + 15), (sx + 50, sy + 15), (sx + 35, sy - 20), (sx - 20, sy - 20)], fill=(10, 15, 25))
            draw.line([(sx, sy - 20), (sx, sy - 55)], fill=(10, 15, 25), width=2)

        # -------------------------------------------------------------
        # THEME 5: MEDIEVAL & CITADEL
        # -------------------------------------------------------------
        elif theme == "MEDIEVAL":
            # Crimson twilight dawn
            for y in range(int(height * 0.6)):
                ratio = y / (height * 0.6)
                r = int(180 - ratio * 100)
                g = int(50 + ratio * 10)
                b = int(70 + ratio * 40)
                draw.line([(0, y), (width, y)], fill=(r, g, b))

            # Fortress and battlements
            bx = int(width * 0.25)
            by = int(height * 0.6)
            draw.rectangle([bx, by - 160, bx + 220, by], fill=(20, 20, 30))
            # Towers
            draw.rectangle([bx - 40, by - 220, bx + 10, by], fill=(15, 15, 25))
            draw.polygon([(bx - 50, by - 220), (bx - 15, by - 270), (bx + 20, by - 220)], fill=(40, 20, 25))
            draw.rectangle([bx + 180, by - 220, bx + 230, by], fill=(15, 15, 25))
            draw.polygon([(bx + 170, by - 220), (bx + 205, by - 270), (bx + 240, by - 220)], fill=(40, 20, 25))

        # -------------------------------------------------------------
        # THEME 6: CYBERPUNK & NEO-CITY (Default)
        # -------------------------------------------------------------
        else:
            # Gradient Neon Sky
            for y in range(int(height * 0.65)):
                ratio = y / (height * 0.65)
                r = int(15 + ratio * 45)
                g = int(10 + ratio * 20)
                b = int(45 + ratio * 85)
                draw.line([(0, y), (width, y)], fill=(r, g, b))

            # Distant skyscrapers with illuminated windows
            x = 0
            while x < width:
                bw = rng.randint(45, 95)
                bh = rng.randint(int(height * 0.35), int(height * 0.62))
                draw.rectangle([x, height * 0.65 - bh, x + bw, height * 0.65], fill=(18, 24, 42))
                # Windows
                for wy in range(int(height * 0.65 - bh + 15), int(height * 0.65 - 10), 16):
                    for wx in range(x + 8, x + bw - 8, 14):
                        if rng.random() > 0.35:
                            wcol = (0, 240, 255) if rng.random() > 0.5 else (255, 190, 40)
                            draw.rectangle([wx, wy, wx + 4, wy + 6], fill=wcol)
                x += bw + rng.randint(8, 20)

            # Reflective street with neon streaks
            ground_top = int(height * 0.65)
            for y in range(ground_top, height):
                draw.line([(0, y), (width, y)], fill=(12, 16, 26))
            for _ in range(30):
                rx = rng.randint(80, width - 80)
                ry = rng.randint(ground_top + 10, height - 25)
                rw = rng.randint(40, 150)
                rcolor = (0, 255, 240) if rng.random() > 0.5 else (255, 0, 128)
                draw.line([(rx, ry), (rx + rw, ry)], fill=rcolor, width=2)

        # -------------------------------------------------------------
        # CHARACTER SILHOUETTE (Adapts to Shot Type & Theme)
        # -------------------------------------------------------------
        char_x = int(width * 0.44 if shot_number % 2 == 1 else width * 0.56)
        char_base_y = int(height * 0.88)

        if "CLOSE_UP" in shot_type.upper():
            # Bust / Close-up
            head_r = 65
            head_y = char_base_y - 230
            draw.polygon([
                (char_x - 140, char_base_y),
                (char_x + 140, char_base_y),
                (char_x + 80, head_y + 45),
                (char_x - 80, head_y + 45)
            ], fill=(8, 10, 18))
            draw.ellipse([char_x - head_r, head_y - head_r, char_x + head_r, head_y + head_r], fill=(8, 10, 18))
            # Glowing Eye / Visor
            eye_col = (0, 255, 240) if theme in ("CYBERPUNK", "SPACE") else (255, 200, 80)
            draw.ellipse([char_x - 10, head_y - 8, char_x + 10, head_y + 4], fill=eye_col)
        else:
            # Medium / Wide shot
            head_r = 24
            head_y = char_base_y - 180
            draw.polygon([
                (char_x - 38, char_base_y),
                (char_x + 38, char_base_y),
                (char_x + 24, head_y + 32),
                (char_x - 24, head_y + 32)
            ], fill=(8, 10, 18))
            draw.ellipse([char_x - head_r, head_y - head_r, char_x + head_r, head_y + head_r], fill=(8, 10, 18))
            draw.line([(char_x - 12, head_y - 2), (char_x + 12, head_y - 2)], fill=(0, 255, 240), width=3)

        # -------------------------------------------------------------
        # CINEMATIC LETTERBOXING (Cinemascope 2.39:1) & TELEMETRY
        # -------------------------------------------------------------
        bar_h = int(height * 0.08)
        draw.rectangle([0, 0, width, bar_h], fill=(0, 0, 0))
        draw.rectangle([0, height - bar_h, width, height], fill=(0, 0, 0))

        # Dynamic HUD info reflecting the REAL prompt and theme
        hud_header = f"AI FILM STUDIO // {theme} SCENE // SHOT {shot_number:02d} [{shot_type}] // {character_name.upper()}"
        draw.text((25, bar_h + 15), hud_header, fill=(0, 240, 255))
        draw.text((25, height - bar_h - 25), f"THEME: {theme} | PROMPT: {prompt[:85]}...", fill=(200, 210, 230))

        img.save(str(output_path), quality=95)
        logger.info(f"Generated dynamic visual still ({theme}) saved to {output_path}")

    def animate_still_to_video(
        self,
        image_path: str,
        output_video_path: str,
        duration: float = 2.0,
        camera_movement: str = "DOLLY_IN",
        resolution: str = "1280x720",
        fps: int = 24
    ) -> ToolExecutionResult:
        val_img = Path(image_path).resolve()
        val_out = Path(output_video_path).resolve()
        val_out.parent.mkdir(parents=True, exist_ok=True)

        frames = int(duration * fps)

        if "PAN_RIGHT" in camera_movement.upper():
            vf = f"zoompan=z='1.2':x='(on/{frames})*(iw-iw/1.2)':y='(ih-ih/1.2)/2':d={frames}:s={resolution}:fps={fps}"
        elif "PAN_LEFT" in camera_movement.upper():
            vf = f"zoompan=z='1.2':x='(1-on/{frames})*(iw-iw/1.2)':y='(ih-ih/1.2)/2':d={frames}:s={resolution}:fps={fps}"
        elif "DOLLY_IN" in camera_movement.upper() or "ZOOM" in camera_movement.upper():
            vf = f"zoompan=z='min(zoom+0.002,1.35)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={resolution}:fps={fps}"
        else:
            vf = f"zoompan=z='min(zoom+0.0008,1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={resolution}:fps={fps}"

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
