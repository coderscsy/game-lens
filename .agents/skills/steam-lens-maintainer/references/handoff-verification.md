# Skill 交接验证记录

日期：2026-09-29。仅记录本次真实执行结果，不代替下一轮 Codex 的基线测试。

## 来源完整性

基线文件：会话提供的 `steam_lens_fixed_full.zip`，18 个原项目文件。单独提供的修复版 HTML 与 ZIP 中 HTML 的 SHA-256 一致；重新运行 build.py 后也保持一致。

```text
原 ZIP SHA-256：10e83bb302f07981444f925cf167c0f98fec55f15a58251d941398e5c2df03e5
HTML SHA-256：9fdba27351f3e4924b8718c855b9bbed71ee614eb2b5b34c1ac88562dba5473c
```

全部文件清单见 `../assets/baseline-manifest.json`。本次仅增加 Skill、交接文档与辅助脚本，未改原应用的业务代码。

## 本次应用回归

先在原包副本中执行构建、JS 语法检查及三套测试；随后使用新增 `bootstrap_project.py` 恢复另一份工作副本，再用新增 `run_checks.py --browser` 完整执行一遍。

| 检查 | 结果 |
| --- | --- |
| build.py 构建 | 通过；生成物与交付修复版一致 |
| Python 语法检查 | 通过 |
| node --check app.js | 通过 |
| 后端 unittest | 31 个通过 |
| Playwright 前端检查 | 54 个通过 |
| Playwright 封面检查 | 40 个通过 |
| 新增 Skill 工具单元测试 | 12 个通过 |

原始报告：[本次检查报告](verification/report.md)、[机器可读报告](verification/report.json)。[Skill 工具测试日志](verification/skill-tools-tests.log)。

执行环境：Python 3.13.5、Node 22.16.0、Playwright 1.57.0、Chromium 144.0.7559.96、Linux。这是验证环境，不是要求用户必须安装完全相同版本。

## Skill 工具验证

初始化检查了真实 ZIP 和逐文件哈希、拒绝非空/空的已有目录、拒绝在 Skill 内初始化、拒绝篡改 ZIP 和路径穿越。报告包装器检查了主动跳过、缺失 Node、缺失 Playwright、构建失败阻止使用旧 HTML，以及按真实输出读取计数而不是硬编码基线数字。

工具单测中的报告分支采用模拟子进程结果；上述 31/54/40 项应用检查则由真实 Python 和 Chromium 执行，并使用原测试定义的模拟 Steam 上游/合成图片。

## 仍未验证

- 没有真实访问 Steam 商店详情、评论接口或 CDN 做端到端抽样；不能宣称真实封面全通过。
- 没有在用户的 Codex 客户端安装或运行这个 Skill。结构、YAML、相对文件链接和恢复流程已本地检查；自动发现规则按 2026-09-29 的官方文档整理。
- 没有在 Windows/macOS 真机上执行新增 Python 脚本；使用标准库与跨平台 Path/subprocess 编写，实际平台异常需在目标机复现。

应用原 `TEST_REPORT.md` 与两个测试结果 JSON 仍保留在原位置，属于旧交付记录。下一轮维护必须重新执行相应检查。
