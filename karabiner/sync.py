#!/usr/bin/env python3
"""Keep the Karabiner rules this keymap depends on in the repo.

    python3 karabiner/sync.py export    # ~/.config/karabiner/karabiner.json -> karabiner/corne.json
    python3 karabiner/sync.py install   # karabiner/corne.json -> ~/.config/karabiner/karabiner.json

The firmware sends keys a Mac keyboard lacks (Pause, Scroll Lock, Keypad ...)
and these rules turn them into the real actions, so the keymap is useless
without them. `install` backs up karabiner.json, replaces rules with the same
description in the selected profile (others are left alone) and makes sure
Karabiner modifies the Corne device.
"""
import json
import shutil
import sys
import time
from pathlib import Path

KARABINER = Path.home() / ".config/karabiner/karabiner.json"
REPO_FILE = Path(__file__).resolve().parent / "corne.json"
TITLE = "Eyelash Corne (zmk-new_corne mac-aerospace)"
CORNE = {"vendor_id": 7504, "product_id": 24926}  # 0x1D50 / 0x615E

# Rules that belong to this keyboard setup: everything prefixed "Corne: "
# plus the Hyper rule that the Right FN macro relies on.
EXTRA = ("Caps Lock and Left Option to Cmd+Ctrl+Alt",)


def ours(rule):
    d = rule.get("description", "")
    return d.startswith("Corne: ") or d.startswith(EXTRA)


def selected_profile(cfg):
    for p in cfg["profiles"]:
        if p.get("selected"):
            return p
    return cfg["profiles"][0]


def export():
    cfg = json.loads(KARABINER.read_text())
    rules = [r for r in selected_profile(cfg).get("complex_modifications", {}).get("rules", []) if ours(r)]
    REPO_FILE.write_text(json.dumps({"title": TITLE, "rules": rules}, indent=4, ensure_ascii=False) + "\n")
    for r in rules:
        print("exported:", r["description"])


def install():
    new = json.loads(REPO_FILE.read_text())["rules"]
    backup = KARABINER.with_name(f"karabiner.json.bak-{time.strftime('%Y%m%d-%H%M%S')}")
    shutil.copy2(KARABINER, backup)
    cfg = json.loads(KARABINER.read_text())
    prof = selected_profile(cfg)
    rules = prof.setdefault("complex_modifications", {}).setdefault("rules", [])
    names = {r["description"] for r in new}
    rules[:] = [r for r in rules if r.get("description") not in names] + new

    devices = prof.setdefault("devices", [])
    if not any(d.get("identifiers", {}).get("vendor_id") == CORNE["vendor_id"]
               and d.get("identifiers", {}).get("product_id") == CORNE["product_id"] for d in devices):
        devices.append({"identifiers": {"is_keyboard": True, "is_pointing_device": True, **CORNE}, "ignore": False})

    KARABINER.write_text(json.dumps(cfg, indent=4, ensure_ascii=False) + "\n")
    print("backup:", backup)
    for r in new:
        print("installed:", r["description"])


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "export":
        export()
    elif cmd == "install":
        install()
    else:
        sys.exit(__doc__)
