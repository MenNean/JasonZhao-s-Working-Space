# 数据库知识库

> 作用：记录 AI-BI 数字员工可理解和可调用的数据源、数据库、表、权限和查询边界。本库回答“数据在哪里、能不能查、查到什么粒度”。

## 一、建设状态

| 字段 | 状态 |
|---|---|
| 当前状态 | 已根据字段表与数据库信息原始文档补充数据库基础知识 |
| 数据来源 | `数据字典及样例.xlsx`；`数据库信息原始文档.docx` |
| 复核状态 | 基础信息已由附件确认；字段级白名单策略已确认；字段级可筛选/可分组状态仍待 BI 复核 |

## 二、数据库范围

| 项目 | 当前结论 |
|---|---|
| 数据库/引擎 | ClickHouse 数据仓库 |
| Schema/库名 | CK06 |
| 已识别 Schema | `dwm` 业务宽表层；`dim` 维度表层；`dws` 汇总层；`temp` 临时表层；`default` 部分报表或临时结果表 |
| 当前纳入知识库表数 | 3 |
| 生产查询权限 | 三张表均可交给 AI 查询 |
| AI 可查询白名单 | `dwm.order_detail_d`、`dwm.member_info_d`、`dim.sku_gather_info` 均可查询 |
| 刷新频率 | 每日定时同步 |
| 数据延迟 | T+1 |
| 同步完成时间 | 一般当日凌晨开始导入前一天数据，早上 9 点前完成 |
| 分区/同步相关字段 | `ods_create_time`、`etl_time` |
| 品牌/客户权限隔离 | 只可查看负责品牌的数据，权限隔离字段为 `shop_id` |
| 默认业务时间字段 | 默认使用下单时间 |
| 默认订单口径 | 默认使用有效订单 |
| SQL 执行方式 | AI 直接查询 |
| 字段白名单策略 | 三张表全字段可用于 AI 查询；敏感标识字段仅允许用于去重、关联和过滤，不允许明细展示 |
| 连接方式 | 待确认 |
| 账号类型 | 服务账号 |
| 账号权限范围 | 仅限 CK06 下三张表：`dwm.order_detail_d`、`dwm.member_info_d`、`dim.sku_gather_info` |
| 查询日志 | 必须记录 |

## 三、表级知识初版

| source_id | Schema | 表名 | 业务表名 | 字段数 | 样例行数 | 表用途 | 表粒度 | AI 可查询 | 复核状态 |
|---|---|---|---|---:|---:|---|---|---|---|
| order_detail_d | dwm | order_detail_d | 订单明细表 | 56 | 1000 | 最核心事实表，用于计算 GMV、订单数、购买人数、新老客、复购、SKU 销售情况等。 | 订单、SKU | 是 | 已由用户补充确认 |
| member_info_d | dwm | member_info_d | 会员信息表 | 16 | 1000 | 记录会员身份、开卡时间，用于判断是否会员和做人群分层。 | 用户、品牌 | 是 | 已由用户补充确认 |
| sku_gather_info | dim | sku_gather_info | 商品维表 | 23 | 1000 | 记录商品信息，用于区分产品线、大小罐、罐数等。 | 店铺、SKU | 是 | 已由附件确认 |

## 四、表详情

### dwm.order_detail_d

- 业务名称：订单明细表
- 表用途：最核心事实表，用于计算 GMV、订单数、购买人数、新老客、复购、SKU 销售情况等。
- 表粒度：订单、SKU。
- 主键/唯一识别字段候选：order_id, sku_id。
- 常用关联字段：sku_id, shop_id, cjyx_encrypt_pin。
- 常用时间字段：pay_confirm_time, order_start_time, order_end_time, order_cancel_time, refund_finish_time, datatime
- 默认业务时间：下单时间。若用户未指定特殊时间口径，订单分析默认按下单时间过滤和统计。
- 主要指标字段：order_amt, order_amt_total, order_amt_sale, order_amt_pay, freight_amt, sale_discount, sku_cnt, sku_amt_jd, sku_amt_page, refund_amt, refund_sku_cnt
- 主要维度字段：order_id, shop_id, shop_type, order_status_id, delivery_time, province, city, town, county, parent_order_id, dparent_order_id, order_type, pay_type, cjyx_encrypt_pin, product_name, lz_pin, vender_id, order_status_name, delivery_type, order_remark
- 可支撑 BI 场景：店铺经营总览, 会员与新老客经营, 商品购买次数分层分析, 复购与留存分析, 商品/SPU/SKU 机会分析, 价格带/客单价分析, 活动/大促 Daily Tracking, 退款分析
- 查询边界：可交给 AI 查询；必须遵守负责品牌的数据权限边界，并经过字段白名单、SQL 审核和日志记录约束。

