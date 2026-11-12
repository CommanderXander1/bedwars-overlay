#!/bin/sh

MAIN_SCRIPT="main.py"
VENV_DIR=".venv"
REQ_FILE="requirements.txt"

TOTAL_STEPS=5

if [ -t 1 ]; then
    GREEN=$(printf '\033[32m'); RED=$(printf '\033[31m')
    YELLOW=$(printf '\033[33m'); CYAN=$(printf '\033[36m')
    BOLD=$(printf '\033[1m'); RESET=$(printf '\033[0m')
else
    GREEN=""; RED=""; YELLOW=""; CYAN=""; BOLD=""; RESET=""
fi

ok()   { printf '  %s✓%s %s\n' "$GREEN" "$RESET" "$1"; }
work() { printf '  %s…%s %s\n' "$YELLOW" "$RESET" "$1"; }
skip() { printf '  %s–%s %s\n' "$YELLOW" "$RESET" "$1"; }
warn() { printf '  %s!%s %s\n' "$YELLOW" "$RESET" "$1"; }
fail() { printf '  %s✗%s %s\n' "$RED" "$RESET" "$1"; }

step() {
    n=$1; title=$2
    filled=$((n * 20 / TOTAL_STEPS))
    empty=$((20 - filled))
    bar=""; i=0
    while [ "$i" -lt "$filled" ]; do bar="${bar}█"; i=$((i + 1)); done
    i=0
    while [ "$i" -lt "$empty" ]; do bar="${bar}░"; i=$((i + 1)); done
    printf '\n%s%s%s  Step %s/%s: %s%s%s\n' "$CYAN" "$bar" "$RESET" "$n" "$TOTAL_STEPS" "$BOLD" "$title" "$RESET"
}

is_supported() {
    "$1" -c 'import sys; sys.exit(0 if (3, 12) <= sys.version_info[:2] <= (3, 13) else 1)' >/dev/null 2>&1
}

cd "$(dirname "$0")" || exit 1

echo "========================================"
echo "  Overlay Launcher - by Xander"
echo "========================================"

step 1 "Checking Python 3.12 / 3.13"
PY_CMD=""
for candidate in python3.13 python3.12 python3 python; do
    if command -v "$candidate" >/dev/null 2>&1 && is_supported "$candidate"; then
        PY_CMD="$candidate"
        break
    fi
done

if [ -z "$PY_CMD" ]; then
    fail "Python 3.12 or 3.13 was not found."
    echo
    echo "  This program only supports Python 3.12 and 3.13."
    case "$(uname -s)" in
        Darwin)
            echo "  Install it with Homebrew:  brew install python@3.13"
            echo "  or download it from:       https://www.python.org/downloads/"
            ;;
        *)
            echo "  Install it with your package manager, for example:"
            echo "    Ubuntu 24.04:  sudo apt install python3.12 python3.12-venv"
            echo "    Fedora:        sudo dnf install python3.13"
            echo "    Any distro:    pyenv install 3.13"
            ;;
    esac
    echo "  Then run this script again."
    echo
    exit 1
fi
PY_VER=$($PY_CMD --version 2>&1)
ok "Compatible Python installed ($PY_VER)"

step 2 "Checking virtual environment"
if [ -x "$VENV_DIR/bin/python" ] && is_supported "$VENV_DIR/bin/python"; then
    ok "Virtual environment present ($VENV_DIR)"
else
    if [ -e "$VENV_DIR" ]; then
        warn "Existing venv is broken or uses an unsupported Python version, rebuilding it..."
        rm -rf "$VENV_DIR"
    fi
    work "Creating \"$VENV_DIR\" with $PY_VER..."
    if ! $PY_CMD -m venv "$VENV_DIR"; then
        rm -rf "$VENV_DIR"
        fail "Failed to create the virtual environment."
        echo "  On Debian/Ubuntu you may need:  sudo apt install python3-venv"
        exit 1
    fi
    ok "Virtual environment created"
fi

step 3 "Activating virtual environment"
if ! . "$VENV_DIR/bin/activate"; then
    fail "Failed to activate the virtual environment."
    exit 1
fi
ok "Virtual environment activated"

step 4 "Checking requirements"
if [ ! -f "$REQ_FILE" ]; then
    skip "$REQ_FILE not found, skipping"
else
    work "Verifying packages, installing any that are missing..."
    if ! python -m pip install -q --disable-pip-version-check -r "$REQ_FILE"; then
        fail "Failed to install requirements."
        exit 1
    fi
    ok "All requirements installed"
fi

step 5 "Starting program"
if [ ! -f "$MAIN_SCRIPT" ]; then
    fail "Could not find $MAIN_SCRIPT in $(pwd)"
    exit 1
fi

ok "Launching $MAIN_SCRIPT"
echo "----------------------------------------"
echo
python "$MAIN_SCRIPT" "$@"
EXIT_CODE=$?
echo
echo "----------------------------------------"

if [ "$EXIT_CODE" -ne 0 ]; then
    printf '  %s!%s Program exited with code %s.\n' "$YELLOW" "$RESET" "$EXIT_CODE"
fi

exit "$EXIT_CODE"
