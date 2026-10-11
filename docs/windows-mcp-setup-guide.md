# Windows-MCP 接入指南（跨机复用版）

> **本文档的读者：另一台电脑上的 WorkBuddy（AI Agent）。**
> 你的任务：把 `CursorTouch/Windows-MCP` 接入你所在的 WorkBuddy，让它获得
> **"不靠图像识别，直接读写 Windows 界面"** 的能力（读无障碍树 + 控制鼠标键盘）。
>
> 本文档由一台已经完整跑通的机器整理，**所有步骤均已实测验证**。
> 照着做即可，不需要再自己摸索。文中标注了每一步"为什么"，遇到环境差异时你可以据此自行判断。

---

## 0. 三十秒速览

| 项目 | 说明 |
|---|---|
| 目标项目 | `CursorTouch/Windows-MCP`（8.6k★，MIT，Python） |
| 它是什么 | 一个 MCP 服务，暴露 **21 个** 操作 Windows 的工具 |
| 核心价值 | `Snapshot` 返回 **UIA 无障碍树**（纯文本的元素名/坐标），**无需图像模型** |
| 中文系统 | ✅ **完全可用，无需任何额外设置**（已实测，见 §7） |
| 总步骤 | 5 步：检查环境 → 装 uv → 写配置 → **界面激活** → 验证 |
| 最大的坑 | ⚠️ **第 4 步**：WorkBuddy 不会自动监听配置文件变化，必须在界面里手动触发一次 |

---

## 1. 环境检查

先确认三件事，缺什么补什么。

### 1.1 操作系统
只用 Windows（7/8/8.1/10/11 都可以）。**不需要把系统语言改成英文。**

### 1.2 uv（Python 包管理器）
WorkBuddy 是 GUI 进程，`PATH` 里通常**不包含** `~/.local/bin`，所以后面配置里必须写**绝对路径**。

```bash
where uvx
# 期望输出类似：C:\Users\<你的用户名>\.local\bin\uvx.exe
```

如果没有，装一个（任选其一）：

- Windows PowerShell：`irm https://astral.sh/uv/install.ps1 | iex`
- 或者：`pip install uv`

装完确认版本：

```bash
uv --version
```

> 参考：验证机上是 `uv 0.13.0`。

### 1.3 Python 版本（**关键**）
当前 windows-mcp **0.8.8** 的 `requires-python = ">=3.14"`。

**你不需要手动装 Python 3.14** —— `uvx --python 3.14` 会让 uv 自动下载。
但如果你的机器上已有 Python 3.14+，它也会直接复用。

```bash
uv python list
# 能看到 cpython-3.14.x 即可（写 <download available> 也表示可用，uv 会自己拉）
```

### 1.4 网络
下载走 PyPI。国内网络建议用镜像（配置里已包含清华源）。
验证机上实测：**24 秒**下载完 Python 3.14.8 + 92 个依赖包。

---

## 2. 写配置文件

### 2.1 文件位置

```
%USERPROFILE%\.workbuddy\mcp.json
```

在 Windows 上通常就是：

```
C:\Users\<你的用户名>\.workbuddy\mcp.json
```

> ⚠️ **两个易错点**
> 1. 是 `.workbuddy`（**没有**前面的点），**不是** `~/.codebuddy/.mcp.json`。
>    `~/.codebuddy/.mcp.json` 是 **CodeBuddy CLI** 的配置文件，**桌面版 WorkBuddy 不读它**。
> 2. 文件名是 `mcp.json`，**不是** `.mcp.json`。

### 2.2 配置内容

把下面这段合并进 `mcpServers`。
**如果文件已存在、里面已有别的服务，请保留原有条目，只新增 `windows-mcp` 这一项 —— 不要整个覆盖。**

```json
{
  "mcpServers": {
    "windows-mcp": {
      "type": "stdio",
      "command": "C:\\Users\\<你的用户名>\\.local\\bin\\uvx.exe",
      "args": ["--python", "3.14", "windows-mcp", "serve"],
      "env": {
        "UV_DEFAULT_INDEX": "https://pypi.tuna.tsinghua.edu.cn/simple",
        "ANONYMIZED_TELEMETRY": "false",
        "WINDOWS_MCP_SCREENSHOT_SCALE": "0.5",
        "WINDOWS_MCP_DISABLE_FLASH": "1"
      },
      "description": "Windows 桌面自动化：UI 无障碍树读取 + 鼠标键盘操作"
    }
  }
}
```

