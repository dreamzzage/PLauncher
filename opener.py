# -----------------------------------------
# SAFE IMPORTS & CONSTANTS
# -----------------------------------------

import os
import sys
import json
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox

# CustomTkinter (required)
import customtkinter as ctk

# Pillow (optional, not strictly required here but kept for future use)
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# windnd (optional drag & drop)
try:
    import windnd
    WINDND_AVAILABLE = True
except ImportError:
    WINDND_AVAILABLE = False

# -----------------------------------------
# CONFIG & THEME CONSTANTS
# -----------------------------------------

CONFIG_FILE = "launcher_programs.json"
THEME_FOLDER = "themes"
DARK_THEME_FILE = "dark.json"

DEFAULT_PROGRAMS = {}  # extend later if you want auto-detected defaults


# -----------------------------------------
# CONFIG HELPERS
# -----------------------------------------

def load_config():
    """Load launcher configuration from JSON file."""
    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # Corrupt or unreadable config → start fresh
        return {}


def save_config(data):
    """Save launcher configuration to JSON file."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        messagebox.showerror("Config Error", f"Failed to save config:\n{e}")


# -----------------------------------------
# PROGRAM DETECTION & LAUNCH
# -----------------------------------------

def detect_program(paths):
    """Return the first existing path from a list of candidate paths."""
    for p in paths:
        if os.path.exists(p):
            return p
    return None


def launch_program(path):
    """Launch a program at the given path."""
    if not path:
        return
    app_dir = os.path.dirname(path)
    try:
        subprocess.Popen([path], cwd=app_dir)
    except Exception as e:
        messagebox.showerror("Launch Error", f"Failed to launch:\n{path}\n\n{e}")


# -----------------------------------------
# STEAM SHORTCUT HANDLING
# -----------------------------------------

def try_resolve_steam_shortcut(path):
    """
    Basic handling for .url and .lnk Steam shortcuts.
    Currently only detects and informs the user.
    """
    lower = path.lower()

    if lower.endswith(".url"):
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            if "steam://rungameid/" in content:
                messagebox.showinfo(
                    "Steam Shortcut Detected",
                    "Steam .url shortcut detected.\n\n"
                    "Set the real EXE manually via 'Path'."
                )
                return None
        except Exception:
            # Ignore errors, just treat as unresolved
            pass

    if lower.endswith(".lnk"):
        messagebox.showinfo(
            "Steam Shortcut Detected",
            ".lnk shortcut detected.\n\n"
            "Resolving .lnk requires extra libraries.\n"
            "Set the real EXE manually."
        )
        return None

    return None


# -----------------------------------------
# THEME LOADING
# -----------------------------------------

def apply_json_theme(theme_path):
    """Apply a CustomTkinter JSON theme if it exists and is valid."""
    if not os.path.exists(theme_path):
        return
    try:
        with open(theme_path, "r", encoding="utf-8") as f:
            theme_dict = json.load(f)
        ctk.ThemeManager.theme = theme_dict
    except Exception as e:
        messagebox.showerror("Theme Error", f"Failed to load theme:\n{e}")


def init_theme():
    """
    Initialize appearance mode and attempt to load dark theme.
    This keeps theme logic in one place.
    """
    ctk.set_appearance_mode("dark")

    # Ensure theme folder exists (no crash if missing)
    if not os.path.isdir(THEME_FOLDER):
        return

    dark_theme_path = os.path.join(THEME_FOLDER, DARK_THEME_FILE)
    if os.path.exists(dark_theme_path):
        apply_json_theme(dark_theme_path)


# -----------------------------------------
# MAIN APPLICATION CLASS
# -----------------------------------------

class LauncherApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window basics
        self.title("PLauncher")
        self.geometry("900x600")
        self.minsize(700, 500)

        # Initialize theme
        init_theme()

        # Load and normalize program config
        self.programs = load_config()
        self._ensure_default_programs()

        # Checkbox state storage
        self.check_vars = {}

        # Build UI
        self._build_main_layout()
        self._build_bottom_buttons()
        self._setup_drag_and_drop()

    # -------------------------------------
    # CONFIG NORMALIZATION
    # -------------------------------------

    def _ensure_default_programs(self):
        """
        Ensure DEFAULT_PROGRAMS entries exist in config,
        auto-detecting paths where possible.
        """
        changed = False
        for name, paths in DEFAULT_PROGRAMS.items():
            if name not in self.programs:
                detected = detect_program(paths)
                self.programs[name] = detected if detected else ""
                changed = True

        if changed:
            save_config(self.programs)

    # -------------------------------------
    # UI BUILDING
    # -------------------------------------

    def _build_main_layout(self):
        """Create main frame and program list area."""
        self.main_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_frame.pack(fill="both", expand=True)
        self.main_frame.grid_rowconfigure(2, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Title
        title = ctk.CTkLabel(
            self.main_frame,
            text="PLauncher",
            font=("Segoe UI", 26, "bold")
        )
        title.grid(row=0, column=0, columnspan=2, pady=(15, 5), padx=20, sticky="w")

        # Theme info (locked to dark)
        theme_frame = ctk.CTkFrame(self.main_frame, corner_radius=12)
        theme_frame.grid(row=1, column=0, columnspan=2, pady=5, padx=20, sticky="ew")

        ctk.CTkLabel(
            theme_frame,
            text="Theme: Dark",
            font=("Segoe UI", 14)
        ).grid(row=0, column=0, padx=10, pady=10, sticky="w")

        # Program list container
        self.program_frame = ctk.CTkFrame(self.main_frame, corner_radius=15)
        self.program_frame.grid(
            row=2,
            column=0,
            columnspan=2,
            sticky="nsew",
            padx=20,
            pady=10
        )

        self.refresh_program_list()

    def _build_bottom_buttons(self):
        """Create bottom action buttons."""
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)

        lavender = "#A78BFA"
        lavender_hover = "#C4B5FD"

        launch_btn = ctk.CTkButton(
            btn_frame,
            text="Launch Selected",
            width=200,
            fg_color=lavender,
            hover_color=lavender_hover,
            command=self.launch_selected
        )
        launch_btn.grid(row=0, column=0, padx=10)

        add_btn = ctk.CTkButton(
            btn_frame,
            text="Add Program",
            width=160,
            fg_color=lavender,
            hover_color=lavender_hover,
            command=self.add_program
        )
        add_btn.grid(row=0, column=1, padx=10)

    def _setup_drag_and_drop(self):
        """Enable drag-and-drop if windnd is available."""
        if WINDND_AVAILABLE:
            try:
                windnd.hook_dropfiles(self, self.handle_drop)
            except Exception as e:
                print(f"Failed to enable drag & drop: {e}")
        else:
            print("windnd not available — drag & drop disabled")

    # -------------------------------------
    # PROGRAM LIST UI
    # -------------------------------------

    def refresh_program_list(self):
        """Rebuild the program list UI."""
        for widget in self.program_frame.winfo_children():
            widget.destroy()

        self.check_vars.clear()

        lavender = "#A78BFA"
        lavender_hover = "#C4B5FD"

        row = 0
        for name, path in self.programs.items():
            var = ctk.BooleanVar()
            self.check_vars[name] = var

            status = "FOUND" if (path and os.path.exists(path)) else "NOT FOUND"

            checkbox = ctk.CTkCheckBox(
                self.program_frame,
                text=f"{name}  ({status})",
                variable=var,
                font=("Segoe UI", 15),
                corner_radius=12
            )
            checkbox.grid(row=row, column=0, sticky="w", padx=10, pady=8)

            edit_btn = ctk.CTkButton(
                self.program_frame,
                text="Path",
                width=70,
                fg_color=lavender,
                hover_color=lavender_hover,
                command=lambda n=name: self.change_path(n)
            )
            edit_btn.grid(row=row, column=1, padx=10)

            del_btn = ctk.CTkButton(
                self.program_frame,
                text="X",
                width=40,
                fg_color="#aa4444",
                hover_color="#cc5555",
                command=lambda n=name: self.delete_program(n)
            )
            del_btn.grid(row=row, column=2, padx=10)

            row += 1

    # -------------------------------------
    # BUTTON ACTIONS
    # -------------------------------------

    def launch_selected(self):
        """Launch all selected programs."""
        selected = [name for name, var in self.check_vars.items() if var.get()]

        if not selected:
            messagebox.showinfo("Nothing Selected", "Select at least one program.")
            return

        for name in selected:
            path = self.programs.get(name)
            if not path or not os.path.exists(path):
                messagebox.showerror("Error", f"{name} path is invalid.")
                continue
            launch_program(path)

        messagebox.showinfo("Done", "Programs launched.")

    def add_program(self):
        """Add a new program via file dialog."""
        file_path = filedialog.askopenfilename(
            title="Select Program",
            filetypes=[("Executable", "*.exe")]
        )
        if not file_path:
            return

        name = os.path.basename(file_path).replace(".exe", "")

        self.programs[name] = file_path
        save_config(self.programs)
        self.refresh_program_list()

    def change_path(self, name):
        """Change the path of an existing program."""
        file_path = filedialog.askopenfilename(
            title=f"Select new path for {name}",
            filetypes=[("Executable", "*.exe")]
        )
        if not file_path:
            return

        self.programs[name] = file_path
        save_config(self.programs)
        self.refresh_program_list()

    def delete_program(self, name):
        """Delete a program from the list (except defaults)."""
        if name in DEFAULT_PROGRAMS:
            messagebox.showwarning("Protected", "Default programs cannot be removed.")
            return

        if name in self.programs:
            del self.programs[name]
            save_config(self.programs)
            self.refresh_program_list()

    # -------------------------------------
    # DRAG-AND-DROP HANDLERS
    # -------------------------------------

    def handle_drop(self, files):
        """Handle dropped files/folders via windnd."""
        paths = [p.decode("utf-8") for p in files]

        for p in paths:
            p = p.strip()

            if os.path.isdir(p):
                self._add_exes_from_folder(p)
            elif p.lower().endswith(".exe"):
                self._add_exe_path(p)
            elif p.lower().endswith(".lnk") or p.lower().endswith(".url"):
                resolved = try_resolve_steam_shortcut(p)
                if resolved:
                    self._add_exe_path(resolved)
            else:
                messagebox.showinfo("Unsupported Drop", f"Unsupported file:\n{p}")

        self.refresh_program_list()

    def _add_exe_path(self, file_path):
        """Add a single EXE path to the config."""
        name = os.path.basename(file_path).replace(".exe", "")
        self.programs[name] = file_path
        save_config(self.programs)

    def _add_exes_from_folder(self, folder):
        """Recursively add all EXEs from a folder."""
        for root, dirs, files in os.walk(folder):
            for f in files:
                if f.lower().endswith(".exe"):
                    full = os.path.join(root, f)
                    name = os.path.basename(full).replace(".exe", "")
                    if name not in self.programs:
                        self.programs[name] = full
        save_config(self.programs)


# -----------------------------------------
# ENTRY POINT
# -----------------------------------------

if __name__ == "__main__":
    app = LauncherApp()
    app.mainloop()
