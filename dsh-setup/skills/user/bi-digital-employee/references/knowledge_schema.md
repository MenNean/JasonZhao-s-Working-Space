# AI-BI 知识库结构说明

> 本知识库以真实数据为事实来源，以旧项目 `ai-bi-engineer-digital-employee` 的方案为建设框架。

## 一、核心原则

1. 真实问法优先：先记录客户经理、业务方或历史工单中的原始表达，再做标准化映射。
2. 指标口径可复核：每个指标都需要有定义、适用条件、字段来源和复核状态。
3. 反问规则可执行：缺少关键条件时，AI 应优先反问，而不是直接查询。
4. SQL 逻辑受控：第一阶段优先使用已校验 SQL 模板、白名单表和白名单字段。
5. 品牌边界清晰：区分品牌专属知识和通用可复用知识。
6. 数据库与数据字典分层：数据库知识回答“有哪些数据源、库表、权限和查询边界”，数据字典回答“字段是什么意思、属于什么维度或指标、如何参与查询”。

## 二、建议知识库文件

| 文件 | 作用 | 状态 |
|---|---|---|
| `project_background.md` | 记录项目背景、试点品牌、建设边界和角色分工 | 待生成 |
| `scenario_dictionary.md` | 记录业务场景字典和真实场景映射 | 待生成 |
| `database_knowledge.md` | 记录数据库、数据源、表、权限、连接边界和白名单范围 | 待生成 |
| `data_dictionary_knowledge.csv` | 记录字段、字段含义、字段类型、维度指标归属和查询用途 | 待生成 |
| `metric_dictionary.csv` | 记录指标、别名、口径、字段、SQL 绑定和复核状态 | 待生成 |
| `clarification_rules.csv` | 记录每类问题缺少条件时的反问规则 | 待生成 |
| `sql_templates.md` | 记录可复用 SQL 模板、参数和限制条件 | 待生成 |
| `answer_templates.md` | 记录 AI 回答结构和解释模板 | 待生成 |
| `test_cases.csv` | 记录调试问题、预期行为、实际结果和修订建议 | 待生成 |

## 三、数据库知识库字段建议

```text
source_id
source_name
database_name
schema_name
table_name
table_business_name
table_purpose
grain
refresh_frequency
available_for_ai
permission_scope
query_boundary
owner
review_status
notes
```

## 四、数据字典知识库字段建议

```text
field_id
source_id
database_name
schema_name
table_name
field_name
field_business_name
field_type
field_description
dimension_or_metric
business_domain
allowed_filter
allowed_group_by
example_values
related_metric
review_status
notes
```

## 五、指标库字段建议

```text
metric_id
metric_name
aliases
scenario
brand_scope
business_definition
required_dimensions
optional_dimensions
default_assumptions
data_table
data_fields
sql_template_id
review_status
review_owner
version
notes
```

## 六、反问规则字段建议

```text
rule_id
scenario
trigger_condition
missing_information
question_to_ask
priority
default_allowed
default_value
risk_if_skipped
review_status
```

## 七、测试问题字段建议

```text
case_id
raw_question
expected_scenario
expected_metric
expected_clarification
expected_sql_template
expected_answer_structure
actual_result
pass_fail
gap_type
fix_action
```
