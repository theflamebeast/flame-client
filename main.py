import minescript
import time
import threading
import ctypes
import math
import json
import os
import sys

# Allow `import flameclient.*` when this script is executed directly by Minescript.
_current_dir = os.path.dirname(os.path.abspath(__file__))
_minescript_root = os.path.dirname(_current_dir)
if _minescript_root not in sys.path:
    sys.path.insert(0, _minescript_root)

from flameclient.config import SETTINGS

# Import feature logic
# We can import them as modules if they are in the path, or just implement logic here.
# Since we want to keep it simple, let's implement the loops here or import classes.
# But `aimbot.py` etc are currently scripts. Let's make them modules.
# Actually, let's just copy the logic into classes here for cleaner integration.

import random

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "latest.log")

def log(message):
    # Streamer Mode Check
    if SETTINGS.get("STREAMER_MODE", False):
        return

    prefix = [
        {"text": "F", "color": "#f5d020", "bold": True},
        {"text": "l", "color": "#f5b617", "bold": True},
        {"text": "a", "color": "#f59c0e", "bold": True},
        {"text": "m", "color": "#f58305", "bold": True},
        {"text": "e", "color": "#f56a03", "bold": True},
        {"text": "C", "color": "#f55a03", "bold": True},
        {"text": "l", "color": "#f54a03", "bold": True},
        {"text": "i", "color": "#f53a03", "bold": True},
        {"text": "e", "color": "#f53803", "bold": True},
        {"text": "n", "color": "#f53803", "bold": True},
        {"text": "t", "color": "#f53803", "bold": True},
        {"text": " ", "color": "white", "bold": False}
    ]
    full_msg = [""] + prefix + [{"text": str(message), "color": "white"}]
    minescript.echo_json(json.dumps(full_msg))
    
    try:
        with open(LOG_FILE, "a") as f:
            timestamp = time.strftime("%H:%M:%S")
            f.write(f"[{timestamp}] {message}\n")
    except: pass

def debug_log(message):
    if SETTINGS.get("DEBUG_MODE", False):
        log(f"§e[DEBUG] {message}")

# ==========================================
#           FEATURE LOGIC
# ==========================================

CURRENT_SCREEN = None

def is_active_window_minecraft():
    hwnd = ctypes.windll.user32.GetForegroundWindow()
    length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
    buff = ctypes.create_unicode_buffer(length + 1)
    ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
    return "Minecraft" in buff.value

def is_key_held(vk):
    if not vk: return False
    if not is_active_window_minecraft():
        return False
    
    # Disable keybinds in any GUI (Chat, Inventory, etc.)
    if CURRENT_SCREEN is not None:
        return False

    return (ctypes.windll.user32.GetAsyncKeyState(vk) & 0x8000) != 0

def find_hotbar_slot(item_name):
    """Find an item in the hotbar (slots 0-8) and return its slot number."""
    try:
        inventory = minescript.player_inventory()
        for item in inventory:
            if item and item.slot is not None and item.slot < 9:  # Hotbar slots 0-8
                if item_name.lower() in item.item.lower():
                    return item.slot
    except: pass
    return None

def get_held_item():
    """Returns the item ID of the currently held item."""
    try:
        inventory = minescript.player_inventory()
        selected_slot = minescript.player_inventory_slot()
        for item in inventory:
            if item.slot == selected_slot:
                return item.item
    except: pass
    return None

def is_looking_at_block(keyword, reach=6.0):
    try:
        targeted_block = minescript.player_get_targeted_block(reach)
        if targeted_block and targeted_block.type:
            return keyword in targeted_block.type.lower()
    except: pass
    return False

def is_looking_at_entity(keyword, reach=6.0):
    try:
        targeted_entity = minescript.player_get_targeted_entity(reach)
        if targeted_entity and targeted_entity.type:
            return keyword in targeted_entity.type.lower()
    except: pass
    return False

class StreamerMode:
    def __init__(self):
        self.was_key_down = False

    def run(self):
        key = SETTINGS.get("STREAMER_MODE_KEY")
        if key:
            is_down = is_key_held(key)
            if is_down and not self.was_key_down:
                new_state = not SETTINGS.get("STREAMER_MODE", False)
                SETTINGS["STREAMER_MODE"] = new_state
                # We can't use log() here because it might be suppressed if we just turned it on
                # But if we just turned it ON, we probably want to see "Streamer Mode ON" before it goes silent?
                # Or maybe we just force echo this one message.
                
                status = "§aON" if new_state else "§cOFF"
                # Force echo this message even if streamer mode is on (so user knows they toggled it)
                minescript.echo(f"§d[FlameClient] §fStreamer Mode: {status}")
                
            self.was_key_down = is_down

