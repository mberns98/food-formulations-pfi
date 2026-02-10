import subprocess
import sys
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

INSERT_DIR = BASE_DIR / "data_engineering" / "insert" / "historical"

def run_script(script_path):
    """Ejecuta un script de Python y captura su salida."""
    print(f"🏃 Ejecutando: {script_path.name}...")
    
    result = subprocess.run(
        [sys.executable, str(script_path)], 
        capture_output=True, 
        text=True,
        encoding='utf-8',
        env=dict(os.environ, PYTHONUTF8="1")
    )
    
    if result.returncode == 0:
        if result.stdout:
            print(result.stdout.strip())
        return True
    else:
        print(f"❌ Error crítico en {script_path.name}:")
        print("-" * 30)
        print(result.stderr)
        print("-" * 30)
        return False

def main():
    scripts = sorted(list(INSERT_DIR.glob("*.py")))
    
    if not scripts:
        print(f"⚠️ No se encontraron scripts .py en {INSERT_DIR}")
        return

    print("🚀 Iniciando Pipeline de Carga Histórica (model Schema)")
    print(f"📂 Carpeta de origen: {INSERT_DIR}\n")

    for script in scripts:
        success = run_script(script)
        if not success:
            print("\n🛑 Pipeline interrumpido debido a un error. Revisa los logs arriba.")
            sys.exit(1)

    print("\n" + "="*40)
    print("🏆 ¡PIPELINE COMPLETADO EXITOSAMENTE!")
    print("El Data Warehouse (model Layer) está totalmente poblado.")
    print("="*40)

if __name__ == "__main__":
    main()