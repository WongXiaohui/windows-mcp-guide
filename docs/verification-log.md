# Windows-MCP 接入 WorkBuddy 说明

> 调研对象：`CursorTouch/Windows-MCP`（8.6k★，MIT，Python）
> 实测机器：Dell Vostro 5460 / Win10 LTSC 2021 / **zh-CN 简体中文系统**
> 实测日期：2026-10-11 ｜ 实测版本：windows-mcp **0.8.8**（serverInfo 报 4.1.0）

---

## 一、结论（三句话）

1. **能用** —— 已在 WorkBuddy 里配置好，走标准 MCP stdio 通道。
2. **中文系统完全没问题** —— 已实测通关，中文界面元素读取正确。
3. **README 里"推荐英文系统"是过时说法** —— 历史上确有坑，官方已修复。

---

## 二、中文系统实测记录（关键证据）

实测环境：`GetUserDefaultUILanguage() = 0x0804 (zh-CN)`，`locale = zh_CN / cp936`。

以 MCP 客户端身份实际拉起服务并调用工具，结果：

| 测试项 | 结果 |
|---|---|
| `initialize` | ✅ 成功，protocolVersion `2025-06-18` |
| `tools/list` | ✅ 返回 **21 个工具** |
| `DisplayInventory` | ✅ 正确读出 1920x1080 / DPI 96 / scale 1.0 |
| **`Snapshot`（UIA 无障碍树）** | ✅ **成功遍历，中文元素全部正确识别** |

`Snapshot` 实际返回的片段（原样摘录）：

```
    Opened Windows:
    Name      Depth  Status      Width    Height    Handle
------  -------  --------  -------  --------  --------
设置            5  Normal        816       641    131634

    UI Tree:
    desktop
    ├── window "WorkBuddy"
    ├── window "任务栏"
    │   └── 窗格 "任务栏"
    │       ├── (24,1060) 按钮 "开始"  [action: click]
    │       ├── (72,1060) 按钮 "在此键入进行搜索"  [action: click]
    │       ├── 工具栏 "运行中的应用程序"
    │       │   ├── (123,1060) 按钮 "文件资源管理器"  [action: click]
    │       │   ├── (172,1060) 按钮 "Microsoft Edge"  [action: click]
    │       │   └── (221,1060) 按钮 "WorkBuddy - 1 个运行窗口"  [action: click]
    │       ├── (1652,1060) 按钮 "通知 V 形"  [action: click]
    │       └── 工具栏 "用户提示通知区域"
    │           └── (1676,1060) 按钮 "未检测到电池"  [action: click]
```

> 注意 `按钮 "开始"` / `按钮 "文件资源管理器"` / `窗口 "设置"` 这类**中文名称是被直接读出来的**——
> 因为走的是 UIA 无障碍树（读控件 Name 属性，由应用自己提供的本地化字符串），
> **与系统显示语言无关，也与截图/OCR 无关**。

原始日志：`raw/mcp_probe_result.txt` ｜ 探针脚本：`tools/mcp_probe.py`

---

## 三、"只支持英文"的来龙去脉

README 第 96 行的原文是：

> `English` as the default language in Windows preferred else disable the `App-Tool` in the MCP Server for Windows with other languages.

**真实影响面很小，且只在 `App` 这一个工具上：**

| 工具 | 是否受系统语言影响 |
|---|---|
| `Snapshot` / `Screenshot` / `Click` / `Type` / `Scroll` / `Move` / `Shortcut` | ❌ 不受影响 |
| `PowerShell` / `FileSystem` / `Registry` / `Process` / `Clipboard` | ❌ 不受影响 |
| **`App`（按开始菜单名启动应用）** | ⚠️ 历史上只认英文名，现已修复 |

相关 issue 时间线：

| Issue | 标题 | 状态 |
|---|---|---|
| #32 | 改进 Launch/Resize 工具的中文应用名支持 | ✅ 已合并（2025-08） |
| #18 | 中文环境下设英文默认语言会有问题 | ✅ 已关闭（2025-08） |
| #147 | 非 ASCII 元素导致 Snapshot 崩溃（`ord()` TypeError） | ✅ 已修（2026-03） |
| **#372** | **`App` 工具无法按中文开始菜单名启动应用** | ✅ 已关闭（2026-09-01） |
| #41 | 中文版 Win11 双屏下读不到文本 | ✅ 已关闭（多屏支持已补齐） |

官方现已带测试用例 `tests/test_app_launch_localized.py`，明确断言：

```python
assert desktop.launch_app("Notepad") == ("", 0, 0)
assert desktop.launch_app("记事本") == ("", 0, 0)   # ← 中文名同样可启动
```

