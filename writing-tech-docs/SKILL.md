---
name: writing-tech-docs
description: Use when creating technical documentation (SRS, PRD, system design, outline design, detailed design) from raw materials like meeting notes, research data, requirement matrices, existing specifications, or tender documents. Also use when synthesizing multiple information sources into structured technical documents or when user says "写PRD", "写方案设计", "写需求规格书", "写概要设计", "写详细设计", "write technical spec", "write design doc".
---

# Writing Tech Docs

## Overview

Eight-phase systematic methodology for producing technical documents from raw source materials. Core principle: **no document content without verified information sources — every claim traceable to raw material. No visual diagram without a plaintext sketch confirmed first.**

## When to Use

- User provides raw materials (meeting notes, SQL files, requirement matrices, bid documents, research reports) and asks for a technical document
- User mentions specific document types: PRD, SRS, system design document, outline design, detailed design
- Task involves synthesizing 2+ heterogeneous information sources into one document
- User says "写文档", "出方案", "整理需求"

**When NOT to use:**
- Pure code implementation tasks
- Single-file edits or bug fixes
- Document translation or formatting-only tasks

---

## Eight-Phase Workflow

**REQUIRED: Execute phases sequentially. Do not skip phases.**

### Phase 1: Source Inventory

**Before any writing, catalog ALL available source materials.**

1. Ask user for all raw materials (or scan project directory if user says "use everything available")
2. List each source file with: path, type, date, relevance
3. Ask user: "Are there any other materials I should use?"
4. Present the source inventory to user for confirmation

```
Output: numbered source list with types and dates
```

### Phase 2: Template Selection

**REQUIRED: Never create document structure from scratch without checking for templates first.**

1. Scan project for existing templates (search for `.docx`, `.md` files named with "模板"/"template"/"规格"/"方案")
2. If templates found: present to user, ask which to use
3. If no templates: propose a standard structure based on document type, ask user to confirm
4. **DO NOT proceed to writing until template/structure is confirmed by user**

```
Standard structures (when no template provided):
- SRS/PRD: 概述→术语→功能需求→非功能需求→接口→约束→附录
- System Design: 概述→架构→模块设计→接口→数据设计→部署→风险
- Detailed Design: 模块概述→流程→接口→数据结构→异常处理→配置
```

### Phase 3: Information Extraction & Cross-Referencing

**Extract structured data from each source. Cross-reference to find conflicts, gaps, and redundancies.**

1. For each source, extract information into categories:
   - Requirements / functional specs
   - Constraints / thresholds / rules
   - Gaps / risks / unknowns
   - Dependencies / interfaces

2. Build a cross-reference matrix:

```
| Topic | Source A says | Source B says | Conflict? | Resolution |
```

3. Identify **gaps** — sections required by the template but missing from source materials
4. Flag gaps to user **before writing**

### Phase 4: Outline with Gap Markers

**Create a complete outline. Mark each section with information source and confidence level.**

1. Build outline matching the confirmed template structure
2. Annotate each section:

```
## 3. 功能需求
  ### 3.1 白名单管理          [来源: session.md L94, 需求矩阵 L19] ✅ 充分
  ### 3.2 外设管控             [来源: session.md L95, 需求矩阵 L20] ✅ 充分
  ### 3.3 性能要求             [来源: session.md L93]              ⚠️ 缺少具体测试方法
  ### 3.4 部署架构             [来源: 会议纪要 L10]                 ❌ 信息不足
```

3. Present annotated outline to user for review
4. **Wait for user confirmation before writing full content**

### Phase 5: Diagram Design

**Identify sections that need architecture, topology, deployment, or flow diagrams. Always confirm with plaintext sketches before using any diagram tool.**

**Step 1: Check available diagram tools.** Before proposing diagrams, scan what tools are available:
- `drawio` skill / `drawio-server_*` tools → can create .drawio files (architecture, topology, flowcharts, wireframes)
- `pencil_batch_*` tools → `.pen` design files (UI mockups, page layouts)
- `architecture-diagram` skill → standalone HTML/SVG dark-themed architecture diagrams
- Mermaid syntax → lightweight inline diagrams (flowcharts, sequence diagrams, ER diagrams, class diagrams)
- Raw SVG → always available as plaintext fallback (write SVG markup directly)
- Report findings to user: "当前可用的画图工具: drawio, mermaid, SVG"