class Aimbot:
    def __init__(self):
        self.active = False
        self.current_target_name = None
        self.last_run = 0
        self.was_key_down = False
        
        # Cooldown & Strafe State
        self.last_attack_time = 0
        self.resume_w_time = 0
        self.was_chasing = False
        
        # Sub-feature Key States
        self.was_strafe_key_down = False
        self.was_attack_key_down = False
        self.was_wtap_key_down = False
        self.was_axe_key_down = False
        
        # Randomness State
        self.random_yaw_offset = 0
        self.random_pitch_offset = 0
        self.last_random_update = 0
        self.next_attack_delay = 0

    def run(self):
        if not SETTINGS.get("AIMBOT_ENABLED", False): return
        
        # 1. Aimbot Toggle Check
        key = SETTINGS.get("AIMBOT_KEY", 0xC0)
        is_down = is_key_held(key)
        
        if is_down and not self.was_key_down:
            self.active = not self.active
            log(f"§fAimbot: {'§aON' if self.active else '§cOFF'}")
            if not self.active:
                self.current_target_name = None
                self.stop_movement()
        self.was_key_down = is_down

        # 2. Sub-feature Toggles
        # Auto Attack
        attack_key = SETTINGS.get("AIMBOT_ATTACK_KEY")
        if attack_key:
            is_attack_down = is_key_held(attack_key)
            if is_attack_down and not self.was_attack_key_down:
                new_state = not SETTINGS.get("AIMBOT_ATTACK_ENABLED", True)
                SETTINGS["AIMBOT_ATTACK_ENABLED"] = new_state
                log(f"§fAuto Attack: {'§aON' if new_state else '§cOFF'}")
            self.was_attack_key_down = is_attack_down

        # Axe Mode
        # Removed manual toggle, now auto-detects held item

        if not self.active: return

        # Safety: Stop if in menu
        if CURRENT_SCREEN is not None:
            if self.was_chasing:
                self.stop_movement()
                self.was_chasing = False
            return

        # Logic
        try:
            target = self.get_target()
            if target:
                mode = SETTINGS.get("AIMBOT_MODE", "1.21")
                if mode == "1.8":
                    self.run_1_8(target)
                else:
                    self.run_1_21(target)
            else:
                if self.was_chasing:
                    self.stop_movement()
                    self.was_chasing = False
        except Exception as e:
            pass

    def stop_movement(self):
        minescript.player_press_forward(False)
        minescript.player_press_left(False)
        minescript.player_press_right(False)
        minescript.player_press_attack(False)

    def get_target(self):
        # 1. Try to maintain lock (if Target Mode is OFF)
        if not SETTINGS.get("AIMBOT_TARGET_MODE", False) and self.current_target_name:
            try:
                candidates = minescript.players(max_distance=SETTINGS["KEEP_TARGET_DISTANCE"])
                target = next((p for p in candidates if p.name == self.current_target_name), None)
                if target: 
                    debug_log(f"Locked: {target.name}")
                    return target
            except: pass
            self.current_target_name = None

        # 2. Find new target (or closest if Target Mode is ON)
        try:
            min_dist = SETTINGS.get("AIMBOT_MIN_DIST", 1.0)
            # Increased limit to 2 to avoid only picking local player
            # Increased max_distance to 6 for better acquisition
            enemies = minescript.players(sort='nearest', limit=2, min_distance=min_dist, max_distance=8)
            if enemies:
                valid = [e for e in enemies if not e.local]
                if valid:
                    self.current_target_name = valid[0].name
                    debug_log(f"Acquired: {valid[0].name}")
                    return valid[0]
        except: pass
        return None

    def get_distance(self, target):
        pos = target.position
        my_pos = minescript.player_position()
        return math.sqrt((pos[0] - my_pos[0])**2 + 
                         (pos[1] - my_pos[1])**2 + 
                         (pos[2] - my_pos[2])**2)

    def aim_at_target(self, target):
        pos = target.position
        my_pos = minescript.player_position()
        
        intensity = SETTINGS.get("AIMBOT_INTENSITY", 5.0)
        
        if intensity >= 5.0:
            # Instant snap (with randomness)
            dx = pos[0] - my_pos[0]
            dy = (pos[1] + 1.6) - (my_pos[1] + 1.62)
            dz = pos[2] - my_pos[2]
            
            target_yaw = -math.degrees(math.atan2(dx, dz)) + self.random_yaw_offset
            horiz_dist = math.sqrt(dx**2 + dz**2)
            target_pitch = -math.degrees(math.atan2(dy, horiz_dist)) + self.random_pitch_offset
            
            minescript.player_set_orientation(target_yaw, target_pitch)
        else:
            # Smooth aim
            dx = pos[0] - my_pos[0]
            dy = (pos[1] + 1.6) - (my_pos[1] + 1.62) # Target Eye - My Eye
            dz = pos[2] - my_pos[2]
            
            # Calculate target angles
            target_yaw = -math.degrees(math.atan2(dx, dz)) + self.random_yaw_offset
            horiz_dist = math.sqrt(dx**2 + dz**2)
            target_pitch = -math.degrees(math.atan2(dy, horiz_dist)) + self.random_pitch_offset
            
            current_yaw, current_pitch = minescript.player_orientation()
            
            # Normalize yaw difference (-180 to 180)
            diff_yaw = (target_yaw - current_yaw + 180) % 360 - 180
            diff_pitch = target_pitch - current_pitch
            
            # Interpolate based on intensity (0.1 to 0.5 factor roughly)
            factor = intensity * 0.15
            if factor > 1.0: factor = 1.0
            
            new_yaw = current_yaw + diff_yaw * factor
            new_pitch = current_pitch + diff_pitch * factor
            
            minescript.player_set_orientation(new_yaw, new_pitch)

    def run_1_8(self, target):
        # 1. Always Aim
        self.aim_at_target(target)
        
        dist = self.get_distance(target)
        min_dist = SETTINGS.get("AIMBOT_MIN_DIST", 1.0)
        
        if dist < min_dist:
            self.stop_movement()
            return

        if dist <= 3.5:
            self.was_chasing = True
            
            # W-Tap Pause Check
            if self.resume_w_time > 0:
                if time.time() >= self.resume_w_time:
                    minescript.player_press_forward(True)
                    self.resume_w_time = 0
                return

            # Attack (Spam Click)
            cps = SETTINGS.get("AIMBOT_CPS", 12)
            if time.time() - self.last_attack_time >= (1.0 / cps):
                minescript.player_press_forward(True)
                
                if SETTINGS.get("AIMBOT_ATTACK_ENABLED", True):
                    minescript.player_press_attack(True)
                    minescript.player_press_attack(False)
                
                self.last_attack_time = time.time()
                
                # W-Tap Logic (Random chance or every N hits?)
                # For 1.8, let's just W-Tap occasionally
                if SETTINGS.get("AIMBOT_WTAP_ENABLED", True):
                    if random.random() < 0.3: # 30% chance per hit
                        minescript.player_press_forward(False)
                        self.resume_w_time = time.time() + 0.1
        else:
            minescript.player_press_forward(True)
            self.was_chasing = True

    def run_1_21(self, target):
        # 1. Always Aim (Reverted to standard behavior)
        self.aim_at_target(target)
        
        dist = self.get_distance(target)
        min_dist = SETTINGS.get("AIMBOT_MIN_DIST", 1.0)
        
        if dist < min_dist:
            self.stop_movement()
            return

        # 2. Check Cooldown
        held_item = get_held_item()
        if held_item and "_axe" in held_item:
            base_cooldown = 1.0
        else:
            base_cooldown = 0.63
            
        ready = (time.time() - self.last_attack_time) >= (base_cooldown + self.next_attack_delay)
        
        # 3. Attack Logic
        if dist <= 3.5:
            self.was_chasing = True
            
            # Handle W-Tap Pause
            if self.resume_w_time > 0:
                if time.time() >= self.resume_w_time:
                    minescript.player_press_forward(True)
                    self.resume_w_time = 0
                    
                    # Change strafe direction
                    if SETTINGS.get("AIMBOT_STRAFE_ENABLED", True):
                        strafe = random.choice(['left', 'right', 'stop'])
                        if strafe == 'left':
                            minescript.player_press_left(True)
                            minescript.player_press_right(False)
                        elif strafe == 'right':
                            minescript.player_press_left(False)
                            minescript.player_press_right(True)
                        else:
                            minescript.player_press_left(False)
                            minescript.player_press_right(False)
                else:
                    pass # Pausing
            else:
                # Not pausing
                if ready:
                    minescript.player_press_forward(True) # Sprint Hit
                    
                    if SETTINGS.get("AIMBOT_ATTACK_ENABLED", True):
                        minescript.player_press_attack(True)
                        minescript.player_press_attack(False)
                    
                    # W-Tap Logic
                    if SETTINGS.get("AIMBOT_WTAP_ENABLED", True):
                        minescript.player_press_forward(False)
                        delay = SETTINGS.get("AIMBOT_WTAP_DELAY", 0.15)
                        self.resume_w_time = time.time() + delay
                    
                    self.last_attack_time = time.time()
                    
                    # Update Randomness
                    timing_randomness = SETTINGS.get("AIMBOT_TIMING_RANDOMNESS", 0.05)
                    self.next_attack_delay = random.uniform(0, timing_randomness)
                    
                    randomness = SETTINGS.get("AIMBOT_RANDOMNESS", 0.0)
                    if randomness > 0:
                        self.random_yaw_offset = random.uniform(-randomness, randomness)
                        self.random_pitch_offset = random.uniform(-randomness, randomness)
                    else:
                        self.random_yaw_offset = 0
                        self.random_pitch_offset = 0
                else:
                    # Just chase
                    minescript.player_press_forward(True)
        else:
            # Target out of attack range but locked on -> Chase
            minescript.player_press_forward(True)
            self.was_chasing = True

