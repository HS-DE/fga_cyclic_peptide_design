
0. 项目名称

针对人源 FGA / fibrinogen alpha chain 的 Cys-Cys 二硫键环肽候选设计流程

1. 项目背景

本项目的目标不是开发药物，也不是做完整实验验证，而是先完成 计算端候选环肽序列设计。

用户提供了一个高丰度血浆蛋白信息表：

高丰度蛋白信息.xlsx

其中包含多个血浆高丰度蛋白的 UniProt ID、Gene、估算丰度和蛋白序列。本阶段只针对：

Gene: FGA
UniProt: P02671
Protein: Fibrinogen alpha chain

进行候选环肽设计。

FGA 是 fibrinogen 的 alpha chain。在真实血浆中，FGA 通常不是孤立单链，而是 fibrinogen 复合体的一部分。因此，本项目的设计对象应理解为：

native fibrinogen 复合体中暴露的 FGA 区域

而不是孤立的 full-length FGA 单链。

RCSB PDB 中的 3GHG 是 human fibrinogen 的实验结构，可作为优先结构来源；该结构为 X-ray 结构，RCSB 页面标注其为 human fibrinogen，分辨率为 2.90 Å。
ColabDesign-cyclic-binder 是基于 AfDesign binder hallucination 的 cyclic peptide binder hallucination 实现，使用 cyclic peptide complex offset 来支持 cyclic peptide–target complex 的结构预测/幻觉设计。
RFdiffusion 是开源结构生成方法，支持 binder design，并在官方 README 中列出了 RFpeptides macrocycle design 相关内容，可作为后续增强路线。

2. 项目总目标

为 FGA / native fibrinogen 中暴露的 FGA 区域生成一批计算候选环肽序列。

最终输出：

results/final/FGA_top50_candidates.csv
results/final/FGA_top10_synthesis_priority.csv
results/final/FGA_design_report.md

候选肽统一采用方案 A：

Biotin-PEG4-GSG-CXXXXXXXXC-NH2

其中：

Biotin-PEG4-GSG = 后续固定到 streptavidin magnetic beads 的连接设计
CXXXXXXXXC      = 核心 Cys-Cys 二硫键环肽
-NH2            = C 端酰胺化

本项目只输出计算候选，不进行实验验证。

3. 最高优先级规则

以下规则必须严格遵守。

3.1 不允许直接编造最终肽段

不能随机写出几条 CXXXXXXXXC 当作最终结果。
所有最终候选必须来自以下流程之一：

结构表位选择
→ 候选生成
→ 序列硬过滤
→ 复合物预测或 docking 评分
→ 可合成性过滤
→ 负筛选
→ 综合排序

如果由于环境限制无法运行真实生成模型，也必须输出：

可运行的 pipeline
配置文件
任务脚本
占位说明
示例 toy 输出
明确标记为 demo，不得冒充真实候选
3.2 不允许把 FGA full-length precursor 当作唯一靶标

用户附件中的 FGA 序列是 full-length sequence。
计算时必须至少生成以下三个 FASTA：

FGA_full_length_1_866.fasta
FGA_extracellular_20_866.fasta
FGA_chain_36_866.fasta

主设计对象优先使用：

FGA_chain_36_866

原因：

1–19 aa 为 signal peptide，不能作为真实血浆靶点；
20–35 aa 为 fibrinopeptide A，存在被切除风险；
36–866 aa 更适合作为第一版主设计区域。
3.3 不允许只基于 AlphaFold 单链设计

FGA 在血浆中主要处于 fibrinogen 复合体环境中。
因此结构来源优先级为：

1. native human fibrinogen experimental structure，例如 PDB 3GHG
2. 其他 human fibrinogen / fibrinogen fragment 实验结构
3. AlphaFold P02671 单链结构，仅作为补充
3.4 只做方案 A

本阶段只做：

Cys-Cys disulfide cyclic peptide

不做：

Lys-Glu lactam cyclic peptide
click cyclization
head-to-tail cyclization
linear peptide binder
miniprotein binder
3.5 最终合成格式必须统一

所有最终候选都必须写成：

Biotin-PEG4-GSG-[core_sequence]-NH2

例如：

Biotin-PEG4-GSG-CXXXXXXXXXXC-NH2

其中 [core_sequence] 必须：

