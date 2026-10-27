# Agent 画布 DSL：结构、参数与已知坑

以下内容基于 RAGFlow v0.26.4 实测（源码 + 线上读写验证）。

## 1. 一份 DSL 有两个视图

```text
{
  "graph":      { "nodes": [...], "edges": [...] },   # React-Flow 布局面；界面读这里
  "components": { "<node-id>": { "obj": {...}, "upstream": [...], "downstream": [...] } },  # 执行拓扑；引擎读这里
  "globals":    { "sys.query": "", "sys.user_id": "", ... },
  "variables":  [], "path": [], "retrieval": [], "history": [], "messages": []
}
```

- **引擎只读 `components`**，完全忽略 `graph`。
- **前端每次保存会用 `graph` 重建 `components`**（源码 `web/src/pages/agent/utils/dsl-bridge.ts` 里有明确说明）。
- 推论：两边必须同时写、保持一致；否则界面一保存就会把 `components` 覆盖成 `graph` 的样子，
  而纯 API 写入时引擎读到的又是 `components`。**两边不一致时的"真值"取决于谁最后写入。**
- 画布节点 `id` 必须等于 `components` 的键。官方模板用 `Agent:<HumanId>` / `Message:<HumanId>` 这种带前缀的 id，
  引用变量时也用它（`{Agent:xxxx@content}`）。

## 2. 最小可用骨架（单 Agent + 知识库 + 记忆）

占位符用 `<>` 标出，实际写入时替换。位置坐标任意，只要不重叠。

```json
{
  "graph": {
    "nodes": [
      {
        "id": "begin", "type": "beginNode",
        "position": { "x": 50, "y": 200 },
        "sourcePosition": "left", "targetPosition": "right",
        "data": { "label": "Begin", "name": "begin",
          "form": { "mode": "conversational", "enablePrologue": true,
                    "prologue": "<开场白>", "inputs": {}, "outputs": {} } }
      },
      {
        "id": "Agent:kbBot", "type": "agentNode",
        "position": { "x": 350, "y": 200 },
        "sourcePosition": "right", "targetPosition": "left",
        "data": { "label": "Agent", "name": "Agent_0", "form": { "<见第 3 节>" : "" } }
      },
      {
        "id": "Message:reply", "type": "messageNode",
        "position": { "x": 650, "y": 200 },
        "sourcePosition": "right", "targetPosition": "left",
        "data": { "label": "Message", "name": "Message_0",
          "form": { "content": [ "{Agent:kbBot@content}" ],
                    "memory_ids": [ "<memory_id>" ] } }
      }
    ],
    "edges": [
      { "id": "e1", "source": "begin", "sourceHandle": "start",
        "target": "Agent:kbBot", "targetHandle": "end" },
      { "id": "e2", "source": "Agent:kbBot", "sourceHandle": "start",
        "target": "Message:reply", "targetHandle": "end" }
    ]
  },
  "components": {
    "begin": {
      "obj": { "component_name": "Begin",
        "params": { "mode": "conversational", "enablePrologue": true,
                    "prologue": "<开场白>", "inputs": {}, "outputs": {} } },
      "upstream": [], "downstream": [ "Agent:kbBot" ]
    },
    "Agent:kbBot": {
      "obj": { "component_name": "Agent", "params": { "<与 graph 中 form 完全相同>" : "" } },
      "upstream": [ "begin" ], "downstream": [ "Message:reply" ]
    },
    "Message:reply": {
      "obj": { "component_name": "Message",
        "params": { "content": [ "{Agent:kbBot@content}" ], "memory_ids": [ "<memory_id>" ] } },
      "upstream": [ "Agent:kbBot" ], "downstream": []
    }
  },
  "globals": { "sys.conversation_turns": 0, "sys.date": "", "sys.files": [],
               "sys.history": [], "sys.query": "", "sys.user_id": "" },
  "variables": [], "path": [], "retrieval": [], "history": [], "messages": []
}
```

## 3. Agent 节点参数

完整键（缺项会退回节点默认值，建议全写）：

```text
cite, delay_after_error, description, exception_default_value, exception_goto,
exception_method, frequencyPenaltyEnabled, frequency_penalty, llm_id,
maxTokensEnabled, max_retries, max_rounds, max_tokens, mcp,
message_history_window_size, outputs, presencePenaltyEnabled, presence_penalty,
prompts, showStructuredOutput, sys_prompt, temperature, temperatureEnabled,
tools, topPEnabled, top_p, user_prompt, visual_files_var
```