class SilentAimbot:
    def __init__(self):
        self.active = False
        self.current_target_name = None
        self.last_attack_time = 0
        self.next_attack_delay = 0
        self.was_key_down = False

    def run(self):
        if not SETTINGS.get("SILENT_AIMBOT_ENABLED", False): return
        
        key = SETTINGS.get("SILENT_AIMBOT_KEY", 0)
        if key:
            is_down = is_key_held(key)
            if is_down and not self.was_key_down:
                self.active = not self.active
                log(f"§fSilent Aimbot: {'§aON' if self.active else '§cOFF'}")
            self.was_key_down = is_down

        if not self.active: return
        if CURRENT_SCREEN is not None: return

        try:
            target = self.get_target()
            if target:
                self.run_logic(target)
            else:
                self.current_target_name = None
        except: pass

    def get_target(self):
        # Simple closest target logic
        try:
            min_dist = SETTINGS.get("AIMBOT_MIN_DIST", 1.0)
            enemies = minescript.players(sort='nearest', limit=2, min_distance=min_dist, max_distance=6)
            if enemies:
                valid = [e for e in enemies if not e.local]
                if valid:
                    return valid[0]
        except: pass
        return None

    def run_logic(self, target):
        pos = target.position
        my_pos = minescript.player_position()
        dist = math.sqrt((pos[0] - my_pos[0])**2 + (pos[1] - my_pos[1])**2 + (pos[2] - my_pos[2])**2)
        
        if dist > 4.0: return # Out of range

        # Check Cooldown
        held_item = get_held_item()
        if held_item and "_axe" in held_item:
            base_cooldown = 1.0
        else:
            base_cooldown = 0.63
            
        ready = (time.time() - self.last_attack_time) >= (base_cooldown + self.next_attack_delay)
        
        if ready:
            # Snap & Attack
            self.aim_at_target(target)
            
            if dist <= 3.5:
                debug_log(f"Silent Aim: Attacking {target.name}")
                minescript.player_press_attack(True)
                minescript.player_press_attack(False)
                self.last_attack_time = time.time()
                
                # Randomness for next hit
                timing_randomness = SETTINGS.get("AIMBOT_TIMING_RANDOMNESS", 0.05)
                self.next_attack_delay = random.uniform(0, timing_randomness)
        else:
            debug_log(f"Silent Aim: Waiting for cooldown (Target: {target.name})")

    def aim_at_target(self, target):
        # Instant snap for silent aim
        pos = target.position
        my_pos = minescript.player_position()
        
        dx = pos[0] - my_pos[0]
        dy = (pos[1] + 1.6) - (my_pos[1] + 1.62)
        dz = pos[2] - my_pos[2]
        
        target_yaw = -math.degrees(math.atan2(dx, dz))
        horiz_dist = math.sqrt(dx**2 + dz**2)
        target_pitch = -math.degrees(math.atan2(dy, horiz_dist))
        
        minescript.player_set_orientation(target_yaw, target_pitch)

    def aim_at(self, target):
        # Legacy wrapper if needed, but we replaced calls to this with run_1_8/run_1_21
        pass



