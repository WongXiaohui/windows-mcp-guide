# Windows-MCP 接入指南（实测验证版）

> **给 AI Agent 的说明**
> 如果你（另一个 AI）是被指到本仓库来的，任务大致是：**在这台电脑上，把 `CursorTouch/Windows-MCP`
> 接入到 WorkBuddy，让 Agent 获得「不靠图像识别、直接读写 Windows 界面」的能力**（读无障碍树 + 控制鼠标键盘）。
>
> 直接读 **[`docs/windows-mcp-setup-guide.md`](docs/windows-mcp-setup-guide.md)** —— 那是主操作手册，
> 5 步走完，全程已实测跑通，含 10 条踩坑清单。**不要自己从头摸索，先读它。**

---

## 这是什么

一份**跨机可复用的接入手册**，把 `CursorTouch/Windows-MCP` 接入 WorkBuddy 的完整过程记录下来，
包括所有踩过的坑。目标是让另一台电脑上的 Agent **照着做即可，不必重复试错**。

所有步骤均在 **Windows 10 LTSC 2021（zh-CN，简体中文系统）** 上完整实测验证。

## 核心结论（三句话）

1. **`Snapshot` 返回 Windows UI Automation 无障碍树** —— 纯文本的元素名 / 类型 / 坐标，
   **全程不需要图像识别/视觉模型**，零推理开销，不受分辨率、DPI、主题、系统语言影响。
2. **中文系统完全可用**，无需把系统语言改成英文（README 那句 "English preferred" 是过时信息，
   只影响 `App` 一个工具，官方 issue #372 已修）。
3. **最容易卡住的一步不是配置，是"界面激活"** —— WorkBuddy 不会监听 `mcp.json` 的文件变化，
   必须在界面里手动触发一次加载（详见手册 §4）。

## 目录结构

```
.
├── README.md                              ← 本文件（总览 + 快速开始）
├── docs/
│   ├── windows-mcp-setup-guide.md         ★ 主手册：跨机复用版，12 章，照做即可
│   ├── verification-log.md                  验证记录：本机实测过程与结果
│   └── desktop-control-survey.md            调研报告：39 个同类项目横向对比（含备选方案）
└── tools/
    └── mcp_probe_generic.py                 通用探针：不依赖界面，直接验证 MCP 能否跑通
```

## 快速开始（5 步，细节见主手册）

| 步骤 | 做什么 | 关键点 |
|---|---|---|
| 1 | 检查环境 | 需要 `uv`（Python 包管理器）、Python ≥3.14（交给 uv 自动拉） |
| 2 | 写配置 | 文件是 `%USERPROFILE%\.workbuddy\mcp.json`（**不是** `.codebuddy/.mcp.json`） |
| 3 | 预拉取（建议） | `uvx --python 3.14 windows-mcp --help`，让首次连接变快 |
| 4 | **界面激活** ⚠️ | 连接器管理 → 右上角「自定义连接器」→ **「配置 MCP」→ 保存** → 点「信任」 |
| 5 | 验证 | 调 `Snapshot(use_vision=false)`，**返回文字**（含中文按钮名）即成功 |

## 三个必知的坑（完整清单见手册 §6）

1. **配置改完不会自动生效** —— 必须点「配置 MCP → 保存」，或完全退出 WorkBuddy 重启。
   否则连接器列表里永远只有内置的 `miora`。
2. **`command` 必须写绝对路径** —— WorkBuddy 是 GUI 进程，`PATH` 里没有 `~/.local/bin`，
   写 `"uvx"` 会报"命令找不到"。要写 `C:\Users\<你的用户名>\.local\bin\uvx.exe`。
3. **适配器版本取决于 Python** —— `windows-mcp` 0.8.8 要求 Python ≥3.14，
   配置里写 `--python 3.14` 让 uv 自己下载即可，本机不需要预装。

## 环境要求

| 项目 | 要求 |
|---|---|
| 操作系统 | Windows 7/8/8.1/10/11（**系统语言不限**，中文实测可用） |
| WorkBuddy | 桌面版（走 `~/.workbuddy/mcp.json`，**不是** CLI 版） |
| uv | 任意较新版本（实测 `uv 0.13.0`）；国内建议配清华源 |
| Python | 无需预装 3.14，`uvx --python 3.14` 会自动拉取（实测 24 秒装完 92 个包） |
| 网络 | 能访问 PyPI（国内用 `UV_DEFAULT_INDEX` 指镜像） |

## 安全提醒（务必读）

接入后一共 **21 个工具**，其中 `PowerShell` / `Registry` / `FileSystem` 属于最高危级别，
**合起来等于整台电脑的完全控制权**。手册 §10 给了三档加固方案（只读只点 / 去掉高危 / 全功能），
建议**先用保守档，确认好用再放开**。

另外它内置了"用户接管保护"：**你一动鼠标键盘，Agent 的控制权立刻交还**（返回 `USER_CONTROL`），
需空闲约 10 秒才能重新接管。**这不是故障。**

## 来源与许可

- 目标项目：[CursorTouch/Windows-MCP](https://github.com/CursorTouch/Windows-MCP)（MIT License）
- 本仓库内容为实测经验整理，仅供参考；`Windows-MCP` 的版本要求与工具列表可能随上游更新而变化。
- 整理时间：2026-10-11
