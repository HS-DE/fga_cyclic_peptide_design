# FGA Cys-Cys 环肽设计项目：Boltz-2 复合物预测第一轮阶段性报告

日期：2026-06-05

项目目录：`C:\SH\fga_cyclic_peptide_design`

报告范围：本报告总结 FGA Cys-Cys 二硫键环肽设计项目中，基于 Boltz-2 的第一轮全量复合物预测筛查结果。本轮重点是验证候选环肽与 FGA 目标 patch 的复合物预测可行性，并用统一评分标准筛选是否存在可进入下一阶段的候选。

## 1. 一句话摘要

本项目目标是针对人 FGA，也就是 fibrinogen alpha chain，设计首尾 Cys-Cys 二硫键环化的短肽，使其尽可能结合 FGA 在实验结构 3GHG 中可见且暴露的表面区域。

本轮已经完成 302 条 hard-filtered candidate peptides 的 Boltz-2 复合物预测。302 个 Boltz 任务全部成功运行并输出结构文件，运行失败数为 0。

但是，按当前项目设定的严格结构评分门槛，没有任何候选同时满足界面可信度、肽段局部可信度、目标 patch 一致性、界面接触数量和 Cys-Cys 几何要求。因此，本轮结果是一次成功完成的真实模型筛查，但筛查结论为阴性。本轮不产生 synthesis-ready final peptide，也不建议直接进入合成。

## 2. 项目背景与设计目标

FGA 是人 fibrinogen alpha chain，对应 UniProt ID `P02671`。本项目关注的是血浆纤维蛋白原相关结构中 FGA 的可暴露表面区域，希望设计可以识别或结合这些区域的短环肽。

选择 Cys-Cys 二硫键环肽的原因是：短肽本身柔性较高，首尾 Cys 形成二硫键后可以限制构象自由度，提高结构稳定性，并让候选肽更接近一个可控的环状结合体。项目当前设计的 core peptide 形式是：

```text
CxxxxxxxxC
```

也就是首位和末位为 Cys，中间不允许出现额外 Cys，避免产生非预期二硫键连接。

需要特别强调：本项目不能直接凭经验给出最终肽段。每条候选都必须经过真实模型生成、硬过滤、复合物预测和评分、负筛选、最终排序和人工复核后，才能被称为最终推荐肽段。本轮只完成到 Boltz-2 复合物预测与初步结构评分阶段。

## 3. 当前项目流程总览

当前项目流程可以概括为：

```text
输入 Excel / FGA 序列
-> FGA 区域划分
-> 3GHG 实验结构准备
-> FGA 可见区域映射
-> 表面 patch 选择
-> ColabDesign 生成 Cys-Cys 环肽候选
-> 序列硬过滤
-> Boltz-2 复合物预测
-> parser 提取结构评分
-> 后续负筛选
-> 最终排序和人工复核
```

本轮已经完成到：

```text
Boltz-2 复合物预测
parser 结构评分
```

尚未完成：

```text
负筛选
多 seed 稳定性复核
最终排序
人工结构复核
实验验证
```

## 4. 输入数据与结构依据

本项目使用的关键输入包括：

```text
FGA 序列来源:
data/input/FGA_chain_36_866.fasta

主要实验结构:
data/structures/raw/3GHG.pdb

清洗后的结构:
data/structures/prepared/fibrinogen_3GHG_clean.pdb

本轮 Boltz template:
data/structures/raw/3GHG.pdb
```

### 4.1 为什么使用 3GHG

3GHG 是实验结构，包含 fibrinogen 中被实验解析到的可见区域。虽然它不是完整 FGA 全长结构，但对本项目很重要，因为项目目标不是任意区域，而是实验结构中可见、稳定、可暴露的 FGA 表面 patch。

换句话说，完整 FGA 单体预测模型可以作为辅助参考，但 3GHG 中的可见表面更接近本项目要设计结合的真实结构背景。

### 4.2 clean PDB 与 raw PDB 的区别

项目中有两个 3GHG 相关 PDB：