class Triggerbot:
    def __init__(self):
        self.active = False
        self.was_key_down = False
        self.last_attack_time = 0

    def run(self):
        if not SETTINGS.get("TRIGGERBOT_ENABLED", False): return
        
        # Toggle Logic
        key = SETTINGS.get("TRIGGERBOT_KEY", 82) # Default 'R'
        is_down = is_key_held(key)
        
        if is_down and not self.was_key_down:
            self.active = not self.active
            log(f"§fTriggerbot: {'§aON' if self.active else '§cOFF'}")
        self.was_key_down = is_down

        if not self.active: return

        if CURRENT_SCREEN is not None:
            return

        # Logic
        try:
            # Check if looking at entity
            reach = SETTINGS.get("TRIGGERBOT_REACH", 3.0)
            targeted_entity = minescript.player_get_targeted_entity(reach, nbt=True)
            if targeted_entity and targeted_entity.type:
                debug_log(f"Triggerbot looking at: {targeted_entity.type}")
                if "player" in targeted_entity.type.lower(): # Loose match
                    
                    # Setup Logic
                    # Disabled auto-shield detection as it triggers on holding (not just blocking)
                    # is_shield = False
                    # if targeted_entity.nbt and "shield" in targeted_entity.nbt:
                    #     is_shield = True
                        
                    is_1_8 = SETTINGS.get("TRIGGERBOT_1_8_MODE", False)
                    is_axe_mode = SETTINGS.get("TRIGGERBOT_AXE_MODE", False)
                    
                    target_suffix = "_sword"
                    should_spam = False
                    
                    if is_1_8:
                        should_spam = True
                    else:
                        if is_axe_mode:
                            target_suffix = "_axe"
                            # User requested simple axe usage (cooldown) for Axe Mode, 
                            # unless we could detect shield. Since we can't reliably, 
                            # we default to Cooldown for Axe too.
                        
                        # if is_shield:
                        #     target_suffix = "_axe"
                        #     should_spam = True 
                    
                    # Use inventory to find slots
                    try:
                        inventory = minescript.player_inventory()
                        target_slot = -1
                        
                        for item in inventory:
                             if item.slot is not None and 0 <= item.slot <= 8 and item.item:
                                if item.item.endswith(target_suffix):
                                    if target_slot == -1: target_slot = item.slot
                                    break
                    except:
                        target_slot = -1

                    # 1. Switch
                    if target_slot != -1:
                        minescript.player_inventory_select_slot(target_slot)
                    
                    # 2. Attack Logic
                    if should_spam:
                         # 1.8 Spam
                         if time.time() - self.last_attack_time >= 0.05:
                            minescript.player_press_attack(True)
                            minescript.player_press_attack(False)
                            self.last_attack_time = time.time()
                            debug_log("Triggerbot: Attack (Spam)")
                    else:
                        # Modern Cooldown
                        # Axe Speed = 1.0s, Sword Speed = 0.63s
                        cooldown = 1.0 if target_suffix == "_axe" else 0.63
                        
                        if time.time() - self.last_attack_time >= cooldown:
                            minescript.player_press_attack(True)
                            time.sleep(0.05)
                            minescript.player_press_attack(False)
                            self.last_attack_time = time.time()
                            debug_log(f"Triggerbot: Attack (Modern)")
        except: pass


