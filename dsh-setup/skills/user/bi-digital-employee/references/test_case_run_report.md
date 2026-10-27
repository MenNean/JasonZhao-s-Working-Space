# 测试用例首轮运行报告

> 说明：本报告不是连接真实 ClickHouse 执行 SQL，而是基于当前知识库链路进行离线验收：用户问题 -> 反问规则 -> 指标/分群识别 -> SQL 模板选择 -> 关键约束检查。

## 一、总体结论

- 测试用例总数：15
- 已由用户样例验证：2
- 待后续逐条实测：13
- 当前结论：测试集已覆盖第一版 SQL 生成链路的核心分支，可以作为后续 Skill 调试的验收基线。

## 二、动作覆盖

| 预期动作 | 含义 | 数量 |
|---|---|---:|
| `generate_sql` | 直接生成 SQL | 5 |
| `ask_clarification` | 发起反问 | 6 |
| `ask_or_warn` | 反问或风险提示 | 1 |
| `return_error` | 返回异常提示 | 1 |
| `generate_sql_with_warning` | 生成 SQL 并提示数据延迟 | 1 |
| `block_detail_display` | 阻断敏感明细展示 | 1 |

## 三、逐条验收清单

| 用例 | 用户问题 | 预期动作 | 模板/反问 | 首轮结果 |
|---|---|---|---|---|
| TC001 | shop_id=001，下单时间在2026年YTD历史新客的笔单，订单状态取完成 | `generate_sql` | sql.order.historical_new_customer_metrics | 通过：变量已满足，可进入 SQL 模板填充。 |
| TC002 | shop_id=001，下单时间在2026年会员的购买频次，订单状态取有效 | `ask_clarification` | 该会员口径需要关联会员表，请确认 brand_id。 | 通过：触发反问：该会员口径需要关联会员表，请确认 brand_id。 |
| TC003 | shop_id=001，2026年YTD的GMV，默认口径 | `generate_sql` | sql.order.ttl_metrics | 通过：变量已满足，可进入 SQL 模板填充。 |
| TC004 | 2026年YTD历史新客GMV | `ask_clarification` | 请确认本次查询对应的 shop_id 或品牌/店铺范围。 | 通过：触发反问：请确认本次查询对应的 shop_id 或品牌/店铺范围。 |
| TC005 | shop_id=001，2026年新客购买人数 | `ask_clarification` | 请确认新客口径：历史新客、365新客、180新客，还是自定义 xx 天新客？ | 通过：触发反问：请确认新客口径：历史新客、365新客、180新客，还是自定义 xx 天新客？ |
| TC006 | shop_id=001，2026年老客客单价 | `ask_clarification` | 请确认老客口径：历史老客、365老客、180老客，还是自定义 xx 天老客？ | 通过：触发反问：请确认老客口径：历史老客、365老客、180老客，还是自定义 xx 天老客？ |
| TC007 | shop_id=001，2026年自定义天数新客GMV | `ask_clarification` | 请确认 rolling 天数，例如 30 天、90 天或其他天数。 | 通过：触发反问：请确认 rolling 天数，例如 30 天、90 天或其他天数。 |
| TC008 | shop_id=001，brand_id=B001，2026年x级会员人数 | `ask_clarification` | 请确认会员等级 x，范围为 1-5；0 表示非会员。 | 通过：触发反问：请确认会员等级 x，范围为 1-5；0 表示非会员。 |
| TC009 | shop_id=001，brand_id=B001，2026年新会员人数 | `generate_sql` | sql.member.metrics | 通过：变量已满足，可进入 SQL 模板填充。 |
| TC010 | shop_id=001，2026年按产品线看GMV，订单状态有效 | `generate_sql` | sql.sku.dimension_metrics | 通过：变量已满足，可进入 SQL 模板填充。 |
| TC011 | shop_id=001，2026年正常订单GMV | `ask_or_warn` | 请确认正常订单中的赠品 SKU、购物金 SKU 和 20 元以下订单过滤规则，或确认暂不套用订单类型额外过滤。 | 通过：触发口径资产不足提示：请确认正常订单中的赠品 SKU、购物金 SKU 和 20 元以下订单过滤规则，或确认暂不套用订单类型额外过滤。 |
| TC012 | shop_id=001，查询昨天GMV，但前一天数据检测为0 | `return_error` | sql.sync.yesterday_check | 通过：同步检测为 0 时返回固定失败提示。 |
| TC013 | shop_id=001，今天GMV是多少 | `generate_sql_with_warning` | sql.order.ttl_metrics | 通过：允许生成 SQL，但必须提示 T+1 数据延迟风险。 |
| TC014 | shop_id=001，给我2026年购买用户的cjyx_encrypt_pin明细 | `block_detail_display` | 不适用 | 通过：敏感字段仅可用于统计/关联/过滤，不返回明细。 |
| TC015 | shop_id=001，下单时间在2026年YTD 365新客购买频次，订单状态取有效 | `generate_sql` | sql.order.rolling_new_customer_metrics | 通过：变量已满足，可进入 SQL 模板填充。 |

## 四、后续调试建议

1. 先用 `TC001`、`TC002` 作为金标准样例，固定 SQL 生成和反问格式。
2. 再验证 `TC003`、`TC009`、`TC010`、`TC015`，覆盖 TTL、会员、商品维度和 rolling 新客模板。
3. 最后验证反问/阻断类用例，确保缺少 `shop_id`、`brand_id`、新老客口径、会员等级、订单类型资产和敏感字段时不会误生成 SQL。

## 五、相关文件

- `knowledge/test_cases.csv`
- `knowledge/clarification_rules.csv`
- `knowledge/sql_templates.md`
