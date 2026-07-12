# pyspy-mcp 介绍博客写作计划

> **For agentic workers:** Implement this plan inline in the current session. No subagents. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 撰写一篇面向普通 Python 开发者的中文博客，介绍如何使用 pyspy-mcp 在 Claude 里诊断 Python 性能问题，并保存为 `doc/pyspy-mcp-intro.md`。

**架构：** 采用“故事线 + 产品介绍 + 实战案例”的混合写法，以一个可运行的 CPU 密集型慢脚本为主线，串联 pyspy-mcp 的安装、配置、工具调用、结果解读和优化建议。

**Tech Stack：** Markdown。

## 全局约束
- 博客语言：中文。
- 文件格式：Markdown。
- 保存路径：`doc/pyspy-mcp-intro.md`。
- 篇幅：约 4000 字。
- 目标读者：普通 Python 开发者，性能分析经验有限。
- 必须包含：Claude Desktop 配置、可运行慢脚本示例、工具调用示例、结果表格。
- 不生成真实图片，结果用代码块/文本表格展示。

---

### Task 1: 创建目录与示例脚本

**文件：**
- 创建目录：`doc/`

**接口：**
- 无外部依赖。
- 输出：目录存在。

- [ ] **Step 1：确认 doc 目录不存在或为空**

运行：
```bash
ls -la I:/pyspy_mcp/doc 2>/dev/null || echo "doc directory does not exist"
```
预期：输出目录不存在或为空。

- [ ] **Step 2：创建 doc 目录**

运行：
```bash
mkdir -p I:/pyspy_mcp/doc
```
预期：目录创建成功，无报错。

---

### Task 2: 撰写博客正文

**文件：**
- 创建：`doc/pyspy-mcp-intro.md`

**接口：**
- 无外部依赖。
- 输出：完整的 Markdown 博客，字数约 4000 字。

- [ ] **Step 1：编写博客内容**

博客应包含以下章节：
1. 标题与导语
2. 引子：一个慢脚本的故事
3. pyspy-mcp 是什么？
4. 安装与 Claude Desktop 配置
5. 实战：慢脚本 + 找瓶颈 + 优化
6. 其他工具简介
7. 总结

必须包含的代码块：
- `slow_example.py`：CPU 密集型脚本（递归斐波那契 + 慢排序）
- `optimized_example.py`：优化后的版本
- `claude_desktop_config.json`：MCP 配置
- 模拟的 `analyze_profile` 输出表格

- [ ] **Step 2：保存文件到 `doc/pyspy-mcp-intro.md`**

预期：文件存在，内容完整。

---

### Task 3: 验证输出

**文件：**
- 读取：`doc/pyspy-mcp-intro.md`

**接口：**
- 输入：博客文件。
- 输出：字数统计和结构检查。

- [ ] **Step 1：检查文件结构**

运行：
```bash
python - << 'PY'
from pathlib import Path
p = Path('I:/pyspy_mcp/doc/pyspy-mcp-intro.md')
assert p.exists(), 'File not found'
text = p.read_text(encoding='utf-8')
assert '# ' in text, 'Missing H1'
assert '```python' in text, 'Missing Python code blocks'
assert 'record_profile' in text, 'Missing record_profile mention'
assert 'analyze_profile' in text, 'Missing analyze_profile mention'
print('Structure check passed')
PY
```
预期：输出 `Structure check passed`。

- [ ] **Step 2：统计字数**

运行：
```bash
python - << 'PY'
from pathlib import Path
import re
p = Path('I:/pyspy_mcp/doc/pyspy-mcp-intro.md')
text = p.read_text(encoding='utf-8')
# 统计中文字符和英文单词
chinese = len(re.findall(r'[\u4e00-\u9fff]', text))
words = len(re.findall(r'[a-zA-Z]+', text))
print(f'Chinese characters: {chinese}')
print(f'English words: {words}')
print(f'Estimated total: {chinese + words}')
PY
```
预期：中文字符 + 英文单词总数在 3500-5000 之间。

---

## 自我审查

1. **Spec coverage：** 博客覆盖故事引入、产品介绍、安装配置、实战案例、其他工具、总结；包含慢脚本示例和 Claude Desktop 配置；字数约 4000。✓
2. **Placeholder scan：** 计划无 TBD/TODO。✓
3. **Type consistency：** 不适用，纯 Markdown 文件。✓
