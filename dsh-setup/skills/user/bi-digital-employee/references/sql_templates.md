# SQL 模板库

> 本模板库基于 `database_knowledge.md`、`metric_dictionary.csv`、`global_variables.md` 和 `clarification_rules.csv` 生成，用于把已确认口径转为可复用 SQL。

## 一、全局约束

- 数据库：ClickHouse，Schema/库名为 CK06。
- 查询必须带 `shop_id` 权限边界。
- 默认时间字段：`order_start_time`。
- 默认订单口径：有效订单。
- 金额单位：字段金额单位为 `1 / 10000 元`，输出金额类指标默认换算为元。
- 数据延迟：T+1，默认稳定查询到前一天及更早日期。
- 敏感字段 `cjyx_encrypt_pin`、`lz_pin`、`nick_name` 不允许明细展示。
- 会员相关 SQL 默认使用 `shop_id + cjyx_encrypt_pin` 关联会员表。
- 订单类型中的赠品 SKU、购物金 SKU、20 元以下订单过滤资产尚未补齐，模板中保留 `{extra_order_type_filter}`。

## 二、常用参数

| 参数 | 说明 | 示例 |
|---|---|---|
| `{shop_id}` | 权限/店铺过滤字段 | `001` |
| `{start_time}` | 查询开始时间 | `2026-01-01 00:00:00` |
| `{end_time}` | 查询结束时间，左闭右开 | `2026-06-09 00:00:00` |
| `{time_field}` | 时间字段 | `order_start_time` / `pay_confirm_time` |
| `{order_status_filter}` | 订单状态过滤，使用不带表别名的字段表达式，便于在 CTE 和主查询中复用 | `order_status_id NOT IN (...)` |
| `{extra_order_type_filter}` | 订单类型额外过滤 | 空字符串或 `AND ...` |

## 三、指标表达式映射

| 指标 | SQL 表达式 | 默认别名 |
|---|---|---|
| GMV / 购买金额 | `sum(ord.sku_amt_jd) / 10000` | `gmv_yuan` |
| Customer / 购买人数 | `countDistinct(ord.cjyx_encrypt_pin)` | `customers` |
| Transactions / 购买订单数 | `countDistinct(ord.order_id)` | `transactions` |
| Items / 购买商品件数 | `sum(ord.sku_cnt)` | `items` |
| ATV / 笔单价 | `(sum(ord.sku_amt_jd) / 10000) / nullIf(countDistinct(ord.order_id), 0)` | `atv_yuan` |
| Spending / 客单价 | `(sum(ord.sku_amt_jd) / 10000) / nullIf(countDistinct(ord.cjyx_encrypt_pin), 0)` | `spending_yuan` |
| frequency / 购买频次 | `countDistinct(ord.order_id) / nullIf(countDistinct(ord.cjyx_encrypt_pin), 0)` | `frequency` |

## 四、模板清单

### sql.sync.yesterday_check — 数据同步检测模板

- 用途：查询前一天稳定数据是否已同步；如果前一天数据量为 0，返回同步失败提示。
- 参数：`{shop_id}`, `{yesterday_start}`, `{today_start}`

```sql
SELECT
    count() AS row_count
FROM dwm.order_detail_d
WHERE shop_id = '{shop_id}'
  AND order_start_time >= toDateTime('{yesterday_start}')
  AND order_start_time < toDateTime('{today_start}');
```

注意事项：
- 如果 row_count = 0，返回：数据同步失败，请咨询中台数仓负责人。
- 数据为 T+1，默认稳定查询到前一天及更早日期。

### sql.order.ttl_metrics — 订单表 TTL 指标模板

- 用途：计算 GMV、购买人数、订单数、件数、笔单价、客单价和购买频次。
- 参数：`{shop_id}`, `{start_time}`, `{end_time}`, `{time_field}`, `{order_status_filter}`, `{extra_order_type_filter}`

