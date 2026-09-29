# 在 Codex 中继续优化 Steam Lens

当前工作区已更新为 v1.2 舒适阅读与封面更新。最新使用方法见 [README_中文.md](README_中文.md)，本轮执行结果见 [TEST_REPORT_v1.2.md](TEST_REPORT_v1.2.md)。下方关于 Skill 打包与 v1.1 的说明属于原始交接记录。

原始接手包带有 v1.1 封面修复版完整项目，以及项目级 Skill；不需要再下载之前的 HTML。

## 直接开始

将完整包解压到一个新的工作目录，在 Codex 中打开包含 `AGENTS.md`、`app.js`、`server.py` 的 `steam-lens` 文件夹。

把 `CODEX_START_PROMPT.md` 中的内容粘贴给 Codex。Skill 名称是 `$steam-lens-maintainer`。

本包已放好：

```text
.agents/skills/steam-lens-maintainer/SKILL.md
```

Codex 当前官方文档支持此仓库级位置。CLI/IDE 可输入 `$` 或 `/skills` 选择；没有显示时重新打开会话或重启 Codex。也可以明确让 Codex 读取这个文件继续工作，但这不等同于已经验证客户端自动发现成功。

## 你已经有更新过的项目

不要用完整基线覆盖它。只复制 `.agents/skills/steam-lens-maintainer/` 到现有项目对应位置；已有同名 Skill 时先比较。`AGENTS.md` 仅供参考，已有仓库指令应手工合并，而非覆盖。

Skill 独立包也可将 `steam-lens-maintainer` 目录放进用户目录的 `.agents/skills/`；不需要同时装项目级和用户级同名副本。macOS Finder 默认隐藏点开头目录，可用显示隐藏文件快捷键，或直接访问完整路径。

## 独立 Skill 如何恢复源码

使用独立 Skill 包且没有项目时，从该 Skill 所在目录运行：

```bash
python scripts/bootstrap_project.py --dest "../steam-lens-work"
```

目的目录必须不存在。脚本检查压缩包与文件哈希、恢复原项目，并安装此 Skill 和接手说明；不会改 Steam、用户目录或远程仓库。

## 本机试运行

直接打开 `steam_lens.html` 可体验演示界面。联网采集使用：

```bash
python server.py
```

macOS/Linux 使用 `python3` 也可以；然后打开 `http://127.0.0.1:8765`。运行时只需 Python 标准库。浏览器图片仍需外部网络。

完整测试：

```bash
python .agents/skills/steam-lens-maintainer/scripts/run_checks.py --root . --browser
```

测试依赖、状态和报告路径详见 Skill 的 `references/validation.md`。新的报告位于 `.codex-checks/`。

## 实际验证边界

Skill 打包保留了原应用文件；本次重新运行 31 个后端测试、54 个前端检查和 40 个封面检查，全部通过。其 Steam 响应与图片是模拟数据，未完成真实 Steam 接口/CDN 端到端验证，也没有在用户的 Codex 客户端执行安装实测。

详见 `.agents/skills/steam-lens-maintainer/references/handoff-verification.md`。

官方安装格式来源（2026-09-29 核对）：https://developers.openai.com/codex/skills/
