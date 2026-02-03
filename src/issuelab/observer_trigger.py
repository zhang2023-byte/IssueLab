"""
Observer 自动触发功能

实现Observer自动触发agent的核心逻辑：
- 内置agent通过GitHub label触发
- 用户agent通过dispatch系统触发
"""

import logging
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# 内置agent列表
BUILTIN_AGENTS = {
    "moderator",
    "reviewer_a",
    "reviewer_b",
    "summarizer",
    "echo",
    "observer",
}


def is_builtin_agent(agent_name: str) -> bool:
    """
    判断是否是内置agent

    Args:
        agent_name: Agent名称

    Returns:
        True: 内置agent
        False: 用户agent
    """
    if not agent_name:
        return False
    return agent_name.lower() in BUILTIN_AGENTS


def trigger_builtin_agent(agent_name: str, issue_number: int) -> bool:
    """
    触发内置agent（通过添加label）

    Args:
        agent_name: Agent名称
        issue_number: Issue编号

    Returns:
        True: 触发成功
        False: 触发失败
    """
    label = f"bot:trigger-{agent_name.lower()}"

    try:
        subprocess.run(
            ["gh", "issue", "edit", str(issue_number), "--add-label", label],
            check=True,
            capture_output=True,
            text=True,
        )
        logger.info(f"✅ 已为 #{issue_number} 添加label: {label}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ 添加label失败: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"❌ 触发内置agent失败: {e}")
        return False


def trigger_user_agent(username: str, issue_number: int, issue_title: str, issue_body: str) -> bool:
    """
    触发用户agent（通过dispatch系统）

    Args:
        username: 用户名
        issue_number: Issue编号
        issue_title: Issue标题
        issue_body: Issue内容

    Returns:
        True: 触发成功
        False: 触发失败
    """
    try:
        # 调用dispatch.py的main函数
        from issuelab.cli.dispatch import main as dispatch_main

        # 模拟命令行参数
        sys.argv = [
            "dispatch",
            "--issue-number",
            str(issue_number),
            "--issue-title",
            issue_title,
            "--issue-body",
            issue_body,
            "--mentions",
            username,
        ]

        exit_code = dispatch_main()
        if exit_code == 0:
            logger.info(f"✅ 已触发用户agent: {username} for #{issue_number}")
            return True
        else:
            logger.error(f"❌ 触发用户agent失败: {username} (exit_code={exit_code})")
            return False

    except Exception as e:
        logger.error(f"❌ 触发用户agent异常: {e}")
        return False


def auto_trigger_agent(agent_name: str, issue_number: int, issue_title: str, issue_body: str) -> bool:
    """
    根据agent类型自动选择触发方式

    Args:
        agent_name: Agent名称
        issue_number: Issue编号
        issue_title: Issue标题
        issue_body: Issue内容

    Returns:
        True: 触发成功
        False: 触发失败
    """
    if is_builtin_agent(agent_name):
        return trigger_builtin_agent(agent_name, issue_number)
    else:
        return trigger_user_agent(agent_name, issue_number, issue_title, issue_body)


def process_observer_results(
    results: list[dict], issue_data: dict[int, dict], auto_trigger: bool = True
) -> int:
    """
    处理Observer批量分析结果，自动触发agent

    Args:
        results: Observer分析结果列表
        issue_data: Issue数据字典 {issue_number: {title, body}}
        auto_trigger: 是否自动触发

    Returns:
        成功触发的agent数量
    """
    if not auto_trigger:
        return 0

    triggered_count = 0

    for result in results:
        if not result.get("should_trigger", False):
            continue

        issue_number = result["issue_number"]
        agent_name = result.get("agent")

        if not agent_name:
            logger.warning(f"⚠️ Issue #{issue_number} 缺少agent名称")
            continue

        if issue_number not in issue_data:
            logger.warning(f"⚠️ Issue #{issue_number} 缺少数据")
            continue

        issue = issue_data[issue_number]
        success = auto_trigger_agent(
            agent_name=agent_name,
            issue_number=issue_number,
            issue_title=issue.get("title", ""),
            issue_body=issue.get("body", ""),
        )

        if success:
            triggered_count += 1

    logger.info(f"📊 总计触发 {triggered_count} 个agent")
    return triggered_count
