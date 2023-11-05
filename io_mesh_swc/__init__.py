bl_info = {
    "name": "SWC format",
    "author": "Martin Pyka",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),  # Adjusted for Blender 3.0
    "location": "File > Import > SWC",
    "description": "Import SWC files",
    "license": "GPL v2",
    "category": "Import"
}

__author__ = bl_info['author']
__license__ = bl_info['license']
__version__ = ".".join([str(s) for s in bl_info['version']])

from . import operator_swc_import


def register():
    operator_swc_import.register()
    

def unregister():
    operator_swc_import.unregister()


if __name__ == "__main__":
    register()
