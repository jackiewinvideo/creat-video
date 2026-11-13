import logging
import time
from typing import Dict, List, Optional
from backend.device_manager.models import (
    DeviceProfile,
    DeviceRole,
    DeviceStatus,
    TaskRequirements,
    TaskFeasibilityReport,
)
from backend.device_manager.detector import DeviceDetector

logger = logging.getLogger(__name__)


class DeviceManager:
    """
    Manages physical and cloud nodes across the distributed AI Film Studio cluster.
    Tracks capacity, matches tasks with suitable nodes, and monitors health.
    """

    def __init__(self, local_device_id: str = "node-primary", local_role: DeviceRole = DeviceRole.HYBRID):
        self._devices: Dict[str, DeviceProfile] = {}
        self.local_device_id = local_device_id
        self.local_role = local_role
        self.initialize_local_device()

    def initialize_local_device(self) -> DeviceProfile:
        """Scan and register local machine."""
        profile = DeviceDetector.scan_local_device(device_id=self.local_device_id, role=self.local_role)
        self.register_device(profile)
        logger.info(
            f"Initialized local device: '{profile.device_id}' ({profile.os.system}) "
            f"with {len(profile.capabilities)} capabilities: {profile.capabilities}"
        )
        return profile

    def register_device(self, profile: DeviceProfile) -> None:
        self._devices[profile.device_id] = profile

    def unregister_device(self, device_id: str) -> None:
        self._devices.pop(device_id, None)

    def get_device(self, device_id: str) -> Optional[DeviceProfile]:
        return self._devices.get(device_id)

    def list_devices(self, role: Optional[DeviceRole] = None) -> List[DeviceProfile]:
        devices = list(self._devices.values())
        if role:
            devices = [d for d in devices if d.role == role or d.role == DeviceRole.HYBRID]
        return devices

    def record_heartbeat(self, device_id: str) -> bool:
        device = self._devices.get(device_id)
        if device:
            device.last_heartbeat = time.time()
            device.status = DeviceStatus.ONLINE
            return True
        return False

    def check_feasibility(self, device_id: str, req: TaskRequirements) -> TaskFeasibilityReport:
        device = self._devices.get(device_id)
        if not device:
            return TaskFeasibilityReport(
                can_execute=False,
                device_id=device_id,
                resource_blockers=[f"Device '{device_id}' is not registered."]
            )

        missing_caps = [
            cap for cap in req.required_capabilities
            if cap not in device.capabilities
        ]

        blockers = []
        if device.status not in (DeviceStatus.ONLINE, DeviceStatus.BUSY):
            blockers.append(f"Device is in {device.status.value} state.")

        if device.ram.available_gb < req.min_ram_gb:
            blockers.append(
                f"Insufficient RAM: available {device.ram.available_gb}GB < required {req.min_ram_gb}GB."
            )

        if req.min_vram_mb > 0:
            total_vram_free = sum(gpu.vram_free_mb for gpu in device.gpus)
            if total_vram_free < req.min_vram_mb:
                blockers.append(
                    f"Insufficient VRAM: available {total_vram_free}MB < required {req.min_vram_mb}MB."
                )

        if req.min_free_disk_gb > 0 and device.disks:
            free_disk = max(d.free_gb for d in device.disks)
            if free_disk < req.min_free_disk_gb:
                blockers.append(
                    f"Insufficient free disk: max free {free_disk}GB < required {req.min_free_disk_gb}GB."
                )

        can_execute = (len(missing_caps) == 0 and len(blockers) == 0)
        return TaskFeasibilityReport(
            can_execute=can_execute,
            device_id=device_id,
            missing_capabilities=missing_caps,
            resource_blockers=blockers
        )

    def find_best_worker_for_task(self, req: TaskRequirements) -> Optional[DeviceProfile]:
        """Find the most capable worker node meeting task requirements."""
        candidates = self.list_devices(role=DeviceRole.WORKER_NODE)

        viable_workers = []
        for worker in candidates:
            report = self.check_feasibility(worker.device_id, req)
            if report.can_execute:
                viable_workers.append(worker)

        if not viable_workers:
            return None

        # Sort by lowest CPU usage and highest available RAM
        return sorted(
            viable_workers,
            key=lambda w: (w.cpu.current_usage_percent, -w.ram.available_gb)
        )[0]