实现方式：同时枚举 `Get-StartApps`（英文名）与 AppsFolder 目录（本地化名），两者合并匹配。

**结论：现在的中文系统不需要做任何额外设置。**

---

## 四、WorkBuddy 接入方式（已配置好）

配置文件：`C:\Users\<你的用户名>\.workbuddy\mcp.json`

```json
{
  "mcpServers": {
    "windows-mcp": {
      "command": "C:\\Users\\<你的用户名>\\.local\\bin\\uvx.exe",
      "args": ["--python", "3.14", "windows-mcp", "serve"],
      "env": {
        "UV_DEFAULT_INDEX": "https://pypi.tuna.tsinghua.edu.cn/simple",
        "ANONYMIZED_TELEMETRY": "false",
        "WINDOWS_MCP_SCREENSHOT_SCALE": "0.5",
        "WINDOWS_MCP_DISABLE_FLASH": "1"
      }
    }
  }
}
```

### 关键设计说明

| 配置项 | 为什么这么写 |
|---|---|
| **绝对路径 `uvx.exe`** | WorkBuddy 是 GUI 进程，PATH 通常不含 `~/.local/bin`，写绝对路径才不会"命令找不到" |
| `--python 3.14` | 0.8.8 的 `requires-python = ">=3.14"`；本机 managed Python 只有 3.13，**必须让 uv 自己拉 3.14** |
| `UV_DEFAULT_INDEX` 清华源 | 首次安装实测 **24 秒拉完 92 个包**，不走镜像会很难受 |
| `SCREENSHOT_SCALE=0.5` | 1920x1080 截图缩一半，避免超出 MCP 结果体积上限；**主路线是 UIA 文本，不靠截图** |
| `DISABLE_FLASH=1` | 关掉截图后那圈橙色闪烁边框，不干扰你的桌面 |
| `ANONYMIZED_TELEMETRY=false` | 关遥测 |

### 激活步骤

1. 打开 WorkBuddy **连接器管理**页面
2. 点右上角的**自定义连接器**入口
3. 找到新出现的 `windows-mcp`，点**「信任」**
4. 信任后这 21 个工具才会对会话可见

> ⚠️ 配置写好**不会自动生效**，必须手动点一次"信任"。

---

## 五、21 个工具清单

```
ControlStatus    App              DisplayInventory   PowerShell
FileSystem       Snapshot         Screenshot         Click
Type             Scroll           Move               Shortcut
Wait             WaitFor          Scrape             MultiSelect
MultiEdit        Clipboard        Process            Notification
Registry
```

按你的两个诉求归类：

**① 操作控制（鼠标键盘）**
`Click`（坐标点击）、`Type`（输入文本）、`Scroll`、`Move`（移动/拖拽）、`Shortcut`（快捷键）、
`MultiSelect` / `MultiEdit`（批量选/批量填）、`Clipboard`、`App`（启停/切换窗口）

**② 视觉能力（不读图）**
`Snapshot` —— **核心**，返回完整无障碍树（元素 id / 类型 / 中文名称 / 坐标 / 可滚动区域）
`Screenshot` —— 截图补充（可选视觉模型，你不给也行）
`DisplayInventory` —— 多显示器布局、DPI、缩放
`WaitFor` —— 轮询等待某文本/窗口/元素出现

**③ 附加能力**（超出你原始需求，但很实用）
`PowerShell`、`FileSystem`、`Registry`、`Process`、`Notification`、`Scrape`

---

## 六、⚠️ 安全提醒

**这 21 个工具 = 整台机器的完全控制权**，其中 `PowerShell` / `Registry` / `FileSystem` 属于最高危级别。

**风险放大效应**：如果这台机器上关着杀毒软件、或者有远程控制软件常驻自启，
把整机控制权交给一个 Agent 的风险会成倍放大（验证机当时正属于这种状态，所以格外谨慎）。

**建议：**
1. 首次使用**逐个功能试**，不要一上来就放任自动执行
2. 权限过宽时可精简 —— 在 `args` 里加 `--exclude-tools`：
   ```json
   "args": ["--python", "3.14", "windows-mcp", "serve",
            "--exclude-tools", "PowerShell,Registry,FileSystem"]
   ```
3. 本机已装 `uvx` 缓存，服务启动很快；若长期不用可从连接器里禁用

---

## 七、故障排查

