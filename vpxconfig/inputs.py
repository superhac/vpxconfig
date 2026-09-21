"""Settings of the Input page: the known-devices line, the sensor counts and the button mappings.

Actions, labels and built-in default keys come from VPX's InputManager.cpp (`addKeyAction(id, label, default
scancode)`). A mapping is stored as `Key;<SDL scancode>` ('Key;225' is Left Shift); ' | ' separates alternatives and
' & ' key combinations, and other input devices add their own terms (e.g. 'SDLJoy_<id>;514;o;-0.3' for a game
controller). Those terms are machine specific and can't be detected here, so they are shown as they are and only the
`Key;` term is changed by the page. The `Devices` line lists all known devices, again shown as it appears in the ini.

`initial` is the answer the page starts with (the values the user asked for).
"""
import re

from .settings import Setting as S, resolve

# (setting id, label, VPX's built-in default mapping, initial answer, group)
# Labels must not contain ':' (the base file comment format is "; Label: description [Default: ...]").
_ACTIONS = [
    ("LeftFlipper", "Left Flipper", "Key;225", "Key;225", "Flippers and magna"),
    ("RightFlipper", "Right Flipper", "Key;229", "Key;229", "Flippers and magna"),
    ("LeftStagedFlipper", "Left Staged Flipper", "Key;225", "Key;225", "Flippers and magna"),
    ("RightStagedFlipper", "Right Staged Flipper", "Key;229", "Key;229", "Flippers and magna"),
    ("LeftMagna", "Left Magna", "Key;224", "Key;224", "Flippers and magna"),
    ("RightMagna", "Right Magna", "Key;228", "Key;228", "Flippers and magna"),

    ("UIUp", "UI Next Item", "Key;224", "Key;224", "Menu navigation"),
    ("UIDown", "UI Previous Item", "Key;228", "Key;228", "Menu navigation"),
    ("UILeft", "UI Decrease/Cancel", "Key;225", "Key;225", "Menu navigation"),
    ("UIRight", "UI Increase/Confirm", "Key;229", "Key;229", "Menu navigation"),

    ("LaunchBall", "Launch Ball", "Key;40", "Key;40", "Play"),
    ("LeftNudge", "Left Nudge", "Key;29", "Key;29", "Play"),
    ("RightNudge", "Right Nudge", "Key;56", "Key;56", "Play"),
    ("CenterNudge", "Center Nudge", "Key;44", "Key;44", "Play"),
    ("Tilt", "Tilt", "Key;23", "Key;23", "Play"),
    ("Credit1", "Credit (1)", "Key;34", "Key;34", "Play"),
    ("Credit2", "Credit (2)", "Key;33", "Key;33", "Play"),
    ("Credit3", "Credit (3)", "Key;32", "Key;32", "Play"),
    ("Credit4", "Credit (4)", "Key;35", "Key;35", "Play"),
    ("Start", "Start", "Key;30", "Key;30", "Play"),
    ("ExtraBall", "Extra Ball", "Key;5", "Key;5", "Play"),
    ("Lockbar", "Lockbar", "Key;226", "Key;226", "Play"),

    ("Pause", "Pause Game", "Key;19", "Key;19", "System"),
    ("PerfOverlay", "Toggle Perf. Overlay", "Key;68", "Key;68", "System"),
    ("ExitGame", "Exit Game", "Key;41", "Key;41", "System"),
    ("InGameUI", "Toggle InGame UI", "Key;69", "Key;69", "System"),
    ("VolumeDown", "Volume Down", "Key;45", "Key;45", "System"),
    ("VolumeUp", "Volume Up", "Key;46", "Key;46", "System"),
    ("ShowRules", "Show Rules", "", "Key;21", "System"),            # no built-in key; 21 is R
    ("SlamTilt", "Slam Tilt", "Key;74", "Key;74", "System"),
    ("CoinDoor", "Coin Door", "Key;77", "Key;77", "System"),
    ("Reset", "Reset", "Key;60", "Key;60", "System"),
    ("ToggleStereo", "Select Stereo Mode", "Key;67", "Key;67", "System"),

    ("Service1", "Service Button #1", "Key;36", "Key;36", "Service buttons"),
    ("Service2", "Service Button #2", "Key;37", "Key;37", "Service buttons"),
    ("Service3", "Service Button #3", "Key;38", "Key;38", "Service buttons"),
    ("Service4", "Service Button #4", "Key;39", "Key;39", "Service buttons"),
    ("Service5", "Service Button #5", "Key;35", "Key;35", "Service buttons"),
    ("Service6", "Service Button #6", "Key;75", "Key;75", "Service buttons"),
    ("Service7", "Service Button #7", "Key;45", "Key;45", "Service buttons"),
    ("Service8", "Service Button #8", "", "", "Service buttons"),

    ("VRCenter", "Align VR view", "Key;93", "Key;93", "VR"),
    ("VRUp", "Move VR view up", "Key;96", "Key;96", "VR"),
    ("VRDown", "Move VR view down", "Key;90", "Key;90", "VR"),
    ("VRFront", "Move VR view to the front", "", "", "VR"),
    ("VRBack", "Move VR view to the back", "", "", "VR"),

    ("GenTournament", "Create Tournament File", "Key;226 & Key;30", "Key;226 & Key;30", "Debug and tools"),
    ("DebugBalls", "Debug Balls", "Key;18", "Key;18", "Debug and tools"),
    ("Debugger", "Open Debugger", "Key;7", "Key;7", "Debug and tools"),

    ("Custom1", "Custom Button #1", "", "", "Custom buttons"),
    ("Custom2", "Custom Button #2", "", "", "Custom buttons"),
    ("Custom3", "Custom Button #3", "", "", "Custom buttons"),
    ("Custom4", "Custom Button #4", "", "", "Custom buttons"),
]

