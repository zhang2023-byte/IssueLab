"""测试 SDK 执行器的超时控制和配置"""

from unittest.mock import patch

from issuelab.sdk_executor import (
    SCENE_CONFIGS,
    AgentConfig,
    _cached_agent_options,
    clear_agent_options_cache,
    create_agent_options,
    get_agent_config_for_scene,
)


class TestAgentConfig:
    """测试 AgentConfig dataclass"""

    def test_agent_config_defaults(self):
        """AgentConfig 应该有合理的默认值"""
        config = AgentConfig()
        assert config.max_turns == 3
        assert config.max_budget_usd == 0.50
        assert config.timeout_seconds == 180

    def test_agent_config_custom_values(self):
        """AgentConfig 应该支持自定义值"""
        config = AgentConfig(
            max_turns=5,
            max_budget_usd=1.00,
            timeout_seconds=300,
        )
        assert config.max_turns == 5
        assert config.max_budget_usd == 1.00
        assert config.timeout_seconds == 300


class TestSceneConfigs:
    """测试场景配置"""

    def test_scene_configs_has_required_scenes(self):
        """SCENE_CONFIGS 应该包含必需的场景"""
        assert "quick" in SCENE_CONFIGS
        assert "review" in SCENE_CONFIGS
        assert "deep" in SCENE_CONFIGS

    def test_quick_config_is_restrictive(self):
        """quick 配置应该更严格"""
        quick = SCENE_CONFIGS["quick"]
        review = SCENE_CONFIGS["review"]
        assert quick.max_turns <= review.max_turns
        assert quick.max_budget_usd <= review.max_budget_usd
        assert quick.timeout_seconds <= review.timeout_seconds

    def test_deep_config_is_permissive(self):
        """deep 配置应该更宽松"""
        deep = SCENE_CONFIGS["deep"]
        review = SCENE_CONFIGS["review"]
        assert deep.max_turns >= review.max_turns
        assert deep.max_budget_usd >= review.max_budget_usd
        assert deep.timeout_seconds >= review.timeout_seconds


class TestCreateAgentOptionsWithTimeout:
    """测试 create_agent_options 的超时控制"""

    def test_create_agent_options_has_max_turns(self):
        """create_agent_options 应该支持 max_turns 参数"""
        options = create_agent_options(max_turns=5)
        assert options.max_turns == 5

    def test_create_agent_options_has_max_budget_usd(self):
        """create_agent_options 应该支持 max_budget_usd 参数"""
        options = create_agent_options(max_budget_usd=1.00)
        assert options.max_budget_usd == 1.00

    def test_create_agent_options_uses_default_max_turns(self):
        """create_agent_options 应该使用默认的 max_turns"""
        options = create_agent_options()
        assert options.max_turns == 3  # 默认值

    def test_create_agent_options_uses_default_max_budget_usd(self):
        """create_agent_options 应该使用默认的 max_budget_usd"""
        options = create_agent_options()
        assert options.max_budget_usd == 0.50  # 默认值


class TestEnvOptimization:
    """测试环境变量优化"""

    @patch("issuelab.config.Config.get_anthropic_env")
    def test_skip_version_check_env(self, mock_env):
        """应该设置跳过版本检查的环境变量"""
        mock_env.return_value = {}
        options = create_agent_options()
        assert "CLAUDE_AGENT_SDK_SKIP_VERSION_CHECK" in options.env
        assert options.env["CLAUDE_AGENT_SDK_SKIP_VERSION_CHECK"] == "true"


class TestCaching:
    """测试 Agent 选项缓存机制"""

    def test_clear_cache_function_exists(self):
        """clear_agent_options_cache 函数应该存在"""
        assert callable(clear_agent_options_cache)

    def test_cached_agent_options_function_exists(self):
        """_cached_agent_options 缓存字典应该存在"""
        # _cached_agent_options 是一个字典，不是函数
        assert isinstance(_cached_agent_options, dict)

    def test_cache_can_be_cleared(self):
        """应该能够清除缓存"""
        # 先调用一次
        options1 = create_agent_options()
        # 清除缓存
        clear_agent_options_cache()
        # 再次调用应该正常工作
        options2 = create_agent_options()
        assert options1 is not None
        assert options2 is not None

    def test_get_agent_config_for_scene(self):
        """get_agent_config_for_scene 应该返回正确的配置"""
        quick = get_agent_config_for_scene("quick")
        assert quick.max_turns == SCENE_CONFIGS["quick"].max_turns

        review = get_agent_config_for_scene("review")
        assert review.max_turns == SCENE_CONFIGS["review"].max_turns

    def test_get_agent_config_for_scene_defaults_to_review(self):
        """get_agent_config_for_scene 未知场景应该返回 review 配置"""
        config = get_agent_config_for_scene("unknown_scene")
        assert config.max_turns == SCENE_CONFIGS["review"].max_turns
