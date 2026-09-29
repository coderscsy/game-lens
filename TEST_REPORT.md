# v1.1 验证报告 — 封面修复

验证日期：2026-09-29。

## 本轮结果

- `node --check app.js`：通过。
- `python -m py_compile server.py test_covers.py`：通过。
- 原有后端测试：31 项通过，使用 Python 标准库与模拟上游；真实本机 HTTP 服务合同测试也通过。
- 原有前端测试：54 项通过，覆盖筛选、排序、收藏、对比、详情、导入导出、地区切换、布局和模拟联网队列。
- 新增封面专项检查：40 项通过，详见 `cover-test-results.json`。

## 封面专项范围

官方 header / capsule 路径及 hash / 查询参数保留；前端标准化与数据往返；同 AppID 校验；非 Steam 域名、伪造域名后缀、脚本 URL 和 URL 凭据拒绝；允许的旧 HTTP 图片升级到 HTTPS。

404 后切换备用源；成功图片显示并隐藏占位文字；图片等比、不裁切；卡片和详情 header 宽高比；成功源在会话内复用；全部失败的次数限制、占位和重试按钮；短期失败记忆；手动重试可恢复且不误开详情；不改变游戏库或收藏；HTTP 200 的 1×1 错误像素拒绝；单源超时自动切换；迟到响应不覆盖已选图片；快速切换不串图，已移除卡片停止后续尝试；总超时停止；关闭封面设置不发送图片请求；手机无横向溢出，小屏单列。

## 不包含的验证

**没有成功读取真实 Steam CDN 图片，也没有逐款验证 36 款演示游戏的真实封面。** 制作环境的直接图片请求无法解析 `shared.fastly.steamstatic.com`。这些测试证明的是加载器的控制逻辑和显示状态，不是所有资源地址当前都可用。测试用图片是运行脚本生成的合成 PNG 色块，并非真实游戏画面。

页面通过 Playwright `set_content` 渲染实际交付 HTML；about:blank 中仅测试文档增加 localStorage 替身。专项图片请求由测试路由返回合成 PNG / 404 / 网络错误，超时用 Playwright 时钟推进实际生产阈值；这些替身和模拟路由不在交付 HTML 中。原有联网队列测试仍使用模拟 fetch，不是实际 Steam 请求。

真实封面可达性、Steam 详情与评论端到端采集，仍需要在用户本地网络中验证。内置演示价格、评分、语言等保持模拟标记。

## 复现

运行应用本身不需要第三方依赖。后端测试：

```bash
python build.py
python -W error::ResourceWarning -m unittest -v test_server.py
```

前端测试需要另行安装 Playwright 和 Chromium；可用 `CHROMIUM_PATH` 指定已有浏览器：

```bash
python test_frontend.py
python test_covers.py
```

前端结果写入 `frontend-test-results.json`，专项结果写入 `cover-test-results.json`。
