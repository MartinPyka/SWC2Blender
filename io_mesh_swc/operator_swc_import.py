import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, FloatProperty
from bpy.types import Operator


def get_material_for_compartment(compartment_type):
    material_names = {
        1: "soma_material",
        2: "axon_material",
        3: "dendrite_material",
        4: "apical_dendrite_material",
        # Add more if needed...
    }

    mat_name = material_names.get(compartment_type, "default_material")

    # If material doesn't exist, create it
    if mat_name not in bpy.data.materials:
        mat = bpy.data.materials.new(name=mat_name)

        if mat_name == "soma_material":
            mat.diffuse_color = (0.8, 0.2, 0.2, 1)  # Red for soma
        elif mat_name == "axon_material":
            mat.diffuse_color = (0.2, 0.8, 0.2, 1)  # Green for axon
        elif mat_name == "dendrite_material":
            mat.diffuse_color = (0.2, 0.2, 0.8, 1)  # Blue for dendrite
        elif mat_name == "apical_dendrite_material":
            mat.diffuse_color = (0.8, 0.8, 0.2, 1) # Yellow for apical dendrite
        else:
            mat.diffuse_color = (0.8, 0.8, 0.8, 1)  # Grey for others
    else:
        mat = bpy.data.materials[mat_name]

    return mat


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
    # x += 1

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

        if value[0] == 1:  # This is typically the root node
            # print(f"Adding sphere at root node location: {value[1:4]}")
            # Adding sphere at the root node location with the specified radius
            sphere_location = (
                value[1] / scale_f,
                value[2] / scale_f,
                value[3] / scale_f,
            )
            soma_radius = value[4] / scale_f  # Assuming value[4] represents the radius
            bpy.ops.mesh.primitive_uv_sphere_add(
                radius=soma_radius, location=sphere_location
            )
            sphere = bpy.context.active_object
            mat = get_material_for_compartment(value[0])
            if len(sphere.data.materials) == 0:
                sphere.data.materials.append(mat)
            else:
                sphere.data.materials[0] = mat
            sphere.parent = a
            continue

        if value[0] == 10:
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
            tracer.bevel_depth = 1.0 / scale_f

            p = spline.bezier_points[0]
            p.co = [
                neuron[value[-1]][1] / scale_f,
                neuron[value[-1]][2] / scale_f,
                neuron[value[-1]][3] / scale_f,
            ]
            p.radius = neuron[value[-1]][4]
            p.handle_right_type = "VECTOR"
            p.handle_left_type = "VECTOR"

            if last > 0:
                spline.bezier_points.add(1)
                p = spline.bezier_points[-1]
                p.co = [value[1] / scale_f, value[2] / scale_f, value[3] / scale_f]
                p.radius = value[4]
                p.handle_right_type = "VECTOR"
                p.handle_left_type = "VECTOR"

            curve.parent = a
            # Assign the material based on compartment type
            compartment_type = value[0]  # The second column in SWC
            mat = get_material_for_compartment(compartment_type)
            if len(curve.data.materials) == 0:
                curve.data.materials.append(mat)
            else:
                curve.data.materials[0] = mat

        if value[-1] == last:
            spline.bezier_points.add(1)
            p = spline.bezier_points[-1]
            p.co = [value[1] / scale_f, value[2] / scale_f, value[3] / scale_f]
            p.radius = value[4]
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
