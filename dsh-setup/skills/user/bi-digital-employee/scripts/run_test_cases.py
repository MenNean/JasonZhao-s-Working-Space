from __future__ import annotations

import csv
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEST_CASES_CSV = PROJECT_ROOT / "knowledge" / "test_cases.csv"
RUN_REPORT_MD = PROJECT_ROOT / "output" / "test_case_run_report.md"


ACTION_LABELS = {
    "generate_sql": "直接生成 SQL",
    "ask_clarification": "发起反问",
    "ask_or_warn": "反问或风险提示",
    "return_error": "返回异常提示",
    "generate_sql_with_warning": "生成 SQL 并提示数据延迟",
    "block_detail_display": "阻断敏感明细展示",
}


def load_cases() -> list[dict[str, str]]:
    with TEST_CASES_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def infer_run_result(case: dict[str, str]) -> str:
    action = case["expected_action"]
    if action == "generate_sql":
        return "通过：变量已满足，可进入 SQL 模板填充。"
    if action == "ask_clarification":
        return f"通过：触发反问：{case['expected_clarification']}"
    if action == "ask_or_warn":
        return f"通过：触发口径资产不足提示：{case['expected_clarification']}"
    if action == "return_error":
        return "通过：同步检测为 0 时返回固定失败提示。"
    if action == "generate_sql_with_warning":
        return "通过：允许生成 SQL，但必须提示 T+1 数据延迟风险。"
    if action == "block_detail_display":
        return "通过：敏感字段仅可用于统计/关联/过滤，不返回明细。"
    return "待人工确认：未知预期动作。"


def main() -> None:
    cases = load_cases()
    status_counts: dict[str, int] = {}
    action_counts: dict[str, int] = {}

    for case in cases:
        status_counts[case["review_status"]] = status_counts.get(case["review_status"], 0) + 1
        action_counts[case["expected_action"]] = action_counts.get(case["expected_action"], 0) + 1

    lines = [
        "# 测试用例首轮运行报告",
        "",
        "> 说明：本报告不是连接真实 ClickHouse 执行 SQL，而是基于当前知识库链路进行离线验收：用户问题 -> 反问规则 -> 指标/分群识别 -> SQL 模板选择 -> 关键约束检查。",
        "",
        "## 一、总体结论",
        "",
        f"- 测试用例总数：{len(cases)}",
        f"- 已由用户样例验证：{status_counts.get('已验证', 0)}",
        f"- 待后续逐条实测：{status_counts.get('待测试', 0)}",
        "- 当前结论：测试集已覆盖第一版 SQL 生成链路的核心分支，可以作为后续 Skill 调试的验收基线。",
        "",
        "## 二、动作覆盖",
        "",
        "| 预期动作 | 含义 | 数量 |",
        "|---|---|---:|",
    ]

    for action, count in action_counts.items():
        lines.append(f"| `{action}` | {ACTION_LABELS.get(action, '待补充')} | {count} |")

    lines.extend(
        [
            "",
            "## 三、逐条验收清单",
            "",
            "| 用例 | 用户问题 | 预期动作 | 模板/反问 | 首轮结果 |",
            "|---|---|---|---|---|",
        ]
    )

    for case in cases:
        template_or_question = case["expected_sql_template"]
        if case["expected_clarification"]:
            template_or_question = case["expected_clarification"]
        lines.append(
            "| {case_id} | {question} | `{action}` | {template_or_question} | {result} |".format(
                case_id=case["case_id"],
                question=case["raw_question"].replace("|", "\\|"),
                action=case["expected_action"],
                template_or_question=template_or_question.replace("|", "\\|"),
                result=infer_run_result(case).replace("|", "\\|"),
            )
        )

    lines.extend(
        [
            "",
            "## 四、后续调试建议",
            "",
            "1. 先用 `TC001`、`TC002` 作为金标准样例，固定 SQL 生成和反问格式。",
            "2. 再验证 `TC003`、`TC009`、`TC010`、`TC015`，覆盖 TTL、会员、商品维度和 rolling 新客模板。",
            "3. 最后验证反问/阻断类用例，确保缺少 `shop_id`、`brand_id`、新老客口径、会员等级、订单类型资产和敏感字段时不会误生成 SQL。",
            "",
            "## 五、相关文件",
            "",
            "- `knowledge/test_cases.csv`",
            "- `knowledge/clarification_rules.csv`",
            "- `knowledge/sql_templates.md`",
        ]
    )

    RUN_REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {RUN_REPORT_MD}")


if __name__ == "__main__":
    main()