```text
raw 3GHG:
data/structures/raw/3GHG.pdb

clean 3GHG:
data/structures/prepared/fibrinogen_3GHG_clean.pdb
```

最初尝试把 clean PDB 作为 Boltz template 时，Boltz 在输入解析阶段失败。原因是 clean PDB 保留了 ATOM 坐标，但缺少 SEQRES 记录。Boltz 在解析 PDB template 时会将 PDB 转换成类似 mmCIF 的结构，并对齐模板链的 full sequence 和实际坐标残基。如果缺少完整序列信息，就可能在 template parsing 阶段失败。

因此，本轮改用 raw `3GHG.pdb` 作为 template。raw PDB 包含 SEQRES 信息，可以被 Boltz 正常解析。

### 4.3 template 链映射修正

3GHG 中 FGA 目标链在项目映射中使用链 `J`。Boltz 解析 PDB template 时，会把原始 PDB 链转换为 subchain 名称。实际解析结果显示：

```text
PDB chain J -> Boltz template chain J1
```

因此，本轮 Boltz YAML 中使用：

```yaml
templates:
  - pdb: data/structures/raw/3GHG.pdb
    chain_id: A
    template_id: J1
```

其中 `chain_id: A` 是 Boltz 输入中的 FGA 链，`template_id: J1` 是 raw 3GHG 被 Boltz 解析后的模板链名。

## 5. 候选环肽生成阶段

候选肽不是手写生成的，而是来自 ColabDesign cyclic binder 设计流程。生成阶段的核心约束包括：

```text
首尾 Cys 固定
内部 Cys 禁止
使用 GREEDY_ITERS > 0 进行序列优化
记录 final_sequence_changed
记录 terminal_cys_mutation_lock
```

这一步很关键，因为项目早期曾出现过 `GREEDY_ITERS=0` 导致候选序列没有真正优化的问题。后续脚本已经增加了 guardrail，不把未优化候选当作生产候选。

进入本轮 Boltz 的候选数量如下：

```text
硬过滤候选总表: 437
进入 Boltz jobs: 302
被跳过: 135
跳过原因: sequence_filter_pass=false
```

本轮的 302 条候选都来自 hard-filtered candidate peptides。

## 6. Boltz-2 复合物预测设置

本轮使用 Boltz-2 进行复合物结构预测。

预测对象为：

```text
FGA target chain A
candidate peptide chain B
```

输入约束包括：

```text
1. FGA sequence
2. candidate peptide sequence
3. peptide 首尾 Cys SG-SG bond constraint
4. Patch_A / Patch_B pocket contact constraint
5. raw 3GHG template
```

本轮运行参数：

```text
Boltz jobs: 302
seed: 1 per candidate
GPU: 2 x NVIDIA RTX A6000
template: data/structures/raw/3GHG.pdb
template chain mapping: J -> J1
output_format: pdb
MSA mode: empty / single-sequence mode
use_potentials: true
```

需要注意：本轮设置为 `MSA mode: empty`，也就是单序列模式。这有利于快速完成第一轮全量筛查，但可能降低模型对 FGA 和肽段构象的置信度。因此，本轮结果应被视为第一轮结构筛查，而不是最终多 seed / 多模型确认结果。

## 7. 判断是否通过的指标

本项目不会只看单一指标，而是综合多个指标判断一个候选是否可以进入下一阶段。当前 parser 输出两个层级的结果：

```text
FGA_boltz_seed_scores.csv:
每个 Boltz seed 的原始结构评分

FGA_boltz_complex_prediction_summary.csv:
按 peptide 汇总后的复合物评分
```

本轮每条 peptide 只跑 1 个 seed，所以 seed-level 和 peptide-level 是一一对应关系。

### 7.1 iPTM

iPTM 是 interface predicted TM-score 相关指标，用于衡量模型对链间相对构象，也就是复合物界面的置信度。取值范围通常在 0 到 1 之间，越高越好。

项目配置中设定：

