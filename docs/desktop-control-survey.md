# Agent 本机控制能力调研报告

> 调研时间：2026-10-11  
> 数据来源：GitHub API（token 认证，5000 次/小时额度）  
> 检索关键词 24 组，抓取 39 个项目 README 存档（存档未随本仓库发布）

> [!NOTE]
> **勘误（2026-10-11 晚，已实测推翻本文一处判断）**
> 本文第五节曾写"`Windows-MCP` 要求英文默认语言"——**这条是错的，已实测推翻**。
> 中文（zh-CN）系统下 `Windows-MCP` 完全可用，无障碍树中的中文元素（`按钮 "开始"` 等）读取正确。
> README 那句 "English preferred" 只影响 `App` 一个工具，且官方 issue #372 已修复。
> 详见 [`windows-mcp-setup-guide.md`](./windows-mcp-setup-guide.md) §7。

---

## 一、结论速览

| 你的需求 | 首选方案 | 为什么 |
|---|---|---|
| **操作控制**（控制鼠标键盘帮你干活） | `PerryLink/dsh-click` | Windows 优先、DSH 原生插件、点击/输入/滚动/快捷键齐全，且**永不抢前台焦点** |
| **视觉能力**（不读图就认按钮） | 同一个 `dsh-click` 的 `screen_read` | 直接返回**无障碍树**（元素 id/类型/中文名称/坐标），**纯文本、零图像模型** |
| 官方后备 | DSH **官方内置 Computer Use**（实验版） | Codex `window2` 13 个方法，返回内容含 `accessibility` 字段 |
| 通用 MCP 客户端（非 DSH） | `CursorTouch/Windows-MCP`（8.6k⭐） | 生态最大、`uvx` 一键跑 |

**核心认知**：你问的"不用读图的 Windows API"就是 **Windows UI Automation（UIA）无障碍接口**——Windows 从 Vista 起内置，任何支持无障碍的应用都会把自己的按钮、输入框、菜单以"控件树"形式暴露出来。Agent 读这棵树就等于拿到了元素的**名字和ID**，不用猜像素坐标。这条路**零推理开销、不怕分辨率/DPI/主题变化**，对你那台 i5-3337U + 8GB 的老机器是最优解。

---

## 二、两条能力路线对照

### 路线 A — DeepSeek Harness 插件（你本机已装 DSH，走这条）

你工作区里已有 `DeepSeek-Harness/deepseek-harness-latest-win-x64.exe`（v0.2.0-rc.2，官方签名有效）。DSH 的核心哲学是 **"Everything is a Plugin"**（官方仓库 24.7 万 star），桌面控制在这套生态里已有现成方案。

#### A1. 官方内置 Computer Use（实验版）⚠️ 先确认

根据生态插件的兼容性说明，**DSH 官方已发布实验性 Computer Use**，工具面沿用 Codex 的 `window2` 规范，共 13 个方法：

```
list_windows  get_window  list_apps  launch_app  get_window_state
click  press_key  type_text  scroll  set_value  drag
perform_secondary_action  activate_window
```

关键点：其返回数据结构里**明确包含 `accessibility` 字段**（无障碍树），与 `window`, `screenshots`, `cacheDiagnostics` 并列。**这就是你要的"不读图识别按钮"的官方实现。**

👉 **第一步建议**：先在你装好的 DSH 里检查插件列表 / 设置页，看是否有 Computer Use 开关。有就不用装第三方了。

#### A2. 社区插件（按契合度排序）