要点：

- `prompts` 是**数组** `[{"role":"user","content":"{sys.query}"}]`；界面上它被渲染成单个输入框（取 `prompts[0].content`）。
- `outputs` 至少要有 `{"content":{"type":"string","value":""}}`，供下游用 `{<节点id>@content}` 引用。
- `mcp` 是数组，元素形如 `{"mcp_id":"<已注册的 MCP 服务 id>","tools":{}}`；**只能引用实例里已注册的 MCP 服务**。
- `llm_id` 形如 `model@provider` 或 `model@embedding@provider`（多段后缀表示 provider 组合），
  取值必须来自 `GET /api/v1/models`。

### 检索工具（`Agent.form.tools[]`）

检索是 Agent 的**内部工具**，不是画布节点。每个元素的形状：

```json
{ "component_name": "Retrieval", "id": "Retrieval:<unique>", "name": "Retrieval_0",
  "params": { "retrieval_from": "dataset", "dataset_ids": ["<dataset_id>"] } }
```

`params` 可用键：

| 键 | 说明 |
|---|---|
| `retrieval_from` | `"dataset"` 或 `"memory"`，**二选一**，决定这个工具的数据来源 |
| `dataset_ids` | 知识库来源；旧版本字段 `kb_ids` 仍兼容，两个都写最稳 |
| `memory_ids` | 记忆来源 |
| `user_id` | 记忆来源时可留空；空值表示不按用户过滤 |
| `similarity_threshold` / `keywords_similarity_weight` / `top_n` / `top_k` | 召回参数 |
| `rerank_id` | 重排模型，留空则不重排 |
| `use_kg` / `toc_enhance` / `cross_languages` / `meta_data_filter` | 知识图谱、目录增强、跨语言、元数据过滤 |
| `empty_response` | 无命中时的返回 |
| `outputs` | 建议保留 `formalized_content`（string）与 `json`（Array\<Object\>） |

**一个检索工具只能选一个来源。** 同时要用知识库和记忆，就放**两个** Retrieval 工具，
分别把 `retrieval_from` 设为 `dataset` 和 `memory`（工具名会按序号区分，不会冲突）。

## 4. 记忆：必须读写两处配合

| 方向 | 位置 | 参数 |
|---|---|---|
| 读 | 检索工具内「检索来源 = 记忆」 | `retrieval_from: "memory"` + `memory_ids` |
| 写 | Message 节点的「保存到记忆」 | `memory_ids` |

只配写入不配读取，记忆只是被存起来、永远不会被召回；只配读取不配写入，则没有内容可读。

## 5. 已知坑（都实测过）

| # | 现象 | 原因与处理 |
|---|---|---|
| 1 | 助手完全不回话，接口返回 `content: ""` 且 `usage.calls = 0` | Message 节点的 `content` 为空数组或空串。必须引用 `{Agent:<节点id>@content}` |
| 2 | 两个检索工具只生效一个 | `max_rounds = 1` 限制了工具调用轮次；配多个工具时把它设到 5 左右 |
| 3 | 找不到温度 / Top P / 存在惩罚 / 频率惩罚 的设置入口 | 它们不在「高级设置」里，而在**「模型」那一行的弹层**里（含「创造性」预设）。预设会一次改五个值，只调单项就别用预设 |
| 4 | 界面上多出一个孤立的 `Tool:` 节点 | 那是工具的视觉占位，**不是**执行组件。引擎从 `Agent.form.tools` 取工具，不读 Tool 节点 |
| 5 | 改完配置外部调用没变化 | Agent 必须 Publish 才对外生效；`last_publish_time` 早于 `update_date` 说明改动还没发布 |
| 6 | 界面里参数看着对，接口行为却相反 | `graph` 与 `components` 漂移了。以实际写入方为准，改完后两边都要核对 |

## 6. 读写流程