```sql
WITH
    toDateTime('{start_time}') AS start_time,
    toDateTime('{end_time}') AS end_time
SELECT
    sum(ord.sku_amt_jd) / 10000 AS gmv_yuan,
    countDistinct(ord.cjyx_encrypt_pin) AS customers,
    countDistinct(ord.order_id) AS transactions,
    sum(ord.sku_cnt) AS items,
    (sum(ord.sku_amt_jd) / 10000) / nullIf(countDistinct(ord.order_id), 0) AS atv_yuan,
    (sum(ord.sku_amt_jd) / 10000) / nullIf(countDistinct(ord.cjyx_encrypt_pin), 0) AS spending_yuan,
    countDistinct(ord.order_id) / nullIf(countDistinct(ord.cjyx_encrypt_pin), 0) AS frequency
FROM dwm.order_detail_d AS ord
WHERE ord.shop_id = '{shop_id}'
  AND ord.{time_field} >= start_time
  AND ord.{time_field} < end_time
  AND {order_status_filter}
  {extra_order_type_filter};
```

注意事项：
- 默认 time_field=order_start_time。
- 默认 order_status_filter 为有效订单；用户指定完成订单时改为完成订单条件。
- extra_order_type_filter 在订单类型资产未补齐前可为空。

### sql.order.historical_new_customer_metrics — 历史新客指标模板

- 用途：查询周期开始前无订单的人群，并计算指定指标。
- 参数：`{shop_id}`, `{start_time}`, `{end_time}`, `{time_field}`, `{order_status_filter}`, `{metric_expression}`, `{metric_alias}`

```sql
WITH
    toDateTime('{start_time}') AS start_time,
    toDateTime('{end_time}') AS end_time,
    historical_new_customers AS (
        SELECT
            cjyx_encrypt_pin
        FROM dwm.order_detail_d
        WHERE shop_id = '{shop_id}'
          AND {order_status_filter}
        GROUP BY cjyx_encrypt_pin
        HAVING min({time_field}) >= start_time
           AND min({time_field}) < end_time
    )
SELECT
    {metric_expression} AS {metric_alias}
FROM dwm.order_detail_d AS ord
INNER JOIN historical_new_customers AS hnc
    ON ord.cjyx_encrypt_pin = hnc.cjyx_encrypt_pin
WHERE ord.shop_id = '{shop_id}'
  AND ord.{time_field} >= start_time
  AND ord.{time_field} < end_time
  AND {order_status_filter};
```

注意事项：
- metric_expression 可替换为 GMV、Customer、Transactions、Items、ATV、Spending、frequency 对应表达式。
- 金额类表达式需要除以 10000 转为元。

### sql.order.rolling_new_customer_metrics — Rolling 新客指标模板

- 用途：查询周期开始前 rolling N 天无订单的人群，覆盖 365 新客、180 新客、xx 新客。
- 参数：`{shop_id}`, `{start_time}`, `{end_time}`, `{time_field}`, `{rolling_days}`, `{order_status_filter}`, `{metric_expression}`, `{metric_alias}`

```sql
WITH
    toDateTime('{start_time}') AS start_time,
    toDateTime('{end_time}') AS end_time,
    rolling_new_customers AS (
        SELECT
            cjyx_encrypt_pin
        FROM dwm.order_detail_d
        WHERE shop_id = '{shop_id}'
          AND {order_status_filter}
          AND {time_field} >= start_time - INTERVAL {rolling_days} DAY
          AND {time_field} < end_time
        GROUP BY cjyx_encrypt_pin
        HAVING countIf({time_field} < start_time) = 0
           AND countIf({time_field} >= start_time AND {time_field} < end_time) > 0
    )
SELECT
    {metric_expression} AS {metric_alias}
FROM dwm.order_detail_d AS ord
INNER JOIN rolling_new_customers AS rnc
    ON ord.cjyx_encrypt_pin = rnc.cjyx_encrypt_pin
WHERE ord.shop_id = '{shop_id}'
  AND ord.{time_field} >= start_time
  AND ord.{time_field} < end_time
  AND {order_status_filter};
```

