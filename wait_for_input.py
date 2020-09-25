import bpy
from bpy.props import BoolProperty
from bpy.types import Operator, Panel
from datetime import datetime
from zpy import Is, register_keymaps, keyframe, utils, Get
km = register_keymaps()


# Play animation for these keys
play_keys = {
    'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
    'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y',
    'LEFTMOUSE', 'PEN', 'ACTIONMOUSE',
    'TAB', 'RET',
}

# Bypass/Ignore these keys
nav_keys = {
    'RIGHTMOUSE',
    'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE',
    'MOUSEROTATE', 'WHEELINMOUSE', 'WHEELOUTMOUSE',
    'LEFT_CTRL', 'LEFT_ALT', 'LEFT_SHIFT',
    'RIGHT_ALT', 'RIGHT_CTRL', 'RIGHT_SHIFT',
    'MOUSEMOVE', 'INBETWEEN_MOUSEMOVE', 'TRACKPADPAN', 'TRACKPADZOOM',
    'EVT_TWEAK_L', 'EVT_TWEAK_M', 'EVT_TWEAK_R', 'EVT_TWEAK_A', 'EVT_TWEAK_S',
    'LEFT_ARROW', 'DOWN_ARROW', 'RIGHT_ARROW', 'UP_ARROW',
    'Z',
}

other_keys = {
    'RIGHTMOUSE', 'SPACE', 'ESC',
    'ACCENT_GRAVE',  # default FPS hotkey in 2.8
    'NONE',

    # To Sort:
    'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10',
    'F11', 'F12', 'F13', 'F14', 'F15', 'F16', 'F17', 'F18', 'F19',
    'ZERO', 'ONE', 'TWO', 'THREE', 'FOUR',
    'FIVE', 'SIX', 'SEVEN', 'EIGHT', 'NINE',
    'BUTTON4MOUSE', 'BUTTON5MOUSE', 'BUTTON6MOUSE', 'BUTTON7MOUSE',
    'SELECTMOUSE', 'ERASER', 'OSKEY', 'GRLESS',
    'LINE_FEED', 'BACK_SPACE', 'DEL', 'SEMI_COLON', 'PERIOD',
    'COMMA', 'QUOTE', 'MINUS', 'PLUS', 'SLASH', 'BACK_SLASH',
    'EQUAL', 'LEFT_BRACKET', 'RIGHT_BRACKET',
    'NUMPAD_0', 'NUMPAD_9', 'NUMPAD_PERIOD', 'NUMPAD_SLASH',
    'NUMPAD_ASTERIX', 'NUMPAD_MINUS', 'NUMPAD_ENTER', 'NUMPAD_PLUS',
    'PAUSE', 'INSERT', 'HOME', 'PAGE_UP', 'PAGE_DOWN', 'END',
    'MEDIA_PLAY', 'MEDIA_STOP', 'MEDIA_FIRST', 'MEDIA_LAST', 'TEXTINPUT',
    'WINDOW_DEACTIVATE', 'TIMER', 'TIMER0', 'TIMER1', 'TIMER2',
    'TIMER_JOBS', 'TIMER_AUTOSAVE', 'TIMER_REPORT', 'TIMERREGION',

    'NDOF_MOTION', 'NDOF_BUTTON_MENU', 'NDOF_BUTTON_FIT', 'NDOF_BUTTON_TOP',
    'NDOF_BUTTON_BOTTOM', 'NDOF_BUTTON_LEFT', 'NDOF_BUTTON_RIGHT',
    'NDOF_BUTTON_FRONT', 'NDOF_BUTTON_BACK', 'NDOF_BUTTON_ISO1',
    'NDOF_BUTTON_ISO2', 'NDOF_BUTTON_ROLL_CW', 'NDOF_BUTTON_ROLL_CCW',
    'NDOF_BUTTON_SPIN_CW', 'NDOF_BUTTON_SPIN_CCW', 'NDOF_BUTTON_TILT_CW',
    'NDOF_BUTTON_TILT_CCW', 'NDOF_BUTTON_ROTATE', 'NDOF_BUTTON_PANZOOM',
    'NDOF_BUTTON_DOMINANT', 'NDOF_BUTTON_PLUS', 'NDOF_BUTTON_MINUS',
    'NDOF_BUTTON_ESC', 'NDOF_BUTTON_ALT', 'NDOF_BUTTON_SHIFT',
    'NDOF_BUTTON_CTRL', 'NDOF_BUTTON_1', 'NDOF_BUTTON_10', 'NDOF_BUTTON_A',
    'NDOF_BUTTON_B', 'NDOF_BUTTON_C',
}


