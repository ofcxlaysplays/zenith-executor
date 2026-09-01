import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
import os
import webbrowser
import requests
import subprocess
import threading
import time
import ctypes
from ctypes import wintypes

# ============================================================
# ⚙️ CONFIG
# ============================================================
CREATOR = "xlaysplays"
VERSION = "v2.0"
EXECUTOR_NAME = "ZENITH"
DLL_NAME = "windows_cache.dll"  # Your renamed DLL

# --- Colors ---
BG_DARK = "#0d0d0d"
BG_LIGHT = "#1a1a1a"
BG_MEDIUM = "#222222"
TEXT_COLOR = "#ffffff"
ACCENT_COLOR = "#00d4ff"  # Zenith blue
CORNER_RADIUS = 15

# ============================================================
# 🧩 DLL INJECTOR CLASS
# ============================================================
class ZenithInjector:
    def __init__(self, dll_path=DLL_NAME):
        self.dll_path = dll_path
        self.dll = None
        self.loaded = False
        self.attached = False
        
    def load_dll(self):
        """Load and initialize the DLL"""
        if not os.path.exists(self.dll_path):
            print(f"❌ DLL not found: {self.dll_path}")
            return False
        
        try:
            self.dll = ctypes.WinDLL(self.dll_path)
            
            # Set up function signatures
            self.dll.initialize.argtypes = []
            self.dll.initialize.restype = None
            
            self.dll.attach.argtypes = []
            self.dll.attach.restype = ctypes.c_int  # 0 = success
            
            self.dll.isAttached.argtypes = []
            self.dll.isAttached.restype = ctypes.c_int  # 1 = attached
            
            self.dll.execute.argtypes = [ctypes.c_char_p]
            self.dll.execute.restype = None
            
            # Initialize the API
            self.dll.initialize()
            self.loaded = True
            print("✅ DLL loaded successfully")
            
            # Try auto-attach
            self.auto_attach()
            return True
            
        except Exception as e:
            print(f"❌ DLL error: {e}")
            self.loaded = False
            return False
    
    def attach(self):
        """Inject into Roblox process"""
        if not self.loaded:
            print("❌ DLL not loaded")
            return False
        
        try:
            result = self.dll.attach()
            if result == 0:
                self.attached = True
                print("✅ Attached to Roblox!")
                return True
            else:
                self.attached = False
                print(f"❌ Attach failed (code: {result})")
                return False
        except Exception as e:
            print(f"❌ Attach error: {e}")
            self.attached = False
            return False
    
    def is_attached(self):
        """Check if currently attached to Roblox"""
        if not self.loaded or not self.dll:
            return False
        try:
            result = self.dll.isAttached()
            self.attached = (result == 1)
            return self.attached
        except:
            return False
    
    def execute(self, script):
        """Execute Lua script in Roblox"""
        if not self.loaded:
            print("❌ DLL not loaded")
            return False
        
        if not self.is_attached():
            print("⚠️ Not attached to Roblox")
            return False
        
        if not script or not script.strip():
            print("⚠️ Empty script")
            return False
        
        try:
            self.dll.execute(script.strip().encode('utf-8'))
            print("✅ Script executed")
            return True
        except Exception as e:
            print(f"❌ Execution error: {e}")
            return False
    
    def auto_attach(self):
        """Try to attach automatically if Roblox is running"""
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq RobloxPlayerBeta.exe'],
                capture_output=True,
                text=True,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if 'RobloxPlayerBeta.exe' in result.stdout:
                print("🔍 Roblox found, attempting auto-attach...")
                time.sleep(1)
                return self.attach()
        except:
            pass
        return False

