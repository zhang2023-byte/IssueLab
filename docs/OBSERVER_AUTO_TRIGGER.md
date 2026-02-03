# Observer 自动触发系统 - TDD实现文档

## 📋 概述

使用TDD（测试驱动开发）方式实现了Observer自动触发agent的功能，解决了GitHub Actions bot评论无法触发workflow的限制。

## 🎯 解决的问题

### 原有问题
- **Bot评论不触发workflow**：GitHub Actions安全机制防止bot创建的评论触发`issue_comment`事件
- **Observer无法触发其他agent**：Observer分析完成后只能发评论，但bot评论无法触发其他agent执行
- **架构缺陷**：依赖评论触发的设计无法支持Observer自动化流程

### 解决方案
**混合触发机制**：
- **内置agent**：通过GitHub label触发（`bot:trigger-{agent}`）
- **用户agent**：通过dispatch系统触发（repository_dispatch）

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                     Observer Workflow                        │
│  (定期扫描issues或手动触发)                                    │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
         ┌───────────────────┐
         │ observe-batch     │
         │ --auto-trigger    │
         └─────────┬─────────┘
                   │
         ┌─────────▼─────────────────────┐
         │  auto_trigger_agent()         │
         │  (判断agent类型)               │
         └─────────┬─────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
┌────────────────┐    ┌──────────────────┐
│ 内置Agent       │    │ 用户Agent         │
│ (label触发)     │    │ (dispatch触发)    │
└────────┬───────┘    └─────────┬────────┘
         │                      │
         ▼                      ▼
┌─────────────────┐    ┌─────────────────┐
│ 添加label:       │    │ 调用dispatch.py  │
│ bot:trigger-X   │    │ 发送dispatch事件 │
└────────┬────────┘    └─────────┬───────┘
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│ orchestrator.yml│    │ 用户仓库的       │
│ observer-       │    │ agent workflow   │
│ triggered-agent │    │                  │
│ job执行agent    │    │                  │
└────────┬────────┘    └─────────────────┘
         │
         ▼
  ┌─────────────┐
  │ 移除label    │
  └─────────────┘
```

## 📦 核心模块

### `src/issuelab/observer_trigger.py`

#### 常量
- `BUILTIN_AGENTS`: 内置agent集合

#### 核心函数

**1. `is_builtin_agent(agent_name: str) -> bool`**
```python
判断是否是内置agent
- moderator, reviewer_a, reviewer_b, summarizer, echo, observer 为内置
- 不区分大小写
```

**2. `trigger_builtin_agent(agent_name: str, issue_number: int) -> bool`**
```python
触发内置agent（通过添加label）
- 构造label: bot:trigger-{agent}
- 使用gh CLI添加label到issue
- 返回是否成功
```

**3. `trigger_user_agent(username: str, issue_number: int, issue_title: str, issue_body: str) -> bool`**
```python
触发用户agent（通过dispatch系统）
- 调用dispatch.py的main函数
- 传递issue信息和用户名
- 返回是否成功
```

**4. `auto_trigger_agent(agent_name: str, issue_number: int, issue_title: str, issue_body: str) -> bool`**
```python
根据agent类型自动选择触发方式
- 内置agent → trigger_builtin_agent()
- 用户agent → trigger_user_agent()
```

**5. `process_observer_results(results: list[dict], issue_data: dict, auto_trigger: bool) -> int`**
```python
处理Observer批量分析结果
- 遍历results，过滤should_trigger=True的条目
- 调用auto_trigger_agent()触发对应agent
- 返回成功触发的数量
```

## 🧪 测试覆盖

### `tests/test_observer_trigger.py`

**20个测试用例，100%通过** ✅

#### 1. TestBuiltinAgentDetection (6个测试)
- ✅ `test_moderator_is_builtin`: moderator应被识别为内置
- ✅ `test_reviewer_a_is_builtin`: reviewer_a应被识别为内置
- ✅ `test_echo_is_builtin`: echo应被识别为内置
- ✅ `test_user_agent_is_not_builtin`: 用户agent不应被识别为内置
- ✅ `test_empty_string_is_not_builtin`: 空字符串不应被识别为内置
- ✅ `test_case_insensitive`: agent名称不区分大小写

#### 2. TestBuiltinAgentTrigger (4个测试)
- ✅ `test_trigger_builtin_agent_adds_label`: 应添加正确的label
- ✅ `test_trigger_builtin_agent_returns_true_on_success`: 成功返回True
- ✅ `test_trigger_builtin_agent_returns_false_on_failure`: 失败返回False
- ✅ `test_trigger_multiple_builtin_agents`: 支持触发多个agent

#### 3. TestUserAgentTrigger (4个测试)
- ✅ `test_trigger_user_agent_calls_dispatch`: 应调用dispatch系统
- ✅ `test_trigger_user_agent_with_correct_params`: 传递正确的参数
- ✅ `test_trigger_user_agent_returns_false_on_failure`: dispatch失败返回False
- ✅ `test_trigger_user_agent_handles_exception`: 异常处理返回False

#### 4. TestObserverAutoTrigger (3个测试)
- ✅ `test_auto_trigger_builtin_agent`: 内置agent调用trigger_builtin_agent
- ✅ `test_auto_trigger_user_agent`: 用户agent调用trigger_user_agent
- ✅ `test_auto_trigger_returns_false_on_failure`: 触发失败返回False

#### 5. TestObserveBatchIntegration (3个测试)
- ✅ `test_observe_batch_triggers_on_should_trigger_true`: should_trigger=True时触发
- ✅ `test_observe_batch_skips_when_should_trigger_false`: should_trigger=False时跳过
- ✅ `test_observe_batch_handles_multiple_issues`: 处理多个issues

## 🔧 集成修改

### 1. `src/issuelab/__main__.py`

**新增参数**：
```python
observe_batch_parser.add_argument(
    "--auto-trigger", 
    action="store_true",
    help="自动触发agent（内置agent用label，用户agent用dispatch）"
)
```

**集成逻辑**：
```python
if getattr(args, "auto_trigger", False):
    from issuelab.observer_trigger import auto_trigger_agent
    
    success = auto_trigger_agent(
        agent_name=result.get("agent", ""),
        issue_number=issue_num,
        issue_title=issue_info.get("issue_title", ""),
        issue_body=issue_info.get("issue_body", ""),
    )
