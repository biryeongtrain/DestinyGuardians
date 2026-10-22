#!/usr/bin/env python3
"""Disposable 26.3 observer with read-only camera/vehicle diagnostics.

Uses H16's source/options isolation. Adds no camera enforcement, movement input,
packet changes, or client rendering fixes; those would invalidate vanilla-camera evidence.
"""
import argparse
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    parser.add_argument("--source", type=Path)
    args = parser.parse_args()
    subprocess.run([sys.executable, str(Path(__file__).with_name("prepare_vision_h16.py")), *sys.argv[1:]], check=True)
    target = args.destination / "src/main/java/com/coppergolem/visionclient/ClientAuxControl.java"
    source = target.read_text()
    needle = r'        out.append(",\"fps\":").append(mc.getFps());'
    assert source.count(needle) == 1
    extra = r'''        if (player != null) {
            out.append(",\"playerX\":").append(player.getX());
            out.append(",\"playerY\":").append(player.getY());
            out.append(",\"playerZ\":").append(player.getZ());
            out.append(",\"vehicleId\":").append(player.getVehicle() == null ? -1 : player.getVehicle().getId());
        }
        net.minecraft.world.entity.Entity camera = mc.getCameraEntity();
        if (camera != null) {
            out.append(",\"cameraEntityId\":").append(camera.getId());
            out.append(",\"cameraIsPlayer\":").append(camera == player);
            out.append(",\"cameraX\":").append(camera.getX());
            out.append(",\"cameraY\":").append(camera.getY());
            out.append(",\"cameraZ\":").append(camera.getZ());
        }
'''
    target.write_text(source.replace(needle, extra + needle))
    print("H18 read-only camera diagnostics added")


if __name__ == "__main__":
    main()