以 C 开头
以 C 结尾
内部不含额外 Cys
长度 10–18 aa
主力长度 12–16 aa
3.6 不写湿实验操作方案

本任务书不要求 Codex 写后续实验步骤。
可以在报告中简单说明这些候选用于未来磁珠去除验证，但不要展开实验操作流程。

4. 输入文件
4.1 用户输入

原始文件：

高丰度蛋白信息.xlsx

文件列名预期为：

UniprotID
Gene
estimated_ng_per_ml
Sequence

Codex 需要从中提取：

Gene == "FGA"
或
UniprotID == "P02671"
4.2 FGA 输入信息

从用户文件中提取后，生成：

data/input/FGA_from_template.xlsx
data/input/FGA_full_length_1_866.fasta
data/input/FGA_extracellular_20_866.fasta
data/input/FGA_chain_36_866.fasta

FASTA 命名规则：

>FGA_P02671_full_length_1_866
>FGA_P02671_extracellular_20_866
>FGA_P02671_chain_36_866
4.3 结构输入

优先下载或使用本地已有：

data/structures/raw/3GHG.pdb

如果无法联网下载，则要求用户手动放置：

data/structures/raw/3GHG.pdb

可选辅助结构：

data/structures/raw/AF-P02671-F1-model_v4.pdb
5. 输出文件
5.1 中间输出
data/annotations/FGA_regions.csv
data/annotations/FGA_structure_mapping.csv
data/annotations/FGA_surface_residues.csv
data/annotations/FGA_epitope_candidates.csv
results/raw_designs/FGA_raw_candidates.csv
results/filtered/FGA_hard_filtered_candidates.csv
results/complex_predictions/FGA_complex_prediction_summary.csv
results/filtered/FGA_scored_candidates.csv
results/filtered/FGA_negative_screen_summary.csv
5.2 最终输出
results/final/FGA_top50_candidates.csv
results/final/FGA_top10_synthesis_priority.csv
results/final/FGA_design_report.md
6. 推荐项目目录结构

Codex 需要创建以下目录结构：

fga_cyclic_peptide_design/
├── README.md
├── TASK_FGA_CYCLIC_PEPTIDE_DESIGN.md
├── config/
│   └── project.yaml
├── data/
│   ├── input/
│   │   ├── 高丰度蛋白信息.xlsx
│   │   ├── FGA_from_template.xlsx
│   │   ├── FGA_full_length_1_866.fasta
│   │   ├── FGA_extracellular_20_866.fasta
│   │   └── FGA_chain_36_866.fasta
│   ├── structures/
│   │   ├── raw/
│   │   │   ├── 3GHG.pdb
│   │   │   └── AF-P02671-F1-model_v4.pdb
│   │   └── prepared/
│   │       ├── fibrinogen_3GHG_clean.pdb
│   │       ├── FGA_visible_regions.pdb
│   │       └── FGA_target_patches.pdb
│   └── annotations/
│       ├── FGA_regions.csv
│       ├── FGA_structure_mapping.csv
│       ├── FGA_surface_residues.csv
│       └── FGA_epitope_candidates.csv
├── scripts/
│   ├── 00_check_environment.py
│   ├── 01_extract_fga_sequence.py
│   ├── 02_prepare_fga_regions.py
│   ├── 03_prepare_structures.py
│   ├── 04_map_fga_structure.py
│   ├── 05_select_surface_patches.py
│   ├── 06_make_design_jobs.py
│   ├── 07_collect_raw_designs.py
│   ├── 08_filter_sequences.py
│   ├── 09_prepare_complex_prediction_jobs.py
│   ├── 10_score_complex_predictions.py
│   ├── 11_negative_screen.py
│   ├── 12_rank_candidates.py
│   └── 13_export_final_report.py
├── notebooks/
│   └── FGA_candidate_review.ipynb
├── tests/
│   ├── test_sequence_filters.py
│   ├── test_region_extraction.py
│   ├── test_candidate_schema.py
│   └── test_ranking_logic.py
├── results/
│   ├── raw_designs/
│   ├── complex_predictions/
│   ├── filtered/
│   └── final/
├── logs/
├── env/
│   └── environment.yml
└── run_pipeline.py
7. 配置文件要求

创建：

config/project.yaml

内容建议如下：

project:
  name: fga_cyclic_peptide_design
  target_gene: FGA
  target_uniprot: P02671
  target_description: "Human fibrinogen alpha chain; design should focus on FGA regions exposed in native fibrinogen."

