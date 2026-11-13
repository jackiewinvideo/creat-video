import os
import platform
import shutil
import socket
import subprocess
import time
from typing import Dict, List, Optional
import psutil

from backend.device_manager.models import (
    DeviceProfile,
    DeviceRole,
    DeviceStatus,
    OSInfo,
    CPUInfo,
    RAMInfo,
    GPUInfo,
    DiskInfo,
    ToolAvailability,
)


class DeviceDetector:
    """
    Performs comprehensive hardware, operating system, and software tool inspection.
    """

    @staticmethod
    def detect_os() -> OSInfo:
        return OSInfo(
            system=platform.system(),
            release=platform.release(),
            version=platform.version(),
            architecture=platform.machine(),
            hostname=socket.gethostname()
        )

    @staticmethod
    def detect_cpu() -> CPUInfo:
        physical = psutil.cpu_count(logical=False) or 1
        logical = psutil.cpu_count(logical=True) or 1
        usage = psutil.cpu_percent(interval=0.1)
        return CPUInfo(
            physical_cores=physical,
            logical_cores=logical,
            current_usage_percent=usage
        )

    @staticmethod
    def detect_ram() -> RAMInfo:
        vm = psutil.virtual_memory()
        return RAMInfo(
            total_gb=round(vm.total / (1024**3), 2),
            available_gb=round(vm.available / (1024**3), 2),
            usage_percent=vm.percent
        )

    @staticmethod
    def detect_disks(target_paths: Optional[List[str]] = None) -> List[DiskInfo]:
        paths = target_paths or [os.getcwd()]
        disks = []
        for p in paths:
            try:
                usage = psutil.disk_usage(p)
                disks.append(DiskInfo(
                    mount_point=p,
                    total_gb=round(usage.total / (1024**3), 2),
                    free_gb=round(usage.free / (1024**3), 2),
                    usage_percent=usage.percent
                ))
            except Exception:
                pass
        return disks

    @staticmethod
    def detect_gpus() -> List[GPUInfo]:
        gpus: List[GPUInfo] = []
        # 1. Try nvidia-smi
        nvidia_smi = shutil.which("nvidia-smi")
        if nvidia_smi:
            try:
                cmd = [
                    nvidia_smi,
                    "--query-gpu=name,memory.total,memory.free,driver_version",
                    "--format=csv,noheader,nounits"
                ]
                output = subprocess.check_output(cmd, text=True, timeout=5)
                for line in output.strip().splitlines():
                    parts = [p.strip() for p in line.split(",")]
                    if len(parts) >= 4:
                        name, total_mb, free_mb, driver_ver = parts[:4]
                        gpus.append(GPUInfo(
                            name=name,
                            vram_total_mb=float(total_mb),
                            vram_free_mb=float(free_mb),
                            driver_version=driver_ver,
                            vendor="NVIDIA"
                        ))
            except Exception:
                pass

        # 2. Windows fallback / complementary via PowerShell if no NVIDIA or additional GPUs
        if not gpus and platform.system() == "Windows":
            try:
                ps_cmd = [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    "Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name"
                ]
                output = subprocess.check_output(ps_cmd, text=True, timeout=5)
                for line in output.strip().splitlines():
                    name = line.strip()
                    if name:
                        gpus.append(GPUInfo(
                            name=name,
                            vram_total_mb=0.0,
                            vram_free_mb=0.0,
                            vendor="Intel/AMD/Generic"
                        ))
            except Exception:
                pass

        return gpus

    @staticmethod
    def detect_tools() -> Dict[str, ToolAvailability]:
        tools_to_check = {
            "ffmpeg": ["ffmpeg", "-version"],
            "ffprobe": ["ffprobe", "-version"],
            "python": ["python", "--version"],
            "docker": ["docker", "--version"],
            "blender": ["blender", "--version"],
            "whisper": ["whisper", "--help"]
        }

        detected = {}
        for name, cmd in tools_to_check.items():
            exe_path = shutil.which(cmd[0])
            is_installed = False
            version_str = None

            if exe_path:
                is_installed = True
                try:
                    res = subprocess.run([exe_path, cmd[1]], capture_output=True, text=True, timeout=3)
                    first_line = (res.stdout or res.stderr).splitlines()
                    version_str = first_line[0][:80] if first_line else "Available"
                except Exception:
                    version_str = "Installed"

            detected[name] = ToolAvailability(
                name=name,
                is_installed=is_installed,
                version=version_str,
                executable_path=exe_path
            )

        return detected

    @classmethod
    def evaluate_capabilities(
        cls,
        gpus: List[GPUInfo],
        tools: Dict[str, ToolAvailability],
        ram: RAMInfo
    ) -> List[str]:
        caps = []

        # Video Capabilities
        if tools.get("ffmpeg", ToolAvailability(name="ffmpeg", is_installed=False)).is_installed:
            caps.append("video_editing_ffmpeg")
            caps.append("video_concat")
            caps.append("video_transcoding")

        if tools.get("ffprobe", ToolAvailability(name="ffprobe", is_installed=False)).is_installed:
            caps.append("media_probe")

        # GPU & AI Capabilities
        has_nvidia = any(gpu.vendor == "NVIDIA" for gpu in gpus)
        if has_nvidia:
            caps.append("gpu_acceleration")
            caps.append("cuda")
            caps.append("video_encoding_nvenc")
            caps.append("ai_local_inference")

        # Audio / Whisper Capabilities
        if tools.get("whisper", ToolAvailability(name="whisper", is_installed=False)).is_installed:
            caps.append("audio_transcription_whisper")

        # 3D Capabilities
        if tools.get("blender", ToolAvailability(name="blender", is_installed=False)).is_installed:
            caps.append("3d_rendering_blender")

        # Large Memory Tasks
        if ram.total_gb >= 16.0:
            caps.append("high_memory_processing")

        return caps

    @classmethod
    def scan_local_device(
        cls,
        device_id: str = "node-local",
        role: DeviceRole = DeviceRole.WORKER_NODE
    ) -> DeviceProfile:
        os_info = cls.detect_os()
        cpu_info = cls.detect_cpu()
        ram_info = cls.detect_ram()
        disks = cls.detect_disks([os.getcwd()])
        gpus = cls.detect_gpus()
        tools = cls.detect_tools()
        capabilities = cls.evaluate_capabilities(gpus, tools, ram_info)

        # Get local IP
        try:
            ip_address = socket.gethostbyname(os_info.hostname)
        except Exception:
            ip_address = "127.0.0.1"

        return DeviceProfile(
            device_id=device_id,
            hostname=os_info.hostname,
            role=role,
            status=DeviceStatus.ONLINE,
            ip_address=ip_address,
            os=os_info,
            cpu=cpu_info,
            ram=ram_info,
            gpus=gpus,
            disks=disks,
            tools=tools,
            capabilities=capabilities,
            last_heartbeat=time.time()
        )
