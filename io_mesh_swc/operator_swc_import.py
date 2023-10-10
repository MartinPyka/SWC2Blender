import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, FloatProperty
from bpy.types import Operator
import os


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
            mat.diffuse_color = (0.8, 0.8, 0.2, 1)  # Yellow for apical dendrite
        else:
            mat.diffuse_color = (0.8, 0.8, 0.8, 1)  # Grey for others
    else:
        mat = bpy.data.materials[mat_name]

    return mat


def read_some_data(
    context, filepath, scale_f=1000, name="neuron_swc", min_radius=0.0, radius_scale=1.0
):
    """a function to read swc files and import them into blender

    Args:
        context (): _description_
        filepath (str): filepath to SWC file
        scale_f (int, optional): scale factor to downsample SWC into blender units. Defaults to 1000.
        name (str, optional): name of the neuron object. Defaults to "neuron_swc".
        min_radius (float, optional): minimum radius of the neuron. Defaults to 0.0.
        radius_scale (float, optional): scale the radius of the non soma components by this amount in order to make thinner objects more visible at distance. Defaults to 1.0.
    Returns:
        set: with "FINISHED" if successful
    """
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
    a.name = name

    last = -10.0

    for key, value in neuron.items():
        print(key, value)
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
            tracer.bevel_depth = radius_scale / scale_f

            if value[-1] != -1:
                p = spline.bezier_points[0]
                p.co = [
                    neuron[value[-1]][1] / scale_f,
                    neuron[value[-1]][2] / scale_f,
                    neuron[value[-1]][3] / scale_f,
                ]
                if neuron[value[-1]][0] == 1:
                    radius = neuron[value[-1]][4] / radius_scale
                else:
                    radius = neuron[value[-1]][4]
                p.radius = max(radius, min_radius)
                p.handle_right_type = "VECTOR"
                p.handle_left_type = "VECTOR"
            else:
                p = spline.bezier_points[0]
                p.co = [
                    value[1] / scale_f,
                    value[2] / scale_f,
                    value[3] / scale_f,
                ]
                radius = value[4]
                p.radius = max(radius, min_radius)
                p.handle_right_type = "VECTOR"
                p.handle_left_type = "VECTOR"
            if last > 0:
                spline.bezier_points.add(1)
                p = spline.bezier_points[-1]
                p.co = [value[1] / scale_f, value[2] / scale_f, value[3] / scale_f]
                if value[0] == 1:
                    radius = value[4] * radius_scale
                else:
                    radius = value[4]
                p.radius = max(radius, min_radius)
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
            p.radius = max(value[4], min_radius)
            p.handle_right_type = "VECTOR"
            p.handle_left_type = "VECTOR"

        last = key

    return {"FINISHED"}


def import_all_swcs_from_directory(
    context, directory, scale_f=1000.0, min_radius=0.0, radius_scale=1.0
):
    # Check if the directory exists
    if not os.path.exists(directory):
        print(f"Directory '{directory}' does not exist!")
        return

    # Iterate over all files in the directory
    for filename in os.listdir(directory):
        # Check if the file has an .swc extension
        if filename.endswith(".swc"):
            filepath = os.path.join(directory, filename)
            neuron_name = os.path.splitext(filename)[
                0
            ]  # Extract name without extension
            read_some_data(
                context, filepath, scale_f, neuron_name, min_radius, radius_scale
            )


class ImportSWCdirectory(Operator, ImportHelper):
    bl_idname = "import_mesh.swc_dir"
    bl_label = "Import SWC-Files from directory"

    directory: StringProperty(
        name="Directory",
        description="Directory to import from",
        subtype="DIR_PATH",
    )
    scale_factor: FloatProperty(
        name="Scale Factor", default=1000.0, description="Factor to downscale the data"
    )
    min_radius: FloatProperty(
        name="Minimum Radius",
        default=0.0,
        description="Will ensure no portion of the object has a radius less than this (before scaling). Make >0 to help make thin axon more visible.",
    )
    radius_scale: FloatProperty(
        name="Radius Scale",
        default=1.0,
        description="Scale the radius of the non soma components by this amount in order to make thinner objects more visible at distance.",
    )

    def execute(self, context):
        import_all_swcs_from_directory(
            context,
            self.directory,
            self.scale_factor,
            self.min_radius,
            self.radius_scale,
        )
        return {"FINISHED"}


class ImportSWCData(Operator, ImportHelper):
    bl_idname = "import_mesh.swc"
    bl_label = "Import SWC-Files"

    filename_ext = ".swc"

    filter_glob: StringProperty(default="*.swc", options={"HIDDEN"})
    scale_factor: FloatProperty(
        name="Scale Factor", default=1000.0, description="Factor to downscale the data"
    )
    min_radius: FloatProperty(
        name="Minimum Radius",
        default=0.0,
        description="Will ensure no portion of the object has a radius less than this (before scaling). Make >0 to help make thin axon more visible.",
    )
    radius_scale: FloatProperty(
        name="Radius Scale",
        default=1.0,
        description="Scale the radius of the non soma components by this amount in order to make thinner objects more visible at distance.",
    )

    def execute(self, context):
        return read_some_data(
            context,
            self.filepath,
            self.scale_factor,
            name="neuron_swc",
            min_radius=self.min_radius,
            radius_scale=self.radius_scale,
        )


def menu_func_import(self, context):
    self.layout.operator(ImportSWCData.bl_idname, text="SWC Importer")
    self.layout.operator(ImportSWCdirectory.bl_idname, text="SWC Directory Importer")


def register():
    bpy.utils.register_class(ImportSWCData)
    bpy.utils.register_class(ImportSWCdirectory)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_class(ImportSWCData)
    bpy.utils.unregister_class(ImportSWCdirectory)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)


if __name__ == "__main__":
    register()
