"""SDK 执行器：使用 Claude Agent SDK 构建评审代理

本模块已重构为多个子模块，此文件作为统一导出入口保持向后兼容。

新的模块结构：
- agents/config.py: 配置管理
- agents/discovery.py: Agent 发现
- agents/parsers.py: 响应解析
- agents/options.py: SDK 选项构建
- agents/executor.py: 执行核心
- agents/observer.py: Observer 专用逻辑
"""

# 从子模块导入所有公共 API
from issuelab.agents.config import (
    SCENE_CONFIGS,
    AgentConfig,
    get_agent_config_for_scene,
)
from issuelab.agents.discovery import (
    discover_agents,
    get_agent_matrix_markdown,
    load_prompt,
    parse_agent_metadata,
)
from issuelab.agents.executor import (
    run_agents_parallel,
    run_single_agent,
)
from issuelab.agents.observer import (
    build_papers_for_observer,
    run_observer,
    run_observer_batch,
    run_observer_for_papers,
)
from issuelab.agents.options import (
    clear_agent_options_cache,
    create_agent_options,
)
from issuelab.agents.parsers import (
    parse_observer_response,
    parse_papers_recommendation,
)

__all__ = [
    # Config
    "AgentConfig",
    "SCENE_CONFIGS",
    "get_agent_config_for_scene",
    # Discovery
    "discover_agents",
    "get_agent_matrix_markdown",
    "load_prompt",
    "parse_agent_metadata",
    # Executor
    "run_single_agent",
    "run_agents_parallel",
    # Observer
    "run_observer",
    "run_observer_batch",
    "run_observer_for_papers",
    "build_papers_for_observer",
    # Options
    "create_agent_options",
    "clear_agent_options_cache",
    # Parsers
    "parse_observer_response",
    "parse_papers_recommendation",
]
