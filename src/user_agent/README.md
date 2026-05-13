# User Agent 模块

最小可用的 user agent 接口实现，负责：
- 从 `data/` 读取 profile/episode/task 配置
- 提供 task 的 initial user message
- 根据 agent 回复给出下一步 action（继续对话或终止）

当前版本简介：
- 仅暴露最小接口：构造函数、`initial_user_message`、`next_action`
- 终止/追问判定通过 LLM 完成；用户回复直接由 hidden intent 内容构造
- 每个 task 的对话历史会写入 `outputs/{safe_model_id}/{user_id}/{task_id}/history/`（JSONL）
- 支持 `TerminalUserAgent`：`/quit` 结束当前 task，`/exit` 结束整个 benchmark

模块结构：
- `base.py`：抽象父类与动作协议（`UserAgentAction`）
- `src/data/models.py`：数据模型
- `src/data/repository.py`：本地数据读取
- `user_agent.py`：LLM user agent（构造/initial/next_action）
- `terminal_user_agent.py`：终端输入 user agent（next_action 由人工输入）
- `src/llm/llm_client.py`：真实 API 调用（async，内置 retry/backoff）
- `prompts/`：hidden intent 判断 / 回复模板（不在本地 task 数据中存储）

环境变量示例见 `env/openai.example.sh`。

---
## 接口说明（对应测试用法）

### 1) 构造函数
```python
agent = UserAgent(user_root="data/user_003")
```
- `user_root`：指向单个用户目录（如 `data/user_003`）
- 可额外传 `model_id` 与 `output_root` 控制日志输出目录
- 初始化时会读取 `profile.yaml`、`episode.yaml` 与 `tasks/*/task.yaml`
- 默认使用 `LLMClient`（需环境变量配置）

### 2) initial_user_message
```python
msg = agent.initial_user_message(task_id="user_003_task_003")
```
- 作用：启动 task，返回 initial user message
- 传 `None` 时按 `episode.task_order` 选择下一个 task
- 会重置内部历史，并创建 `{output_root}/{model_id}/{user_id}/{task_id}/history/{YYYYMMDD_HHMMSS}-messages.jsonl`

### 3) next_action
```python
action = await agent.next_action(agent_response="...")
```
- 输入：待测 agent 的回复
- 输出：`UserAgentAction`
  - `type == "message"`：继续交互，`message` 为用户回复
  - `type == "terminate"`：终止本 task
- 内部流程：先判断 latest assistant response 是否满足 hidden intent，再判断是否存在明确打到点上的追问，最后按状态生成用户回复

---
## data/（输入数据）结构

用户目录示例：
```
data/
  user_003/
    profile.yaml
    episode.yaml
    tasks/
      user_003_task_003/
        task.yaml
```

关键文件：
- `profile.yaml`：用户画像（Role/Preferences/Goals）
- `episode.yaml`：episode 级别任务编排（`task_order`）
- `tasks/*/task.yaml`：任务定义（title/description/intent/objectives/metadata 等）

---
## outputs/（history 输出）结构

每个 task 的历史写入：
```
outputs/
  {model_id}/
    user_003/
      user_003_task_003/
        history/
          {YYYYMMDD_HHMMSS}-messages.jsonl
          {YYYYMMDD_HHMMSS}-user.jsonl
          {YYYYMMDD_HHMMSS}-log.jsonl
```

JSONL 每行结构：
```json
{"task_id":"user_003_task_003","agent_id":"test_agent","round":1,"role":"user","message":"...","timestamp":1710000000.0}
```

字段说明：
- `task_id`：任务 id
- `agent_id`：被测 agent 的 id
- `round`：该 task 内的交互轮次（从 1 开始，逐条递增）
- `role`：`user` 或 `assistant`
- `message`：该轮消息内容
- `timestamp`：写入时的 Unix 时间戳（秒）