input:
  excel_file: "data/input/高丰度蛋白信息.xlsx"
  gene_column: "Gene"
  uniprot_column: "UniprotID"
  sequence_column: "Sequence"
  abundance_column: "estimated_ng_per_ml"

target_regions:
  full_length:
    start: 1
    end: 866
    use_for_design: false
    note: "Full-length precursor; keep for record only."
  extracellular:
    start: 20
    end: 866
    use_for_design: true
    note: "Signal peptide removed."
  main_chain:
    start: 36
    end: 866
    use_for_design: true
    preferred: true
    note: "Avoids fibrinopeptide A as primary target."

structures:
  primary_pdb: "3GHG"
  primary_pdb_file: "data/structures/raw/3GHG.pdb"
  cleaned_pdb_file: "data/structures/prepared/fibrinogen_3GHG_clean.pdb"
  alphafold_pdb_file: "data/structures/raw/AF-P02671-F1-model_v4.pdb"
  prefer_native_complex: true

peptide_design:
  scheme: "A"
  cyclization: "Cys-Cys disulfide"
  final_format_prefix: "Biotin-PEG4-GSG-"
  final_format_suffix: "-NH2"
  core_length_min: 10
  core_length_max: 18
  preferred_core_lengths: [12, 14, 16]
  terminal_residue: "C"
  forbid_internal_cys: true

generation:
  total_raw_designs_target: 5000
  patches:
    Patch_A:
      description: "Stable visible exposed FGA surface in 3GHG"
      n_designs: 2000
      priority: high
    Patch_B:
      description: "FGA 36-200 visible exposed surface"
      n_designs: 2000
      priority: medium
    Patch_C:
      description: "FGA C-terminal / alphaC-related exploratory region"
      n_designs: 1000
      priority: exploratory
  length_distribution:
    10: 0.10
    12: 0.30
    14: 0.30
    16: 0.20
    18: 0.10

sequence_filters:
  max_hydrophobic_run: 4
  net_charge_min: -3
  net_charge_max: 3
  max_w_count: 1
  max_m_count: 1
  forbid_low_complexity: true
  forbid_poly_basic: true
  forbid_poly_acidic: true

complex_prediction:
  run_prediction: true
  prediction_engines:
    - "colabfold"
    - "boltz2_optional"
  seeds_per_candidate: 5
  require_patch_consistency: true

scoring_thresholds:
  max_interface_pae: 10.0
  min_peptide_plddt: 70.0
  min_interface_contacts: 8
  min_iptm_soft: 0.50
  min_iptm_preferred: 0.65
  require_cys_geometry_pass: true

negative_screen:
  enabled: true
  targets:
    - ALB
    - APOA1
    - TF
    - A2M
    - C3
    - IGG_FC
  purpose: "Remove obviously sticky non-specific peptides."

ranking:
  top_n_candidates: 50
  top_n_synthesis_priority: 10

report:
  language: "zh-CN"
  include_warnings: true
  do_not_claim_experimental_validation: true
8. 每个脚本的职责
8.1 00_check_environment.py

职责：

检查 Python 版本
检查必须包是否安装
检查目录是否存在
检查输入 Excel 是否存在
检查 3GHG.pdb 是否存在
输出环境检查日志

必须检查：

python >= 3.10
pandas
numpy
biopython
pyyaml
openpyxl
scipy
scikit-learn
pytest

可选检查：

freesasa
mdtraj
pymol
colabfold_batch
boltz

要求：

如果可选依赖不存在，不要中断整个流程；
只在日志中写 warning。
8.2 01_extract_fga_sequence.py

职责：

读取 data/input/高丰度蛋白信息.xlsx
提取 Gene == FGA 或 UniprotID == P02671 的记录
校验序列是否存在
输出 FGA_from_template.xlsx
输出 full-length FASTA

要求：

不能硬编码用户序列。
必须从 Excel 读取。
如果找不到 FGA，则报错并说明需要检查列名或 Gene/UniprotID。
8.3 02_prepare_fga_regions.py

职责：

基于 full-length FGA sequence 生成三个区域 FASTA：
1. FGA_full_length_1_866.fasta
2. FGA_extracellular_20_866.fasta
3. FGA_chain_36_866.fasta

输出：

data/annotations/FGA_regions.csv

字段：

