# jy-customer-requirement-analysis

金融投顾智能助理技能 - 基于客户沟通素材生成标准化投资需求分析报告。

## 目录结构

```
jy-customer-requirement-analysis/
├── README.md                                    # 本文件
└── jy-customer-requirement-analysis/
    ├── SKILL.md                                 # 技能主文档
    └── references/
        └── output-examples.md                   # 输出示例与格式规范
```

## 前置要求

- Node.js 和 npm
- mcporter CLI
- JY_API_KEY（向恒生聚源申请：datamap@gildata.com）

## 安装配置

1. 安装 mcporter：`npm install -g mcporter`
2. 配置 MCP 服务：
   ```bash
   mcporter config add gildata-tool --url "https://api.gildata.com/mcp-servers/aidata-assistant-srv-tool?token=你的 JY_API_KEY"
   mcporter config add gildata-api --url "https://api.gildata.com/mcp-servers/aidata-assistant-srv-api?token=你的 JY_API_KEY"
   ```
3. 重启 OpenClaw：`openclaw gateway restart`

## 使用方式

提供客户沟通素材，技能自动输出七步标准化分析报告：
1. 客户需求分析
2. 宏观环境分析与配置调整建议
3. 投资需求可行性评估
4. 解决方案建议
5. 产品池匹配分析
6. 再平衡与后续关注
7. 潜在需求挖掘与引导话术

## 触发词

- "分析客户需求"
- "投顾分析"
- "客户画像"
- "理财方案"
- "投资需求分析"

## 详细文档

- 完整使用说明：`jy-customer-requirement-analysis/SKILL.md`
- 输出示例：`jy-customer-requirement-analysis/references/output-examples.md`
