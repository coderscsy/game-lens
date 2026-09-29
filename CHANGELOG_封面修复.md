# v1.1 — 封面修复

## 旧版已确认的问题

1. `coverMarkup()` 只拼接单一 `shared.fastly.steamstatic.com/.../{AppID}/header.jpg`，没有备用资源。
2. 前端 `normalizeGame()` 与后端 `normalize_app()` 均丢弃官方封面 URL，因此采集后也无法利用完整文件名及 hash 子目录。
3. 页面上的全局图片错误监听器直接隐藏图片，不重试、不提示用户如何恢复。
4. 卡片使用固定高度 + `object-fit:cover`，详情横幅也被固定在很矮的高度，比例不匹配时会裁掉标题或主体。

## 本次修改

- 保留 API 的 `header_image`、`capsule_image`、`capsule_imagev5`，序列化成可选 `headerImage` / `capsuleImage` / `capsuleImageV5`；JSON 导入、导出和本地数据恢复保留字段。
- 支持完整图片路径、hash 子目录和查询参数。限定 HTTPS / Steam 图片域名及当前 AppID，拒绝脚本地址、外部站点、跨游戏地址和 URL 用户凭据。
- 完整官方 URL 优先，其次尝试同一路径的备用 Steam CDN，以及有限的常用旧路径。候选去重，上限 12 个，整轮硬超时 18 秒。
- 懒加载，单源超时 4.5 秒；独立图片对象预载成功后再进入可见 DOM，防止破图和旧请求覆盖新卡片。
- 成功源会话内复用；短期失败缓存减少反复排序的请求；全部失败提供占位状态和手动重试。离开卡片时停止其后续尝试。
- 图片容器按照 920:430 的 header 比例，使用 `object-fit:contain` 完整显示。图片比例不同可能出现留白，这是为了不裁切内容。窄屏手机改为单列，避免封面和状态按钮挤在一起。
- 加入 40 项封面专项检查，原有 54 项前端检查和 31 项后端检查保持通过。

## 保持不变

不改推荐公式、游戏排序、过滤条件、演示数据属性、地区币种口径、收藏存储键或服务端端口；不使用公共跨域代理，不新接入账号，不后台采集全库。

## 验证范围

所有专项图片测试使用合成 PNG / 模拟 HTTP 结果。真实 Steam CDN 在制作环境中无法解析域名，不能声称用户本地或所有游戏图片均已实测成功。

布局比例参考 Steamworks 的 Store Graphical Assets 文档：
https://partner.steamgames.com/doc/store/assets/standard