```text
min_iptm_soft: 0.50
min_iptm_preferred: 0.65
```

含义：

```text
iPTM >= 0.50:
作为软性参考，说明界面可能有一定可信度。

iPTM >= 0.65:
作为优先级参考，说明界面预测更值得复核。
```

为什么这样设定：

```text
FGA-短肽复合物比一般蛋白单体更难预测。
短肽柔性大，界面小，单一 iPTM 高并不能保证可用。
因此 iPTM 只作为排序和解释的重要指标，不能单独决定通过。
```

当前 parser 的 `complex_score_pass` 没有把 iPTM 作为独立硬门槛，而是把 iPTM 纳入 `complex_score` 中参与排序。最终是否通过主要由 PAE、pLDDT、接触、patch 一致性和 Cys-Cys 几何共同决定。

### 7.2 interface PAE

PAE 是 Predicted Aligned Error，用于评估模型对两个残基或两个结构部分相对位置的置信度。数值单位通常可理解为埃级误差，越低越好。

本项目计算的是 FGA 与 peptide 之间的 interface PAE，即模型对 FGA-肽段相对位置的可信程度。

项目阈值：

```text
max_interface_pae: 10.0
```

通过条件：

```text
interface_pae <= 10.0
```

为什么这样设定：

```text
本项目要判断肽段是否真的稳定结合到 FGA patch。
如果 interface PAE 很高，说明模型对 FGA 和肽段之间相对位置不确定。
在这种情况下，即使 PDB 里看起来有接触，也不能可靠认为该复合物构象成立。
10 Å 是一个相对保守的筛选阈值，用来排除界面位置不可信的候选。
```

本轮 302 条中：

```text
interface_pae <= 10: 0 / 302
```

这是本轮没有候选通过的主要原因之一。

### 7.3 peptide pLDDT

pLDDT 是 predicted Local Distance Difference Test，用来表示模型对局部结构的置信度。它主要反映局部残基构象是否可信。通常 70 以上可作为较低限度的可信局部结构参考，90 以上才属于很高置信度。

本项目关注的是 peptide 部分的 pLDDT，而不是整个 FGA 的平均 pLDDT。

项目阈值：

```text
min_peptide_plddt: 70.0
```

通过条件：

```text
peptide_plddt >= 70.0
```

为什么这样设定：

```text
候选是短肽，短肽本身柔性高。
如果 peptide pLDDT 低，说明模型对该肽段局部构象不确定。
低可信的肽段结构不适合作为合成或后续实验设计依据。
```

本轮 302 条中：

```text
peptide_plddt >= 70: 0 / 302
```

这也是本轮没有候选通过的主要原因之一。

### 7.4 interface contacts

interface_contacts 是结构文件中 FGA 与 peptide 之间的接触数量。当前 parser 使用 5 Å heavy-atom contact cutoff 统计接触。

项目阈值：

```text
min_interface_contacts: 8
```

通过条件：

```text
interface_contacts >= 8
```

为什么这样设定：

```text
一个真实候选不应只靠一两个偶然接触。
至少 8 个界面接触可以排除非常弱或几何偶然的贴近。
```

本轮 302 条中：

```text
interface_contacts >= 8: 302 / 302
```

这说明大多数预测结构中确实存在 FGA-肽段接触，但接触存在不等于界面可信。它还必须同时满足 interface PAE、peptide pLDDT 和 Cys-Cys 几何要求。

### 7.5 patch consistency

patch_consistency 用来判断 peptide 是否接触到预设目标 patch。

当前 parser 的规则：

```text
patch_contact_count > 0 -> pass
patch_contact_count = 0 -> fail
```

为什么这样设定：

```text
本项目不是寻找任意 FGA 结合肽，而是寻找能结合指定 FGA 表面 patch 的环肽。
如果预测结构中的 peptide 没有接触目标 patch，即使它接触 FGA 其他区域，也不符合当前设计目标。
```

本轮结果：

```text
patch_contact_count > 0: 277 / 302
Patch_A: 256 pass, 25 fail
Patch_B: 21 pass, 0 fail
```

