import os
import re
from concurrent.futures import ThreadPoolExecutor

from common import check_path, list_log_files
from config import NUM_THREADS


def _search_one(path: str, pattern: re.Pattern, limit: int) -> list[str]:
    """从单文件中搜索匹配的完整日志行，最多返回 limit 条。"""
    try:
        with open(path, "r", errors="replace") as f:
            matched = []
            for line in f:
                if len(matched) >= limit:
                    break
                if pattern.search(line):
                    matched.append(line)
            return matched
    except (PermissionError, OSError):
        return []


def search(logpath: str, regex: str, maximum=100) -> str:
    real, err = check_path(logpath)
    if err:
        return err

    if not os.path.isdir(real):
        return f"Error: not a directory: {logpath}"

    try:
        pattern = re.compile(regex)
    except re.error as e:
        return f"Error: invalid regex: {e}"

    paths = list_log_files(real)
    if not paths:
        return f"(no .log files in {logpath})"

    # 分批处理：每批 NUM_THREADS 个文件并行，命中 maximum 则提前退出
    all_matched = []

    for start in range(0, len(paths), NUM_THREADS):
        batch = paths[start:start + NUM_THREADS]
        remaining = maximum - len(all_matched)

        with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
            batch_results = list(executor.map(
                lambda p: _search_one(p, pattern, remaining), batch
            ))

        for lines in batch_results:
            all_matched.extend(lines)
            if len(all_matched) >= maximum:
                break

        if len(all_matched) >= maximum:
            break

    all_matched = all_matched[:maximum]

    if not all_matched:
        return f"(no lines matched /{regex}/ in {logpath})"
    return "".join(all_matched)