注意事项：
- 365 新客 rolling_days=365；180 新客 rolling_days=180；xx 新客需要反问 rolling_days。
- 该模板要求查询周期内有订单，且查询周期开始前 rolling N 天无订单。

### sql.order.old_customer_by_difference — 老客差集指标模板

- 用途：按 TTL 减去对应新客得到老客口径，覆盖历史老客、365 老客、180 老客、xx 老客。
- 参数：`{shop_id}`, `{start_time}`, `{end_time}`, `{time_field}`, `{new_customer_cte}`, `{order_status_filter}`, `{metric_expression}`, `{metric_alias}`

```sql
WITH
    toDateTime('{start_time}') AS start_time,
    toDateTime('{end_time}') AS end_time,
    {new_customer_cte},
    old_customers AS (
        SELECT DISTINCT
            cjyx_encrypt_pin
        FROM dwm.order_detail_d
        WHERE shop_id = '{shop_id}'
          AND {time_field} >= start_time
          AND {time_field} < end_time
          AND {order_status_filter}
          AND cjyx_encrypt_pin NOT IN (SELECT cjyx_encrypt_pin FROM new_customers)
    )
SELECT
    {metric_expression} AS {metric_alias}
FROM dwm.order_detail_d AS ord
INNER JOIN old_customers AS oc
    ON ord.cjyx_encrypt_pin = oc.cjyx_encrypt_pin
WHERE ord.shop_id = '{shop_id}'
  AND ord.{time_field} >= start_time
  AND ord.{time_field} < end_time
  AND {order_status_filter};
```

注意事项：
- new_customer_cte 需要传入对应新客定义，并命名为 new_customers。
- 老客定义来自 TTL 差对应新客。

### sql.member.metrics — 会员指标模板

- 用途：查询会员、新会员、老会员、x 级会员人数。
- 参数：`{shop_id}`, `{start_time}`, `{end_time}`, `{member_condition}`

```sql
WITH
    toDateTime('{start_time}') AS start_time,
    toDateTime('{end_time}') AS end_time
SELECT
    countDistinct(mem.cjyx_encrypt_pin) AS member_count
FROM dwm.member_info_d AS mem
WHERE mem.shop_id = '{shop_id}'
  AND mem.cjyx_encrypt_pin IN (
      SELECT DISTINCT
          ord.cjyx_encrypt_pin
      FROM dwm.order_detail_d AS ord
      WHERE ord.shop_id = '{shop_id}'
  )
  AND {member_condition};
```

注意事项：
- 会员相关指标默认使用 `shop_id + cjyx_encrypt_pin` 识别会员身份。
- member_condition 示例：会员=1=1；新会员=open_card_time>=start_time AND open_card_time<end_time；老会员=open_card_time<start_time；x级会员=member_level={level}。

### sql.order.member_purchase_frequency — 会员购买频次模板

- 用途：订单表关联会员表后计算会员购买频次。
- 参数：`{shop_id}`, `{start_time}`, `{end_time}`, `{time_field}`, `{order_status_filter}`, `{member_condition}`

```sql
WITH
    toDateTime('{start_time}') AS start_time,
    toDateTime('{end_time}') AS end_time
SELECT
    countDistinct(ord.order_id) / nullIf(countDistinct(ord.cjyx_encrypt_pin), 0) AS purchase_frequency
FROM dwm.order_detail_d AS ord
INNER JOIN dwm.member_info_d AS mem
    ON ord.cjyx_encrypt_pin = mem.cjyx_encrypt_pin
   AND ord.shop_id = mem.shop_id
WHERE ord.shop_id = '{shop_id}'
  AND ord.{time_field} >= start_time
  AND ord.{time_field} < end_time
  AND {order_status_filter}
  AND {member_condition};
```

