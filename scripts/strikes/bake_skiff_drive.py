"""Bake the supplied shader-connected skiff using the existing strike shader/coverage pipeline.

Run inside isolated Blender with --disable-autoexec and --python-exit-code 1.
Arguments after -- are source .blend and an owned output directory.
"""
import importlib.util
import sys
from pathlib import Path
import bpy

source, output = map(Path,sys.argv[sys.argv.index('--')+1:])
repo=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(source))
spec=importlib.util.spec_from_file_location('devils_shader_pipeline',repo/'scripts/strikes/build_devils_models.py')
pipeline=importlib.util.module_from_spec(spec);spec.loader.exec_module(pipeline)
pipeline.CACHE=output.resolve()
pipeline.drive_shader_dump('skiff', inspection_lighting=True)