class animation:
    in_modal = False
    custom_playing = False
    custom_playback = False  # Just running slowmo playback
    selected = list()

    def __init__(self, scn):
        animation.last_frame = scn.frame_current
        animation.start = datetime.now()
        animation.start_frame = scn.frame_current_final

        def save_pose(src, loc, rot, scale):
            items = dict()
            if loc:
                items['location'] = src.location[:]
            if rot:
                if (src.rotation_mode == 'QUATERNION'):
                    items['rotation_quaternion'] = src.rotation_quaternion[:]
                elif (src.rotation_mode == 'AXIS_ANGLE'):
                    items['rotation_axis_angle'] = src.rotation_axis_angle[:]
                else:
                    items['rotation_euler'] = src.rotation_euler[:]
            if scale:
                items['scale'] = src.scale[:]
            return items

        def save_poses(keyframes_inserted):
            lrc = dict()
            if keyframes_inserted:
                for src in animation.selected:
                    lrc[src] = save_pose(src, *keyframes_inserted)
                    for ik in Get.ik_chain(src):
                        lrc[ik] = save_pose(ik, *keyframes_inserted)
            return lrc

        def load_poses(lrc):
            for (src, items) in lrc.items():
                for (attrib, value) in items.items():
                    setattr(src, attrib, value)

        def playback():
            if (not scn.get('is_animation_playing')) or (not animation.custom_playing):
                # Recording stopped, so exit function and clear subframe
                scn.frame_set(scn.frame_current, subframe=0)
                return

            prefs = scn.wait
            loop = (not prefs.stop_loop)
            stop = prefs.stop_at_end and (not loop)

            offset = (1 / prefs.factor)  # SlowMo value

            # Find the next frame
            if (scn.sync_mode == 'NONE'):
                final = scn.frame_current + scn.frame_subframe + offset
            else:
                elapsed = (datetime.now() - animation.start).total_seconds()
                fps = (scn.render.fps / prefs.factor)
                final = animation.start_frame + (elapsed * fps)

            # Split subframe
            frame = int(final)
            subframe = final - int(final)
            if (frame < 0 and subframe) or (subframe < 0):
                # Negative numbers have to offset a little for frame_set
                frame -= 1
                subframe = 1 - abs(subframe)

            (frame_start, frame_end) = Get.frame_range(bpy.context)

            # Insert final pose keyframes before changing the frame
            insert_keys = animation.keyframe_insert(scn.frame_current)

            # Delete old keyframes between frame skips
            if (not animation.custom_playback) and (scn.sync_mode != 'NONE'):
                # for dframe in range(animation.last_frame + 1, scn.frame_current):
                for dframe in range(scn.frame_current + 1, frame):
                    animation.keyframe_delete(dframe)

            # Save active pose before changing frame
            lrc = save_poses(insert_keys)

            # Change frame to first/next/last
            if (stop or loop) and (frame_end < final):
                # Next frame is going to extend past timeline

                if loop:
                    scn.frame_set(frame_start, subframe=0)
                    animation.start = datetime.now()
                    animation.start_frame = scn.frame_current_final
                elif stop:
                    scn.frame_set(frame_end, subframe=0)
                    animation.keyframe_insert(scn.frame_current)
                    # load_poses(lrc)
                    return animation.stop(scn)
            else:
                scn.frame_set(frame, subframe=subframe)

            # Restore the active pose
            load_poses(lrc)

            animation.last_frame = scn.frame_current

            if (scn.sync_mode == 'NONE'):
                # 1 = one second
                # fps = frames to view in a second
                # basically, split the number of frames, so to repeat that many times in one second
                return offset / scn.render.fps  # wait to try to playback at normal rate
            else:
                return 0  # Don't wait because I don't know how to get normal rate

        animation.custom_playing = True
        scn['is_animation_playing'] = True
        utils.register_timer(0, playback)
        # animation.keyframe_insert(scn.frame_current)

    def keyframe_insert(frame):
        if animation.custom_playback:
            return

        context = bpy.context
        scn = context.scene
        prefs = scn.wait
        loc = prefs.use_location
        rot = prefs.use_rotation
        scale = prefs.use_scale

        if not (loc or rot or scale):
            ks = scn.keying_sets_all.active
            if (ks is None) or (not keyframe.use_keyingset(context)):
                loc = rot = scale = True
            elif ks.bl_idname == 'Variable':
                loc = keyframe.poll_keyingset(context, 'key_location')
                rot = keyframe.poll_keyingset(context, 'key_rotation')
                scale = keyframe.poll_keyingset(context, 'key_scale')
            else:
                ks = ks.bl_idname.replace('Visual ', '')
                loc = ks in ('Location', 'LocRot', 'LocScale', 'LocRotScale')
                rot = ks in ('Rotation', 'LocRot', 'LocRotScale', 'RotScale')
                scale = ks in ('Scaling', 'LocScale', 'LocRotScale', 'RotScale')
                # 'WholeCharacter', 'WholeCharacterSelected'

            if not (loc or rot or scale):
                return

        def key(src, **kargs):
            if keyframe.poll_insert(context, src=src):
                if loc:
                    keyframe.location(context, src, **kargs)
                if rot:
                    keyframe.rotation(context, src, **kargs)
                if scale:
                    keyframe.scale(context, src, **kargs)

        for src in animation.selected:
            key(src, frame=frame)
            for ik in Get.ik_chain(src):
                if (ik not in animation.selected):
                    key(ik, frame=frame, options={'INSERTKEY_VISUAL'})

        return (loc, rot, scale)

    def keyframe_delete(frame):
        context = bpy.context
        scn = context.scene
        prefs = scn.wait
        loc = prefs.use_location
        rot = prefs.use_rotation
        scale = prefs.use_scale

        if not (loc or rot or scale):
            ks = scn.keying_sets_all.active
            if (ks is None) or (not keyframe.use_keyingset(context)):
                loc = rot = scale = True
            elif ks.bl_idname == 'Variable':
                loc = keyframe.poll_keyingset(context, 'key_location')
                rot = keyframe.poll_keyingset(context, 'key_rotation')
                scale = keyframe.poll_keyingset(context, 'key_scale')
            else:
                ks = ks.bl_idname.replace('Visual ', '')
                loc = ks in ('Location', 'LocRot', 'LocScale', 'LocRotScale')
                rot = ks in ('Rotation', 'LocRot', 'LocRotScale', 'RotScale')
                scale = ks in ('Scaling', 'LocScale', 'LocRotScale', 'RotScale')
                # 'WholeCharacter', 'WholeCharacterSelected'

            if not (loc or rot or scale):
                return

        def key(src, **kargs):
            if keyframe.poll_insert(context, src=src):
                if loc:
                    src.keyframe_delete('location', **kargs)
                if rot:
                    if (src.rotation_mode == 'QUATERNION'):
                        prop = 'rotation_quaternion'
                    elif (src.rotation_mode == 'AXIS_ANGLE'):
                        prop = 'rotation_axis_angle'
                    else:
                        prop = 'rotation_euler'
                    src.keyframe_delete(prop, **kargs)
                if scale:
                    src.keyframe_delete('scale', **kargs)

        for src in animation.selected:
            key(src, frame=frame)
            for ik in Get.ik_chain(src):
                if (ik not in animation.selected):
                    key(ik, frame=frame, options={'INSERTKEY_VISUAL'})

        return (loc, rot, scale)

    def stop(scn):
        if scn.get('is_animation_playing'):
            del scn['is_animation_playing']
        animation.custom_playing = False
        animation.custom_playback = False
        animation.selected = list()

        # Try to update keyed poses
        scn.frame_set(scn.frame_current, subframe=0)


