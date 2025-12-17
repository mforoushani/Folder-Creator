# =============================================================================
# Folder Creator — Research Group Structure (Code-only prefixes for section & subfolders)
# =============================================================================
# Features:
# - Two-column layout (requested order)
# - Scrollable window + mouse wheel
# - “Select all subfolders” per section
# - Option A: fixed sub-subfolders for specific subfolders
# - Validation: Folder Name (Code–Acronym) + Drive required; Year–Person optional but validated if filled
# - Create button styled (green) and centered
# - After success: ask Continue (reset form) or Exit
# - Mansour Ahmadi Foroushani  2024 Marburg, Germany 
# =============================================================================

# ============================= 01. IMPORTS ===================================
import sys
import re
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, Checkbutton, IntVar
from tkinter import ttk
BASE_DIR = Path(__file__).resolve().parent
print("SCRIPT LOCATION :", BASE_DIR)
print("CURRENT WORKDIR :", Path.cwd())
print("ICONS DIR TRY  :", BASE_DIR / "icons")
print("ICONS EXISTS? :", (BASE_DIR / "icons").exists())

# Optional: Pillow for icons (safe if missing)
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

def create_folder(path: Path):
    """Create a folder (and parents) with error handling."""
    try:
        path.mkdir(parents=True, exist_ok=True)
        print("Folder created:", path)
    except OSError as e:
        print(f"Error creating folder: {path}\n{e}")
        proceed = messagebox.askyesno("Error", f"Error creating folder:\n{path}\n{e}\n\nContinue?")
        if not proceed:
            sys.exit(1)


# =========================== 02. GENERIC HELPERS =============================
def load_icon(icon_path: Path, size=(20, 20)):
    if not icon_path.exists():
        print("❌ ICON NOT FOUND:", icon_path)
        return None

    if not PIL_AVAILABLE:
        print("⚠️ PIL not available, icon skipped:", icon_path.name)
        return None

    try:
        from PIL import Image
        resample = getattr(Image, "Resampling", Image).LANCZOS
        img = Image.open(icon_path)
        img = img.resize(size, resample)
        print("✅ ICON LOADED:", icon_path.name)
        return ImageTk.PhotoImage(img)
    except Exception as e:
        print("❌ ICON LOAD ERROR:", icon_path.name, e)
        return None


class Tooltip:
    """Simple tooltip with optional icon."""
    def __init__(self, widget, text, icon=None):
        self.widget = widget
        self.text = text
        self.icon = icon
        self.tw = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, _event=None):
        if self.tw:
            return
        x = self.widget.winfo_pointerx() + 15
        y = self.widget.winfo_pointery() + 15
        self.tw = tk.Toplevel(self.widget)
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry(f"+{x}+{y}")
        self.tw.configure(bg="yellow")

        frame = tk.Frame(self.tw, bg="yellow")
        frame.pack(padx=5, pady=5)

        if self.icon is not None:
            tk.Label(frame, image=self.icon, bg="yellow").pack(side="left", padx=(0, 6))

        tk.Label(
            frame, text=self.text, justify="left",
            bg="yellow", relief="flat", wraplength=260
        ).pack(side="left")

    def hide(self, _event=None):
        if self.tw:
            self.tw.destroy()
            self.tw = None

# ========================= 03. SCROLLABLE CONTAINER ==========================
class ScrollableFrame(ttk.Frame):
    """A vertically scrollable frame."""
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)

        self.vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.frame = ttk.Frame(self.canvas)
        self.window_id = self.canvas.create_window((0, 0), window=self.frame, anchor="nw")

        self.frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # Mouse wheel
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel_linux)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel_linux)

    def _on_frame_configure(self, _event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.window_id, width=event.width)

    def _on_mousewheel(self, event):
        delta = int(-1 * (event.delta / 120))
        self.canvas.yview_scroll(delta, "units")

    def _on_mousewheel_linux(self, event):
        if event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")
   