注意事项：
- 会员相关购买指标默认使用 `shop_id + cjyx_encrypt_pin` 关联会员表。
- 默认 member_condition 可为 1=1 表示会员表命中人群。

### sql.sku.dimension_metrics — 商品/产品线维度指标模板

- 用途：订单表关联商品表后按商品或产品线维度计算订单指标。
- 参数：`{shop_id}`, `{start_time}`, `{end_time}`, `{time_field}`, `{order_status_filter}`, `{dimension_field}`, `{metric_expression}`, `{metric_alias}`

```sql
WITH
    toDateTime('{start_time}') AS start_time,
    toDateTime('{end_time}') AS end_time
SELECT
    sku.{dimension_field} AS dimension_value,
    {metric_expression} AS {metric_alias}
FROM dwm.order_detail_d AS ord
INNER JOIN dim.sku_gather_info AS sku
    ON ord.sku_id = sku.sku_id
WHERE ord.shop_id = '{shop_id}'
  AND sku.shop_id = '{shop_id}'
  AND ord.{time_field} >= start_time
  AND ord.{time_field} < end_time
  AND {order_status_filter}
GROUP BY
    sku.{dimension_field}
ORDER BY
    {metric_alias} DESC;
```

注意事项：
- 商品表 sku_id 唯一，shop_id 主要用于权限/店铺范围过滤。
- dimension_field 示例：sku_name、productline、brand_level_category2、brand_level_category3。

### sql.order.old_customer_repurchase — XX 老客回购人数模板

- 用途：计算前置时间窗内发生过购买，且查询时间段内也发生购买的老客回购人数。
- 参数：`{shop_id}`, `{pre_start_time}`, `{pre_end_time}`, `{start_time}`, `{end_time}`, `{time_field}`, `{order_status_filter}`, `{extra_order_type_filter}`

```sql
WITH
    toDateTime('{pre_start_time}') AS pre_start_time,
    toDateTime('{pre_end_time}') AS pre_end_time,
    toDateTime('{start_time}') AS start_time,
    toDateTime('{end_time}') AS end_time,
    pre_buyers AS (
        SELECT DISTINCT
            cjyx_encrypt_pin
        FROM dwm.order_detail_d
        WHERE shop_id = '{shop_id}'
          AND {time_field} >= pre_start_time
          AND {time_field} < pre_end_time
          AND {order_status_filter}
          {extra_order_type_filter}
    ),
    period_buyers AS (
        SELECT DISTINCT
            cjyx_encrypt_pin
        FROM dwm.order_detail_d
        WHERE shop_id = '{shop_id}'
          AND {time_field} >= start_time
          AND {time_field} < end_time
          AND {order_status_filter}
          {extra_order_type_filter}
    )
SELECT
    countDistinct(pb.cjyx_encrypt_pin) AS old_customer_repurchase_customers
FROM period_buyers AS pb
INNER JOIN pre_buyers AS pre
    ON pb.cjyx_encrypt_pin = pre.cjyx_encrypt_pin;
```

注意事项：
- 该模板是双时间窗人群交集：前置购买人群 ∩ 查询期购买人群。
- 如果用户只说“XX 老客回购”但未说明前置时间窗，需要反问前置时间窗。
- 查询期仍必须使用全局变量中的 shop_id、时间字段、订单状态和订单类型过滤。

### sql.order.new_customer_second_purchase — 新客二回人数模板

- 用途：计算查询期新客中，查询期内订单数大于等于 2 的人数。
- 参数：`{shop_id}`, `{start_time}`, `{end_time}`, `{time_field}`, `{order_status_filter}`, `{new_customer_cte}`, `{extra_order_type_filter}`

