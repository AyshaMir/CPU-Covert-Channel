#!/usr/bin/env bash
set -euo pipefail
curl -sS https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
python3 /tmp/get-pip.py --user
export PATH="$HOME/.local/bin:$PATH"
python3 -m pip install --user matplotlib
python3 -c 'import matplotlib; print("matplotlib", matplotlib.__version__)'