这说明大部分预测构象能接触目标 patch，但由于界面 PAE 和 peptide pLDDT 不达标，仍不能通过。

### 7.6 Cys-Cys geometry

本项目设计的是 Cys-Cys 二硫键环肽，因此预测结构必须满足合理的 SG-SG 距离。

当前 parser 的判定范围：

```text
1.8 Å <= Cys SG-SG distance <= 2.4 Å
```

通过条件：

```text
cys_cys_geometry = pass
```

为什么这样设定：

```text
真实二硫键的 S-S 距离通常接近 2.0 Å。
设置 1.8-2.4 Å 是为了允许模型预测误差，但仍排除明显不合理的首尾 Cys 几何。
如果 Cys-Cys 几何失败，则该预测构象不能支持“二硫键环化结构合理”这一判断。
```

本轮结果：

```text
cys_cys_geometry pass: 83 / 302
cys_cys_geometry fail: 219 / 302
```

### 7.7 complex_score

complex_score 是项目内部用于排序的综合分数，不是直接的物理结合能，也不是实验亲和力。

当前计算方式来自 `scripts/ranking.py`：

```text
complex_score =
0.35 * iPTM
+ 0.25 * PAE_score
+ 0.20 * peptide_pLDDT_score
+ 0.20 * contact_score
```

其中：

```text
PAE_score = (30 - interface_pae) / 30，限制在 0 到 1
peptide_pLDDT_score = peptide_pLDDT / 100，限制在 0 到 1
contact_score = interface_contacts / 20，限制在 0 到 1
```

为什么这样设定：

```text
iPTM 反映界面整体可信度，权重最高。
PAE 反映相对位置误差，权重第二。
peptide pLDDT 反映短肽自身结构可信度。
contacts 反映界面接触是否足够。
```

但需要强调：complex_score 只是排序指标。最终是否通过仍依赖硬条件，尤其是 interface PAE、peptide pLDDT、patch consistency 和 Cys-Cys geometry。

### 7.8 complex_score_pass

当前 parser 的硬通过条件为：

```text
best_interface_pae <= 10.0
mean_peptide_plddt >= 70.0
interface_contacts >= 8
patch_consistency_flag = pass
cys_cys_geometry = pass
```

全部满足时：

```text
complex_score_pass = True
```

任一不满足时：

```text
complex_score_pass = False
```

本轮结果：

```text
complex_score_pass=True: 0
complex_score_pass=False: 302
```

## 8. 本轮运行结果

Boltz 任务运行层面：

```text
Boltz jobs: 302
成功完成: 302
失败: 0
confidence JSON: 302
PDB structures: 302
parser seed rows: 302
parser peptide summaries: 302
```

复合物评分层面：

```text
complex_score_pass=True: 0
complex_score_pass=False: 302
```

按 patch 分布：

```text
Patch_A: 281
Patch_B: 21
```

patch consistency：

```text
Patch_A pass: 256
Patch_A fail: 25
Patch_B pass: 21
Patch_B fail: 0
```

Cys-Cys geometry：

```text
pass: 83
fail: 219
```

关键指标统计：

```text
mean_iPTM:
mean 0.350, max 0.759

mean_interface_PAE:
mean 28.614, min 21.502

mean_peptide_pLDDT:
mean 40.106, max 66.040

interface_contacts:
mean 47.040, min 11, max 115
```

单项阈值通过数量：

```text
iPTM >= 0.50: 13 / 302
iPTM >= 0.65: 1 / 302
interface_PAE <= 10: 0 / 302
peptide_pLDDT >= 70: 0 / 302
interface_contacts >= 8: 302 / 302
patch_contact_count > 0: 277 / 302
Cys-Cys geometry pass: 83 / 302
```

## 9. 结果解读

本轮不能简单理解为“流程失败”。恰恰相反，计算流程是成功的：

```text
302 个 Boltz 任务全部成功
302 个结构全部生成
302 个结果全部解析
```