class AttributeSwap:
    def __init__(self):
        self.active = False
        self.was_key_down = False
        self.last_swap_time = 0
        self.cooldown = 0.3

    def run(self):
        if not SETTINGS.get("ATTRIBUTE_SWAP_ENABLED", False): return
        
        key = SETTINGS.get("ATTRIBUTE_SWAP_KEY", 89) # Default 'Y'
        is_down = is_key_held(key)
        
        if is_down and not self.was_key_down:
            if time.time() - self.last_swap_time >= self.cooldown:
                self.last_swap_time = time.time()
                threading.Thread(target=self.swap_sequence).start()
        
        self.was_key_down = is_down

    def swap_sequence(self):
        try:
            # Find weapon (Spear or Mace)
            inventory = minescript.player_inventory()
            weapon_slot = None
            for item in inventory:
                if item.slot is not None and 0 <= item.slot <= 8 and item.item is not None:
                    if item.item.endswith('_spear') or item.item == 'minecraft:mace':
                        weapon_slot = item.slot
                        break
            
            if weapon_slot is not None:
                minescript.player_inventory_select_slot(weapon_slot)
            else:
                minescript.player_inventory_select_slot(7) # Fallback
            
            minescript.player_press_attack(True)
            time.sleep(0.15)
            minescript.player_press_attack(False)
            
            minescript.player_inventory_select_slot(0)
            debug_log("Attribute Swap: Executed")
        except Exception as e:
            debug_log(f"Attribute Swap Error: {e}")


