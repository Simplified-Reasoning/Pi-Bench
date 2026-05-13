---
name: jy-customer-requirement-analysis
description: 金融投顾智能助理技能。基于客户沟通素材，帮助理财师/投顾经理快速精准理解客户投资需求，输出标准化分析报告（需求痛点、可行性评估、解决方案、产品匹配、潜在需求挖掘）。支持 PDF 导出和 HTML 可视化。使用场景：当用户需要分析客户投资需求、生成投顾分析报告、进行客户画像分析、制定理财方案或匹配金融产品时触发。Financial advisory assistant skill for analyzing customer investment needs and generating standardized reports. Supports PDF export and HTML visualization. Triggered for customer analysis, advisory reports, financial planning, and product matching.
metadata:
  openclaw:
    requires:
      bins: ["node", "npm", "mcporter"]
    install:
      - id: install-mcporter
        kind: node
        package: mcporter
        label: Install mcporter via npm
---

# 客户需求分析 - 金融投顾智能助理

基于客户沟通素材，输出标准化七步分析报告。详细示例见 `references/output-examples.md`。

## 功能范围

- 客户需求痛点分析、宏观环境分析与配置建议
- 投资需求可行性评估、解决方案建议
- 产品池匹配分析（基金、债券、黄金、QDII 等）
- 再平衡与后续关注建议、潜在需求挖掘与引导话术
- 支持 Markdown、HTML、PDF 多种输出格式

## 查询建议

**查询要素：** 客户基本信息（年龄、职业、收入、家庭）、投资历史、风险测评结果、资金用途和时间规划。

**触发词：** "分析客户需求"、"投顾分析"、"客户画像"、"理财方案"、"投资需求分析"

**查询示例：**
```
客户王先生，45 岁，企业高管，年收入 150 万，已婚有一子（12 岁）。
现有资产：房产 2 套，存款 200 万，股票 50 万。
对话记录："最近市场波动太大，我有点担心。希望能有稳定收益。"
风险测评：平衡型
```

## 环境检查与配置

**每次使用本技能前，必须先检查 mcporter 安装和 MCP 服务配置状态！**

### 步骤 1：检查 mcporter 是否安装

```bash
mcporter --version
```

**如未安装：**
```bash
npm install -g mcporter
mcporter --version
```

### 步骤 2：检查 MCP 服务配置

```bash
mcporter list
```

**预期输出：** `jy-financedata-tool`（5 个工具：FundMultipleFactorFilter, StockMultipleFactorFilter, FinQuery, FinancialResearchReport, MacroIndustryData）和 `jy-financedata-api`（252 个接口）

**如未配置，获取 JY_API_KEY：**

向恒生聚源申请：datamap@gildata.com

**邮件标题：** 数据地图 KEY 申请-XX 公司 - 申请人姓名

**正文模板：** 姓名、手机号、公司全称、部门、岗位、MCP_KEY 申请用途、Skill 申请列表、是否需要 Skill 安装包。

**无 JY_API_KEY 无法使用，必须先申请！**

### 步骤 3：配置 MCP 服务

```bash
# 配置 jy-financedata-tool 服务（5 个工具）
mcporter config add jy-financedata-tool --url "https://api.gildata.com/mcp-servers/aidata-assistant-srv-tool?token=你的 JY_API_KEY"

# 配置 jy-financedata-api 服务（252 个接口）
mcporter config add jy-financedata-api --url "https://api.gildata.com/mcp-servers/aidata-assistant-srv-api?token=你的 JY_API_KEY"

# 验证配置
mcporter list
```

### 步骤 4：使用方式

```bash
# 所有工具入参均为 query
# jy-financedata-tool 包含 5 个工具：FundMultipleFactorFilter, StockMultipleFactorFilter, FinQuery, FinancialResearchReport, MacroIndustryData
# 其他工具都在 jy-financedata-api 中
mcporter call jy-financedata-tool.工具名 query="查询内容"
mcporter call jy-financedata-api.工具名 query="查询内容"

# 示例（jy-financedata-tool）
mcporter call jy-financedata-tool.MacroIndustryData query="中国最新 GDP 增速和 CPI 数据"
mcporter call jy-financedata-tool.SmartFundSelection query="稳健型债券基金 年化收益 4% 以上"
mcporter call jy-financedata-tool.FinQuery query="沪深 300 指数当前点位和近期走势"
mcporter call jy-financedata-tool.FinancialResearchReport query="固收 + 策略配置建议"
mcporter call jy-financedata-tool.SmartStockSelection query="市盈率低于 20 的科技股"

# 示例（jy-financedata-api - 其他 252 个接口）
mcporter call jy-financedata-api.FinQuery query="基金代码 012348 基金简称"
```

### 步骤 5：在 OpenClaw 中启用 mcporter

**配置文件路径：**
- mcporter: `C:\Users\你的用户名\.mcporter\mcporter.json`
- openclaw: `C:\Users\你的用户名\.openclaw\openclaw.json`

**编辑 openclaw.json：**
```json
{
  "skills": {
    "entries": {
      "mcporter": {
        "enabled": true,
        "env": {
          "MCPORTER_CONFIG": "C:\\Users\\你的用户名\\.mcporter\\mcporter.json"
        }
      }
    }
  }
}
```

**重启 OpenClaw：** `openclaw gateway restart`

## 核心工作流程

### 步骤 1：接收并解析客户输入

提取关键信息：客户基本信息、资产负债、投资目标、风险偏好、资金用途。信息不足时询问用户。

### 步骤 2：并发查询宏观数据

