---
name: relationship-architecture-diagram
description: Create or revise dense HTML relationship architecture diagrams when business modules need orthogonal connectors, scoped dashed boundaries, route highlighting, and browser-verified delivery. Do not use for quick Mermaid diagrams or presentation-only sketches.
metadata:
  type: codex-skill
  scope: cross-project
  source_project: project22
  source_path: project22/知识库架构汇报/知识库标准架构图_V3_20260908.html
  source_date: 2026-09-09
  evidence_type: user-approved reusable delivery method
  applicability: large multi-zone HTML business relationship diagrams
  updated: 2026-09-09
  tags:
    - Codex-Skill
    - 关系架构图
    - HTML
    - 正交连线
    - 可视化
---

# 关系架构图作图 Skill

## 目标

把复杂的业务模块、调用关系、执行工作流和数据回流放进一张可横向阅读的 HTML 大图中。图要先讲清角色边界和信息方向，再补充细节；即使关系很多，也不能出现斜线、穿卡、错误箭头或文字叠层。

## 适用场景

- 多个业务 Agent、知识库、数据源和回流结果需要在同一张图中说明。
- 业务模块较多，需要用分区、分组和正交线梳理来源、调用、执行和沉淀。
- 用户需要点击模块后高亮完整路径，并能打开详情说明。
- 最终交付是可浏览、可打印或可保存为 PDF 的 HTML 架构图。

小型单链路或临时草图优先使用 Mermaid；纯汇报页且不需要交互时，优先使用演示文稿或静态 SVG。

## 工作方式

1. 先读取现有文件、用户批注和参考图。附件只作为证据，业务内容和箭头方向以用户确认的表达为准。
2. 建立关系清单，至少记录节点 ID、所属分区、显示名称、来源、去向、关系类型和说明文案。未确认的业务关系不得自行补造。
3. 先排分区与卡片，再画线。为每组关系预留独立走线通道；空间不足时扩大列距或模块间距，不允许让线穿过卡片解决拥挤。
4. 关系线使用 SVG 动态生成，只使用水平线、垂直线和直角转折。相邻分区共享主干线，跨区回流使用外侧或底部总线。
5. 将背景关系网和单条高亮路径分层：默认显示低对比度总览，点击或悬停节点时突出相关路线和节点。
6. 重要 HTML 修改前建立独立备份。完成后同时进行结构检查和真实浏览器检查，并明确两类检查各自结论。

## 必须遵守

- 不得为了排版擅自删减业务内容、合并不同语义的节点或改变来源与去向。
- 连接线不得斜穿卡片、表格、标题或说明文字；箭头必须落到真实目标卡片边缘。
- 分区范围框使用浅色虚线和低透明底色，位于关系线与卡片后方；范围说明必须在框内且不遮挡内容。
- 卡片、分组框、关系线和说明标签使用稳定层级，避免叠层随交互或打印变化。
- 画布可以横向滚动，但正文不得因视口缩放而改变字号；窄屏应保留可读性和可浏览性。
- `window.print()` 只能标为“打印 / 另存为 PDF”。只有实际生成文件时，才可以标为“直接导出 PDF”。
- 不得把静态检查描述成视觉验收；未在浏览器中检查时要明确说明。

## 详细规则

- 新建或大幅调整布局前，读取 [作图规则](references/作图规则.md)。
- 交付或修复穿线、叠层、错位问题前，读取 [验收清单](references/验收清单.md)。
- 指标拆分型关系图还应参考 [[关系图线框 HTML 设计与交付法]]。

## 默认交付

- 一个可独立打开或通过本地服务预览的 HTML 文件。
- 修改前备份；备份放在源项目或知识引擎备份区，不放入纯 Markdown 知识库。
- 可访问的本地预览地址。
- 结构检查、桌面与窄屏视觉检查、交互检查和控制台检查结果。
- 对仍需业务确认的关系，保留明确标记，不自行补齐。
