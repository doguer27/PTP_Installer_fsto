import sys
import os
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk, simpledialog
import subprocess
import shutil
import tempfile
import threading
import json 
import webbrowser
import time
import zipfile
import re 
import urllib.request

# --- BLOQUE CRÍTICO DE INICIO ---
# Esto debe ir ANTES de cualquier otra cosa lógica de rutas
if getattr(sys, 'frozen', False):
    # Detectamos la carpeta temporal interna (_MEIPASS)
    base_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(os.path.abspath(sys.executable))
    
    # 1. Definimos la variable que falta
    os.environ['_PYI_APPLICATION_HOME_DIR'] = base_path
    
    # 2. Le decimos a tkinterdnd2 dónde está su librería (gracias al --collect-all del paso 1)
    os.environ['TKDND_LIBRARY'] = os.path.join(base_path, 'tkinterdnd2')
    
    # 3. Aseguramos que el PATH vea esta carpeta para cargar DLLs
    if base_path not in os.environ.get('PATH', ''):
        os.environ['PATH'] = base_path + os.pathsep + os.environ.get('PATH', '')

# --- INTENTO DE IMPORTAR LIBRERÍA DE DRAG & DROP ---
DRAG_DROP_AVAILABLE = False
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DRAG_DROP_AVAILABLE = True
except ImportError:
    pass

    BRAND_NAME = "doguer;"
    FOOTER_LINK_TEXT = "Donate Here"
    FOOTER_LINK_URL = "https://paypal.me/doguer26"
    FOOTER_BTN_COLOR = "#0079C1" 
    FOOTER_BTN_HOVER = "#005ea6"
    GITHUB_REPO = "doguer27/PTP_Installer_fsto"

VER_NUM = "v1.1.2" # Actualizado ligeramente para reflejar cambios
TARGET_EXE_NAME = "Livery_Installer_Converter_PMDG.exe"

COLOR_BG = "#0F1225"           # Fondo Principal
COLOR_CARD = "#1A1E3F"         # Tarjetas / Marcos
COLOR_SURFACE = "#252A40"      # UI Inputs
COLOR_ACCENT = "#00A8FF"       # Azul Vibrante
COLOR_GOLD = "#FFD700"         # Dorado
COLOR_DISCORD = "#5865F2"      # Azul Discord
COLOR_TEXT_PRIMARY = "#FFFFFF" 
COLOR_TEXT_SECONDARY = "#AEC6CF"

FONT_MAIN = ("Segoe UI", 9)
FONT_BOLD = ("Segoe UI", 9, "bold")
FONT_TITLE = ("Segoe UI", 16, "bold")

CONFIG_FILE_NAME = "installer_config.json"

try:
    if getattr(sys, 'frozen', False):
        BASE_DIR = sys._MEIPASS
        APP_DIR = os.path.dirname(os.path.abspath(sys.executable)) 
    else:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        APP_DIR = BASE_DIR 
except Exception as e:
    messagebox.showerror("Critical Error", f"Error detectando rutas:\n{e}")
    sys.exit(1)

CONFIG_PATH = os.path.join(APP_DIR, CONFIG_FILE_NAME)

def get_resource_path(relative_path):
    return os.path.join(BASE_DIR, relative_path)

def normalize_path(path):
    if path: return os.path.normpath(path).replace("\\", "/")
    return ""

def windows_path(path):
    if path: return os.path.normpath(path).replace("/", "\\")
    return ""

# --- GESTIÓN DE CONFIGURACIÓN (JSON) ---
def load_user_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r') as f: return json.load(f)
        except: pass
    return {}

def save_user_config():
    data = {"platform": platform_var.get(), "community_path": entry_community.get()}
    try:
        with open(CONFIG_PATH, 'w') as f: json.dump(data, f, indent=4)
    except Exception as e: print(f"Error saving config: {e}")

# --- VARIABLES GLOBALES ---
log_visible = False 

# --- RUTAS DE HERRAMIENTAS ---
def get_converter_path():
    return get_resource_path(os.path.join("ptp_converter", "ptp_converter.exe"))

def get_texconv_path():
    path = get_resource_path(os.path.join("required", "texconv.exe"))
    if not os.path.exists(path):
        path = os.path.join(APP_DIR, "required", "texconv.exe")
    return path

def get_layout_tool_path():
    return get_resource_path(os.path.join("MSFS24_Data", "MSFSLayoutGenerator.exe"))

def get_model_airframe_source(model_folder):
    return get_resource_path(os.path.join("MSFS24_Data", "models", model_folder, "model.airframe"))

# --- GUI LOGGING ---
def log_gui(message):
    try:
        txt_log.config(state=tk.NORMAL)
        txt_log.insert(tk.END, message + "\n")
        txt_log.see(tk.END)
        txt_log.config(state=tk.DISABLED)
    except: pass

def toggle_log():
    global log_visible
    if log_visible:
        txt_log.pack_forget()
        btn_toggle_log.config(text="Show Debug Log ▼")
        log_visible = False
    else:
        txt_log.pack(side=tk.BOTTOM, fill="both", expand=True, padx=20, pady=(0, 10))
        btn_toggle_log.config(text="Hide Debug Log ▲")
        log_visible = True

# --- FUNCIÓN DE ENLACE DINÁMICO ---
def open_footer_link(event):
    webbrowser.open_new(FOOTER_LINK_URL)

def on_footer_enter(e):
    lbl_link.config(fg=FOOTER_BTN_HOVER)

def on_footer_leave(e):
    lbl_link.config(fg=FOOTER_BTN_COLOR)

# =============================================================================
# FUNCIONES DE ACTUALIZACIÓN AUTOMÁTICA
# =============================================================================
def check_for_updates():
    try:
        log_gui("[UPDATER] Checking for updates...")
        api_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        req = urllib.request.Request(api_url, data=None, headers={'User-Agent': 'Livery_Installer_Converter_PMDG'})
        
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            latest_tag = data.get("tag_name", "").strip()
            assets = data.get("assets", [])
            
            exe_url = ""
            txt_url = "" 

            for asset in assets:
                if asset["name"] == TARGET_EXE_NAME:
                    exe_url = asset["browser_download_url"]
                elif asset["name"].endswith(".txt"):
                    txt_url = asset["browser_download_url"]
            
            if not exe_url:
                for asset in assets:
                    if asset["name"].endswith(".exe"):
                        exe_url = asset["browser_download_url"]
                        break
            
            if latest_tag and latest_tag != VER_NUM and exe_url:
                log_gui(f"[UPDATER] New version found: {latest_tag}")
                root.after(0, lambda: show_update_dialog(latest_tag, exe_url, txt_url))
            else:
                log_gui("[UPDATER] App is up to date.")
                
    except Exception as e:
        log_gui(f"[UPDATER] Check failed: {e}")

def show_update_dialog(new_version, url_exe, url_txt):
    msg = f"A new version is available!\n\nCurrent: {VER_NUM}\nLatest: {new_version}\n\nUpdate automatically now?"
    if messagebox.askyesno(f"Update Available - {BRAND_NAME}", msg, icon='info'):
        download_and_restart(url_exe, url_txt, new_version)

def download_and_restart(url_exe, url_txt, new_version):
    if not getattr(sys, 'frozen', False): 
        messagebox.showinfo("Info", "Auto-update only works in compiled (.exe) mode.")
        return

    wait_window = tk.Toplevel(root)
    wait_window.title("Updating...")
    ws = root.winfo_screenwidth()
    hs = root.winfo_screenheight()
    x = (ws/2) - (300/2)
    y = (hs/2) - (150/2)
    wait_window.geometry('%dx%d+%d+%d' % (300, 150, x, y))
    wait_window.attributes("-topmost", True)
    tk.Label(wait_window, text="Downloading update...\nPlease wait...", font=("Segoe UI", 12)).pack(expand=True)
    wait_window.update()

    def _download_thread():
        try:
            current_exe = sys.executable
            current_dir = os.path.dirname(current_exe)
            orig_exe_name = os.path.basename(current_exe)
            
            temp_exe_name = f"update_{int(time.time())}.exe"
            downloaded_exe_path = os.path.join(current_dir, temp_exe_name)
            
            import urllib.request
            urllib.request.urlretrieve(url_exe, downloaded_exe_path)
            
            txt_cmd = ""
            if url_txt:
                try:
                    temp_txt = os.path.join(current_dir, "patch_notes_temp.txt")
                    urllib.request.urlretrieve(url_txt, temp_txt)
                    txt_cmd = f'move /Y "{temp_txt}" "{os.path.join(current_dir, "PatchNotes.txt")}"'
                except: pass
            
            bat_path = os.path.join(current_dir, "update_fix.bat")
            
            bat_content = f"""@echo off
chcp 65001 >nul
timeout /t 3 /nobreak > NUL
del "{current_exe}"
ren "{downloaded_exe_path}" "{orig_exe_name}"
{txt_cmd}
set _MEIPASS2=
set _MEIPASS=
start "" explorer.exe "{current_exe}"
del "%~f0"
exit
"""
            with open(bat_path, "w", encoding="utf-8") as f: 
                f.write(bat_content)
            
            os.startfile(bat_path)
            os._exit(0)
            
        except Exception as e:
            try:
                root.after(0, lambda: messagebox.showerror("Update Error", f"Failed to update:\n{e}"))
                root.after(0, wait_window.destroy)
            except: pass

    threading.Thread(target=_download_thread, daemon=True).start()

