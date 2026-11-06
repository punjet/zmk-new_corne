# Karabiner rules for this keymap

The keymap on branch `mac-aerospace` only works together with these Karabiner-Elements rules. The firmware sends keys a Mac keyboard lacks, and Karabiner turns them into the real action for the active layout (ABC or RussianWin):

| Firmware sends | From | Karabiner does |
|---|---|---|
| Pause | Left FN tap | toggle ABC ↔ RussianWin |
| Scroll Lock / Print Screen | chords `jkl;` / `asdf` | `,` / `.` in both layouts |
| Insert / Application | Left FN + S / D | `[` / `]` (in Obsidian also on RussianWin) |
| Keypad = | Right FN + Space (Sol macro) | Right Option + Space |
| Keypad 0 | Left Cmd + Left FN chord | plain Left Option |
| Keypad 1 | Left FN + B | Option + Backspace |
| Keypad 2 / 3 | Left FN + F+D / J+K | Option + ← / → |
| Right Option | hold rightmost thumb, in Logic Pro / Final Cut Pro | Hyper (⌘⌃⌥) |
| Left Option / Caps Lock | Right FN / double-tap Shift | Hyper (Left Option stays Option in Logic Pro / Final Cut Pro) |

Don't use F13–F24: the default NKRO report can't send them, and enabling the extended NKRO report changes the HID descriptor, which macOS doesn't pick up over BLE.

## Usage

```sh
python3 karabiner/sync.py install   # put corne.json into ~/.config/karabiner/karabiner.json
python3 karabiner/sync.py export    # save the current rules from the Mac back into corne.json
```

`install` backs up `karabiner.json` first and replaces only rules with the same description. Karabiner reloads the file on its own.

Run `export` and commit after changing a rule in Karabiner. `corne.json` also uses Karabiner's import format, so it can be copied to `~/.config/karabiner/assets/complex_modifications/` and enabled from the Karabiner UI.
