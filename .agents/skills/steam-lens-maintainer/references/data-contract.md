# 数据契约、评分与兼容性

以当前源码为最终运行行为；本文件记录 v1.1 的维护约束，不保证外部 Steam 数据当前可用。

## 数据模式与身份

`state.mode` 是 `demo` / `live` / `import`；游戏 `source` 是 `demo` / `steam` / `imported`，名称不同不可混用。导入文件声称 Steam 来源不能直接升级为可信采集记录；演示标识不能被导入流程抹掉。

游戏池按地区隔离，去重按地区 + AppID。收藏是本浏览器 AppID 集合，不是远程 Steam 愿望单。默认 localStorage 键 `steam-lens.v1`；不要通过清空本地存储修复无关故障。

地区与币种：`cn→CNY`、`hk→HKD`、`us→USD`、`jp→JPY`。拒绝不一致，不自行换汇成某地区商店报价。

## 字段

| 字段 | 语义 |
| --- | --- |
| `appid` | 合法正整数，当前上限 9,999,999,999 |
| `name`, `aliases` | 展示与搜索文字；渲染需转义 |
| `price`, `originalPrice` | 主货币单位或 `null`，例如 CNY 48 表示 48 元 |
| `discount` | 0–100 或未知；无价格时不生成折扣值 |
| `isFree` | 明确免费才为 true，且 price 必须为 0 |
| `genres`, `tags` | 不把商店 genres 冒充社区标签；未接入真实标签时不伪造 |
| `languages`, `audioLanguages` | 语言代码数组或 `null`；未知与已知空列表不同 |
| `reviews` | `null` 或 `{positive, negative, total, description, scope}` |
| `metacritic` | 0–100 或 `null`，不是 Steam 好评率 |
| `platforms` | windows/mac/linux，布尔或未知；不推断特定硬件帧率 |
| `requirements` | 按平台区分最低/推荐配置，作为文字展示，不执行原始 HTML |
| `detailsAt`, `reviewsAt` | 各自原始采集时间；部分失败不能统一改成当前时间 |
| `warnings` | 缓存过期、字段缺失等提示，卡片/详情/导出保留必要信息 |
| `headerImage`, `capsuleImage`, `capsuleImageV5` | v1.1 可选封面字段；保留完整官方地址但先通过安全校验 |
| `coverUrls` | 前端可接受最多 6 条已校验候选；不是任意站点图片入口 |

评论正负数必须是非负整数且 `positive + negative == total`。零评论的好评率和 Wilson 分都是未知，不能渲染成 0%。

中文配音与语言支持独立；商店支持中文不自动等于全中文配音。macOS 标签也不等于 Apple Silicon 已验证兼容。

## 当前评论请求口径

`fetch_app` 使用 `query_summary`，请求 `language=all`、`purchase_type=steam`、`review_type=all`、`filter_offtopic_activity=1`。不是所有购买来源的评论，也不是近期好评率；`day_range=365` 不能被当作近期汇总定义。改变口径时需要同步文案、导出、数据 scope 和测试。

## 推荐分

默认权重：口碑 65、价格 20、折扣 10、中文支持 5，按总权重归一化。不是 Steam 官方排名，也不是机器学习推断的用户喜好。

```text
z = 1.96
p = positive / total
quality = 100 × [p + z²/(2n) − z × sqrt((p(1−p) + z²/(4n))/n)] / [1 + z²/n]
priceScore = clamp(100 × [1 − log1p(price) / log1p(anchor)], 0, 100)
languageScore = 支持简体或繁体中文 ? 100 : 0
score = Σ(component × weight) / Σ(weight)
```

`n=0` 时口碑未知。anchor 优先取有效的最高预算，否则为 CNY 200 / HKD 240 / USD 40 / JPY 5000；这些是设计参数，不是市场统计。

任一非零权重依赖的字段缺失，推荐分必须未知；某权重为零时允许忽略该字段缺失。未知值在升序和降序中均排在数值之后；同分使用稳定兜底顺序，避免刷新后乱跳。

## 导入导出与统计

JSON `schemaVersion: 1`，v1.1 的封面字段是可选扩展。旧文件没有封面字段时仍应能导入。

单文件上限 20 MB，单批最多 5,000 条。先验证整批再确认合并；重复地区 + AppID、币种不一致和评论计数错误都不能半批写入。CSV 使用 UTF-8 BOM、完整排序结果、正确引号和公式注入防护。

统计仅覆盖当前筛选结果：价格中位数仅使用已知价格，包含明确免费项；汇总好评率用总正面评论数 / 总评论数，不是各游戏好评率简单平均。多类型分布允许一款游戏落在多个类型，不能误标成互斥占比。

## 上游缓存和安全

v1.1：详情 3,600 秒、评论 21,600 秒、搜索 900 秒；缓存按完整请求 URL 区分。失败读旧缓存时保留原 fetched 时间并标注 warning。

后端上游只允许固定 Steam 商店域名；全局串行间隔至少 1.6 秒、5xx 最多重试一次、429 冷却并处理 Retry-After。当前本机服务只面向个人使用，不是公网多用户服务。优化吞吐之前先确认限流边界，不用更高并发掩盖稳定性问题。
