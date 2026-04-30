import shutil
import subprocess
from pathlib import Path


def try_execute_r(script_path: Path, workdir: Path, rscript_executable: str | None = None) -> dict:
    rscript = rscript_executable or shutil.which("Rscript")
    if not rscript:
        return {"engine": "R", "ran": False, "status": "skipped", "message": "Rscript not found"}
    try:
        proc = subprocess.run(
            [rscript, str(script_path)],
            cwd=str(workdir),
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        return {"engine": "R", "ran": True, "status": "timeout", "message": "R execution timed out (120s)"}
    return {
        "engine": "R",
        "ran": True,
        "status": "ok" if proc.returncode == 0 else "error",
        "returncode": proc.returncode,
        "stdout": proc.stdout[-3000:],
        "stderr": proc.stderr[-3000:],
    }


def try_execute_sas(script_path: Path, workdir: Path, sas_executable: str | None = None) -> dict:
    sas_cmd = sas_executable or shutil.which("sas")
    if not sas_cmd:
        return {"engine": "SAS", "ran": False, "status": "skipped", "message": "SAS executable not found"}
    try:
        proc = subprocess.run(
            [sas_cmd, str(script_path)],
            cwd=str(workdir),
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        return {"engine": "SAS", "ran": True, "status": "timeout", "message": "SAS execution timed out (120s)"}
    return {
        "engine": "SAS",
        "ran": True,
        "status": "ok" if proc.returncode == 0 else "error",
        "returncode": proc.returncode,
        "stdout": proc.stdout[-3000:],
        "stderr": proc.stderr[-3000:],
    }