# --- AUTO DETECT SDK ---
def detect_automatic_sdk():
    candidates = ["C:/MSFS 2024 SDK", "D:/MSFS 2024 SDK", "E:/MSFS 2024 SDK", "F:/MSFS 2024 SDK", "G:/MSFS 2024 SDK"]
    for path in candidates:
        if os.path.exists(path):
            if os.path.exists(os.path.join(path, "Tools", "bin", "fspackagetool.exe")) or \
               os.path.exists(os.path.join(path, "Tools", "fspackagetool.exe")):
                return normalize_path(path)
    return ""

def restart_program():
    try:
        python = sys.executable
        os.execl(python, python, *sys.argv)
    except Exception as e: messagebox.showerror("Error", f"Could not restart automatically.\n{e}")

def run_sdk_installer():
    msi_path = os.path.join(APP_DIR, "SDK Install", "MSFS2024_SDK_Core_Installer_1.5.7.msi")
    msi_path = windows_path(msi_path)
    if os.path.exists(msi_path):
        try:
            log_gui(f"[INSTALLER] Launching: {msi_path}")
            os.startfile(msi_path) 
            if messagebox.askokcancel("Installing SDK...", "Once installed, click OK to RESTART this app."): restart_program()
        except Exception as e:
            messagebox.showerror("Installer Error", f"{e}")
            select_sdk()
    else:
        messagebox.showerror("Installer Missing", "Installer not found.")
        select_sdk()

def update_community_path_from_platform(*args):
    platform = platform_var.get()
    if "Please choose" in platform: return
    log_gui(f"[DETECTING] Searching for Community ({platform})...")
    ruta_opt = ""
    if platform == "Steam":
        ruta_opt = os.path.join(os.getenv('APPDATA'), "Microsoft Flight Simulator 2024", "UserCfg.opt")
    elif platform == "Microsoft Store":
        ruta_opt = os.path.join(os.getenv('LOCALAPPDATA'), "Packages", "Microsoft.Limitless_8wekyb3d8bbwe", "LocalCache", "UserCfg.opt")

    detected_comm = ""
    if os.path.exists(ruta_opt):
        try:
            with open(ruta_opt, "r", encoding="utf-8", errors="ignore") as f:
                for line in reversed(f.readlines()):
                    if "InstalledPackagesPath" in line:
                        parts = line.split('"')
                        if len(parts) >= 2:
                            detected_comm = f"{normalize_path(parts[1])}/Community"
                            break
        except: pass
     
    if detected_comm:
        entry_community.delete(0, tk.END)
        entry_community.insert(0, detected_comm)
        log_gui(f"[SUCCESS] Community found: {detected_comm}")
        save_user_config()
    else:
        log_gui("[WARN] Could not auto-detect Community folder.")

# --- SDK WAIT ---
def wait_for_sdk_finish():
    log_gui("[STEAM] Waiting for SDK to initialize...")
    time.sleep(8)
    
    start_time = time.time()
    timeout_seconds = 600
    sdk_started = False

    log_gui("[AUTO] Monitoring FlightSimulator2024.exe...")
     
    while True:
        if (time.time() - start_time) > timeout_seconds:
            log_gui("[ERROR] Timeout reached waiting for SDK.")
            break

        try:
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            cmd = ['tasklist', '/FI', 'IMAGENAME eq FlightSimulator2024.exe']
            
            process = subprocess.run(cmd, capture_output=True, text=True, startupinfo=si)
            output = str(process.stdout or "")
             
            if "FlightSimulator2024.exe" in output:
                if not sdk_started:
                    log_gui("[AUTO] SDK Process detected and running...")
                    sdk_started = True
                time.sleep(3)
            else:
                if sdk_started:
                    log_gui("[AUTO] SDK process finished successfully.")
                    break
                else:
                    time.sleep(2)
                    
        except Exception as e:
            log_gui(f"[WARN] Monitor failed ({e}), continuing...")
            break

def analyze_json_flags(json_path):
    try:
        if not os.path.exists(json_path): return "ALBD" 
        with open(json_path, 'r', encoding='utf-8', errors='ignore') as f: content = f.read()
        if "FL_BITMAP_METAL_ROUGH_AO_DATA" in content: return "COMP"
        if "FL_BITMAP_TANGENT_DXT5N" in content: return "NORM"
        return "ALBD"
    except Exception: return "ALBD"

def generate_xml_content(texture_type):
    bitmap_slot = "MTL_BITMAP_DECAL0"
    user_flags_content = '<UserFlags Type="_DEFAULT">QUALITYHIGH</UserFlags>'
    force_no_alpha = "" 
    if texture_type == "COMP":
        bitmap_slot = "MTL_BITMAP_METAL_ROUGH_AO"
        force_no_alpha = "<ForceNoAlpha>true</ForceNoAlpha>"
    elif texture_type == "NORM":
        bitmap_slot = "MTL_BITMAP_NORMAL"
        force_no_alpha = "" 
    return f"""<?xml version="1.0" encoding="utf-8"?>
<BitmapConfiguration>
    <BitmapSlot>{bitmap_slot}</BitmapSlot>
    {user_flags_content}
    {force_no_alpha}
</BitmapConfiguration>"""

def prepare_modular_project(temp_dir):
    temp_dir = normalize_path(temp_dir)
    pkg_name = "livery-converter-2024"
    physical_path_texture = f"{temp_dir}/PackageSources/SimObjects/Airplanes/{pkg_name}/common/texture"
    path_definitions = f"{temp_dir}/PackageDefinitions"
    os.makedirs(physical_path_texture, exist_ok=True)
    os.makedirs(path_definitions, exist_ok=True)
     
    with open(f"{path_definitions}/{pkg_name}.xml", "w", encoding="utf-8") as f:
        f.write(f"""<?xml version="1.0" encoding="utf-8"?>
<AssetPackage Version="0.1.0">
    <ItemSettings><ContentType>AIRCRAFT</ContentType><Title>{pkg_name}</Title><Manufacturer>Converter</Manufacturer><Creator>Converter</Creator></ItemSettings>
    <Flags><VisibleInStore>false</VisibleInStore><CanBeReferenced>false</CanBeReferenced></Flags>
    <AssetGroups>
        <AssetGroup Name="{pkg_name}">
            <Type>ModularSimObject</Type>
            <Flags><FSXCompatibility>false</FSXCompatibility></Flags>
            <AssetDir>PackageSources\\SimObjects\\Airplanes\\{pkg_name}\\</AssetDir>
            <OutputDir>SimObjects\\Airplanes\\{pkg_name}\\</OutputDir>
        </AssetGroup>
    </AssetGroups>
</AssetPackage>""")

    project_xml_path = f"{temp_dir}/{pkg_name}.xml"
    with open(project_xml_path, "w", encoding="utf-8") as f:
        f.write(f"""<?xml version="1.0" encoding="utf-8"?>
<Project Version="2" Name="{pkg_name}" FolderName="Packages" MetadataFolderName="PackagesMetadata">
    <OutputDirectory>.</OutputDirectory>
    <TemporaryOutputDirectory>_PackageInt</TemporaryOutputDirectory>
    <Packages><Package>PackageDefinitions\\{pkg_name}.xml</Package></Packages>
</Project>""")
    with open(f"{temp_dir}/{pkg_name}.xml.user", "w", encoding="utf-8") as f:
        f.write("<UserSettings><ShowOnlyEdited>false</ShowOnlyEdited></UserSettings>")

    return project_xml_path, physical_path_texture

