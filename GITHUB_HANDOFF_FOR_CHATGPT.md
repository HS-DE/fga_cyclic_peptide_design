# FGA 环肽设计项目 GitHub / ChatGPT 交接说明

更新时间：2026-06-05

这个文档用于把当前项目交给网页版 ChatGPT、另一台电脑或其他协作者快速理解。它不是实验结论报告，而是项目交接、环境说明和后续任务入口。

## 1. 项目一句话说明

本项目针对 human FGA / fibrinogen alpha chain 设计 Cys-Cys 二硫键环化肽，希望找到能够结合 FGA 指定表面 patch 的候选环肽。流程包括候选生成、序列硬过滤、复合物结构预测、打分、负筛和最终排序。

当前阶段：已经完成一批 ColabDesign 候选生成，并完成 Boltz2 的全量和 MSA/server top30 复合物预测筛选；正在用 LocalColabFold / AlphaFold-Multimer 对 Boltz2 top30 候选做第二模型交叉验证。

重要原则：当前所有候选都只能叫“候选”或“待验证候选”，不能叫最终合成候选。只有通过真实候选生成、硬过滤、复合物预测/评分、负筛、最终排序和人工复核后，才可以进入合成优先级讨论。

## 2. 代码仓库应该包含什么

适合放 GitHub 的内容：

- `scripts/`：主流程脚本、ColabDesign/Boltz/ColabFold 外部运行脚本、解析脚本。
- `config/project.yaml`：项目配置和筛选阈值。
- `tests/`：单元测试。
- `data/input/FGA_*.fasta` 和 `data/input/FGA_from_template.xlsx`：FGA 相关生成输入。
- `data/structures/raw/3GHG.pdb`：公开 PDB 结构。
- `data/structures/prepared/*.pdb`：由 3GHG 清洗/筛出的项目结构。
- `data/annotations/*.csv`：FGA 区域、结构映射、表面 patch 注释。
- `env/environment.yml` 和 `env/MODEL_ENV_SETUP.md`：轻量项目环境说明。
- `results/**` 中的关键 CSV/MD 汇总表。
- `docs/` 和项目说明文档。

不适合放 GitHub 的内容：

- `.conda/` Windows 本地 Python 环境。
- WSL 里的 `~/fga_model_envs/` 模型环境。
- AlphaFold 参数、Boltz 权重、ColabFold 权重。
- 大批量 Boltz/ColabFold/ColabDesign 输出目录。
- 大量 PDB/CIF/JSON/PNG 原始预测结果。
- 原始高丰度蛋白 Excel，除非确认可以公开。

本仓库的 `.gitignore` 已经按这个原则设置。

## 3. 关键目录说明

```text
config/
  project.yaml
```

项目配置。这里定义输入文件、输出目录、patch 参数、过滤条件和复合物评分阈值。

```text
scripts/
```

主流程脚本。常用脚本包括：

- `00_check_environment.py`：检查目录、依赖和输入文件。
- `01_extract_fga_sequence.py`：从 Excel 提取 FGA 序列。
- `02_prepare_fga_regions.py`：生成 FGA full-length、extracellular、chain 区域 FASTA。
- `03_prepare_structures.py`：准备 3GHG clean PDB。
- `04_map_fga_structure.py`：把 FGA 序列映射到 3GHG 链。
- `05_select_surface_patches.py`：选择 FGA 表面 patch。
- `06_make_design_jobs.py`：生成 ColabDesign/RFdiffusion job 模板。
- `07_collect_raw_designs.py`：收集真实候选生成结果。
- `08_filter_sequences.py`：序列硬过滤。
- `09_prepare_complex_prediction_jobs.py`：传统 ColabFold/Boltz 复合物 job 准备。
- `14_prepare_boltz_prediction_jobs.py`：Boltz2 分支 job/YAML 准备。
- `15_parse_boltz_predictions.py`：Boltz2 输出解析和评分。
- `16_prepare_colabfold_prediction_jobs.py`：AlphaFold-Multimer job/FASTA 准备。
- `17_parse_colabfold_predictions.py`：AlphaFold-Multimer 输出解析和评分。

```text
scripts/external/
```

外部模型运行封装脚本：

- `run_colabdesign_cyclic_binder.py`
- `run_colabdesign_safe_batch.sh`
- `run_colabdesign_chunk_batch.sh`
- `run_boltz_batch.sh`
- `run_colabfold_batch.sh`

```text
results/
```

只建议 GitHub 保存关键 CSV/MD 汇总，不保存完整大模型输出。

