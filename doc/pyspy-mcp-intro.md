# pyspy-mcp：借助 LLM 诊断 Python 程序性能瓶颈

Python 性能优化是后端开发、数据工程和高并发服务中绕不开的话题。常见的性能问题包括 CPU 热点函数、低效算法、GIL 争抢、子进程开销以及 C 扩展调用栈过长等。传统的分析手段如 `cProfile` 和 `line_profiler` 虽然有效，但往往需要修改代码、插桩或记住复杂的命令行参数；而外部采样工具如 `py-spy` 虽能低侵入地 attach 到运行中的进程，但其命令行接口对普通开发者仍有一定门槛。

pyspy-mcp 是一个基于 [Model Context Protocol（MCP）](https://modelcontextprotocol.io) 的服务器，它将 Python 采样分析器 [py-spy](https://github.com/benfred/py-spy) 的能力暴露给 DeepSeek、Kimi、Claude、GPT 等大型语言模型。通过 MCP，开发者无需手动记忆命令，也无需在终端与文档之间反复切换，只需在对话中描述需求，即可由 LLM 驱动完成性能采样、火焰图生成、热点分析和优化前后对比。

## 为什么需要 pyspy-mcp？

在 Python 性能分析领域，传统工具有两类：

- **内置型分析器**：如 `cProfile`、`profile`、`line_profiler`。这类工具通常需要在代码中显式启用，或通过装饰器、上下文管理器注入，会对运行时产生一定开销，且不适合分析已经启动的进程。
- **外部采样型分析器**：如 `py-spy`、`pyinstrument`。这类工具以独立进程的形式，定期读取目标进程的内存，反推其当前的调用栈，对目标程序的侵入性极低，可以 attach 到正在运行的进程上。

py-spy 属于第二类，它的特点是低侵入、低开销、支持实时 attach。但它的使用方式以命令行为主，参数较多，学习成本不低：

```bash
py-spy record -o profile.svg --pid 12345 -d 5 -r 100 --format flamegraph
```

如果你希望把性能分析能力集成到 AI 辅助工作流中，让 Claude 帮你选择进程、执行采样、解析结果、提出优化建议，那么就需要一个中间层。pyspy-mcp 就是这个中间层。

## pyspy-mcp 是什么？

pyspy-mcp 把 py-spy 的核心能力封装成一组 MCP 工具。每个工具都有明确的输入参数和返回格式，Claude 可以根据用户请求自动调用。主要工具包括：

| 工具名 | 作用 |
| --- | --- |
| `record_profile` | 对指定进程或命令采样，生成 `speedscope` / `flamegraph` / `raw` / `chrometrace` 等格式的火焰图或分析数据 |
| `analyze_profile` | 分析已生成的 profile 文件，返回最热的函数及其占用比例 |
| `compare_profiles` | 对比两个 profile，看优化前后哪些函数变快/变慢了 |
| `dump_stacks` | 立即抓取目标进程的 Python 调用栈 |
| `top_profile` | 像 `py-spy top` 一样持续监控，返回最活跃的函数 |
| `list_python_processes` | 列出当前机器上的 Python 进程，方便选目标 |

### 输出格式说明

`record_profile` 支持四种输出格式，适用于不同分析场景：

| 格式 | 文件后缀 | 用途 |
| --- | --- | --- |
| `speedscope` | `.json` | 与 speedscope.app 兼容的交互式火焰图，推荐用于可视化分析 |
| `flamegraph` | `.svg` | 自包含的 SVG 火焰图，可直接在浏览器中打开 |
| `raw` | `.txt` | 简单的栈计数文本，便于脚本化分析 |
| `chrometrace` | `.json` | Chrome DevTools 兼容的 timeline 格式，可与前端性能分析工具结合使用 |

对于日常诊断，`speedscope` 和 `raw` 是最常用的选择。`analyze_profile` 可以解析 `speedscope` 和 `raw` 两种格式。

### 它背后的 py-spy 是怎么工作的？

py-spy 的采样原理和传统的 Python 分析器不太一样。你熟悉的 `cProfile` 需要在代码里插入 hook，运行时会有一定开销；而 py-spy 是一个**外部进程**，它定期读取目标 Python 进程的内存，根据解释器内部的线程状态和调用栈结构，反推出当前正在执行的函数。

这种“外部采样”的好处是：

- **低侵入**：不需要修改代码，不需要在目标进程里插桩。
- **低开销**：采样频率通常只有 100Hz 到 1000Hz，对目标程序的影响很小。
- **可以分析运行中的进程**：即使程序已经启动，你也可以随时 attach 上去采样。
- **能看 C 扩展**：开启 `native=True` 后，还能把 C/Cython 扩展的栈帧一起抓出来。

也正因为它要读取其他进程内存，所以在 Linux 上需要 `ptrace` 能力，在 macOS 上受 SIP 保护，在 Windows 上有时需要管理员权限。这是安全机制，不是 bug。

相比直接在命令行敲 `py-spy record --pid xxx --output ...`，MCP 最大的好处是：

1. **自然语言驱动**：你不用再记命令参数，描述你的需求即可。
2. **上下文连续**：Claude 拿到结果后，可以直接继续帮你解读、给出优化建议。
3. **结果结构化**：返回的表格和火焰图 URL 直接嵌入对话，不用切窗口。

---

## 安装与配置

pyspy-mcp 的安装和普通 Python 包一样简单。

### 安装

```bash
pip install pyspy-mcp
```

如果你用 `uv`：

```bash
uv pip install pyspy-mcp
# 或者作为全局工具安装
uv tool install pyspy-mcp
```

安装完成后，你会得到一个 `pyspy-mcp` 命令。这个命令启动一个基于 stdio 的 MCP 服务器，Claude Desktop 可以通过配置直接调用它。

### 在 Claude Desktop 中配置

打开 Claude Desktop 的设置，找到 `claude_desktop_config.json`（通常在菜单 `Settings → Developer → Edit Config`），添加如下配置：

```json
{
  "mcpServers": {
    "pyspy": {
      "command": "pyspy-mcp"
    }
  }
}
```

保存后重启 Claude Desktop。如果一切正常，你会在对话工具栏里看到 `pyspy` 相关的工具图标。

### 在 OpenCode 中配置

OpenCode 同样支持 MCP 服务器，配置格式与 Claude Desktop 兼容。编辑 OpenCode 的 MCP 配置文件（通常为 `~/.opencode/mcp.json`，具体路径可能因版本而异），添加如下内容：

```json
{
  "mcpServers": {
    "pyspy": {
      "command": "pyspy-mcp"
    }
  }
}
```

保存后重启 OpenCode，pyspy-mcp 的工具会出现在 OpenCode 的 AI 对话工具列表中。如果 `pyspy-mcp` 不在 PATH 中，需使用完整路径，例如：

```json
{
  "mcpServers": {
    "pyspy": {
      "command": "/Users/yourname/.local/bin/pyspy-mcp"
    }
  }
}
```

OpenCode 与 Claude Desktop 的 MCP 配置结构基本一致，因此你可以在不同客户端之间复用相同的 `mcpServers` 配置。

pyspy-mcp 并不是替代 py-spy CLI，而是提供另一种更易于集成到 AI 工作流中的调用方式。下表对比了两种使用方式：

| 能力 | py-spy CLI | pyspy-mcp |
| --- | --- | --- |
| 命令/参数记忆 | 需要记忆命令和参数 | 通过 Claude 自然语言触发 |
| 进程选择 | 手动查 PID | 可调用 `list_python_processes` 自动列出 |
| 结果解读 | 人工查看火焰图/表格 | Claude 可直接解析并解释 |
| 上下文连续性 | 每次分析独立 | 可在同一会话中持续追问 |
| 自动化集成 | 适合脚本/CI | 适合对话式 AI 辅助开发 |
| 底层能力 | 完整 | 完整，通过调用 py-spy 实现 |

如果你已经在 CI 脚本或运维流程中大量使用 py-spy CLI，可以继续保留；如果希望把性能分析交给 Claude 辅助完成，pyspy-mcp 是更合适的入口。

### 权限提示

py-spy 需要读取其他进程内存，所以不同平台可能需要额外权限：

- **Linux**：通常需要 `ptrace` 权限，可以用 `sudo` 运行 Claude，或者给 Python 进程设置 `cap_sys_ptrace` 能力。
- **macOS**：受 System Integrity Protection（SIP）影响，分析系统进程或某些保护进程通常需要 root。
- **Windows**：部分进程需要管理员权限。

如果你只是分析自己启动的普通 Python 脚本，通常不会有问题。

---

## 实战：CPU 密集型示例分析

本节通过一个包含递归计算与低效排序的示例，演示完整的性能诊断流程。该示例模拟了 CPU 密集型代码中常见的性能暗坑：无缓存递归和 O(n²) 排序算法。

### 步骤 1：准备示例脚本

创建 `slow_example.py`：

```python
# slow_example.py
import time


def fibonacci(n):
    """递归版斐波那契，完全没有缓存。"""
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


def bubble_sort(arr):
    """经典但低效的冒泡排序。"""
    arr = arr.copy()
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr


def process_data():
    """模拟一个数据处理流程。"""
    numbers = list(range(500, 0, -1))
    sorted_numbers = bubble_sort(numbers)
    return sum(fibonacci(x % 20) for x in sorted_numbers[:80])


if __name__ == "__main__":
    print("Starting slow_example.py, pid =", __import__("os").getpid())
    while True:
        result = process_data()
        print("Result:", result)
        time.sleep(0.5)
```

运行它：

```bash
python slow_example.py
```

你会看到输出类似：

```text
Starting slow_example.py, pid = 12345
Result: 6765
Result: 6765
...
```

记住这个 PID，比如 `12345`。它就是我们要分析的目标。

### 步骤 2：列出目标进程

调用 `list_python_processes` 工具，Claude 会返回当前运行的 Python 进程列表：

```text
| PID   | RSS (MB) | Command                                    |
|-------|----------|--------------------------------------------|
| 12345 | 12.3     | python slow_example.py                     |
| 9876  | 45.6     | /usr/bin/python3 /usr/local/bin/some-tool  |
```

你确认 `12345` 就是目标进程。

### 步骤 3：录制性能分析

调用 `record_profile`，对目标进程采样 5 秒，输出格式为 `speedscope`：

```python
record_profile(
    pid=12345,
    duration=5,
    output_format="speedscope",
    rate=100,
)
```

pyspy-mcp 会在后台执行 `py-spy record -o ... --format speedscope --pid 12345 -d 5 -r 100`，采样结束后返回生成的 JSON 内容，或将其写入你指定的路径。若要落盘，可额外指定 `output_path` 参数。

### 步骤 4：分析瓶颈

对 Claude 说：

> “分析刚才生成的 profile，返回最热的 10 个函数。”

Claude 会调用 `analyze_profile`，输出类似下面这样的表格：

```text
| Frame                                | Samples | % of Total |
|--------------------------------------|---------|------------|
| fibonacci (slow_example.py:4)        | 3521    | 72.4%      |
| bubble_sort (slow_example.py:11)     | 842     | 17.3%      |
| process_data (slow_example.py:21)    | 378     | 7.8%       |
| <builtin> sum                       | 92      | 1.9%       |
| <builtin> print                     | 18      | 0.4%       |
| <builtin> time.sleep                | 5       | 0.1%       |
| ...                                  | ...     | ...        |
```

从这个表格可以一目了然地看到：

- `fibonacci` 函数占了 **72.4%** 的采样时间，是头号瓶颈。
- `bubble_sort` 占了 **17.3%**，也是低效实现。

> **说明**：`% of Total` 表示在采样期间，该函数出现在调用栈中的样本比例。比例越高，说明程序在该函数及其子调用上花费的时间越多。

### 步骤 5：优化并验证

从分析结果可以得出：

- `fibonacci` 采用无缓存递归，时间复杂度为指数级 $O(2^n)$，应使用 `functools.lru_cache` 或改写为迭代实现。
- `bubble_sort` 的时间复杂度为 $O(n^2)$，应替换为 Python 内置的 Timsort（`sorted()`），时间复杂度为 $O(n \log n)$。

优化后的代码如下（`optimized_example.py`）：

```python
# optimized_example.py
import time
from functools import lru_cache


@lru_cache(maxsize=None)
def fibonacci(n):
    """带缓存的递归斐波那契。"""
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


def process_data():
    """用内置排序替代冒泡排序。"""
    numbers = list(range(500, 0, -1))
    sorted_numbers = sorted(numbers)
    return sum(fibonacci(x % 20) for x in sorted_numbers[:80])


if __name__ == "__main__":
    print("Starting optimized_example.py, pid =", __import__("os").getpid())
    while True:
        result = process_data()
        print("Result:", result)
        time.sleep(0.5)
```

再次采样并分析，结果会变成类似：

```text
| Frame                                | Samples | % of Total |
|--------------------------------------|---------|------------|
| process_data (optimized_example.py:13)| 2812    | 58.2%      |
| <builtin> sum                       | 1204    | 24.9%      |
| fibonacci (optimized_example.py:5)   | 312     | 6.5%       |
| <builtin> sorted                    | 298     | 6.2%       |
| ...                                  | ...     | ...        |
```

最热的函数从 `fibonacci` 和 `bubble_sort` 变成了 `process_data` 和 `sum`，说明 CPU 不再被递归排序拖累。两个 profile 可以通过 `compare_profiles` 直接对比：

```python
compare_profiles(
    profile_a="/tmp/slow.json",
    profile_b="/tmp/optimized.json",
    top_n=10,
)
```

该工具会返回一个差异表格，直观展示各函数在优化前后的样本占比变化。

### 实战里可能遇到的问题

使用 pyspy-mcp 时，常见的错误及其处理方法如下：

**问题 1：Claude 找不到 pyspy-mcp 工具**
- 检查 `pyspy-mcp` 是否在 PATH 中。Linux/macOS 下运行 `which pyspy-mcp`，Windows 下运行 `where pyspy-mcp`。
- 若不在 PATH，在 `claude_desktop_config.json` 中使用完整路径，例如 `"command": "/Users/x/.local/bin/pyspy-mcp"`。.

**问题 2：采样失败，提示权限不足**
- Linux 上，尝试用 `sudo` 启动 Claude Desktop，或者给 Python 进程设置 `CAP_SYS_PTRACE`：
  ```bash
  sudo setcap cap_sys_ptrace+ep /usr/bin/python3
  ```
- macOS 上，分析系统或受 SIP 保护的进程通常需要 root。
- Windows 上，右键以管理员身份运行 Claude Desktop。

**问题 3：`analyze_profile` 显示没有样本**
- 检查采样时间是否太短，或目标进程是否处于空闲状态。
- 若进程主要在等待 IO 或网络，可设置 `idle=True` 以包含 idle 线程。
- 多进程程序需设置 `subprocesses=True`。

**问题 4：Windows 上 `top_profile` 结果格式不同**
- Windows 上 `py-spy top` 无法通过管道捕获，pyspy-mcp 会自动回退到 `record --format raw`，然后返回最热函数。结果仍然准确，只是展示格式不同。

---

## 其他工具与进阶参数

### dump_stacks

`dump_stacks` 用于抓取目标进程当前所有线程的调用栈，适用于排查死锁、长时间等待、网络超时等“卡住”场景：

```python
dump_stacks(
    pid=12345,
    json_output=True,
    locals_level=0,
)
```

返回示例：

```json
[
  {
    "pid": 12345,
    "tid": 12345,
    "active": true,
    "frames": [
      "process_data (optimized_example.py:13)",
      "fibonacci (optimized_example.py:5)",
      "<builtin> sum"
    ]
  }
]
```

这能帮你瞬间知道程序此刻卡在哪一行。

### top_profile

`top_profile` 类似 `py-spy top`，会持续监控进程并返回最活跃的函数。适合快速查看当前的热点函数。

在 Linux/macOS 上，它会直接运行 `py-spy top` 并捕获输出；在 Windows 上，由于 `py-spy top` 无法被管道捕获，pyspy-mcp 会自动回退到一段短时间的 `record --format raw`，然后返回最热函数。这个细节对用户是透明的。

### 进阶参数

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `gil` | bool | 只采样持有 GIL 的线程，用于定位多线程中的 CPU 争抢问题。 |
| `subprocesses` | bool | 同时分析子进程，适用于 `multiprocessing` 或 `subprocess` 启动的程序。 |
| `native` | bool | 把 C 扩展栈也纳入采样，适用于 NumPy、Pandas、Cython 等场景。部分平台不支持。 |
| `idle` | bool | 包含 idle 线程，适合分析 IO 等待或低 CPU 占用场景。 |
| `rate` | int | 每秒采样次数，默认 100。提高频率可增加精度，但也会增大开销。 |

## 常见误区

用好性能分析工具，除了会用，还得避免一些常见误解。

**误区 1：火焰图里占比高的函数就是“罪魁祸首”**

不一定。一个函数占比高，可能是因为它本身很慢，也可能是因为它被调用了太多次。要结合代码看：
- 如果是单次执行慢，优化函数内部逻辑。
- 如果是调用次数太多，优化调用它的上层逻辑。

**误区 2：采样频率越高越准确**

采样频率确实影响精度，但 100Hz（默认）对大多数场景已经够用了。频率太高会增加目标进程开销，甚至让结果失真。除非你非常确定，否则不建议轻易调到 1000Hz 以上。

**误区 3：profile 工具只能优化 CPU 问题**

py-spy 主要反映 CPU 层面的调用栈。如果你的程序卡在数据库查询、网络请求、磁盘 IO 上，你可能看到 Python 停在 `socket.recv` 或 `file.read` 之类的地方，但真正的根因需要结合数据库慢查询日志、网络监控等工具进一步分析。

**误区 4：优化后不需要再测**

性能优化最怕“感觉变快了”。每次改动后，最好重新跑一遍 `record_profile` + `analyze_profile`，或者用 `compare_profiles` 对比优化前后的数据，用数字说话。

---

## 总结

pyspy-mcp 提供了一种将 py-spy 的采样分析能力接入 MCP 生态的方案。通过 `record_profile`、`analyze_profile`、`compare_profiles`、`dump_stacks`、`top_profile` 和 `list_python_processes` 等工具，开发者可以在 Claude 对话中完成从目标进程选择、采样、分析到优化的完整流程，而无需手动记忆复杂的命令行参数。

主要适用场景：

- CPU 密集型脚本的瓶颈定位。
- Python 多线程/多进程程序中的 GIL 或子进程行为分析。
- C 扩展（NumPy、Pandas、Cython）的栈帧采样。
- 优化前后的性能数据对比。

局限性：

- py-spy 主要反映 Python 层面的调用栈，对于数据库慢查询、网络延迟、磁盘 IO 等外部瓶颈，需要结合数据库慢查询日志、系统监控、网络抓包等工具进一步分析。
- 部分平台（如 macOS）受 SIP 限制，分析某些进程需要 root 权限。
- Windows 上 `top_profile` 存在实现回退，输出格式与 Linux/macOS 略有不同。

对于希望把性能分析工作流集成到 AI 辅助开发中的团队，pyspy-mcp 是一个低门槛、高效率的入口。

---

## 延伸阅读

1. 将 `record_profile` 生成的 `speedscope` JSON 文件上传到 [speedscope.app](https://www.speedscope.app/)，使用交互式火焰图查看完整调用链。
2. 使用 `compare_profiles` 对比优化前后的 profile，建立数据驱动的性能验证习惯。
3. 阅读 [py-spy 官方文档](https://github.com/benfred/py-spy)，了解 `--idle`、`--gil`、`--subprocesses`、`--native` 等高级参数。

---

**参考链接**

- pyspy-mcp: https://github.com/LBurny/pyspy-mcp
- py-spy: https://github.com/benfred/py-spy
- Model Context Protocol: https://modelcontextprotocol.io
