# py-spy MCP Server

一个基于 [Model Context Protocol (MCP)](https://modelcontextprotocol.io) 的服务器，通过 [py-spy](https://github.com/benfred/py-spy) 提供 Python 性能测试工具。

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-2ea44f)
![tests passing](https://img.shields.io/badge/tests-passing-brightgreen)

🌐 [English](README.md) | 简体中文

**在对话中完成 Python 性能分析。** 采样运行中的进程、生成火焰图、抓取调用栈、对比多次采样 —— 全部通过 MCP 完成。

## 功能特性

- **支持 PID 或命令启动分析** —— 既可以采样正在运行的 Python 进程，也可以直接启动一个新进程进行分析。
- **`record_profile`** —— 以多种格式生成采样报告：
  - `speedscope`（可交互的 JSON）
  - `flamegraph`（自包含 SVG 火焰图）
  - `raw`（栈计数文本）
  - `chrometrace`（Chrome DevTools 时间线 JSON）
- **`dump_stacks`** —— 抓取目标进程当前的 Python 调用栈，支持 JSON 或纯文本输出。
- **`list_python_processes`** —— 列出本机正在运行的 Python 进程，方便选择分析目标。
- **`analyze_profile`** —— 解析已有的采样文件并返回热点函数。
- **`compare_profiles`** —— 对比两份 speedscope 采样报告，展示占比变化。
- **`top_profile`** —— 运行一段短时间的 `py-spy top` 并返回汇总结果。
  - 在 Windows 上，`py-spy top` 无法通过管道捕获输出，因此该工具会回退为短时 `record --format raw`，并返回热点函数表。
- **低开销采样** —— 由 [py-spy](https://github.com/benfred/py-spy) 驱动，通过读取进程内存完成采样，不会修改或侵入目标进程。
- **跨平台** —— 支持 Linux、macOS 和 Windows（需满足操作系统权限要求）。
- **本地源码友好** —— 开发期间会自动优先使用本地 Rust 源码构建的 `py-spy` 二进制（位于 `src/pyspy/`）。
- **可选的 Native/C 扩展分析** —— 在支持的平台可开启 `--native` 采样 C/C++/Cython 扩展栈。
- **GIL 与空闲线程过滤** —— 可聚焦活跃线程或仅看持有 GIL 的线程。

## 从 PyPI 安装

使用 `pip`：

```bash
pip install pyspy-mcp
```

使用 `uv`：

```bash
uv pip install pyspy-mcp
# 或以全局工具方式安装
uv tool install pyspy-mcp
```

这会自动安装适合你当前平台的 `py-spy` 二进制 wheel。

## 在 Claude Desktop / Claude Code 中使用

将该服务器作为 **本地命令（Local command）** 连接器添加：

```json
{
  "mcpServers": {
    "pyspy": {
      "command": "pyspy-mcp"
    }
  }
}
```

或直接运行：

```bash
pyspy-mcp
```

服务器通过 stdio 协议与 MCP Host 通信。

## 从源码开发

如果你想使用本地 `py-spy` Rust 源码，而不是 PyPI 上的包：

```bash
# 从本地 Rust 源码构建 py-spy
cargo build --release

# 二进制文件位置：
#   Linux / macOS: target/release/py-spy
#   Windows:       target/release/py-spy.exe

# 以可编辑模式安装 Python MCP 包
pip install -e ".[dev]"

# 或使用 uv
uv pip install -e ".[dev]"

# 运行测试
python -m pytest tests/pyspy_mcp -v
```

服务器会自动优先使用 `target/release/py-spy[.exe]` 本地构建二进制。你也可以通过环境变量强制指定：

```bash
export PYSPY_MCP_BINARY=/path/to/py-spy
```

## 发布到 PyPI

```bash
python -m build
python -m twine upload dist/*
```

发布的 wheel 是纯 Python 的 `py3-none-any` 包，依赖上游 `py-spy` PyPI 包。如果你修改了 Rust 源码并希望打包发布这些改动，需要构建各平台专用 wheel（或将重新编译的 `py-spy` 二进制作为包数据一起分发）。

## 权限说明

- **Linux**：对已有 PID 进行采样通常需要 `ptrace` 权限（使用 `sudo` 或设置 `CAP_SYS_PTRACE` 能力）。
- **macOS**：通常需要 root 权限，且系统二进制受 System Integrity Protection (SIP) 保护。
- **Windows**：某些进程可能需要以管理员身份运行。

## 配置

设置 `PYSPY_MCP_BINARY` 环境变量可覆盖 bundled/开发版 py-spy 二进制的位置。
