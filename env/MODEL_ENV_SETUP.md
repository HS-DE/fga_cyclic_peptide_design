# 模型环境安装与运行说明

本文件记录当前项目的专用环境状态，以及需要手动安装的大模型环境。目标是保证基础 pipeline 在当前项目目录内独立运行，同时把 ColabDesign/RFdiffusion/ColabFold/Boltz-2 这类重型工具放到更合适的 GPU/Linux 环境中运行。

## 1. 已完成：项目本地基础环境

已在当前项目目录创建：

```text
.conda/fga-cyclic-design
```

该环境包含基础 pipeline 依赖：

```text
python 3.10
pandas
numpy
biopython
pyyaml
openpyxl
scipy
scikit-learn
pytest
matplotlib
tqdm
```

验证命令：

```powershell
cd C:\Work\SH\高丰度蛋白环肽设计\fga_cyclic_peptide_design
& .\.conda\fga-cyclic-design\python.exe -m pytest -q
& .\.conda\fga-cyclic-design\python.exe run_pipeline.py --config config/project.yaml --mode full
```

当前验证结果：

```text
16 passed
pipeline completed
```

说明：这个环境用于 Excel/FASTA/PDB 准备、patch 选择、job 生成、候选过滤、评分汇总和报告生成。它不包含 ColabDesign、RFdiffusion、ColabFold、Boltz-2。

## 2. 当前机器状态

Windows 侧：

```text
GPU: NVIDIA GeForce RTX 3060 12GB
Docker Desktop: 未运行
```

WSL 侧：

```text
Distro: Ubuntu-22.04
nvidia-smi: 可用
nvcc: 未安装或不在 PATH
python3: 3.10.12
git/curl/wget: 可用
```

`nvidia-smi` 可用说明 WSL 能看到 GPU；`nvcc` 不可用会影响 LocalColabFold 官方安装流程，因为 LocalColabFold README 要求检查 CUDA compiler driver。

## 3. 推荐优先级

第一优先级：ColabDesign-cyclic-binder，用于生成 raw cyclic peptide candidates。

第二优先级：LocalColabFold 或 ColabFold-cycpep-dock，用于复合物预测和 cyclic peptide complex offset 检查。

第三优先级：Boltz-2，可作为复合物预测/交叉验证路线。

第四优先级：RFdiffusion/RFpeptides，可作为增强路线；安装和参数调试成本更高。

## 4. ColabDesign-cyclic-binder 手动运行

官方仓库：

```text
https://github.com/ohuelab/ColabDesign-cyclic-binder
```

该仓库提供 `cyclic_peptide_binder_design.ipynb`，更适合先用 Google Colab 或 Jupyter Notebook 跑通，不建议先在 Windows 本地硬装。

本项目已经准备好输入：

```text
data/structures/prepared/fibrinogen_3GHG_clean.pdb
data/annotations/FGA_epitope_candidates.csv
results/raw_designs/design_jobs.csv
results/raw_designs/colabdesign_jobs/*.sh
```

手动运行时按 `design_jobs.csv` 中每个 patch/length/n_designs 组合运行。真实输出 CSV 放回：

```text
results/raw_designs/colabdesign_outputs/
```

CSV 至少包含：

```text
core_sequence
job_id
patch_id
raw_score
```

建议包含：

```text
raw_id
method
target_region
notes
```

放回后运行：

```powershell
& .\.conda\fga-cyclic-design\python.exe scripts/07_collect_raw_designs.py --config config/project.yaml
& .\.conda\fga-cyclic-design\python.exe scripts/08_filter_sequences.py --config config/project.yaml
& .\.conda\fga-cyclic-design\python.exe scripts/09_prepare_complex_prediction_jobs.py --config config/project.yaml
```

## 5. LocalColabFold 手动安装路线

官方仓库：

```text
https://github.com/YoshitakaMo/localcolabfold
```

官方 README 当前推荐 `pixi install && pixi run setup`，并说明 `colabfold_batch` 能自动判断 monomer/complex，complex 输入可用 `TARGET:PEPTIDE`。

### 5.1 推荐装在 WSL Linux 文件系统

由于项目目录在 `/mnt/c/...`，Windows 文件系统上的符号链接和大小写敏感可能影响 Python/JAX/ColabFold 安装。更稳妥做法是把大模型工具装在 WSL home 下，然后读写本项目输入输出。

WSL 中运行：

```bash
mkdir -p ~/fga_model_envs
cd ~/fga_model_envs
curl -fsSL https://pixi.sh/install.sh | sh
source ~/.bashrc
git clone https://github.com/YoshitakaMo/localcolabfold.git
cd localcolabfold
pixi install && pixi run setup
```

验证：

```bash
~/fga_model_envs/localcolabfold/.pixi/envs/default/bin/colabfold_batch --help
```

如果提示缺 `nvcc`，需要先在 WSL 安装 CUDA Toolkit，让 `nvcc --version` 可用。当前 WSL 只有 `nvidia-smi` 可用，尚未发现 `nvcc`。

### 5.2 如果坚持装在当前项目目录

先在 Windows PowerShell 中启用大小写敏感目录：

```powershell
cd C:\Work\SH\高丰度蛋白环肽设计\fga_cyclic_peptide_design
mkdir external_tools
fsutil file SetCaseSensitiveInfo .\external_tools enable
```

然后在 WSL 中运行：

```bash
cd "/mnt/c/Work/SH/高丰度蛋白环肽设计/fga_cyclic_peptide_design/external_tools"
curl -fsSL https://pixi.sh/install.sh | sh
source ~/.bashrc
git clone https://github.com/YoshitakaMo/localcolabfold.git
cd localcolabfold
pixi install && pixi run setup
```