class PLAYBACK_OT_wait_for_input(Operator):
    bl_description = "Begin animation playback after pressing an action key"\
        ".\nClick + Alt/Shift/Ctrl to restore frame when done"
    bl_idname = 'zpy.wait_for_input'
    bl_label = "Wait For Input"
    # bl_options = {'REGISTER', 'UNDO'}

    keypress = None

    @classmethod
    def poll(self, context):
        return (not Is.animation_playing(context)) and (not animation.in_modal) \
            and (not animation.custom_playing)

    def invoke(self, context, event):
        if event.type in {'LEFTMOUSE', 'RET'}:
            self.restore_frame = any((event.alt, event.shift, event.ctrl))
        else:
            self.report({'INFO'}, "Waiting for Input")
        self.keypress = event.type
        self.startup = True
        self.wait_delays = 0

        context.window_manager.modal_handler_add(self)
        animation.in_modal = True
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        prefs = context.scene.wait
        if self.startup:
            # if event.type not in {'MOUSEMOVE'}:
                # debug(event.type, event.value)
            if event.type == self.keypress:
                self.startup = False
        elif (event.type == 'SPACE') and prefs.use_timer:
            if animation.in_modal:
                # Waiting for input
                if event.shift:
                    if self.wait_delays:
                        return self.exit_pass(context)
                    else:
                        # Delay cancel one time; clicked keys too fast
                        self.wait_delays += 1
                elif event.value != 'PRESS':
                    animation.custom_playback = True
                    animation.selected = list()
                    return self.exit_play(context)  # .union({'FINISHED'})
                else:
                    return {'RUNNING_MODAL'}
            else:
                # Running playback
                if event.value != 'PRESS':
                    return self.exit_stop(context)
                else:
                    return {'RUNNING_MODAL'}
        elif animation.custom_playback:
            # Doing slowmo playback
            if event.type == 'ESC':
                return self.exit_stop(context)
        elif animation.in_modal:
            # Waiting for input

            if event.type in {'SPACE', 'ESC'}:
                return self.exit_pass(context)
            elif event.type == 'RIGHTMOUSE':
                # Make room for dragging things, or cancel with single click
                if event.value == 'CLICK_DRAG':
                    animation.selected = Get.selected(context)
                    return self.exit_play(context)
                elif event.value in {'CLICK', 'RELEASE'}:
                    return self.exit_pass(context)
            elif event.value in {'PRESS', 'CLICK', 'DOUBLE_CLICK'}:
                                # 'ANY', 'NOTHING', 'RELEASE'
                if event.type in play_keys:
                    animation.selected = Get.selected(context)
                    return self.exit_play(context)
                elif event.type == 'ACCENT_GRAVE':
                    animation.selected = Get.selected(context)
                    return self.exit_play(context).union(self.exit_pass(context))
                elif event.type not in nav_keys:
                    return self.exit_pass(context)
        else:
            # Waiting to finish recording

            if event.type == 'SPACE' and self.restore_frame:
                return {'FINISHED'}
            elif event.type in {'SPACE', 'ESC', 'RIGHTMOUSE'} \
                    or event.value in {'PRESS', 'CLICK', 'DOUBLE_CLICK'}:
                return self.exit_stop(context)

        return {'PASS_THROUGH'}
        return {'RUNNING_MODAL'}

    def exit_pass(self, context):
        "Exit operator and do nothing"
        animation.in_modal = False

        animation.stop(context.scene)

        self.report({'INFO'}, "Cancel Wait for Input")
        return {'PASS_THROUGH', 'CANCELLED'}

    def exit_play(self, context):
        "Begin recording animation"
        scn = context.scene
        prefs = scn.wait

        animation.in_modal = False

        if prefs.use_timer:
            animation(scn)
        else:
            bpy.ops.screen.animation_play('INVOKE_DEFAULT')
            scn.render.fps_base *= prefs.factor

        return {'PASS_THROUGH'}

    def exit_stop(self, context):
        "Was recording, now exit operation"
        scn = context.scene
        prefs = scn.wait

        if prefs.use_timer:
            animation.stop(scn)
        else:
            # if Is.animation_playing():
            #     bpy.ops.screen.animation_play('INVOKE_DEFAULT')
            bpy.ops.screen.animation_cancel(restore_frame=self.restore_frame)
                # If restore frame, the animation will jump back
                # to the initial frame. This only "MAY" jump back
            scn.render.fps_base /= prefs.factor

        return {'PASS_THROUGH', 'FINISHED'}

    # from_ui: BoolProperty(default=True, options=set({'HIDDEN', 'SKIP_SAVE'}))
    restore_frame: BoolProperty(
        name="Restore Frame",
        description="Return to the initial frame after stopping playback",
        default=False,
        options={'SKIP_SAVE'},
    )


