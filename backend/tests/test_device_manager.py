import platform
import pytest
from backend.device_manager.models import (
    DeviceRole,
    DeviceStatus,
    TaskRequirements,
)
from backend.device_manager.detector import DeviceDetector
from backend.device_manager.manager import DeviceManager


def test_device_detector_live_scan():
    profile = DeviceDetector.scan_local_device(device_id="test-node-01")

    # OS Info checks
    assert profile.os.system in ("Windows", "Linux", "Darwin")
    assert profile.os.architecture != ""

    # Hardware checks
    assert profile.cpu.logical_cores >= 1
    assert profile.ram.total_gb > 0

    # Disk checks
    assert len(profile.disks) >= 1
    assert profile.disks[0].total_gb > 0

    # Tool checks
    assert "ffmpeg" in profile.tools
    assert "ffprobe" in profile.tools

    # Capabilities check: on this machine, FFmpeg and NVIDIA GPU are present
    assert "video_editing_ffmpeg" in profile.capabilities
    assert "media_probe" in profile.capabilities


def test_device_manager_initialization_and_registration():
    mgr = DeviceManager(local_device_id="node-master", local_role=DeviceRole.HYBRID)
    local_dev = mgr.get_device("node-master")

    assert local_dev is not None
    assert local_dev.device_id == "node-master"
    assert local_dev.status == DeviceStatus.ONLINE
    assert mgr.record_heartbeat("node-master") is True


def test_task_feasibility_check():
    mgr = DeviceManager(local_device_id="node-master", local_role=DeviceRole.HYBRID)

    # 1. Video editing requirement (should pass because ffmpeg is installed)
    req_video = TaskRequirements(
        required_capabilities=["video_editing_ffmpeg"],
        min_ram_gb=1.0,
        min_free_disk_gb=0.1
    )
    report_video = mgr.check_feasibility("node-master", req_video)
    assert report_video.can_execute is True
    assert len(report_video.missing_capabilities) == 0

    # 2. Impossible requirement (should fail gracefully)
    req_impossible = TaskRequirements(
        required_capabilities=["quantum_teleportation_capability"],
        min_ram_gb=999999.0
    )
    report_impossible = mgr.check_feasibility("node-master", req_impossible)
    assert report_impossible.can_execute is False
    assert "quantum_teleportation_capability" in report_impossible.missing_capabilities
    assert any("Insufficient RAM" in blocker for blocker in report_impossible.resource_blockers)


def test_find_best_worker():
    mgr = DeviceManager(local_device_id="node-master", local_role=DeviceRole.WORKER_NODE)

    req = TaskRequirements(
        required_capabilities=["video_editing_ffmpeg"],
        min_ram_gb=0.5
    )
    best_worker = mgr.find_best_worker_for_task(req)
    assert best_worker is not None
    assert best_worker.device_id == "node-master"