```sql
WITH
    toDateTime('{start_time}') AS start_time,
    toDateTime('{end_time}') AS end_time,
    {new_customer_cte},
    period_order_cnt AS (
        SELECT
            cjyx_encrypt_pin,
            countDistinct(order_id) AS order_cnt
        FROM dwm.order_detail_d
        WHERE shop_id = '{shop_id}'
          AND {time_field} >= start_time
          AND {time_field} < end_time
          AND {order_status_filter}
          {extra_order_type_filter}
        GROUP BY
            cjyx_encrypt_pin
    )
SELECT
    countDistinct(nc.cjyx_encrypt_pin) AS new_customer_second_purchase_customers
FROM new_customers AS nc
INNER JOIN period_order_cnt AS poc
    ON nc.cjyx_encrypt_pin = poc.cjyx_encrypt_pin
WHERE poc.order_cnt >= 2;
```

注意事项：
- `new_customer_cte` 需要传入对应新客定义，并命名为 `new_customers`。
- 新客天然满足首购发生在查询期内，不需要在本模板中重复增加首购时间条件。
- 如果用户只说“二回/二次购买”但未说明新客或老客，需要先反问人群口径。

### sql.order.repeat_purchase_cycle_avg — 人群平均复购周期模板

- 用途：计算购买次数大于等于 2 的消费者的人群平均复购周期。
- 参数：`{shop_id}`, `{start_time}`, `{end_time}`, `{time_field}`, `{order_status_filter}`, `{extra_order_type_filter}`

```sql
WITH
    toDateTime('{start_time}') AS start_time,
    toDateTime('{end_time}') AS end_time,
    buyer_orders AS (
        SELECT
            cjyx_encrypt_pin,
            min({time_field}) AS first_order_time,
            max({time_field}) AS last_order_time,
            countDistinct(order_id) AS order_cnt
        FROM dwm.order_detail_d
        WHERE shop_id = '{shop_id}'
          AND {time_field} >= start_time
          AND {time_field} < end_time
          AND {order_status_filter}
          {extra_order_type_filter}
        GROUP BY
            cjyx_encrypt_pin
        HAVING order_cnt >= 2
    )
SELECT
    avg(dateDiff('day', first_order_time, last_order_time) / nullIf(order_cnt - 1, 0)) AS avg_repeat_purchase_cycle_days
FROM buyer_orders;
```

注意事项：
- 必须先 by 到消费者粒度，计算个人平均复购周期。
- 个人平均复购周期 = `dateDiff('day', first_order_time, last_order_time) / (order_cnt - 1)`。
- 最终结果是所有购买次数大于等于 2 消费者的个人平均复购周期均值。
- 不能直接用整体最晚订单时间减整体最早订单时间，也不能除以总订单数。

### sql.product.same_order_affinity_rank — 同单商品连带排行模板

- 用途：查询同一订单中既购买目标 SKU/SKU 集合/商品组/产品线，又购买其他商品的连带排行。
- 参数：`{shop_id}`, `{start_time}`, `{end_time}`, `{time_field}`, `{order_status_filter}`, `{target_sku_filter}`, `{other_dimension_field}`, `{top_n}`, `{extra_order_type_filter}`

```sql
WITH
    toDateTime('{start_time}') AS start_time,
    toDateTime('{end_time}') AS end_time,
    target_orders AS (
        SELECT DISTINCT
            order_id,
            cjyx_encrypt_pin
        FROM dwm.order_detail_d
        WHERE shop_id = '{shop_id}'
          AND {time_field} >= start_time
          AND {time_field} < end_time
          AND {order_status_filter}
          AND {target_sku_filter}
          {extra_order_type_filter}
    ),
    target_summary AS (
        SELECT
            countDistinct(cjyx_encrypt_pin) AS target_buyers,
            countDistinct(order_id) AS target_orders
        FROM target_orders
    )
SELECT
    sku.{other_dimension_field} AS other_product,
    countDistinct(ord.cjyx_encrypt_pin) AS affinity_buyers,
    countDistinct(ord.order_id) AS affinity_orders,
    countDistinct(ord.cjyx_encrypt_pin) / nullIf(any(ts.target_buyers), 0) AS affinity_buyer_rate,
    countDistinct(ord.order_id) / nullIf(any(ts.target_orders), 0) AS affinity_order_rate
FROM dwm.order_detail_d AS ord
INNER JOIN target_orders AS tgt
    ON ord.order_id = tgt.order_id
INNER JOIN dim.sku_gather_info AS sku
    ON ord.sku_id = sku.sku_id
CROSS JOIN target_summary AS ts
WHERE ord.shop_id = '{shop_id}'
  AND sku.shop_id = '{shop_id}'
  AND ord.{time_field} >= start_time
  AND ord.{time_field} < end_time
  AND {order_status_filter}
  AND NOT ({target_sku_filter})
  {extra_order_type_filter}
GROUP BY
    sku.{other_dimension_field}
ORDER BY
    affinity_buyer_rate DESC,
    affinity_buyers DESC
LIMIT {top_n};
```

