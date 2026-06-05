# FGA Boltz 复合物预测分支任务书

更新时间: 2026-06-04

## 1. 任务目标

在不破坏现有 ColabDesign / ColabFold 主流程的前提下，新增一条 Boltz 专用复合物预测分支。

这条分支的目标不是重新生成环肽序列，而是使用已经通过硬过滤的候选环肽，进行 FGA-环肽复合物结构预测、评分解析、负筛选和最终排序。

## 2. 当前状态

当前候选来源:

```text
C:\SH\fga_cyclic_peptide_design\results\filtered\FGA_hard_filtered_candidates.csv
```

当前可进入 Boltz 分支的候选:

```text
raw candidates: 437
hard-filtered pass candidates: 302
unique pass core sequences: 302
Patch_A pass candidates: 281
Patch_B pass candidates: 21
```

这些序列已经完成:

```text
ColabDesign 真实生成
terminal Cys-Cys lock 检查
final_sequence_changed 检查
硬过滤
```

这些序列尚未完成:

```text
Boltz 复合物预测
复合物评分解析
负筛选
最终排名
```

因此它们只能称为候选序列，不能称为最终肽段。

## 3. Boltz 环境状态

Boltz 已安装在 WSL 环境:

```text
~/fga_model_envs/boltz2
```

已确认:

```text
which boltz -> /home/luomi/fga_model_envs/boltz2/bin/boltz
torch cuda available -> True
cuda device count -> 2
```

后续运行 Boltz 前需要激活环境:

```bash
source ~/fga_model_envs/boltz2/bin/activate
export BOLTZ_CACHE="$HOME/fga_model_envs/boltz_cache"
```

## 4. 新分支目录规划

新增目录:

```text
C:\SH\fga_cyclic_peptide_design\results\boltz_predictions\
```

建议结构:

```text
results/boltz_predictions/
  inputs/
    yaml/
  outputs/
  logs/
  boltz_jobs.csv
  FGA_boltz_complex_prediction_summary.csv
```

这条分支不直接覆盖:

```text
results/complex_predictions/complex_prediction_jobs.csv
results/complex_predictions/FGA_complex_prediction_summary.csv
```

等 Boltz 解析结果确认可靠后，再决定是否接入主排序流程。

## 5. 需要新增的脚本

### 5.1 生成 Boltz YAML job

建议新增:

```text
scripts/14_prepare_boltz_prediction_jobs.py
```

职责:

1. 读取 `results/filtered/FGA_hard_filtered_candidates.csv`。
2. 只选择 `sequence_filter_pass=True/pass` 的候选。
3. 为每个候选生成 Boltz YAML 输入。
4. 写出 `results/boltz_predictions/boltz_jobs.csv`。
5. 不运行模型，只生成待运行任务。

输入:

```text
FGA_chain_36_866 sequence
candidate core_sequence
candidate raw_id
patch_id
peptide_length
```

输出:

```text
results/boltz_predictions/inputs/yaml/{peptide_id}_seed{seed}.yaml
results/boltz_predictions/boltz_jobs.csv
```

### 5.2 运行 Boltz job

建议新增:

```text
scripts/external/run_boltz_batch.sh
```

职责:

1. 从 `boltz_jobs.csv` 读取待运行任务。
2. 支持 GPU 选择。
3. 支持先跑小规模 pilot。
4. 支持跳过已有完整输出。
5. 每个 job 写独立 log。

建议先做 pilot:

```text
2 candidates x 1 seed
```

确认输出格式和 GPU 正常后，再扩展到:

```text
302 candidates x 3 seeds 或 302 candidates x 5 seeds
```

### 5.3 解析 Boltz 输出

建议新增:

```text
scripts/15_parse_boltz_predictions.py
```

职责:

1. 读取 Boltz 输出目录。
2. 解析 confidence / scores / structure 文件。
3. 提取或计算项目需要的字段。
4. 写出 `FGA_boltz_complex_prediction_summary.csv`。