**If no dedicated diagram tools (drawio, pencil, architecture-diagram) are available:** Mermaid and raw SVG are always available fallbacks. NEVER skip the diagram phase with the excuse "没有画图工具" — Mermaid can be embedded in any Markdown document, and SVG works standalone. Suggest: "没有 drawio，可以用 mermaid 画流程图/时序图，或用 SVG 画架构图。"

**Step 2: Identify diagram candidates.** Scan the confirmed outline for sections that typically need diagrams:

| 章节类型 | 推荐图表 | 推荐工具 |
|---------|---------|---------|
| 系统架构 | 架构图 (System Architecture) | drawio / architecture-diagram / SVG |
| 模块分解 | 组件图 (Component Diagram) | drawio / mermaid |
| 网络拓扑 | 拓扑图 (Network Topology) | drawio / SVG |
| 部署架构 | 部署图 (Deployment Diagram) | drawio / SVG |
| 数据流/控制流 | 数据流图 (Data Flow) | drawio / mermaid |
| 业务流程/状态机 | 流程图/状态图 (Flowchart/State) | mermaid / drawio |
| 接口关系 | 接口关系图 (Interface Diagram) | drawio / mermaid |
| 时序交互 | 时序图 (Sequence Diagram) | mermaid |

**Step 3: Ask user.** Present diagram candidates:

```
以下章节建议配图：
  - 3. 总体架构         → 建议：系统架构图
  - 4. 功能模块         → 建议：模块分解图
  - 10. 部署约束        → 建议：部署拓扑图
  - 5. 接口设计         → 建议：接口关系图

请确认哪些需要画图？使用什么工具？
（回复如 "全画，用drawio" 或 "3和10画，10用mermaid"）
```

**Step 4: Plaintext sketch FIRST — MANDATORY.** For EACH confirmed diagram, produce an ASCII/plaintext sketch for user review BEFORE generating:

```
【系统架构图 草图】
┌─────────────────────────────────────────┐
│              安全服务器                   │
│  ┌───────────────────────────────────┐  │
│  │    系统安全综合管理平台 (CSCI-009)   │  │
│  └───────────┬───────────────────────┘  │
└──────────────┼──────────────────────────┘
               │ 策略下发 / 日志上报
    ┌──────────┼──────────┐
    ▼          ▼          ▼
┌───────┐ ┌───────┐ ┌───────┐
│工作站A │ │工作站B │ │服务器C │
│CSCI007│ │CSCI007│ │CSCI007│
└───────┘ └───────┘ └───────┘
```

**Step 5: Wait for sketch confirmation.** Do not generate the final diagram until user confirms the sketch.

```
草图确认无误？(回复"确认"开始绘制) 或有修改意见？
```

**Step 6: Generate the diagram** using the confirmed tool, then embed or reference it in the document.

**If user says "不用画图" or "文本够用":** Skip this phase entirely. Diagrams are recommended but not mandatory.

### Phase 6: Section-by-Section Writing

**Write each section based on extracted information. Mark gaps explicitly — never fabricate.**

1. Write one section at a time
2. For each claim, verify: "Which source material supports this?"
3. Mark untraceable claims with: `[待确认]` or `[推断]`
4. Mark information gaps with: `[TODO: 需要XX信息]`
5. Preserve all thresholds, parameters, and identifiers exactly as in source materials

### Phase 7: Completeness Check

**Before declaring done, verify every requirement in source materials appears in the document.**

1. Build a requirements traceability matrix:

```
| 来源 | 需求ID/行号 | 需求描述 | 文档章节 | 覆盖状态 |
```

2. Check each template section is either filled or explicitly marked as N/A with reason
3. Verify all numeric values (thresholds, capacities, limits) match source materials exactly
4. Run the self-check: "If I were the developer reading this, what questions would I still have?"

### Phase 8: Output & Metadata

1. Write document to specified path
2. Add metadata header:
   - Document number
   - Version
   - Source materials list with paths
   - Information completeness assessment (% sections with sufficient source data)