这条路线可能受 Windows 文件系统和中文路径影响；如果出错，改用 5.1。

## 6. ColabFold-cycpep-dock 可选路线

官方仓库：

```text
https://github.com/ohuelab/ColabFold-cycpep-dock
```

该仓库针对 protein-cyclic peptide complex prediction，并说明输入格式可用：

```text
TARGETPROTEINSEQ:CYCLICPEPTIDESEQ
```

且需要设置 cyclic 选项。它更贴近本项目的 Cys-Cys cyclic peptide complex 预测需求，但安装和使用需要按该仓库 notebook/脚本调整。

## 7. Boltz-2 手动安装路线

官方仓库：

```text
https://github.com/jwohlwend/boltz
```

Boltz 文档中的预测命令形式：

```bash
boltz predict <INPUT_PATH> [OPTIONS]
```

常用选项包括：

```bash
--use_msa_server
--use_potentials
--out_dir <OUTPUT_DIR>
```

建议在 WSL 中单独创建环境，不装进基础 pipeline 环境：

```bash
cd "/mnt/c/Work/SH/高丰度蛋白环肽设计/fga_cyclic_peptide_design"
mkdir -p external_tools/boltz2
cd external_tools/boltz2
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install "boltz[cuda]" -U
boltz --help
```

如果 CUDA kernel 或 PyTorch CUDA 安装失败，优先改用 Linux/云 GPU/Colab。Boltz 适合后续做复合物预测交叉验证，不是第一步候选生成器。

## 8. RFdiffusion/RFpeptides 手动安装路线

官方仓库：

```text
https://github.com/RosettaCommons/RFdiffusion
```

官方 README 提供两类路线：

1. 本地 conda 安装，需要下载 model weights，并按 CUDA/PyTorch 版本调环境。
2. Docker 路线，官方 README 提供 Dockerfile 和 `docker run --gpus all` 示例。

当前 Windows Docker Desktop 未运行；若采用 Docker，请先启动 Docker Desktop，并确认：

```powershell
docker info
docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
```

然后按 RFdiffusion README 的 Docker 方式构建/运行。RFdiffusion/RFpeptides 是备用路线，建议在 ColabDesign-cyclic-binder 跑通后再尝试。

## 9. 复合物预测结果回填格式

无论用 LocalColabFold、ColabFold-cycpep-dock 还是 Boltz-2，最终需要整理成：

```text
results/complex_predictions/manual_complex_prediction_summary.csv
```

字段：

```text
peptide_id
core_sequence
patch_id
n_seeds
best_seed
mean_iptm
best_iptm
mean_interface_pae
best_interface_pae
mean_peptide_plddt
interface_contacts
pose_consistency_rmsd
patch_consistency_flag
cys_cys_geometry
notes
```

之后运行：

```powershell
& .\.conda\fga-cyclic-design\python.exe scripts/10_score_complex_predictions.py --config config/project.yaml
& .\.conda\fga-cyclic-design\python.exe scripts/11_negative_screen.py --config config/project.yaml
& .\.conda\fga-cyclic-design\python.exe scripts/12_rank_candidates.py --config config/project.yaml
& .\.conda\fga-cyclic-design\python.exe scripts/13_export_final_report.py --config config/project.yaml
```

## 10. 当前不可跳过的原则

没有真实 ColabDesign/RFdiffusion 生成结果时，不生成真实候选。

没有真实复合物预测或 docking 评分时，不生成可用于合成的 top10。

`results/raw_designs/FGA_raw_candidates.demo.csv` 永远不能进入 final 表。

## 11. 2026-05-27 当前 WSL 安装状态

用户已在 WSL `Ubuntu-22.04` 中完成并验证：

```text
nvcc: CUDA 12.6, V12.6.85
nvidia-smi: RTX 3060 12GB 可见
pixi: 0.69.0
LocalColabFold: colabfold_batch --help 可用
ColabDesign-cyclic-binder: 已安装到 LocalColabFold pixi Python 环境
JAX backend: gpu
JAX device: CudaDevice(id=0)
```

下一步必须下载 AlphaFold 参数包，ColabDesign/AfDesign 才能真正运行：

```bash
cd "/mnt/c/Work/SH/高丰度蛋白环肽设计/fga_cyclic_peptide_design"
bash env/download_alphafold_params_for_colabdesign.sh
```

参数默认安装到：

```text
~/fga_model_envs/af_params/params/
```

参数包就绪后，先只跑 smoke test：

```bash
cd "/mnt/c/Work/SH/高丰度蛋白环肽设计/fga_cyclic_peptide_design"
bash results/raw_designs/colabdesign_jobs/Patch_B_L10_smoke_test_wsl.sh
```

smoke test 只用于验证 ColabDesign 调用链，不作为正式最终候选输出。

smoke test 输出位于：

```text
results/raw_designs/smoke_tests/Patch_B_L10_smoke/
```

该目录不会被 `07_collect_raw_designs.py` 自动收集。

如 smoke test 在 `Stage 1` 出现 `Segmentation fault`，优先按以下方式处理：

1. 在 Windows PowerShell 中释放 WSL/GPU 残留状态：

```powershell
wsl --shutdown
```

2. 重新打开 WSL 后检查空闲显存：

```bash
nvidia-smi
```

3. 再运行 smoke test：

```bash
cd "/mnt/c/Work/SH/高丰度蛋白环肽设计/fga_cyclic_peptide_design"
bash results/raw_designs/colabdesign_jobs/Patch_B_L10_smoke_test_wsl.sh
```

当前 smoke test 已改为只裁剪 chain A 27-43 的小靶标，并设置更保守的 JAX 显存分配变量；这只是环境验证，不作为正式设计输入。
