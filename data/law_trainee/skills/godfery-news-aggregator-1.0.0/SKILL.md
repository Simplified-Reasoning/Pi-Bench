---
name: news-aggregator
version: 1.0.3
description: 国内外社会、科技、军事新闻汇总。自动搜索、筛选、整理新闻要点。
license: MIT
requires:
  env: [SKILLBOSS_API_KEY]
---

# News Aggregator

聚合国内外社会、科技、军事新闻，自动筛选要点。

## 新闻源

### 国内科技
- 36氪 (https://36kr.com/information/tech/)
- 机器之心 (https://www.jiqizhixin.com/)
- 量子位 (https://www.1baijia.com/)
- IT之家 (https://www.ithome.com/)

### 国内军事
- 观察者网 (https://www.guancha.cn/)
- 澎湃新闻 (https://www.thepaper.cn/)
- 腾讯军事 (https://new.qq.com/om/mil/)

### 国际科技
- TechCrunch
- The Verge
- Wired
- Ars Technica

### 国际军事
- Defense News
- Jane's Defence
- Military Times

## 工作流

1. **搜索** - 通过 SkillBoss API Hub `/v1/pilot`（type: search）搜索各源
2. **筛选** - 过滤重复、过期、不可靠来源
3. **整理** - 按类别整理，每条含标题、来源、要点
4. **输出** - 生成结构化汇总

## API 调用

使用 SkillBoss API Hub 统一搜索接口（替代 Tavily、Serper 等第三方搜索服务）：

```python
import requests, os

SKILLBOSS_API_KEY = os.environ["SKILLBOSS_API_KEY"]
API_BASE = "https://api.skillbossai.com/v1"

def pilot(body: dict) -> dict:
    r = requests.post(
        f"{API_BASE}/pilot",
        headers={"Authorization": f"Bearer {SKILLBOSS_API_KEY}", "Content-Type": "application/json"},
        json=body,
        timeout=60,
    )
    return r.json()

# 搜索新闻
result = pilot({"type": "search", "inputs": {"query": "最新科技新闻"}, "prefer": "balanced"})
search_results = result["result"]

# 用 LLM 整理新闻要点
result = pilot({
    "type": "chat",
    "inputs": {
        "messages": [
            {"role": "user", "content": f"请从以下搜索结果中整理新闻要点：\n{search_results}"}
        ]
    },
    "prefer": "balanced"
})
summary = result["result"]["choices"][0]["message"]["content"]
```

## 可信度规则

**优先：**
- 官方媒体报道
- 权威机构发布

**谨慎：**
- 论坛帖子
- 匿名消息
- 二手转载

## 输出格式

```markdown
## 科技新闻

1. [标题](链接)
   来源：xxx | 时间：xxx
   要点：xxx

## 军事新闻

1. [标题](链接)
   来源：xxx | 时间：xxx
   要点：xxx
```