### 2.3 每个字段为什么这么写（改动前请先读）

| 字段 | 原因 | 能不能改 |
|---|---|---|
| `command` 用**绝对路径** | WorkBuddy 是 GUI 进程，`PATH` 不含 `~/.local/bin`，写 `uvx` 会"命令找不到" | **必须**绝对路径 |
| `--python 3.14` | 0.8.8 要求 Python ≥3.14；显式指定让 uv 自己拉，避免本机版本不够 | 若本机已有 3.15+，可改成对应版本 |
| `UV_DEFAULT_INDEX` 清华源 | 国内网络加速。**海外机器可删掉这行** | 可删 |
| `SCREENSHOT_SCALE: 0.5` | 1920×1080 截图缩一半，避免结果体积超限。主路线是文本树，不靠截图 | 4K 屏建议保持 0.5 |
| `DISABLE_FLASH` | 关掉截图后那圈橙色闪烁边框，不干扰桌面 | 可删 |
| `ANONYMIZED_TELEMETRY` | 关遥测 | 可删 |
| `type: stdio` | 官方文档说可选，但 WorkBuddy 内置插件都显式写，加上更保险 | 可删 |

### 2.4 如果机器需要代理
上面配置在直连 + 清华源的情况下已验证可行。若你的网络必须走代理，在 `env` 里补：

```json
"HTTPS_PROXY": "http://127.0.0.1:7890",
"HTTP_PROXY": "http://127.0.0.1:7890"
```

（端口按你的代理工具实际配置改。）

---

## 3. 预拉取（可选，但强烈建议）

先手动把包拉一遍，这样后面界面激活时是秒连，不会因为下载超时而失败。

```bash
set UV_DEFAULT_INDEX=https://pypi.tuna.tsinghua.edu.cn/simple
"C:\Users\<你的用户名>\.local\bin\uvx.exe" --python 3.14 windows-mcp --help
```

**期望输出**（说明服务本体可用了）：

```
Usage: windows-mcp [OPTIONS] COMMAND [ARGS]...

  Windows-MCP: MCP server for Windows desktop automation.

Commands:
  auth       Generate an auth key ...
  install    Install windows-mcp as a scheduled task ...
  serve
  uninstall  Remove the windows-mcp scheduled task ...
```

> 首次运行会看到一串 `Downloading ...`，属正常。

---

## 4. 在 WorkBuddy 界面里激活 ⚠️ **最容易卡住的一步**

### 4.1 为什么必须手动激活

**WorkBuddy 不会实时监听 `mcp.json` 的文件变化。**

验证机上的实证：WorkBuddy 进程 14:12 启动，配置文件 20:05 才写入 ——
它的连接器状态文件里 `connectors` 始终是空的，日志里也**没有任何加载记录**。
所以直接改文件后，界面里**看不到**新服务。

### 4.2 操作路径

```
① 左侧边栏 → 「专家·技能·连接器」→ 选「连接器」
② 页面右上角 → 点「自定义连接器」→ 打开「MCP 服务管理」
③ 点击「配置 MCP」按钮  ← 关键！它会打开 mcp.json 编辑器
④ 在编辑器里确认内容无误 → 点「保存」   ← 这一步才会触发重新加载
⑤ 列表中出现 windows-mcp → 点「信任」
```

> **注意**：第 ② 步打开的那个列表，显示的是**内存中已加载的服务**。
> 如果里面只有一个内置的 `miora`，那是正常的 —— `miora` 是随插件包自带的，天然就在。

### 4.3 如果列表里还是不出现

**完全退出 WorkBuddy 再重新打开**（要退到托盘图标也消失，不是只关窗口）。
重启后 WorkBuddy 一定会重新扫描 `mcp.json`。

### 4.4 首次连接会比较慢

验证机日志：

