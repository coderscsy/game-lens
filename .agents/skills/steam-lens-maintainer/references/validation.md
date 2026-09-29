# 验证与交付

## 测试环境与应用环境分开

应用运行只需浏览器；可选服务需要 Python 3.10+ 标准库。前端测试另需 Python Playwright 与 Chromium，JS 语法检查用 Node。不要把测试依赖加成用户运行 HTML 的前置条件。

在当前环境允许安装开发依赖时可执行：

```bash
python -m pip install playwright
python -m playwright install chromium
```

已有 Chromium 可设置 `CHROMIUM_PATH`。Windows PowerShell 示例：

```powershell
$env:CHROMIUM_PATH = "C:\path\to\chrome.exe"
```

此路径只是示例，不要假定用户电脑上已存在。不得降低浏览器安全设置来绕过问题。

## 推荐入口

项目根目录：

```bash
python .agents/skills/steam-lens-maintainer/scripts/run_checks.py --root . --browser
```

包装器依次构建、检查 Python/JS 语法、运行后端、前端、封面测试。每步记录状态、退出码、耗时和原始日志。默认不安装依赖，不联系真实 Steam；基础模式未传 `--browser` 会明确标为跳过浏览器检查。

构建会更新 `steam_lens.html` 与 `demo_data.json`，浏览器测试会更新原有结果 JSON；检查前保护用户已有变更。日志和总报告进入新的 `.codex-checks/` 子目录，不提交本机敏感环境路径或缓存。

退出码：0 表示本轮请求执行的检查通过；1 表示失败；2 表示必要依赖缺失。未请求浏览器检查的 0 不代表完整回归已通过。`--browser` 下缺少 Playwright/浏览器要报告，不转成通过。

## 等价原生命令

```bash
python build.py
node --check app.js
python -m py_compile server.py build.py test_server.py test_frontend.py test_covers.py
python -W error::ResourceWarning -m unittest -v test_server.py
python test_frontend.py
python test_covers.py
```

基线是 31 个后端测试、54 个前端检查、40 个封面检查。此数字是历史基线，不是未来硬编码的正确答案；新增测试后应以当次实际输出为准。

## 验证层级

| 层级 | 能证明什么 | 不能证明什么 |
| --- | --- | --- |
| 静态/语法 | 文件可解析、生成产物完整 | 业务交互正确 |
| 单元与本机 HTTP | 标准化、缓存、访问保护等合同 | Steam 上游当前可用 |
| Playwright 模拟 | 浏览器交互、图片成功/失败/竞态、布局 | 真实图片 URL 存在或所有网络可访问 |
| 本机真实 Steam 抽样 | 指定时间、地区、AppID 的详情/评论/图片观测 | 永久可用或已覆盖全库 |

前端测试使用合成 PNG、路由模拟、about:blank 存储替身和模拟 fetch；不要将测试替身注入生产 HTML。

## 交付检查

- 单文件 HTML 与源代码一致；构建不残留占位符。
- 价格/地区/评分/语言/收藏/对比/导出没有被封面修改破坏。
- 没有真实数据时保持演示或未知状态，显示信息不掩盖缓存过期。
- 桌面与窄屏操作可用；图片失败可恢复，不串图、不无限重试。
- 记录当前具体测试命令、结果与限制，不复制旧测试报告充数。
- 保留许可证；ZIP 不包含 `.steam_lens_cache.sqlite3`、浏览器个人数据、密钥、`.git` 或虚拟环境。
- 未经要求，不迁移框架、不全库爬取、不改 Steam 账号、不推送远端。

## Skill 辅助工具本身的测试

下面只测试初始化与报告脚本，不代替应用回归：

```bash
python .agents/skills/steam-lens-maintainer/scripts/test_skill_tools.py
```

全用 Python 标准库，不访问真实 Steam。本次 12 个测试覆盖拒绝覆盖、哈希与路径安全、报告状态和构建失败保护。
