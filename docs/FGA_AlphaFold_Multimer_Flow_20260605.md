# FGA 环肽候选的 AlphaFold-Multimer 交叉验证流程

更新时间：2026-06-05

本文档记录当前项目中使用 LocalColabFold/AlphaFold-Multimer 对 FGA 环肽候选进行复合物结构预测和评分的完整流程。这个流程是 Boltz2 之后的第二模型交叉验证分支，目标是判断候选肽是否在另一个结构预测模型下也表现出可信的 FGA 结合姿态。

重要说明：本流程输出的是“复合物预测与打分结果”，不是最终可合成候选。任何候选都不能仅凭 AlphaFold-Multimer 通过就称为最终结果；仍需经过候选生成、硬过滤、复合物预测/评分、负筛、最终排序和人工复核。

## 1. 这一步在整个项目中的位置

当前项目主线可以理解为：

1. 从 FGA 序列和 3GHG 结构中确定可设计区域和表面 patch。
2. 用 ColabDesign 生成 Cys-Cys 环化肽候选序列。
3. 对候选进行序列硬过滤。
4. 用结构预测模型预测“FGA + 环肽”的复合物构象。
5. 解析复合物输出，计算 ipTM、pLDDT、PAE、patch 接触、Cys-Cys 几何等指标。
6. 做负筛和最终排序。

Boltz2 分支已经跑过一轮筛选，结果整体偏负面。因此现在用 AlphaFold-Multimer 再做一轮交叉验证，重点看是否有候选在另一个模型下显示更可信的复合物界面。

## 2. 本轮 AlphaFold-Multimer 的输入

当前优先验证的是 Boltz2 MSA/server top30 中的 30 条候选：

```text
results/boltz_predictions_raw3ghg_template_msa_top30/boltz_jobs.csv
```

AlphaFold-Multimer job 生成后写入：

```text
results/colabfold_predictions_top30_seed1/colabfold_jobs.csv
```

每个 job 的输入 FASTA 是一个二链复合物：

```text
FGA_chain_36_866:候选环肽序列
```

也就是说，AlphaFold-Multimer 预测的是：

```text
FGA 可见/结构域序列 + 一个候选环肽
```

不是单独预测肽段结构。

## 3. 环境和权重检查

AlphaFold-Multimer 通过 LocalColabFold 调用。当前环境路径应为：

```text
~/fga_model_envs/localcolabfold/.pixi/envs/default
```

AlphaFold 参数目录应为：

```text
~/fga_model_envs/af_params/params
```

检查命令：

```bash
cd /mnt/c/SH/fga_cyclic_peptide_design

export LCF_HOME="$HOME/fga_model_envs/localcolabfold"
export LCF_PY="$LCF_HOME/.pixi/envs/default/bin/python"
export PATH="$LCF_HOME/.pixi/envs/default/bin:$PATH"
export AF_PARAMS="$HOME/fga_model_envs/af_params"

which python
which colabfold_batch

python - <<'PY'
import jax
print("backend:", jax.default_backend())
print("devices:", jax.devices())
PY

ls -lh "$AF_PARAMS/params"/params_model_*_multimer_v3.npz
ls -lh "$AF_PARAMS/params/download_complexes_multimer_v3_finished.txt"
```

预期结果：

```text
which python -> /home/luomi/fga_model_envs/localcolabfold/.pixi/envs/default/bin/python
which colabfold_batch -> /home/luomi/fga_model_envs/localcolabfold/.pixi/envs/default/bin/colabfold_batch
backend: gpu
devices: [CudaDevice(id=0), CudaDevice(id=1)]
```

如果 `params_model_*_multimer_v3.npz` 不存在，或者文件大小异常，需要先重新解压官方参数包。

## 4. 生成 AlphaFold-Multimer job

这一步只生成 job CSV 和 FASTA 输入，不跑 GPU。

建议在 PowerShell 里执行：

