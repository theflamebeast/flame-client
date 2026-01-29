from flameclient.esp.imports import *;
from flameclient.config import COLORS, SETTINGS;

def make_color(a, r, g, b):
    # Manual ARGB packing to avoid class resolution issues
    val = (a << 24) | (r << 16) | (g << 8) | b
    # Convert to signed 32-bit int for Java
    if val > 0x7FFFFFFF:
        val -= 0x100000000
    return val

def parse_color(hex_str):
    if not isinstance(hex_str, str): return hex_str
    hex_str = hex_str.lstrip('#')
    if len(hex_str) == 8:
        a = int(hex_str[0:2], 16)
        r = int(hex_str[2:4], 16)
        g = int(hex_str[4:6], 16)
        b = int(hex_str[6:8], 16)
    elif len(hex_str) == 6:
        a = 255
        r = int(hex_str[0:2], 16)
        g = int(hex_str[2:4], 16)
        b = int(hex_str[4:6], 16)
    else:
        return 0xFFFFFFFF
    return make_color(a, r, g, b)

def update_colors():
    for key in COLORS:
        COLORS[key] = parse_color(COLORS[key])

# Initial load
update_colors()

def safe_literal(text):
    try:
        return component.literal(text)
    except:
        try:
            return component.method_43470(text)
        except:
            return component.literal(text)

try:
    _empty_style = style.EMPTY
except:
    try:
        _empty_style = style.field_24360
    except:
        _empty_style = safe_literal("").getStyle()

try:
    FLAGS = _empty_style.withShadowColor(0xFFFFFF)
except:
    FLAGS = _empty_style

try:
    MINECRAFT = minecraft_class.getInstance()
except:
    MINECRAFT = minecraft_class.method_1551()

try:
    WINDOW = MINECRAFT.getWindow()
except:
    WINDOW = MINECRAFT.method_22683()

try:
    GAME_RENDERER = MINECRAFT.gameRenderer
except:
    GAME_RENDERER = MINECRAFT.field_1773

try:
    PLAYER = MINECRAFT.player
except:
    PLAYER = MINECRAFT.field_1724

try:
    LEVEL = MINECRAFT.level
except:
    LEVEL = MINECRAFT.field_1687

try:
    OPTIONS = MINECRAFT.options
except:
    OPTIONS = MINECRAFT.field_1690

try:
    FONT = MINECRAFT.font
except:
    FONT = MINECRAFT.field_1772

# Access protected field for font manager if needed (kept from original)
try:
    FONT_MANAGER = MINECRAFT.getClass().getDeclaredField("field_1708");
    FONT_MANAGER.setAccessible(True);
except:
    pass # Might fail on different mappings/versions

import flameclient.esp.drawing as DRAWING;
import flameclient.esp.math as MATH;

class EVENT_MANAGER_CLASS:
    def __init__(self):
        self.events = { };
        
    def register(self, name, callback):
        self.events[name] = callback;

EVENT_MANAGER = EVENT_MANAGER_CLASS();

_debug_hud_ticks = 0
_debug_no_events_ticks = 0

# Keep strong references so the callback isn't GC'd.
HUD_MANAGED_CALLBACK = None
HUD_RENDER_CALLBACK = None

def HUD_RENDER(draw_context, _):
    global _debug_hud_ticks
    global _debug_no_events_ticks
    try:
        if SETTINGS.get("DEBUG_MODE", False):
            _debug_hud_ticks = _debug_hud_ticks + 1
            # Throttle to avoid chat spam: roughly once per ~300 frames.
            if _debug_hud_ticks % 300 == 0:
                try:
                    echo("[flameclient] HUD_RENDER tick")
                except:
                    pass

            if len(EVENT_MANAGER.events) == 0:
                _debug_no_events_ticks = _debug_no_events_ticks + 1
                # Throttle: about once per ~300 frames while empty.
                if _debug_no_events_ticks % 300 == 0:
                    try:
                        echo("[flameclient] ESP: no render events registered")
                    except:
                        pass
            else:
                _debug_no_events_ticks = 0

        for name, callback in EVENT_MANAGER.events.items():
            try:
                callback(draw_context);
            except Exception as e:
                if SETTINGS.get("DEBUG_MODE", False):
                    try:
                        echo("[flameclient] ESP event '" + str(name) + "' exception: " + str(e))
                    except:
                        pass
    except Exception as e:
        # Never let exceptions bubble into Fabric's render loop.
        if SETTINGS.get("DEBUG_MODE", False):
            try:
                echo("[flameclient] HUD_RENDER exception: " + str(e))
            except:
                pass

# Register the HUD render callback.
# IMPORTANT: Do not register a null callback; Fabric will crash if a null event is invoked.
try:
    # Per Minescript v5 docs: HudRenderCallback.EVENT.register(HudRenderCallback(ManagedCallback(...)))
    # Also disable cancel_on_exception so transient rendering errors don't permanently disable ESP.
    HUD_MANAGED_CALLBACK = ManagedCallback(HUD_RENDER, False)
    HUD_RENDER_CALLBACK = hud_render_callback(HUD_MANAGED_CALLBACK)
    if HUD_RENDER_CALLBACK is not None:
        hud_render_callback.EVENT.register(HUD_RENDER_CALLBACK)
    else:
        if SETTINGS.get("DEBUG_MODE", False):
            echo("[flameclient] ESP HUD register returned null")
except Exception as e:
    if SETTINGS.get("DEBUG_MODE", False):
        try:
            echo("[flameclient] ESP HUD register failed: " + str(e))
        except:
            pass
