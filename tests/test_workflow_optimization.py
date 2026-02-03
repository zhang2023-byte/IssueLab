"""测试 GitHub Actions 工作流配置"""

from pathlib import Path

import pytest


class TestWorkflowFiles:
    """测试工作流文件配置"""

    def test_orchestrator_workflow_exists(self):
        """orchestrator.yml 工作流应该存在"""
        workflow_dir = Path(__file__).parent.parent / ".github" / "workflows"
        workflow_file = workflow_dir / "orchestrator.yml"
        assert workflow_file.exists(), f"工作流文件不存在: {workflow_file}"

    def test_orchestrator_workflow_has_timeout(self):
        """orchestrator.yml 应该设置 timeout-minutes"""
        workflow_dir = Path(__file__).parent.parent / ".github" / "workflows"
        workflow_file = workflow_dir / "orchestrator.yml"

        if not workflow_file.exists():
            pytest.skip("工作流文件不存在")

        content = workflow_file.read_text()
        assert "timeout-minutes:" in content, "工作流应该设置 timeout-minutes"

    def test_orchestrator_workflow_has_uv_cache(self):
        """orchestrator.yml 应该启用 uv 缓存"""
        workflow_dir = Path(__file__).parent.parent / ".github" / "workflows"
        workflow_file = workflow_dir / "orchestrator.yml"

        if not workflow_file.exists():
            pytest.skip("工作流文件不存在")

        content = workflow_file.read_text()
        assert "enable-cache: true" in content or "enable-cache: true" in content.replace(
            " ", ""
        ), "工作流应该启用 uv 缓存"

    def test_orchestrator_workflow_sets_skip_version_check(self):
        """orchestrator.yml 应该设置 CLAUDE_AGENT_SDK_SKIP_VERSION_CHECK"""
        workflow_dir = Path(__file__).parent.parent / ".github" / "workflows"
        workflow_file = workflow_dir / "orchestrator.yml"

        if not workflow_file.exists():
            pytest.skip("工作流文件不存在")

        content = workflow_file.read_text()
        assert (
            "CLAUDE_AGENT_SDK_SKIP_VERSION_CHECK" in content
        ), "工作流应该设置 CLAUDE_AGENT_SDK_SKIP_VERSION_CHECK 环境变量"


class TestEnvironmentVariables:
    """测试环境变量配置"""

    def test_skip_version_check_env_is_true(self):
        """CLAUDE_AGENT_SDK_SKIP_VERSION_CHECK 应该设置为 true"""
        from issuelab.sdk_executor import create_agent_options

        options = create_agent_options()
        assert "CLAUDE_AGENT_SDK_SKIP_VERSION_CHECK" in options.env
        assert options.env["CLAUDE_AGENT_SDK_SKIP_VERSION_CHECK"] == "true"

    def test_default_agent_config(self):
        """默认 AgentConfig 应该符合预期"""
        from issuelab.sdk_executor import AgentConfig

        config = AgentConfig()
        assert config.max_turns == 3
        assert config.max_budget_usd == 0.50
        assert config.timeout_seconds == 180