## 4. 当前候选生成状态

ColabDesign 候选生成曾经出现过两个重要问题：

1. `GREEDY_ITERS=0` 时，序列没有经过 semigreedy 替换优化，结果基本只是初始随机序列。
2. terminal Cys 锁定不足时，环肽两端 Cys 可能被后续优化改掉。

当前已经修复：

- 生产式候选生成使用 `PSSM_ITERS=80`。
- semigreedy 优化使用 `GREEDY_ITERS=32`。
- 两端 Cys 通过 mutation lock 保持不变。
- Patch_A 和 Patch_B 不再因为相同 seed 生成完全相同初始序列。

当前硬过滤结果：

```text
results/filtered/FGA_hard_filtered_candidates.csv
```

已知状态：

- 硬过滤候选约 437 条。
- Boltz-eligible 候选约 302 条。
- 被序列过滤跳过约 135 条。

这些只是候选，不是最终结果。

## 5. Boltz2 分支状态

Boltz2 环境：

```text
~/fga_model_envs/boltz2
```

主要脚本：

```text
scripts/14_prepare_boltz_prediction_jobs.py
scripts/external/run_boltz_batch.sh
scripts/15_parse_boltz_predictions.py
```

### 5.1 全量 empty-MSA 轮

输出目录：

```text
results/boltz_predictions_raw3ghg_template_all_seed1
```

状态：

- 302 个 Boltz2 job 完成。
- 302 个 confidence JSON 输出。
- 302 个 PDB 输出。
- parser 已完成。

核心结果：

```text
complex_score_pass = 0 / 302
```

主要失败原因：

- interface PAE 偏高。
- peptide pLDDT 偏低。
- Cys-Cys 几何经常不满足二硫键距离。

这是一轮技术上成功、科学上偏负面的筛选。

### 5.2 MSA/server top30 轮

输出目录：

```text
results/boltz_predictions_raw3ghg_template_msa_top30
```

状态：

- 从 empty-MSA 结果中选 top30 near-miss。
- 每条候选跑 3 个 seed。
- 总计 90 个 Boltz2 job。
- 已完成并解析。

核心结果：

```text
complex_score_pass = 0 / 30
```

主要统计：

- patch consistency pass：30/30
- Cys geometry pass：15/30
- best_iptm >= 0.50：5/30
- best_iptm >= 0.65：2/30
- best_interface_pae <= 10：0/30
- mean_peptide_plddt >= 70：0/30

这说明 Boltz2 认为这些候选能接触目标 patch，但对界面相对位置和肽段局部结构的信心不足。

## 6. AlphaFold-Multimer / ColabFold 分支状态

LocalColabFold 环境：

```text
~/fga_model_envs/localcolabfold/.pixi/envs/default
```

AlphaFold 参数目录：

```text
~/fga_model_envs/af_params/params
```

主要脚本：

```text
scripts/16_prepare_colabfold_prediction_jobs.py
scripts/external/run_colabfold_batch.sh
scripts/17_parse_colabfold_predictions.py
```

当前任务：

```text
results/colabfold_predictions_top30_seed1/colabfold_jobs.csv
```

这是 Boltz2 MSA/server top30 候选的 AlphaFold-Multimer 交叉验证。

已验证：

- LocalColabFold 可运行。
- `alphafold2_multimer_v3` 权重已准备。
- 第一个 pilot job 已成功跑通。

第一个 pilot 输出日志显示：

```text
pLDDT = 24.4
pTM = 0.17
ipTM = 0.158
```

这代表流程成功，但该单个候选预测质量差，不能作为通过证据。

完整运行说明见：

```text
docs/FGA_AlphaFold_Multimer_Flow_20260605.md
```

## 7. 关键评分指标

### ipTM

模型对链间相对位置的置信度。越高越好。

参考：

- `< 0.50`：通常不可信。
- `>= 0.50`：软参考。
- `>= 0.65`：更值得关注。

### pLDDT / peptide pLDDT

局部结构置信度。`peptide_plddt` 是只看候选肽部分的 pLDDT，比整体 pLDDT 更重要。

当前阈值：

```text
mean_peptide_plddt >= 70
```

### PAE / interface PAE

PAE 是 Predicted Aligned Error。对本项目最重要的是 FGA 与环肽之间的 cross-chain PAE，即 `interface_pae`。

当前阈值：

```text
best_interface_pae <= 10 Å
```

### interface contacts

FGA 与环肽之间的原子接触数量，当前按 5.0 Å cutoff 统计。

