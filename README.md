
# Flame Client

A Python-powered utility client for Minecraft, built on Minescript.  
**For educational and anarchy use only.**

## ⚠️ Disclaimer

This project is for **educational and research purposes**. Do not use on servers where it violates the Terms of Service.

## What Makes Flame Client Unique?

- **Scripted in Python:** No Java modding required. All logic is in Python, running via Minescript.
- **Live Reload:** Change scripts and settings without restarting Minecraft.
- **Modular:** Enable only the features you want.
- **Open Source:** No obfuscation or hidden code.

## Installation

1. Install **Fabric Loader** for your Minecraft version.
2. Add **Fabric API** and **Minescript** to your `mods` folder.
3. Place the `FlameClient` folder inside your `mods/minescript/` directory.

## Usage

1. Launch Minecraft and join a world/server.
2. Run the client’s Python process (`flame_client_menu.bat`).
3. Use the in-game Minescript GUI to open the Flame Client menu (Right Shift by default).
4. Use the GUI to toggle modules, adjust settings, and reload scripts.

## Features

### Combat
- **SwordBot:** Automated melee combat with aim randomization, strafe, and configurable keys.
- **TriggerBot:** Auto-attacks when your crosshair is over a target.
- **Auto Crystal/Anchor:** Automated end crystal and respawn anchor combat.
- **Axe Mode:** Switches SwordBot to use axes.

### ESP (Extrasensory Perception)
- **Boxes:** Draws boxes around players.
- **Healthbars:** Shows health (green to red) next to players.
- **Nametags:** Customizable name display.
- **Item Display:** Shows held item.
- **Configurable Colors, Alpha, and Scale.**

### Utility
- **Auto Speed Bridge:** Automated bridging.
- **Breezily Bridge:** Alternates S + A/D for fast bridging.
- **Keybinds:** All features have customizable keybinds.
- **Menu Settings:** Opacity, color, and more.

### Render
- **Customizable text and box colors.**
- **Outline and alpha settings.**

## Hot Reloading

- Use the **Reload Minescript Jobs** button in the console window to reload all scripts without restarting Minecraft.
- Use **Reload Config** to reload settings from disk.

## Controls

- **Right Shift:** Open/close the menu.
- **All keybinds are customizable in the GUI.**

## License

GNU GPLv3. Free to modify and distribute, but must remain open-source.