3. Report to user:
   - Document path, word count, chapter count
   - List of `[TODO]` items requiring user input
   - Information completeness score
   - Sections with low confidence

---

## Quick Reference

| Phase | Deliverable | Must Wait For User? |
|-------|------------|:---:|
| 1. Source Inventory | Numbered source list | Yes |
| 2. Template Selection | Confirmed template | Yes |
| 3. Info Extraction | Cross-reference matrix + gap list | Yes (for gaps) |
| 4. Outline | Annotated outline with confidence markers | Yes |
| 5. Diagram Design | Plaintext sketches → confirmed diagrams | Yes (sketch confirmation) |
| 6. Writing | Completed sections with `[TODO]`/`[推断]` markers | No |
| 7. Completeness | Traceability matrix + value verification | No |
| 8. Output | Document + metadata report + TODO list | No |

## Common Mistakes

| Mistake | Why It Happens | Fix |
|---------|---------------|-----|
| "The structure is obvious, I'll just write it" | Agent overconfidence | Phase 2: ALWAYS check for templates first |
| Reading all sources then jumping to writing | No extraction discipline | Phase 3: Force explicit extraction before any prose |
| "I'll note the gaps as I go" | Wishful thinking | Phase 4: Gaps must be identified in outline BEFORE writing |
| "The user can review after I finish" | Efficiency illusion | Phase 4: Outline review catches structural errors early |
| Fabricating plausible details to fill gaps | "It makes the doc more complete" | `[TODO]` markers are REQUIRED — never invent data |
| Skipping traceability "because doc is short" | Underestimating downstream impact | Phase 7: Even short docs benefit from source-to-section mapping |
| Writing in one pass without section verification | Flow state bias | Phase 6: Verify each section against its source before moving on |
| "I'll just draw the diagram directly, the sketch is wasted time" | Overconfidence in visual layout | Phase 5: Sketch catches layout errors BEFORE tool investment |
| "This diagram is obvious, no need to confirm with user" | Assuming user agrees with visual interpretation | Phase 5 Step 5: User must confirm sketch before generation |
| "I don't have a diagram tool, so I'll skip this phase" | Giving up on tool discovery | Phase 5 Step 1: Mermaid and raw SVG are ALWAYS available — no excuse to skip |
| "The plaintext sketch is ugly, I'll just make the real diagram" | Vanity over correctness | Ugly sketch that's correct > beautiful diagram that's wrong |

## Scaling for Document Complexity

**Simple docs** (single module, 1-2 sources): Execute all 8 phases but keep outputs minimal. Phase 3 matrix can be a 3-row table. Phase 4 outline can be bullet points. Phase 5 diagram sketches can be brief. Never skip phases entirely.

**Complex docs** (multi-module, 5+ sources): Full execution. Consider splitting Phase 6 writing across multiple turns.

**Reusing prior phases** (same project, sequential docs): Phases 1-2 outputs can be reused from the prior session without redoing, but **verify** sources haven't changed. Phases 3-8 must be done fresh for each document.

## Red Flags — STOP and Go Back

- Starting to write before user confirms template
- Outline has sections with ❌ but you're writing content anyway
- Using "probably", "typically", "usually" for specific parameters
- Cannot point to which source file a claim comes from
- Skipping the cross-reference step "because sources are small"
- Adding features or parameters not in source materials
- "This is a simple doc, I can skip Phase 3-4"
- "I already know this project, I don't need Phase 1-2"
- "The user is in a hurry, I'll just write it and they can fix later"
- "The template is obvious for this type of document"
- Generating a diagram without doing a plaintext sketch first
- Drawing a diagram without confirming the tool choice with user
- Assuming a section "obviously needs" a diagram without asking user

**All of these mean: Stop writing. Go back to the appropriate phase.**

**Violating the letter of the workflow is violating the spirit of the workflow.**

## Information Confidence Levels

| Marker | Meaning | Action |
|--------|---------|--------|
| ✅ 充分 | Source materials provide complete information | Proceed |
| ⚠️ 部分 | Source materials mention but lack detail | Write what's available, flag gaps |
| ❌ 不足 | Required by template but absent from sources | Do NOT fabricate; mark `[TODO]` |
| ⚡ 矛盾 | Sources disagree | Flag both versions, ask user to resolve |