目标字段:

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
complex_score
complex_score_pass
notes
```

## 6. 评分原则

Boltz 输出不能直接等同最终结果。必须转成项目统一评分字段后才能进入后续流程。

最低要求:

```text
真实 Boltz 输出存在
iptm / ptm / plddt 等信心指标可解析
interface PAE 或可替代界面置信指标可解析
预测结构中环肽和 FGA 有合理接触
Cys-Cys geometry 检查通过
patch consistency 检查通过
```

只有满足上述条件的候选，才能进入负筛选。

## 7. 不可跳过的科学约束

不得把任何候选描述为最终肽段，除非它已经通过:

```text
真实生成
硬过滤
Boltz 或其他真实复合物预测与评分
负筛选
最终排序
人工复核
```

当前 302 条候选只能称为:

```text
hard-filtered candidate peptides
```

不能称为:

```text
final peptides
synthesis-ready top candidates
validated binders
```

## 8. 下一步执行顺序

建议顺序:

```text
1. 新增 14_prepare_boltz_prediction_jobs.py
2. 生成 2 条候选 x 1 seed 的 pilot YAML
3. 手动运行 Boltz pilot
4. 观察 Boltz 输出文件结构
5. 新增 15_parse_boltz_predictions.py
6. 解析 pilot 输出并确认评分字段
7. 扩展到 302 条候选 x 3-5 seeds
8. 跑负筛选
9. 跑最终排名
```

## 9. 验收标准

Boltz 分支第一阶段完成标准:

```text
boltz_jobs.csv 生成正确
YAML 文件数量符合候选数 x seed 数
pilot Boltz job 能在 GPU 上完成
parser 能生成非空 FGA_boltz_complex_prediction_summary.csv
complex_score_pass 不是手填或伪造
未通过负筛选前 final top10 仍为空或标记为未完成
```

## 10. 当前决定

当前决定:

```text
保留现有 ColabDesign 候选
不重新生成序列
Boltz 作为新的主复合物预测分支
ColabFold 暂时作为可选复核工具
不把 Boltz job 混入旧 complex_prediction_jobs.csv
```

## 11. 已创建脚本

2026-06-04 已新增 Boltz 分支脚本:

```text
C:\SH\fga_cyclic_peptide_design\scripts\14_prepare_boltz_prediction_jobs.py
C:\SH\fga_cyclic_peptide_design\scripts\external\run_boltz_batch.sh
C:\SH\fga_cyclic_peptide_design\scripts\15_parse_boltz_predictions.py
```

已完成的本地检查:

```text
Python py_compile 通过
Bash 语法检查通过
2 candidates x 1 seed pilot YAML/job 生成通过
parser 在无真实 Boltz 输出时生成空 summary，不伪造评分
```

pilot 输出目录:

```text
C:\SH\fga_cyclic_peptide_design\results\boltz_predictions_pilot\
```

pilot YAML 已包含:

```text
FGA target chain A
peptide chain B
Cys1 SG - CysN SG bond constraint
Patch hotspot pocket constraint
3GHG template chain mapping
```

## 2026-06-04 Boltz pilot input correction

Observed issue:

```text
Boltz failed during YAML preprocessing before prediction.
Error path: parse_yaml -> parse_boltz_schema -> parse_pdb -> parse_mmcif -> parse_polymer
Error: IndexError: list index out of range
```

Root cause:

```text
The pilot YAML used data/structures/prepared/fibrinogen_3GHG_clean.pdb as a template.
That cleaned PDB contains ATOM records but no SEQRES records.
Boltz converts PDB templates to mmCIF and aligns entity full_sequence to polymer residues.
Without a complete entity sequence, template parsing can fail before model inference starts.
```

Script changes:

```text
scripts/14_prepare_boltz_prediction_jobs.py:
- Default template_pdb is now empty.
- If a user passes a PDB template without SEQRES, the script skips the template and records template_skip_reason.
- YAML still keeps the peptide terminal Cys SG-SG bond constraint.
- YAML still keeps patch pocket constraints unless explicitly disabled.