def simple_extract(source, target):
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    converter_exe = get_converter_path()
    
    if os.path.isdir(source):
        shutil.copytree(source, target, dirs_exist_ok=True)
        return True
    
    ext = os.path.splitext(source)[1].lower()
    if ext == ".ptp":
        fname = os.path.basename(source)
        shutil.copy2(source, f"{target}/{fname}")
        subprocess.run([converter_exe, f"{target}/{fname}"], cwd=target, startupinfo=si)
        return True
    elif ext == ".zip":
        try:
            with zipfile.ZipFile(source, 'r') as zip_ref: zip_ref.extractall(target)
            return True
        except: return False
    return False

# --- MAIN PROCESS (ACTUALIZADO) ---
def start_conversion_process():
    source_file_path = normalize_path(entry_ptp_path.get())
    commons_file_path = normalize_path(entry_commons_path.get())
    use_fleet_mode = is_fleet_mode.get()
    
    sdk_path = normalize_path(entry_sdk.get())
    platform_version = str(platform_var.get() or "")
    community_path = normalize_path(entry_community.get()) 
     
    if "Please choose" in platform_version:
        messagebox.showwarning("Selection Required", "Please select your Simulator Version.")
        btn_run.config(state=tk.NORMAL, bg=COLOR_GOLD)
        return

    if not community_path or not os.path.exists(community_path):
        messagebox.showerror("Error", "Invalid Community Folder Path.")
        btn_run.config(state=tk.NORMAL, bg=COLOR_GOLD)
        return

    if use_fleet_mode and (not commons_file_path or not os.path.exists(commons_file_path)):
        messagebox.showerror("Error", "Fleet Mode is checked but Commons file/folder is missing.")
        btn_run.config(state=tk.NORMAL, bg=COLOR_GOLD)
        return

    file_base_name = os.path.splitext(os.path.basename(source_file_path))[0]
    is_directory = os.path.isdir(source_file_path)
    file_extension = "" if is_directory else os.path.splitext(source_file_path)[1].lower()
     
    converter_exe = get_converter_path()
    texconv_exe = get_texconv_path()
    layout_gen_original = get_layout_tool_path()
     
    fspackagetool = f"{sdk_path}/Tools/bin/fspackagetool.exe"
    if not os.path.exists(fspackagetool): fspackagetool = f"{sdk_path}/Tools/fspackagetool.exe"
    fspackagetool = normalize_path(fspackagetool)

    if not os.path.exists(source_file_path): return messagebox.showerror("Error", "Source path missing.")
    log_gui(f"[DEBUG] Buscando texconv en: {texconv_exe}")
    if not os.path.exists(texconv_exe): 
        return messagebox.showerror("Error", f"texconv missing at: {texconv_exe}")
    if not os.path.exists(fspackagetool): return messagebox.showerror("Error", "fspackagetool missing inside SDK folder.")
    if file_extension == ".ptp" and not os.path.exists(converter_exe): return messagebox.showerror("Error", "ptp_converter missing.")

    btn_run.config(state=tk.DISABLED, bg="#555555")
    if not log_visible: toggle_log()
    txt_log.config(state=tk.NORMAL); txt_log.delete(1.0, tk.END); txt_log.config(state=tk.DISABLED)

    temp_extract = None
    temp_commons = None 
    temp_build = None
    temp_thumb_safe = None
    temp_short_path = None 
    new_ini_path = None 
     
    detected_variant_str = "Unknown"
    detected_base_container = "Unknown" 
    target_folder_name = "Unknown"
     
    aircraft_family = "737" 
    target_simobjects_subpath = ""
    target_wasm_subpath = ""
    source_model_airframe = "" 
    req_tag_model = ""
    wing_tag_cfg = "" 

    try:
        # 1. EXTRACTION & VALIDATION
        temp_extract = tempfile.mkdtemp(prefix="extract_temp_")
        filename_only = os.path.basename(source_file_path)
        log_gui(f"[PHASE 1] Extracting/Processing: {filename_only}")
         
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        if is_directory:
            log_gui(" > Mode: Folder Structure")
            try: shutil.copytree(source_file_path, temp_extract, dirs_exist_ok=True)
            except Exception as e: return log_gui(f"[ERROR] Folder Copy Failed: {e}")
             
            has_cfg = False; has_texture = False
            for root_scan, dirs, files in os.walk(temp_extract):
                for f in files:
                    if f.lower() in ["aircraft.cfg", "livery.cfg", "sim.cfg", "config.cfg"]: has_cfg = True
                for d in dirs:
                    if d.lower() == "texture" or d.lower().startswith("texture."): has_texture = True
            if not (has_cfg and has_texture): return log_gui("[ERROR] Folder Validation Failed.")

        elif file_extension == ".ptp":
            log_gui(" > Mode: PTP Conversion")
            shutil.copy2(source_file_path, f"{temp_extract}/{filename_only}")
            subprocess.run([converter_exe, f"{temp_extract}/{filename_only}"], cwd=temp_extract, startupinfo=si)
             
        elif file_extension == ".zip":
            log_gui(" > Mode: ZIP Extraction")
            try:
                with zipfile.ZipFile(source_file_path, 'r') as zip_ref: zip_ref.extractall(temp_extract)
            except Exception as e: return log_gui(f"[ERROR] Bad Zip File: {e}")

            has_cfg = False; has_texture = False; has_ini = False 
            for root_scan, dirs, files in os.walk(temp_extract):
                for f in files:
                    if f.lower() in ["aircraft.cfg", "livery.cfg", "sim.cfg", "config.cfg"]: has_cfg = True
                    if f.lower().endswith(".ini"): has_ini = True
                for d in dirs:
                    if d.lower() == "texture" or d.lower().startswith("texture."): has_texture = True
            if not (has_cfg and has_texture): return log_gui("[ERROR] ZIP Validation Failed.")
            if not has_ini: log_gui("[WARN] No .ini file found.")

        # =========================================================================
        # [FEATURE 1] DETECTOR DE PTPS ANIDADOS (NESTED PTPs)
        # =========================================================================
        nested_ptps = []
        for root_scan, dirs, files in os.walk(temp_extract):
            for file in files:
                if file.lower().endswith(".ptp") and file != filename_only:
                     nested_ptps.append(os.path.join(root_scan, file))
        
        if nested_ptps:
            log_gui(f"[INFO] Found {len(nested_ptps)} nested PTP files.")
            docs_path = os.path.join(os.path.expanduser("~"), "Documents", "PMDG_Extracted_PTPs")
            os.makedirs(docs_path, exist_ok=True)
            
            moved_count = 0
            for p_path in nested_ptps:
                try:
                    shutil.move(p_path, os.path.join(docs_path, os.path.basename(p_path)))
                    moved_count += 1
                except Exception as e:
                    log_gui(f"[WARN] Could not move {os.path.basename(p_path)}: {e}")

            if moved_count > 0:
                os.startfile(docs_path)
                messagebox.showinfo("Package Detected", 
                                    f"Found {moved_count} PTP files inside the package.\n"
                                    "This does mean this is a fleet package with many liveries\n\n"
                                    "They have been moved to a safe folder in your Documents.\n"
                                    "Folder is now open. Please install them individually.")
                return 

        if use_fleet_mode:
            temp_commons = tempfile.mkdtemp(prefix="commons_temp_")
            log_gui(f"[FLEET] Extracting Commons Pack...")
            
            if simple_extract(commons_file_path, temp_commons):
                commons_texture_path = None
                for root_scan, dirs, files in os.walk(temp_commons):
                    for d in dirs:
                        if d.lower().startswith("texture"):
                            commons_texture_path = os.path.join(root_scan, d)
                            break
                    if commons_texture_path: break
                
                if commons_texture_path:
                    log_gui(f"[FLEET] Commons texture found. Merging...")
                    main_texture_path = None
                    for root_scan, dirs, files in os.walk(temp_extract):
                        for d in dirs:
                            if d.lower().startswith("texture"):
                                main_texture_path = os.path.join(root_scan, d)
                                break
                        if main_texture_path: break
                    
                    if main_texture_path:
                        shutil.copytree(commons_texture_path, main_texture_path, dirs_exist_ok=True, 
                                        ignore=shutil.ignore_patterns('thumbnail.jpg', 'thumbnail.JPG', 'thumbnail.png', 'thumbnail.PNG'))
                        log_gui("[FLEET] Textures merged successfully (Thumbnail preserved).")
                    else:
                        log_gui("[ERROR] Main livery has no texture folder.")
                else:
                    log_gui("[WARN] No texture folder found inside Commons file.")
            else:
                log_gui("[ERROR] Failed to extract Commons file.")
        log_gui("[PHASE 1.5] Analyzing & Naming...")
         
        temp_cfg_path = None
        detected_title = ""
        detected_model_key = ""
        detected_sim_key = ""

        for root_scan, dirs, files in os.walk(temp_extract):
            for f in files:
                if f.lower() in ["aircraft.cfg", "livery.cfg", "sim.cfg", "config.cfg"]:
                    temp_cfg_path = os.path.join(root_scan, f)
                    break
            if temp_cfg_path: break
            
        if temp_cfg_path:
            with open(temp_cfg_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line_clean = line.strip()
                    if "base_container" in line_clean.lower() and "=" in line_clean:
                        detected_base_container = line_clean.split("=")[1].strip().replace('"', '')
                    if "title" in line_clean.lower() and "=" in line_clean:
                        parts = line_clean.split("=")
                        if parts[0].strip().lower() == "title":
                            detected_title = parts[1].strip().split(';')[0].replace('"', '')
                    if "model" in line_clean.lower() and "=" in line_clean:
                        try: detected_model_key = line_clean.split("=")[1].strip().replace('"', '').upper()
                        except: pass
                    if "sim" in line_clean.lower() and "=" in line_clean:
                        try: detected_sim_key = line_clean.split("=")[1].strip().replace('"', '').upper()
                        except: pass
         
        base_clean_upper = str(detected_base_container).upper()
        base_clean_original = str(detected_base_container).replace("..\\", "").replace("../", "").strip()
        title_upper = str(detected_title).upper()
        det_mod = str(detected_model_key)
        det_sim = str(detected_sim_key)

        if "777F" in base_clean_upper or "777F" in det_mod or "B777F" in det_sim or "PMDG 777F" in title_upper:
            aircraft_family = "777F"
            if detected_base_container == "Unknown": detected_base_container = "PMDG 777F" 
            target_simobjects_subpath = "SimObjects/Airplanes/PMDG 777F/liveries/pmdg"
            target_wasm_subpath = "pmdg-aircraft-77f"
            source_model_airframe = get_model_airframe_source("777F")
            req_tag_model = "b77f_ext"
            wing_tag_cfg = "engine_ge" 
            detected_variant_str = "777F (Freighter)"
            log_gui(f" > Detected {detected_variant_str}")

        elif "777-300ER" in base_clean_upper or "300ER" in det_mod or "B777-300ER" in det_sim or "PMDG 777-300ER" in title_upper:
            aircraft_family = "777-300ER"
            if detected_base_container == "Unknown": detected_base_container = "PMDG 777-300ER"
            target_simobjects_subpath = "SimObjects/Airplanes/PMDG 777-300ER/liveries/pmdg"
            target_wasm_subpath = "pmdg-aircraft-77w"
            source_model_airframe = get_model_airframe_source("777-300ER")
            req_tag_model = "b77w_ext"
            wing_tag_cfg = "engine_gew" 
            detected_variant_str = "777-300ER"
            log_gui(f" > Detected {detected_variant_str}")

        elif "777-200LR" in base_clean_upper or "200LR" in det_mod or "B777-200LR" in det_sim or "PMDG 777-200LR" in title_upper:
            aircraft_family = "777-200LR"
            if detected_base_container == "Unknown": detected_base_container = "PMDG 777-200LR"
            target_simobjects_subpath = "SimObjects/Airplanes/PMDG 777-200LR/liveries/pmdg"
            target_wasm_subpath = "pmdg-aircraft-77l"
            source_model_airframe = get_model_airframe_source("777-200LR")
            req_tag_model = "b77l_ext"
            wing_tag_cfg = "engine_gel" 
            detected_variant_str = "777-200LR"
            log_gui(f" > Detected {detected_variant_str}")

        elif "777-200ER" in base_clean_upper or "777" in base_clean_upper:
            aircraft_family = "777-200ER"
            if detected_base_container == "Unknown": detected_base_container = "PMDG 777-200ER"
            target_simobjects_subpath = "SimObjects/Airplanes/PMDG 777-200ER/liveries/pmdg"
            target_wasm_subpath = "pmdg-aircraft-77er"
            source_model_airframe = get_model_airframe_source("777-200ER")
            log_gui(f" > Detected PMDG 777 Family ({detected_base_container})")

# --- MODIFICACIÓN: SOPORTE PARA 737-900ER (Ruta Unificada) ---
        elif "737-900ER" in base_clean_upper or "737-900ER" in title_upper or "B737-900ER" in det_sim:
            aircraft_family = "737-900ER" # Mantenemos esto para que luego asigne el tag "b739er_ext"
            if detected_base_container == "Unknown": detected_base_container = "PMDG 737-900ER"
            
            # CAMBIO CLAVE AQUÍ: Apuntamos a la carpeta del 900 normal
            target_simobjects_subpath = "SimObjects/Airplanes/PMDG 737-900/liveries/pmdg"
            
            # El WASM se mantiene específico para que encuentre su config
            target_wasm_subpath = "pmdg-aircraft-739" 
            source_model_airframe = get_model_airframe_source("737-900")
            log_gui(f" > Detected PMDG 737-900ER Family ({detected_base_container})")

        # --- SOPORTE PARA 737-900 (Normal) ---
        elif "737-900" in base_clean_upper or "737-900" in title_upper or "B737-900" in det_sim:
            aircraft_family = "737-900" # Mantenemos esto para el tag "b739_ext"
            if detected_base_container == "Unknown": detected_base_container = "PMDG 737-900"
            
            # Esta ruta ya es la correcta, coincide con la de arriba
            target_simobjects_subpath = "SimObjects/Airplanes/PMDG 737-900/liveries/pmdg"
            
            target_wasm_subpath = "pmdg-aircraft-739" 
            source_model_airframe = get_model_airframe_source("737-900")
            log_gui(f" > Detected PMDG 737-900 Family ({detected_base_container})")

        elif "737-600" in base_clean_upper or "737-600" in title_upper or "B737-600" in det_sim:
            aircraft_family = "737-600" # Mantenemos esto para el tag "b739_ext"
            if detected_base_container == "Unknown": detected_base_container = "PMDG 737-600"
            
            # Esta ruta ya es la correcta, coincide con la de arriba
            target_simobjects_subpath = "SimObjects/Airplanes/PMDG 737-600/liveries/pmdg"
            
            target_wasm_subpath = "pmdg-aircraft-736" 
            source_model_airframe = get_model_airframe_source("737-600")
            log_gui(f" > Detected PMDG 737-600 Family ({detected_base_container})")

        else:
            aircraft_family = "737"
            if detected_base_container == "Unknown": detected_base_container = "PMDG 737-800"
            target_simobjects_subpath = "SimObjects/Airplanes/PMDG 737-800/liveries/pmdg"
            target_wasm_subpath = "pmdg-aircraft-738"
            source_model_airframe = get_model_airframe_source("737-800")
            log_gui(f" > Detected PMDG 737 Family ({detected_base_container})")

        base_clean_original = str(detected_base_container).replace("..\\", "").replace("../", "").strip()

        if detected_title:
            folder_raw_name = detected_title.lower()
            remove_strings = [
                base_clean_original.lower(),   
                "pmdg 777-300er", "pmdg 777-200lr", "pmdg 777f",
                "pmdg 777-200er", "pmdg 777-200",
                "pmdg 737-900er", "pmdg 737-900", 
                "pmdg 737-600", "pmdg 737-800", "pmdg 737", 
                "pmdg", "777-300er", "777-200lr", "777f",
                "737-900er", "737-900", "737-600"
            ]
            for s in remove_strings:
                folder_raw_name = folder_raw_name.replace(s, "")

            folder_raw_name = re.sub(r'[^a-z0-9\-\s]', '', folder_raw_name) 
            folder_raw_name = folder_raw_name.replace(" ", "-")
            while "--" in folder_raw_name: folder_raw_name = folder_raw_name.replace("--", "-")
            folder_raw_name = folder_raw_name.strip("-")
             
            if folder_raw_name: target_folder_name = folder_raw_name
            else: target_folder_name = file_base_name 
        else:
            target_folder_name = file_base_name 
             
        log_gui(f" > Folder Name Generated: {target_folder_name}")

        if not os.path.exists(source_model_airframe):
            return log_gui(f"[ERROR] model.airframe not found at: {source_model_airframe}")

        root_pkg_name = "pmdg-converted-liveries"
        community_root_path = f"{community_path}/{root_pkg_name}"
        liveries_parent_folder = f"{community_root_path}/{target_simobjects_subpath}"
        final_plane_path = f"{liveries_parent_folder}/{target_folder_name}"

        if os.path.exists(final_plane_path):
            if not messagebox.askyesno("Folder Exists", f"Overwrite '{target_folder_name}'?"): return log_gui("[ABORT] User cancelled.")

        # ---------------------------------------------------------------------
         
        # 3. THUMBNAIL SAFEGUARD
        temp_thumb_safe = tempfile.mkdtemp(prefix="thumb_safe_")
        safe_thumb_path = None
        for root_scan, dirs, files in os.walk(temp_extract):
            for f in files:
                if "thumbnail" in f.lower() and f.lower().endswith(".jpg"):
                    shutil.copy2(os.path.join(root_scan, f), os.path.join(temp_thumb_safe, "original_thumb.jpg"))
                    safe_thumb_path = os.path.join(temp_thumb_safe, "original_thumb.jpg")
                    break
            if safe_thumb_path: break

        log_gui("[PHASE 4] Searching for textures...")
        source_textures = None
        
        for root_scan, dirs, files in os.walk(temp_extract):
            # Ordenamos para mirar primero las que parecen texturas
            dirs.sort(key=lambda x: not x.lower().startswith("texture")) 
            
            for d in dirs:
                # 1. ¿El nombre de la carpeta empieza por "texture"?
                if d.lower() == "texture" or d.lower().startswith("texture."):
                    candidate_path = os.path.join(root_scan, d)
                    
                    # 2. VALIDACIÓN CRUCIAL: ¿Tiene archivos .DDS dentro?
                    has_dds = False
                    try:
                        for f in os.listdir(candidate_path):
                            if f.lower().endswith(".dds"):
                                has_dds = True
                                break
                    except: pass
                    
                    if has_dds:
                        found_path = normalize_path(candidate_path)
                        # Renombrar a Texture.MSFS2020 en su ubicación actual
                        new_path = os.path.join(os.path.dirname(found_path), "Texture.MSFS2020")
                        
                        if os.path.exists(new_path):
                            try: shutil.rmtree(new_path)
                            except: pass
                        
                        try:
                            os.rename(found_path, new_path)
                            source_textures = normalize_path(new_path)
                            log_gui(f" > Texture folder found: {d} (Contains DDS)")
                        except Exception as e:
                            log_gui(f"[ERROR] Rename failed: {e}")
                        
                        break # Rompe el loop interno
            if source_textures: break # Rompe el loop de os.walk
         
        if not source_textures: return log_gui("[ERROR] No valid 'Texture' folder with .DDS files found.")

        # 5. PREPARATION & CONVERSION
        drive = os.path.splitdrive(os.path.abspath(APP_DIR))[0] or "C:"
        temp_build = os.path.normpath(f"{drive}/pmdg_sdk_build")
        
        if os.path.exists(temp_build): 
            try: shutil.rmtree(temp_build, ignore_errors=True)
            except: pass
        os.makedirs(temp_build, exist_ok=True)
        
        log_gui(f"[PHASE 2] Setting up project at: {temp_build}")
        
        path_project_xml, path_texture_deep = prepare_modular_project(temp_build)
         
        dds_files = [f for f in os.listdir(source_textures) if f.lower().endswith(".dds")]
        log_gui(f"Analyzing {len(dds_files)} files...")
        texconv_exe_win = windows_path(texconv_exe)
        path_dest_win = windows_path(path_texture_deep)

        for dds in dds_files:
            if "thumbnail" in dds.lower() or dds.lower() == "texture.cfg": continue
            dds_source = f"{source_textures}/{dds}"
            dds_dest = f"{path_texture_deep}/{dds}"
            shutil.copy2(dds_source, dds_dest)
             
            json_path = f"{source_textures}/{dds}.json"
            if not os.path.exists(json_path): json_path = f"{source_textures}/{os.path.splitext(dds)[0]}.json"
             
            subprocess.run([texconv_exe_win, "-ft", "png", "-f", "R8G8B8A8_UNORM", "-m", "1", "-y", "-o", path_dest_win, dds], 
                           cwd=path_texture_deep, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, startupinfo=si)
            if os.path.exists(dds_dest): os.remove(dds_dest)
             
            expected_png = f"{path_texture_deep}/{os.path.splitext(dds)[0]}.png"
            if os.path.exists(expected_png):
                with open(f"{expected_png}.xml", "w", encoding="utf-8") as f: f.write(generate_xml_content(analyze_json_flags(json_path)))
                log_gui(f" > OK: {os.path.splitext(dds)[0]}")

        # 6. COMPILATION
        log_gui(f"[PHASE 3] Compiling with SDK...")
         
        project_xml_win = os.path.abspath(path_project_xml).replace("/", "\\")
        cwd_win = os.path.abspath(temp_build).replace("/", "\\")
         
        cmd_build = [fspackagetool, "-nopause", "-rebuild", "-outputtoseparateconsole", project_xml_win]
        if platform_version == "Steam": 
            cmd_build.insert(1, "-forcesteam")
         
        subprocess.run(cmd_build, cwd=cwd_win, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, startupinfo=si)
        wait_for_sdk_finish()

        # 7. INSTALLATION (FILES)
        log_gui(f"[PHASE 4] Installing to Community...")
        final_texture_path = f"{final_plane_path}/texture"
        final_thumb_path = f"{final_plane_path}/thumbnail"
        if os.path.exists(final_plane_path): shutil.rmtree(final_plane_path, ignore_errors=True)
        os.makedirs(final_texture_path, exist_ok=True); os.makedirs(final_thumb_path, exist_ok=True)
         
        temp_packages_path = f"{temp_build}/Packages"
        count = 0
        if os.path.exists(temp_packages_path):
            for root_scan, dirs, files in os.walk(temp_packages_path):
                for file in files:
                    if "thumbnail" in file.lower() or "texture.cfg" in file.lower(): continue
                    final_name = ""
                    if file.lower().endswith(".ktx2") or file.lower().endswith(".kktx"):
                        base_name = os.path.splitext(file)[0]
                        while base_name.lower().endswith(('.png', '.ktx2', '.kktx')): base_name = os.path.splitext(base_name)[0]
                        final_name = f"{base_name}.PNG.KTX2"
                    elif file.lower().endswith(".json") and "manifest" not in file and "layout" not in file:
                         base_name = os.path.splitext(file)[0]
                         while base_name.lower().endswith(('.png', '.ktx2', '.kktx', '.json')): base_name = os.path.splitext(base_name)[0]
                         final_name = f"{base_name}.PNG.KTX2.json"
                    if final_name:
                        try:
                            shutil.copy2(os.path.join(root_scan, file), os.path.join(final_texture_path, final_name))
                            count += 1
                        except: pass

        try:
            if os.path.exists(os.path.join(final_plane_path, "model.airframe")): shutil.rmtree(os.path.join(final_plane_path, "model.airframe"))
            shutil.copytree(source_model_airframe, os.path.join(final_plane_path, "model.airframe"))
        except Exception as e: log_gui(f"[ERROR] model.airframe copy: {e}")

        aircraft_root_extract = os.path.dirname(source_textures)
        for item in os.listdir(aircraft_root_extract):
            src_item = os.path.join(aircraft_root_extract, item)
            if item.lower() in ["model.cfg", "settings.dat", "texture.cfg", "livery.json", "manifest.json", "layout.json"]: continue
            if item.lower() == "model" or item.lower().startswith("model."): continue 
            if "thumbnail" in item.lower(): continue
            if os.path.normpath(src_item) == os.path.normpath(source_textures): continue
             
            dst_item = os.path.join(final_plane_path, item)
            try:
                if os.path.isdir(src_item): shutil.copytree(src_item, dst_item, dirs_exist_ok=True)
                else: shutil.copy2(src_item, dst_item)
            except: pass

        if safe_thumb_path and os.path.exists(safe_thumb_path):
            subprocess.run([texconv_exe_win, "-w", "1618", "-h", "582", "-ft", "png", "-f", "R8G8B8A8_UNORM", "-y", "-o", windows_path(final_thumb_path), windows_path(safe_thumb_path)], 
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, startupinfo=si)
            gen_thumb = os.path.join(final_thumb_path, "original_thumb.png")
            if os.path.exists(gen_thumb):
                for name in ["thumbnail.png", "thumbnail_side.png", "thumbnail_button.png", "thumbnail_small.png"]: shutil.copy2(gen_thumb, os.path.join(final_thumb_path, name))
                os.remove(gen_thumb)
         
        # 8. CONFIG FILES & AUTO-DETECT
        log_gui("[PHASE 5] Config Files & Variant Logic...")
        cfg_path = None; target_ini_path = None
        for f in os.listdir(final_plane_path):
            if f.lower().endswith(".cfg") and "texture" not in f and "model" not in f: cfg_path = os.path.join(final_plane_path, f)
            if f.lower().endswith(".ini"): target_ini_path = os.path.join(final_plane_path, f)

        if cfg_path:
            atc_id, title, atc_airline, model_val = "", "", "", ""
            with open(cfg_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    if "=" in line:
                        k, v = line.split("=", 1)
                        k, v = k.strip().lower(), v.split(';')[0].strip().replace('"', '')
                        if k == "atc_id": atc_id = v
                        elif k == "title": title = v
                        elif k == "atc_airline": atc_airline = v
                        elif k == "model": model_val = v.upper()

            if not atc_id: atc_id = simpledialog.askstring("ATC ID Missing", "Enter ATC ID (e.g. LV-GVC):") or "XX-XXX"
             
            clean_title = title.replace("PMDG 737-800", "").replace("PMDG 777-200ER", "").strip()
            if clean_title.startswith("-"): clean_title = clean_title[1:].strip()
             
            json_tags = []
             
            if aircraft_family == "777-200ER":
                req_tag_model = "b772_ext"
                if "GE" in base_clean_upper:
                    wing_tag_cfg = "engine_ge"; json_tags.append("GE"); detected_variant_str = "777-200ER | GE"
                elif "PW" in base_clean_upper:
                    wing_tag_cfg = "engine_pw"; json_tags.append("PW"); detected_variant_str = "777-200ER | PW"
                elif "RR" in base_clean_upper:
                    wing_tag_cfg = "engine_rr"; json_tags.append("RR"); detected_variant_str = "777-200ER | RR"
                else:
                    wing_tag_cfg = "engine_ge"; json_tags.append("GE"); detected_variant_str = "777-200ER | GE (Default)"

            # --- LÓGICA 737-900ER ---
            elif aircraft_family == "737-900ER":
                req_tag_model = "b739er_ext"
                if model_val == "ERBW":
                    json_tags.append("BW"); wing_tag_cfg = "BW_L,BW_R"; detected_variant_str = "737-900ER | BW"
                elif model_val == "ERSSW":
                    json_tags.append("SSW"); wing_tag_cfg = "SSW_L,SSW_R"; detected_variant_str = "737-900ER | SSW"
                else:
                    json_tags.append("BW"); wing_tag_cfg = "BW_L,BW_R"; detected_variant_str = "737-900ER | BW (Default)"

            # --- LÓGICA 737-900 ---
            elif aircraft_family == "737-900":
                req_tag_model = "b739_ext"
                if model_val == "BW":
                    json_tags.append("BW"); wing_tag_cfg = "BW_L,BW_R"; detected_variant_str = "737-900 | BW"
                elif model_val == "SSW":
                    json_tags.append("SSW"); wing_tag_cfg = "SSW_L,SSW_R"; detected_variant_str = "737-900 | SSW"
                else:
                    json_tags.append("BW"); wing_tag_cfg = "BW_L,BW_R"; detected_variant_str = "737-900 | BW (Default)"
             
            elif aircraft_family == "737-600":
                req_tag_model = "b736_ext"
                json_tags.append(""); wing_tag_cfg = "WT_L,WT_R"; detected_variant_str = "737-600 (Default)"

            elif aircraft_family == "737":
                req_tag_model = "b738_ext"
                if model_val == "BW": json_tags.append("BW"); wing_tag_cfg = "BW_L,BW_R"; detected_variant_str = "737-800 | BW"
                elif model_val == "SSW": json_tags.append("SSW"); wing_tag_cfg = "SSW_L,SSW_R"; detected_variant_str = "737-800 | SSW"
                elif model_val == "BCFBW": json_tags.append("BCF"); json_tags.append("BW"); req_tag_model = "b738bcf_ext"; wing_tag_cfg = "BW_L,BW_R"; detected_variant_str = "737-800 BCF | BW"
                elif model_val == "BCFSSW": json_tags.append("BCF"); json_tags.append("SSW"); req_tag_model = "b738bcf_ext"; wing_tag_cfg = "SSW_L,SSW_R"; detected_variant_str = "737-800 BCF | SSW"
                elif model_val == "BDSFBW": json_tags.append("BDSF"); json_tags.append("BW"); req_tag_model = "b738bdsf_ext"; wing_tag_cfg = "BW_L,BW_R"; detected_variant_str = "737-800 BDSF | BW"
                elif model_val == "BDSFSSW": json_tags.append("BDSF"); json_tags.append("SSW"); req_tag_model = "b738bdsf_ext"; wing_tag_cfg = "SSW_L,SSW_R"; detected_variant_str = "737-800 BDSF | SSW"
                elif model_val == "BBJ2BW": json_tags.append("BBJ2"); json_tags.append("BW"); req_tag_model = "b73bbj2_ext"; wing_tag_cfg = "BW_L,BW_R"; detected_variant_str = "737-800 BBJ2 | BW"
                elif model_val == "BBJ2SSW": json_tags.append("BBJ2"); json_tags.append("SSW"); req_tag_model = "b73bbj2_ext"; wing_tag_cfg = "SSW_L,SSW_R"; detected_variant_str = "737-800 BBJ2 | SSW"
                else: json_tags.append("BW"); wing_tag_cfg = "BW_L,BW_R"; detected_variant_str = "737-800 | BW (Default)"
             
            if not wing_tag_cfg: 
                wing_tag_cfg = "" 
             
            tags_final = f"{req_tag_model},{wing_tag_cfg}" if wing_tag_cfg else req_tag_model

            log_gui(f"[AUTO] Config Variant: {detected_variant_str}")

            with open(os.path.join(final_plane_path, "livery.json"), "w", encoding="utf-8") as f:
                json.dump({"rev": 2, "productId": 212, "title": clean_title, "airline": atc_airline, "airlineIcao": atc_airline, 
                           "registration": atc_id, "liveryId": target_folder_name, "version": 1002, "tags": json_tags}, f, indent=2)

            with open(os.path.join(final_plane_path, "livery.cfg"), "w", encoding="utf-8") as f:
                f.write(f"[Version]\nmajor=1\nminor=2\n[Selection]\nrequired_tags={tags_final}\n[GENERAL]\nname={clean_title}\natc_airline={atc_airline}\nicao_airline={atc_airline}\nui_variation={clean_title}\n[FLTSIM]\natc_id={atc_id}\n")

            if target_ini_path and atc_id:
                new_ini_path = os.path.join(final_plane_path, f"{atc_id}.ini")
                if os.path.exists(new_ini_path): os.remove(new_ini_path)
                os.rename(target_ini_path, new_ini_path)
             
            os.remove(cfg_path)
         
        # 9. MANIFEST & LAYOUT
        log_gui("[PHASE 6] Manifest & Layout...")
        drive = os.path.splitdrive(os.path.abspath(BASE_DIR))[0] or "C:"
        temp_short_path = os.path.normpath(f"{drive}/pmdg_tmp_gen")
        if os.path.exists(temp_short_path): shutil.rmtree(temp_short_path)

        try:
            shutil.move(community_root_path, temp_short_path)
        except Exception as e: return log_gui(f"[ERROR] Move to temp failed: {e}")

        try:
            m_title = "PMDG 738 Livery" if aircraft_family == "737" else "PMDG 777 Livery"
             
            manifest_path = os.path.join(temp_short_path, "manifest.json")
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump({"dependencies": [], "content_type": "AIRCRAFT", "title": m_title, "manufacturer": "PMDG", "creator": "PMDG Installer", "package_version": "1.0.0", "minimum_game_version": "1.0.0"}, f, indent=4)
                f.flush()
                os.fsync(f.fileno())

            layout_path = os.path.join(temp_short_path, "layout.json")
            with open(layout_path, "w", encoding="utf-8") as f:
                json.dump({"content": []}, f)
                f.flush()
                os.fsync(f.fileno())
             
            local_exe_path = os.path.join(temp_short_path, "MSFSLayoutGenerator.exe")
            shutil.copy2(layout_gen_original, local_exe_path)
             
            local_exe_win = os.path.abspath(local_exe_path).replace("/", "\\")
            cwd_win = os.path.abspath(temp_short_path).replace("/", "\\")
             
            subprocess.run([local_exe_win, "layout.json"], cwd=cwd_win, check=True, startupinfo=si)
             
            try: os.remove(local_exe_path)
            except: pass
        finally:
            log_gui(" > Moving back to Community...")
            time.sleep(1) 
            if os.path.exists(temp_short_path):
                if os.path.exists(community_root_path): shutil.rmtree(community_root_path)
                shutil.move(temp_short_path, community_root_path)

        # 10. WASM COPY
        wasm_dest_dir = ""
        if platform_version == "Steam": 
            wasm_dest_dir = os.path.join(os.getenv('APPDATA'), "Microsoft Flight Simulator 2024", "WASM", "MSFS2024", target_wasm_subpath, "work", "Aircraft")
        else: 
            wasm_dest_dir = os.path.join(os.getenv('LOCALAPPDATA'), "Packages", "Microsoft.Limitless_8wekyb3d8bbwe", "LocalState", "WASM", "MSFS2024", target_wasm_subpath, "work", "Aircraft")
         
        if new_ini_path and os.path.exists(new_ini_path):
            os.makedirs(wasm_dest_dir, exist_ok=True)
            shutil.copy2(new_ini_path, os.path.join(wasm_dest_dir, os.path.basename(new_ini_path)))

        if count > 0:
            log_gui(f"[SUCCESS] Installation Complete.")
            entry_ptp_path.delete(0, tk.END)
            entry_commons_path.delete(0, tk.END)
            messagebox.showinfo("Installation Report", f"Livery Installed Successfully!\n\nFolder Name:\n{target_folder_name}\n\nAircraft:\n{detected_base_container}\n\nVariant Config:\n{detected_variant_str}")
        else:
            log_gui("[ERROR] No KTX2 files generated.")

    except Exception as e:
        log_gui(f"[EXCEPTION] {str(e)}")
        import traceback; traceback.print_exc()
    finally:
        try:
            if temp_extract and os.path.exists(temp_extract): shutil.rmtree(temp_extract, ignore_errors=True)
            if temp_build and os.path.exists(temp_build): shutil.rmtree(temp_build, ignore_errors=True)
            if temp_thumb_safe and os.path.exists(temp_thumb_safe): shutil.rmtree(temp_thumb_safe, ignore_errors=True)
            if temp_short_path and os.path.exists(temp_short_path): shutil.rmtree(temp_short_path, ignore_errors=True)
            if temp_commons and os.path.exists(temp_commons): shutil.rmtree(temp_commons, ignore_errors=True)
        except: pass
         
        btn_run.config(state=tk.NORMAL, bg=COLOR_GOLD)

def start_thread():
    if not messagebox.askyesno("Confirm Installation", "Note: Converting legacy textures may result in minor quality differences compared to native MSFS 2024 liveries.\n\n"
        "Do you want to proceed with the installation?"): return
    threading.Thread(target=start_conversion_process).start()

def select_source_file():
    if is_folder_mode.get(): target = filedialog.askdirectory(title="Select Livery Folder")
    else: target = filedialog.askopenfilename(filetypes=[("Livery Files", "*.ptp *.zip"), ("PTP Files", "*.ptp"), ("ZIP Files", "*.zip")])
    if target: entry_ptp_path.delete(0, tk.END); entry_ptp_path.insert(0, normalize_path(target))

def select_commons_file():
    if is_folder_mode.get():
        target = filedialog.askdirectory(title="Select Commons Folder")
    else:
        target = filedialog.askopenfilename(filetypes=[("Archives", "*.ptp *.zip"), ("All Files", "*.*")])
    if target: 
        entry_commons_path.delete(0, tk.END)
        entry_commons_path.insert(0, normalize_path(target))

def toggle_fleet_mode():
    if is_fleet_mode.get():
        frame_commons.pack(fill="x", padx=20, pady=(0, 10), after=frame_ptp)
    else:
        frame_commons.pack_forget()

def select_sdk():
    folder = filedialog.askdirectory(title="Select SDK Root")
    if folder: entry_sdk.delete(0, tk.END); entry_sdk.insert(0, normalize_path(folder))

def select_community():
    folder = filedialog.askdirectory(title="Select Community Folder")
    if folder: entry_community.delete(0, tk.END); entry_community.insert(0, normalize_path(folder)); save_user_config()

# --- DROP HANDLER ---
def drop_handler_main(event):
    file_path = event.data
    if file_path.startswith('{') and file_path.endswith('}'): file_path = file_path[1:-1]
    entry_ptp_path.delete(0, tk.END)
    entry_ptp_path.insert(0, normalize_path(file_path))

def drop_handler_commons(event):
    file_path = event.data
    if file_path.startswith('{') and file_path.endswith('}'): file_path = file_path[1:-1]
    entry_commons_path.delete(0, tk.END)
    entry_commons_path.insert(0, normalize_path(file_path))

# --- GUI SETUP ---
if DRAG_DROP_AVAILABLE:
    root = TkinterDnD.Tk() 
else:
    root = tk.Tk()

root.title(f"PMDG Livery Converter from MSFS 2020 to MSFS 2024 - {BRAND_NAME}, {VER_NUM}")
root.geometry("800x750") 
root.configure(bg=COLOR_BG)

# 1. HEADER
frame_header = tk.Frame(root, bg=COLOR_BG)
frame_header.pack(fill="x", padx=20, pady=(20, 10))
tk.Label(frame_header, text=f"PMDG Converter by {BRAND_NAME} | MSFS 2024 ONLY", font=FONT_TITLE, bg=COLOR_BG, fg=COLOR_GOLD).pack(anchor="w")
tk.Label(frame_header, text="Compatible with: PMDG 737 Series (600/800/900/900ER) & 777 Series", font=FONT_MAIN, bg=COLOR_BG, fg=COLOR_TEXT_SECONDARY).pack(anchor="w")

# 2. PTP FILE SECTION
frame_ptp = tk.LabelFrame(root, text=" 1. Source File (Drag & Drop .PTP, .ZIP or Folder here) ", bg=COLOR_BG, fg=COLOR_ACCENT, font=FONT_BOLD, bd=1, relief="solid")
frame_ptp.pack(fill="x", padx=20, pady=10)

tk.Label(frame_ptp, text="File Path:", bg=COLOR_BG, fg=COLOR_TEXT_PRIMARY, font=FONT_MAIN).pack(anchor="w", padx=10, pady=(10,0))
frame_ptp_inner = tk.Frame(frame_ptp, bg=COLOR_BG)
frame_ptp_inner.pack(fill="x", padx=10, pady=5)

entry_ptp_path = tk.Entry(frame_ptp_inner, bg=COLOR_SURFACE, fg=COLOR_TEXT_PRIMARY, insertbackground="white", relief="flat", font=FONT_MAIN)
entry_ptp_path.pack(side=tk.LEFT, fill="x", expand=True, ipady=4, padx=(0, 5))

btn_browse = tk.Button(frame_ptp_inner, text="BROWSE", command=select_source_file, bg=COLOR_ACCENT, fg="white", relief="flat", font=FONT_BOLD, width=10)
btn_browse.pack(side=tk.RIGHT)

is_folder_mode = tk.BooleanVar()
chk_folder = tk.Checkbutton(frame_ptp_inner, text="Folder Mode", variable=is_folder_mode, 
                            bg=COLOR_BG, fg=COLOR_ACCENT, selectcolor=COLOR_BG, 
                            activebackground=COLOR_BG, activeforeground=COLOR_ACCENT, 
                            font=("Segoe UI", 8), cursor="hand2")
chk_folder.pack(side=tk.RIGHT, padx=5)

is_fleet_mode = tk.BooleanVar()
chk_fleet = tk.Checkbutton(frame_ptp, text='Fleet/Pack with "commons" folder/file', variable=is_fleet_mode, command=toggle_fleet_mode,
                           bg=COLOR_BG, fg=COLOR_GOLD, selectcolor=COLOR_BG, activebackground=COLOR_BG, activeforeground=COLOR_GOLD, font=FONT_BOLD, cursor="hand2")
chk_fleet.pack(anchor="w", padx=10, pady=(0, 10))

# Commons Section
frame_commons = tk.LabelFrame(root, text=" 1.5 Commons Source (Merge Textures) ", bg=COLOR_BG, fg=COLOR_GOLD, font=FONT_BOLD, bd=1, relief="solid")

tk.Label(frame_commons, text="Folder/file path for the commons folder:", bg=COLOR_BG, fg=COLOR_TEXT_PRIMARY, font=FONT_MAIN).pack(anchor="w", padx=10, pady=(10,0))
frame_commons_inner = tk.Frame(frame_commons, bg=COLOR_BG)
frame_commons_inner.pack(fill="x", padx=10, pady=5)

entry_commons_path = tk.Entry(frame_commons_inner, bg=COLOR_SURFACE, fg=COLOR_TEXT_PRIMARY, insertbackground="white", relief="flat", font=FONT_MAIN)
entry_commons_path.pack(side=tk.LEFT, fill="x", expand=True, ipady=4, padx=(0, 5))

btn_browse_common = tk.Button(frame_commons_inner, text="BROWSE", command=select_commons_file, bg=COLOR_GOLD, fg="black", relief="flat", font=FONT_BOLD, width=10)
btn_browse_common.pack(side=tk.RIGHT)

if DRAG_DROP_AVAILABLE:
    entry_ptp_path.drop_target_register(DND_FILES)
    entry_ptp_path.dnd_bind('<<Drop>>', drop_handler_main)
    entry_commons_path.drop_target_register(DND_FILES)
    entry_commons_path.dnd_bind('<<Drop>>', drop_handler_commons)

# 2. Installation Path
frame_install = tk.LabelFrame(root, text=" 2. Installation Path (Community) ", bg=COLOR_BG, fg=COLOR_ACCENT, font=FONT_BOLD, bd=1, relief="solid")
frame_install.pack(fill="x", padx=20, pady=10)
frame_inst_inner = tk.Frame(frame_install, bg=COLOR_BG)
frame_inst_inner.pack(fill="x", padx=10, pady=10)
entry_community = tk.Entry(frame_inst_inner, bg=COLOR_SURFACE, fg=COLOR_TEXT_PRIMARY, insertbackground="white", relief="flat", font=FONT_MAIN)
entry_community.pack(side=tk.LEFT, fill="x", expand=True, ipady=4, padx=(0, 5))
tk.Button(frame_inst_inner, text="Change...", command=select_community, bg=COLOR_CARD, fg="white", relief="flat", width=10).pack(side=tk.RIGHT)

# 3. SETTINGS
frame_cfg = tk.LabelFrame(root, text=" 3. Configuration ", bg=COLOR_BG, fg=COLOR_ACCENT, font=FONT_BOLD, bd=1, relief="solid")
frame_cfg.pack(fill="x", padx=20, pady=10)
frame_cfg_grid = tk.Frame(frame_cfg, bg=COLOR_BG)
frame_cfg_grid.pack(fill="x", padx=10, pady=10)

frame_sdk_row = tk.Frame(frame_cfg_grid, bg=COLOR_BG)
frame_sdk_row.grid(row=0, column=1, sticky="w")
tk.Label(frame_cfg_grid, text="SDK 2024 Path:", bg=COLOR_BG, fg=COLOR_TEXT_PRIMARY, font=FONT_MAIN).grid(row=0, column=0, sticky="w", pady=5)
entry_sdk = tk.Entry(frame_sdk_row, bg=COLOR_SURFACE, fg=COLOR_TEXT_PRIMARY, insertbackground="white", relief="flat", font=FONT_MAIN, width=50)
entry_sdk.pack(side=tk.LEFT, ipady=4)
tk.Button(frame_sdk_row, text="...", command=select_sdk, bg=COLOR_CARD, fg="white", relief="flat", width=3).pack(side=tk.LEFT, padx=(2,0))
tk.Label(frame_cfg_grid, text="Simulator Version:", bg=COLOR_BG, fg=COLOR_TEXT_PRIMARY, font=FONT_MAIN).grid(row=1, column=0, sticky="w", pady=5)

platform_var = tk.StringVar(value="Please choose your Sim version") 
platform_var.trace("w", update_community_path_from_platform) 
platform_options = ["Microsoft Store", "Steam"]
opt_platform = tk.OptionMenu(frame_cfg_grid, platform_var, *platform_options)
opt_platform.config(bg=COLOR_SURFACE, fg=COLOR_TEXT_PRIMARY, activebackground=COLOR_ACCENT, activeforeground="white", relief="flat", bd=0, font=FONT_MAIN, highlightthickness=0, anchor="w", width=30) 
opt_platform["menu"].config(bg=COLOR_SURFACE, fg=COLOR_TEXT_PRIMARY, activebackground=COLOR_ACCENT, font=FONT_MAIN, bd=0)
opt_platform.grid(row=1, column=1, sticky="w", padx=0, ipady=2)

# 4. ACTION
btn_run = tk.Button(root, text="CONVERT AND INSTALL LIVERY", command=start_thread, bg=COLOR_GOLD, fg="black", font=("Segoe UI", 11, "bold"), relief="flat", cursor="hand2")
btn_run.pack(fill="x", padx=20, pady=10, ipady=5)

# 5. FOOTER
frame_footer = tk.Frame(root, bg=COLOR_BG)
frame_footer.pack(side=tk.BOTTOM, fill="x", padx=20, pady=15)
lbl_copyright = tk.Label(frame_footer, text=f"@{BRAND_NAME} 2025, {VER_NUM}", bg=COLOR_BG, fg=COLOR_TEXT_SECONDARY, font=("Segoe UI", 8))
lbl_copyright.pack(side=tk.LEFT)

lbl_link = tk.Label(frame_footer, text=FOOTER_LINK_TEXT, bg=COLOR_BG, fg=FOOTER_BTN_COLOR, font=("Segoe UI", 8, "bold"), cursor="hand2")
lbl_link.pack(side=tk.RIGHT)
lbl_link.bind("<Button-1>", open_footer_link)
lbl_link.bind("<Enter>", on_footer_enter)
lbl_link.bind("<Leave>", on_footer_leave)

# 6. LOG FRAME
frame_log_container = tk.Frame(root, bg=COLOR_BG)
frame_log_container.pack(side=tk.BOTTOM, fill="both", expand=True, padx=20, pady=(0, 5))
btn_toggle_log = tk.Button(root, text="Show Debug Log ▼", command=toggle_log, bg=COLOR_SURFACE, fg=COLOR_TEXT_SECONDARY, font=("Segoe UI", 8), relief="flat", bd=0, cursor="hand2")
btn_toggle_log.pack(side=tk.BOTTOM, fill="x", padx=20, pady=(0, 0), before=frame_log_container)
txt_log = scrolledtext.ScrolledText(frame_log_container, height=10, bg=COLOR_SURFACE, fg="#00FF00", font=("Consolas", 9), relief="flat", bd=0)

# --- INITIALIZE ---
found_sdk = detect_automatic_sdk()
if found_sdk:
    entry_sdk.delete(0, tk.END); entry_sdk.insert(0, found_sdk)
    log_gui(f"[AUTO] SDK found at: {found_sdk}")
else:
    log_gui("[AUTO] SDK not found automatically.")
    root.update() 
    if messagebox.askyesno("SDK Not Detected", "SDK not found.\nInstall now?"): run_sdk_installer()
    else: select_sdk()

saved_cfg = load_user_config()

if "platform" in saved_cfg: platform_var.set(saved_cfg["platform"])
if "community_path" in saved_cfg: entry_community.delete(0, tk.END); entry_community.insert(0, saved_cfg["community_path"])

threading.Thread(target=check_for_updates, daemon=True).start()

root.mainloop()