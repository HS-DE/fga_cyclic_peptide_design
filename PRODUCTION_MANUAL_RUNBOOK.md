# FGA Cys-Cys 环肽生产手动运行手册

本文档用于手动运行 FGA Cys-Cys 二硫键环肽设计流程。核心原则是：不把 smoke test、debug 输出、raw 生成结果直接当成最终肽段；只有经过真实模型生成、序列硬过滤、复合物预测、结构评分、Cys-Cys 几何检查、负筛选和最终排序的候选，才允许进入 final 表。

当前项目根目录：

```powershell
C:\SH\fga_cyclic_peptide_design
```

WSL 路径：

```bash
/mnt/c/SH/fga_cyclic_peptide_design
```

## 1. 基础检查

在 PowerShell 里运行：

```powershell
cd C:\SH\fga_cyclic_peptide_design
.\.conda\fga-cyclic-design\python.exe -m pytest -q
.\.conda\fga-cyclic-design\python.exe run_pipeline.py --config config\project.yaml --mode full
```

预期：

- pytest 全部通过。
- pipeline completed。
- 如果还没有 `manual_complex_prediction_summary.csv` 和 `manual_negative_screen_summary.csv`，final top50/top10 为空是正确行为。

查看当前表格行数：

```powershell
@'
import pandas as pd
for p in [
 "results/raw_designs/FGA_raw_candidates.csv",
 "results/filtered/FGA_hard_filtered_candidates.csv",
 "results/complex_predictions/complex_prediction_jobs.csv",
 "results/complex_predictions/FGA_complex_prediction_summary.csv",
 "results/final/FGA_top50_candidates.csv",
 "results/final/FGA_top10_synthesis_priority.csv",
]:
    df = pd.read_csv(p)
    print(p, len(df))
'@ | .\.conda\fga-cyclic-design\python.exe -
```

## 2. 重新生成 patch 和 design job

生产前先重新生成 05/06：

```powershell
cd C:\SH\fga_cyclic_peptide_design
.\.conda\fga-cyclic-design\python.exe scripts\05_select_surface_patches.py --config config\project.yaml
.\.conda\fga-cyclic-design\python.exe scripts\06_make_design_jobs.py --config config\project.yaml
```

检查 job：

```powershell
Import-Csv results\raw_designs\design_jobs.csv |
  Select-Object job_id,patch_id,target_chain,hotspot_residues,peptide_length,n_designs |
  Format-Table -AutoSize
```

当前合理结果：

- `Patch_B` 使用 `target_chain A`，hotspot 为 `A27,A30,A31,A32,A33,A34,A35,A37,A38,A43`。
- `Patch_A` 使用 `target_chain J`，hotspot 为 `J31,J32,J33,J34,J35,J37,J199,J200,J202`。
- `Patch_C` 是 fallback/exploratory，不建议放在第一批生产主力里。

不要手写 `A202` 这类不存在于链 A 的 hotspot。

## 3. ColabDesign 生产生成 raw 候选

不要一次用 `NUM_DESIGNS=100` 压进一个 Python/JAX 进程。建议用小块生产：每块 5 条，每个 job 跑 20 块，总计 100 条设计请求。这样即使某块崩溃，也只损失那一小块。

在 WSL 里运行：

```bash
cd /mnt/c/SH/fga_cyclic_peptide_design

export PROJECT_DIR="/mnt/c/SH/fga_cyclic_peptide_design"
export LCF_PY="$HOME/fga_model_envs/localcolabfold/.pixi/envs/default/bin/python"
export AF_PARAMS="$HOME/fga_model_envs/af_params"
export CUDA_VISIBLE_DEVICES=0
export XLA_PYTHON_CLIENT_PREALLOCATE=false
export XLA_PYTHON_CLIENT_MEM_FRACTION=0.30
export XLA_FLAGS=--xla_gpu_enable_triton_gemm=false
export PYTHONUNBUFFERED=1
export PYTHONFAULTHANDLER=1
```