注意事项：
- 同单连带必须限制在同一个 `order_id` 内。
- 主体目标可以是单个 `sku_id`、SKU 集合、商品组或产品线；需要先把目标商品口径转换为 `{target_sku_filter}`。
- 默认连带率按人数口径：连带购买人数 / 目标商品购买人数；同时输出订单口径用于复核。
- `other_dimension_field` 可为 `sku_id`、`sku_name`、`productline`、`brand_level_category2` 等。

### sql.product.cross_order_affinity_rank — 跨单商品连带排行模板

- 用途：查询同一消费者在查询期内既购买目标 SKU/SKU 集合/商品组/产品线，又购买其他商品的连带排行，不要求同一订单。
- 参数：`{shop_id}`, `{start_time}`, `{end_time}`, `{time_field}`, `{order_status_filter}`, `{target_sku_filter}`, `{other_dimension_field}`, `{top_n}`, `{extra_order_type_filter}`

```sql
WITH
    toDateTime('{start_time}') AS start_time,
    toDateTime('{end_time}') AS end_time,
    target_buyers AS (
        SELECT DISTINCT
            cjyx_encrypt_pin
        FROM dwm.order_detail_d
        WHERE shop_id = '{shop_id}'
          AND {time_field} >= start_time
          AND {time_field} < end_time
          AND {order_status_filter}
          AND {target_sku_filter}
          {extra_order_type_filter}
    ),
    target_summary AS (
        SELECT
            countDistinct(cjyx_encrypt_pin) AS target_buyers
        FROM target_buyers
    )
SELECT
    sku.{other_dimension_field} AS other_product,
    countDistinct(ord.cjyx_encrypt_pin) AS affinity_buyers,
    countDistinct(ord.cjyx_encrypt_pin) / nullIf(any(ts.target_buyers), 0) AS affinity_buyer_rate,
    countDistinct(ord.order_id) AS affinity_orders
FROM dwm.order_detail_d AS ord
INNER JOIN target_buyers AS tgt
    ON ord.cjyx_encrypt_pin = tgt.cjyx_encrypt_pin
INNER JOIN dim.sku_gather_info AS sku
    ON ord.sku_id = sku.sku_id
CROSS JOIN target_summary AS ts
WHERE ord.shop_id = '{shop_id}'
  AND sku.shop_id = '{shop_id}'
  AND ord.{time_field} >= start_time
  AND ord.{time_field} < end_time
  AND {order_status_filter}
  AND NOT ({target_sku_filter})
  {extra_order_type_filter}
GROUP BY
    sku.{other_dimension_field}
ORDER BY
    affinity_buyer_rate DESC,
    affinity_buyers DESC
LIMIT {top_n};
```

注意事项：
- 跨单连带以 `cjyx_encrypt_pin` 为消费者粒度，不限制同一 `order_id`。
- 默认连带率按人数口径：既买目标又买其他商品的人数 / 目标商品购买人数。
- 如果用户说“连带”但未说明同单或跨单，需要先反问场景类型。
- 其他商品默认排除目标商品自身，即 `NOT ({target_sku_filter})`。