scripts/external/run_boltz_batch.sh:
- Logs now follow the JOBS_CSV directory via LOG_ROOT.
- Pilot logs no longer mix into results/boltz_predictions/logs unless that is the selected job root.
```

Current pilot recommendation:

```text
Use no-template Boltz pilot first.
Treat this as a technical validation of Boltz input/output parsing, disulfide handling, and post-hoc patch-contact scoring.
Do not call no-template Boltz outputs final binders unless they pass parser contact checks, negative screening, final ranking, and manual review.
Template anchoring remains a separate future hardening step using a Boltz-compatible template file.
```

## 2026-06-04 Boltz pilot result and path fix

Pilot result:

```text
results/boltz_predictions_pilot_no_template
Boltz batch status: pass
Prediction files were generated under the Boltz output predictions directory.
WSL-side parser successfully parsed the real Boltz output.
```

Pilot score outcome:

```text
One real prediction summary was produced.
The pilot candidate did not pass quality gates:
- interface_pae was high
- peptide_plddt was below threshold
- Cys-Cys geometry failed
Therefore this pilot is a successful technical run, not a qualified binder.
```

Path hardening:

```text
Long Boltz job IDs caused Windows-side recursive parsing problems because Boltz nests output directories deeply.
scripts/14_prepare_boltz_prediction_jobs.py now emits short boltz_job_id values like Patch_A_boltz_00001_seed1.
The original candidate raw_id remains traceable through peptide_id and notes.source_candidate_raw_id.
scripts/15_parse_boltz_predictions.py now tolerates missing/unreadable output paths instead of crashing.
```

## 2026-06-04 raw 3GHG template chain-name correction

Observed issue:

```text
Raw 3GHG template pilot no longer failed with missing SEQRES/list-index parsing.
It failed because Boltz did not expose PDB chain J as template chain J.
Error: Template chain J assigned for template3GHG is not one of the protein chains.
```

Root cause:

```text
Boltz converts PDB templates to mmCIF-like subchains before parsing.
For raw 3GHG.pdb, parsed protein chain names are A1, B1, C1, ..., J1, ...
Therefore PDB chain J must be referenced as template_id J1 in Boltz YAML.
```

Script change:

```text
scripts/14_prepare_boltz_prediction_jobs.py now converts PDB template chain IDs without digits to Boltz subchain IDs.
Example: source chain J -> template_id J1.
The original source chain is preserved in notes.source_template_chain_id.
```

Next pilot root:

```text
results/boltz_predictions_pilot_raw3ghg_template_v2
```

## 2026-06-05 Boltz2 empty-MSA full round and MSA/server follow-up

Current candidate state:

```text
hard-filtered candidate rows: 437
Boltz-eligible candidates after sequence filtering: 302
sequence-filter skipped candidates: 135
```

These are still candidate peptides only. They are not final, synthesis-ready, or validated binders because negative screening, final ranking, and manual review have not been completed.

Empty-MSA full round:

```text
output root: results/boltz_predictions_raw3ghg_template_all_seed1
jobs completed: 302
confidence JSON outputs: 302
PDB structures: 302
parser outputs:
  FGA_boltz_seed_scores.csv
  FGA_boltz_complex_prediction_summary.csv
complex_score_pass: 0 / 302
```

Interpretation:

```text
This was a technically successful Boltz2 run but a scientifically negative first screen.
Main failure modes were high interface PAE, low peptide pLDDT, and frequent Cys-Cys geometry failure.
```

MSA/server follow-up:

```text
output root: results/boltz_predictions_raw3ghg_template_msa_top30
source candidates: top30 near-miss candidates from the empty-MSA round
seeds per candidate: 3
total jobs: 90
MSA mode: server
template: data/structures/raw/3GHG.pdb
```

Current MSA/server status as of 2026-06-05 09:49:

```text
Patch_A_boltz_00001_seed1: pass
Patch_A_boltz_00001_seed2: pass
Full 90-job run has been started with BOLTZ_OVERRIDE=false.
Existing passed jobs are skipped instead of overwritten.
Active WSL jobs observed:
  Patch_A_boltz_00001_seed3
  Patch_A_boltz_00002_seed1