### dwm.member_info_d

- 业务名称：会员信息表
- 表用途：记录会员身份、开卡时间，用于判断是否是会员和做人群分层。
- 表粒度：用户、品牌。
- 主键/唯一识别字段候选：shop_id, cjyx_encrypt_pin。
- 常用关联字段：shop_id, cjyx_encrypt_pin, brand_id, member_channel_id。订单表关联会员表时，默认通过 `shop_id + cjyx_encrypt_pin` 双字段匹配。
- 常用时间字段：open_card_time, member_level_change_time, member_level_start_time, member_level_end_time, etl_time
- 主要指标字段：无直接数值指标字段或待确认
- 主要维度字段：product_name, member_level, member_level_old, nick_name, open_card_type, member_level_name, ods_create_time, cjyx_encrypt_pin, is_unbind, member_channel_id, brand_id
- 可支撑 BI 场景：会员与新老客经营, 会员等级分析, 开卡与退会分析, 入会渠道分析
- 查询边界：可交给 AI 查询；必须遵守负责品牌的数据权限边界，并经过字段白名单、SQL 审核和日志记录约束。

### dim.sku_gather_info

- 业务名称：商品维表
- 表用途：记录商品信息，用于区分产品线、大小罐、罐数等。
- 表粒度：店铺、SKU。
- 主键/唯一识别字段：sku_id。`shop_id` 不唯一，同一个店铺下会有多个不同 SKU 商品。
- 常用关联字段：sku_id, shop_id, brand。`shop_id` 主要用于店铺/品牌权限过滤，不作为唯一键。
- 常用时间字段：datatime
- 主要指标字段：无直接数值指标字段或待确认
- 主要维度字段：shop_id, action_scope, update_person, sku_id, sku_name, main_categories, brand, platform_level_category1, platform_level_category2, platform_level_category3, brand_level_category2, brand_level_category3, productline, attribute1, attribute2, attribute3, attribute4, attribute5, attribute6, attribute7
- 可支撑 BI 场景：商品/SPU/SKU 机会分析, 商品连带分析, 商品购买次数分层分析, 价格带/客单价分析, 品类结构分析
- 查询边界：可交给 AI 查询；必须遵守负责品牌的数据权限边界，并经过字段白名单、SQL 审核和日志记录约束。

## 五、表关联关系初版

| 关系 | 关联字段 | 用途 | 状态 |
|---|---|---|---|
| order_detail_d -> sku_gather_info | `ord.sku_id = sku.sku_id`，查询时仍需用 `shop_id` 做权限过滤 | 将订单交易明细关联到商品、产品线、大小罐、罐数等商品信息 | 已由用户补充确认：`sku_id` 唯一，`shop_id` 不唯一 |
| order_detail_d -> member_info_d | `ord.shop_id = mem.shop_id` 且 `ord.cjyx_encrypt_pin = mem.cjyx_encrypt_pin` | 将订单交易明细关联到会员身份、开卡时间和人群分层 | 已由用户修正确认：会员关联默认使用 `shop_id + cjyx_encrypt_pin` |
| member_info_d -> 品牌/店铺维度 | brand_id / member_channel_id | 用于品牌和渠道维度分析，实际维表待补充 | 待补充 |

## 六、口径与码值规则

| 类型 | 规则 |
|---|---|
| 金额单位 | 金额字段单位为 `1 / 10000 元` |
| 完成订单 | `order_status_id IN (4, 105, 120, 121)` |
| 有效订单 | `order_status_id NOT IN ('5', '106', '109', '112', '113', '115', '118', '124', '128', '201')`，用于去除未支付、取消、关闭、拒收 |
| 默认订单口径 | 默认使用有效订单；除非用户明确要求“完成订单”或其他订单状态口径 |
| 会员等级 | `1-5` 对应 `1-5星会员` |
| 非会员 | `member_level = 0` |
| 是否退款 | `is_refund = 1` 表示退款 |
| 是否预售 | `is_presale = 1` 表示预售 |
| 是否退会 | `is_unbind = 1` 表示退会 |
| 开卡或入会渠道 | 第一版不需要对应码值，仅保留字段含义 |
| 订单类型、支付类型、绑定类型 | 暂无码值，第一版不解析码值，仅保留字段含义 |

