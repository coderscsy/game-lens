# 源码地图与构建入口

文件名是 v1.1 的真实文件；函数可能随用户后续修改移动，优先按符号查找，不依赖旧行号。

| 文件 | 作用 / 关键位置 |
| --- | --- |
| `app.js` | 全部前端逻辑；`REGIONS`、`DEFAULT_WEIGHTS`、`STORAGE_KEY`、`state`、`filters` |
| `ui.template.html` | 页面骨架及 CSS；`__DEMO__` 与 `__SCRIPT__` 构建占位符；`.cover` / `.cover-image` / `.detail-hero` 相关规则 |
| `build.py` | 将模板、JS 与固定随机种子的演示数据打包到单文件 HTML，同时生成 demo JSON |
| `steam_lens.html` | 生成产物，面向使用者；不要只修改它而遗漏源文件 |
| `demo_data.json` | 导入结构样例；内容为模拟数据，构建会重新生成 |
| `server.py` | 本机 HTTP、Steam 适配器、SQLite 缓存、标准化 |
| `test_server.py` | 标准库后端单元与本机 HTTP 合同测试 |
| `test_frontend.py` | Playwright 前端交互与模拟联网回归 |
| `test_covers.py` | Playwright 封面加载与前后端 URL 契约检查 |
| `README_中文.md` / `CHANGELOG_封面修复.md` | 原使用说明与最近变更 |
| `TEST_REPORT.md` / `*-test-results.json` | 原交付报告，不能代表未来执行结果 |
| `start_windows.bat` / `start_mac.command` / `start_linux.sh` | 仅运行应用；不用测试依赖 |

## 前端定位

- 数据清洗：`normalizeGame`、`restoreCatalog`、`persist`。
- 封面：`safeSteamImage` → `coverCandidates` → `coverMarkup` → `CoverLoader.init/retry/retryFailed`。
- 推荐：`ratio`、`wilson`、`recommendation`、`sortValue`、`sortGames`。
- 筛选/统计：`filterGames`、`dataset`、`renderStats`、各图表渲染和 `render`。
- 联网：`isLocal`、`api`、`showNetwork`、`runTask`、`parseIds`；`state.abort` 与 `state.cancelled`。
- CSV：`csvCell`，保留公式注入处理。
- 测试接口：`window.SteamLensTest`。现有测试依赖其导出；重构时同步测试，不要误当作生产服务 API。

## 后端定位

- 图片 URL：`safe_steam_image`；与前端校验规则要一致。
- 上游：`SafeRedirect`、`_remote`、`cached`、`get_json`。
- 详情及评论：`fetch_app`、`normalize_app`、`parse_languages`。
- 搜索：`SearchParser`、`discover`。
- 本机访问：`Handler.allowed`、`Handler.do_GET`、`main`。

## 本机 HTTP 契约

本项目不是一个接受任意 URL 的代理。

| 路径 | 参数 / 行为 |
| --- | --- |
| `/`、`/index.html`、`/steam_lens.html` | 返回构建好的 HTML |
| `/api/health` | 本机服务状态，`upstreamVerified` 保持明确语义 |
| `/api/app` | `appid`、`cc`、`refresh=1`（可选）；成功返回 `{"game": ...}` |
| `/api/discover` | `cc`、`term`、`kind`、`start`；候选 AppID 和分页信息 |

API 需 `X-Steam-Lens: 1`；Host/Origin 同源校验独立保留。基础 HTML 本身不要求此自定义头。

## 构建与运行

```bash
python build.py
node --check app.js
python server.py --no-browser
```

先改源码，再构建。检查生成 HTML 不残留 `__DEMO__` / `__SCRIPT__`，不引用开发机绝对路径，不引入额外 JS 或字体 CDN 依赖。

应用默认 `127.0.0.1:8765`。用另一个端口、另一个浏览器或 `file://` 打开时，不能假设 localStorage 与原地址共享。