region_name
start
end
length
use_for_design
priority
note
sequence

必须包含：

full_length_1_866
extracellular_20_866
chain_36_866
8.4 03_prepare_structures.py

职责：

准备 3GHG 结构
清理 PDB
去除水分子
去除非必要小分子
保留蛋白链
输出 clean PDB

输入：

data/structures/raw/3GHG.pdb

输出：

data/structures/prepared/fibrinogen_3GHG_clean.pdb

规则：

如果 data/structures/raw/3GHG.pdb 不存在：
  1. 如果允许联网，尝试从 RCSB 下载；
  2. 如果无法下载，生成明确错误信息，提示用户手动放入文件。

不要静默失败。

8.5 04_map_fga_structure.py

职责：

识别 3GHG 中对应 FGA 的 chain
建立 PDB residue 编号和 UniProt residue 编号之间的映射
输出结构中可见的 FGA 区域

输出：

data/annotations/FGA_structure_mapping.csv
data/structures/prepared/FGA_visible_regions.pdb

字段：

pdb_id
chain_id
pdb_residue_number
pdb_residue_name
uniprot_id
uniprot_residue_number
uniprot_residue_name
mapping_confidence
is_visible

规则：

不能假设 chain ID 一定固定。
必须通过序列比对或 PDB chain annotation 判断。
如果 mapping 不确定，必须在报告中标记。
8.6 05_select_surface_patches.py

职责：

识别 FGA 在 native fibrinogen 结构中的表面暴露残基
根据暴露残基聚类生成候选设计 patch

推荐方法：

优先使用 freesasa 计算 SASA；
如果 freesasa 不可用，使用 residue neighbor count 作为近似暴露度；
对暴露残基做空间聚类；
输出 Patch_A / Patch_B / Patch_C 候选区域。

输出：

data/annotations/FGA_surface_residues.csv
data/annotations/FGA_epitope_candidates.csv
data/structures/prepared/FGA_target_patches.pdb

FGA_epitope_candidates.csv 字段：

patch_id
patch_type
chain_id
uniprot_residue_numbers
pdb_residue_numbers
center_x
center_y
center_z
n_surface_residues
mean_sasa
priority
risk_level
note

Patch 定义规则：

Patch_A:
  3GHG 中结构可见、表面暴露、空间聚类稳定的 FGA 区域。
  最高优先级。

Patch_B:
  FGA 36–200 附近结构可见、表面暴露的区域。
  中等优先级。

Patch_C:
  FGA C-terminal / alphaC 相关或结构不完整区域。
  只作为探索，高风险。
8.7 06_make_design_jobs.py

职责：

根据 FGA_epitope_candidates.csv 生成环肽设计任务。

输出：

results/raw_designs/design_jobs.csv
results/raw_designs/colabdesign_jobs/
results/raw_designs/rfdiffusion_jobs_optional/

每个 design job 至少包含：

job_id
target_pdb
patch_id
hotspot_residues
peptide_length
n_designs
method
output_dir
command_or_notebook
status

规则：

主路线：ColabDesign-cyclic-binder
备用路线：RFdiffusion / RFpeptides

如果本地没有安装模型，不要伪造输出。
应该生成：

可执行命令模板
notebook 运行说明
待运行 job 表
8.8 07_collect_raw_designs.py

职责：

收集模型生成的 raw candidate peptide sequences。

输入可能包括：

ColabDesign 输出
RFdiffusion 输出
用户手动放入的 candidate csv

输出：

results/raw_designs/FGA_raw_candidates.csv

字段：

raw_id
method
job_id
patch_id
target_region
core_sequence
core_length
raw_score
source_file
notes

规则：

如果没有真实模型输出，只允许生成 demo 文件：
results/raw_designs/FGA_raw_candidates.demo.csv

demo 文件不得进入最终 top10。
8.9 08_filter_sequences.py

职责：

对 raw candidates 做硬性序列过滤。

过滤规则：

1. core_sequence 必须以 C 开头
2. core_sequence 必须以 C 结尾
3. core_sequence 内部不能含 C
4. core length 必须在 10–18 aa
5. 净电荷必须在 -3 到 +3
6. 不允许连续 4 个以上强疏水残基
7. W 数量 <= 1
8. M 数量 <= 1
9. 不允许明显低复杂度序列
10. 不允许 poly-K/poly-R/poly-D/poly-E

输出：

