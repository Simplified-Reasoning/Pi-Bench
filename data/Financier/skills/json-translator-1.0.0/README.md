# JSON Translator 技能

JSON 文件翻译助手，用于翻译 JSON 文件中的文本内容，特别是 `description` 字段。

## 文件结构

```
json-translator/
├── SKILL.md          # 技能说明文档
├── README.md         # 使用说明（本文件）
└── scripts/
    └── translate_json.py  # 翻译脚本
```

## 快速开始

### 1. 翻译 description 字段到中文

```bash
python scripts/translate_json.py data.json --target-language zh
```

### 2. 翻译多个字段

```bash
python scripts/translate_json.py data.json --target-language en --fields name,description
```

### 3. 指定源语言

```bash
python scripts/translate_json.py data.json --target-language ja --source-language zh
```

## 参数说明

| 参数 | 必需 | 说明 | 示例 |
|------|------|------|------|
| 输入文件 | 是 | JSON 文件路径 | `data.json` |
| `--target-language` | 是 | 目标语言代码 | `zh`, `en`, `ja`, `ko` |
| `--source-language` | 否 | 源语言代码 | `zh`, `en`, `ja`, `ko`, `auto` |
| `--fields` | 否 | 要翻译的字段名（逗号分隔） | `name,description` |
| `--output` | 否 | 输出文件路径 | `output.json` |

## 支持的语言

| 语言代码 | 语言名称 |
|---------|---------|
| `zh` | 中文（简体） |
| `en` | 英文 |
| `ja` | 日文 |
| `ko` | 韩文 |

## 使用场景

- **产品描述翻译**：翻译产品信息中的描述字段
- **API 文档翻译**：翻译 API 文档的多语言版本
- **配置文件翻译**：翻译配置文件中的说明文本
- **数据集翻译**：翻译数据集中的文本字段
- **国际化开发**：快速生成 JSON 文件的多语言版本

## 注意事项

1. 需要安装 `requests` 库：`pip install requests`
2. 确保网络可以访问 MyMemory API
3. 建议文件大小不超过 10MB
4. 翻译失败时会保留原文并添加错误标记

## 更多信息

详细的使用说明和示例请参考 [SKILL.md](./SKILL.md)