| 现象 | 原因与处理 |
|---|---|
| 连接器里看不到 `windows-mcp` | 检查 `mcp.json` 的 JSON 语法（逗号、引号） |
| 报 "command not found: uvx" | 确认 `C:\Users\<你的用户名>\.local\bin\uvx.exe` 存在 |
| 首次调用特别慢 | uv 在拉 Python 3.14 + 依赖，等 30 秒即可，之后走缓存 |
| 截图全黑 | 老旧集显上 `dxcam` 可能异常，加 `"WINDOWS_MCP_SCREENSHOT_BACKEND": "mss"` |
| `Snapshot` 卡住 | 某个应用的 UIA 提供程序有问题，用 `WINDOWS_MCP_EXCLUDE_PROCESSES` 排除它 |
| 拉包超时 | 确认 `UV_DEFAULT_INDEX` 环境变量已生效 |

---

## 八、和 DSH 方案的关系（你已选择不走）

| | Windows-MCP（本方案） | DSH 插件（`dsh-click`） |
|---|---|---|
| 生态 | **WorkBuddy / Claude / Cursor 通用 MCP** | 仅 DeepSeek Harness |
| 语言 | 中文实测可用 | 中文可用 |
| 交互 | **会抢占鼠标键盘**（`ControlStatus` 可交还控制） | UIA invoke 优先，**不抢前台焦点** |
| 定位 | 功能全、生态大、8.6k★ | 更克制、更安全 |

> 取舍：Windows-MCP 工具更全、生态更硬，但**操作时会真的动你的鼠标**；
> 若后续觉得干扰，可再考虑 `dsh-click` 那种"不抢焦点"的实现。

---

## 九、接入后的端到端实测记录（2026-10-11 21:00）

### 9.1 接入确认（WorkBuddy 日志实证）

```
12:56:48  wb:mcp:setEnabled   arg="custom-mcp:windows-mcp"
12:56:48  wb:mcp:connect      arg="custom-mcp:windows-mcp"
12:57:15  [MCP-AuthDiag] stdio-connected {"pid":10572,"elapsedMs":27391}
12:57:16  [MethodCh] end #169 wb:mcp:connect elapsedMs=27780
```

> 首次连接耗时 **27.4 秒**（uv 在拉 Python 3.14）；之后走缓存会快很多。
> 日志里那条 `VERY_SLOW` 警告属正常，不影响功能。

### 9.2 只读验证 —— **全程零图像识别**

调用 `Snapshot(use_vision=false, use_ui_tree=true)`，返回的是**纯文本无障碍树**：

```
Cursor Position: (158, 454)
Visible Displays: 0:\\.\DISPLAY1 (0,0,1920,1080) primary

Focused Window:  WorkBuddy   (Maximized 1936x1056)
Opened Windows:  设置        (Normal 816x641)

UI Tree:
desktop
├── window "WorkBuddy"
├── window "任务栏"
│   └── 窗格 "任务栏"
│       ├── (24,1060)   按钮 "开始"
│       ├── (123,1060)  按钮 "文件资源管理器"
│       ├── (1676,1060) 按钮 "未检测到电池"
│       ├── (1700,1060) 按钮 "CMCC Internet 访问"
│       ├── (1724,1060) 按钮 "2481W: 静音"
│       ├── (1776,1060) 按钮 "任务栏输入指示 - 中文(简体，中国)"
│       └── (1830,1060) 按钮 "系统时钟, 21:00, 2026/10/11"
...
```

**没有传任何截图给模型**，界面结构完全来自 UIA 无障碍树。

### 9.3 写操作验证 —— 读 / 操作 / 再读 闭环

| 步骤 | 调用 | 结果 |
|---|---|---|
| ① 读 | `Snapshot` | 光标 `(158, 454)` |
| ② 操作 | `Move(loc=[960, 540])` | `Moved the mouse pointer to (960,540).` |
| ③ 回位 | `Move(loc=[158, 454])` | `Moved the mouse pointer to (158,454).` |
| ④ 复读 | `Snapshot` | 光标 `(158, 454)` ✅ 闭环成立 |

### 9.4 安全机制实测 —— 用户接管保护有效

实测中触发了两种保护返回：

```json
{"code": "USER_CONTROL",      "status": {"state": "user", "wait_seconds": 9.92}}
{"code": "CONTROL_PREEMPTED", "status": {"state": "unavailable"}}
```

空闲后 `ControlStatus` 回报：

```json
{"state": "ai", "generation": 2, "wait_seconds": 0.0}
```

**结论：只要你一动鼠标或键盘，Agent 的控制权就立刻交还，需要你空闲约 10 秒才能重新接管。**

### 9.5 实测踩到的两个坑

| 现象 | 原因 |
|---|---|
| `Move` 传 `duration` 报错 `from_loc and duration require drag=True` | 平滑移动参数只能配合拖拽使用 |
| `Notification` 无法调用 | 该工具**必填 `app_id`（有效 AUMID）**，不是可选参数 |