```
12:56:48  wb:mcp:setEnabled   custom-mcp:windows-mcp
12:56:48  wb:mcp:connect      custom-mcp:windows-mcp
12:57:15  stdio-connected     pid=10572, elapsedMs=27391
12:57:16  end #169 wb:mcp:connect elapsedMs=27780   ← 会有 VERY_SLOW 警告
```

**27.4 秒属于正常**（uv 在拉 Python）。那条 `VERY_SLOW` 警告不影响功能。
如果已经做了 §3 的预拉取，这里会快得多。

---

## 5. 验证是否成功

### 5.1 方法一：直接调用工具（推荐）

激活并信任后，WorkBuddy 里会出现 `mcp__windows-mcp__*` 系列工具。直接调用：

```
调用 DisplayInventory（无参数）
→ 期望返回显示器分辨率、DPI、缩放比
```

```
调用 Snapshot，参数 use_vision = false
→ 期望返回一大段纯文本，包含光标位置、焦点窗口、任务栏按钮名称
```

**关键：确认返回的是"文字"而不是"图片"。** 这才是"不读图"的证据。

### 5.2 方法二：跑独立探针（不依赖 WorkBuddy 界面）

把下面的脚本存成 `mcp_probe.py`，用任意 Python 3 运行。
它会自己拉起服务、列出工具、并实测读一次界面：

```python
# -*- coding: utf-8 -*-
"""Windows-MCP 连通性探针（通用版）"""
import json, os, shutil, subprocess, sys, time

def find_uvx():
    c = shutil.which("uvx") or shutil.which("uvx.exe")
    if c: return c
    home = os.path.expanduser("~")
    for p in [os.path.join(home, ".local", "bin", "uvx.exe"),
              os.path.join(home, ".local", "bin", "uvx"),
              os.path.join(os.environ.get("LOCALAPPDATA",""), "Programs","uv","uvx.exe")]:
        if p and os.path.isfile(p): return p
    return ""

UVX = find_uvx()
if not UVX:
    print("[FAIL] 找不到 uvx，请先安装 uv"); sys.exit(1)
print("[OK] uvx =", UVX)

env = dict(os.environ)
env.setdefault("UV_DEFAULT_INDEX", "https://pypi.tuna.tsinghua.edu.cn/simple")
env["PYTHONIOENCODING"] = "utf-8"

proc = subprocess.Popen([UVX, "--python", "3.14", "windows-mcp", "serve"],
                        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE, env=env)

def send(o): proc.stdin.write((json.dumps(o)+"\n").encode()); proc.stdin.flush()
def read_msg(t=120):
    end = time.time()+t
    while time.time() < end:
        ln = proc.stdout.readline()
        if not ln: time.sleep(0.05); continue
        s = ln.decode("utf-8","replace").strip()
        if not s: continue
        try: return json.loads(s)
        except Exception: continue
    return None

send({"jsonrpc":"2.0","id":1,"method":"initialize","params":{
    "protocolVersion":"2025-06-18","capabilities":{},
    "clientInfo":{"name":"probe","version":"1.0"}}})
r = read_msg()
if not r:
    print("[FAIL]", proc.stderr.read().decode("utf-8","replace")[:2000]); sys.exit(1)
print("[OK] serverInfo =", json.dumps((r.get("result") or {}).get("serverInfo"), ensure_ascii=False))

send({"jsonrpc":"2.0","method":"notifications/initialized","params":{}})
send({"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}})
tools = ((read_msg() or {}).get("result") or {}).get("tools") or []
print("[OK] 工具数 =", len(tools))
for t in tools: print("     -", t.get("name"))

send({"jsonrpc":"2.0","id":3,"method":"tools/call",
      "params":{"name":"Snapshot","arguments":{}}})
r = read_msg(180)
if r and "result" in r:
    for c in (r["result"].get("content") or []):
        if c.get("type") == "text":
            print("[OK] Snapshot 前 1200 字符：")
            print((c.get("text") or "")[:1200]); break
else:
    print("[FAIL]", json.dumps(r, ensure_ascii=False)[:800])

proc.terminate()
```

**期望输出**（能看到中文按钮名就说明一切正常）：

