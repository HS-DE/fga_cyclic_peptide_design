# 外部模型运行指南

当前本机尚未安装 ColabDesign-cyclic-binder、RFdiffusion/RFpeptides、ColabFold 或 Boltz-2，因此不能在本机直接生成真实候选肽或复合物预测评分。

## 1. 当前可直接交给 GPU 环境的输入

候选生成 job 表：

```text
results/raw_designs/design_jobs.csv
```

ColabDesign-cyclic-binder 主路线模板：

```text
results/raw_designs/colabdesign_jobs/*.sh
```

RFdiffusion/RFpeptides 备用路线模板：

```text
results/raw_designs/rfdiffusion_jobs_optional/*.yaml
```

目标结构：

```text
data/structures/prepared/fibrinogen_3GHG_clean.pdb
data/structures/prepared/FGA_target_patches.pdb
```

Patch 注释：

```text
data/annotations/FGA_epitope_candidates.csv
```

## 2. 真实候选生成输出格式

运行 ColabDesign-cyclic-binder 或 RFdiffusion/RFpeptides 后，把真实候选 CSV 放入：

```text
results/raw_designs/colabdesign_outputs/
results/raw_designs/rfdiffusion_outputs/
```

候选 CSV 至少需要这些列：

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

## 3. 回填真实候选后的本地步骤

```powershell
& 'C:\Users\luomi123\anaconda3\envs\Proteomics\python.exe' scripts/07_collect_raw_designs.py --config config/project.yaml
& 'C:\Users\luomi123\anaconda3\envs\Proteomics\python.exe' scripts/08_filter_sequences.py --config config/project.yaml
& 'C:\Users\luomi123\anaconda3\envs\Proteomics\python.exe' scripts/09_prepare_complex_prediction_jobs.py --config config/project.yaml
```

## 4. 复合物预测阶段

`09_prepare_complex_prediction_jobs.py` 会生成：

```text
results/complex_predictions/complex_prediction_jobs.csv
results/complex_predictions/inputs/*.fasta
```

在 ColabFold/Boltz-2 环境中运行后，需要把解析结果整理为：

```text
results/complex_predictions/manual_complex_prediction_summary.csv
```

该表需要包含：

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

## 5. 禁止使用的文件

```text
results/raw_designs/FGA_raw_candidates.demo.csv
```

这是 demo/toy 占位文件，不是模型结果，不能进入最终 top50/top10。

## 6. 当前本机阻断

本机有 RTX 3060 12GB，但当前可用 Python 环境没有健康的 GPU 模型运行栈：

- `Proteomics` 环境基础依赖齐全，测试通过，但 PyTorch DLL 导入失败。
- `AI` 环境 PyTorch 为 CPU 版，CUDA 不可用。
- ColabDesign-cyclic-binder / RFdiffusion / ColabFold / Boltz-2 均未安装。

因此下一步需要在可运行这些模型的 GPU/Linux/Colab 环境执行候选生成。
