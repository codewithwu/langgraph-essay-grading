"""多提供商 LLM 客户端工厂"""

import os
from dotenv import load_dotenv
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_core.rate_limiters import InMemoryRateLimiter

load_dotenv()


# OpenAI 兼容提供商的配置映射：(显示名称, 环境变量前缀)
_OPENAI_PROVIDERS = {
    "zhipu": ("智谱", "ZHIPU"),
    "bailing": ("百灵", "LING"),
    "siliconflow": ("硅基流动", "SILICONFLOW"),
    "modelscope": ("魔塔社区", "MODELSCOPE"),
    "longcat": ("美团LongCat", "LONGCAT"),
    "deepseek": ("DeepSeek", "DEEPSEEK"),
}

rate_limiter = InMemoryRateLimiter(
    requests_per_second=0.1,  # 每秒最多 0.1 个请求（即 10 秒 1 个）
    check_every_n_seconds=0.1,  # 每 100ms 检查一次是否可以发送
    max_bucket_size=10,  # 令牌桶最大容量（突发容量）
)


class LLMFactory:
    """多提供商 LLM 客户端创建工厂"""

    def __init__(
        self,
        provider: str = "ollama",
        model_name: str | None = None,
        temperature: float = 0,
        max_tokens: int = 2000,
        timeout: int = 30,
        max_retries: int = 3,
        profile: dict | None = None,
        base_url: str | None = None,
        rate_limiter: InMemoryRateLimiter | None = None,
        logprobs: bool = False,
    ):
        self.provider = provider or os.getenv("LLM_PROVIDER", "ollama").lower()
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.max_retries = max_retries
        self.model_name = model_name
        self.profile = profile
        self.base_url = base_url
        self.rate_limiter = rate_limiter
        self.logprobs = logprobs

    def get_client(self) -> ChatOpenAI | ChatOllama | ChatNVIDIA:
        """根据配置初始化客户端"""
        if self.provider == "ollama":
            return self._setup_ollama()
        elif self.provider == "nvidia":
            return self._setup_nvidia()
        elif self.provider in _OPENAI_PROVIDERS:
            return self._setup_openai_compatible(*_OPENAI_PROVIDERS[self.provider])
        else:
            raise ValueError(f"不支持的LLM提供商: {self.provider}")

    def _setup_openai_compatible(
        self, provider_name: str, env_prefix: str
    ) -> ChatOpenAI:
        """初始化 OpenAI 兼容的客户端"""
        api_key = os.getenv(f"{env_prefix}_API_KEY")
        base_url = (
            self.base_url if self.base_url else os.getenv(f"{env_prefix}_BASEURL")
        )
        model_name = self.model_name or os.getenv(f"{env_prefix}_MODEL_NAME")

        missing = [
            k
            for k, v in [
                (f"{env_prefix}_API_KEY", api_key),
                (f"{env_prefix}_BASEURL", base_url),
                (f"{env_prefix}_MODEL_NAME", model_name),
            ]
            if not v
        ]

        if missing:
            raise ValueError(f"{provider_name} API配置缺失: {', '.join(missing)}")

        print(f"✓ 已初始化{provider_name}客户端，使用模型: {model_name}")

        return ChatOpenAI(
            model=model_name,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            timeout=self.timeout,
            api_key=api_key,
            base_url=base_url,
            max_retries=self.max_retries,
            profile=self.profile,
            rate_limiter=self.rate_limiter,
        )  # .bind(logprobs=self.logprobs)

    def _setup_ollama(self) -> ChatOllama:
        """初始化 Ollama 客户端"""
        model_name = self.model_name or os.getenv("OLLAMA_MODEL_NAME")
        base_url = self.base_url if self.base_url else os.getenv("OLLAMA_BASEURL")

        if not all([base_url, model_name]):
            raise ValueError("Ollama API配置缺失")

        print(f"✓ 已初始化Ollama客户端，使用模型: {model_name}")

        return ChatOllama(
            model=model_name,
            base_url=base_url,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            timeout=self.timeout,
        )

    def _setup_nvidia(self) -> ChatNVIDIA:
        """初始化 NVIDIA NGC 客户端"""
        api_key = os.getenv("NVIDIA_API_KEY")
        model_name = self.model_name or os.getenv("NVIDIA_MODEL_NAME")

        if not api_key:
            raise ValueError("NVIDIA_API_KEY 环境变量未设置")
        if not model_name:
            raise ValueError("NVIDIA_MODEL_NAME 环境变量未设置")

        print(f"✓ 已初始化NVIDIA客户端，使用模型: {model_name}")

        return ChatNVIDIA(
            model=model_name,
            api_key=api_key,
            temperature=self.temperature,
            max_completion_tokens=self.max_tokens,
        )