真正的结论是：

```text
本轮 302 条 hard-filtered candidates 在 Boltz-2 raw 3GHG template 条件下，没有候选通过严格复合物评分门槛。
```

主要问题集中在三点：

```text
1. interface PAE 整体偏高
   说明模型对 FGA 和 peptide 的相对位置不够有把握。

2. peptide pLDDT 整体偏低
   说明模型对短肽自身构象置信度不足。

3. Cys-Cys geometry 只有 83 条通过
   说明很多预测构象不能支持合理二硫键环化。
```

虽然 302 条都满足 `interface_contacts >= 8`，且 277 条接触到了目标 patch，但这些接触在当前置信度条件下不能被视为可靠结合证据。

因此，本轮不产生最终推荐肽段，也不建议直接合成。

## 10. Near-miss 候选，仅用于后续复核

以下候选按 complex_score 排序靠前，但全部 `complex_score_pass=False`。它们只能作为后续多 seed / MSA / 人工结构复核对象，不能作为最终候选。

| Rank | peptide_id | core_sequence | patch | iPTM | interface_PAE | peptide_pLDDT | contacts | patch | Cys geom | score | pass |
|---:|---|---|---|---:|---:|---:|---:|---|---|---:|---|
| 1 | Patch_A_L14_colabdesign_chunk_seed0000_n005_raw_0004 | CEPTEDGRHYWGFC | Patch_A | 0.7592 | 21.502 | 41.19 | 77 | pass | fail | 0.6189 | False |
| 2 | Patch_A_L16_colabdesign_chunk_seed0065_n005_raw_0005 | CYMRTNEYYHPPWKIC | Patch_A | 0.6351 | 23.659 | 44.90 | 66 | pass | fail | 0.5649 | False |
| 3 | Patch_A_L18_colabdesign_chunk_seed0050_n005_raw_0005 | CHTPNNNNERPYTYVYIC | Patch_A | 0.6111 | 24.474 | 40.94 | 85 | pass | pass | 0.5418 | False |
| 4 | Patch_A_L18_colabdesign_chunk_seed0015_n005_raw_0005 | CYIPPYWGLDYGDTKLTC | Patch_A | 0.6201 | 26.940 | 44.35 | 57 | pass | pass | 0.5312 | False |
| 5 | Patch_A_L12_colabdesign_chunk_seed0020_n005_raw_0002 | CKVNDWTPIVYC | Patch_A | 0.5684 | 25.065 | 41.31 | 55 | pass | fail | 0.5227 | False |
| 6 | Patch_A_L12_colabdesign_chunk_seed0030_n005_raw_0003 | CYYQNDNSIHVC | Patch_A | 0.4923 | 25.196 | 48.97 | 46 | pass | fail | 0.5103 | False |
| 7 | Patch_A_L16_colabdesign_chunk_seed0070_n005_raw_0003 | CYNPVGEEWPIYYVQC | Patch_A | 0.5993 | 26.349 | 34.87 | 79 | pass | fail | 0.5099 | False |
| 8 | Patch_A_L12_colabdesign_chunk_seed0035_n005_raw_0003 | CWQSYRDGTVIC | Patch_A | 0.4907 | 26.169 | 52.43 | 31 | pass | pass | 0.5085 | False |
| 9 | Patch_A_L18_colabdesign_chunk_seed0010_n005_raw_0005 | CVWYHPTDQQGDRQDYIC | Patch_A | 0.4860 | 25.411 | 48.74 | 47 | pass | fail | 0.5058 | False |
| 10 | Patch_A_L14_colabdesign_chunk_seed0050_n005_raw_0001 | CHYRPGHDYQVYVC | Patch_A | 0.4642 | 27.637 | 59.66 | 35 | pass | fail | 0.5015 | False |
| 11 | Patch_A_L14_colabdesign_chunk_seed0075_n005_raw_0005 | CHINRYPDNSYIYC | Patch_A | 0.5907 | 27.877 | 37.75 | 74 | pass | pass | 0.4999 | False |
| 12 | Patch_B_L12_colabdesign_chunk_seed0015_n005_raw_0005 | CPDNHTHVGMRC | Patch_B | 0.4784 | 26.881 | 53.05 | 60 | pass | fail | 0.4995 | False |
| 13 | Patch_B_L12_colabdesign_chunk_seed0025_n005_raw_0004 | CRMRDGRPPNGC | Patch_B | 0.5278 | 27.766 | 46.47 | 65 | pass | fail | 0.4963 | False |
| 14 | Patch_B_L12_colabdesign_chunk_seed0020_n005_raw_0005 | CWYPPDDPKYQC | Patch_B | 0.3958 | 27.526 | 66.04 | 28 | pass | fail | 0.4912 | False |
| 15 | Patch_A_L14_colabdesign_chunk_seed0020_n005_raw_0004 | CYFYYRPDNDHHLC | Patch_A | 0.5537 | 28.231 | 39.33 | 51 | pass | pass | 0.4872 | False |