```bash
mcporter call jy-financedata-tool.MacroIndustryData query="中国最新 GDP 增速 CPI PMI"
mcporter call jy-financedata-tool.FinQuery query="沪深 300 上证指数 创业板指当前点位"
mcporter call jy-financedata-tool.FinQuery query="10 年期国债收益率 人民币兑美元汇率"
mcporter call jy-financedata-tool.FinQuery query="COMEX 黄金 布伦特原油当前价格"
mcporter call jy-financedata-tool.FinQuery query="VIX 恐慌指数当前值"
```

### 步骤 3：查询研报观点

```bash
mcporter call jy-financedata-tool.FinancialResearchReport query="当前市场环境下资产配置建议"
```

### 步骤 4：根据风险等级筛选产品

```bash
mcporter call jy-financedata-tool.SmartFundSelection query="平衡型混合基金 近 3 年收益排名前 20 规模大于 10 亿"
mcporter call jy-financedata-tool.SmartFundSelection query="稳健型债券基金 近 1 年收益大于 3%"
mcporter call jy-financedata-tool.SmartFundSelection query="成长型股票基金 近 3 年收益排名前 20"
```

### 步骤 5：查询产品详情

```bash
mcporter call jy-financedata-tool.FinQuery query="基金代码 近 1 年收益 近 3 年收益 阶段业绩表现"
mcporter call jy-financedata-tool.FinQuery query="基金代码 基金规模 资产规模"
mcporter call jy-financedata-tool.FinQuery query="基金代码 基金经理 申购状态 基金公司名称"
```

### 步骤 6：生成七步分析报告

1. 客户需求分析
2. 宏观环境分析与配置调整建议
3. 投资需求可行性评估
4. 解决方案建议
5. 产品池匹配分析
6. 再平衡与后续关注
7. 潜在需求挖掘与引导话术

### 步骤 7：合规检查与免责声明

检查禁用词语，标注数据来源和查询日期，添加免责声明。

## 快速开始

### 工具调用命令

**jy-financedata-tool（5 个工具）：**

| 工具 | 用途 | 调用示例 |
|------|------|----------|
| `FinQuery` | 金融数据查询 | `mcporter call jy-financedata-tool.FinQuery query="沪深 300 指数走势"` |
| `MacroIndustryData` | 宏观经济数据 | `mcporter call jy-financedata-tool.MacroIndustryData query="最新 GDP 增速 CPI"` |
| `FinancialResearchReport` | 券商研报 | `mcporter call jy-financedata-tool.FinancialResearchReport query="固收 + 策略配置建议"` |
| `FundMultipleFactorFilter` | 筛选基金 | `mcporter call jy-financedata-tool.SmartFundSelection query="稳健型债券基金 年化收益 4% 以上"` |
| `StockMultipleFactorFilter` | 选股 | `mcporter call jy-financedata-tool.SmartStockSelection query="市盈率低于 20 的科技股"` |

**jy-financedata-api（252 个接口）：** 其他所有金融数据接口

### 数据完整性要求

- ❌ 禁止出现"待查询"字样
- ✅ 所有数据必须来自聚源 MCP 实时查询
- ✅ 查询不到的数据标注"--"并说明原因
- ✅ 每个产品标注数据来源和查询日期

### 产品准入标准

| 检查项 | 标准 | 处理方式 |
|--------|------|----------|
| 申购状态 | 开放申购 | 暂停申购标注"⚠️"并提供替代 |
| 存续规模 | ≥5000 万元 | <5000 万标注"⚠️ 规模过小" |
| 成立年限 | 建议≥1 年 | <1 年标注"⚠️ 新基金" |
| 异常收益 | 纯债>8% 或固收+>15% | 检查大额赎回，标注"⚠️ 收益失真" |

详细规则见 `references/output-examples.md`。

## 风险等级映射

| 等级 | 权益上限 | 适合产品 |
|------|---------|----------|
| 保守型 | 0% | 货币基金、国债 |
| 稳健型 | 20% | 纯债基金、固收 + |
| 平衡型 | 50% | 混合基金、指数基金 |
| 成长型 | 70% | 股票基金、行业主题 |
| 进取型 | 100% | 股票基金、QDII |

## 输出结构

### 一、客户需求分析
精准提炼核心痛点，语言精炼、观点鲜明。

### 二、宏观环境分析与配置调整建议
基于聚源 MCP 数据，给出 2-3 条配置建议。

### 三、投资需求可行性评估
评估可行性，给出判断（高/中/低）。

### 四、解决方案建议
提出针对性方案，明确产品类型和配置策略。

### 五、产品池匹配分析
从聚源基金库匹配推荐，每类 2-4 个产品，数据实时查询。

### 六、再平衡与后续关注
提供动态平衡建议和关注指标。

### 七、潜在需求挖掘与引导话术
挖掘潜在需求，提供专业引导话术。

## 限制

### 数据源限制
- ✅ 允许：`mcporter call jy-financedata-tool.*` 或 `jy-financedata-api.*` 查询的数据
- ❌ 禁止：编造数据、引用其他平台（Wind、同花顺、东方财富等）

### 输出要求
- 不承诺具体收益，使用"预期"、"历史"等限定词
- 必须包含风险提示
- 推荐产品时检查申购状态和规模
- 风险与需求不匹配时需明确指出

## 免责声明模板

```
---
⚠️ 免责声明

1. 本报告基于客户提供的信息和聚源金融数据平台数据生成，仅供参考，不构成投资建议。
2. 基金过往业绩不代表未来表现，市场有风险，投资需谨慎。
3. 产品推荐基于当前市场环境和产品状态，实际投资前请再次确认产品最新信息。
4. 投资者应根据自身风险承受能力、投资目标和资金流动性需求，独立做出投资决策。
5. 理财师在向客户推荐产品时，应确保已完成适当性匹配，并向客户充分揭示产品风险。

报告生成时间：{当前日期时间}
数据来源：恒生聚源金融数据平台
---
```

