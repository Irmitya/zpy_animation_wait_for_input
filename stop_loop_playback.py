import bpy
from bpy.app.handlers import persistent, frame_change_post
from bpy.props import BoolProperty
from zpy import Is

last_frame = -1e309  # -inf


@persistent
def wait_for_end(scn):
    global last_frame
    context = bpy.context

    fc = scn.frame_current
    enabled = scn.wait.stop_loop
    playing = Is.animation_playing(context)

    if not (enabled and playing):
        last_frame = fc
        return

    if (scn.use_preview_range):
        fs = scn.frame_preview_start
        fe = scn.frame_preview_end
    else:
        fs = scn.frame_start
        fe = scn.frame_end

    if (fc >= fe) or (fc < last_frame):
        try:
            bpy.ops.screen.animation_cancel(restore_frame=False)
            if (fc < last_frame):
                scn.frame_current = fe
        except:
            pass

    last_frame = fc


def register():
    frame_change_post.append(wait_for_end)


def unregister():
    if (wait_for_end in frame_change_post):
        frame_change_post.remove(wait_for_end)
