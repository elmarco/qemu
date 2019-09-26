#!/bin/sh

REQ="$1"
OUTDIR="$2"
PYTHON="$3"

"$PYTHON" -m venv --system-site-packages "$OUTDIR"

"$OUTDIR/bin/python" -m pip -q install -r "$REQ"
