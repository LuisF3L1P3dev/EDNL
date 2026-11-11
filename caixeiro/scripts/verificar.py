"""Executa a suíte e registra a saída completa para a entrega acadêmica."""
import os
from pathlib import Path
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    run = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-v"],
                         cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8")
    texto = f"Python: {platform.python_version()}\nPlataforma: {platform.platform()}\nComando: python -B -m unittest discover -s tests -v\n\n{run.stdout}{run.stderr}"
    (ROOT / "docs/validacao_final.txt").write_text(texto, encoding="utf-8")
    print(run.stderr)
    return run.returncode


if __name__ == "__main__":
    raise SystemExit(main())
