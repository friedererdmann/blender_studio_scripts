"""BLENDER STUDIO SCRIPTS

This file is meant to be in /startup/ (e.g. of the location defined in BLENDER_USER_SCRIPTS)

It parses the environment variable BLENDER_STUDIO_SCRIPTS, which supports multiple paths

Currently supported
- Users can still locally install addons
- Multiple addon locations
- Multiple module locations
- Multiple startup script locations
"""

import os
import sys
import pkgutil
import importlib
import inspect
from typing import List
from types import ModuleType


BLENDER_STUDIO_SCRIPTS = "BLENDER_STUDIO_SCRIPTS"
SEPARATOR = ";"
STARTUP_MODULES = []


def fix_default_addon_path():
    """This method patches the default install location from the addons preferences
    to install to the user's app data rather than to BLENDER_USER_SCRIPTS (our entry point)
    """
    import bpy
    import _bpy
    old_function = bpy.utils.user_resource

    real_default = os.path.join(_bpy.resource_path("USER"), 'scripts', 'addons')

    def patched_function(resource_type, *, path="", create=False):
        current_frame = inspect.currentframe()
        caller_frame = inspect.getouterframes(current_frame, 2)
        outer_frame = caller_frame[1]
        method_name = outer_frame.function
        file_path = os.path.normpath(outer_frame.filename)
        compare = os.path.normpath(os.path.join('scripts', 'startup', 'bl_operators', 'userpref.py'))
        if method_name == 'execute' and file_path.endswith(compare):
            return real_default
        return old_function(resource_type, path=path, create=create)

    bpy.utils.user_resource = patched_function


def add_module_path(base_path: str):
    module_path = os.path.join(base_path, "modules")
    if os.path.exists(module_path) and os.path.isdir(module_path):
        sys.path.append(module_path)


def add_addon_paths(base_paths: List[str]):
    if not base_paths:
        return

    import addon_utils
    standard_paths = addon_utils.paths

    def patched_paths():
        addon_paths = standard_paths()
        for base_path in base_paths:
            addon_path = os.path.join(base_path, "addons")
            if os.path.exists(addon_path) and os.path.isdir(addon_path):
                addon_paths.append(addon_path)
        import _bpy
        user_directory = os.path.join(_bpy.resource_path("USER"), 'scripts', 'addons')
        if os.path.exists(user_directory) and os.path.isdir(user_directory):
            addon_paths.append(user_directory)
        return addon_paths

    addon_utils.paths = patched_paths


def import_startup_scripts(base_path: str) -> List[ModuleType]:
    startup = os.path.join(base_path, "startup")

    if os.path.exists(startup) and os.path.isdir(startup):
        sys.path.insert(0, startup)

    module_list = list(pkgutil.iter_modules([startup]))
    modules = []

    for module_info in module_list:
        module = importlib.import_module(module_info.name)
        modules.append(module)

    return modules


def register_startup_scripts():
    for module in STARTUP_MODULES:
        if hasattr(module, 'register'):
            module.register()


def get_studio_paths():
    env_variable = os.environ.get(BLENDER_STUDIO_SCRIPTS, "")

    if not env_variable:
        return []

    return [entry.strip() for entry in env_variable.split(SEPARATOR)]


fix_default_addon_path()

base_paths = get_studio_paths()

add_addon_paths(base_paths)

for base_path in base_paths:
    add_module_path(base_path)

for base_path in base_paths:
    STARTUP_MODULES += import_startup_scripts(base_path)


def register():
    register_startup_scripts()