results/filtered/FGA_hard_filtered_candidates.csv

额外添加字段：

starts_with_cys
ends_with_cys
internal_cys_count
core_length_pass
net_charge
charge_pass
hydrophobic_run_max
hydrophobicity_pass
w_count
m_count
low_complexity_flag
sequence_filter_pass
filter_notes
8.10 09_prepare_complex_prediction_jobs.py

职责：

为 hard-filtered candidates 准备复合物预测任务。

任务：

target structure + candidate peptide
每条候选至少 5 个 seed

输出：

results/complex_predictions/complex_prediction_jobs.csv

字段：

prediction_job_id
peptide_id
core_sequence
target_pdb
patch_id
seed
engine
input_fasta
output_dir
command
status

规则：

优先支持 ColabFold / AlphaFold-Multimer 输出格式；
可选支持 Boltz-2；
如果工具不存在，只生成 job 文件和说明，不伪造预测分数。
8.11 10_score_complex_predictions.py

职责：

解析复合物预测结果，计算结构和界面评分。

输入：

ColabFold / AlphaFold-Multimer / Boltz-2 输出

输出：

results/complex_predictions/FGA_complex_prediction_summary.csv
results/filtered/FGA_scored_candidates.csv

需要计算或解析：

ipTM
pTM
interface PAE
peptide pLDDT
interface contact count
peptide-target minimum distance
peptide patch consistency
multi-seed pose consistency
Cys-Cys geometry

Cys-Cys geometry 检查：

检查核心肽首尾 Cys 是否在预测结构中空间接近；
如果存在 SG 原子，优先使用 SG-SG distance；
如果没有 SG 原子，用 CA-CA distance 近似；
不满足合理几何的候选标记为 fail 或 warning。

输出字段：

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
8.12 11_negative_screen.py

职责：

对 top candidates 做负筛选，排除明显非特异 sticky peptide。

负筛目标：

ALB
APOA1
TF
A2M
C3
IGG_FC

注意：

负筛不是为了证明绝对不结合；
只是为了排除预测中明显到处都强结合的脏肽。

输出：

results/filtered/FGA_negative_screen_summary.csv

字段：

peptide_id
negative_target
negative_score
negative_interface_pae
negative_contacts
non_specific_risk
negative_screen_pass
notes
8.13 12_rank_candidates.py

职责：

综合序列过滤、复合物评分、负筛选结果，对候选肽排序。

综合评分建议：

final_score =
  0.35 * normalized_complex_score
+ 0.20 * patch_consistency_score
+ 0.15 * cys_geometry_score
+ 0.15 * synthesis_score
+ 0.15 * negative_screen_score

必须输出：

results/final/FGA_top50_candidates.csv
results/final/FGA_top10_synthesis_priority.csv

最终表字段必须包括：

peptide_id
target
target_uniprot
target_patch
uniprot_region
hotspot_residues
core_sequence
core_length
final_synthesis_format
cyclization
mean_iptm
best_iptm
mean_interface_pae
best_interface_pae
peptide_plddt
interface_contacts
pose_consistency_rmsd
cys_cys_geometry
net_charge
hydrophobicity_flag
sequence_filter_pass
negative_screen_flag
final_score
priority
notes

final_synthesis_format 必须自动生成：

Biotin-PEG4-GSG-{core_sequence}-NH2
8.14 13_export_final_report.py

职责：

生成中文设计报告。

输出：

results/final/FGA_design_report.md

报告必须包括：

1. 项目目的
2. 输入数据说明
3. 为什么不用 full-length precursor 直接设计
4. 为什么优先考虑 native fibrinogen 中暴露的 FGA 区域
5. 结构来源说明
6. patch 选择方法
7. 环肽设计规则
8. 序列过滤规则
9. 复合物预测评分规则
10. 负筛选规则
11. top10 候选表
12. 风险和限制
13. 下一步建议

报告中必须明确写：

这些序列是计算生成的候选环肽 binder；
尚未经过实验验证；
不能宣称具有已验证结合能力；
后续需要合成和实验验证。
9. 候选肽硬过滤细则

实现函数：

filter_candidate_sequence(seq: str) -> dict

必须检查：

9.1 长度
10 <= len(seq) <= 18
9.2 端点 Cys
seq[0] == "C"
seq[-1] == "C"
9.3 内部 Cys
seq[1:-1] 不允许含 C
9.4 净电荷

