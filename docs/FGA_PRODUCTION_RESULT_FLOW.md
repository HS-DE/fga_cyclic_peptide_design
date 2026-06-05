# FGA 环肽项目生产出结果流程

本文档用于正式生产候选肽段，不再重复 pytest / full pipeline 基础检查。  
原则：不交付未经真实模型生成、复合物预测、评分、负筛选支持的最终肽段。

项目目录：

```text
Windows: C:\SH\fga_cyclic_peptide_design
WSL:     /mnt/c/SH/fga_cyclic_peptide_design
```

## 1. 直接跑 ColabDesign 生产候选

先跑最稳的 Patch_B，不要一开始跑 Patch_C。  
这一步是正式生产 raw 候选，不是测试。

当前机器上 JAX/CUDA 偶发 native `Segmentation fault`。不要用一个 Python 进程连续跑多条设计。  
使用安全 runner：每条候选单独启动一个进程；某个 seed 崩溃只记录失败，其他 seed 继续累计产出。

在 WSL 中运行：

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

mkdir -p logs

DESIGNS_PER_JOB=100
PSSM_ITERS=80
MAX_RETRIES=1

bash scripts/external/run_colabdesign_safe_batch.sh \
  Patch_B_L12_colabdesign \
  Patch_B_L14_colabdesign \
  Patch_B_L16_colabdesign
```

这个批次会发起：

```text
3 个长度 x 每个长度 100 条 = 300 条设计请求
```

监控 GPU：

```bash
watch -n 10 nvidia-smi
```

如果某个 seed 失败，先保留日志，不要删除输出目录。安全 runner 会继续后面的 seed。

失败和成功汇总：

```bash
tail -n 20 logs/colabdesign_safe_batch_summary.tsv
tail -n 20 logs/colabdesign_safe_batch_failures.tsv
```

## 2. 收集 raw 候选并硬过滤

ColabDesign 跑完后，回到 PowerShell：

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
    print(p, len(pd.read_csv(p)))
'@ | .\.conda\fga-cyclic-design\python.exe -
```

判断：

- `FGA_raw_candidates.csv` 是真实 raw 候选池。
- `FGA_hard_filtered_candidates.csv` 是通过 Cys-Cys、长度、电荷、疏水性等硬过滤的候选。
- 如果 hard-filtered 数量太少，继续补跑 Patch_B 或增加 Patch_A。

## 3. 如果候选不够，补跑 Patch_A

Patch_B 不够时，再跑 Patch_A 的 L12/L14/L16：

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

mkdir -p logs

DESIGNS_PER_JOB=100
PSSM_ITERS=80
MAX_RETRIES=1

bash scripts/external/run_colabdesign_safe_batch.sh \
  Patch_A_L12_colabdesign \
  Patch_A_L14_colabdesign \
  Patch_A_L16_colabdesign
```

然后重新执行第 2 节收集和过滤。

## 4. 跑 ColabFold seed1 初筛

不要一开始对所有候选跑 5 seeds。先跑 ColabFold seed1。

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

生成 seed1 执行脚本：

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

```text
输出目录里有 *_unrelaxed_rank_001_*.pdb
输出目录里有 *_scores_rank_001_*.json
log.txt 结尾出现 Done
```

只有 `.a3m / config.json / coverage.png` 不算完成。

## 5. seed1 后的去留

查看 seed1 分数：

```bash
grep -R "rank_001" results/complex_predictions/*_colabfold_seed1/log.txt | tee logs/colabfold_seed1_rank_summary.txt
```

粗筛建议：

```text
ipTM < 0.30         淘汰或低优先级
0.30 <= ipTM < 0.50 谨慎观察
ipTM >= 0.50        进入 5-seed 复评
ipTM >= 0.65        高优先级
```

这只是初筛，不是最终结果。

## 6. 整理复合物评分表

最终评分脚本读取：

```text
results/complex_predictions/manual_complex_prediction_summary.csv
```

必须整理真实模型结果，不能手填虚假结果。字段至少包括：

```text
peptide_id,core_sequence,patch_id,n_seeds,best_seed,mean_iptm,best_iptm,
mean_interface_pae,best_interface_pae,mean_peptide_plddt,interface_contacts,
pose_consistency_rmsd,patch_consistency_flag,cys_cys_geometry,notes
```

通过标准来自 `config/project.yaml`：

```text
best_interface_pae <= 10
mean_peptide_plddt >= 70
interface_contacts >= 8
patch_consistency_flag == pass
cys_cys_geometry == pass
```

## 7. 负筛选

负筛选结果表：

```text
results/filtered/manual_negative_screen_summary.csv
```

字段：

```text
peptide_id,negative_target,negative_score,negative_interface_pae,
negative_contacts,non_specific_risk,negative_screen_pass,notes
```

负筛选目标包括：

```text
ALB, APOA1, TF, A2M, C3, IGG_FC
```

没有负筛选，不生成可交付 top10。

## 8. 导出最终结果

完成复合物评分和负筛选后，在 PowerShell 运行：

```powershell
cd C:\SH\fga_cyclic_peptide_design

.\.conda\fga-cyclic-design\python.exe scripts\10_score_complex_predictions.py --config config\project.yaml
.\.conda\fga-cyclic-design\python.exe scripts\11_negative_screen.py --config config\project.yaml
.\.conda\fga-cyclic-design\python.exe scripts\12_rank_candidates.py --config config\project.yaml
.\.conda\fga-cyclic-design\python.exe scripts\13_export_final_report.py --config config\project.yaml
```

最终交付文件：

```text
results/final/FGA_top50_candidates.csv
results/final/FGA_top10_synthesis_priority.csv
results/final/FGA_design_report.md
```

如果 top50/top10 为空，不要手动补肽段；这说明真实评分链条还没完成，或者没有候选通过。
