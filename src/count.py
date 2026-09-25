import json
import subprocess
from concurrent.futures import ThreadPoolExecutor

from common import check_path, list_log_files
from config import COUNTER_BIN, NUM_THREADS


def _count_one(path: str, query: str) -> int:
    result = subprocess.run(
        [COUNTER_BIN],
        input=f"{path}\n{query}\n",
        capture_output=True,
        text=True,
    )
    return int(result.stdout)


def count_all(logpath: str, queries: list[str]) -> str:
    """对一组查询串，多线程并行统计每个串在所有日志文件中的总出现次数（分词边界匹配）。
    返回 JSON 字符串: {"query_str": count, ...}"""
    real, err = check_path(logpath)
    if err:
        return json.dumps({"error": err})

    paths = list_log_files(real)
    if not paths or not queries:
        return json.dumps({q: 0 for q in queries})

    # 展开所有 (文件, 查询) 对
    tasks = [(p, q) for p in paths for q in queries]

    with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        counts = executor.map(lambda t: _count_one(*t), tasks)

    # 汇总
    totals = {q: 0 for q in queries}
    for (_, query), c in zip(tasks, counts):
        totals[query] += c

    return json.dumps(totals, ensure_ascii=False)