```powershell
cd C:\SH\fga_cyclic_peptide_design

.\.conda\fga-cyclic-design\python.exe scripts\16_prepare_colabfold_prediction_jobs.py `
  --config config\project.yaml `
  --candidate-csv results\boltz_predictions_raw3ghg_template_msa_top30\boltz_jobs.csv `
  --output-root results\colabfold_predictions_top30_seed1 `
  --target-fasta data\input\FGA_chain_36_866.fasta `
  --seeds 1 `
  --msa-mode single_sequence `
  --model-type alphafold2_multimer_v3 `
  --num-models 1 `
  --num-recycle 0
```

生成文件：

```text
results/colabfold_predictions_top30_seed1/colabfold_jobs.csv
results/colabfold_predictions_top30_seed1/inputs/fasta/*.fasta
```

当前 top30 × seed1，所以应有 30 个 job。

## 5. 先跑 1 个 pilot

先只跑 1 个任务，确认环境、权重、GPU、输入和输出都正常。

在 WSL 中执行：

```bash
cd /mnt/c/SH/fga_cyclic_peptide_design

export PROJECT_DIR="/mnt/c/SH/fga_cyclic_peptide_design"
export LCF_HOME="$HOME/fga_model_envs/localcolabfold"
export LCF_PY="$LCF_HOME/.pixi/envs/default/bin/python"
export PATH="$LCF_HOME/.pixi/envs/default/bin:$PATH"
export AF_PARAMS="$HOME/fga_model_envs/af_params"

export JOBS_CSV="results/colabfold_predictions_top30_seed1/colabfold_jobs.csv"
export GPU_LIST=0
export MAX_JOBS=1
export MAX_RETRIES=1
export COLABFOLD_TIMEOUT_SECONDS=7200
export COLABFOLD_OVERRIDE=false

bash scripts/external/run_colabfold_batch.sh
```

成功标志：

```text
Done
Patch_A_afm_00001_seed1 seed=1 gpu=0 pass attempt=1
ColabFold batch complete.
```

输出目录示例：

```text
results/colabfold_predictions_top30_seed1/outputs/Patch_A_afm_00001_seed1/
```

其中应包含：

```text
*_scores_rank_001_*.json
*_predicted_aligned_error_v1.json
*_unrelaxed_rank_001_*.pdb
*_pae.png
*_plddt.png
log.txt
```

注意：pilot 成功只代表流程可运行，不代表这个候选通过。比如当前已跑的第一个 pilot：

```text
pLDDT=24.4
pTM=0.17
ipTM=0.158
```

这说明该复合物预测质量很低，不能作为有效结合证据。

## 6. 跑完 top30 剩余任务

pilot 成功后，跑完 CSV 中剩余任务。脚本会自动跳过已完成输出，因此不会覆盖已经成功的 pilot。

```bash
cd /mnt/c/SH/fga_cyclic_peptide_design

export PROJECT_DIR="/mnt/c/SH/fga_cyclic_peptide_design"
export LCF_HOME="$HOME/fga_model_envs/localcolabfold"
export LCF_PY="$LCF_HOME/.pixi/envs/default/bin/python"
export PATH="$LCF_HOME/.pixi/envs/default/bin:$PATH"
export AF_PARAMS="$HOME/fga_model_envs/af_params"

export JOBS_CSV="results/colabfold_predictions_top30_seed1/colabfold_jobs.csv"
export GPU_LIST=0,1
export MAX_JOBS=0
export MAX_RETRIES=1
export COLABFOLD_TIMEOUT_SECONDS=7200
export COLABFOLD_OVERRIDE=false

bash scripts/external/run_colabfold_batch.sh
```

参数含义：

```text
GPU_LIST=0,1
```

使用两张 GPU 并行跑任务。

```text
MAX_JOBS=0
```

不限制任务数，跑完 `colabfold_jobs.csv` 里的全部任务。已完成任务会被跳过。

```text
MAX_RETRIES=1
```

每个任务失败后不重复尝试。AlphaFold-Multimer 单任务很慢，先不建议高重试。

```text
COLABFOLD_TIMEOUT_SECONDS=7200
```

单个任务最长允许 7200 秒，也就是 2 小时。

```text
COLABFOLD_OVERRIDE=false
```

不覆盖已有成功结果。

## 7. 运行期间如何看状态

查看 GPU：

```bash
watch -n 10 nvidia-smi
```

查看 summary：

```bash
cd /mnt/c/SH/fga_cyclic_peptide_design
tail -n 50 results/colabfold_predictions_top30_seed1/logs/colabfold_batch_summary.tsv
```

查看失败：

```bash
cat results/colabfold_predictions_top30_seed1/logs/colabfold_batch_failures.tsv
```

查看已完成输出目录数量：

```bash
find results/colabfold_predictions_top30_seed1/outputs -mindepth 1 -maxdepth 1 -type d | wc -l
```

top30 seed1 全部完成后，输出目录数量应接近 30。

## 8. 解析 AlphaFold-Multimer 输出

跑完后执行解析脚本。建议在 PowerShell 里执行：

```powershell
cd C:\SH\fga_cyclic_peptide_design

.\.conda\fga-cyclic-design\python.exe scripts\17_parse_colabfold_predictions.py `
  --config config\project.yaml `
  --jobs-csv results\colabfold_predictions_top30_seed1\colabfold_jobs.csv `
  --output-root results\colabfold_predictions_top30_seed1 `
  --target-fasta data\input\FGA_chain_36_866.fasta `
  --contact-cutoff 5.0
```

解析输出：

```text
results/colabfold_predictions_top30_seed1/FGA_colabfold_seed_scores.csv
results/colabfold_predictions_top30_seed1/FGA_colabfold_complex_prediction_summary.csv
```

`FGA_colabfold_seed_scores.csv` 是每个 seed 的原始解析结果。

`FGA_colabfold_complex_prediction_summary.csv` 是按 peptide_id 汇总后的结果，后续主要看这个。

## 9. 关键指标是什么意思

### ipTM

`ipTM` 是模型对链间相对位置的信心。对我们来说，它反映 FGA 和环肽之间的复合物关系是否可信。

经验解释：

```text
ipTM < 0.5  通常不可信
ipTM >= 0.5 可作为软参考
ipTM >= 0.65 更值得关注
```

但是 ipTM 不能单独决定候选是否通过。一个模型可能有较高 ipTM，但界面 PAE 或肽段 pLDDT 仍然很差。

### pTM

`pTM` 是整体结构拓扑置信度。它对大复合物整体折叠有参考意义，但本项目更关心链间结合界面，因此 pTM 不是核心通过指标。

### complex_plddt

`complex_plddt` 是整个复合物的平均局部结构置信度。

### peptide_plddt

`peptide_plddt` 是只针对候选环肽部分计算的 pLDDT。它比 complex_plddt 更重要，因为我们真正关心的是环肽本身是否被模型稳定预测。

当前阈值：

```text
mean_peptide_plddt >= 70
```

低于 70 说明模型对肽段构象不够自信。

### PAE / interface_pae

PAE 是 Predicted Aligned Error，预测对齐误差。AlphaFold-Multimer 输出的是一个矩阵，而不是单个数字。

对我们最重要的是：

```text
FGA 残基 vs 环肽残基之间的 cross-chain PAE
```

解析脚本会从完整 PAE 矩阵中切出 FGA-肽之间的区域，计算：

```text
interface_pae
```

当前阈值：

```text
best_interface_pae <= 10.0 Å
```

解释：

```text
interface_pae 越低越好
<= 10 Å 说明模型对链间相对位置有一定信心
> 20 Å 通常说明复合物结合姿态不可信
```

### interface_contacts

`interface_contacts` 是 FGA 与环肽之间的接触数量。当前按 5.0 Å 原子距离统计。

当前阈值：

```text
interface_contacts >= 8
```

如果接触数量太少，说明预测出的肽没有形成足够的结合界面。

### patch_consistency_flag

这个指标检查环肽是否真的接触到该候选所属的目标 patch。

当前要求：

```text
patch_consistency_flag == pass
```

这很重要，因为 AlphaFold-Multimer 输入是整段 FGA 序列，模型可能把肽预测到非目标区域。只有接触回 Patch_A/Patch_B 的目标残基，才符合项目目标。

### cys_cys_geometry

本项目候选是 Cys-Cys 二硫键环化肽。AlphaFold-Multimer FASTA 输入不能显式强制二硫键，因此解析时必须检查第 1 位和末位 Cys 的 SG-SG 距离。

当前要求：

```text
1.8 Å <= Cys SG-SG distance <= 2.4 Å
cys_cys_geometry == pass
```

如果不通过，说明模型预测出的肽结构不符合预期的二硫键环化几何。

## 10. 当前通过阈值

阈值来自：

```text
config/project.yaml
```

当前设置：

```yaml
scoring_thresholds:
  max_interface_pae: 10.0
  min_peptide_plddt: 70.0
  min_interface_contacts: 8
  min_iptm_soft: 0.50
  min_iptm_preferred: 0.65
  require_cys_geometry_pass: true
```

解析脚本中的 `complex_score_pass` 目前主要要求：

```text
best_interface_pae <= 10.0
mean_peptide_plddt >= 70.0
interface_contacts >= 8
patch_consistency_flag == pass
cys_cys_geometry == pass
```

`ipTM` 会进入评分和人工判断，但不是当前硬通过条件中唯一的决定项。

## 11. 如何查看最终汇总

PowerShell：

```powershell
cd C:\SH\fga_cyclic_peptide_design

.\.conda\fga-cyclic-design\python.exe - <<'PY'
import pandas as pd

p = "results/colabfold_predictions_top30_seed1/FGA_colabfold_complex_prediction_summary.csv"
df = pd.read_csv(p)

print("summary rows:", len(df))
print("complex_score_pass:", df["complex_score_pass"].sum() if "complex_score_pass" in df else "missing")

cols = [
    "peptide_id",
    "core_sequence",
    "patch_id",
    "best_iptm",
    "best_interface_pae",
    "mean_peptide_plddt",
    "interface_contacts",
    "patch_consistency_flag",
    "cys_cys_geometry",
    "complex_score",
    "complex_score_pass",
]
print(df[cols].sort_values("complex_score", ascending=False).head(20).to_string(index=False))
PY
```

如果 `complex_score_pass` 仍然是 0，不代表流程失败，而是说明这些候选在 AlphaFold-Multimer 交叉验证下也没有达到当前可信复合物阈值。

## 12. 如果要扩展到 302 条候选

当前 top30 是为了交叉验证 Boltz2 的近似优选结果。如果要把 302 条 Boltz-eligible 候选都用 AlphaFold-Multimer 跑一遍，可以从 Boltz 全量 job 表生成 AF-Multimer jobs。

建议另开输出目录，不覆盖 top30：

```powershell
cd C:\SH\fga_cyclic_peptide_design

.\.conda\fga-cyclic-design\python.exe scripts\16_prepare_colabfold_prediction_jobs.py `
  --config config\project.yaml `
  --candidate-csv results\boltz_predictions_raw3ghg_template_all_seed1\boltz_jobs.csv `
  --output-root results\colabfold_predictions_all302_seed1 `
  --target-fasta data\input\FGA_chain_36_866.fasta `
  --seeds 1 `
  --msa-mode single_sequence `
  --model-type alphafold2_multimer_v3 `
  --num-models 1 `
  --num-recycle 0
```

然后 WSL 运行：

```bash
cd /mnt/c/SH/fga_cyclic_peptide_design

export PROJECT_DIR="/mnt/c/SH/fga_cyclic_peptide_design"
export LCF_HOME="$HOME/fga_model_envs/localcolabfold"
export LCF_PY="$LCF_HOME/.pixi/envs/default/bin/python"
export PATH="$LCF_HOME/.pixi/envs/default/bin:$PATH"
export AF_PARAMS="$HOME/fga_model_envs/af_params"

export JOBS_CSV="results/colabfold_predictions_all302_seed1/colabfold_jobs.csv"
export GPU_LIST=0,1
export MAX_JOBS=0
export MAX_RETRIES=1
export COLABFOLD_TIMEOUT_SECONDS=7200
export COLABFOLD_OVERRIDE=false

bash scripts/external/run_colabfold_batch.sh
```

解析：

```powershell
cd C:\SH\fga_cyclic_peptide_design

.\.conda\fga-cyclic-design\python.exe scripts\17_parse_colabfold_predictions.py `
  --config config\project.yaml `
  --jobs-csv results\colabfold_predictions_all302_seed1\colabfold_jobs.csv `
  --output-root results\colabfold_predictions_all302_seed1 `
  --target-fasta data\input\FGA_chain_36_866.fasta `
  --contact-cutoff 5.0
```

注意：302 条 × AlphaFold-Multimer 会非常慢。按当前 pilot，单任务约 18 分钟，双 GPU 并行仍可能需要数十小时。

## 13. 常见问题和处理

### `python: command not found`

旧版脚本曾经用裸 `python` 读 CSV。现在脚本已改成使用 `$CF_PY`。如果仍遇到这个问题，执行：

```bash
export LCF_HOME="$HOME/fga_model_envs/localcolabfold"
export PATH="$LCF_HOME/.pixi/envs/default/bin:$PATH"
```

### 又开始下载 AlphaFold 参数

说明 `AF_PARAMS` 指向的目录里没有 ColabFold 期望的参数文件或 marker。

检查：

```bash
export AF_PARAMS="$HOME/fga_model_envs/af_params"
ls -lh "$AF_PARAMS/params"/params_model_*_multimer_v3.npz
ls -lh "$AF_PARAMS/params/download_complexes_multimer_v3_finished.txt"
```

如果缺失，重新解压官方参数包：

```bash
export AF_PARAMS="$HOME/fga_model_envs/af_params"

rm -rf "$AF_PARAMS/params"
mkdir -p "$AF_PARAMS/params"

tar -xf "$HOME/fga_model_envs/downloads/alphafold_params_colab_2022-12-06.tar" \
  -C "$AF_PARAMS/params"

touch "$AF_PARAMS/params/download_complexes_multimer_v3_finished.txt"
```

### 输出显示 cuDNN/cuBLAS already registered

类似：

```text
Unable to register cuDNN factory
Unable to register cuBLAS factory
computation placer already registered
```

这是 TensorFlow/JAX 初始化时常见 warning。只要后面出现：

```text
Running on GPU
Done
pass
```

就不视为失败。

### 任务很慢

当前输入长度约 845 aa，其中 FGA 片段很长，所以 AlphaFold-Multimer 单任务慢是正常的。当前设置已经是轻量配置：

```text
num_models=1
num_recycle=0
msa_mode=single_sequence
```

如果结果值得继续深入，可以对少量近似通过候选再提高 `num_recycle` 或增加 seeds。

## 14. 本轮结束后的判断方式

AlphaFold-Multimer 分支结束后，应和 Boltz2 分支一起看：

1. Boltz2 是否有通过或近似通过候选。
2. AlphaFold-Multimer 是否支持同一批候选。
3. 是否存在候选同时满足：
   - `best_interface_pae <= 10`
   - `mean_peptide_plddt >= 70`
   - `interface_contacts >= 8`
   - `patch_consistency_flag == pass`
   - `cys_cys_geometry == pass`
   - `ipTM` 至少达到软参考区间
4. 是否需要对少量候选做更高精度复跑。
5. 是否进入负筛和最终排序。

如果 AlphaFold-Multimer 与 Boltz2 都不给出可信复合物，则应诚实汇报为：当前这批候选完成了生成和结构预测，但没有达到复合物可信筛选阈值；下一步应调整设计策略、patch、长度、约束或生成模型，而不是包装成阳性结果。
