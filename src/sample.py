import random
from concurrent.futures import ThreadPoolExecutor

from common import check_path, list_log_files
from config import NUM_THREADS


def _sample_one(path: str, line: int) -> str:
    with open(path, errors="replace") as f:
        lines = f.readlines()
    if not lines:
        return ""
    start = random.randint(0, len(lines) - 1)
    return "".join(lines[start:start + line])


def sample(logpath: str, line=10) -> str:
    """从每个日志分片中随机采样连续的 line 行"""
    real, err = check_path(logpath)
    if err:
        return err

    paths = list_log_files(real)
    if not paths:
        return ""

    with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        return "".join(executor.map(lambda p: _sample_one(p, line), paths))
