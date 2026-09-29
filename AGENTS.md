# Steam Lens 仓库说明

这是已有的中文 Steam 游戏筛选与推荐工具，不是空白脚手架。当前交接基线为 v1.1 封面修复版。

## 接手

先读取 `.agents/skills/steam-lens-maintainer/SKILL.md`，按本轮任务加载其 references。检查现有工作区改动，不用基线包覆盖用户更新。不需要从头搭建新框架。

## 源文件与产物

- 前端：`app.js` + `ui.template.html`。
- 构建：`python build.py`，生成 `steam_lens.html` 和 `demo_data.json`。
- 服务：`python server.py --no-browser`，仅本机访问。
- 不要只改生成 HTML。修改后同步构建产物。

## 保持不变

保留价格、类型、语言/配音、评分、排序、统计、对比、收藏与导入导出。保留 `steam-lens.v1` 存储键与地区/币种隔离。未明确授权，不引入账号、公共代理、后台全库采集、付费 API 或框架迁移。

36 款内置样例不是实时数据。未知价格不是免费，零评价不是 0% 好评。旧缓存时间不能冒充本次采集时间。真实数据和封面未完成全量端到端验证。

## 检查

```bash
python .agents/skills/steam-lens-maintainer/scripts/run_checks.py --root . --browser
```

Node 用于 JS 语法检查，Playwright/Chromium 仅用于前端测试；应用本身不需要它们。缺依赖如实记录。测试、真实 Steam 抽样和未验证事项分别报告。

## 交付

给出最小代码修改、构建后的 HTML、实际测试结果和使用方法。不得把历史测试报告当作本轮执行结果。未经用户要求不自动提交、推送或部署。
