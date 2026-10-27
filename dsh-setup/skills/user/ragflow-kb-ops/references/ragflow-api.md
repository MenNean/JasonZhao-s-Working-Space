# RAGFlow HTTP API 速查

基准路径 `/api/v1`，鉴权头 `Authorization: Bearer $RAGFLOW_API_KEY`。
除特别标注外，响应统一为 `{"code":0,"data":...,"message":"success"}`。

下表"实测"列：✅ = 在 v0.26.4 实例上实际调通过；📖 = 取自官方 Python SDK 源码（路径权威，但未在本机逐一实跑）。

## 通用

| 方法 | 路径 | 用途 | 实测 |
|---|---|---|---|
| GET | `/system/version` | 实例版本 | ✅ |
| GET | `/models` | 可用模型清单。返回列表，每条含 `name` / `instance_name` / `provider_name` / `model_type`（**`model_type` 是列表**，如 `["chat"]`）。Agent 的 `llm_id` / `embd_id` / `rerank_id` 取值来源 | ✅ |

Agent 里要填的模型 id 是 **`name@instance_name@provider_name`** 三段拼起来，例如
`qwen-max@my-qwen@Tongyi-Qianwen`。用 `models` 子命令直接打印这种形式。
| GET | `/datasets` | 数据集清单 | ✅ |

## 数据集

| 方法 | 路径 | 用途 | 实测 |
|---|---|---|---|
| POST | `/datasets` | 新建数据集。必填只有 `name`；`embedding_model`（不传用租户默认）、`chunk_method`（不传为 `naive`）、`description`、`parser_config`、`permission` 可选 | ✅ |
| POST | `/datasets/{id}/index?type=` | **真正发起**数据集级索引重建，`type` 取 `raptor` / `graph`（还有 `mindmap`） | 📖 路由已核于 v0.26.4 源码，未实跑 |
| PUT | `/datasets/{id}` | 更新数据集配置（切分策略、解析器等） | 📖 |
| DELETE | `/datasets` | 删除数据集 | 📖 |

## 文档与切片

| 方法 | 路径 | 用途 | 实测 |
|---|---|---|---|
| POST | `/datasets/{id}/documents` | 上传文档（multipart，字段名 `file`，可多文件） | 📖 |
| GET | `/datasets/{id}/documents` | 文档清单；参数 `page` / `page_size` / `keywords` / `id` / `name` / `orderby` / `desc`；返回含 `name`、`chunk_count`、`meta_fields`、解析进度 | ✅ |
| PATCH | `/datasets/{id}/documents/{doc_id}` | 更新单个文档（`meta_fields`、`chunk_method`、启用状态等）。**`meta_fields` 是整体覆盖**：实测只带 1 个键提交，该文档另外 4 个元数据字段被清空 | ✅（覆盖语义已实测） |
| PATCH | `/datasets/{id}/documents/metadatas` | **批量改元数据，按键更新**。body `{selector:{document_ids}, updates:[{key,value}], deletes:[{key}]}`；只动指定键，返回 `{updated, matched_docs}` | ✅ |
| DELETE | `/datasets/{id}/documents` | 删除文档，body `{"ids":[...]}` 或 `{"delete_all":true}` | 📖 |
| POST | `/datasets/{id}/chunks` | **触发解析**，body `{"document_ids":[...]}`（异步，立即返回） | 📖 |
| DELETE | `/datasets/{id}/chunks` | 取消解析 | 📖 |
| GET | `/datasets/{id}/documents/{doc_id}/chunks` | 查看切片（`questions` / `important_keywords` 等都在这里） | 📖 |
| POST / DELETE | `/datasets/{id}/documents/{doc_id}/chunks` | 手工增删切片 | 📖 |

解析是异步的：`POST /chunks` 之后要轮询 `GET /documents` 的进度字段，不要在当前请求里等。

## 元数据

| 方法 | 路径 | 用途 | 实测 |
|---|---|---|---|
| PATCH | `/datasets/{id}/documents/metadatas` | 批量写元数据，**按键更新**（只动指定键） | ✅ |
| POST | `/datasets/{id}/metadata/update` | 同上。两个路由 body 形状与行为完全一致，最终都落到 `DocMetadataService.batch_update_metadata` | ✅（本项目实操） |
| GET / PUT | `/datasets/{id}/metadata/config` | 自动元数据（LLM 抽取）配置 | 📖 |

两者的 body 都是：

```json
{
  "selector": {"document_ids": ["<doc_id>"], "metadata_condition": {}},
  "updates":  [{"key": "是否可外发", "value": "仅内部"}],
  "deletes":  [{"key": "<要删掉的字段>"}]
}
```

返回 `{"updated": n, "matched_docs": n}`。`selector.metadata_condition` 可以让服务端按已有
元数据圈选文档，不必把 id 全传过来。

批量补元数据是性价比最高的一步：不触发重解析、不改文档 id。

## 数据集级索引与知识图谱

