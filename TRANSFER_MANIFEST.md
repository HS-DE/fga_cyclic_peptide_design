# FGA cyclic peptide design transfer manifest

Generated: 2026-05-27

This manifest describes how to move the project to another machine without exporting the whole WSL distribution.

## Transfer artifacts

The transfer folder is expected to contain:

```text
fga_cyclic_peptide_design_project_20260527_174109.zip
fga_model_sources_without_env_20260527_174109.tgz
alphafold_params_2022-12-06.tar
```

`fga_cyclic_peptide_design_project_*.zip` contains this project, excluding local caches and the local `.conda` environment.

`fga_model_sources_without_env_*.tgz` contains source trees for:

```text
localcolabfold/
ColabDesign-cyclic-binder/
```

It intentionally excludes `.pixi` and `.git` directories. Rebuild the model environment on the new machine.

`alphafold_params_2022-12-06.tar` is the reusable AlphaFold parameter archive downloaded from Google storage. It avoids downloading the 5.2 GB file again.

## Environment exports included in project

```text
env/exports/windows_conda_env_export_no_builds.yml
env/exports/windows_conda_env_explicit.txt
env/exports/windows_pip_freeze.txt
env/exports/windows_python_info.txt
env/exports/wsl_model_env/cuda_gpu_check.txt
env/exports/wsl_model_env/pixi_version.txt
env/exports/wsl_model_env/localcolabfold_pixi.lock
env/exports/wsl_model_env/localcolabfold_pyproject.toml
env/exports/wsl_model_env/localcolabfold_pixi_list.txt
env/exports/wsl_model_env/localcolabfold_pip_freeze.txt
env/exports/wsl_model_env/localcolabfold_git_state.txt
env/exports/wsl_model_env/colabdesign_setup.py
env/exports/wsl_model_env/colabdesign_git_state.txt
env/exports/wsl_model_env/alphafold_params_manifest.txt
```

## Restore project on new Windows machine

Unzip the project to a stable path. Keeping the same path reduces path edits:

```text
C:\Work\SH\高丰度蛋白环肽设计\fga_cyclic_peptide_design
```

Recreate the lightweight project environment:

```powershell
cd C:\Work\SH\高丰度蛋白环肽设计\fga_cyclic_peptide_design
conda env create -p .\.conda\fga-cyclic-design -f env\environment.yml
.\.conda\fga-cyclic-design\python.exe -m pytest -q
.\.conda\fga-cyclic-design\python.exe run_pipeline.py --config config/project.yaml --mode full
```

For a closer Windows package match, inspect:

```text
env/exports/windows_conda_env_explicit.txt
```

## Restore WSL model assets on new machine

Install and verify WSL GPU basics first:

```bash
nvcc --version
nvidia-smi
pixi --version
```

Restore source trees:

```bash
mkdir -p ~/fga_model_envs
tar -xzf /mnt/c/Work/SH/fga_transfer_20260527_174109/fga_model_sources_without_env_20260527_174109.tgz -C ~/fga_model_envs
```

Rebuild LocalColabFold:

```bash
cd ~/fga_model_envs/localcolabfold
pixi install && pixi run setup
pixi add pip
```

Install ColabDesign-cyclic-binder into the LocalColabFold pixi Python:

```bash
cd ~/fga_model_envs/ColabDesign-cyclic-binder
LCF_PY=~/fga_model_envs/localcolabfold/.pixi/envs/default/bin/python

cat > /tmp/colabdesign-constraints.txt <<'EOF'
jax==0.5.3
jaxlib==0.5.3
EOF

$LCF_PY -m pip install -e . -c /tmp/colabdesign-constraints.txt
```

Restore AlphaFold parameters:

```bash
mkdir -p ~/fga_model_envs/af_params/params
cp /mnt/c/Work/SH/fga_transfer_20260527_174109/alphafold_params_2022-12-06.tar ~/fga_model_envs/af_params/
tar -xf ~/fga_model_envs/af_params/alphafold_params_2022-12-06.tar -C ~/fga_model_envs/af_params/params
```

Verify ColabDesign GPU import:

```bash
LCF_PY=~/fga_model_envs/localcolabfold/.pixi/envs/default/bin/python
$LCF_PY - <<'PY'
import jax
import jaxlib
import colabdesign
from colabdesign.af import mk_afdesign_model
print("jax:", jax.__version__)
print("jaxlib:", jaxlib.__version__)
print("backend:", jax.default_backend())
print("devices:", jax.devices())
print("colabdesign:", colabdesign.__file__)
print("mk_afdesign_model: OK")
PY
```

## Current modeling status

No real final peptide candidates have been generated.

The current machine successfully installed CUDA, pixi, LocalColabFold, ColabDesign-cyclic-binder, and AlphaFold parameters, but ColabDesign smoke testing segfaulted during JAX/XLA optimization while GPU memory was heavily occupied by Windows graphics processes. The transfer package preserves project state and environment records; model generation should be retried on the new machine.

Do not use files under `results/raw_designs/smoke_tests/` as final candidates. They are environment checks only and are not collected by `07_collect_raw_designs.py`.
