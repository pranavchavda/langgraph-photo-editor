#!/bin/bash
# Python bundle startup script for Linux
BUNDLE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export LD_LIBRARY_PATH="${BUNDLE_DIR}/lib:${LD_LIBRARY_PATH}"
export PYTHONPATH="${BUNDLE_DIR}/lib/python3.13/site-packages:${PYTHONPATH}"
exec "${BUNDLE_DIR}/bin/python" "$@"