MAPPING_HELP = "Key or button that triggers this action, as Key;<SDL scancode>."


def input_groups():
    groups = [
        {"title": "Devices", "fields": [S("Input", "Devices", initial="Key"), S("Input", "NudgeSensorCount"),
                                        S("Input", "PlungerSensorCount")]},
    ]
    by_group = {}
    for action_id, label, default, initial, group in _ACTIONS:
        by_group.setdefault(group, []).append(
            S("Input", f"Mapping.{action_id}", type="mapping", default=default, initial=initial or None, label=label,
              description=MAPPING_HELP))
    groups += [{"title": title, "fields": fields} for title, fields in by_group.items()]
    return groups


# ---- [Input] lines found in a loaded ini that the wizard does not define ---------------------------------------
# A connected game controller (or other device) adds lines such as Device.SDLJoy_<id>.Name, Mapping.Nudge0.X or
# Device.<id>.Element3. Their ids and names are machine specific and can't be detected here, so they are read from
# the loaded file and shown as they are. Kinds that VPX's source defines get their real type; everything else is text.

DEVICE_TYPES = [("0", "Unknown"), ("1", "Keyboard"), ("2", "Joystick"), ("3", "Mouse"), ("4", "VRController"), ("5", "OpenPinDev")]
NUDGE_TYPES = [("0", "Game Controller"), ("1", "Intent Sensor"), ("2", "Cabinet Sensor")]
NUDGE_TYPE_HELP = ("Game controller uses the stick position to evaluate the players nudge intent. Intent Sensor uses the sensor to "
                   "evaluate the player nudge intent, while the Cabinet Sensor directly maps the sensor to a simulated nudge (only "
                   "valid on a real pinball cabinet with a high frequency, low latency, noise free sensor on a high speed "
                   "communication port).")
SENSOR_HELP = "Sensor mapping (<device>;<axis>;...) shown as it appears in the ini."

_DEVICE_LINE = re.compile(r"Device\.(.+)\.(Type|NoAutoLayout|Name|Element\d+)")
_NUDGE_LINE = re.compile(r"Mapping\.Nudge\d+\.(Type|Strength|CabWeight|X|Y)")
_SENSOR_LINE = re.compile(r"Mapping\.(Plunger|Nudge)\d+\.\w+")

GROUP_DEVICES = "Devices in this file"
GROUP_SENSORS = "Plunger and nudge sensors"
GROUP_MAPPINGS = "Other mappings in this file"
GROUP_ELEMENTS = "Device elements (written by VPX)"
GROUP_OTHER = "Other lines in this file"


def _dynamic_setting(key):
    """(group title, Setting) for an [Input] line. The label is the key itself: these are the file's own lines."""
    def text(description):
        return S("Input", key, type="text", default="", label=key, description=description, placeholder="")

    m = _DEVICE_LINE.fullmatch(key)
    if m:
        kind = m[2]
        if kind == "Type":
            return GROUP_DEVICES, S("Input", key, type="select", options=DEVICE_TYPES, default="", label=key,
                                    description="Kind of input device. Blank: VPX detects it.")
        if kind == "NoAutoLayout":
            return GROUP_DEVICES, S("Input", key, type="bool", default="0", label=key,
                                    description="Disable proposing to overwrite settings with the default layout for this device "
                                                "in upcoming sessions.")
        if kind == "Name":
            return GROUP_DEVICES, text("Name of this input device.")
        return GROUP_ELEMENTS, text("Written by VPX: <element id>;<kind>;<name> of a button or axis of this device.")
    m = _NUDGE_LINE.fullmatch(key)
    if m and m[1] == "Type":
        return GROUP_SENSORS, S("Input", key, type="select", options=NUDGE_TYPES, default="0", label=key, description=NUDGE_TYPE_HELP)
    if m and m[1] == "Strength":
        return GROUP_SENSORS, S("Input", key, type="float", default="1.0", min="0.0", max="2.0", label=key,
                                description="Custom strength factor applied to this sensor.")
    if m and m[1] == "CabWeight":
        return GROUP_SENSORS, S("Input", key, type="float", default="113.0", min="0.0", max="200.0", label=key,
                                description="Weight of the cabinet (kg). This is needed to compute the nudge force from the "
                                            "acquired acceleration.")
    if _SENSOR_LINE.fullmatch(key):
        return GROUP_SENSORS, text(SENSOR_HELP)
    if key.startswith("Mapping."):
        return GROUP_MAPPINGS, S("Input", key, type="mapping", default="", label=key, description=MAPPING_HELP)
    return GROUP_OTHER, text("Line found in the loaded ini.")


def dynamic_input_groups(file_keys, static_keys, template_doc):
    """Resolved groups (same shape as steps.build_steps) for the [Input] keys of a loaded ini that the wizard doesn't define."""
    groups = {}
    for key in file_keys:
        if key in static_keys:
            continue
        title, setting = _dynamic_setting(key)
        groups.setdefault(title, []).append(resolve(setting, template_doc, "Input", title))
    order = [GROUP_DEVICES, GROUP_SENSORS, GROUP_MAPPINGS, GROUP_OTHER, GROUP_ELEMENTS]
    return [{"title": t, "collapsed": t == GROUP_ELEMENTS, "fields": groups[t]} for t in order if t in groups]