class Bridge:
    def run(self):
        if not SETTINGS.get("BRIDGING_ENABLED", False): return
        
        key = SETTINGS.get("BRIDGE_KEY", 0x33)
        if is_key_held(key):
            pos = minescript.player_position()
            if not pos: return
            
            x, y, z = pos
            bx, by, bz = int(math.floor(x)), int(math.floor(y - 1)), int(math.floor(z))
            
            block = minescript.get_block(bx, by, bz)
            debug_log(f"Bridge: Block below is {block}")
            if "air" in block:
                minescript.player_press_sneak(True)
                minescript.player_press_use(True)
                minescript.player_press_use(False)
            else:
                minescript.player_press_sneak(False)





class AutoAnchor:
    def __init__(self):
        self.active = False
        self.was_key_down = False
        self.last_anchor_time = 0
        self.executing = False

    def run(self):
        if not SETTINGS["ANCHOR_ENABLED"]: return
        
        # Toggle Logic
        key = SETTINGS.get("ANCHOR_KEY", 90) # Default 'Z'
        is_down = is_key_held(key)
        
        if is_down and not self.was_key_down:
            self.active = not self.active
            log(f"§fAuto Anchor: {'§aON' if self.active else '§cOFF'}")
        self.was_key_down = is_down

        if not self.active: return

        # Logic
        if time.time() - self.last_anchor_time >= 0.5 and not self.executing:
            if is_looking_at_block("respawn_anchor"):
                self.executing = True
                log("§eAnchor detected! §fCharging...")
                debug_log("Anchor: Starting sequence")
                threading.Thread(target=self.sequence).start()

    def sequence(self):
        try:
            glowstone_slot = find_hotbar_slot("glowstone")
            if glowstone_slot is not None:
                debug_log(f"Anchor: Found glowstone at slot {glowstone_slot}")
                minescript.player_inventory_select_slot(glowstone_slot)
                time.sleep(0.05)
                
                # Save original camera
                yaw, pitch = minescript.player_orientation()
                
                # Charge 1
                minescript.player_press_use(True)
                time.sleep(0.02)
                minescript.player_press_use(False)
                time.sleep(0.05)
                
                # Move camera down
                minescript.player_set_orientation(yaw, pitch + 20)
                time.sleep(0.02)
                
                # Charge 2
                minescript.player_press_use(True)
                time.sleep(0.02)
                minescript.player_press_use(False)
                time.sleep(0.05)
                
                # Reset camera
                minescript.player_set_orientation(yaw, pitch) 
                time.sleep(0.05)
                
                # Explode
                sword_slot = find_hotbar_slot("sword")
                if sword_slot is not None:
                    minescript.player_inventory_select_slot(sword_slot)
                    time.sleep(0.3)
                    
                    minescript.player_press_use(True)
                    time.sleep(0.02)
                    minescript.player_press_use(False)
                    
                    log("§cBOOM! §fAnchor exploded.")
                    debug_log("Anchor: Sequence complete")
                    self.last_anchor_time = time.time()
        except Exception as e:
            print(f"Anchor Error: {e}")
            debug_log(f"Anchor Error: {e}")
        finally:
            self.executing = False

