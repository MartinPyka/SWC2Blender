import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, FloatProperty
from bpy.types import Operator


def read_some_data(context, filepath, scale_f=1000):
    """a function to read swc files and import them into blender

    Args:
        context (): _description_
        filepath (str): filepath to SWC file
        scale_f (int, optional): scale factor to downsample SWC into blender units. Defaults to 1000.

    Returns:
        set: with "FINISHED" if successful
    """
    print(filepath)
    with open(filepath) as f:
        lines = f.readlines()

    x = 0
    while lines[x][0] == "#":
        x += 1

    data = lines[x].strip().split(" ")
    neuron = {float(data[0]): [float(d) for d in data[1:7]]}
    x += 1

    for l in lines[x:]:
        data = l.strip().split(" ")
        neuron[float(data[0])] = [float(d) for d in data[1:7]]

    bpy.ops.object.empty_add(
        location=(
            neuron[1][1] / scale_f,
            neuron[1][2] / scale_f,
            neuron[1][3] / scale_f,
        )
    )
    a = bpy.context.active_object
    a.name = "neuron_swc"

    last = -10.0

    for key, value in neuron.items():
        if value[-1] == -1 or value[0] == 10:
            continue

        if value[-1] != last:
            tracer = bpy.data.curves.new("tracer", "CURVE")
            tracer.dimensions = "3D"
            spline = tracer.splines.new("BEZIER")

            curve = bpy.data.objects.new("curve", tracer)
            context.collection.objects.link(curve)

            tracer.resolution_u = 8
            tracer.bevel_resolution = 8
            tracer.fill_mode = "FULL"
            tracer.bevel_depth = 0.001

            p = spline.bezier_points[0]
            p.co = [
                neuron[value[-1]][1] / scale_f,
                neuron[value[-1]][2] / scale_f,
                neuron[value[-1]][3] / scale_f,
            ]
            p.radius = neuron[value[-1]][5] / scale_f
            p.handle_right_type = "VECTOR"
            p.handle_left_type = "VECTOR"

            if last > 0:
                spline.bezier_points.add(1)
                p = spline.bezier_points[-1]
                p.co = [value[1] / scale_f, value[2] / scale_f, value[3] / scale_f]
                p.radius = value[5] / scale_f
                p.handle_right_type = "VECTOR"
                p.handle_left_type = "VECTOR"

            curve.parent = a

        if value[-1] == last:
            spline.bezier_points.add(1)
            p = spline.bezier_points[-1]
            p.co = [value[1] / scale_f, value[2] / scale_f, value[3] / scale_f]
            p.radius = value[5] / scale_f
            p.handle_right_type = "VECTOR"
            p.handle_left_type = "VECTOR"

        last = key

    return {"FINISHED"}


class ImportSWCData(Operator, ImportHelper):
    bl_idname = "import_mesh.swc"
    bl_label = "Import SWC-Files"

    filename_ext = ".swc"

    filter_glob: StringProperty(default="*.swc", options={"HIDDEN"})
    scale_factor: FloatProperty(
        name="Scale Factor", default=1000.0, description="Factor to downscale the data"
    )

    def execute(self, context):
        return read_some_data(context, self.filepath, self.scale_factor)


def menu_func_import(self, context):
    self.layout.operator(ImportSWCData.bl_idname, text="SWC Importer")


def register():
    bpy.utils.register_class(ImportSWCData)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_class(ImportSWCData)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)


if __name__ == "__main__":
    register()