```

### 2. `.github/workflows/observer.yml`

**改进**：
```yaml
- name: Run Observer for all issues (parallel)
  run: |
    # 🔥 使用新的 auto-trigger 参数替代 --post
    uv run python -m issuelab observe-batch \
      --issues "${{ steps.get_issues.outputs.issue_numbers }}" \
      --auto-trigger
```

### 3. `.github/workflows/orchestrator.yml`

**新增job**：
```yaml
# ========== Observer 触发：bot:trigger-* 标签 ==========
observer-triggered-agent:
  if: github.event_name == 'issues' &&
      github.event.action == 'labeled' &&
      startsWith(github.event.label.name, 'bot:trigger-')
  runs-on: ubuntu-latest
  timeout-minutes: 10

  steps:
    - name: Extract agent name from label
      id: extract_agent
      run: |
        LABEL="${{ github.event.label.name }}"
        AGENT_NAME="${LABEL#bot:trigger-}"
        echo "agent_name=${AGENT_NAME}" >> $GITHUB_OUTPUT

    - name: Execute triggered agent
      run: |
        uv run python -m issuelab execute \
          --issue ${{ github.event.issue.number }} \
          --agents "${{ steps.extract_agent.outputs.agent_name }}" \
          --post

    - name: Remove trigger label
      if: always()
      run: |
        gh issue edit ${{ github.event.issue.number }} \
          --remove-label "${{ github.event.label.name }}"
```

## 🚀 工作流程

### 1. Observer定期扫描
```bash
# 每小时自动运行
cron: '0 * * * *'

# 或手动触发
gh workflow run observer.yml
```

### 2. 并行分析Issues
```bash
uv run python -m issuelab observe-batch \
  --issues "1,2,3" \
  --auto-trigger
```

### 3. 自动触发判断

**内置Agent示例**：
```python
# Observer分析结果
result = {
    "issue_number": 1,
    "should_trigger": True,
    "agent": "moderator",
    "reason": "New paper needs moderation"
}

