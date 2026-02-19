import PyInstaller.__main__
import os
import sys


SCRIPT_PRINCIPAL = "main.py" 
NOMBRE_EXE = "Livery_Installer_Converter_PMDG.exe"
ICONO = "ico.ico"
VERSION_FILE = "version_info.txt"

BASE_PATH = os.path.dirname(os.path.abspath(__file__))

DATAS = [
    # Solo los datos de configuración internos
    (os.path.join(BASE_PATH, "MSFS24_Data"), "MSFS24_Data"),
]

BINARIES = [
    (os.path.join(BASE_PATH, "ptp_converter", "ptp_converter.exe"), "ptp_converter"),
    (os.path.join(BASE_PATH, "required", "texconv.exe"), "required"),
    (os.path.join(BASE_PATH, "tcl86t.dll"), "."),
    (os.path.join(BASE_PATH, "tk86t.dll"), "."),
]

EXTERNAL_FOLDERS = [
    "SDK Install" 
]

def check_integrity():
    print("--- Verificando archivos ---")
    missing = []

    if not os.path.exists(os.path.join(BASE_PATH, SCRIPT_PRINCIPAL)):
        missing.append(f"SCRIPT: {SCRIPT_PRINCIPAL}")

    for src, _ in DATAS:
        if not os.path.exists(src): missing.append(f"DATA FALTANTE: {src}")
    
    for src, _ in BINARIES:
        if "ptp_converter" in src or "texconv" in src:
            if not os.path.exists(src): missing.append(f"EXE CRITICO FALTANTE: {src}")

    if missing:
        print("\n[ERROR CRÍTICO] Faltan archivos para compilar:")
        for m in missing: print(f" - {m}")
        input("Presiona ENTER para salir...")
        sys.exit(1)

    print("\n--- Verificando archivos externos (para el ZIP) ---")
    for folder in EXTERNAL_FOLDERS:
        path = os.path.join(BASE_PATH, folder)
        if os.path.exists(path):
            print(f"[OK] '{folder}' encontrado. (Recuerda incluirlo en tu ZIP)")
        else:
            print(f"[AVISO] '{folder}' NO encontrado. El .exe compilará, pero fallará al intentar instalar el SDK si no incluyes esta carpeta en el ZIP.")

    print("\nIntegridad verificada. Iniciando compilación...\n")

def build():
    check_integrity()

    # Nota: No agregamos EXTERNAL_FOLDERS a 'args' para que queden fuera.
    args = [
        os.path.join(BASE_PATH, SCRIPT_PRINCIPAL),
        f'--name={NOMBRE_EXE}',
        '--noconfirm',
        '--onefile',
        '--windowed',
        '--clean',
        f'--collect-all=tkinterdnd2',  # <--- ¡ESTA ES LA LÍNEA QUE FALTABA!
    ]

    if os.path.exists(os.path.join(BASE_PATH, ICONO)):
        args.append(f'--icon={os.path.join(BASE_PATH, ICONO)}')

    if os.path.exists(os.path.join(BASE_PATH, VERSION_FILE)):
        args.append(f'--version-file={os.path.join(BASE_PATH, VERSION_FILE)}')

    sep = ';' if os.name == 'nt' else ':'
    
    for src, dest in DATAS:
        args.append(f'--add-data={src}{sep}{dest}')

    for src, dest in BINARIES:
        if os.path.exists(src):
            args.append(f'--add-binary={src}{sep}{dest}')

    try:
        PyInstaller.__main__.run(args)
        print("\n" + "="*40)
        print(" COMPILACIÓN EXITOSA")
        print("="*40)
        dist_path = os.path.join(BASE_PATH, 'dist')
        print(f"Ejecutable: {os.path.join(dist_path, NOMBRE_EXE + '.exe')}")
        print("IMPORTANTE: Copia la carpeta 'SDK Install' al lado del .exe antes de distribuir.")
        
        os.startfile(dist_path)
        
    except Exception as e:
        print(f"\n[ERROR FATAL] {e}")

if __name__ == "__main__":
    build()
    input("\nPresiona ENTER para cerrar...")