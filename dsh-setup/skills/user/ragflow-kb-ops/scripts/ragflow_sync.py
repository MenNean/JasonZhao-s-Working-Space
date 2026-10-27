#!/usr/bin/env python3
"""RAGFlow 知识库运维助手（仅依赖标准库）。

鉴权与地址走环境变量，脚本不持有任何凭据：
    RAGFLOW_API_KEY    必填
    RAGFLOW_BASE_URL   必填，例如 https://your-ragflow.example.com

写操作（upload / parse / index / metadata）默认只打印计划，必须显式加 --apply 才执行。

常用：
    python ragflow_sync.py version
    python ragflow_sync.py datasets
    python ragflow_sync.py docs --dataset-id <id>
    python ragflow_sync.py upload --dataset-id <id> --path ./files --apply
    python ragflow_sync.py parse  --dataset-id <id> --wait --apply
    python ragflow_sync.py index  --dataset-id <id> --type graph --wait --apply
    python ragflow_sync.py agent-verify --agent-id <id>
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:  # pragma: no cover - 老版本解释器
    pass

TIMEOUT = 120
POLL_INTERVAL = 60


class Api:
    def __init__(self) -> None:
        key = os.environ.get("RAGFLOW_API_KEY", "").strip()
        base = os.environ.get("RAGFLOW_BASE_URL", "").strip().rstrip("/")
        if not key:
            sys.exit("缺少环境变量 RAGFLOW_API_KEY")
        if not base:
            sys.exit("缺少环境变量 RAGFLOW_BASE_URL（例如 https://your-ragflow.example.com）")
        self.base = base if base.endswith("/api/v1") else base + "/api/v1"
        self.key = key

    def _request(self, method: str, path: str, params: dict | None = None,
                 body: dict | None = None, files: list | None = None):
        url = self.base + path
        if params:
            clean = {k: v for k, v in params.items() if v not in (None, "")}
            if clean:
                url += "?" + urllib.parse.urlencode(clean)

        headers = {"Authorization": f"Bearer {self.key}"}
        data = None
        if files:
            boundary = "----ragflow" + uuid.uuid4().hex
            buf = []
            for field, filename, content in files:
                buf.append(f"--{boundary}\r\n".encode())
                buf.append(
                    f'Content-Disposition: form-data; name="{field}"; filename="{filename}"\r\n'.encode()
                )
                ctype = mimetypes.guess_type(filename)[0] or "application/octet-stream"
                buf.append(f"Content-Type: {ctype}\r\n\r\n".encode())
                buf.append(content)
                buf.append(b"\r\n")
            buf.append(f"--{boundary}--\r\n".encode())
            data = b"".join(buf)
            headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        elif body is not None:
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                raw = resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:400]
            raise SystemExit(f"HTTP {e.code} {method} {path}\n{detail}")
        except urllib.error.URLError as e:
            raise SystemExit(f"网络错误 {method} {path}: {e.reason}")

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            return {"raw": raw}
        if isinstance(payload, dict) and payload.get("code") not in (0, None):
            raise SystemExit(f"接口返回错误 {path}: {payload.get('message') or payload}")
        return payload

    def get(self, path, params=None):
        return self._request("GET", path, params=params)

    def post(self, path, body=None, files=None, params=None):
        return self._request("POST", path, params=params,
                             body=body if files is None else None, files=files)

    def put(self, path, body=None, params=None):
        return self._request("PUT", path, params=params, body=body)

    def delete(self, path, body=None):
        return self._request("DELETE", path, body=body)

    def patch(self, path, body=None):
        return self._request("PATCH", path, body=body)


def p(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def confirm(apply: bool, plan: str) -> bool:
    if apply:
        return True
    print(f"[DRY-RUN] {plan}")
    print("未加 --apply，未做任何改动。")
    return False


def list_all_docs(api, dataset_id: str) -> list[dict]:
    """文档列表接口的 page_size 上限是 100，这里自动翻页取全量。"""
    docs, page = [], 1
    while True:
        data = api.get(f"/datasets/{dataset_id}/documents",
                       {"page": page, "page_size": 100})["data"]
        batch = data.get("docs", [])
        docs.extend(batch)
        total = data.get("total", len(docs))
        if not batch or len(docs) >= total:
            return docs
        page += 1


def collect_files(path_arg: str, recursive: bool) -> list[Path]:
    root = Path(path_arg).expanduser()
    if root.is_file():
        return [root]
    if not root.is_dir():
        sys.exit(f"路径不存在：{root}")
    it = root.rglob("*") if recursive else root.glob("*")
    return sorted(f for f in it if f.is_file() and not f.name.startswith("~$"))


def cmd_version(api, a):
    p(api.get("/system/version"))


def cmd_datasets(api, a):
    data = api.get("/datasets", {"page": 1, "page_size": a.page_size})["data"]
    for d in data:
        print(f"{d['id']}  docs={d.get('document_count')}  chunks={d.get('chunk_count')}  {d.get('name')}")


def cmd_docs(api, a):
    docs = list_all_docs(api, a.dataset_id)
    shown = docs[:a.limit] if a.limit else docs
    print(f"total={len(docs)}  (showing {len(shown)})")
    for d in shown:
        run = d.get("run") or d.get("status") or ""
        print(f"{d['id']}  chunks={d.get('chunk_count')}  run={run}  progress={d.get('progress')}  {d['name']}")


def cmd_graph(api, a):
    g = api.get(f"/datasets/{a.dataset_id}/knowledge_graph").get("data", {}).get("graph", {})
    print(f"nodes={len(g.get('nodes', []))}  edges={len(g.get('edges', []))}")


def cmd_models(api, a):
    """列出实例里真正可用的模型。Agent 的 llm_id / embd_id / rerank_id 必须用这里的 id。"""
    data = api.get("/models")["data"]
    if not isinstance(data, list):
        p(data)
        return
    rows = []
    for m in data:
        types = m.get("model_type") or []
        if isinstance(types, str):
            types = [types]
        model_id = "@".join(x for x in (m.get("name"), m.get("instance_name"), m.get("provider_name")) if x)
        rows.append((",".join(types), model_id, m.get("model_name") or m.get("name")))
    if a.type:
        want = {t.strip() for t in a.type.split(",") if t.strip()}
        rows = [r for r in rows if want & set(r[0].split(","))]
    for types, model_id, _ in sorted(rows):
        print(f"[{types}] {model_id}")
    print(f"共 {len(rows)} 个。Agent 的 llm_id / embd_id / rerank_id 直接填上面这种 name@instance_name@provider_name。")


def cmd_dataset_create(api, a):
    body = {"name": a.name}
    if a.description:
        body["description"] = a.description
    if a.embedding_model:
        body["embedding_model"] = a.embedding_model
    if a.chunk_method:
        body["chunk_method"] = a.chunk_method
    if a.parser_config:
        body["parser_config"] = json.loads(
            Path(a.parser_config).expanduser().read_text(encoding="utf-8"))
    if not confirm(a.apply,
                   f"新建数据集「{a.name}」embedding={a.embedding_model or '实例默认'} "
                   f"chunk_method={a.chunk_method or 'naive'}"):
        return
    d = api.post("/datasets", body).get("data") or {}
    print(f"已创建：{d.get('id')}  {d.get('name')}")
    print("下一步：python ragflow_sync.py upload --dataset-id "
          f"{d.get('id')} --path <目录> --apply")


def cmd_memories(api, a):
    d = api.get("/memories", {"page": 1, "page_size": 100})["data"]
    rows = d.get("memory_list", []) if isinstance(d, dict) else d
    for m in rows:
        print(f"{m.get('id')}  {m.get('name')}  types={m.get('memory_type')}  "
              f"embd={m.get('embd_id')}  llm={m.get('llm_id')}")
    print(f"共 {len(rows)} 个记忆库")


def cmd_memory_create(api, a):
    types = [t.strip() for t in a.memory_type.split(",") if t.strip()]
    body = {"name": a.name, "memory_type": types,
            "embd_id": a.embd_id, "llm_id": a.llm_id}
    if a.description:
        body["description"] = a.description
    if not confirm(a.apply, f"新建记忆库「{a.name}」memory_type={types}"):
        return
    d = api.post("/memories", body).get("data") or {}
    print(f"已创建：{d.get('id')}  {d.get('name')}")
    print("接下来把它填到 Agent 的两处：检索工具 retrieval_from=memory 的 memory_ids，"
          "以及 Message 节点的 memory_ids。两处都配才会真正读写记忆。")


def cmd_index_status(api, a):
    for t in (a.types or ["raptor", "graph"]):
        d = api.get(f"/datasets/{a.dataset_id}/index", {"type": t}).get("data") or {}
        print(f"[{t}] progress={d.get('progress')} duration={d.get('process_duration')} begin={d.get('begin_at')}")
        msg = (d.get("progress_msg") or "").strip().splitlines()
        if msg:
            print(f"      last: {msg[-1]}")


def cmd_upload(api, a):
    files = collect_files(a.path, a.recursive)
    if not files:
        sys.exit("没有找到可上传的文件")
    existing = {d["name"] for d in list_all_docs(api, a.dataset_id)}
    todo = files if a.force else [f for f in files if f.name not in existing]
    skipped = len(files) - len(todo)
    print(f"待上传 {len(todo)}，按文件名跳过 {skipped}（已存在）")
    for f in todo[:20]:
        print(f"  + {f}")
    if len(todo) > 20:
        print(f"  ... 其余 {len(todo) - 20} 个")
    if not confirm(a.apply, f"上传 {len(todo)} 个文件到数据集 {a.dataset_id}"):
        return
    for i in range(0, len(todo), a.batch):
        batch = todo[i:i + a.batch]
        payload = [("file", f.name, f.read_bytes()) for f in batch]
        res = api.post(f"/datasets/{a.dataset_id}/documents", files=payload)
        for d in res.get("data", []):
            print(f"  ok {d.get('id')}  {d.get('name')}")


def cmd_parse(api, a):
    ids = a.doc_ids or []
    if not ids:
        ids = [d["id"] for d in list_all_docs(api, a.dataset_id)]
    if not ids:
        sys.exit("数据集内没有文档")
    if not confirm(a.apply, f"触发解析 {len(ids)} 个文档"):
        return
    api.post(f"/datasets/{a.dataset_id}/chunks", {"document_ids": ids})
    print(f"已触发解析 {len(ids)} 个文档")
    if a.wait:
        wait_parse(api, a.dataset_id, set(ids), a.max_minutes)


def wait_parse(api, dataset_id, ids, max_minutes):
    deadline = time.time() + max_minutes * 60
    last = None
    while time.time() < deadline:
        docs = list_all_docs(api, dataset_id)
        pend = [d for d in docs if d["id"] in ids and d.get("progress", 0) not in (1, -1)]
        done = sum(1 for d in docs if d["id"] in ids and d.get("progress") == 1)
        failed = [d["name"] for d in docs if d["id"] in ids and d.get("progress") == -1]
        state = f"done={done}/{len(ids)} pending={len(pend)}"
        if state != last:
            print(f"  {state}")
            last = state
        if failed:
            sys.exit("解析失败：" + ", ".join(failed[:10]))
        if not pend:
            print("  解析完成")
            return
        time.sleep(POLL_INTERVAL)
    sys.exit(f"等待超时（{max_minutes} 分钟）")


def cmd_index(api, a):
    if a.trigger:
        if not confirm(a.apply,
                       f"触发数据集级 {a.type} 索引（小时级长任务，会重建已有 {a.type} 产物）"):
            return
        api.post(f"/datasets/{a.dataset_id}/index", params={"type": a.type})
        print(f"已触发 [{a.type}] 索引")

    d = api.get(f"/datasets/{a.dataset_id}/index", {"type": a.type}).get("data") or {}
    tid = d.get("task_id")
    print(f"[{a.type}] progress={d.get('progress')} begin={d.get('begin_at')}"
          + (f" task={tid}" if tid else ""))
    if not a.wait:
        return
    deadline = time.time() + a.max_minutes * 60
    last = None
    while time.time() < deadline:
        d = api.get(f"/datasets/{a.dataset_id}/index", {"type": a.type}).get("data") or {}
        prog = d.get("progress")
        if prog != last:
            msg = (d.get("progress_msg") or "").strip().splitlines()
            print(f"  progress={prog}  {msg[-1] if msg else ''}")
            last = prog
        if prog == 1:
            print("  完成")
            return
        if prog == -1:
            sys.exit("索引任务失败，检查 progress_msg")
        time.sleep(POLL_INTERVAL)
    sys.exit(f"等待超时（{a.max_minutes} 分钟）")


def _parse_pairs(items):
    out = {}
    for it in items or []:
        if "=" not in it:
            sys.exit(f"格式应为 字段=值，收到：{it}")
        k, v = it.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def batch_update_metadata(api, dataset_id, doc_ids, updates, deletes=None):
    """按键更新文档元数据：只改指定键，其他元数据字段原样保留。

    对应 PATCH /datasets/{id}/documents/metadatas。该接口把 updates 与 deletes 分开，
    所以确定是"按键合并"而不是整体覆盖 meta_fields。
    """
    if not doc_ids:
        return {"matched_docs": 0, "updated": 0}
    body = {
        "selector": {"document_ids": list(doc_ids)},
        "updates": [{"key": k, "value": v} for k, v in updates.items()],
        "deletes": [{"key": k} for k in (deletes or [])],
    }
    return api.patch(f"/datasets/{dataset_id}/documents/metadatas", body).get("data") or {}


def backup_docs_metadata(docs_by_id, ids, backup_dir, tag):
    out = Path(backup_dir).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    f = out / f"metadata_{tag}_{time.strftime('%Y%m%d_%H%M%S')}.json"
    payload = [{"id": i,
                "name": docs_by_id[i]["name"],
                "meta_fields": docs_by_id[i].get("meta_fields") or {}}
               for i in ids if i in docs_by_id]
    f.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"改动前元数据已备份：{f}")


def cmd_metadata(api, a):
    if a.csv and (a.where or a.set_):
        sys.exit("--csv 与 --where/--set 只能二选一")
    if not a.csv and not (a.where and a.set_):
        sys.exit("要么给 --csv，要么同时给 --where 和 --set")

    docs = list_all_docs(api, a.dataset_id)
    by_id = {d["id"]: d for d in docs}

    if a.csv:
        import csv
        rows = list(csv.DictReader(Path(a.csv).expanduser().open(encoding="utf-8-sig")))
        if not rows:
            sys.exit("CSV 没有数据行")
        if "doc_id" not in rows[0] and "name" not in rows[0]:
            sys.exit("CSV 需要 doc_id 或 name 列用于定位文档")
        keys = [k for k in rows[0].keys() if k not in ("doc_id", "name")]
        by_name = {d["name"]: d for d in docs}
        groups: dict = {}
        misses = []
        for row in rows:
            doc = by_id.get(row.get("doc_id") or "") or by_name.get(row.get("name") or "")
            if not doc:
                misses.append(row.get("name") or row.get("doc_id"))
                continue
            pairs = tuple((k, row[k]) for k in keys if row.get(k) not in (None, ""))
            if not pairs:
                continue
            groups.setdefault(pairs, []).append(doc["id"])

        total = sum(len(v) for v in groups.values())
        print(f"CSV {len(rows)} 行 -> 命中 {total} 篇，按取值合并成 {len(groups)} 组写入")
        for pairs, ids in groups.items():
            print(f"  {len(ids):>3} 篇 <- " + ", ".join(f"{k}={v}" for k, v in pairs))
        for m in misses:
            print(f"  skip 未找到：{m}")
        if not confirm(a.apply, f"按键写入 {total} 篇文档的元数据"):
            return
        ids_all = [i for v in groups.values() for i in v]
        backup_docs_metadata(by_id, ids_all, a.backup_dir, "csv")
        for pairs, ids in groups.items():
            print(f"  ok 请求 {len(ids)} -> {batch_update_metadata(api, a.dataset_id, ids, dict(pairs))}")
        return

    conds = _parse_pairs(a.where)
    sets = _parse_pairs(a.set_)

    def hit(d):
        mf = d.get("meta_fields") or {}
        for k, v in conds.items():
            want = "" if v in ("<空>", "<empty>", "<none>") else v
            if str(mf.get(k) or "") != want:
                return False
        return True

    target = [d for d in docs if hit(d)]
    print(f"筛选条件 " + ", ".join(f"{k}={v}" for k, v in conds.items()))
    print(f"命中 {len(target)} / {len(docs)} 篇：")
    for d in target[:30]:
        print("   " + d["name"])
    if len(target) > 30:
        print(f"   ... 其余 {len(target) - 30} 篇")
    if not target:
        return
    if not confirm(a.apply, f"按键写入 {len(sets)} 个字段到 {len(target)} 篇文档"):
        return
    backup_docs_metadata(by_id, [d["id"] for d in target], a.backup_dir, "where")
    print(f"  ok -> {batch_update_metadata(api, a.dataset_id, [d['id'] for d in target], sets)}")


def cmd_agent(api, a):
    d = api.get(f"/agents/{a.agent_id}")["data"]
    dsl = d.get("dsl", {})
    if getattr(a, "dump", None):
        out = Path(a.dump).expanduser()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"完整 DSL 已写到 {out}")
    nodes = dsl.get("graph", {}).get("nodes", [])
    print(f"title={d.get('title')}  nodes={len(nodes)}  components={len(dsl.get('components', {}))}")
    print(f"update={d.get('update_date')}  publish={d.get('last_publish_time')}")
    for n in nodes:
        print(f"  {n['id']}  type={n.get('type')}  label={n.get('data', {}).get('label')}")
    for n in nodes:
        if n.get("data", {}).get("label") == "Agent":
            form = n["data"].get("form", {})
            print(f"  [Agent {n['id']}] llm={form.get('llm_id')} max_rounds={form.get('max_rounds')} "
                  f"tools={len(form.get('tools') or [])}")
            for t in form.get("tools") or []:
                prm = t.get("params", {})
                src = prm.get("retrieval_from")
                print(f"      tool {t.get('component_name')} from={src} "
                      f"datasets={prm.get('dataset_ids')} memories={prm.get('memory_ids')}")


def cmd_agent_verify(api, a):
    d = api.get(f"/agents/{a.agent_id}")["data"]
    dsl = d.get("dsl", {})
    nodes = dsl.get("graph", {}).get("nodes", [])
    comps = dsl.get("components", {})
    issues: list[str] = []
    warns: list[str] = []

    comp_keys = set(comps.keys())
    node_keys = {n["id"] for n in nodes if n.get("data", {}).get("label") not in ("Note", "Tool", "Placeholder")}
    if comp_keys != node_keys:
        issues.append(f"graph 与 components 节点不一致：only_graph={node_keys - comp_keys} only_comp={comp_keys - node_keys}")

    agent_nodes = [n for n in nodes if n.get("data", {}).get("label") == "Agent"]
    if not agent_nodes:
        issues.append("画布里没有 Agent 节点")
    for n in agent_nodes:
        form = n["data"].get("form", {})
        cid = n["id"]
        if not form.get("llm_id"):
            issues.append(f"{cid}: llm_id 为空")
        comp_form = (comps.get(cid, {}).get("obj", {}) or {}).get("params")
        if comp_form is not None and comp_form != form:
            issues.append(f"{cid}: graph 与 components 参数不一致（界面一保存就会覆盖 components）")

        tools = form.get("tools") or []
        if len(tools) > 1 and int(form.get("max_rounds") or 0) < 2:
            issues.append(f"{cid}: 有 {len(tools)} 个工具但 max_rounds={form.get('max_rounds')}，工具串不起来")
        for t in tools:
            prm = t.get("params", {})
            src = prm.get("retrieval_from")
            if src == "dataset" and not (prm.get("dataset_ids") or prm.get("kb_ids")):
                issues.append(f"{cid}: 知识库检索未绑定任何 dataset")
            if src == "memory" and not prm.get("memory_ids"):
                issues.append(f"{cid}: 记忆检索未绑定任何记忆库")
            if src is None:
                warns.append(f"{cid}: 检索工具未显式设置 retrieval_from，来源判定会退化")

    msg_nodes = [n for n in nodes if n.get("data", {}).get("label") == "Message"]
    if not msg_nodes:
        warns.append("画布里没有 Message 节点，返回值可能为空")
    for n in msg_nodes:
        content = n["data"].get("form", {}).get("content") or []
        text = "".join(c for c in content if isinstance(c, str)).strip()
        if not text:
            issues.append(f"{n['id']}: Message 内容为空，Agent 输出会被丢弃（表现为答案为空、usage.calls=0）")
        else:
            for ref in {part for part in text.split("}") if part}:
                if "@" in ref and ref.lstrip("{").split("@")[0] not in node_keys:
                    warns.append(f"{n['id']}: 引用了不存在的节点 {ref.lstrip('{')}")

    read_mem = any(
        (t.get("params") or {}).get("retrieval_from") == "memory"
        for n in agent_nodes for t in (n["data"].get("form", {}).get("tools") or [])
    )
    write_mem = any((n["data"].get("form", {}).get("memory_ids") or []) for n in msg_nodes)
    if write_mem and not read_mem:
        warns.append("记忆只配了写入（Message）没有配读取（检索工具来源=记忆），存了但不会被召回")
    if read_mem and not write_mem:
        warns.append("记忆只配了读取没有配写入，没有内容可读")

    pub, upd = d.get("last_publish_time"), d.get("update_time")
    if pub and upd and pub < upd:
        gap = (upd - pub) / 1000
        note = f"最近保存晚于发布 {int(gap)} 秒，若刚改过参数请重新 Publish"
        # 界面自动保存会造成几十秒的小差值，只有明显更晚才判定为未发布
        (issues if gap > 600 else warns).append(note)

    for label, items in (("FAIL", issues), ("WARN", warns)):
        for i in items:
            print(f"[{label}] {i}")
    if not issues and not warns:
        print("[OK] 未发现结构性问题")
    return 1 if issues else 0


_MISSING = object()


def _deep_merge(dst: dict, src: dict) -> None:
    """原地深合并：dict 递归合并，其他类型（含 list）整体替换。"""
    for k, v in src.items():
        if isinstance(v, dict) and isinstance(dst.get(k), dict):
            _deep_merge(dst[k], v)
        else:
            dst[k] = v


def _leaf_paths(obj, prefix=""):
    if isinstance(obj, dict):
        if not obj:
            yield prefix, obj
        for k, v in obj.items():
            yield from _leaf_paths(v, f"{prefix}.{k}" if prefix else str(k))
    else:
        yield prefix, obj


def _get_path(obj, path):
    cur = obj
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return _MISSING
    return cur


def apply_patch_to_dsl(dsl: dict, patch: dict) -> list[str]:
    """把 patch 合并进 DSL，graph 与 components 两侧同时写（RAGFlow 的硬性要求）。"""
    changed: list[str] = []

    unknown = set(patch) - {"set_node_form", "replace_graph", "replace_components",
                            "globals", "messages"}
    if unknown:
        print(f"[WARN] patch 里这些键不认识，已忽略：{sorted(unknown)}")

    if "replace_graph" in patch:
        dsl["graph"] = patch["replace_graph"]
        changed.append("replace_graph")
    if "replace_components" in patch:
        dsl["components"] = patch["replace_components"]
        changed.append("replace_components")
    for key in ("globals", "messages"):
        if key in patch:
            dsl[key] = patch[key]
            changed.append(key)

    nodes = dsl.setdefault("graph", {}).setdefault("nodes", [])
    comps = dsl.setdefault("components", {})
    by_id = {n.get("id"): n for n in nodes}

    touched = patch.get("set_node_form") or {}
    for nid, fields in touched.items():
        node = by_id.get(nid)
        if node is None:
            raise SystemExit(f"patch 里的节点不存在于当前画布：{nid}")
        _deep_merge(node.setdefault("data", {}).setdefault("form", {}), fields)
        params = ((comps.get(nid) or {}).get("obj") or {}).get("params")
        if isinstance(params, dict):
            _deep_merge(params, fields)
        else:
            print(f"[WARN] {nid}: components 里没有 obj.params，只写了 graph 侧；"
                  "界面下一次保存会重建 components，请在界面上确认一次")
        changed.append(f"{nid} 的 form")

    # 一致性守卫：只对本次改过的节点提示
    for nid in touched:
        node = by_id.get(nid)
        params = ((comps.get(nid) or {}).get("obj") or {}).get("params")
        if isinstance(params, dict) and node and params != node.get("data", {}).get("form"):
            print(f"[WARN] {nid}: 合并后 graph.form 与 components.params 不完全一致，"
                  "建议跑 agent-verify 复核")
    return changed


def verify_patch(dsl_after: dict, patch: dict) -> list[str]:
    """读回校验：确认 patch 里的每个叶子值都真的落库了。"""
    missing: list[str] = []
    nodes = {n.get("id"): n for n in (dsl_after.get("graph") or {}).get("nodes", [])}
    comps = dsl_after.get("components") or {}

    for nid, fields in (patch.get("set_node_form") or {}).items():
        node = nodes.get(nid)
        if node is None:
            missing.append(f"{nid}: 读回后节点不存在")
            continue
        form = (node.get("data") or {}).get("form") or {}
        params = ((comps.get(nid) or {}).get("obj") or {}).get("params")
        for path, want in _leaf_paths(fields):
            got = _get_path(form, path)
            if got != want:
                missing.append(f"graph[{nid}].form.{path} 期望 {want!r} 实际 {got!r}")
            if isinstance(params, dict):
                got2 = _get_path(params, path)
                if got2 != want:
                    missing.append(f"components[{nid}].params.{path} 期望 {want!r} 实际 {got2!r}")

    for key in ("globals", "messages"):
        if key in patch and (dsl_after.get(key) != patch[key]):
            missing.append(f"{key} 未按 patch 落库")
    return missing


def _put_dsl(api, agent_id: str, dsl: dict, wrapped: bool = False) -> str:
    api.put(f"/agents/{agent_id}", {"dsl": dsl} if wrapped else dsl)
    return "wrapped" if wrapped else "flat"


def cmd_agent_apply(api, a):
    patch = json.loads(Path(a.patch).expanduser().read_text(encoding="utf-8"))
    if not isinstance(patch, dict):
        sys.exit("patch 文件必须是一个 JSON 对象")

    d = api.get(f"/agents/{a.agent_id}")["data"]
    dsl = d.get("dsl") or {}
    if not isinstance(dsl, dict) or not dsl.get("graph"):
        sys.exit("取回的 DSL 为空或不含 graph，先确认 agent_id 是否正确")

    backup_dir = Path(a.backup_dir).expanduser()
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup = backup_dir / f"agent_{a.agent_id}_{time.strftime('%Y%m%d_%H%M%S')}.json"
    backup.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已备份改动前的完整 Agent：{backup}")

    changes = apply_patch_to_dsl(dsl, patch)
    if not changes:
        sys.exit("patch 里没有可识别字段。支持 set_node_form / replace_graph / "
                 "replace_components / globals / messages")
    print("本次改动：" + "；".join(changes))

    if not confirm(a.apply, f"把上述改动写回 Agent {a.agent_id}"):
        return

    shape = _put_dsl(api, a.agent_id, dsl)
    after = (api.get(f"/agents/{a.agent_id}")["data"] or {}).get("dsl") or {}
    missing = verify_patch(after, patch)
    if missing and shape == "flat":
        print("flat 形状读回校验没过，改用 {\"dsl\": ...} 重试一次")
        shape = _put_dsl(api, a.agent_id, dsl, wrapped=True)
        after = (api.get(f"/agents/{a.agent_id}")["data"] or {}).get("dsl") or {}
        missing = verify_patch(after, patch)

    print(f"写回形状：{shape}")
    if missing:
        print("[FAIL] 以下改动没有落库：")
        for m in missing:
            print(f"  {m}")
        print(f"改动前的完整 Agent 已备份在 {backup}，可用 agent-apply --patch 反向恢复。")
        return 1
    print("[OK] 改动已落库，且读回校验通过")
    print("提醒：Publish 是界面动作，改完还要在界面上发布一次才对外生效。")
    return 0


def build_parser():
    ap = argparse.ArgumentParser(description="RAGFlow 知识库运维助手")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("version", help="实例版本").set_defaults(func=cmd_version)

    sp = sub.add_parser("models", help="可用模型清单（llm_id / embd_id / rerank_id 的取值来源）")
    sp.add_argument("--type", help="只看某类，如 chat / embedding / rerank / rerank,chat")
    sp.set_defaults(func=cmd_models)

    sp = sub.add_parser("datasets", help="数据集清单")
    sp.add_argument("--page-size", type=int, default=100)
    sp.set_defaults(func=cmd_datasets)

    sp = sub.add_parser("dataset-create", help="新建数据集")
    sp.add_argument("--name", required=True)
    sp.add_argument("--description")
    sp.add_argument("--embedding-model", help="留空用实例默认 embedding")
    sp.add_argument("--chunk-method",
                    help="naive（默认）/ book / laws / manual / one / paper / picture / "
                         "presentation / qa / table / tag / email / knowledge_graph")
    sp.add_argument("--parser-config", help="parser_config 的 JSON 文件（高级）")
    sp.add_argument("--apply", action="store_true")
    sp.set_defaults(func=cmd_dataset_create)

    sp = sub.add_parser("memories", help="记忆库清单")
    sp.set_defaults(func=cmd_memories)

    sp = sub.add_parser("memory-create", help="新建记忆库（Agent 读写记忆的前提）")
    sp.add_argument("--name", required=True)
    sp.add_argument("--memory-type", default="raw,semantic",
                    help="raw 只存原文；raw,semantic 额外抽取语义（推荐）")
    sp.add_argument("--embd-id", required=True, help="取值来源：models --type embedding")
    sp.add_argument("--llm-id", required=True, help="取值来源：models --type chat")
    sp.add_argument("--description")
    sp.add_argument("--apply", action="store_true")
    sp.set_defaults(func=cmd_memory_create)

    sp = sub.add_parser("docs", help="文档清单")
    sp.add_argument("--dataset-id", required=True)
    sp.add_argument("--limit", type=int, default=30, help="打印条数，0 表示全部")
    sp.set_defaults(func=cmd_docs)

    sp = sub.add_parser("graph", help="知识图谱节点/边数量")
    sp.add_argument("--dataset-id", required=True)
    sp.set_defaults(func=cmd_graph)

    sp = sub.add_parser("index-status", help="数据集级索引状态")
    sp.add_argument("--dataset-id", required=True)
    sp.add_argument("--type", dest="types", action="append", choices=["raptor", "graph"])
    sp.set_defaults(func=cmd_index_status)

    sp = sub.add_parser("upload", help="上传文件（按文件名幂等跳过）")
    sp.add_argument("--dataset-id", required=True)
    sp.add_argument("--path", required=True, help="文件或目录")
    sp.add_argument("--recursive", action="store_true")
    sp.add_argument("--force", action="store_true", help="不跳过同名文件")
    sp.add_argument("--batch", type=int, default=5)
    sp.add_argument("--apply", action="store_true")
    sp.set_defaults(func=cmd_upload)

    sp = sub.add_parser("parse", help="触发解析")
    sp.add_argument("--dataset-id", required=True)
    sp.add_argument("--doc-ids", nargs="*")
    sp.add_argument("--wait", action="store_true")
    sp.add_argument("--max-minutes", type=int, default=180)
    sp.add_argument("--apply", action="store_true")
    sp.set_defaults(func=cmd_parse)

    sp = sub.add_parser("index", help="数据集级索引（RAPTOR / GraphRAG）")
    sp.add_argument("--dataset-id", required=True)
    sp.add_argument("--type", required=True, choices=["raptor", "graph"])
    sp.add_argument("--trigger", action="store_true", help="真正发起索引（不带则只查状态）")
    sp.add_argument("--wait", action="store_true")
    sp.add_argument("--max-minutes", type=int, default=240)
    sp.add_argument("--apply", action="store_true")
    sp.set_defaults(func=cmd_index)

    sp = sub.add_parser("metadata",
                        help="批量写文档元数据（按键更新，不影响其他字段；改动前自动备份）")
    sp.add_argument("--dataset-id", required=True)
    sp.add_argument("--csv", help="含 doc_id 或 name 列 + 元数据列；相同取值自动合并成一组")
    sp.add_argument("--where", action="append",
                    help="筛选条件 字段=值，可给多次（AND）；用 字段=<空> 表示该字段为空")
    sp.add_argument("--set", dest="set_", action="append",
                    help="要写入的 字段=值，可给多次")
    sp.add_argument("--backup-dir", default="./ragflow_backups")
    sp.add_argument("--apply", action="store_true")
    sp.set_defaults(func=cmd_metadata)

    sp = sub.add_parser("agent", help="Agent 结构概览")
    sp.add_argument("--agent-id", required=True)
    sp.add_argument("--dump", help="把完整 Agent（含 DSL）写到该文件，用作备份或写 patch 的底稿")
    sp.set_defaults(func=cmd_agent)

    sp = sub.add_parser("agent-verify", help="按常见坑逐项体检 Agent 配置")
    sp.add_argument("--agent-id", required=True)
    sp.set_defaults(func=cmd_agent_verify)

    sp = sub.add_parser("agent-apply",
                        help="用 patch 文件改 Agent DSL（自动同时写 graph 与 components，并读回校验）")
    sp.add_argument("--agent-id", required=True)
    sp.add_argument("--patch", required=True, help="patch JSON 文件路径")
    sp.add_argument("--backup-dir", default="./ragflow_backups",
                    help="改动前的完整 Agent 备份目录")
    sp.add_argument("--apply", action="store_true")
    sp.set_defaults(func=cmd_agent_apply)

    return ap


def main():
    args = build_parser().parse_args()
    api = Api()
    rc = args.func(api, args)
    sys.exit(rc or 0)


if __name__ == "__main__":
    main()
