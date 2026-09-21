"""Produce the new ini from a base ini and the wizard answers."""
from .ini import IniDocument


def _same(a, b, ftype):
    if ftype in ("int", "float"):
        try:
            return float(a) == float(b)
        except ValueError:
            return False
    return a == b


def _plan(field, answer, base_value):
    """New value to write for a key, or None to leave the base untouched. '' means 'back to the VPX default'."""
    want = (answer or "").strip()
    base = (base_value or "").strip()
    if want and _same(want, field["default"], field["type"]):   # equal to VPX's default: leave it blank (blank means the default)
        want = ""
    if not want:
        return "" if base and not _same(base, field["default"], field["type"]) else None
    return want if not base or not _same(want, base, field["type"]) else None


def changes(fields, values, base):
    """Keys whose value in the output differs from the base ini (an IniDocument)."""
    out = []
    for fid, f in fields.items():
        was = base.get(f["section"], f["key"]) or ""
        new = _plan(f, values.get(fid), was)
        if new is None:
            continue
        out.append({"id": fid, "section": f["section"], "key": f["key"], "step": f["step"], "parent": f.get("parent", ""), "group": f["group"], "label": f["label"],
                    "value": new, "was": was, "default": f["default_label"]})
    return out


def generate(base_text, fields, values):
    doc = IniDocument(base_text)
    todo = changes(fields, values, IniDocument(base_text))
    for c in todo:
        doc.set(c["section"], c["key"], c["value"])
    return doc.to_text(), todo