| 方法 | 路径 | 用途 | 实测 |
|---|---|---|---|
| GET | `/datasets/{id}/index?type=raptor` | RAPTOR 索引任务状态（`progress` / `progress_msg` / `process_duration`） | ✅ |
| GET | `/datasets/{id}/index?type=graph` | GraphRAG 索引任务状态 | ✅ |
| GET | `/datasets/{id}/knowledge_graph` | 知识图谱本体，返回 `graph.nodes` / `graph.edges` | ✅ |

要点：

- 两者都是**数据集级**任务，一次覆盖全库，不是逐文档跑。
- 都是小时级长任务；触发后异步轮询，`progress` 到 `1` 为完成，`-1` 为失败。
- 完成后建议抽查：图谱节点/边不为 0；切片里的 `questions` / `important_keywords` 仍在。

## Agent

| 方法 | 路径 | 用途 | 实测 |
|---|---|---|---|
| GET | `/agents` | Agent 清单 | ✅ |
| GET | `/agents/{id}` | 取完整 DSL（含 `graph` / `components` / `last_publish_time`） | ✅ |
| PUT | `/agents/{id}` | 写回完整 DSL（**body 就是 DSL 对象本身**，不是 `{"dsl": ...}`），返回 `{"code":0,"data":true}` | ✅ |
| GET | `/agents/templates` | 官方模板清单（`data[].id` / `title` / `dsl`），可直接取模板 DSL 作起点 | ✅ |
| POST | `/agents/{id}/sessions` | 建会话（body 可为 `{}`），返回 `data.id` 作为 `session_id` | ✅ |
| POST | `/agents/{id}/completions` | 问答，body `{"question":"...","stream":false,"session_id":"..."}` | ✅ |
| GET / DELETE | `/agents/{id}/sessions` | 会话列表 / 删除 | 📖 |

`completions` 的返回里重点看两处：`data.data.content`（答案；为空说明 Message 节点没接上游输出）
和 `data.data.usage.calls`（模型调用次数；为 0 说明流程根本没跑到模型）。

写回 Agent 时注意：**`graph` 与 `components` 必须同时写、且保持一致**，因为引擎读
`components`、界面读 `graph`，前端每次保存会用 `graph` 重建 `components`。已实测在真实
Agent 上这两处对同一节点是逐字相等的（`components[id].obj.params == graph.nodes[].data.form`）。
手写容易漏，建议直接用 `agent-apply` 子命令，它会自动两边同写并读回校验。

## 记忆

| 方法 | 路径 | 用途 | 实测 |
|---|---|---|---|
| POST | `/memories` | 新建记忆库。**必填 `name` + `memory_type` + `embd_id` + `llm_id`**（少一个会报 `required argument are missing`） | ✅ |
| GET | `/memories` | 记忆库清单，返回 `{memory_list: [...], total_count}`，**不是裸列表** | ✅ |
| GET | `/memories/{id}` | 记忆库详情，含 `messages.message_list`（raw + semantic 记录及抽取状态） | ✅ |
| PUT | `/memories/{id}` | 更新记忆库配置 | 📖 |
| GET | `/memories/{id}/config` | 记忆库配置 | 📖 |
| DELETE | `/memories/{id}` | 删除记忆库 | 📖 |
| PUT | `/messages/{memory_id}:{message_id}` | 启用/禁用单条记忆（`{"status":false}`） | 📖 |
| DELETE | `/messages/{memory_id}:{message_id}` | 遗忘单条记忆 | 📖 |

注意记忆消息的 id 形如 `<memory_id>:<message_id>`，用冒号拼接。

## 其他

| 方法 | 路径 | 用途 | 实测 |
|---|---|---|---|
| GET | `/chats/{id}` | 聊天助手（非 Agent）配置 | ✅ |
| GET | `/mcp/servers` | 已注册的 MCP 服务清单 | ✅ |

## 不存在或易错的路径

以下路径在 v0.26.4 上返回 404，不要照抄旧资料：

```text
GET  /api/v1/llm/list          → 用 /api/v1/models
GET  /api/v1/llms
GET  /api/v1/memory            → 用 /api/v1/memories
GET  /api/v1/memories/{id}/messages   → 记忆消息在 GET /api/v1/memories/{id} 的 messages 里
GET  /api/v1/tenant/list
```

另外：Agent 的 **Publish** 在界面上是一个动作，写 DSL 之后必须发布才对外生效；
判断是否已发布，比较 `last_publish_time` 与 `update_date`——前者早于后者说明改动还没发布。

## 轮询建议

- 长任务（解析、RAPTOR、GraphRAG）：**分钟级**间隔轮询，同一进度数字不要重复汇报。
- 进度不推进超过约定时长（例如 40 分钟）或 `progress = -1`：主动报错并给建议，而不是继续空转。
- 状态字段看 `progress`（0~1）与 `progress_msg`（带时间戳的步骤日志）。
