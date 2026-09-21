"""Plugin settings shown on the Plugins page: `Enable` for every plugin in the default ini, plus the
parameters found in the reference config.

Labels, ranges and defaults come from the plugin sources in the vpinball repo (plugins/<name>/, the
MSGPI_*_SETTING lines), because these keys have no comments in the ini. Where the source has a
description it is used as is. The B2SLegacy B2S* keys have none there, so their descriptions are
written from how the plugin code uses them (the B2S* keys, AltSound Folder, PinMAME Cheat, PUP PUPFolder).
Parameters still missing are listed in docs/PLAN.md.

Plugins that are not in the default ini (EXTRA_PLUGINS) have no comment to read. VPX gives them a generic
`Enable` (player.cpp: default Off), so that default is set here, and the description is the plugin's own
plugin.cfg text.
"""
from .settings import Setting as S

# [Plugin.<name>] sections of the default ini, in its order (a test checks none is missing).
PLUGINS = ["AltSound", "B2SLegacy", "DMDUtil", "FlexDMD", "PinMAME", "PUP", "ScoreView", "Serum", "WMP", "VNI"]


# Plugins present in the reference config but not in the default ini: (id, plugin.cfg description, notes).
# Kiki is development tooling and is deliberately not listed.
EXTRA_PLUGINS = [
    ("vpx", "Visual Pinball X core plugin.",
     ["VPX's own in-game settings hide this plugin because disabling it would crash the app. "
      "Leave it at the default unless you know you need to change it."]),
    ("UpscaleDMD", "Upscale DMD output either to a regular LCD/CRT display or a high res DMD.", None),
    ("B2S", "B2S renderer (Backglass Second Screen).", None),
    ("DOF", "Direct Output Framework plugin for hardware control.", None),
    ("HelloScript", "Show how to expose plugin to script.", None),
    ("Inspector", "VPX Inspector Plugin.", None),
    ("RemoteControl", "Use one computer to play on another computer on the same local area network.", None),
    ("AlphaDMD", "Render alphanumeric segment displays on a DMD.", None),
    ("HelloWorld", "Just a Hello World.", None),
]


def _b2s_dmd(prefix, label, where):
    section = "Plugin.B2SLegacy"
    return [
        S(section, f"{prefix}DMDOverlay", type="bool", default="0", label=f"{label} DMD Overlay",
          description=f"Enable a DMD overlay on the {where}"),
        S(section, f"{prefix}DMDAutoPos", type="bool", default="0", label=f"{label} DMD Automatic position",
          description="Enable automatic DMD bounds detection"),
        S(section, f"{prefix}DMDX", type="int", default="0", min="0", max="65535", label=f"{label} DMD X position",
          description="DMD overlay X position"),
        S(section, f"{prefix}DMDY", type="int", default="0", min="0", max="65535", label=f"{label} DMD Y position",
          description="DMD overlay Y position"),
        S(section, f"{prefix}DMDW", type="int", default="0", min="0", max="65535", label=f"{label} DMD width",
          description="DMD overlay width"),
        S(section, f"{prefix}DMDH", type="int", default="0", min="0", max="65535", label=f"{label} DMD height",
          description="DMD overlay height"),
    ]


def _b2s_general():
    """B2SLegacy's B2S* keys (B2SSettings.cpp, B2SScreen.cpp). Source defaults: Hide DMD is On, the rest Off."""
    section = "Plugin.B2SLegacy"
    return [
        S(section, "B2SHideGrill", type="bool", default="0", label="B2S Hide Grill",
          description="Hide the grill part of the B2S backglass."),
        S(section, "B2SHideB2SDMD", type="bool", default="0", label="B2S Hide B2S DMD",
          description="Hide the DMD that is embedded in the B2S backglass file."),
        S(section, "B2SHideB2SBackglass", type="bool", default="0", label="B2S Hide B2S Backglass",
          description="Do not draw the B2S backglass image."),
        S(section, "B2SHideDMD", type="bool", default="1", label="B2S Hide DMD",
          description="Hide the DMD."),
        S(section, "B2SDualMode", type="select", default="1", options=[("1", "Authentic"), ("2", "Fantasy")],
          label="B2S Dual Mode", description="Which variant of a dual-mode B2S backglass to use."),
        S(section, "B2SBackglassWidth", type="int", default="1024", min="0", max="16384", label="B2S Backglass Width",
          description="Backglass width, in pixels, used by the B2S renderer."),
        S(section, "B2SBackglassHeight", type="int", default="768", min="0", max="16384", label="B2S Backglass Height",
          description="Backglass height, in pixels, used by the B2S renderer."),
        S(section, "B2SDMDWidth", type="int", default="512", min="0", max="16384", label="B2S DMD Width",
          description="DMD width, in pixels, used by the B2S renderer."),
        S(section, "B2SDMDHeight", type="int", default="128", min="0", max="16384", label="B2S DMD Height",
          description="DMD height, in pixels, used by the B2S renderer."),
        S(section, "B2SDMDFlipY", type="bool", default="0", label="B2S DMD Flip Y",
          description="Flip the DMD image vertically."),
    ]