| 项目 | ⭐ | 语言 | 平台 | 关键能力 | 备注 |
|---|---|---|---|---|---|
| **[PerryLink/dsh-click](https://github.com/PerryLink/dsh-click)** | 17 | TS | **Windows 优先** | `screen_read` 无障碍树 / `screen_shot` / click·type·scroll·key / app_launch | ⭐**首选**：纯文本模型即可用，UIA 优先，审批门控 + 新鲜度校验 + 进程身份校验 + 审计；有 [Gitee 镜像](https://gitee.com/perrylink/dsh-click) |
| [988hj7tczd-oss/dsh-computer-use](https://github.com/988hj7tczd-oss/dsh-computer-use) | 47 | JS | 跨平台 | AX/UIA 观测 + 独立**虚拟光标** + 截图视觉，12 个受控工具 | 中文文档完善；有 Gitee 镜像；虚拟光标可看见操作过程 |
| [Anionex/dsh-computer-use](https://github.com/Anionex/dsh-computer-use) | 33 | TS | 跨平台 | Accessibility 观测 + **作用域权限** | 权限模型设计较细 |
| [JohnXu22786/computer-control](https://github.com/JohnXu22786/computer-control) | 0 | Python | 跨平台 | 截图 + 指针/键盘注入 + **无障碍树语义动作** + 紧急停止 + 允许/拒绝规则 | 功能全但很新，star 少 |
| [wushi2333/dsh-computer-use_codex-style](https://github.com/wushi2333/dsh-computer-use_codex-style) | 20 | Python | Windows | 完整复刻 Codex `window2` 13 方法 + 覆盖层 Esc 中断 + 按应用审批 | 与官方插件**可共存**，但两个 driver 别同时开 |
| [Ethanout/computer-use-plus](https://github.com/Ethanout/computer-use-plus) | 2 | JS | Windows | 低 token 低延迟，**UIA/CDP/OCR 路由** | 卖点是省 token |
| [jing-hy/computer-user](https://github.com/jing-hy/computer-user) | 4 | JS | Windows | 读屏 + `SendInput` 驱动鼠标键盘 | Codex 风格 |
| [mrpulor-gh/dsh-nuphus-mcp](https://github.com/mrpulor-gh/dsh-nuphus-mcp) | 4 | JS | 跨平台 | 把 nuphus-mcp（45 工具）挂载为 DSH 原生工具 `mcp__nuphus-mcp__*` | 官方明确"DSH 用户请装这个，别装 nuphus-mcp 本体" |

#### A3. 视觉增强类（补 DSH 的"眼睛"）

| 项目 | ⭐ | 能力 |
|---|---|---|
| [ysr666/dsh-vision-router](https://github.com/ysr666/dsh-vision-router) | 1141 | 给纯文本模型的免费视觉链：问答 / grounding / 裁剪 / 像素对比 / 取色 / OCR / SVG 描摹 |
| [Anionex/dsh-vision-toolkit](https://github.com/Anionex/dsh-vision-toolkit) | 887 | OCR、grounding、多图问答、截图分析、UI 还原，输出结构化 JSON |

> 这两个是"截图→理解"路线，适合 Canvas/游戏等无 UIA 信息的界面。**有 `screen_read` 时优先用无障碍树，省 token 也更准。**

---

### 路线 B — 通用 MCP Server（WorkBuddy / Claude Desktop / Cursor 等任何 MCP 客户端）

| 项目 | ⭐ | 语言 | 技术路线 | 亮点 |
|---|---|---|---|---|
| **[CursorTouch/Windows-MCP](https://github.com/CursorTouch/Windows-MCP)** | 8639 | Python | **UIA**，不依赖任何视觉模型 | 生态最大（MCP Registry 收录，Claude Desktop 200 万用户）；`uvx windows-mcp serve` 一键起；延迟 0.2–0.5s ⚠️**要求 Windows 默认语言为英文** |
| **[sbroenne/mcp-windows](https://github.com/sbroenne/mcp-windows)** | 111 | C# | **Windows UI Automation API**，按名字操作 | "Click buttons **by name, not coordinates**"，不受 DPI/主题/分辨率/窗口位置影响；MCP + CLI 双通道；有 VS Code 扩展 |
| **[shanselman/FlaUI-MCP](https://github.com/shanselman/FlaUI-MCP)** | 103 | C# | FlaUI + UIA | Scott Hanselman（微软）出品；设计类比 Playwright：`windows_snapshot` 拿 ref → `windows_click ref="w1e5"`，**"No screenshot parsing. No coordinate guessing."** |
| [AmrDab/clawdcursor](https://github.com/AmrDab/clawdcursor) | 405 | TS | **无障碍树 + OCR 融合成 UI map** | 跨平台；按稳定 `el_NN` id 操作；**每个动作自我验证**；单一安全闸门 |
| [deploymenttheory/windows-mcp-server](https://github.com/deploymenttheory/windows-mcp-server) | 8 | Go | **UIA 无障碍树**（明确声明无需视觉模型） | 工具面最全：UIA + 模拟输入 + 截图 + PowerShell + 注册表 + 进程 + 文件 + 爬虫；带设备策略引擎 / 出网白名单 / 防篡改审计链 ⚠️ 功能强=风险大，README 自述无沙箱 |
| [mrpulor-gh/nuphus-mcp](https://github.com/mrpulor-gh/nuphus-mcp) | 322 | Rust | 45 工具，含 7 个**语义桌面（UIA）**工具 | 单二进制 stdio，无守护进程；内置本地 OCR；Chrome CDP；有 Gitee 国内镜像 |
| [AB498/computer-control-mcp](https://github.com/AB498/computer-control-mcp) | 169 | Python | PyAutoGUI + **RapidOCR** + ONNXRuntime | `uvx computer-control-mcp`；**零外部依赖**。注：你离线库里已有 RapidOCR 模型，契合度高 |
| [shuyu-labs/Windows-MCP.Net](https://github.com/shuyu-labs/Windows-MCP.Net) | 233 | C# | .NET 桌面自动化 | 中文项目，`.NET 10` + `dnx` 安装；⚠️最后更新 2025-11，偏旧 |

---

## 三、底层库（想自己造轮子时）

| 项目 | ⭐ | 说明 |
|---|---|---|
| [yinkaisheng/Python-UIAutomation-for-Windows](https://github.com/yinkaisheng/Python-UIAutomation-for-Windows) | 3586 | **Microsoft UIAutomation 的 Python 3 封装**。支持 MFC / WinForms / WPF / Metro / Qt / IE / Firefox / Chrome / Electron（需 `--force-renderer-accessibility`）。`pip install uiautomation` 后自带 `automation.py` 可遍历控件树。**这就是"不用读图识别按钮"的最底层答案。** ⚠️ 需以管理员运行 |
| [pywinauto/pywinauto](https://github.com/pywinauto/pywinauto) | 6209 | Windows GUI 自动化老牌库，基于文本属性定位控件 |

---

## 四、不推荐（本机跑不动）

这些是"截图 → 视觉大模型 → 输出坐标"路线，效果强但需要 GPU / 大显存推理，你那台 2 核 4 线程 + 8GB 的 Vostro 5460 硬扛不了：

| 项目 | ⭐ | 原因 |
|---|---|---|
| bytedance/UI-TARS-desktop | 39230 | 需 UI-TARS 专用模型（本机无 GPU） |
| microsoft/OmniParser | 25511 | 屏幕解析模型，需 GPU |
| microsoft/UFO³ | 9987 | 微软官方 Windows AgentOS，功能强，但**必须配 LLM API Key**，且是多进程重型架构 |
| trycua/cua | 29326 | 面向虚拟化车队/评测，非单机场景 |
| simular-ai/Agent-S | 12582 | 学术框架，部署成本高 |

> **排除项**：`lahfir/agent-desktop`（1783⭐，Rust）看着很合适——"sees any app's real UI structure through OS accessibility trees"，但 **README 明确写 `Requires Rust 1.89+ and macOS 13.0+`，只支持 macOS，Windows 用不了。**

---

## 五、本机适配性分析

| 维度 | 现状 | 影响 |
|---|---|---|
| CPU / 内存 | i5-3337U（2C4T）+ 8GB | **必须避开本地视觉模型**；纯 UIA 路线几乎零开销 ✅ |
| Windows 语言 | **中文系统** | ✅ 无关。UIA 类方案（含 `Windows-MCP`）直接返回**中文化控件名**，不需改系统语言（旧说法已勘误，见文首） |
| 权限 | WorkBuddy 已是管理员；UIA 枚举通常需管理员 | ✅ 满足 |
| Node 版本 | DSH 插件普遍要求 `^22.19 \|\| >=24` | DSH 桌面版**自带 Node + pnpm**，无需另装 |
| 网络 | 需访问 npm / GitHub | 多个插件提供 **Gitee 镜像**，国内可用 |
| 安全 | 验证机关闭了杀毒软件、且有远程控制软件常驻 | 🔴 **桌面控制插件 = 最高权限入口**，务必保留审批门控，别开全自动放行 |

---

## 六、建议落地顺序

1. **第 1 步**：打开已装的 DSH，查插件列表里有没有官方 Computer Use（实验版）。
2. **第 2 步**：若没有或不够用，装 `PerryLink/dsh-click`——最贴合你的两点需求，且 Windows 优先。

   ```bash
   # 官方渠道（Gitee 镜像：https://gitee.com/perrylink/dsh-click）
   npm i -g dsh1024
   dsh1024 plugin --profile web add dsh-click
   ```

3. **第 3 步**：验证两条能力——
   - 让它 `screen_read` 一个窗口（比如记事本），看能否列出按钮名称 → 验证**视觉能力**
   - 让它点击一个按钮 → 验证**操作控制**
4. **第 4 步**（可选）：需要看无法用 UIA 描述的界面（Canvas / 游戏）时，再补 `dsh-vision-router`。

---

## 附：检索记录

- 检索脚本：`tools/gh_search.py`、`tools/fetch_readmes.py`
- 原始搜索输出：`raw/search_raw*.txt`
- README 存档：`readmes/`（39 个项目）

**所有 star 数、更新时间均为 2026-10-11 实测值，会随时间变化。**