```
[OK] serverInfo = {"name": "windows-mcp", "version": "4.1.0"}
[OK] 工具数 = 21
     - ControlStatus / App / DisplayInventory / PowerShell / FileSystem / Snapshot ...
[OK] Snapshot 前 1200 字符：
     Cursor Position: (158, 454)
     ...
     ├── window "任务栏"
     │   └── 窗格 "任务栏"
     │       ├── (24,1060) 按钮 "开始"  [action: click]
     │       ├── (123,1060) 按钮 "文件资源管理器"  [action: click]
```

### 5.3 方法三：验证"真的能控制"（读 / 操作 / 再读 闭环）

```
① Snapshot                        → 记下 Cursor Position，例如 (158, 454)
② Move(loc=[960, 540])            → 鼠标应真的移到屏幕中央
③ Move(loc=[158, 454])            → 移回原位
④ Snapshot                        → 光标应回到 (158, 454)  → 闭环成立
```

> 验证机上这四步全部通过。这是"能控制电脑"最直接的证据。

---

## 6. 全部踩坑清单（照这个避雷）

| # | 坑 | 现象 | 解决 |
|---|---|---|---|
| 1 | **界面里找不到新服务** | 配好了但列表里只有 `miora` | **必须**走 §4.2：点「配置 MCP」→ 保存；不行就重启 WorkBuddy |
| 2 | **配置位置写错** | 一直不生效 | 桌面版是 `~/.workbuddy/mcp.json`；`~/.codebuddy/.mcp.json` 是 CLI 的，别混 |
| 3 | **`command` 写了 `uvx`** | 报"命令找不到" | GUI 进程 PATH 不含 `.local/bin`，**必须写绝对路径** |
| 4 | **Python 版本不够** | 装不上 / 报版本不满足 | 0.8.8 要求 ≥3.14，用 `uvx --python 3.14` 让 uv 自拉 |
| 5 | **下载太慢或超时** | 卡在 Downloading | 配 `UV_DEFAULT_INDEX` 清华源 |
| 6 | **误以为要英文系统** | 不敢在中文系统上用 | ❌ **不用改语言**，中文实测完全可用（见 §7） |
| 7 | **`Move` 传了 `duration`** | 报 `from_loc and duration require drag=True` | 平滑移动只能配合 `drag=True` 用 |
| 8 | **`Notification` 调不动** | 报参数错误 | 该工具 **必填 `app_id`（有效 AUMID）**，不是可选 |
| 9 | **调用被拒绝** | 返回 `USER_CONTROL` 或 `CONTROL_PREEMPTED` | 这是**保护机制不是故障**，见 §8 |
| 10 | **首次连接有 `VERY_SLOW` 警告** | 日志里 27 秒 | 正常，属于首次拉依赖 |

---

## 7. 关于"只支持英文系统"的澄清

原始 README 里有这句话：

> `English` as the default language in Windows preferred else disable the `App-Tool` ...

**这已经过时了，而且影响面极小：**

- 历史上**只有 `App`（按开始菜单名启动应用）这一个工具**受影响，其余 20 个与系统语言无关；
- 官方 **issue #372 已修复**，仓库里有测试文件 `tests/test_app_launch_localized.py`，明确断言
  `launch_app("记事本")` 和 `launch_app("Notepad")` **都能成功**；
- 修复方式：同时枚举 `Get-StartApps`（英文名）和 AppsFolder 目录（本地化名），两份清单合并匹配。

**验证机实测**（系统 `zh-CN`，`locale = zh_CN / cp936`）：
`Snapshot` 正确读出 `按钮 "开始"`、`按钮 "文件资源管理器"`、`窗口 "设置"`、`任务栏` 等中文元素。

> **结论：中文系统不需要做任何设置。**

---

## 8. 安全机制说明（**别把它当故障**）

Windows-MCP 内置了"用户接管保护"，实测行为：

```json
{"code": "USER_CONTROL",      "status": {"state": "user", "wait_seconds": 9.92}}
{"code": "CONTROL_PREEMPTED", "status": {"state": "unavailable"}}
```

空闲后 `ControlStatus` 会回报：

```json
{"state": "ai", "generation": 2, "wait_seconds": 0.0}
```

**含义：用户一旦碰鼠标或键盘，Agent 的控制权立刻交还；需要用户空闲约 10 秒才能重新接管。**
`ControlStatus` 可以随时查询当前是谁在掌控（`ai` / `user`）。