当前阈值：

```text
interface_contacts >= 8
```

### patch consistency

检查候选肽是否接触到指定 Patch_A / Patch_B，而不是跑到 FGA 其他区域。

当前要求：

```text
patch_consistency_flag == pass
```

### Cys-Cys geometry

检查第 1 位和末位 Cys 的 SG-SG 距离是否接近二硫键。

当前要求：

```text
1.8 Å <= SG-SG <= 2.4 Å
cys_cys_geometry == pass
```

## 8. 当前硬通过条件

配置来自：

```text
config/project.yaml
```

当前阈值：

```yaml
scoring_thresholds:
  max_interface_pae: 10.0
  min_peptide_plddt: 70.0
  min_interface_contacts: 8
  min_iptm_soft: 0.50
  min_iptm_preferred: 0.65
  require_cys_geometry_pass: true
```

解析脚本中的 `complex_score_pass` 主要要求：

- `best_interface_pae <= 10.0`
- `mean_peptide_plddt >= 70.0`
- `interface_contacts >= 8`
- `patch_consistency_flag == pass`
- `cys_cys_geometry == pass`

## 9. 在新电脑上如何重建轻量项目环境

Windows 项目轻量环境：

```powershell
cd C:\SH\fga_cyclic_peptide_design
conda env create -p .\.conda\fga-cyclic-design -f env\environment.yml
.\.conda\fga-cyclic-design\python.exe -m pytest -q
.\.conda\fga-cyclic-design\python.exe run_pipeline.py --config config\project.yaml --mode full
```

注意：这个环境只负责项目脚本、CSV/PDB/FASTA 处理和测试，不包含 Boltz2、ColabFold、ColabDesign GPU 模型环境。

## 10. WSL 模型环境说明

模型环境通常不随 GitHub 仓库迁移，需要在 WSL 里单独安装：

```text
~/fga_model_envs/localcolabfold
~/fga_model_envs/boltz2
~/fga_model_envs/af_params
~/fga_model_envs/sources/ColabDesign-cyclic-binder
```

需要确认：

```bash
nvidia-smi
nvcc --version
```

LocalColabFold 检查：

```bash
export LCF_HOME="$HOME/fga_model_envs/localcolabfold"
export PATH="$LCF_HOME/.pixi/envs/default/bin:$PATH"

which colabfold_batch
python - <<'PY'
import jax
print(jax.default_backend())
print(jax.devices())
PY
```

Boltz2 检查：

```bash
source ~/fga_model_envs/boltz2/bin/activate
which boltz
python - <<'PY'
import torch
print(torch.__version__)
print(torch.cuda.is_available())
print(torch.cuda.device_count())
PY
```

## 11. 给网页版 ChatGPT 的推荐提问方式

打开网页版 ChatGPT 后，可以这样说：

```text
我正在做一个 FGA Cys-Cys 环肽设计项目。请先阅读这个 GitHub 仓库里的 GITHUB_HANDOFF_FOR_CHATGPT.md、README.md、config/project.yaml、scripts/14_prepare_boltz_prediction_jobs.py、scripts/15_parse_boltz_predictions.py、scripts/16_prepare_colabfold_prediction_jobs.py、scripts/17_parse_colabfold_predictions.py。

当前状态是：ColabDesign 已生成并硬过滤候选；Boltz2 empty-MSA 302 条和 MSA/server top30 已完成但没有候选通过硬阈值；现在正在用 AlphaFold-Multimer top30 做交叉验证。请不要把任何候选称为 final 或 synthesis-ready，除非它通过了生成、硬过滤、复合物预测、负筛、最终排序和人工复核。

请帮我继续分析 AlphaFold-Multimer 输出结果，并解释 interface_pae、peptide_plddt、ipTM、patch consistency 和 Cys-Cys geometry 的筛选意义。
```

## 12. 下一步建议

当前最直接的下一步：

1. 跑完 `results/colabfold_predictions_top30_seed1/colabfold_jobs.csv` 中剩余 AlphaFold-Multimer 任务。
2. 执行 `scripts/17_parse_colabfold_predictions.py`。
3. 对比 Boltz2 MSA/server top30 与 AlphaFold-Multimer top30。
4. 如果两个模型都没有候选通过，应诚实汇报为当前候选集未达到复合物可信阈值。
5. 后续可考虑调整 patch、长度、候选生成约束、负筛策略或引入更高精度复跑。

不要为了交付而把未通过候选包装成阳性结果。