## 七、长期待办

> 以下事项不阻塞当前第一版知识库建设，后续进入真实连接、生产执行或商品细分分析时再确认。

| 事项 | 当前处理方式 | 触发确认时机 |
|---|---|---|
| 实际分区字段 | 暂以 `ods_create_time`、`etl_time` 作为同步相关字段记录 | 需要优化查询性能、按分区裁剪或处理大范围查询时 |
| 数据库连接方式 | 当前标记为待确认，账号类型已确认为服务账号 | 技术侧开始接入 ClickHouse 或中间查询服务时 |
| 商品表大小罐、罐数字段映射 | 暂时忽略，作为非重要字段后续再补 | 需要按大小罐、罐数、规格做商品细分分析时 |

## 八、使用原则

- 样例值仅作为字段理解辅助，不作为可选值全集。
- 三张表均可交给 AI 查询，但必须遵守负责品牌的数据权限边界。
- 品牌权限隔离使用 `shop_id`，AI 查询必须带入负责品牌对应的 `shop_id` 范围。
- AI 执行方式为直接查询；查询时必须默认带入 `shop_id` 权限边界、下单时间口径和有效订单口径。
- AI 查询使用服务账号，权限范围仅限 CK06 下三张表，并且必须记录查询日志。
- 订单表关联商品表以 `sku_id` 为主；`shop_id` 不唯一，主要用于权限过滤和店铺范围限定。
- 订单表关联会员表时，必须使用 `shop_id + cjyx_encrypt_pin` 双字段匹配，避免同一用户跨店铺/品牌多行导致错误匹配。
- 第一版不解析开卡/入会渠道、订单类型、支付类型、绑定类型码值，仅保留字段含义；退款、预售、退会按标记字段 `=1` 判断。
- 数据为 T+1，同步一般在早上 9 点前完成；查询当日数据时需提示可能未同步，默认稳定查询到前一天。
- 查询前应增加数据同步检测机制：如果前一天数据为 0，则返回“数据同步失败，请咨询中台数仓负责人”。
- 三张表全字段可用于 AI 查询；敏感标识字段仅允许用于去重、关联和过滤，不允许明细展示。
- 涉及生产查询时，仍需确认权限隔离、SQL 审核规则和查询日志机制。

## 九、敏感字段展示规则

| 字段 | 所在表 | 允许用途 | 禁止用途 |
|---|---|---|---|
| `cjyx_encrypt_pin` | `dwm.order_detail_d`、`dwm.member_info_d` | 用户去重、购买人数计算、订单表与会员表关联、人群过滤 | 作为明细结果展示给用户 |
| `lz_pin` | `dwm.order_detail_d` | 去重、关联、过滤 | 作为明细结果展示给用户 |
| `nick_name` | `dwm.member_info_d` | 必要时用于内部识别和核验 | 作为明细结果展示给用户 |

## 十、数据同步检测规则

| 项目 | 规则 |
|---|---|
| 数据延迟 | T+1 |
| 同步窗口 | 当日凌晨开始导入前一天数据，通常早上 9 点前完成 |
| 默认可稳定查询日期 | 前一天及更早日期 |
| 当日数据查询 | 需要提示数据可能尚未同步，不作为默认稳定口径 |
| 异常检测 | 查询前一天数据时，如果数据量为 0，则判定为疑似同步失败 |
| 异常返回 | `数据同步失败，请咨询中台数仓负责人` |

## 十一、连接与审计规则

| 项目 | 规则 |
|---|---|
| 连接方式 | 长期待办，后续由技术侧确认 |
| 账号类型 | 服务账号 |
| 权限范围 | 仅限 CK06 下三张表：`dwm.order_detail_d`、`dwm.member_info_d`、`dim.sku_gather_info` |
| 查询日志 | 必须记录 |
| 建议日志字段 | 提问内容、生成 SQL、执行时间、查询账号、`shop_id` 范围、查询表、返回行数、异常信息 |