MSA top30 parser summary is not yet present.
```

After the MSA/server run finishes, parse with:

```bash
cd /mnt/c/SH/fga_cyclic_peptide_design
/home/luomi/fga_model_envs/boltz2/bin/python scripts/15_parse_boltz_predictions.py \
  --jobs-csv results/boltz_predictions_raw3ghg_template_msa_top30/boltz_jobs.csv \
  --output-root results/boltz_predictions_raw3ghg_template_msa_top30
```

Then compare against the empty-MSA round using:

```text
complex_score_pass
interface_pae / best_interface_pae
peptide_plddt / mean_peptide_plddt
iptm / mean_iptm
patch_consistency_flag
cys_cys_geometry
```

## 2026-06-05 ColabFold / AlphaFold-Multimer cross-check branch

Purpose:

```text
Use ColabFold / AlphaFold-Multimer as a second-model cross-check for the same near-miss candidates.
This is not a replacement for Boltz scoring and is not a direct final-candidate call.
```

Important modeling limitation:

```text
ColabFold FASTA input supports multimer chains but does not directly encode the Cys-Cys disulfide bond or the Patch_A/Patch_B pocket constraint.
Therefore post-processing must still check:
  interface PAE
  peptide pLDDT
  interface contacts
  patch_contact_count / patch_consistency_flag
  terminal Cys SG-SG distance / cys_cys_geometry
```

New scripts:

```text
C:\SH\fga_cyclic_peptide_design\scripts\16_prepare_colabfold_prediction_jobs.py
C:\SH\fga_cyclic_peptide_design\scripts\external\run_colabfold_batch.sh
C:\SH\fga_cyclic_peptide_design\scripts\17_parse_colabfold_predictions.py
```

Current prepared job root:

```text
results/colabfold_predictions_top30_seed1
```

Prepared job table:

```text
results/colabfold_predictions_top30_seed1/colabfold_jobs.csv
```

Scope:

```text
source candidates: Boltz top30 near-miss candidates
seeds per candidate: 1
total ColabFold jobs: 30
model_type: alphafold2_multimer_v3
msa_mode: single_sequence
num_models: 1
num_recycle: 0
```

Recommended first pilot:

```bash
cd /mnt/c/SH/fga_cyclic_peptide_design
export PROJECT_DIR="/mnt/c/SH/fga_cyclic_peptide_design"
export JOBS_CSV="results/colabfold_predictions_top30_seed1/colabfold_jobs.csv"
export GPU_LIST=0,1
export MAX_JOBS=2
export MAX_RETRIES=1
export COLABFOLD_TIMEOUT_SECONDS=7200
export COLABFOLD_OVERRIDE=false

bash scripts/external/run_colabfold_batch.sh
```

If pilot passes, run all prepared jobs:

```bash
export MAX_JOBS=0
bash scripts/external/run_colabfold_batch.sh
```

Parse after completion:

```bash
cd /mnt/c/SH/fga_cyclic_peptide_design
/home/luomi/fga_model_envs/boltz2/bin/python scripts/17_parse_colabfold_predictions.py \
  --jobs-csv results/colabfold_predictions_top30_seed1/colabfold_jobs.csv \
  --output-root results/colabfold_predictions_top30_seed1
```

Expected parser outputs:

```text
results/colabfold_predictions_top30_seed1/FGA_colabfold_seed_scores.csv
results/colabfold_predictions_top30_seed1/FGA_colabfold_complex_prediction_summary.csv
```