class AutoCrystal:
    def __init__(self):
        self.active = False
        self.was_key_down = False
        self.last_crystal_time = 0
        self.last_explode_time = 0
        self.executing = False

    def run(self):
        if not SETTINGS["CRYSTAL_ENABLED"]: return
        
        # Input Logic
        key = SETTINGS.get("CRYSTAL_KEY", 67) # Default 'C'
        is_down = is_key_held(key)

        if SETTINGS.get("CRYSTAL_HOLD_MODE", False):
            # Hold Mode
            self.active = is_down
        else:
            # Toggle Mode
            if is_down and not self.was_key_down:
                self.active = not self.active
                log(f"§fAuto Crystal: {'§aON' if self.active else '§cOFF'}")
            self.was_key_down = is_down

        if not self.active: return

        # Logic
        if self.executing: return

        # Explode (High Priority)
        if is_looking_at_entity("end_crystal"):
            # Removed delay for instant reaction
            self.executing = True
            debug_log("Crystal: Detected crystal, exploding")
            threading.Thread(target=self.explode_sequence).start()
        
        # Place (Low Priority)
        elif is_looking_at_block("obsidian"):
            self.executing = True
            debug_log("Crystal: Detected obsidian, placing")
            threading.Thread(target=self.place_sequence).start()

    def place_sequence(self):
        try:
            crystal_slot = find_hotbar_slot("end_crystal")
            if crystal_slot is not None:
                debug_log(f"Crystal: Placing from slot {crystal_slot}")
                minescript.player_inventory_select_slot(crystal_slot)
                
                minescript.player_press_use(True)
                minescript.player_press_use(False)
                
                log("§aPlaced Crystal")
                self.last_crystal_time = time.time()
        except: pass
        finally:
            self.executing = False

    def explode_sequence(self):
        try:
            sword_slot = find_hotbar_slot("sword")
            if sword_slot is not None:
                debug_log(f"Crystal: Exploding with slot {sword_slot}")
                minescript.player_inventory_select_slot(sword_slot)
                
                minescript.player_press_attack(True)
                minescript.player_press_attack(False)
                
                log("§cExploded Crystal")
                self.last_explode_time = time.time()
        except: pass
        finally:
            self.executing = False


# ==========================================
#           MAIN LOOP
# ==========================================

class ESPManager:
    def __init__(self):
        self.was_key_down = False
        self.last_state = SETTINGS.get("ESP_ENABLED", False)

    def run(self):
        # Key Toggle
        key = SETTINGS.get("ESP_KEY")
        if key:
            is_down = is_key_held(key)
            if is_down and not self.was_key_down:
                new_state = not SETTINGS.get("ESP_ENABLED", False)
                SETTINGS["ESP_ENABLED"] = new_state
                log(f"§fESP: {'§aON' if new_state else '§cOFF'}")
                
                # Trigger Minescript execution if enabled
                if new_state:
                    minescript.execute(r"\flameclient\esp\main")
            self.was_key_down = is_down
        
        # Check for external state change (e.g. from menu)
        current_state = SETTINGS.get("ESP_ENABLED", False)
        if current_state != self.last_state:
            if current_state:
                minescript.execute(r"\flameclient\esp\main")
            self.last_state = current_state

def main():
    global SETTINGS
    log("§fCore Loaded!")
    
    # 1. Start ESP (Pyjinn Script)
    if SETTINGS["ESP_ENABLED"]:
        minescript.execute(r"\flameclient\esp\main")
        log("§fESP Started.")

    # 2. Initialize Features
    streamer_mode = StreamerMode()
    esp_manager = ESPManager()
    aimbot = Aimbot()
    silent_aimbot = SilentAimbot()
    triggerbot = Triggerbot()
    bridge = Bridge()
    anchor = AutoAnchor()
    crystal = AutoCrystal()
    attr_swap = AttributeSwap()

    # Menu State
    menu_visible = True
    was_rshift_down = False
    menu_state_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "menu_state.txt")
    
    # Initialize menu state file
    try:
        with open(menu_state_path, "w") as f:
            f.write("OPEN")
    except: pass

    log("§fFeatures Active.")

    # 3. Main Loop
    global CURRENT_SCREEN
    last_config_check = 0
    
    while True:
        try:
            # Reload Config every 1s
            if time.time() - last_config_check > 1.0:
                try:
                    import importlib
                    import flameclient.config
                    importlib.reload(flameclient.config)
                    from flameclient.config import SETTINGS
                    last_config_check = time.time()
                except: pass

            CURRENT_SCREEN = minescript.screen_name()
            
            streamer_mode.run()
            esp_manager.run()
            aimbot.run()
            silent_aimbot.run()
            triggerbot.run()
            bridge.run()
            anchor.run()
            crystal.run()
            attr_swap.run()
            
            time.sleep(0.01) # 100 ticks/sec roughly
        except Exception as e:
            log(f"§cError: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()
