---
name: ragflow-kb-ops
description: Set up and operate a RAGFlow knowledge base end to end. Includes first-time onboarding on a fresh instance (connectivity check, listing the models the instance actually has, creating the dataset and the memory store), then normalize legacy local files, upload and parse them idempotently, apply document metadata, run dataset-level RAPTOR/GraphRAG indexing, and wire the dataset into an Agent canvas with knowledge-base retrieval, memory retrieval and memory saving. Use when the work involves a RAGFlow dataset, its chunking/index configuration, or a RAGFlow agent/canvas; not for generic RAG design outside RAGFlow.
metadata:
  short-description: RAGFlow 知识库入库、索引与智能体接线
---

# RAGFlow 知识库运维

把"一堆历史本地文件"变成"能被智能体稳定引用的知识库"，再把知识库接到 Agent 上。

## 从零上手（第一次接手）

按顺序过一遍，某一步不过就别往下走。

### 1. 先凑齐三样东西

- **实例地址**：形如 `https://your-ragflow.example.com`
- **API Key**：实例界面「个人设置 → API」里生成
- **可用的模型 provider**：至少要有对话模型和 embedding 模型（rerank 建议有）

### 2. 配好环境变量（凭据不进任何文件）

```bash
export RAGFLOW_BASE_URL="https://your-ragflow.example.com"
export RAGFLOW_API_KEY="<你的 key>"
```

Windows PowerShell 用 `$env:RAGFLOW_BASE_URL = "..."`。

### 3. 连通性自检

```bash
python scripts/ragflow_sync.py version    # 期望返回版本号，如 v0.26.4
python scripts/ragflow_sync.py datasets   # 期望能列出数据集
```

401/403 是 Key 不对；网络错误是地址或网络不通。这两条不过，后面全部免谈。

### 4. 把实例真实有的模型列出来（最容易翻车的一步）

```bash
python scripts/ragflow_sync.py models --type chat
python scripts/ragflow_sync.py models --type embedding
python scripts/ragflow_sync.py models --type rerank
```

输出形如 `qwen-max@my-qwen@Tongyi-Qianwen`，这个
`模型名@实例名@provider名` 才是 Agent 里 `llm_id` / `embd_id` / `rerank_id` 的合法取值。

**不要照抄别人截图或文档里的模型字符串。** 每个实例的 provider 别名和实例名都不一样；
填了一个本实例不存在的 id，表现为"配置看着全对，但助手完全不出话"——这是最难查的一类故障。

### 5. 建数据集

```bash
python scripts/ragflow_sync.py dataset-create --name "我的知识库" --apply
```

记下返回的 dataset id，后面每一步都要用。

### 6.（要用记忆才做）建记忆库

```bash
python scripts/ragflow_sync.py memory-create --name "我的助手记忆" \
  --embd-id "<models --type embedding 的输出>" \
  --llm-id  "<models --type chat 的输出>" --apply
```

### 7. 之后走下面的「标准工作流」

### 只在界面上能做的步骤（别在这上面白折腾）

| 步骤 | 说明 |
|---|---|
| Publish Agent | 写 DSL 只算"保存"，发布是界面动作，脚本不代做 |
| 看切片质量、调画布布局 | 需要人判断 |
| 新建 provider、填各家模型 Key | 实例管理动作 |

## 先认清两套模型（错误大多出在这里）

1. **知识侧**：数据集(dataset) → 文档(document) → 切片(chunk)。切片质量由解析配置决定；
   RAPTOR 与 GraphRAG 是**数据集级**索引，一次覆盖全库，不是逐文档跑。
2. **智能体侧**：Agent 画布的 DSL 有两个视图，**引擎只读 `components`，界面只认 `graph`**，
   前端每次保存会用 graph 重建 components。用 API 写入必须两边同时写，且画布节点 id 必须等于 components 的键。
   细节与最小骨架见 [references/agent-canvas-dsl.md](references/agent-canvas-dsl.md)。

## 标准工作流

1. **源数据规范化** — 见 [references/ingest-normalization.md](references/ingest-normalization.md)。
   pptx/xlsx 直接入库会丢结构，先转 PDF / Markdown；命名规范本身就是检索信号，先定后传。
2. **幂等入库** — 先列清单，按文件名跳过已存在的，再上传、触发解析、轮询到位。
3. **元数据** — 文档级字段（文档类型 / 品牌 / 产品线 / 是否可外发 / 生效与失效时间 / 是否有效）。
   走 `POST /api/v1/datasets/{id}/metadata/update`，**不需要重解析**。
