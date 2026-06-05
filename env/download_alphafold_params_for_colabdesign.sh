#!/usr/bin/env bash
set -euo pipefail

# Downloads the AlphaFold parameter archive needed by ColabDesign/AfDesign.
# This is a large download. The extracted files are expected under:
#   ~/fga_model_envs/af_params/params/

PARAM_DIR="${PARAM_DIR:-$HOME/fga_model_envs/af_params}"
PARAM_URL="https://storage.googleapis.com/alphafold/alphafold_params_2022-12-06.tar"
ARCHIVE="$PARAM_DIR/alphafold_params_2022-12-06.tar"

mkdir -p "$PARAM_DIR/params"
cd "$PARAM_DIR"

if [[ ! -f "$ARCHIVE" ]]; then
  if command -v aria2c >/dev/null 2>&1; then
    aria2c -x 16 -s 16 -c -o "$(basename "$ARCHIVE")" "$PARAM_URL"
  else
    wget -c -O "$ARCHIVE" "$PARAM_URL"
  fi
fi

tar -xf "$ARCHIVE" -C "$PARAM_DIR/params"

test -f "$PARAM_DIR/params/params_model_1_ptm.npz"
test -f "$PARAM_DIR/params/params_model_1_multimer_v3.npz"

echo "AlphaFold params ready: $PARAM_DIR"