## 11. 当前限制

本轮结果需要在以下限制下解读：

```text
1. 每条候选只跑 1 个 seed
   不能评估构象稳定性和 seed-to-seed 一致性。

2. 使用 empty MSA / single-sequence mode
   运行速度较快，但可能降低复杂结构预测置信度。

3. 只做了 Boltz-2 raw 3GHG template 分支
   尚未进行 ColabFold / AlphaFold-Multimer 交叉验证。

4. 尚未做负筛选
   不能排除候选对 ALB、APOA1、TF、A2M、C3、IGG_FC 等高丰度蛋白的非特异性结合。

5. 尚未做人工结构复核
   parser 能做几何和数值筛查，但不能完全替代人工检查结合姿态。

6. 没有实验验证
   任何计算预测都不能直接等同于真实结合。
```

## 12. 阶段性结论

本轮完成了一次成功的全量 Boltz-2 复合物预测流程：

```text
302 条 hard-filtered FGA Cys-Cys 环肽候选
302 个 Boltz-2 复合物预测任务
302 个任务成功完成
302 个结果成功解析
```

但结构评分结果显示：

```text
0 条候选通过 complex_score_pass
```

因此，本轮不能给出可合成 top10，也不能给出 final peptide。

本轮最重要的成果是：

```text
1. 建立并跑通了 Boltz-2 raw 3GHG template 复合物预测流程。
2. 发现当前候选在 interface PAE 和 peptide pLDDT 上整体偏弱。
3. 确认当前 parser 能够阻止低置信度候选进入最终推荐。
```

## 13. 下一步建议

建议下一步不要直接合成，而是进入复核和改进阶段。

### 13.1 短期建议

从 near-miss 候选中选 20-30 条，进行：

```text
多 seed Boltz 复跑
MSA server 模式复跑
人工检查预测 PDB
重点观察 interface PAE 是否下降
重点观察 peptide pLDDT 是否提高
重点观察 Cys-Cys geometry 是否稳定通过
```

优先复核对象可以包括：

```text
complex_score 排名前列
iPTM 较高
Cys-Cys geometry pass
patch_consistency pass
```

### 13.2 中期建议

如果多 seed / MSA 复跑后出现少量通过候选，再进行：

```text
负筛选
ColabFold / AlphaFold-Multimer 交叉验证
不同模型之间的 pose 一致性比较
```

### 13.3 长期建议

如果仍无候选通过，建议回到生成阶段改进候选来源：

```text
增加 ColabDesign 生成规模
调整 patch 选择
调整 peptide length 分布
引入更多长度 14-18 的候选
探索 Patch_C 或其他 FGA 暴露区域
考虑 RFdiffusionAA / ProteinMPNN 等替代设计分支
```

## 14. 关键输出文件

本轮关键文件：

