# FGA Cys-Cys 环肽计算设计流程

本项目针对 human FGA / fibrinogen alpha chain / UniProt P02671，建立一套 Cys-Cys 二硫键环肽计算设计流程。设计对象优先限定为 native fibrinogen 结构中暴露的 FGA 区域，而不是 full-length precursor 或孤立 FGA 单链。

当前工程只生成可复现的 pipeline、配置、任务文件、过滤评分逻辑和报告。没有真实 ColabDesign/RFdiffusion/ColabFold/Boltz-2 输出时，不会生成可用于合成的最终候选肽。

## 目录结构

```text
config/project.yaml
data/input/
data/structures/raw/
data/structures/prepared/
data/annotations/
scripts/
tests/
results/raw_designs/
results/complex_predictions/
results/filtered/
results/final/
logs/
env/environment.yml
run_pipeline.py
```

## 环境安装

```bash
conda env create -f env/environment.yml
conda activate fga-cyclic-design
python run_pipeline.py --config config/project.yaml
```

基础流程依赖 `openpyxl`、`pyyaml`、`pandas`、`numpy`、`scipy`、`scikit-learn`、`biopython`、`pytest`。当前脚本为了便于准备阶段运行，核心 Excel/FASTA/PDB 处理尽量使用标准库和 `openpyxl`；完整环境仍建议按 `env/environment.yml` 安装。

可选重型工具不强制安装：`freesasa`、`mdtraj`、`pymol`、`colabfold_batch`、`boltz`、ColabDesign-cyclic-binder、RFdiffusion/RFpeptides。

## 输入文件要求

`data/input/高丰度蛋白信息.xlsx` 必须包含：

```text
UniprotID
Gene
estimated_ng_per_ml
Sequence
```

脚本会提取 `Gene == FGA` 或 `UniprotID == P02671` 的记录，并生成：

```text
data/input/FGA_from_template.xlsx
data/input/FGA_full_length_1_866.fasta
data/input/FGA_extracellular_20_866.fasta
data/input/FGA_chain_36_866.fasta
data/annotations/FGA_regions.csv
```

结构优先使用 `data/structures/raw/3GHG.pdb`。如果不存在，`03_prepare_structures.py` 会尝试从 RCSB 下载。下载失败时需要手动放入该路径。

## 如何运行

准备阶段：

```bash
python run_pipeline.py --config config/project.yaml --mode prepare
```

完整流程：

```bash
python run_pipeline.py --config config/project.yaml --mode full
```

单步运行：

```bash
python scripts/01_extract_fga_sequence.py --config config/project.yaml
python scripts/02_prepare_fga_regions.py --config config/project.yaml
python scripts/06_make_design_jobs.py --config config/project.yaml
```

## 每一步输出

`00_check_environment.py` 检查 Python、依赖、目录、输入 Excel、3GHG 结构，日志写入 `logs/00_check_environment.log`。

`01_extract_fga_sequence.py` 从 Excel 提取 FGA，写出 `FGA_from_template.xlsx` 和 full-length FASTA。

`02_prepare_fga_regions.py` 生成 full-length、20-866 extracellular、36-866 main chain FASTA 和 `FGA_regions.csv`。

`03_prepare_structures.py` 准备并清理 `3GHG.pdb`。

`04_map_fga_structure.py` 通过序列比对识别 3GHG 中 FGA 链，生成结构映射表和可见 FGA PDB。

`05_select_surface_patches.py` 使用 freesasa 或 residue neighbor count 近似暴露度，生成 Patch_A/Patch_B/Patch_C。

`06_make_design_jobs.py` 生成 ColabDesign-cyclic-binder 主路线 job 和 RFdiffusion/RFpeptides 备用 job 模板。

`07_collect_raw_designs.py` 只收集真实模型输出。没有真实输出时只生成空的 `FGA_raw_candidates.demo.csv`，不会进入最终 top10。

`08_filter_sequences.py` 对真实 raw candidates 执行 Cys-Cys 环肽硬过滤。

`09_prepare_complex_prediction_jobs.py` 为过滤后的真实候选生成 ColabFold/Boltz-2 复合物预测任务。

`10_score_complex_predictions.py` 解析真实复合物预测输出并计算界面评分、patch consistency、Cys-Cys geometry。

`11_negative_screen.py` 汇总负筛选结果。

`12_rank_candidates.py` 只对真实、完成评分并通过过滤的候选排序，输出 header-only 或真实 top50/top10。

`13_export_final_report.py` 生成中文报告。

## 接入 ColabDesign-cyclic-binder

先运行：

```bash
python scripts/06_make_design_jobs.py --config config/project.yaml
```

查看：

```text
results/raw_designs/design_jobs.csv
results/raw_designs/colabdesign_jobs/*.sh
```

在装有 ColabDesign-cyclic-binder 的 GPU 环境中按 job 模板替换实际入口脚本和参数，运行后把真实输出 CSV 放回：

```text
results/raw_designs/colabdesign_outputs/
```

输出 CSV 至少应包含 `core_sequence`，建议同时包含 `raw_id, job_id, patch_id, raw_score`。

## 接入 RFdiffusion/RFpeptides

RFdiffusion/RFpeptides 是备用增强路线。任务模板位于：

```text
results/raw_designs/rfdiffusion_jobs_optional/
```

运行后把解析后的候选 CSV 放入：

```text
results/raw_designs/rfdiffusion_outputs/
```

## 接入 ColabFold/Boltz-2

真实候选通过硬过滤后运行：

```bash
python scripts/09_prepare_complex_prediction_jobs.py --config config/project.yaml
```

任务表位于：

```text
results/complex_predictions/complex_prediction_jobs.csv
```

在相应环境中运行 ColabFold 或 Boltz-2 后，把结果目录放回 `results/complex_predictions/`，再运行：

```bash
python scripts/10_score_complex_predictions.py --config config/project.yaml
python scripts/11_negative_screen.py --config config/project.yaml
python scripts/12_rank_candidates.py --config config/project.yaml
python scripts/13_export_final_report.py --config config/project.yaml
```

## 查看最终 top10

只有当真实候选完成生成、过滤、复合物预测评分和负筛选后，`results/final/FGA_top10_synthesis_priority.csv` 才会包含候选序列。没有真实模型输出时，该文件为空表或不存在真实候选，报告会明确说明不能用于合成。

## 常见错误

`缺少 Excel 文件`：确认 `data/input/高丰度蛋白信息.xlsx` 存在。

`找不到 FGA/P02671`：检查列名是否为 `UniprotID, Gene, estimated_ng_per_ml, Sequence`。

`缺少 3GHG.pdb`：检查网络下载是否成功，或手动放入 `data/structures/raw/3GHG.pdb`。

`缺少 pyyaml/pandas/pytest`：按 `env/environment.yml` 创建 conda 环境。

`没有 top10`：说明尚未提供真实生成模型和复合物预测评分输出；这是预期行为，不是失败。