简化计算：

K, R = +1
D, E = -1
H 可先按 0 或 +0.1，默认 0

要求：

-3 <= net_charge <= +3
9.5 疏水连续片段

强疏水残基定义：

A, V, I, L, M, F, W, Y

不允许：

连续强疏水残基 > 4
9.6 氧化风险
W <= 1
M <= 1
9.7 低复杂度

不允许：

AAAA
KKKK
RRRR
DDDD
EEEE
GGGG
SSSS

也不允许明显重复：

GSGSGS
PAPAPA

低复杂度检测可以先实现简单版本。

10. 评分规则
10.1 复合物预测基础要求

候选必须满足：

peptide 贴在 FGA 指定 patch 附近
多 seed 预测姿势基本一致
interface PAE 尽量 < 10
peptide pLDDT 尽量 > 70
interface contacts >= 8
Cys-Cys geometry pass
10.2 Patch consistency

定义：

如果 5 个 seeds 中至少 3 个预测肽结合在目标 patch 附近，则 pass；
否则 warning 或 fail。
10.3 Cys-Cys geometry

定义：

优先用 SG-SG distance；
如果无法获得 SG 原子，用 CA-CA distance 近似；
如果距离明显过远，则 fail。
10.4 负筛选

如果候选对多个非目标蛋白也表现出强结合预测，则：

negative_screen_flag = fail
priority 降级
11. 测试要求

必须写 pytest 测试。

11.1 test_sequence_filters.py

测试内容：

CXXXXXXXXC 合格
非 C 开头失败
非 C 结尾失败
内部 Cys 失败
长度过短失败
长度过长失败
净电荷过高失败
疏水连续片段过长失败
11.2 test_region_extraction.py

测试内容：

full-length 长度是否正确
20–866 区域是否正确
36–866 区域是否正确
FASTA header 是否正确
11.3 test_candidate_schema.py

测试内容：

最终候选表是否包含所有必需字段
final_synthesis_format 是否正确拼接
11.4 test_ranking_logic.py

测试内容：

高 complex score 候选排名更高
negative screen fail 候选排名下降
cys geometry fail 候选不能进入 top10
12. 代码风格要求
12.1 注释

所有 Python 脚本必须有清晰中文注释，按照步骤写：

# =====================
# Step 1. 读取输入文件
# =====================
12.2 日志

所有脚本必须输出日志到：

logs/

日志内容包括：

运行时间
输入文件
输出文件
候选数量变化
warning
error
12.3 不允许静默失败

如果某一步无法继续，必须报错并说明：

缺少什么文件
缺少什么依赖
应该如何补齐
12.4 可重复运行

脚本必须支持重复运行。
如果输出文件已存在，应：

覆盖输出
或
通过 --overwrite 参数控制

不要因为文件已存在直接崩溃。

13. run_pipeline.py 要求

创建一个总入口：

python run_pipeline.py --config config/project.yaml

它应按顺序执行：

00_check_environment.py
01_extract_fga_sequence.py
02_prepare_fga_regions.py
03_prepare_structures.py
04_map_fga_structure.py
05_select_surface_patches.py
06_make_design_jobs.py
07_collect_raw_designs.py
08_filter_sequences.py
09_prepare_complex_prediction_jobs.py
10_score_complex_predictions.py
11_negative_screen.py
12_rank_candidates.py
13_export_final_report.py

如果某些重型步骤无法本地运行，例如 ColabDesign、RFdiffusion、ColabFold、Boltz-2，则 pipeline 应该：

生成任务文件
提示用户到相应环境运行
等待用户把输出文件放回指定目录
然后继续后续解析和评分

不能伪造模型结果。

14. README.md 要求

README.md 必须包含：

项目目的
目录结构
环境安装
输入文件要求
如何运行
每一步输出什么
如何接入 ColabDesign-cyclic-binder
如何接入 RFdiffusion/RFpeptides
如何接入 ColabFold/Boltz-2
如何查看最终 top10
常见错误

最小运行命令：

conda env create -f env/environment.yml
conda activate fga-cyclic-design
python run_pipeline.py --config config/project.yaml
15. environment.yml 要求

创建：

env/environment.yml

建议内容：

name: fga-cyclic-design
channels:
  - conda-forge
  - bioconda
