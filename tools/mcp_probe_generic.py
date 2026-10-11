# -*- coding: utf-8 -*-
"""Windows-MCP 连通性探针（通用版，跨机器可用）

用途：在不依赖 WorkBuddy 界面的情况下，独立验证 Windows-MCP 能否在这台机器上跑起来。
      它会自己拉起 MCP 服务、列出工具、并实测读取一次 UI 无障碍树。

用法：
    python mcp_probe.py

依赖：标准库即可（不需要额外安装任何包）。
"""

import json
import os
import shutil
import subprocess
import sys
import time

# ---------------------------------------------------------------- 定位 uvx
def find_uvx() -> str:
    """按优先级查找 uvx.exe / uvx。"""
    candidates = []

    # 1) PATH
    found = shutil.which("uvx") or shutil.which("uvx.exe")
    if found:
        candidates.append(found)

    # 2) 常见安装位置
    home = os.path.expanduser("~")
    candidates += [
        os.path.join(home, ".local", "bin", "uvx.exe"),
        os.path.join(home, ".local", "bin", "uvx"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "uv", "uvx.exe"),
        os.path.join(os.environ.get("USERPROFILE", ""), ".cargo", "bin", "uvx.exe"),
    ]

    for c in candidates:
        if c and os.path.isfile(c):
            return c
    return ""


UVX = find_uvx()
if not UVX:
    print("[FAIL] 找不到 uvx。请先安装 uv：")
    print("       https://docs.astral.sh/uv/getting-started/installation/")
    print("       Windows PowerShell: irm https://astral.sh/uv/install.ps1 | iex")
    sys.exit(1)

print("[OK] uvx = %s" % UVX)

# ---------------------------------------------------------------- 启动服务
env = dict(os.environ)
# 国内网络建议使用镜像，海外可删掉这一行
env.setdefault("UV_DEFAULT_INDEX", "https://pypi.tuna.tsinghua.edu.cn/simple")
env["PYTHONIOENCODING"] = "utf-8"
env["ANONYMIZED_TELEMETRY"] = "false"

print("[..] 正在拉起 windows-mcp（首次会下载 Python 3.14 + 依赖，约 25~60 秒）...")
proc = subprocess.Popen(
    [UVX, "--python", "3.14", "windows-mcp", "serve"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    env=env,
)


def send(obj):
    proc.stdin.write((json.dumps(obj) + "\n").encode("utf-8"))
    proc.stdin.flush()


def read_msg(timeout=120):
    deadline = time.time() + timeout
    while time.time() < deadline:
        line = proc.stdout.readline()
        if not line:
            time.sleep(0.05)
            continue
        s = line.decode("utf-8", "replace").strip()
        if not s:
            continue
        try:
            return json.loads(s)
        except Exception:
            continue
    return None


# ---------------------------------------------------------------- 握手
send({
    "jsonrpc": "2.0", "id": 1, "method": "initialize",
    "params": {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {"name": "probe", "version": "1.0"},
    },
})
r = read_msg()
if not r:
    print("[FAIL] initialize 无响应。stderr 如下：")
    print(proc.stderr.read().decode("utf-8", "replace")[:3000])
    sys.exit(1)

si = (r.get("result") or {}).get("serverInfo") or {}
print("[OK] initialize 成功  serverInfo = %s" % json.dumps(si, ensure_ascii=False))

send({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})

# ---------------------------------------------------------------- 工具清单
send({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
r = read_msg()
tools = ((r or {}).get("result") or {}).get("tools") or []
print("[OK] 工具清单：共 %d 个" % len(tools))
for t in tools:
    print("     - %s" % t.get("name"))

# ---------------------------------------------------------------- 实测读 UI
print("\n[..] 实测 Snapshot（遍历 UIA 无障碍树）...")
send({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
      "params": {"name": "Snapshot", "arguments": {}}})
r = read_msg(timeout=180)
if r and "result" in r:
    for c in (r["result"].get("content") or []):
        if c.get("type") == "text":
            txt = c.get("text") or ""
            print("[OK] Snapshot 成功，返回 %d 字符。前 1200 字符：" % len(txt))
            print(txt[:1200])
            break
else:
    print("[FAIL] Snapshot 失败：%s" % json.dumps(r, ensure_ascii=False)[:1000])

proc.terminate()
print("\n探针结束。若上面能看到中文按钮名称，说明一切正常。")
