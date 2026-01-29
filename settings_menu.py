import sys
import os
import pprint
import ctypes
import subprocess
from tkinter import font
import tkinter as tk

# Dependency Check
try:
    import customtkinter as ctk
except ImportError:
    import tkinter.messagebox
    root = tk.Tk()
    root.withdraw()
    tkinter.messagebox.showerror("Missing Dependency", 
        "Flame Client requires 'customtkinter'.\n\n"
        "Please install it by running:\n"
        "pip install customtkinter\n\n"
        "in your terminal or command prompt.")
    sys.exit(1)

# Add minescript root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
minescript_root = os.path.dirname(current_dir)
if minescript_root not in sys.path:
    sys.path.append(minescript_root)

from flameclient.config import SETTINGS, COLORS

# --- KEY MAPPING ---
VK_CODE_MAP = {
    1: "LBUTTON", 2: "RBUTTON", 4: "MBUTTON", 5: "XBUTTON1", 6: "XBUTTON2",
    8: "BACKSPACE", 9: "TAB", 13: "ENTER", 16: "SHIFT", 17: "CTRL", 18: "ALT",
    19: "PAUSE", 20: "CAPSLOCK", 27: "ESC", 32: "SPACE", 33: "PGUP", 34: "PGDN",
    35: "END", 36: "HOME", 37: "LEFT", 38: "UP", 39: "RIGHT", 40: "DOWN",
    44: "PRTSC", 45: "INSERT", 46: "DELETE",
    48: "0", 49: "1", 50: "2", 51: "3", 52: "4", 53: "5", 54: "6", 55: "7", 56: "8", 57: "9",
    65: "A", 66: "B", 67: "C", 68: "D", 69: "E", 70: "F", 71: "G", 72: "H", 73: "I",
    74: "J", 75: "K", 76: "L", 77: "M", 78: "N", 79: "O", 80: "P", 81: "Q", 82: "R",
    83: "S", 84: "T", 85: "U", 86: "V", 87: "W", 88: "X", 89: "Y", 90: "Z",
    91: "LWIN", 92: "RWIN", 93: "APPS",
    96: "NUM0", 97: "NUM1", 98: "NUM2", 99: "NUM3", 100: "NUM4", 101: "NUM5",
    102: "NUM6", 103: "NUM7", 104: "NUM8", 105: "NUM9",
    106: "NUM*", 107: "NUM+", 109: "NUM-", 110: "NUM.", 111: "NUM/",
    112: "F1", 113: "F2", 114: "F3", 115: "F4", 116: "F5", 117: "F6",
    118: "F7", 119: "F8", 120: "F9", 121: "F10", 122: "F11", 123: "F12",
    144: "NUMLOCK", 145: "SCROLL",
    160: "LSHIFT", 161: "RSHIFT", 162: "LCTRL", 163: "RCTRL", 164: "LALT", 165: "RALT",
    186: ";", 187: "=", 188: ",", 189: "-", 190: ".", 191: "/", 192: "`",
    219: "[", 220: "\\", 221: "]", 222: "'"
}

def get_key_name(vk_code):
    if vk_code is None: return "None"
    return VK_CODE_MAP.get(vk_code, f"Key_{vk_code}")

# --- THEME SETUP ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class ConsoleRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, text):
        self.text_widget.configure(state="normal")
        self.text_widget.insert("end", text)
        self.text_widget.see("end")
        self.text_widget.configure(state="disabled")

    def flush(self):
        pass

