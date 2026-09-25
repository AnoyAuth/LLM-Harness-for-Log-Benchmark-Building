import os

BASE = os.path.dirname(os.path.abspath(__file__))

# Root directory of the sharded log datasets: <LOG_ROOT>/<log>/{0,1,2,...}.log
# The agent is sandboxed to this directory.
LOG_ROOT = os.path.realpath(os.environ.get("LOG_ROOT", os.path.join(BASE, "logs")))

# Token-boundary counter binary (built by `make`)
COUNTER_BIN = os.path.join(BASE, "src", "O", "counter")

METADATA_PATH = os.path.join(BASE, "MetaData.json")
EXAMPLE_PATH = os.path.join(BASE, "category", "example.json")
CATEGORY_DIR = os.path.join(BASE, "category")
RUNTIME_LOG_DIR = os.path.join(BASE, "runtime-log")
BENCHMARK_PATH = os.path.join(BASE, "benchmark.json")

# Any OpenAI-compatible endpoint works; defaults are the ones used for the paper.
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.deepseek.com")
LLM_MODEL = os.environ.get("LLM_MODEL", "deepseek-v4-flash")
LLM_REASONING_EFFORT = os.environ.get("LLM_REASONING_EFFORT", "high")

# Hard cap of LLM turns per category (the prompt tells the agent it has 30)
MAX_TURNS = 40

# Thread pool size used by count_query / sample_logs / search_file
NUM_THREADS = 20