第一批建议先跑 Patch_B，再跑 Patch_A：

```bash
mkdir -p logs

CHUNK_SIZE=5
CHUNKS=20
PSSM_ITERS=80

for JOB in \
  Patch_B_L12_colabdesign \
  Patch_B_L14_colabdesign \
  Patch_B_L16_colabdesign \
  Patch_A_L12_colabdesign \
  Patch_A_L14_colabdesign \
  Patch_A_L16_colabdesign
do
  for CHUNK in $(seq 0 $((CHUNKS - 1))); do
    TAG=$(printf "%s_chunk%03d" "$JOB" "$CHUNK")
    START_SEED=$((CHUNK * CHUNK_SIZE))
    echo "=== Running $TAG seed=$START_SEED n=$CHUNK_SIZE ==="

    NUM_DESIGNS="$CHUNK_SIZE" \
    START_SEED="$START_SEED" \
    JOB_ID="$TAG" \
    OUT_DIR="results/raw_designs/colabdesign_outputs/$TAG" \
    PSSM_ITERS="$PSSM_ITERS" \
    bash "results/raw_designs/colabdesign_jobs/${JOB}.sh" \
      2>&1 | tee "logs/${TAG}.log"
  done
done
```

监控：

```bash
watch -n 10 nvidia-smi
```

检查某块输出：

```bash
cat results/raw_designs/colabdesign_outputs/Patch_B_L12_colabdesign_chunk000/run_summary.json
tail -n 5 results/raw_designs/colabdesign_outputs/Patch_B_L12_colabdesign_chunk000/candidates.csv
```

如果某块失败，不要删除日志。记录失败的 `TAG`，之后只重跑该 chunk。

## 4. 收集 raw 并做序列硬过滤

ColabDesign 生产块完成后，回到 PowerShell：

```powershell
cd C:\SH\fga_cyclic_peptide_design
.\.conda\fga-cyclic-design\python.exe scripts\07_collect_raw_designs.py --config config\project.yaml
.\.conda\fga-cyclic-design\python.exe scripts\08_filter_sequences.py --config config\project.yaml
.\.conda\fga-cyclic-design\python.exe scripts\09_prepare_complex_prediction_jobs.py --config config\project.yaml
```

查看数量：

```powershell
@'
import pandas as pd
for p in [
 "results/raw_designs/FGA_raw_candidates.csv",
 "results/filtered/FGA_hard_filtered_candidates.csv",
 "results/complex_predictions/complex_prediction_jobs.csv",
]:
    df = pd.read_csv(p)
    print(p, len(df))
'@ | .\.conda\fga-cyclic-design\python.exe -
```

生产判断：

- raw candidates 最好达到至少 100。
- hard-filtered candidates 如果太少，继续增加 chunk 或补跑 L10/L18。
- `rejected_non_scheme_A.csv` 不会进入候选池。

## 5. ColabFold 复合物预测初筛

先只跑 ColabFold seed1，不要一开始对所有候选跑 5 seeds。

在 WSL 中：

```bash
cd /mnt/c/SH/fga_cyclic_peptide_design

export CF="$HOME/fga_model_envs/localcolabfold/.pixi/envs/default/bin/colabfold_batch"
export AF_PARAMS="$HOME/fga_model_envs/af_params"
export CUDA_VISIBLE_DEVICES=0
export COLABFOLD_TIMEOUT_SECONDS=3600
export XLA_PYTHON_CLIENT_PREALLOCATE=false
export XLA_PYTHON_CLIENT_MEM_FRACTION=0.70
export XLA_FLAGS=--xla_gpu_enable_triton_gemm=false
```

生成 seed1 脚本：