dependencies:
  - python=3.10
  - pandas
  - numpy
  - scipy
  - scikit-learn
  - biopython
  - openpyxl
  - pyyaml
  - pytest
  - matplotlib
  - pip
  - pip:
      - tqdm

可选依赖在 README 中说明：

freesasa
mdtraj
colabfold
boltz
pymol

不要强制用户一定安装所有重型工具才能跑基础流程。

16. 最终报告中的风险说明

FGA_design_report.md 必须包含以下风险说明：

1. FGA 在血浆中主要位于 fibrinogen 复合体中，因此单链预测存在偏差。
2. 3GHG 是实验结构，但不一定覆盖 FGA 全部柔性区域。
3. FGA alphaC 等区域可能柔性较高，相关候选应标记为 exploratory/high risk。
4. Cys-Cys 二硫键环肽在计算结构中需要检查首尾 Cys 几何合理性。
5. Biotin-PEG4-GSG linker 未必完整进入结构模型，因此最终磁珠固定后的表现仍需实验验证。
6. 所有候选均为计算候选，不能宣称已验证结合。
7. 负筛选只能降低明显非特异风险，不能证明绝对特异。
17. 完成标准

Codex 完成任务后，项目目录中必须至少存在：

config/project.yaml
env/environment.yml
README.md
run_pipeline.py
scripts/*.py
tests/*.py
data/input/FGA_full_length_1_866.fasta
data/input/FGA_extracellular_20_866.fasta
data/input/FGA_chain_36_866.fasta
data/annotations/FGA_regions.csv
results/final/FGA_design_report.md

如果没有真实模型输出，则可以没有真实 top10，但必须有：

results/raw_designs/design_jobs.csv
results/complex_predictions/complex_prediction_jobs.csv
results/final/FGA_design_report.md

并且报告中明确写：

当前尚未运行真实生成/复合物预测模型，因此没有可用于合成的真实候选序列。

如果已经提供真实模型输出，则必须生成：

results/final/FGA_top50_candidates.csv
results/final/FGA_top10_synthesis_priority.csv
18. 绝对禁止事项

Codex 不得：

1. 随机编造 top10 肽段并当作真实候选。
2. 把 demo 序列写入最终合成优先级表。
3. 声称候选肽已经实验验证。
4. 声称候选肽一定能结合 FGA。
5. 忽略 FGA signal peptide / mature chain 问题。
6. 只使用孤立 FGA AlphaFold 结构而不考虑 native fibrinogen。
7. 输出没有评分依据的候选。
8. 输出没有 final_synthesis_format 的候选。
9. 输出内部含额外 Cys 的方案 A 候选。
10. 写湿实验 SOP。
19. 推荐执行顺序

第一轮先做基础 pipeline，不跑重型模型：

python run_pipeline.py --config config/project.yaml --mode prepare
pytest

确认可以生成：

FGA FASTA
FGA regions
structure preparation jobs
surface patch candidates
design jobs

第二轮接入生成模型：

python scripts/06_make_design_jobs.py --config config/project.yaml

然后手动或在 GPU 环境运行 ColabDesign-cyclic-binder / RFdiffusion。

第三轮解析模型输出：

python scripts/07_collect_raw_designs.py --config config/project.yaml
python scripts/08_filter_sequences.py --config config/project.yaml

第四轮接入复合物预测：

python scripts/09_prepare_complex_prediction_jobs.py --config config/project.yaml

运行 ColabFold/Boltz-2 后：

python scripts/10_score_complex_predictions.py --config config/project.yaml
python scripts/11_negative_screen.py --config config/project.yaml
python scripts/12_rank_candidates.py --config config/project.yaml
python scripts/13_export_final_report.py --config config/project.yaml
20. 最终交付给用户的解释口径

最终报告或 README 中可以这样写：

本项目针对 human FGA / fibrinogen alpha chain / UniProt P02671，建立了一套 Cys-Cys 二硫键环肽计算设计流程。设计对象优先限定为 native fibrinogen 结构中暴露的 FGA 区域，而不是 full-length precursor 或孤立 FGA 单链。候选肽统一采用 Biotin-PEG4-GSG-CXXXXXXXXC-NH2 格式，以便后续固定到 streptavidin magnetic beads。所有候选均经过序列硬过滤、复合物预测评分、Cys-Cys 几何检查、可合成性过滤和负筛选排序。当前输出为计算候选，尚需后续合成和实验验证。