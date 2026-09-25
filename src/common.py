import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import LOG_ROOT


def check_path(path: str) -> tuple[str | None, str | None]:
    """校验 path 在白名单 LOG_ROOT 下，返回 (real_path, error)"""
    try:
        real = os.path.realpath(path)
    except (TypeError, ValueError):
        return None, f"Error: invalid path: {path}"
    if not (real == LOG_ROOT or real.startswith(LOG_ROOT + os.sep)):
        return None, f"Error: path must be under {LOG_ROOT}, got: {path}"
    return real, None


def list_log_files(real_dir: str) -> list[str]:
    """按 0.log, 1.log, ... 的顺序收集日志分片，遇到第一个缺失编号即停止"""
    paths = []
    i = 0
    while os.path.isfile(os.path.join(real_dir, f"{i}.log")):
        paths.append(os.path.join(real_dir, f"{i}.log"))
        i += 1
    return paths