```text
Boltz job table:
C:\SH\fga_cyclic_peptide_design\results\boltz_predictions_raw3ghg_template_all_seed1\boltz_jobs.csv

Boltz skipped candidates:
C:\SH\fga_cyclic_peptide_design\results\boltz_predictions_raw3ghg_template_all_seed1\boltz_job_skipped_candidates.csv

Boltz batch summary:
C:\SH\fga_cyclic_peptide_design\results\boltz_predictions_raw3ghg_template_all_seed1\logs\boltz_batch_summary.tsv

Boltz batch failures:
C:\SH\fga_cyclic_peptide_design\results\boltz_predictions_raw3ghg_template_all_seed1\logs\boltz_batch_failures.tsv

Seed-level parsed scores:
C:\SH\fga_cyclic_peptide_design\results\boltz_predictions_raw3ghg_template_all_seed1\FGA_boltz_seed_scores.csv

Peptide-level summary:
C:\SH\fga_cyclic_peptide_design\results\boltz_predictions_raw3ghg_template_all_seed1\FGA_boltz_complex_prediction_summary.csv
```

## 15. 本轮运行命令

Boltz job 生成：

```bash
python scripts/14_prepare_boltz_prediction_jobs.py \
  --seeds 1 \
  --output-root results/boltz_predictions_raw3ghg_template_all_seed1 \
  --msa-mode empty \
  --template-pdb data/structures/raw/3GHG.pdb
```

Boltz 全量预测：

```bash
cd /mnt/c/SH/fga_cyclic_peptide_design
source ~/fga_model_envs/boltz2/bin/activate

export PROJECT_DIR="/mnt/c/SH/fga_cyclic_peptide_design"
export JOBS_CSV="results/boltz_predictions_raw3ghg_template_all_seed1/boltz_jobs.csv"
export GPU_LIST=0,1
export MAX_JOBS=0
export MAX_RETRIES=1
export OUTPUT_FORMAT=pdb
export BOLTZ_USE_MSA_SERVER=false
export BOLTZ_USE_POTENTIALS=true
export BOLTZ_OVERRIDE=false

bash scripts/external/run_boltz_batch.sh
```

结果解析：

```bash
python scripts/15_parse_boltz_predictions.py \
  --jobs-csv results/boltz_predictions_raw3ghg_template_all_seed1/boltz_jobs.csv \
  --output-root results/boltz_predictions_raw3ghg_template_all_seed1
```

## 16. 参考说明

AlphaFold / 类 AlphaFold 模型常用 pLDDT 和 PAE 作为结构预测置信度指标。pLDDT 用于局部结构置信度，PAE 用于相对位置和结构单元之间的置信度。本项目参考这些通用解释，并结合 FGA-短肽复合物任务特点设置内部筛选阈值。

参考链接：

```text
AlphaFold pLDDT explanation:
https://www.ebi.ac.uk/training/online/courses/alphafold/inputs-and-outputs/evaluating-alphafolds-predicted-structures-using-confidence-scores/plddt-understanding-local-confidence/

AlphaFold PAE explanation:
https://www.ebi.ac.uk/training/online/courses/alphafold/inputs-and-outputs/evaluating-alphafolds-predicted-structures-using-confidence-scores/pae-a-measure-of-global-confidence-in-alphafold-predictions/

AlphaFold DB FAQ:
https://alphafold.ebi.ac.uk/faq
```

## 17. 报告用结论版本

如果需要在汇报中压缩成一段话，可以使用：

```text
本轮完成 302 条 FGA Cys-Cys 环肽候选的 Boltz-2 raw 3GHG template 复合物预测。全部 302 个任务成功运行并生成 PDB、confidence 和 PAE 输出，计算流程成功率为 100%。但按当前严格结构评分门槛，没有候选同时满足 interface PAE、peptide pLDDT、patch consistency、interface contact 和 Cys-Cys geometry 要求，因此本轮不产生可合成最终候选。结果提示当前候选虽然多数能与目标 patch 发生接触，但界面相对位置和短肽局部构象置信度不足。建议下一步从 near-miss 候选中选择 20-30 条进行多 seed、MSA server 和人工结构复核，再决定是否进入负筛选和最终排序。
```
