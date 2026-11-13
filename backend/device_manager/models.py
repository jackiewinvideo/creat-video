from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class DeviceRole(str, Enum):
    CONTROL_NODE = "control_node"
    WORKER_NODE = "worker_node"
    STORAGE_NODE = "storage_node"
    HYBRID = "hybrid"


class DeviceStatus(str, Enum):
    ONLINE = "online"
    BUSY = "busy"
    DEGRADED = "degraded"
    OFFLINE = "offline"


class OSInfo(BaseModel):
    system: str
    release: str
    version: str
    architecture: str
    hostname: str


class CPUInfo(BaseModel):
    physical_cores: int
    logical_cores: int
    current_usage_percent: float


class RAMInfo(BaseModel):
    total_gb: float
    available_gb: float
    usage_percent: float


class GPUInfo(BaseModel):
    name: str
    vram_total_mb: float = 0.0
    vram_free_mb: float = 0.0
    driver_version: Optional[str] = None
    cuda_version: Optional[str] = None
    vendor: str = "Unknown"


class DiskInfo(BaseModel):
    mount_point: str
    total_gb: float
    free_gb: float
    usage_percent: float


class ToolAvailability(BaseModel):
    name: str
    is_installed: bool
    version: Optional[str] = None
    executable_path: Optional[str] = None


class DeviceProfile(BaseModel):
    device_id: str
    hostname: str
    role: DeviceRole = DeviceRole.WORKER_NODE
    status: DeviceStatus = DeviceStatus.ONLINE
    ip_address: Optional[str] = None
    os: OSInfo
    cpu: CPUInfo
    ram: RAMInfo
    gpus: List[GPUInfo] = Field(default_factory=list)
    disks: List[DiskInfo] = Field(default_factory=list)
    tools: Dict[str, ToolAvailability] = Field(default_factory=dict)
    capabilities: List[str] = Field(default_factory=list)
    last_heartbeat: float = Field(default=0.0)


class TaskRequirements(BaseModel):
    required_capabilities: List[str] = Field(default_factory=list)
    min_ram_gb: float = 0.0
    min_vram_mb: float = 0.0
    min_free_disk_gb: float = 1.0


class TaskFeasibilityReport(BaseModel):
    can_execute: bool
    device_id: str
    missing_capabilities: List[str] = Field(default_factory=list)
    resource_blockers: List[str] = Field(default_factory=list)