4. **数据集级索引** — RAPTOR 与 GraphRAG 都是小时级任务，异步触发 + 轮询，不要阻塞等待。
5. **接线到 Agent** — 见 [references/agent-canvas-dsl.md](references/agent-canvas-dsl.md)。
   检索是 Agent 的内部工具而非画布节点；记忆必须"读 + 写"两处配合才生效。
6. **验收** — 先静态核对参数落库，再用 `completions` 实跑问答看引用。
   "配置已写入"不等于"运行时已生效"。

接口清单与实测状态见 [references/ragflow-api.md](references/ragflow-api.md)。

**批量改元数据只走按键更新接口**（`PATCH /datasets/{id}/documents/metadatas`，见
`metadata` 子命令）。**不要**用逐文档的 `PATCH /datasets/{id}/documents/{doc_id}` 带
`meta_fields`——那条路是**整体覆盖**语义。实测：只带 1 个键去 PATCH，同一文档上另外
4 个元数据字段直接被清掉。用批量接口则只改指定键，其他字段原样保留。

## 硬约束

- **API Key 只从环境变量读**（`RAGFLOW_API_KEY`），绝不写进任何文件、笔记、日志或回复。
  实例地址用 `RAGFLOW_BASE_URL`，不要在脚本或文档里硬编码某个实例地址。
- **改动前备份**：Agent DSL、实例配置、模型目录等，先写带时间戳的备份再动。
- **区分"已写入"与"已生效"**：写完必须验证；Agent 还要 Publish 才对外生效。
- **幂等优先**：批量入库或索引前先查现状，已存在的不重复上传、不重复解析。
- **长任务不阻塞**：小时级任务用轮询加阶段性汇报。
- **记录只追加**：更新历史进度记录时只追加新章节，不改既有内容。

## 脚本

`scripts/ragflow_sync.py`（仅标准库，无需 pip 安装）。**读操作直接跑；写操作必须先不带
`--apply` 干跑一遍，确认计划无误再加 `--apply`。**

```bash
# 摸底
python scripts/ragflow_sync.py version
python scripts/ragflow_sync.py models   --type chat
python scripts/ragflow_sync.py datasets
python scripts/ragflow_sync.py docs     --dataset-id <id> [--limit 0]
python scripts/ragflow_sync.py graph    --dataset-id <id>
python scripts/ragflow_sync.py memories

# 建（写）
python scripts/ragflow_sync.py dataset-create --name <名字> --apply
python scripts/ragflow_sync.py memory-create  --name <名字> \
        --embd-id <id> --llm-id <id> --apply

# 入库（写；upload 按文件名幂等跳过已存在的）
python scripts/ragflow_sync.py upload --dataset-id <id> --path ./files [--recursive] --apply
python scripts/ragflow_sync.py parse  --dataset-id <id> [--wait] --apply

# 元数据：两种模式二选一，都是"按键更新"，不碰其他字段
python scripts/ragflow_sync.py metadata --dataset-id <id> \
        --where "文档类型=报价" --set "是否可外发=仅内部" --apply
python scripts/ragflow_sync.py metadata --dataset-id <id> --csv ./meta.csv --apply

# 数据集级索引：不带 --trigger 只查状态，加了才真正发起
python scripts/ragflow_sync.py index --dataset-id <id> --type graph  --trigger --wait --apply
python scripts/ragflow_sync.py index --dataset-id <id> --type raptor --trigger --wait --apply

# Agent
python scripts/ragflow_sync.py agent        --agent-id <id>            # 概览
python scripts/ragflow_sync.py agent        --agent-id <id> --dump a.json  # 导出完整 DSL
python scripts/ragflow_sync.py agent-verify --agent-id <id>            # 按常见坑体检
python scripts/ragflow_sync.py agent-apply  --agent-id <id> --patch p.json --apply
```

`agent-apply` 是改 Agent 参数的**正规入口**：它会自动把同一个改动同时写进 `graph` 和
`components`（RAGFlow 的硬性要求），备份改动前的完整 Agent，写回后再读回逐字段校验。
patch 文件格式见 [assets/agent-patch.example.json](assets/agent-patch.example.json)
与 [references/agent-canvas-dsl.md](references/agent-canvas-dsl.md)。

Agent 参数改完**仍要在界面上 Publish** 才对外生效。

## 交付前自检

- 命名一致、无版本冲突；同类文件的命名规则统一
- 幂等：同一批文件重复执行不会产生重复文档
- 索引：RAPTOR / GraphRAG 的 `progress` 到 1，知识图谱节点与边不为 0
- Agent：Message 内容非空、检索来源正确、记忆读写两处都配、已 Publish
- 回归：至少 2~3 个真实业务问题有引用、无明显退化