class BaseWindow(ctk.CTkToplevel):
    def __init__(self, parent, title, geometry):
        super().__init__(parent)
        self.title(title)
        self.geometry(geometry)
        self.attributes('-alpha', SETTINGS.get("MENU_OPACITY", 0.9))
        self.attributes('-topmost', True)
        self.protocol("WM_DELETE_WINDOW", self.withdraw) # Don't destroy, just hide
        self.refresh_callbacks = []
        
    def add_collapsible_section(self, parent, title):
        # Container for the whole section
        section_frame = ctk.CTkFrame(parent, fg_color="transparent")
        section_frame.pack(fill="x", pady=2)
        
        # Toggle Button
        is_expanded = tk.BooleanVar(value=False)
        
        content_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
        
        def toggle():
            if is_expanded.get():
                content_frame.pack_forget()
                is_expanded.set(False)
                btn.configure(text=f"▶ {title}")
            else:
                content_frame.pack(fill="x", padx=10, pady=5)
                is_expanded.set(True)
                btn.configure(text=f"▼ {title}")

        btn = ctk.CTkButton(section_frame, text=f"▶ {title}", 
                            font=("Nunito", 14, "bold"), 
                            fg_color="transparent", 
                            text_color="#55FFFF",
                            hover_color="#333333",
                            anchor="w",
                            command=toggle)
        btn.pack(fill="x")
        
        return content_frame

    def add_label(self, parent, text, text_color=None):
        label = ctk.CTkLabel(parent, text=text, font=("Nunito", 10), text_color=text_color)
        label.pack(anchor="w", pady=2)
        return label

    def add_switch(self, parent, text, setting_key):
        switch = ctk.CTkSwitch(parent, text=text, font=("Nunito", 12), command=lambda: self.master.update_setting(setting_key, switch.get()))
        if SETTINGS.get(setting_key):
            switch.select()
        switch.pack(pady=2, anchor="w")
        return switch

    def add_button(self, parent, text_func, command, color=None):
        btn = ctk.CTkButton(parent, text=text_func(), font=("Nunito", 12), height=28, command=None)
        
        def cmd_wrapper():
            command()
            self.master.refresh_all_ui()
        
        btn.configure(command=cmd_wrapper)
        if color:
            btn.configure(fg_color=color, hover_color="#444444")
        
        btn.pack(pady=3, fill="x")
        
        # Register for refresh
        self.refresh_callbacks.append(lambda: btn.configure(text=text_func()))
        return btn

    def add_slider(self, parent, text, setting_key, from_, to_, steps=None, is_int=False, warning_text=None, warning_color="#FF4444"):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(pady=5, fill="x")
        
        current_val = SETTINGS.get(setting_key, from_)
        label = ctk.CTkLabel(frame, text=f"{text}: {current_val}", font=("Nunito", 12))
        label.pack(anchor="w")
        
        if warning_text:
            lbl_warn = ctk.CTkLabel(frame, text=warning_text, text_color=warning_color, font=("Nunito", 10))
            lbl_warn.pack(anchor="w", padx=0, pady=(0, 2))

        def on_value(value):
            if is_int:
                value = int(value)
            else:
                value = round(value, 2)
            
            SETTINGS[setting_key] = value
            label.configure(text=f"{text}: {value}")
            
            # Auto-save config on slider change (Debounced)
            self.master.schedule_save()
            
            # Special case for opacity
            if setting_key == "MENU_OPACITY":
                self.master.update_opacity(value)
            
            # Special case for alpha colors
            if setting_key == "TEXT_ALPHA":
                 self.master.update_alpha_hex("TEXT_COLOR", value)
            if setting_key == "BOX_ALPHA":
                 self.master.update_alpha_hex("BOX_COLOR", value)

        slider = ctk.CTkSlider(frame, from_=from_, to=to_, number_of_steps=steps, command=on_value)
        slider.set(current_val)
        slider.pack(fill="x")
        
        return slider

    def add_combobox(self, parent, text, setting_key, values):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(pady=2, fill="x")
        
        label = ctk.CTkLabel(frame, text=text, font=("Nunito", 12))
        label.pack(side="left", padx=0)
        
        def callback(choice):
            SETTINGS[setting_key] = choice
            self.master.schedule_save()
            
        combo = ctk.CTkComboBox(frame, values=values, command=callback, width=120, height=24, font=("Nunito", 12))
        combo.set(SETTINGS.get(setting_key, values[0]))
        combo.pack(side="right", padx=0)
        
        return combo
        
    def refresh_ui(self):
        for cb in self.refresh_callbacks:
            cb()

class SettingsApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.withdraw() # Hide the root window
        self.title("Flame Client Manager")
        
        self.save_timer = None
        
        # Create Windows
        self.combat_window = BaseWindow(self, "Combat", "300x800")
        self.utility_window = BaseWindow(self, "Utility", "300x800")
        self.console_window = BaseWindow(self, "Console", "400x800")
        
        self.windows = [self.combat_window, self.utility_window, self.console_window]
        
        # Setup Content
        self.setup_combat()
        self.setup_utility()
        self.setup_console()
        
        # Position Windows
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        self.combat_window.geometry(f"+{screen_width//2 - 460}+{screen_height//2 - 400}")
        self.utility_window.geometry(f"+{screen_width//2 - 150}+{screen_height//2 - 400}")
        self.console_window.geometry(f"+{screen_width//2 + 160}+{screen_height//2 - 400}")

        # Input State
        self.was_rshift_down = False
        self.menu_visible = True
        self.last_read_state = None

        # Start Polling
        self.check_visibility()
        self.check_input()

    def check_input(self):
        try:
            # VK_RSHIFT = 0xA1
            is_rshift = (ctypes.windll.user32.GetAsyncKeyState(0xA1) & 0x8000) != 0
            
            if is_rshift and not self.was_rshift_down:
                self.toggle_menu()
            
            self.was_rshift_down = is_rshift
        except Exception as e:
            print(f"Input Error: {e}")
            
        self.after(50, self.check_input)

    def toggle_menu(self):
        self.menu_visible = not self.menu_visible
        state_str = "OPEN" if self.menu_visible else "CLOSED"
        
        try:
            state_file = os.path.join(current_dir, "menu_state.txt")
            with open(state_file, "w") as f:
                f.write(state_str)
            print(f"Menu Toggled: {state_str}")
        except Exception as e:
            print(f"Error writing state: {e}")

    def setup_combat(self):
        # ESP
        content_esp = self.combat_window.add_collapsible_section(self.combat_window, "ESP")
        self.setup_esp_section(content_esp, self.combat_window)
        
        # Aimbot
        content_aim = self.combat_window.add_collapsible_section(self.combat_window, "AIMBOT")
        self.setup_aimbot_section(content_aim, self.combat_window)

        # Silent Aimbot
        content_silent = self.combat_window.add_collapsible_section(self.combat_window, "SILENT AIMBOT")
        self.setup_silent_aimbot_section(content_silent, self.combat_window)

        # Triggerbot
        content_trigger = self.combat_window.add_collapsible_section(self.combat_window, "TRIGGERBOT")
        self.setup_triggerbot_section(content_trigger, self.combat_window)

        # Auto Anchor
        content_anchor = self.combat_window.add_collapsible_section(self.combat_window, "AUTO ANCHOR")
        self.setup_anchor_section(content_anchor, self.combat_window)

        # Auto Crystal
        content_crystal = self.combat_window.add_collapsible_section(self.combat_window, "AUTO CRYSTAL")
        self.setup_crystal_section(content_crystal, self.combat_window)

    def setup_utility(self, parent=None, window=None):
        # Bridging
        content_bridge = self.utility_window.add_collapsible_section(self.utility_window, "AUTO BRIDGING")
        self.setup_bridging_section(content_bridge, self.utility_window)

        # Attribute Swap
        content_swap = self.utility_window.add_collapsible_section(self.utility_window, "ATTRIBUTE SWAP")
        self.setup_attribute_swap_section(content_swap, self.utility_window)

        # Menu Settings
        content_menu = self.utility_window.add_collapsible_section(self.utility_window, "MENU SETTINGS")
        self.setup_menu_section(content_menu, self.utility_window)

    def setup_console(self):
        self.console_textbox = ctk.CTkTextbox(self.console_window, font=("Consolas", 12))
        self.console_textbox.pack(expand=True, fill="both", padx=5, pady=5)
        self.console_textbox.configure(state="disabled")
        
        sys.stdout = ConsoleRedirector(self.console_textbox)
        print("Flame Client Console Initialized...")
        
        btn_jobs = ctk.CTkButton(self.console_window, text="Reload Minescript Jobs", command=self.reload_jobs, height=40, font=("Nunito", 14, "bold"), fg_color="#2CC985", hover_color="#229E68")
        btn_jobs.pack(fill="x", padx=10, pady=10)

        btn_reload = ctk.CTkButton(self.console_window, text="Reload Config", command=self.reload_config, height=40, font=("Nunito", 14, "bold"), fg_color="#FFA500", hover_color="#CC8400")
        btn_reload.pack(fill="x", padx=10, pady=(0, 10))

        btn_exit = ctk.CTkButton(self.console_window, text="Exit Client", command=self.exit_app, height=40, font=("Nunito", 14, "bold"), fg_color="#FF4444", hover_color="#CC0000")
        btn_exit.pack(fill="x", padx=10, pady=(0, 10))
        
        self.last_log_size = 0
        self.check_log_updates()

    def check_log_updates(self):
        try:
            log_path = os.path.join(current_dir, "latest.log")
            if os.path.exists(log_path):
                current_size = os.path.getsize(log_path)
                if current_size > self.last_log_size:
                    with open(log_path, "r") as f:
                        f.seek(self.last_log_size)
                        new_content = f.read()
                        self.last_log_size = current_size
                        
                        self.console_textbox.configure(state="normal")
                        self.console_textbox.insert("end", new_content)
                        self.console_textbox.see("end")
                        self.console_textbox.configure(state="disabled")

                        # Auto Reload Checks
                        if SETTINGS.get("AUTO_RELOAD_ON_SERVER_SWITCH", False):
                            if "[Render thread/INFO]: Connecting to" in new_content or "Connecting to" in new_content:
                                print("Detected server switch, triggering reload sequence in 5s...")
                                self.after(5000, self.reload_jobs)

                elif current_size < self.last_log_size:
                     # File was truncated/reset
                     self.last_log_size = 0
        except Exception as e:
            print(f"Log Error: {e}")
            
        self.after(500, self.check_log_updates)

    def check_visibility(self):
        try:
            state_file = os.path.join(current_dir, "menu_state.txt")
            if os.path.exists(state_file):
                with open(state_file, "r") as f:
                    state = f.read().strip()
                
                if state != self.last_read_state:
                    self.last_read_state = state
                    if state == "OPEN":
                        for win in self.windows:
                            win.deiconify()
                    else:
                        for win in self.windows:
                            win.withdraw()
        except Exception as e:
            print(f"Error checking visibility: {e}")
            
        self.after(200, self.check_visibility)

    def update_opacity(self, value):
        for win in self.windows:
            win.attributes('-alpha', value)

    def refresh_all_ui(self):
        for win in self.windows:
            win.refresh_ui()

    # --- SECTIONS ---

    def setup_esp_section(self, parent, window):
        window.add_button(parent, lambda: self.get_key_text("ESP_KEY", "ESP Key"), lambda: self.update_keybind("ESP_KEY"))
        window.add_switch(parent, "Enable Module", "ESP_ENABLED")
        window.add_switch(parent, "Boxes", "SHOW_BOX")
        window.add_switch(parent, "Health", "SHOW_HEALTH")
        window.add_switch(parent, "Nametags", "SHOW_NAME")
        window.add_switch(parent, "Item", "SHOW_WEAPON")
        
        window.add_slider(parent, "Text Scale", "TEXT_SCALE", 0.1, 3.0, steps=29)
        window.add_slider(parent, "Min Dist", "MIN_DISTANCE_NAME", 0, 100, steps=100, is_int=True)
        
        window.add_button(parent, lambda: f"Text Color", lambda: self.update_color("TEXT_COLOR"), color="#333333")
        window.add_slider(parent, "Text Alpha", "TEXT_ALPHA", 0, 100, steps=100, is_int=True)
        
        window.add_button(parent, lambda: "Box Color", lambda: self.update_color("BOX_COLOR"), color="#333333")
        window.add_slider(parent, "Box Alpha", "BOX_ALPHA", 0, 100, steps=100, is_int=True)

    def setup_aimbot_section(self, parent, window):
        window.add_button(parent, lambda: self.get_key_text("AIMBOT_KEY", "Aimbot Key"), lambda: self.update_keybind("AIMBOT_KEY"))
        
        # Keybinds for sub-features (Moved to top)
        window.add_button(parent, lambda: self.get_key_text("AIMBOT_ATTACK_KEY", "Auto-Attack Key"), lambda: self.update_keybind("AIMBOT_ATTACK_KEY"))
        
        window.add_switch(parent, "Enable Module", "AIMBOT_ENABLED")
        
        window.add_combobox(parent, "Mode", "AIMBOT_MODE", ["1.21", "1.8"])
        window.add_slider(parent, "CPS (1.8 Only)", "AIMBOT_CPS", 1, 20, steps=19, is_int=True)
        
        window.add_switch(parent, "Target Mode (ON=Closest, OFF=Lock)", "AIMBOT_TARGET_MODE")
        
        # Sub-features
        window.add_switch(parent, "Auto Attack", "AIMBOT_ATTACK_ENABLED")
        window.add_switch(parent, "W-Tap", "AIMBOT_WTAP_ENABLED")
        window.add_switch(parent, "Strafe", "AIMBOT_STRAFE_ENABLED")
        
        window.add_slider(parent, "W-Tap Delay", "AIMBOT_WTAP_DELAY", 0.0, 1.0, steps=20)
        window.add_slider(parent, "Intensity", "AIMBOT_INTENSITY", 0.1, 5.0, steps=49)
        
        window.add_slider(parent, "Min Dist", "AIMBOT_MIN_DIST", 0.0, 5.0, steps=50)
        window.add_slider(parent, "Aim Randomness", "AIMBOT_RANDOMNESS", 0.0, 30.0, steps=300)
        window.add_slider(parent, "Timing Randomness", "AIMBOT_TIMING_RANDOMNESS", 0.0, 0.2, steps=20)

    def setup_silent_aimbot_section(self, parent, window):
        window.add_button(parent, lambda: self.get_key_text("SILENT_AIMBOT_KEY", "Silent Aim Key"), lambda: self.update_keybind("SILENT_AIMBOT_KEY"))
        window.add_switch(parent, "Enable Module", "SILENT_AIMBOT_ENABLED")
        window.add_label(parent, "Uses Aimbot Min Dist & Randomness settings", text_color="#AAAAAA")

    def setup_triggerbot_section(self, parent, window):
        window.add_button(parent, lambda: self.get_key_text("TRIGGERBOT_KEY", "Trigger Key"), lambda: self.update_keybind("TRIGGERBOT_KEY"))
        window.add_switch(parent, "Enable Module", "TRIGGERBOT_ENABLED")
        window.add_switch(parent, "1.8 Mode", "TRIGGERBOT_1_8_MODE")
        window.add_switch(parent, "Axe Mode (Modern)", "TRIGGERBOT_AXE_MODE")
        window.add_slider(parent, "Reach", "TRIGGERBOT_REACH", 3.0, 6.0, steps=30)

    def setup_bridging_section(self, parent, window):
        window.add_button(parent, lambda: self.get_key_text("BRIDGE_KEY", "Speed Bridge Key"), lambda: self.update_keybind("BRIDGE_KEY"))
        window.add_switch(parent, "Enable Module", "BRIDGING_ENABLED")



    def setup_attribute_swap_section(self, parent, window):
        window.add_button(parent, lambda: self.get_key_text("ATTRIBUTE_SWAP_KEY", "Swap Key"), lambda: self.update_keybind("ATTRIBUTE_SWAP_KEY"))
        window.add_switch(parent, "Enable Module", "ATTRIBUTE_SWAP_ENABLED")

    def setup_anchor_section(self, parent, window):
        window.add_button(parent, lambda: self.get_key_text("ANCHOR_KEY", "Anchor Key"), lambda: self.update_keybind("ANCHOR_KEY"))
        window.add_switch(parent, "Enable Module", "ANCHOR_ENABLED")

    def setup_crystal_section(self, parent, window):
        window.add_button(parent, lambda: self.get_key_text("CRYSTAL_KEY", "Crystal Key"), lambda: self.update_keybind("CRYSTAL_KEY"))
        window.add_switch(parent, "Enable Module", "CRYSTAL_ENABLED")
        window.add_switch(parent, "Hold Mode", "CRYSTAL_HOLD_MODE")

    def setup_menu_section(self, parent, window):
        window.add_slider(parent, "Menu Opacity", "MENU_OPACITY", 0.2, 1.0, steps=80)
        window.add_switch(parent, "Debug Mode", "DEBUG_MODE")
        window.add_switch(parent, "Streamer Mode", "STREAMER_MODE")
        window.add_button(parent, lambda: self.get_key_text("STREAMER_MODE_KEY", "Streamer Mode Key"), lambda: self.update_keybind("STREAMER_MODE_KEY"))
        window.add_switch(parent, "Auto Reload on Join", "AUTO_RELOAD_ON_SERVER_SWITCH")

    # --- LOGIC ---

    def update_setting(self, key, value):
        SETTINGS[key] = value
        print(f"Set {key} to {value}")
        self.save_config()

    def get_key_text(self, key, label):
        code = SETTINGS.get(key)
        return f"{label}: {get_key_name(code)}"

    def update_keybind(self, key_setting):
        top = ctk.CTkToplevel(self)
        top.geometry("300x150")
        top.title("Bind Key")
        
        # Ensure it stays on top of the main window
        top.transient(self)
        top.attributes('-topmost', True)
        top.lift()
        top.grab_set()
        
        # Center on screen
        x = self.winfo_x() + (self.winfo_width() // 2) - 150
        y = self.winfo_y() + (self.winfo_height() // 2) - 75
        top.geometry(f"+{x}+{y}")
        
        lbl = ctk.CTkLabel(top, text=f"Press any key for {key_setting}...\nPress ESC to unbind.", font=("Nunito", 14))
        lbl.pack(expand=True)
        
        def on_key(event):
            if event.keysym == "Escape":
                SETTINGS[key_setting] = None
                print(f"Unbound {key_setting}")
            else:
                SETTINGS[key_setting] = event.keycode
                print(f"Bound {key_setting} to {event.keycode}")
            self.save_config()
            top.grab_release()
            top.destroy()
            self.refresh_all_ui()
            
        top.bind("<Key>", on_key)
        top.focus_force()

    def update_color(self, key):
        dialog = ctk.CTkInputDialog(text="Enter Hex Color (#RRGGBB):", title=key)
        val = dialog.get_input()
        if val and val.startswith("#"):
            # Preserve alpha if exists
            current = COLORS.get(key, "#FFFFFFFF")
            if len(current) == 9: # #AARRGGBB
                alpha = current[1:3]
                if len(val) == 7:
                    val = f"#{alpha}{val[1:]}"
            COLORS[key] = val
            print(f"Set {key} to {val}")
            self.save_config()

    def update_alpha_hex(self, color_key, alpha_val):
        alpha_int = int((alpha_val / 100.0) * 255)
        alpha_hex = f"{alpha_int:02X}"
        
        current = COLORS.get(color_key, "#FFFFFF")
        if current.startswith("#"):
            clean = current[1:]
            if len(clean) == 8: rgb = clean[2:]
            else: rgb = clean
            COLORS[color_key] = f"#{alpha_hex}{rgb}"
        self.save_config()

    def reload_config(self):
        try:
            config_path = os.path.join(current_dir, "config.py")
            with open(config_path, "r") as f:
                code = f.read()
            
            temp_scope = {}
            exec(code, temp_scope)
            
            if "SETTINGS" in temp_scope:
                SETTINGS.clear()
                SETTINGS.update(temp_scope["SETTINGS"])
            
            if "COLORS" in temp_scope:
                COLORS.clear()
                COLORS.update(temp_scope["COLORS"])
                
            print("Config reloaded from disk!")
            self.refresh_all_ui()
        except Exception as e:
            print(f"Error reloading config: {e}")

    def reload_jobs(self):
        print("Attempting to reload Minescript jobs...")
        try:
            # PowerShell script to focus Minecraft and type commands
            ps_script = """
            $wshell = New-Object -ComObject wscript.shell;
            $wshell.AppActivate('Minecraft');
            Start-Sleep -Milliseconds 100;
            $wshell.SendKeys('{ENTER}');
            Start-Sleep -Milliseconds 50;
            $wshell.SendKeys('\\killjob -1~');
            Start-Sleep -Milliseconds 100;
            $wshell.SendKeys('{ENTER}');
            Start-Sleep -Milliseconds 50;
            $wshell.SendKeys('\\flameclient\\watcher~');
            """
            subprocess.Popen(["powershell", "-Command", ps_script])
            print("Sent reload commands to Minecraft.")
        except Exception as e:
            print(f"Error sending commands: {e}")

    def exit_app(self):
        print("Exiting Flame Client Manager...")
        try:
            # PowerShell script to focus Minecraft and kill jobs
            ps_script = """
            $wshell = New-Object -ComObject wscript.shell;
            $wshell.AppActivate('Minecraft');
            Start-Sleep -Milliseconds 100;
            $wshell.SendKeys('{ENTER}');
            Start-Sleep -Milliseconds 50;
            $wshell.SendKeys('\\killjob -1~');
            """
            subprocess.Popen(["powershell", "-Command", ps_script])
            print("Sent killjob command to Minecraft.")
        except Exception as e:
            print(f"Error sending kill command: {e}")

        self.quit()
        sys.exit()

    def schedule_save(self):
        if self.save_timer:
            self.after_cancel(self.save_timer)
        self.save_timer = self.after(1000, self.save_config)

    def save_config(self):
        self.save_timer = None
        config_path = os.path.join(current_dir, "config.py")
        with open(config_path, "w") as f:
            f.write("# ==========================================\n")
            f.write("#           FLAME CLIENT CONFIGURATION\n")
            f.write("# ==========================================\n\n")
            f.write("COLORS = " + pprint.pformat(COLORS, indent=4) + "\n\n")
            f.write("SETTINGS = " + pprint.pformat(SETTINGS, indent=4) + "\n")
        print("Config saved!")

if __name__ == "__main__":
    app = SettingsApp()
    app.mainloop()