---

## 9. 21 个工具清单

```
ControlStatus    App              DisplayInventory   PowerShell
FileSystem       Snapshot         Screenshot         Click
Type             Scroll           Move               Shortcut
Wait             WaitFor          Scrape             MultiSelect
MultiEdit        Clipboard        Process            Notification
Registry
```

**按用途归类：**

- **视觉（不读图）**：`Snapshot`（核心，返回无障碍树）、`Screenshot`（截图，可选）、
  `DisplayInventory`（多屏/DPI）、`WaitFor`（轮询等待元素出现）
- **操作控制**：`Click`、`Type`、`Scroll`、`Move`、`Shortcut`、`MultiSelect`、`MultiEdit`、
  `Clipboard`、`App`（启停/切换窗口）
- **系统级**：`PowerShell`、`FileSystem`、`Registry`、`Process`、`Notification`、`Scrape`

---

## 10. ⚠️ 安全加固建议（**必读**）

这 21 个工具合起来等于**整台电脑的完全控制权**，其中 `PowerShell` / `Registry` / `FileSystem`
属于最高危级别。如果这台机器上还关着杀软、或者有远程控制软件常驻，风险会成倍放大。

**三档方案，按需选择：**

**① 最保守（只保留"看 + 点"）**
```json
"args": ["--python", "3.14", "windows-mcp", "serve",
         "--tools", "Snapshot,Screenshot,DisplayInventory,Click,Type,Scroll,Move,Shortcut,Wait,WaitFor,ControlStatus"]
```

**② 中等（去掉文件/注册表/命令执行）**
```json
"args": ["--python", "3.14", "windows-mcp", "serve",
         "--exclude-tools", "PowerShell,Registry,FileSystem"]
```

**③ 全功能（默认，测试阶段）**

> 另外两个常被用到的加固开关：
> - `WINDOWS_MCP_EXCLUDE_PROCESSES`：把某些进程排除在 UIA 遍历之外（它们无障碍树有问题时会拖慢 Snapshot）
>   例：`"WINDOWS_MCP_EXCLUDE_PROCESSES": "Code.exe,Cursor.exe"`
> - `WINDOWS_MCP_SCREENSHOT_BACKEND`：截图后端。默认 `auto`（dxcam→mss→pillow），
>   老显卡截图全黑时可设成 `"mss"`。

---

## 11. 附录：配置文件参考（已验证版本）

以下是验证机上实际生效的完整配置，可直接参考：

```json
{
  "mcpServers": {
    "windows-mcp": {
      "type": "stdio",
      "command": "C:\\Users\\<你的用户名>\\.local\\bin\\uvx.exe",
      "args": ["--python", "3.14", "windows-mcp", "serve"],
      "env": {
        "UV_DEFAULT_INDEX": "https://pypi.tuna.tsinghua.edu.cn/simple",
        "ANONYMIZED_TELEMETRY": "false",
        "WINDOWS_MCP_SCREENSHOT_SCALE": "0.5",
        "WINDOWS_MCP_DISABLE_FLASH": "1"
      },
      "description": "Windows 桌面自动化：UI 无障碍树读取 + 鼠标键盘操作"
    }
  }
}
```

---

## 12. 完成自检清单

照着打勾，全绿就算成功：

- [ ] `where uvx` 能找到，或 `~/.local/bin/uvx.exe` 存在
- [ ] `uv --version` 正常
- [ ] `uv python list` 里有 3.14+
- [ ] `~/.workbuddy/mcp.json` 已写入，JSON 语法合法
- [ ] `command` 写的是**绝对路径**
- [ ] 界面里走了「配置 MCP → 保存」，或重启过 WorkBuddy
- [ ] 连接器列表里出现 `windows-mcp` 且已点「信任」
- [ ] 调用 `Snapshot(use_vision=false)` **返回文字**（含中文按钮名）
- [ ] `Move` 能让鼠标真的移动，且能移回
- [ ] 理解 `USER_CONTROL` 是保护机制而不是报错

---

*本文档基于 2026-10-11 在 Windows 10 LTSC 2021（zh-CN）上的完整实测整理。*
*项目地址：https://github.com/CursorTouch/Windows-MCP*
