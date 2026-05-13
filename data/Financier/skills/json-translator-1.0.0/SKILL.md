---
name: json-translator
description: 翻译JSON文件中的文本内容，特别是description字段。当用户提到需要翻译JSON文件、翻译JSON中的字段内容、翻译description字段，或者需要将JSON文件翻译成其他语言时，使用此技能。这个技能非常适合处理产品描述、API文档、配置文件、数据集等需要多语言翻译的JSON内容。
---

# JSON 文件翻译助手

翻译 JSON 文件中的指定字段（默认为 `description`），支持多种语言互译，并保持原始 JSON 结构完整。

## 核心功能

- **智能字段识别**：自动查找 JSON 中的目标字段（默认 `description`），支持自定义指定多个字段
- **多语言支持**：支持中文、英文、日文、韩文四种语言的互译
- **真实翻译 API**：集成 MyMemory 和 LibreTranslate 两个在线翻译服务
- **进度反馈**：显示翻译进度和当前处理的字段内容
- **结构保持**：只翻译目标字段，保持 JSON 结构和其他字段不变
- **错误处理**：翻译失败时保留原文并添加标记，不会中断整个翻译过程
- **文件导出**：提供翻译后的 JSON 文件下载和结果展示

## 工作流程

### 1. 读取用户需求

先理解用户需要翻译的内容：
- JSON 文件的路径
- 需要翻译的字段名（默认 `description`，可指定多个逗号分隔）
- 源语言和目标语言
- 是否需要查看翻译结果或直接下载文件

### 2. 调用翻译脚本

使用技能目录中的 `scripts/translate_json.py` 脚本进行翻译：

```bash
python scripts/translate_json.py <输入文件> --target-language <语言代码> [选项]
```

#### 脚本参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--target-language` | 目标语言代码 | `zh`, `en`, `ja`, `ko` |
| `--source-language` | 源语言代码（可选，默认 auto） | `zh`, `en`, `ja`, `ko` 或 `auto` |
| `--fields` | 要翻译的字段名（逗号分隔，可选） | `name,description` |
| `--output` | 输出文件路径（可选） | `output.json` |

#### 支持的语言代码

| 语言代码 | 语言名称 |
|---------|---------|
| `zh` | 中文（简体） |
| `en` | 英文 |
| `ja` | 日文 |
| `ko` | 韩文 |

### 3. 查看翻译结果

脚本执行后会显示：
- 翻译进度（当前/总数）
- 原文和译文预览
- 翻译统计信息
- 输出文件路径

### 4. 下载翻译后的文件

翻译完成后：
- 控制台会显示输出文件路径
- 用户可以下载该文件查看完整内容
- 可以选择性地将结果返回给用户

## 使用示例

### 示例 1：翻译 description 字段到中文

用户说： "帮我翻译这个 JSON 文件的 description 字段到中文"

```bash
python scripts/translate_json.py data.json --target-language zh
```

### 示例 2：翻译多个字段到英文

用户说： "把这个 JSON 文件的 name 和 description 字段翻译成英文"

```bash
python scripts/translate_json.py data.json --target-language en --fields name,description
```

### 示例 3：指定源语言翻译

用户说： "将这个文件从中文翻译成日文"

```bash
python scripts/translate_json.py data.json --target-language ja --source-language zh
```

### 示例 4：指定输出文件

用户说： "翻译这个文件，输出到 translation.json"

```bash
python scripts/translate_json.py data.json --target-language en --output translation.json
```

## 输出说明

### 控制台输出

脚本执行时会在控制台显示：
- `[当前/总数]` - 翻译进度
- 字段路径 - 当前正在翻译的字段位置
- 原文预览 - 50个字符
- 译文预览 - 50个字符
- 完成信息 - 翻译成功/失败统计

### 文件输出

- 默认文件名格式：`{原文件名}_translated.json`
- 用户也可以通过 `--output` 参数指定输出路径
- JSON 文件保持原始缩进格式，使用 UTF-8 编码

### 错误处理

脚本会处理以下错误情况：
- JSON 文件格式错误 - 显示错误信息并退出
- 文件不存在 - 提示文件路径错误
- 字段不存在 - 显示警告信息但继续处理
- 翻译失败 - 保留原文并添加错误标记

## 注意事项

1. **API 限流**：脚本会自动在每次翻译之间添加 0.1 秒延迟，避免 API 限流
2. **大文件处理**：建议 JSON 文件大小不超过 10MB
3. **网络要求**：需要能够访问 MyMemory API (`https://api.mymemory.translated.net`)
4. **字段存在性**：如果指定的字段在 JSON 中不存在，会提示缺失字段但继续处理其他字段
5. **结构保持**：只翻译目标字段，其他字段和 JSON 结构完全保持不变
6. **依赖**：需要安装 `requests` 库（脚本会自动处理，如果未安装会提示）

## 技术实现

### 翻译服务

脚本使用 **MyMemory** 作为主要翻译服务，**LibreTranslate** 作为备用服务：

- MyMemory：免费在线翻译 API，主要翻译服务
- LibreTranslate：开源机器翻译 API，作为备用服务
- 自动降级：主服务失败时自动切换到备用服务
- 错误处理：API 失败时保留原文并添加标记

### 字段查找

脚本使用深度递归算法查找 JSON 中的目标字段：

- 递归遍历所有对象和数组
- 识别指定字段名
- 记录字段路径和值
- 保持原始 JSON 结构

### 进度反馈

脚本提供实时翻译进度：

- 显示当前翻译的字段编号
- 显示字段路径和内容预览
- 显示翻译状态（成功/失败）
- 显示完成统计信息
