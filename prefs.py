import bpy
from bpy.props import BoolProperty, FloatProperty
from zpy import utils


class Wait_For_Input_SlowMo(bpy.types.AddonPreferences, utils.Preferences):
    bl_idname = __package__  # __name__

    def draw(self, context):
        layout = self.layout
        self.draw_keymaps(context)


class wait(bpy.types.PropertyGroup):
    stop_loop: BoolProperty(
        name="Stop Playback Loop",
        description="Stop animation playback at the end of the timeline",
        default=False,
    )
    stop_at_end: BoolProperty(
        name="Stop At End",
        description="Don't continue playing past the end of the timeline",
        default=True,
    )

    use_timer: BoolProperty(
        name="Use Timer",
        description="Use custom animation playback, to enable slowmo",
        default=False,
    )
    factor: FloatProperty(
        name="Factor",
        description=(
            "Amout to divide framerate (i.e. 1/1 of 24 fps = 24 fps, 1 / 5 of 24 fps = 4.8 fps)"
        ),
        default=1,
        min=1 / 120,
        max=1200,
        soft_min=1,
        soft_max=120,
        options={'HIDDEN'},
        step=3,
        precision=2,
        subtype='NONE',
        unit='NONE',
    )

    use_location: BoolProperty(
        name="Location",
        description="",
        default=False,
    )
    use_rotation: BoolProperty(
        name="Rotation",
        description="",
        default=False,
    )
    use_scale: BoolProperty(
        name="Scale",
        description="",
        default=False,
    )


def register():
    bpy.types.Scene.wait = utils.register_pointer(wait)


def unregister():
    del bpy.types.Scene.wait
