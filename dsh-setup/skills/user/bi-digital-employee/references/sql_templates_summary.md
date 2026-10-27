# SQL 模板库生成摘要

- 模板数量：13
- 指标表达式数量：7
- 输出文件：`knowledge/sql_templates.md`

## 模板列表

| 模板 ID | 用途 |
|---|---|
| `sql.sync.yesterday_check` | 查询前一天稳定数据是否已同步；如果前一天数据量为 0，返回同步失败提示。 |
| `sql.order.ttl_metrics` | 计算 GMV、购买人数、订单数、件数、笔单价、客单价和购买频次。 |
| `sql.order.historical_new_customer_metrics` | 查询周期开始前无订单的人群，并计算指定指标。 |
| `sql.order.rolling_new_customer_metrics` | 查询周期开始前 rolling N 天无订单的人群，覆盖 365 新客、180 新客、xx 新客。 |
| `sql.order.old_customer_by_difference` | 按 TTL 减去对应新客得到老客口径，覆盖历史老客、365 老客、180 老客、xx 老客。 |
| `sql.member.metrics` | 查询会员、新会员、老会员、x 级会员人数。 |
| `sql.order.member_purchase_frequency` | 订单表关联会员表后计算会员购买频次。 |
| `sql.sku.dimension_metrics` | 订单表关联商品表后按商品或产品线维度计算订单指标。 |
| `sql.order.old_customer_repurchase` | 计算前置时间窗内发生过购买，且查询时间段内也发生购买的老客回购人数。 |
| `sql.order.new_customer_second_purchase` | 计算查询期新客中，查询期内订单数大于等于 2 的人数。 |
| `sql.order.repeat_purchase_cycle_avg` | 先按消费者计算个人平均复购周期，再计算人群平均复购周期。 |
| `sql.product.same_order_affinity_rank` | 查询同一订单中既购买目标商品，又购买其他商品的同单连带排行。 |
| `sql.product.cross_order_affinity_rank` | 查询同一消费者在查询期内既购买目标商品，又购买其他商品的跨单连带排行。 |
