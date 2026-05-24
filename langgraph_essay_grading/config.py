"""配置"""

from dotenv import load_dotenv

load_dotenv()

LLM_PROVIDER = "bailing"

# 各维度权重
WEIGHT_RELEVANCE = 0.3
WEIGHT_EVIDENCE = 0.2
WEIGHT_STRUCTURE = 0.2
WEIGHT_EXPRESSION = 0.3

# 条件短路阈值
RELEVANCE_THRESHOLD = 0.5
