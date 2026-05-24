# pyproject.toml 可编辑包配置（扁平目录结构）

## 背景

当项目使用扁平目录结构（不采用 src-layout）时，无法在 `[project]` 中使用 `packages` 字段（这是 PEP 621 的限制）。此时需要通过 `[tool.setuptools]` 配置来声明包。

## 适用场景

- 项目根目录直接包含业务包（如 `langchain_agent/`、`backend/`）
- 不希望将代码移动到 `src/` 子目录
- 需要通过 `uv pip install -e .` 实现可编辑安装

## 配置示例

```toml
[build-system]
requires = ["setuptools>=61"]
build-backend = "setuptools.build_meta"

[project]
name = "myproject"
version = "0.1.0"
description = "A Python project"
requires-python = ">=3.13"
dependencies = [
    # 你的依赖...
]

[tool.setuptools]
package-dir = {"" = "."}

[tool.setuptools.packages.find]
where = ["."]
include = ["langchain_agent*", "backend*"]
exclude = ["jupyter*", "tests*"]
```

## 配置说明

| 配置项 | 说明 |
| :--- | :--- |
| `package-dir = {"" = "."}` | 将包根目录映射到项目根目录（`.`） |
| `include = ["langchain_agent*", "backend*"]` | 声明哪些包需要被包含（支持 glob 模式） |
| `exclude = ["jupyter*", "tests*"]` | 排除不需要当作包的目录 |

## 使用方法

```bash
# 安装为可编辑包
uv pip install -e .

# 验证安装
python -c "import langchain_agent; print(langchain_agent)"
```

安装后，无论在 Jupyter 还是命令行中，都可以直接 `import langchain_agent` 和 `import backend`，**无需**使用 `sys.path.insert(0, ...)`。

## 注意事项

1. 每个需要被当作包的目录必须包含 `__init__.py` 文件
2. 如果包名包含下划线或特殊字符，需要确保 glob 模式匹配正确
3. 排除列表应根据实际项目结构调整，确保不包含不需要的目录