# ======================== 04. MAIN APPLICATION CLASS =========================
class FolderCreatorApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Folder Creator — Research Group Structure")
        self.root.configure(bg="#f0f0f0")
        self.root.minsize(800, 560)

        self.style = ttk.Style(root)
        self.style.configure("BoldLabel.TLabel", font=("Arial", 11, "bold"))
        self._bulk_update = False

        # ---------- Icons ----------
        icons_dir = BASE_DIR /"icons"
        self.icon_name = load_icon(icons_dir / "info_icon_name.png")
        self.icon_project = load_icon(icons_dir / "info_icon_project.png")
        self.icon_drive = load_icon(icons_dir / "info_icon_drive.png")

        # ---------- Folder tree ----------
        self.tree = {
            "Intro & Documentation": [
                "General Info", "Project Proposal", "Go-to Person", "Fieldwork Site",
                "Sample list 4 Lab-Team", "Material List", "Fieldwork Protocol-Planning-Permission",
                "Images", "Meetings",
            ],
            "Lab Measurements": [
                "TOC", "pH", "CN", "ICP-MS", "CFA", "Aqualog", "Raw Data Preparation", "Misc-Lab Data",
            ],
            "Field Measurements": [
                "Meteorology", "Hydrology", "Vegetation", "Soil",
            ],
            "Geodata": [
                "Coordinates", "Maps", "Satellite Images",
            ],
            "Finance & Administration": [
                "Approvals & Guidelines", "Expenditure Reports", "Account Overview", "Bank Statements",
                "Personnel-Assistants & Staff", "Contracts - Service & Transfer",
                "Travel Expense Reports", "Reimbursement Claims", "Purchase Orders",
            ],
            "Outcome": [
                "Master Files", "Presentations", "Publications", "Reports", "Logo", "Other Outputs",
            ],
        }

        # ---------- Option A: sub-subfolders ----------
        self.sub_sub_map = {
            "Finance & Administration": {
                "Personnel-Assistants & Staff": ["Personnel-Assistants", "Personnel-Staff"],
                "Contracts - Service & Transfer": ["Contracts-Service", "Contracts-Transfer"],
            },
            "Field Measurements": {
                "Meteorology": ["Meteorology Manual", "Meteorology Instrument"],
                "Hydrology": ["Hydrology Manual", "Hydrology Instrument"],
                "Vegetation": ["Vegetation Manual", "Vegetation Instrument"],
                "Soil": ["Soil Manual", "Soil Instrument"],
            },
        }

        # ---------- Layout order (2 cols) ----------
        self.layout_order = [
            ("Intro & Documentation", 0),
            ("Lab Measurements", 1),
            ("Field Measurements", 0),
            ("Geodata", 0),
            ("Finance & Administration", 1),
            ("Outcome", 0),
        ]

        # Build UI
        self._build_ui()

    # ====================== 05.Utilities ======================
    def _find_widget_for_var(self, var: IntVar, container: tk.Misc):
        for child in container.winfo_children():
            try:
                if isinstance(child, Checkbutton) and child.cget("variable") == str(var):
                    return child
            except Exception:
                pass
            res = self._find_widget_for_var(var, child)
            if res is not None:
                return res
        return None

    # ====================== 06.Build UI =======================
    def _build_ui(self):
        scroll = ScrollableFrame(self.root)
        scroll.pack(fill="both", expand=True)
        main = scroll.frame

        btn_name = tk.Button(main, image=self.icon_name, command=lambda: messagebox.showinfo("Meta Format", "Format: A-HYMO"))
        btn_name.image = self.icon_name
        btn_name.grid(row=0, column=2, padx=5)

        btn_meta = tk.Button(main, image=self.icon_project, command=lambda: messagebox.showinfo("Meta Format", "Format: 2026-Peter"))
        btn_meta.image = self.icon_project
        btn_meta.grid(row=1, column=2, padx=5)

        btn_drive = tk.Button(main, image=self.icon_drive, command=lambda: messagebox.showinfo("Drive Format", "Format: Drive Letter D, E, F"))
        btn_drive.image = self.icon_drive
        btn_drive.grid(row=2, column=2, padx=5)


        main.columnconfigure(0, weight=1, uniform="cols")
        main.columnconfigure(1, weight=1, uniform="cols")
        main.columnconfigure(2, weight=0)

        # Inputs
        ttk.Label(main, text="Code & Project Acronym (e.g., A-CABCAR):", style="BoldLabel.TLabel")\
            .grid(row=0, column=0, sticky="w", padx=8, pady=(10,6), columnspan=2)
        self.entry_name = ttk.Entry(main, width=40, font=("Arial", 11))
        self.entry_name.grid(row=0, column=1, padx=8, pady=(10,6), sticky="we")

        ttk.Label(main, text="Start Year-Person (e.g., 2025-Thomas):", style="BoldLabel.TLabel")\
            .grid(row=1, column=0, sticky="w", padx=8, pady=6, columnspan=2)
        self.entry_meta = ttk.Entry(main, width=40, font=("Arial", 11))
        self.entry_meta.grid(row=1, column=1, padx=8, pady=6, sticky="we")

        ttk.Label(main, text=r"Drive or Path (e.g., D, D:\work, \\server\share):", style="BoldLabel.TLabel")\
            .grid(row=2, column=0, sticky="w", padx=8, pady=6, columnspan=2)
        self.entry_drive = ttk.Entry(main, width=40, font=("Arial", 11))
        self.entry_drive.grid(row=2, column=1, padx=8, pady=6, sticky="we")

        # Sections
        start_row = 4
        col_rows = {0: start_row, 1: start_row}

        self.section_vars = {}
        self.sub_vars = {}
        self.select_all_vars = {}
        self.select_all_widgets = {}

        for section, col in self.layout_order:
            svar = IntVar(value=0)
            self.section_vars[section] = svar
            Checkbutton(main, text=section, variable=svar)\
                .grid(row=col_rows[col], column=col, sticky="w", padx=8, pady=(12, 2))
            col_rows[col] += 1

            sel_all_var = IntVar(value=0)
            self.select_all_vars[section] = sel_all_var
            sel_all_cb = Checkbutton(main, text="    Select all subfolders", variable=sel_all_var, state=tk.DISABLED)
            self.select_all_widgets[section] = sel_all_cb
            sel_all_cb.grid(row=col_rows[col], column=col, sticky="w", padx=22, pady=(0, 2))
            col_rows[col] += 1

            self.sub_vars[section] = []
            for sub in self.tree[section]:
                v = IntVar(value=0)
                self.sub_vars[section].append((sub, v))
                Checkbutton(main, text=f"    {sub}", variable=v, state=tk.DISABLED)\
                    .grid(row=col_rows[col], column=col, sticky="w", padx=22)
                col_rows[col] += 1

            # Traces
            def set_children_enabled(enabled, sect=section):
                self.select_all_widgets[sect].configure(state=(tk.NORMAL if enabled else tk.DISABLED))
                for _, v in self.sub_vars[sect]:
                    w = self._find_widget_for_var(v, main)
                    if w:
                        w.configure(state=(tk.NORMAL if enabled else tk.DISABLED))

            def update_select_all(sect=section):
                if self._bulk_update:
                    return
                all_on = all(v.get() == 1 for _, v in self.sub_vars[sect])
                if self.select_all_vars[sect].get() != int(all_on):
                    self._bulk_update = True
                    self.select_all_vars[sect].set(int(all_on))
                    self._bulk_update = False

            def toggle_all_children(to_value, sect=section):
                self._bulk_update = True
                for _, v in self.sub_vars[sect]:
                    v.set(to_value)
                self._bulk_update = False

            svar.trace_add("write", lambda *_a, s=section, sv=svar: set_children_enabled(bool(sv.get()), sect=s))
            self.select_all_vars[section].trace_add("write", lambda *_a, s=section: toggle_all_children(self.select_all_vars[s].get(), sect=s))
            for _, v in self.sub_vars[section]:
                v.trace_add("write", lambda *_a, s=section: update_select_all(sect=s))

        # Create button (styled, centered)
        bottom_row = max(col_rows.values()) + 2
        tk.Button(
            main, text="Create Folders", command=self.create_folders,
            bg="#4CAF50", fg="white", font=("Arial", 11, "bold"),
            padx=15, pady=6, relief="raised", bd=3, cursor="hand2"
        ).grid(row=bottom_row, column=0, columnspan=2, pady=20)

    # ====================== 07. Reset form ======================
    def reset_form(self):
        self.entry_name.delete(0, tk.END)
        self.entry_meta.delete(0, tk.END)
        # self.entry_drive.delete(0, tk.END)  # uncomment to clear drive too
        self.entry_name.focus_set()

        for section, svar in self.section_vars.items():
            svar.set(0)
        for section, subs in self.sub_vars.items():
            for _, v in subs:
                v.set(0)
        for section, selvar in self.select_all_vars.items():
            selvar.set(0)

    # ====================== 08. Create folders =================
    def create_folders(self):
        validated = self._validate_inputs()
        if not validated:
            return
        project_code, acronym, main_folder = validated

        # Derive Code from "Code–Acronym" (or accept just "Code")
        # code_label = name.split("-", 1)[0].strip() if name else ""

        if not messagebox.askyesno("Confirmation", f"Create folder tree under:\n{main_folder}\n\nProceed?"):
            return

        # Main (keeps full name)
        create_folder(main_folder)

        # Sections & subfolders (Code-only prefixes)
        for section, svar in self.section_vars.items():
            if not svar.get():
                continue

            # Section folder now uses Code only
            section_path = main_folder / f"{project_code}-{acronym} {section}"
            create_folder(section_path)

            for sub, v in self.sub_vars[section]:
                if not v.get():
                    continue

                # Subfolder uses Code only
                sub_path = section_path / f"{project_code}-{acronym} {sub}"
                create_folder(sub_path)

                # Option A: extra children (also prefixed with Code only)
                extra_children = self.sub_sub_map.get(section, {}).get(sub, [])
                for child in extra_children:
                    create_folder(sub_path / f"{project_code}-{acronym} {child}")

        messagebox.showinfo("Success", f"Folders created under:\n{main_folder}")
        do_more = messagebox.askyesno("Continue?", "Do you want to create another folder set?\n\nYes = Continue   |   No = Exit")
        if do_more:
            self.reset_form()
        else:
            self.root.destroy()

    # ====================== 09. Validation =====================
    def _validate_inputs(self):
        name = self.entry_name.get().strip()   # expects "Code–Acronym" (or just "Code")
        meta = self.entry_meta.get().strip()   # expects "YYYY-Person" (optional)
        drive = self.entry_drive.get().strip() # expects single letter only

    # ====================== 10. Required fields
        missing = []
        if not name:
            missing.append("Code & Project Acronym")
        if not meta:
            missing.append("Start Year & Person")
        if not drive:
            missing.append("Drive/Path")

        if missing:
            msg = (
                "The following required fields are empty:\n"
                f" - " + "\n - ".join(missing) +
                "\n\nDo you want to continue filling the form?\n"
                "Yes = keep editing   |   No = exit"
            )
            keep_editing = messagebox.askyesno("Incomplete form", msg)
            if keep_editing:
                if "Code & Project Acronym" in missing:
                    self.entry_name.focus_set()
                elif "Start Year & Person" in missing:
                    self.entry_meta.focus_set()     
                else:
                    self.entry_drive.focus_set()
                return None
            else:
                self.root.destroy()
                return None

        # ---------- Validate name: Code-Acronym ----------
        m_name = re.match(r"^([A-Za-z])\-([A-Za-z0-9][A-Za-z0-9\- _]*)$", name)
        if not m_name:
            messagebox.showerror("Invalid Name", "Name must be: Code-Acronym (e.g., A-CABCAR)")
            self.entry_name.focus_set()
            return None
        code = m_name.group(1).upper()
        acronym = m_name.group(2)

        # ---------- Validate meta if provided: must be YYYY-Person

        m_meta = re.match(r"^(\d{4})\-([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\s\-\.\']*)$", meta)
        if not m_meta:
            messagebox.showerror("Invalid format", "Start Year & Person must look like: 2025-Thomas")
            self.entry_meta.focus_set()
            return None
        year = m_meta.group(1)
        person = m_meta.group(2).strip()

        # ---------- Validate drive: single letter A-Z ----------
        if not re.fullmatch(r"^[A-Za-z]$", drive):
            messagebox.showerror("Invalid Drive", "Drive must be ONE letter (A–Z), e.g., F")
            self.entry_drive.focus_set()
            return None

        base = Path(drive.upper() + ":/")

# =========================== 11.  Build main folder name: CodeYY-Acronym-YYYY-Person =================
        yy = year[-2:]  # 2026 -> 26
        project_code = f"{code}{yy}"  # A26
        main_folder_name = f"{project_code}-{acronym}-{year}-{person}"
        main = base / main_folder_name

        # Return code_label (for section/subfolders) + main path
        # IMPORTANT: return project_code so it prefixes sections/subfolders too
        return project_code, acronym, main
        

# ============================= 12. ENTRY POINT ===============================
def main():
    root = tk.Tk()
    app = FolderCreatorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
