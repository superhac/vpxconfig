"""One wizard setting: the structure to add or change entries in.

    Setting("Player", "BGSet")                      # everything comes from the template ini's comment
    Setting("Player", "BGSet", label="View Mode")   # ...except what you give explicitly
    Setting("Input", "Mapping.Tilt", type="text", label="Tilt", default="", description="...")  # key not in the template

Any attribute left as None is taken from the comment above the key in the template ini
(`; Label: description [Default: ...]`). A key that is not in the template has no comment to
read, so it needs at least `type`; label, default, options and min/max are then given here too.
"""
import math
import re
from dataclasses import dataclass

from .ini import FieldMeta

DISPLAY = "display"  # free text with a dropdown of the monitors detected on this machine
MAPPING = "mapping"  # a button mapping such as "Key;225" (edited with a key-capture button)
TYPES = ("bool", "int", "float", "text", "select", DISPLAY, MAPPING)


@dataclass
class Setting:
    section: str                 # ini section, e.g. "Player"
    key: str                     # ini key, e.g. "BGSet"
    label: str = None            # short name shown in the UI (default: from the template, else the key)
    description: str = None      # help text under the field
    type: str = None             # bool | int | float | text | select | display (default: inferred)
    default: str = None          # VPX's own default; a blank ini value means this
    options: list = None         # acceptable values for select/bool: [("0", "Disabled"), ("1", "Enabled")]
    min: str = None              # acceptable range for int/float
    max: str = None
    placeholder: str = None      # grey hint in empty inputs (default: the default; "" = none)
    notes: list = None           # extra help lines
    initial: str = None          # answer the wizard starts with (a suggestion; the user can change or clear it)


def _infer_type(options, lo, hi, default):
    if options:
        return "select"
    if lo is not None:
        return "float" if any("." in str(x) for x in (default, lo, hi) if x is not None) else "int"
    if default in ("0", "1"):
        return "bool"
    return "text"


def _pick(explicit, from_template):
    return from_template if explicit is None else explicit


def _check(f):
    """Catch mistakes in a definition at startup instead of at runtime."""
    where = f["id"]
    if f["type"] not in TYPES:
        raise ValueError(f"{where}: type must be one of {', '.join(TYPES)}, not {f['type']!r}")
    values = [o["value"] for o in f["options"]]
    if f["type"] in ("select", "bool"):
        if not values:
            raise ValueError(f"{where}: a {f['type']} setting needs options")
        if len(set(values)) != len(values):
            raise ValueError(f"{where}: duplicate option values")
        if f["default"] != "" and f["default"] not in values:
            raise ValueError(f"{where}: default {f['default']!r} is not one of the options {values}")
    if f["type"] in ("int", "float"):
        for name in ("default", "min", "max"):
            v = f[name]
            if v not in (None, ""):
                try:
                    float(v)
                except ValueError:
                    raise ValueError(f"{where}: {name} {v!r} is not a number")
        if f["min"] is not None and f["max"] is not None and float(f["min"]) > float(f["max"]):
            raise ValueError(f"{where}: min is greater than max")


def resolve(setting, template, step_title="", group_title=""):
    """Combine a Setting with what the template ini says about the key. Returns the field dict the UI uses."""
    meta = template.meta(setting.section, setting.key)
    if meta is None and setting.type is None:
        raise ValueError(f"{setting.section}.{setting.key} is not in the template ini, so it needs an explicit "
                         f"type (and usually label, default, options or min/max)")
    m = meta or FieldMeta()
    options = list(_pick(setting.options, m.options))
    lo, hi = _pick(setting.min, m.min), _pick(setting.max, m.max)
    default = _pick(setting.default, m.default)
    ftype = setting.type or _infer_type(options, lo, hi, default)
    if ftype == "bool" and not options:
        options = [("1", "On"), ("0", "Off")]
    f = {
        "id": f"{setting.section}.{setting.key}", "section": setting.section, "key": setting.key,
        "step": step_title, "group": group_title, "type": ftype,
        "label": setting.label or m.label or setting.key,
        "help": _pick(setting.description, m.help),
        "detail": list(_pick(setting.notes, m.detail)),
        "default": default,
        "default_label": next((label for v, label in options if v == default), default),
        "options": [{"value": v, "label": label} for v, label in options],
        "min": lo, "max": hi,
        "placeholder": _pick(setting.placeholder, default),
        "initial": setting.initial or "",
    }
    _check(f)
    return f


def validate(field, value):
    """Why `value` isn't acceptable for this field, or None. Blank always is (it means the VPX default)."""
    v = (value or "").strip()
    if not v:
        return None
    ftype = field["type"]
    if ftype in ("select", "bool"):
        if v not in [o["value"] for o in field["options"]]:
            return "must be one of " + ", ".join(f"{o['value']} ({o['label']})" for o in field["options"])
    elif ftype in ("int", "float"):
        try:
            n = int(v) if ftype == "int" else float(v)
        except ValueError:
            return "must be a whole number" if ftype == "int" else "must be a number"
        if not math.isfinite(n):
            return "must be a number"
        lo, hi = field["min"], field["max"]
        if (lo is not None and n < float(lo)) or (hi is not None and n > float(hi)):
            return f"must be between {lo} and {hi}"
    elif ftype == MAPPING:
        for alternative in v.split("|"):
            for term in (t.strip() for t in alternative.split("&")):
                if not term:
                    return "has an empty part (separate terms with ' | ' or ' & ')"
                if term.startswith("Key;") and not (re.fullmatch(r"Key;\d{1,3}", term) and 1 <= int(term[4:]) <= 511):
                    return f"has an invalid key '{term}' (expected Key;<SDL scancode from 1 to 511>)"
    return None