class WAIT_PT_ui(Panel):
    bl_category = "Tool"
    bl_label = "Wait For Input"
    # bl_options = {'DEFAULT_CLOSED'}
    bl_region_type = 'UI'
    bl_space_type = 'VIEW_3D'

    @classmethod
    def poll(cls, context):
        # "Only display a panel if it's in the workspace"
        # return context.area.type == 'PROPERTIES'
        return context.mode in ('OBJECT', 'POSE')

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        prefs = context.scene.wait

        if animation.in_modal or animation.custom_playing:
            layout.active = False

        col = layout.column(align=True)
        row = col.row(align=True)

        row.prop(prefs, 'use_timer', toggle=True)
        if prefs.use_timer:
            end = row.row(align=True)
            end.active = (not prefs.stop_loop)
            end.prop(prefs, 'stop_at_end', text="", icon='FF', toggle=True)
        icon = ('FILE_REFRESH', 'PAUSE')[prefs.stop_loop]
        row.prop(prefs, 'stop_loop', text="", icon=icon)

        col2 = col.column(align=True)
        # col2.active = prefs.use_timer

        rfps = context.scene.render.fps
        fps = f"{round(rfps / (1 * prefs.factor), 1)} fps"
        col2.prop(prefs, 'factor', text=fps, icon='TIME', slider=False)

        row = col2.row(align=True)
        row.active = prefs.use_timer
        row.prop(prefs, 'use_location', text="Loc", toggle=True)
        row.prop(prefs, 'use_rotation', text="Rot", toggle=True)
        row.prop(prefs, 'use_scale', text="Scale", toggle=True)

        row = col2.row(align=True)
        row.prop_enum(context.scene, 'sync_mode', 'NONE')
        row.prop_enum(context.scene, 'sync_mode', 'FRAME_DROP')
        row.prop_enum(context.scene, 'sync_mode', 'AUDIO_SYNC')


def register():
    kargs = dict(name='Window', type='SPACE', shift=True)
    km.toggle('wm.toolbar', value='PRESS', **kargs)
    km.add('wm.toolbar', value='CLICK', **kargs)
    km.add(PLAYBACK_OT_wait_for_input, name='Frames', type='SPACE',
           value='CLICK_DRAG', shift=True)  # , from_ui=False)


def unregister():
    km.remove()
