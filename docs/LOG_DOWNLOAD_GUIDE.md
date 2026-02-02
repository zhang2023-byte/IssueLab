# 日志下载和查看指南

## 📥 日志导出功能

IssueLab 现在为所有 workflow 运行提供完整的日志导出功能，方便开发者和用户调试问题。

## 🎯 日志覆盖范围

### 1. **Orchestrator Workflow** (`orchestrator.yml`)
- `/review` 命令执行日志：`review_<issue_number>.log`
- `/triage` 命令执行日志：`triage_<issue_number>.log`
- `/summarize` 命令执行日志：`summarize_<issue_number>.log`
- 自动评审触发日志：`auto_review_<issue_number>.log`

### 2. **Dispatch Agents Workflow** (`dispatch_agents.yml`)
- Agent dispatch 过程日志：`dispatch_<issue_number>.log`
- 包含 GitHub App 认证、token 生成、dispatch 请求等详细信息

### 3. **Observer Workflow** (`observer.yml`)
- 自动扫描和分析日志：`observer_<run_id>.log`
- 包含 Issue 扫描、分析决策、触发建议等

### 4. **User Agent Workflow** (`user_agent.yml`)
- 用户 fork 仓库中的 agent 执行日志
- 文件名：`user-agent-logs-<issue_number>-<run_id>`

## 📂 如何下载日志

### 方法一：GitHub Actions 网页界面

1. 访问 [Actions 页面](https://github.com/gqy20/IssueLab/actions)
2. 点击你想查看的 workflow 运行
3. 滚动到页面底部的 **Artifacts** 区域
4. 点击日志文件名下载（ZIP 格式）

### 方法二：使用 GitHub CLI

```bash
# 列出最近的运行
gh run list --limit 10

# 下载特定运行的 artifacts
gh run download <run-id>

# 下载所有 artifacts 到指定目录
gh run download <run-id> -D ./logs

# 查看运行详情
gh run view <run-id>
```

### 方法三：使用 REST API

```bash
# 获取 artifacts 列表
curl -H "Authorization: token YOUR_TOKEN" \
  https://api.github.com/repos/gqy20/IssueLab/actions/runs/<run-id>/artifacts

# 下载 artifact
curl -L -H "Authorization: token YOUR_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/gqy20/IssueLab/actions/artifacts/<artifact-id>/zip \
  -o logs.zip
```

## 📊 日志格式

### 日志条目格式
```
2026-02-02 15:30:35,654 - issuelab.issuelab.sdk_executor - INFO - [sdk_executor.py:381] - 开始运行 agent: moderator
```

**字段说明：**
- **时间戳**：`2026-02-02 15:30:35,654`
- **模块名**：`issuelab.issuelab.sdk_executor`
- **日志级别**：`INFO` (DEBUG/INFO/WARNING/ERROR)
- **位置**：`[sdk_executor.py:381]`（文件名和行号）
- **消息**：具体的日志内容

### 日志级别说明

| 级别 | 用途 | 包含内容 |
|------|------|---------|
| **DEBUG** | 详细调试信息 | API 调用、参数传递、中间状态 |
| **INFO** | 常规信息 | Agent 开始/完成、主要步骤 |
| **WARNING** | 警告信息 | 重试操作、非致命错误 |
| **ERROR** | 错误信息 | 执行失败、异常堆栈 |

## 🔍 常见问题排查

### 1. Agent 执行失败
**查看日志位置**：`logs/review_<issue_number>.log` 或 `logs/triage_<issue_number>.log`

**关键信息**：
- Agent 启动时间
- API 调用记录
- 错误堆栈信息
- Claude SDK 的详细输出

### 2. Dispatch 失败
**查看日志位置**：`logs/dispatch_<issue_number>.log`

**关键信息**：
- GitHub App token 生成是否成功
- 目标仓库识别是否正确
- Dispatch 请求响应状态
- 失败原因代码（403/404 等）

### 3. Observer 没有触发
**查看日志位置**：`logs/observer_<run_id>.log`

**关键信息**：
- Issue 扫描结果
- 触发条件判断
- 决策过程记录

## 🗄️ 日志保留策略

- **保留时间**：7 天
- **自动清理**：7 天后 GitHub 会自动删除 artifacts
- **大小限制**：单个 artifact 最大 10GB
- **数量限制**：总共最多 1GB 或 30 天的 artifacts（根据 GitHub 计划）

## 💡 最佳实践

### 1. 下载前先查看
在下载完整日志前，可以先在 GitHub Actions 页面查看控制台输出，判断是否需要详细日志。

### 2. 定期清理
对于调试完成的问题，不需要保留超过 7 天的日志。

### 3. 关键日志备份
对于重要的调试案例，建议在 7 天内下载并本地备份关键日志。

### 4. 使用 grep 过滤
```bash
# 查找错误信息
grep -i "error" logs/*.log

# 查找特定 agent 的日志
grep "agent: moderator" logs/*.log

# 查找 API 调用
grep "Anthropic API" logs/*.log
```

### 5. 组合分析
对于复杂问题，可能需要同时查看多个日志文件：
- `dispatch_<issue>.log`：了解 dispatch 过程
- `review_<issue>.log`：了解评审执行
- GitHub Actions 控制台：了解整体流程

## 📧 问题反馈

如果遇到日志相关问题，请提供：
1. **Run ID**：GitHub Actions 运行 ID
2. **Issue Number**：相关的 Issue 编号
3. **时间戳**：问题发生的大致时间
4. **错误信息**：关键的错误日志片段

提交 Issue 时附上日志文件可以大大加快问题诊断速度。

## 🔗 相关资源

- [GitHub Actions Artifacts 文档](https://docs.github.com/en/actions/using-workflows/storing-workflow-data-as-artifacts)
- [GitHub CLI 下载指南](https://cli.github.com/manual/gh_run_download)
- [IssueLab 架构文档](./ARCHITECTURE.md)
- [日志配置代码](../src/issuelab/logging_config.py)