def _dmdutil():
    """DMDUtil parameters (DMDUtilPlugin.cpp). The plugin passes each one to the DMDUtil library; the source gives them no
    description, so the text is written from how they are used. Defaults: FindDisplays is On, the other switches Off."""
    section = "Plugin.DMDUtil"

    def flag(key, label, description, default="0"):
        return S(section, key, type="bool", default=default, label=label, description=description)

    def number(key, label, description, default, lo, hi):
        return S(section, key, type="int", default=default, min=lo, max=hi, label=label, description=description)

    def text(key, label, description, default=""):
        return S(section, key, type="text", default=default, label=label, description=description)

    return [
        flag("ZeDMD", "ZeDMD", "Send the DMD to a ZeDMD device."),
        flag("ZeDMDDebug", "ZeDMD Debug", "Enable ZeDMD debug output."),
        number("ZeDMDBrightness", "ZeDMD Brightness", "Brightness sent to the ZeDMD. -1 means not set.", "-1", "-1", "1000"),
        flag("ZeDMDWiFiEnabled", "ZeDMD WiFi Enabled", "Connect to the ZeDMD over WiFi."),
        flag("ZeDMDSPIEnabled", "ZeDMD SPI Enabled", "Connect to the ZeDMD over SPI."),
        number("ZeDMDSPISpeed", "ZeDMD SPI Speed", "SPI clock speed of the ZeDMD connection, in Hz.", "72000000", "0", "100000000"),
        number("ZeDMDSPIFramePause", "ZeDMD SPI Frame Pause", "Pause between frames when sending over SPI.", "2", "0", "1000"),
        number("ZeDMDSPIWidth", "ZeDMD SPI Width", "Width of the ZeDMD display, in pixels.", "128", "0", "1000"),
        number("ZeDMDSPIHeight", "ZeDMD SPI Height", "Height of the ZeDMD display, in pixels.", "32", "0", "1000"),
        flag("Pixelcade", "Pixelcade", "Send the DMD to a Pixelcade."),
        flag("PIN2DMD", "PIN2DMD", "Send the DMD to a PIN2DMD."),
        flag("DMDServer", "DMD Server", "Send the DMD to a DMD server."),
        number("DMDServerPort", "DMD Server Port", "Port of the DMD server.", "6789", "0", "65535"),
        flag("FindDisplays", "Find Displays", "Look for connected DMD displays.", default="1"),
        flag("DumpDMDTxt", "Dump DMD Text", "Write the DMD frames to a text dump (for debugging)."),
        flag("DumpDMDRaw", "Dump DMD Raw", "Write the DMD frames to a raw dump (for debugging)."),
        number("LumTintR", "Luminance Tint Red", "Red part of the tint applied to a luminance-only DMD (red = luminance x this, 0-255).",
               "255", "0", "255"),
        number("LumTintG", "Luminance Tint Green", "Green part of the tint applied to a luminance-only DMD (0-255).", "140", "0", "255"),
        number("LumTintB", "Luminance Tint Blue", "Blue part of the tint applied to a luminance-only DMD (0-255).", "0", "0", "255"),
        text("ZeDMDDevice", "ZeDMD Device", "Device (port) of the ZeDMD."),
        text("ZeDMDWiFiAddr", "ZeDMD WiFi Address", "Network address of the ZeDMD when using WiFi.", default="zedmd-wifi.local"),
        text("PixelcadeDevice", "Pixelcade Device", "Device (port) of the Pixelcade."),
        text("DMDServerAddr", "DMD Server Address", "Address of the DMD server.", default="localhost"),
    ]