# ============================================================
# 🎨 MAIN APPLICATION - ZENITH
# ============================================================
class ZenithApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # --- Window Settings ---
        self.title(f"{EXECUTOR_NAME} // {VERSION}")
        self.geometry("1100x700")
        self.minsize(900, 600)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        
        # --- Remove default title bar ---
        self.overrideredirect(True)
        
        # --- Bind window movement ---
        self.x = None
        self.y = None
        self.dragging = False
        
        # --- Apply rounded corners ---
        self.after(100, self.apply_rounded_corners)
        
        # --- Main Container ---
        self.main_frame = ctk.CTkFrame(self, fg_color=BG_DARK, corner_radius=CORNER_RADIUS)
        self.main_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        # --- Top Bar ---
        self.top_bar()
        
        # --- Content Area ---
        self.content_frame = ctk.CTkFrame(self.main_frame, fg_color=BG_DARK, corner_radius=0)
        self.content_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # --- Sidebar (Left) ---
        self.sidebar = ctk.CTkFrame(self.content_frame, width=200, fg_color=BG_LIGHT, corner_radius=10)
        self.sidebar.pack(side="left", fill="y", padx=(0, 10))
        self.sidebar.pack_propagate(False)
        self.sidebar.configure(width=200)
        
        # --- Main Content (Right) ---
        self.main_content = ctk.CTkFrame(self.content_frame, fg_color=BG_DARK, corner_radius=10)
        self.main_content.pack(side="right", fill="both", expand=True)
        
        # --- Sidebar Content ---
        self.sidebar_content()
        
        # --- Status Bar ---
        self.status_bar()
        
        # --- Tab System ---
        self.tabs = {}
        self.current_tab = None
        self.tab_counter = 0
        
        # --- Initialize Injector ---
        self.injector = ZenithInjector()
        if self.injector.load_dll():
            self.status_label.configure(text="✅ DLL loaded")
            if self.injector.attached:
                self.status_label.configure(text="✅ Auto-attached to Roblox")
                self.status_indicator.configure(text="🟢 Injected", text_color=ACCENT_COLOR)
        else:
            self.status_label.configure(text="⚠️ DLL not found. Place windows_cache.dll in the same folder.")
        
        # --- Show Editor First ---
        self.show_editor()
        
        # --- Start status updater ---
        self.update_status()
    
    # ============================================================
    # 🖥️ TOP BAR
    # ============================================================
    def top_bar(self):
        top_frame = ctk.CTkFrame(self.main_frame, height=45, fg_color=BG_LIGHT, corner_radius=0)
        top_frame.pack(fill="x", padx=0, pady=0)
        top_frame.pack_propagate(False)
        
        # Drag overlay
        drag_overlay = ctk.CTkFrame(top_frame, fg_color="transparent", height=45)
        drag_overlay.pack(fill="both", expand=True)
        drag_overlay.bind("<Button-1>", self.start_move)
        drag_overlay.bind("<B1-Motion>", self.on_move)
        drag_overlay.bind("<ButtonRelease-1>", self.stop_move)
        
        # Left: Logo + Title
        title_frame = ctk.CTkFrame(drag_overlay, fg_color="transparent", height=45)
        title_frame.pack(side="left", padx=15, pady=0)
        title_frame.pack_propagate(False)
        title_frame.bind("<Button-1>", self.start_move)
        title_frame.bind("<B1-Motion>", self.on_move)
        title_frame.bind("<ButtonRelease-1>", self.stop_move)
        
        icon_lbl = ctk.CTkLabel(title_frame, text="◆", 
                               font=("Segoe UI", 18, "bold"), 
                               text_color=ACCENT_COLOR)
        icon_lbl.pack(side="left", padx=(0, 8))
        icon_lbl.bind("<Button-1>", self.start_move)
        icon_lbl.bind("<B1-Motion>", self.on_move)
        icon_lbl.bind("<ButtonRelease-1>", self.stop_move)
        
        title_lbl = ctk.CTkLabel(title_frame, text=EXECUTOR_NAME, 
                    font=("Segoe UI", 15, "bold"), 
                    text_color=TEXT_COLOR)
        title_lbl.pack(side="left")
        title_lbl.bind("<Button-1>", self.start_move)
        title_lbl.bind("<B1-Motion>", self.on_move)
        title_lbl.bind("<ButtonRelease-1>", self.stop_move)
        
        ver_lbl = ctk.CTkLabel(title_frame, text=VERSION, 
                    font=("Segoe UI", 9), 
                    text_color="#666666")
        ver_lbl.pack(side="left", padx=(8, 0))
        ver_lbl.bind("<Button-1>", self.start_move)
        ver_lbl.bind("<B1-Motion>", self.on_move)
        ver_lbl.bind("<ButtonRelease-1>", self.stop_move)
        
        # Right: Window Controls
        controls = ctk.CTkFrame(drag_overlay, fg_color="transparent")
        controls.pack(side="right", padx=10, pady=0)
        
        ctk.CTkButton(controls, text="—", width=35, height=28, 
                     fg_color="transparent", hover_color="#333333",
                     font=("Segoe UI", 14, "bold"),
                     command=self.iconify).pack(side="left", padx=1)
        
        ctk.CTkButton(controls, text="☐", width=35, height=28,
                     fg_color="transparent", hover_color="#333333",
                     font=("Segoe UI", 12, "bold"),
                     command=self.toggle_maximize).pack(side="left", padx=1)
        
        ctk.CTkButton(controls, text="✕", width=35, height=28,
                     fg_color="transparent", hover_color="#cc0000",
                     font=("Segoe UI", 12, "bold"),
                     command=self.quit_app).pack(side="left", padx=1)
    
    def apply_rounded_corners(self):
        """Apply rounded corners to the window"""
        try:
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            if hwnd:
                DWM_WINDOW_CORNER_PREFERENCE = 33
                DWMWCP_ROUND = 2
                try:
                    ctypes.windll.dwmapi.DwmSetWindowAttribute(
                        hwnd,
                        DWM_WINDOW_CORNER_PREFERENCE,
                        ctypes.byref(ctypes.c_int(DWMWCP_ROUND)),
                        ctypes.sizeof(ctypes.c_int)
                    )
                except:
                    pass
        except:
            pass
    
    def start_move(self, event):
        self.dragging = True
        self.x = event.x_root
        self.y = event.y_root
    
    def on_move(self, event):
        if self.dragging and self.x is not None and self.y is not None:
            deltax = event.x_root - self.x
            deltay = event.y_root - self.y
            x = self.winfo_x() + deltax
            y = self.winfo_y() + deltay
            self.geometry(f"+{x}+{y}")
            self.x = event.x_root
            self.y = event.y_root
    
    def stop_move(self, event):
        self.dragging = False
    
    def toggle_maximize(self):
        if self.attributes("-fullscreen"):
            self.attributes("-fullscreen", False)
            self.geometry("1100x700")
        else:
            self.attributes("-fullscreen", True)
    
    def quit_app(self):
        if messagebox.askyesno(EXECUTOR_NAME, "Are you sure you want to exit?"):
            self.destroy()
    
    # ============================================================
    # 📂 SIDEBAR
    # ============================================================
    def sidebar_content(self):
        # Logo
        ctk.CTkLabel(self.sidebar, text=EXECUTOR_NAME, 
                    font=("Impact", 36), 
                    text_color=ACCENT_COLOR).pack(pady=(20, 5))
        
        ctk.CTkLabel(self.sidebar, text="EXECUTOR", 
                    font=("Segoe UI", 10, "bold"), 
                    text_color="#666666").pack(pady=(0, 20))
        
        # Sidebar Buttons
        buttons = [
            ("📄 Editor", self.show_editor),
            ("📁 Saved Scripts", self.show_saved),
            ("☁️ Script Hub", self.show_hub),
            ("🛠️ Tools", self.show_tools),
            ("⚙️ Settings", self.show_settings),
        ]
        
        for text, cmd in buttons:
            btn = ctk.CTkButton(self.sidebar, text=text, 
                              fg_color="transparent", 
                              hover_color=BG_MEDIUM,
                              text_color="#cccccc",
                              anchor="w", height=40,
                              font=("Segoe UI", 12, "bold"),
                              command=cmd)
            btn.pack(fill="x", padx=15, pady=2)
        
        # Inject/Execute buttons (bottom)
        btn_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        btn_frame.pack(side="bottom", fill="x", padx=15, pady=20)
        
        ctk.CTkButton(btn_frame, text="INJECT", 
                     fg_color="#2a7a3a", hover_color="#3a9a4a",
                     height=35, command=self.inject_btn).pack(fill="x", pady=2)
        
        ctk.CTkButton(btn_frame, text="EXECUTE", 
                     fg_color=ACCENT_COLOR, text_color="black",
                     hover_color="#00e5ff", height=35,
                     command=self.execute_btn).pack(fill="x", pady=2)
        
        self.status_indicator = ctk.CTkLabel(self.sidebar, text="⏳ Detecting...", 
                                           font=("Segoe UI", 10), 
                                           text_color="#888888")
        self.status_indicator.pack(side="bottom", pady=10)
    
    # ============================================================
    # 📊 STATUS BAR
    # ============================================================
    def status_bar(self):
        self.status_bar_frame = ctk.CTkFrame(self.main_frame, height=25, 
                                            fg_color=BG_LIGHT, corner_radius=0)
        self.status_bar_frame.pack(side="bottom", fill="x")
        self.status_bar_frame.pack_propagate(False)
        
        self.status_label = ctk.CTkLabel(self.status_bar_frame, text="Ready", 
                                        font=("Segoe UI", 10), 
                                        text_color="#888888")
        self.status_label.pack(side="left", padx=10)
        
        self.pid_label = ctk.CTkLabel(self.status_bar_frame, text="Roblox: Not found", 
                                     font=("Segoe UI", 10), 
                                     text_color="#888888")
        self.pid_label.pack(side="right", padx=10)
    
    # ============================================================
    # 📄 EDITOR
    # ============================================================
    def show_editor(self):
        self.clear_main()
        
        # Tab bar
        tab_bar = ctk.CTkFrame(self.main_content, fg_color=BG_LIGHT, height=35, corner_radius=0)
        tab_bar.pack(fill="x", padx=0, pady=0)
        tab_bar.pack_propagate(False)
        
        # Tab container
        self.tab_container = ctk.CTkFrame(tab_bar, fg_color="transparent")
        self.tab_container.pack(side="left", fill="x", expand=True, padx=5)
        
        # + button
        ctk.CTkButton(tab_bar, text="+", width=30, height=25, 
                     fg_color="transparent", hover_color=BG_MEDIUM,
                     font=("Segoe UI", 16, "bold"),
                     command=self.new_tab).pack(side="right", padx=5)
        
        # Editor container
        self.editor_container = ctk.CTkFrame(self.main_content, fg_color=BG_DARK)
        self.editor_container.pack(fill="both", expand=True, padx=5, pady=5)
        
        # If no tabs, create one
        if not self.tabs:
            self.create_tab("Main")
        
        if self.tabs:
            self.switch_tab(list(self.tabs.keys())[0])
    
    def new_tab(self):
        self.tab_counter += 1
        name = f"Tab {self.tab_counter}"
        self.create_tab(name)
        self.switch_tab(name)
    
    def create_tab(self, name):
        """Create a new tab with editor and line numbers"""
        # Tab container frame
        tab_frame = ctk.CTkFrame(self.tab_container, fg_color="transparent")
        tab_frame.pack(side="left", padx=2)
        
        # Tab button
        tab_btn = ctk.CTkButton(tab_frame, text=name, 
                               fg_color="transparent", hover_color=BG_MEDIUM,
                               height=25, width=70,
                               font=("Segoe UI", 10))
        tab_btn.pack(side="left")
        
        # Close button
        close_btn = ctk.CTkButton(tab_frame, text="x", width=18, height=18,
                                 fg_color="transparent", hover_color="#cc0000",
                                 font=("Segoe UI", 8))
        close_btn.pack(side="left", padx=(2, 0))
        
        # Bind events
        def on_tab_click(n=name):
            self.switch_tab(n)
        tab_btn.configure(command=on_tab_click)
        
        def on_close(n=name):
            self.close_tab(n)
        close_btn.configure(command=on_close)
        
        # Editor frame
        editor_frame = ctk.CTkFrame(self.editor_container, fg_color=BG_DARK)
        editor_frame.pack(fill="both", expand=True)
        
        # Text editor with line numbers
        text_frame = tk.Frame(editor_frame, bg=BG_DARK)
        text_frame.pack(fill="both", expand=True)
        
        # Line numbers
        line_numbers = tk.Text(text_frame, width=4, padx=3, takefocus=0, 
                               border=0, background=BG_LIGHT, foreground="#555555",
                               font=("Consolas", 11))
        line_numbers.pack(side="left", fill="y")
        
        # Main editor
        editor = tk.Text(text_frame, wrap="word", font=("Consolas", 11),
                        bg=BG_DARK, fg=TEXT_COLOR, insertbackground=TEXT_COLOR,
                        border=0, highlightthickness=0, undo=True)
        editor.pack(side="right", fill="both", expand=True)
        
        # Bind line number updates
        def update_line_numbers(event=None):
            lines = editor.get("1.0", "end-1c").count('\n') + 1
            line_numbers.config(state="normal")
            line_numbers.delete("1.0", "end")
            line_numbers.insert("1.0", "\n".join(str(i) for i in range(1, lines + 1)))
            line_numbers.config(state="disabled")
        
        editor.bind("<KeyRelease>", update_line_numbers)
        editor.bind("<MouseWheel>", update_line_numbers)
        editor.bind("<ButtonRelease-1>", update_line_numbers)
        
        # Store tab data
        self.tabs[name] = {
            "frame": tab_frame,
            "button": tab_btn,
            "close": close_btn,
            "editor_frame": editor_frame,
            "editor": editor,
            "line_numbers": line_numbers,
            "text_frame": text_frame
        }
        
        # Initial line numbers
        update_line_numbers()
        
        # Insert default script for main tab
        if name == "Main":
            default = f'''-- {EXECUTOR_NAME} Editor
-- Join Discord: https://discord.gg/xxaVG4eUzU
-- Press EXECUTE to run your script

print("Hello from {EXECUTOR_NAME}!")
'''
            editor.insert("1.0", default)
            update_line_numbers()
        
        # Auto-switch to new tab
        self.switch_tab(name)
    
    def switch_tab(self, name):
        if name not in self.tabs:
            return
        
        # Hide all editor frames
        for tab_name, data in self.tabs.items():
            data["editor_frame"].pack_forget()
            data["button"].configure(fg_color="transparent")
        
        # Show selected tab
        self.tabs[name]["editor_frame"].pack(fill="both", expand=True)
        self.tabs[name]["button"].configure(fg_color=BG_MEDIUM)
        self.current_tab = name
        
        # Update status
        self.status_label.configure(text=f"Editing: {name}")
    
    def close_tab(self, name):
        if len(self.tabs) <= 1:
            self.status_label.configure(text="Cannot close last tab")
            return
        
        if name in self.tabs:
            # Destroy tab widgets
            self.tabs[name]["frame"].destroy()
            self.tabs[name]["editor_frame"].destroy()
            del self.tabs[name]
            
            # Switch to first available tab
            if self.current_tab == name:
                remaining = list(self.tabs.keys())
                if remaining:
                    self.switch_tab(remaining[0])
    
    # ============================================================
    # 💾 SAVED SCRIPTS
    # ============================================================
    def show_saved(self):
        self.clear_main()
        
        ctk.CTkLabel(self.main_content, text="📁 Saved Scripts", 
                    font=("Segoe UI", 20, "bold"), 
                    text_color=TEXT_COLOR).pack(pady=20)
        
        # Script list
        self.saved_frame = ctk.CTkScrollableFrame(self.main_content, fg_color=BG_DARK)
        self.saved_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.load_saved_scripts()
    
    def load_saved_scripts(self):
        for w in self.saved_frame.winfo_children():
            w.destroy()
        
        scripts_dir = os.path.join(os.getcwd(), "scripts")
        if not os.path.exists(scripts_dir):
            os.makedirs(scripts_dir)
        
        files = [f for f in os.listdir(scripts_dir) if f.endswith('.lua')]
        
        if not files:
            ctk.CTkLabel(self.saved_frame, text="No saved scripts found.", 
                        font=("Segoe UI", 14), text_color="#666666").pack(pady=20)
            return
        
        for filename in files:
            frame = ctk.CTkFrame(self.saved_frame, fg_color=BG_LIGHT, corner_radius=8)
            frame.pack(fill="x", pady=4)
            
            ctk.CTkLabel(frame, text=f"📜 {filename}", 
                        font=("Segoe UI", 12), 
                        text_color=TEXT_COLOR).pack(side="left", padx=15, pady=10)
            
            ctk.CTkButton(frame, text="Load", width=60, height=30,
                         fg_color=ACCENT_COLOR, text_color="black",
                         command=lambda f=filename: self.load_saved_script(f)).pack(side="right", padx=5)
            
            ctk.CTkButton(frame, text="✕", width=30, height=30,
                         fg_color="transparent", hover_color="#cc0000",
                         command=lambda f=filename: self.delete_saved_script(f)).pack(side="right", padx=5)
    
    def load_saved_script(self, filename):
        scripts_dir = os.path.join(os.getcwd(), "scripts")
        with open(os.path.join(scripts_dir, filename), "r") as f:
            content = f.read()
        
        self.show_editor()
        if self.current_tab and self.current_tab in self.tabs:
            self.tabs[self.current_tab]["editor"].delete("1.0", "end")
            self.tabs[self.current_tab]["editor"].insert("1.0", content)
            self.status_label.configure(text=f"Loaded: {filename}")
    
    def delete_saved_script(self, filename):
        if messagebox.askyesno(EXECUTOR_NAME, f"Delete {filename}?"):
            scripts_dir = os.path.join(os.getcwd(), "scripts")
            os.remove(os.path.join(scripts_dir, filename))
            self.load_saved_scripts()
            self.status_label.configure(text=f"Deleted: {filename}")
    
    # ============================================================
    # ☁️ SCRIPT HUB
    # ============================================================
    def show_hub(self):
        self.clear_main()
        
        ctk.CTkLabel(self.main_content, text="☁️ Script Hub", 
                    font=("Segoe UI", 20, "bold"), 
                    text_color=TEXT_COLOR).pack(pady=20)
        
        search_frame = ctk.CTkFrame(self.main_content, fg_color="transparent")
        search_frame.pack(fill="x", padx=20, pady=10)
        
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Search scripts...", 
                                        height=40, font=("Segoe UI", 12))
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        ctk.CTkButton(search_frame, text="🔍 Search", 
                     fg_color=ACCENT_COLOR, text_color="black",
                     command=self.search_hub).pack(side="right")
        
        self.hub_frame = ctk.CTkScrollableFrame(self.main_content, fg_color=BG_DARK)
        self.hub_frame.pack(fill="both", expand=True, padx=20, pady=10)
    
    def search_hub(self):
        query = self.search_entry.get()
        if not query:
            return
        
        for w in self.hub_frame.winfo_children():
            w.destroy()
        
        self.status_label.configure(text=f"Searching: {query}")
        
        try:
            resp = requests.get(
                f"https://scriptblox.com/api/script/search?q={query}&max=15",
                timeout=10
            )
            data = resp.json()
            
            for script in data.get('result', {}).get('scripts', []):
                frame = ctk.CTkFrame(self.hub_frame, fg_color=BG_LIGHT, corner_radius=8)
                frame.pack(fill="x", pady=4)
                
                title = script.get('title', 'Untitled')[:50]
                ctk.CTkLabel(frame, text=title, 
                            font=("Segoe UI", 12, "bold"), 
                            text_color=TEXT_COLOR).pack(side="left", padx=15, pady=10)
                
                slug = script.get('slug', '')
                ctk.CTkButton(frame, text="Load", width=60, height=30,
                             fg_color=ACCENT_COLOR, text_color="black",
                             command=lambda s=slug: self.load_hub_script(s)).pack(side="right", padx=5)
            
            self.status_label.configure(text=f"Found {len(data.get('result', {}).get('scripts', []))} scripts")
            
        except Exception as e:
            self.status_label.configure(text=f"Search error: {e}")
            ctk.CTkLabel(self.hub_frame, text="Search failed. Try again.", 
                        font=("Segoe UI", 14), text_color="#ff4444").pack(pady=20)
    
    def load_hub_script(self, slug):
        try:
            resp = requests.get(f"https://scriptblox.com/api/script/{slug}", timeout=10)
            data = resp.json()
            script_data = data.get('result', {}).get('script', {})
            code = script_data.get('script') or script_data.get('rawScript') or script_data.get('source')
            
            if code:
                self.show_editor()
                if self.current_tab and self.current_tab in self.tabs:
                    self.tabs[self.current_tab]["editor"].delete("1.0", "end")
                    self.tabs[self.current_tab]["editor"].insert("1.0", code)
                    self.status_label.configure(text=f"Loaded: {slug}")
            else:
                self.status_label.configure(text="No script content found")
        except Exception as e:
            self.status_label.configure(text=f"Load error: {e}")
    
    # ============================================================
    # 🛠️ TOOLS
    # ============================================================
    def show_tools(self):
        self.clear_main()
        
        ctk.CTkLabel(self.main_content, text="🛠️ Tools", 
                    font=("Segoe UI", 20, "bold"), 
                    text_color=TEXT_COLOR).pack(pady=20)
        
        tools_frame = ctk.CTkFrame(self.main_content, fg_color=BG_DARK)
        tools_frame.pack(fill="both", expand=True, padx=30, pady=10)
        
        tools = [
            ("📋 Infinite Yield", "loadstring(game:HttpGet('https://raw.githubusercontent.com/EdgeIY/infiniteyield/master/source'))()"),
            ("🔍 Dex Explorer", "loadstring(game:HttpGet('https://raw.githubusercontent.com/infyiff/backup/main/dex.lua'))()"),
            ("🔧 VG Hub", "loadstring(game:HttpGet('https://raw.githubusercontent.com/1201nelson/V.G-Hub/main/V.G-Hub'))()"),
            ("🎯 AimBot", "loadstring(game:HttpGet('https://raw.githubusercontent.com/your-aimbot/main/aimbot.lua'))()"),
            ("🔄 Anti-AFK", "loadstring(game:HttpGet('https://raw.githubusercontent.com/anti-afk/main/afk.lua'))()"),
        ]
        
        for name, code in tools:
            frame = ctk.CTkFrame(tools_frame, fg_color=BG_LIGHT, corner_radius=8)
            frame.pack(fill="x", pady=4)
            
            ctk.CTkLabel(frame, text=name, 
                        font=("Segoe UI", 12), 
                        text_color=TEXT_COLOR).pack(side="left", padx=15, pady=10)
            
            ctk.CTkButton(frame, text="▶ Execute", width=80, height=30,
                         fg_color=ACCENT_COLOR, text_color="black",
                         command=lambda c=code: self.execute_tool(c)).pack(side="right", padx=5)
    
    def execute_tool(self, code):
        if self.injector.execute(code):
            self.status_label.configure(text="✅ Tool executed!")
        else:
            self.status_label.configure(text="❌ Execution failed")
    
    # ============================================================
    # ⚙️ SETTINGS
    # ============================================================
    def show_settings(self):
        self.clear_main()
        
        ctk.CTkLabel(self.main_content, text="⚙️ Settings", 
                    font=("Segoe UI", 20, "bold"), 
                    text_color=TEXT_COLOR).pack(pady=20)
        
        settings_frame = ctk.CTkFrame(self.main_content, fg_color=BG_DARK)
        settings_frame.pack(fill="both", expand=True, padx=30, pady=10)
        
        # Theme
        ctk.CTkLabel(settings_frame, text="Theme", 
                    font=("Segoe UI", 14), 
                    text_color=TEXT_COLOR).pack(anchor="w", pady=5)
        
        theme_var = ctk.StringVar(value="Dark")
        ctk.CTkComboBox(settings_frame, values=["Dark", "Light"], 
                       variable=theme_var,
                       command=self.change_theme).pack(anchor="w", pady=5)
        
        ctk.CTkLabel(settings_frame, text="", height=10).pack()
        
        # Always on Top
        ctk.CTkSwitch(settings_frame, text="Always on Top", 
                     command=self.toggle_ontop).pack(anchor="w", pady=5)
        
        ctk.CTkLabel(settings_frame, text="", height=10).pack()
        
        # Buttons
        ctk.CTkButton(settings_frame, text="🗑️ Clear Logs", 
                     fg_color="#444444", hover_color="#555555",
                     command=self.clear_logs).pack(anchor="w", pady=3)
        
        ctk.CTkButton(settings_frame, text="💀 Kill Roblox", 
                     fg_color="#882222", hover_color="#aa3333",
                     command=self.kill_roblox).pack(anchor="w", pady=3)
        
        ctk.CTkButton(settings_frame, text="🔄 Flush RAM", 
                     fg_color="#444444", hover_color="#555555",
                     command=self.flush_ram).pack(anchor="w", pady=3)
    
    def change_theme(self, choice):
        if choice == "Light":
            ctk.set_appearance_mode("light")
        else:
            ctk.set_appearance_mode("dark")
    
    def toggle_ontop(self):
        self.attributes("-topmost", not self.attributes("-topmost"))
    
    def clear_logs(self):
        self.status_label.configure(text="Logs cleared")
    
    def kill_roblox(self):
        if messagebox.askyesno(EXECUTOR_NAME, "Kill all Roblox processes?"):
            os.system("taskkill /F /IM RobloxPlayerBeta.exe")
            self.status_label.configure(text="💀 Roblox killed")
    
    def flush_ram(self):
        try:
            ctypes.windll.psapi.EmptyWorkingSet(ctypes.windll.kernel32.GetCurrentProcess())
            self.status_label.configure(text="🔄 RAM flushed")
        except:
            pass
    
    # ============================================================
    # ?? CORE FUNCTIONS
    # ============================================================
    def clear_main(self):
        for widget in self.main_content.winfo_children():
            widget.destroy()
    
    def inject_btn(self):
        """Handle INJECT button click"""
        if self.injector.attach():
            self.status_label.configure(text="✅ Injected successfully!")
            self.status_indicator.configure(text="🟢 Injected", text_color=ACCENT_COLOR)
        else:
            self.status_label.configure(text="❌ Injection failed. Is Roblox running?")
            self.status_indicator.configure(text="🔴 Not injected", text_color="#ff4444")
    
    def execute_btn(self):
        """Handle EXECUTE button click"""
        if not self.current_tab or self.current_tab not in self.tabs:
            self.status_label.configure(text="⚠️ No active tab")
            return
        
        editor = self.tabs[self.current_tab]["editor"]
        code = editor.get("1.0", "end-1c")
        
        if not code.strip():
            self.status_label.configure(text="⚠️ No script to execute")
            return
        
        if self.injector.execute(code):
            self.status_label.configure(text="✅ Script executed successfully!")
        else:
            self.status_label.configure(text="❌ Execution failed. Is Roblox injected?")
    
    def update_status(self):
        """Update Roblox status in status bar - runs silently"""
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq RobloxPlayerBeta.exe'],
                capture_output=True,
                text=True,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if 'RobloxPlayerBeta.exe' in result.stdout:
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'RobloxPlayerBeta.exe' in line:
                        parts = line.split()
                        if len(parts) > 1:
                            pid = parts[1]
                            self.pid_label.configure(text=f"Roblox: PID {pid}")
                            if self.injector.is_attached():
                                self.status_indicator.configure(text="🟢 Injected", text_color=ACCENT_COLOR)
                            else:
                                self.status_indicator.configure(text="🔴 Detected", text_color="#ff4444")
                            break
            else:
                self.pid_label.configure(text="Roblox: Not found")
                self.status_indicator.configure(text="⏳ Roblox not found", text_color="#888888")
        except:
            pass
        
        # Update every 3 seconds
        self.after(3000, self.update_status)

# ============================================================
# 🏃 RUN
# ============================================================
if __name__ == "__main__":
    app = ZenithApp()
    app.mainloop()