```bash
python - <<'PY' > /tmp/run_fga_colabfold_seed1.sh
import csv

print('set -euo pipefail')
print('cd /mnt/c/SH/fga_cyclic_peptide_design')
print('CF="${CF:-$HOME/fga_model_envs/localcolabfold/.pixi/envs/default/bin/colabfold_batch}"')
print('AF_PARAMS="${AF_PARAMS:-$HOME/fga_model_envs/af_params}"')
print('export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"')
print('export XLA_PYTHON_CLIENT_PREALLOCATE="${XLA_PYTHON_CLIENT_PREALLOCATE:-false}"')
print('export XLA_PYTHON_CLIENT_MEM_FRACTION="${XLA_PYTHON_CLIENT_MEM_FRACTION:-0.70}"')
print('export XLA_FLAGS="${XLA_FLAGS:---xla_gpu_enable_triton_gemm=false}"')
print('mkdir -p logs')

with open("results/complex_predictions/complex_prediction_jobs.csv", newline="", encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        if r["engine"] != "colabfold" or r["seed"] != "1":
            continue
        inp = r["input_fasta"].replace("\\", "/")
        out = r["output_dir"].replace("\\", "/")
        job = r["prediction_job_id"]
        print(f'echo "=== Running {job} ==="')
        print(f'mkdir -p "{out}"')
        print(f'timeout "${{COLABFOLD_TIMEOUT_SECONDS:-3600}}" "$CF" '
              f'--msa-mode single_sequence --model-type alphafold2_multimer_v3 '
              f'--num-models 1 --num-recycle 0 --num-seeds 1 --random-seed 1 '
              f'--data "$AF_PARAMS" --overwrite-existing-results "{inp}" "{out}" '
              f'2>&1 | tee "{out}/job_stdout_stderr.log"')
PY
```

运行：

```bash
bash /tmp/run_fga_colabfold_seed1.sh
```

成功标志：

- 输出目录有 `*_unrelaxed_rank_001_*.pdb`。
- 输出目录有 `*_scores_rank_001_*.json`。
- `log.txt` 结尾出现 `Done`。

只有 `.a3m/config.json/coverage.png` 不算完成。

## 6. 人工评分表

当前 `10_score_complex_predictions.py` 不会自动解析 ColabFold 输出；它读取：

```text
results/complex_predictions/manual_complex_prediction_summary.csv
```

你需要根据真实 ColabFold/Boltz 结果整理该表，字段至少包含：

```text
peptide_id,core_sequence,patch_id,n_seeds,best_seed,mean_iptm,best_iptm,
mean_interface_pae,best_interface_pae,mean_peptide_plddt,interface_contacts,
pose_consistency_rmsd,patch_consistency_flag,cys_cys_geometry,notes
```

门槛在 `config/project.yaml`：

- `best_interface_pae <= 10`
- `mean_peptide_plddt >= 70`
- `interface_contacts >= 8`
- `patch_consistency_flag == pass`
- `cys_cys_geometry == pass`

## 7. 负筛选与最终排序

负筛选表：

```text
results/filtered/manual_negative_screen_summary.csv
```

字段：

```text
peptide_id,negative_target,negative_score,negative_interface_pae,
negative_contacts,non_specific_risk,negative_screen_pass,notes
```

完成复合物评分和负筛选后运行：

```powershell
cd C:\SH\fga_cyclic_peptide_design
.\.conda\fga-cyclic-design\python.exe scripts\10_score_complex_predictions.py --config config\project.yaml
.\.conda\fga-cyclic-design\python.exe scripts\11_negative_screen.py --config config\project.yaml
.\.conda\fga-cyclic-design\python.exe scripts\12_rank_candidates.py --config config\project.yaml
.\.conda\fga-cyclic-design\python.exe scripts\13_export_final_report.py --config config\project.yaml
```

最终只看：

```text
results/final/FGA_top50_candidates.csv
results/final/FGA_top10_synthesis_priority.csv
results/final/FGA_design_report.md
```

如果这两个 CSV 仍为空，不要手动补肽段；说明真实评分链条还没完成或没有候选通过。
