# JW Search for ZBrush 2025.3

This folder now includes a first-pass ZScript search tool:

- [JW_CommandSearch.txt](/c:/Users/jwilc/Documents/maya/scripts/jw/zBrush/JW_CommandSearch.txt)
- [JW_CommandSearch_Macro.txt](/c:/Users/jwilc/Documents/maya/scripts/jw/zBrush/JW_CommandSearch_Macro.txt)
- [Deploy_JW_CommandSearch.bat](/c:/Users/jwilc/Documents/maya/scripts/jw/zBrush/Deploy_JW_CommandSearch.bat)
- [Deploy_JW_CommandSearch.ps1](/c:/Users/jwilc/Documents/maya/scripts/jw/zBrush/Deploy_JW_CommandSearch.ps1)

## What it does

It adds a startup macro button, prompts for a text query, and shows matching results from a curated command and brush catalog.

This is designed to feel like a lightweight Maya-style command search, within the limits of ZBrush 2025.3's ZScript system.

## Install

1. Double-click [Deploy_JW_CommandSearch.bat](/c:/Users/jwilc/Documents/maya/scripts/jw/zBrush/Deploy_JW_CommandSearch.bat).
2. The deploy script copies [JW_CommandSearch_Macro.txt](/c:/Users/jwilc/Documents/maya/scripts/jw/zBrush/JW_CommandSearch_Macro.txt) into `C:\Program Files\Maxon ZBrush 2025\ZStartup\Macros\JW\JW Command Search.txt`.
3. Restart ZBrush.
4. Open `Macro:JW`.
5. `Ctrl+Alt+click` `JW Command Search` and press `Ctrl+F` if ZBrush accepts that combo in your setup.
6. Store the hotkey in `Preferences:Hotkeys:Store`.

## Notes

ZBrush 2025.3 predates the newer Python SDK docs that Maxon publishes for 2026.x, so this implementation uses classic ZScript. Official docs for startup plugins expect compiled `.zsc` files in `ZPlugs64`, while macros can be installed as text and auto-loaded from `ZStartup\Macros`. Because of that, this deployment uses a macro for the no-compile path. The search itself still uses a hand-built catalog instead of a true live index of all UI controls.

The current pass expands the catalog substantially and makes the macro easier to maintain by grouping entries into logical sections like Transform, Geometry, SubTool, Masking, and Brushes.