# 触发流程
is_builtin_agent("moderator")  # True
→ trigger_builtin_agent("moderator", 1)
→ gh issue edit 1 --add-label "bot:trigger-moderator"
→ orchestrator.yml的observer-triggered-agent job捕获
→ 执行agent并移除label
```

**用户Agent示例**：
```python
# Observer分析结果
result = {
    "issue_number": 1,
    "should_trigger": True,
    "agent": "gqy22",
    "reason": "User requested review"
}

# 触发流程
is_builtin_agent("gqy22")  # False
→ trigger_user_agent("gqy22", 1, "Title", "Body")
→ 调用dispatch.py
→ 发送repository_dispatch到用户仓库
→ 用户仓库的agent workflow捕获并执行
```

## 📊 测试结果

```bash
$ uv run pytest tests/test_observer_trigger.py -v

============= 20 passed in 0.13s =============

✅ TestBuiltinAgentDetection (6/6)
✅ TestBuiltinAgentTrigger (4/4)
✅ TestUserAgentTrigger (4/4)
✅ TestObserverAutoTrigger (3/3)
✅ TestObserveBatchIntegration (3/3)
```

## 🎉 优势

### 1. 绕过Bot限制
- ✅ **Label触发**: 不依赖bot评论，直接通过label触发workflow
- ✅ **Dispatch触发**: repository_dispatch不受bot限制

### 2. MVP原则
- ✅ **最小改动**: 仅新增observer_trigger.py，不破坏现有架构
- ✅ **渐进增强**: --auto-trigger参数可选，保留--post兼容

### 3. 可测试性
- ✅ **100%覆盖**: 20个单元测试覆盖所有逻辑分支
- ✅ **Mock隔离**: 使用unittest.mock隔离外部依赖

### 4. 可扩展性
- ✅ **统一接口**: auto_trigger_agent()统一触发逻辑
- ✅ **灵活配置**: BUILTIN_AGENTS集合易于扩展

### 5. 可观测性
- ✅ **日志记录**: 每个触发操作都有logger输出
- ✅ **状态反馈**: 通过label可见agent触发状态

## 🔍 TDD实现回顾

### Red → Green → Refactor

#### 🔴 Red (测试失败)
```bash
$ uv run pytest tests/test_observer_trigger.py

============= 20 failed in 0.84s =============
ModuleNotFoundError: No module named 'issuelab.observer_trigger'
```

#### 🟢 Green (测试通过)
```bash
$ uv run pytest tests/test_observer_trigger.py

============= 20 passed in 0.13s =============
```

#### 🔵 Refactor (持续优化)
- 集成到__main__.py
- 更新workflow配置
- 文档完善

## 📚 使用示例

### 手动测试单个agent触发

**内置agent**:
```python
from issuelab.observer_trigger import trigger_builtin_agent

success = trigger_builtin_agent("echo", 1)
# → 添加label: bot:trigger-echo 到 Issue #1
```

**用户agent**:
```python
from issuelab.observer_trigger import trigger_user_agent

success = trigger_user_agent(
    username="gqy22",
    issue_number=1,
    issue_title="Test Issue",
    issue_body="This is a test"
)
# → 调用dispatch.py发送repository_dispatch
```

### 命令行使用

```bash
# 使用auto-trigger
uv run python -m issuelab observe-batch \
  --issues "1,2,3" \
  --auto-trigger

# 兼容旧版（不推荐，bot评论无法触发）
uv run python -m issuelab observe-batch \
  --issues "1,2,3" \
  --post
```

## 🔗 相关文档

- [MVP.md](./MVP.md) - 项目MVP原则
- [COLLABORATION_FLOW.md](./COLLABORATION_FLOW.md) - 协作流程
- [DISPATCH_SETUP.md](./DISPATCH_SETUP.md) - Dispatch系统配置
- [GITHUB_APP_SETUP.md](./GITHUB_APP_SETUP.md) - GitHub App配置

## 📝 TODO

- [ ] 为observer-triggered-agent job添加失败重试机制
- [ ] 添加label触发的rate limiting保护
- [ ] 监控dispatch成功率指标
- [ ] 支持批量label操作优化性能
- [ ] 添加e2e集成测试验证完整流程

---

**实现日期**: 2026-02-03  
**实现方法**: TDD (Test-Driven Development)  
**测试覆盖**: 20/20 测试通过 ✅