def _pup_pads(prefix, label, where):
    return [S("Plugin.PUP", f"{prefix}Pad{side}", type="int", default="0", min="0", max="4096",
              label=f"{label} {side} Pad", description=f"{side} Padding of {where}")
            for side in ("Left", "Right", "Top", "Bottom")]


def _folder(plugin, key, label, description, notes=None):
    return S(f"Plugin.{plugin}", key, type="text", default="", label=label, description=description, notes=notes)


PARAMETERS = {
    "DMDUtil": _dmdutil(),
    "AltSound": [_folder("AltSound", "Folder", "AltSound Folder",
                         "Global AltSound folder, used when the table has no altsound folder of its own.",
                         notes=["Give the path of an 'altsound' folder; the plugin looks for 'altsound/<rom name>' "
                                "in that folder's parent."])],    "B2SLegacy": (_b2s_dmd("Backglass", "Backglass", "Backglass") + _b2s_dmd("ScoreView", "ScoreView", "Score View")
                  + _b2s_general()),
    "PinMAME": [S("Plugin.PinMAME", "Cheat", type="bool", default="0", label="Cheat Mode",
                  description="Start PinMAME games in cheat mode."),
                _folder("PinMAME", "PinMAMEPath", "PinMAME Path", "Folder that contains PinMAME subfolders (roms, nvram, ...)")],
    "PUP": (_pup_pads("BG", "Backglass", "backglass") + _pup_pads("SV", "Score View", "Score View")
            + _pup_pads("Topper", "Topper", "topper")
            + [S("Plugin.PUP", "MainVol", type="float", default="1.0", min="0.0", max="1.0",
                 label="Main Volume", description="Overall volume"),
               _folder("PUP", "PUPFolder", "PinUp Player Folder",
                       "Global PinUp Player folder, in which PUP looks for a 'pupvideos' folder.",
                       notes=["When blank, the 'pupvideos' folder next to each table is used."])]),
    "ScoreView": [_folder("ScoreView", "LayoutFolder", "Layout Folder", "Folder where custom ScoreView layouts are stored")],
    "Serum": [_folder("Serum", "SerumPath", "Serum Path", "Folder that contains Serum colorization files (cROMc, cRZ)")],
    "VNI": [_folder("VNI", "VniPath", "VNI Path", "Folder that contains VNI colorization files (PAL, VNI)")],
    "Inspector": [S("Plugin.Inspector", "port", type="int", default="2113", min="1024", max="65535",
                    label="Web Server Port", description="Port used by the inspector web server")],
}


def plugin_groups():
    """One group per plugin: its Enable switch, then its parameters. Default-ini plugins first, then EXTRA_PLUGINS."""
    groups = [{"title": name, "fields": [S(f"Plugin.{name}", "Enable", label="Enable"), *PARAMETERS.get(name, [])]}
              for name in PLUGINS]
    groups += [{"title": name, "fields": [S(f"Plugin.{name}", "Enable", type="bool", default="0", label="Enable",
                                            description=description, notes=notes), *PARAMETERS.get(name, [])]}
               for name, description, notes in EXTRA_PLUGINS]
    return groups


# Page subtitles for the plugins of the default ini (plugin.cfg descriptions; PinMAME's own is just "PinMAME").
PLUGIN_DESCRIPTIONS = {
    "AltSound": "Provides alternate sound for PinMAME based tables.",
    "B2SLegacy": "B2SLegacy renderer (Backglass Second Screen).",
    "DMDUtil": "Cross platform library for performing DMD tasks.",
    "FlexDMD": "A plugin to create DMD from script.",
    "PinMAME": "Emulation of ROM based pinball machines (PinMAME).",
    "PUP": "Pin Up Player renderer.",
    "ScoreView": "Displays score on an ancillary window.",
    "Serum": "Serum DMD Colorization.",
    "VNI": "VNI DMD Colorization.",
    "WMP": "WMP audio support (bloodm, ag).",
}


def plugin_steps():
    """One wizard page per plugin, listed under the "Plugins" header of the sidebar (`parent`)."""
    extra = {name: description for name, description, _ in EXTRA_PLUGINS}
    return [{"id": "plugin-" + group["title"].lower(), "title": group["title"], "parent": "Plugins",
             "description": PLUGIN_DESCRIPTIONS.get(group["title"]) or extra.get(group["title"], ""),
             "groups": [group]}
            for group in plugin_groups()]