```text
GET  /api/v1/agents/{id}            # 拿到完整 DSL，先备份
    ↓ 就地修改 graph.nodes[].data.form 与 components[].obj.params（两边同改）
PUT  /api/v1/agents/{id}            # body 就是完整 DSL 对象，返回 {"code":0,"data":true}
GET  /api/v1/agents/{id}            # 回读比对
    ↓ 界面 Publish（或对应发布接口）
POST /api/v1/agents/{id}/sessions   # 建会话
POST /api/v1/agents/{id}/completions# 实跑问答，检查 content 与 reference
```

注意：纯 API 写入不会触发前端的一致性重建，所以**两边同时写**这一步不能省。
后续如果在界面上改过并保存，界面版本会覆盖 `components`。

## 7. 用 patch 改参数（推荐做法）

手写整个 DSL 很容易漏掉 `components` 那一半。用 `scripts/ragflow_sync.py agent-apply` 改：

```bash
# 1) 先导出当前完整 DSL，当作写 patch 的底稿与回滚依据
python scripts/ragflow_sync.py agent --agent-id <id> --dump agent_before.json

# 2) 写一个只含"要改的部分"的 patch（示例见 assets/agent-patch.example.json）

# 3) 干跑，确认计划
python scripts/ragflow_sync.py agent-apply --agent-id <id> --patch my_patch.json

# 4) 确认无误再落库（自动备份 + 读回校验）
python scripts/ragflow_sync.py agent-apply --agent-id <id> --patch my_patch.json --apply

# 5) 体检，然后到界面上 Publish
python scripts/ragflow_sync.py agent-verify --agent-id <id>
```

### patch 文件支持哪些键

| 键 | 作用 |
|---|---|
| `set_node_form` | `{节点id: {要改的字段}}`，深合并进该节点 form，**并镜像写入 components 的 obj.params** |
| `replace_graph` | 整块替换 `graph`（高级） |
| `replace_components` | 整块替换 `components`（高级） |
| `globals` / `messages` | 整块替换对应字段 |

`set_node_form` 的合并语义：dict 递归合并、list（如 `tools`、`content`）整体替换。
所以"只调一个温度"就只写 `temperature`，"换一整套检索工具"就把 `tools` 数组整个重写。
顶层写了不认识的键会提示出来，不会静默忽略。

### 节点里到底有哪些字段名（实测）

**Agent 节点 form**——注意是 `message_history_window_size`，**不是** `history_window`：

`llm_id` / `sys_prompt` / `user_prompt` / `temperature` / `top_p` / `presence_penalty` /
`frequency_penalty` / `max_tokens` / `max_rounds` / `message_history_window_size` / `cite` /
`tools` / `outputs` / `mcp` / `prompts`，
外加 `temperatureEnabled` / `topPEnabled` / `presencePenaltyEnabled` /
`frequencyPenaltyEnabled` / `maxTokensEnabled` 这组"是否启用"开关。只改数值不改开关，
界面上可能仍显示为未启用。

**检索工具**（`tools[]` 的每一项）：`id` / `name` / `component_name`（固定 `Retrieval`）/ `params`。
`params` 常用键：`retrieval_from`（`dataset` 或 `memory`）/ `dataset_ids` / `kb_ids` /
`memory_ids` / `similarity_threshold` / `top_n` / `top_k` / `keywords_similarity_weight` /
`rerank_id` / `use_kg` / `toc_enhance` / `cross_languages` / `meta_data_filter`。

**Message 节点 form**：`content`（数组）/ `memory_ids` / `auto_play`。

**Begin 节点 form**：`mode`（`conversational`）/ `enablePrologue` / `prologue` / `inputs` / `outputs`。

**工具项的 `id`** 形如 `Retrieval:GentleOlivesDesign`（`类型:随机短语`），`name` 是显示名
（默认 `Retrieval_0`，记忆那条常被人改成「记忆」）。整体替换 `tools` 时建议沿用原有 `id`，
否则界面上可能出现重复或对不上的工具项——先用 `agent --dump` 看一眼原值最稳。

### agent-apply 的三道安全阀

- **默认干跑**：不加 `--apply` 只打印计划；同时把改动前的完整 Agent 备份到
  `--backup-dir`（默认 `./ragflow_backups`）。
- **逐字段读回校验**：写回后重新拉取，patch 里每个叶子值都要跟回读结果对上；
  对不上会逐条列出并以非 0 退出码结束。
- **节点 id 写错直接中止**，不会写出半个坏 DSL。
