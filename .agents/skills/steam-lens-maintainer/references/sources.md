# 来源与版本说明

## 本次检查过的官方 Skill 资料

核对日期：2026-09-29。OpenAI 的 Codex skills 文档地址目前重定向到统一的 Build skills 页面。

- https://developers.openai.com/codex/skills/
- https://learn.chatgpt.com/docs/build-skills

采用其中的 `SKILL.md` + YAML `name/description`、可选 `scripts/references/assets/agents/openai.yaml` 结构。仓库级安装使用 `.agents/skills`，用户级可使用 `$HOME/.agents/skills`；CLI/IDE 可用 `$技能名` 或 `/skills` 选择。未显示时重新打开会话或重启 Codex。不是 `.skill` 专有格式，也不需要杜撰一条 ZIP 安装命令。

本包是本地开发/项目接手 Skill，不是已发布的官方插件，不代表已经安装到用户电脑或完成 Codex 客户端加载实测。

## 原项目已记录的外部资料

以下链接从原项目文档继承，本次只核对了 Skill 格式；若要改接口、许可或依赖，需要再次读取相关一手文档并记录日期。

- Steam 评论接口：https://partner.steamgames.com/doc/store/getreviews
- Steam 商店素材：https://partner.steamgames.com/doc/store/assets/standard
- Augmented Steam：https://github.com/IsThereAnyDeal/AugmentedSteam
- SteamStorefrontAPI：https://github.com/mmuffins/SteamStorefrontAPI
- MDN CORS：https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS
- Playwright Python 安装：https://playwright.dev/python/docs/intro

Augmented Steam 和 SteamStorefrontAPI 是原项目记录的参考方向，不是本包运行依赖；本包未新增它们的源码。发现新的开源实现时先读许可证，不假定所有项目都能按 MIT 混用。

## 基线真实性

`assets/baseline-manifest.json` 包含原 ZIP、单文件 HTML 和每个原文件的 SHA-256。`bootstrap_project.py` 校验 ZIP 和条目后只向全新目录恢复。

原包的模拟数据、历史报告和未验证限制一并保留，不能把它们解释成刚刚抓取的真实 Steam 数据。
