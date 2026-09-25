import argparse
import json
import os
import sys
from contextlib import redirect_stdout

from config import CATEGORY_DIR, METADATA_PATH, RUNTIME_LOG_DIR
from run import run


def gen_one(log: str, category: str, retries: int) -> bool:
    """跑 (log, category)，失败时最多重试 retries 次；agent 轨迹写入 runtime-log/"""
    os.makedirs(RUNTIME_LOG_DIR, exist_ok=True)
    for attempt in range(1, retries + 1):
        log_path = os.path.join(RUNTIME_LOG_DIR, f"{log}-{category}.log")
        succeed = False
        with open(log_path, "w", encoding="utf-8") as flog, redirect_stdout(flog):
            try:
                succeed = run(log, category)
            except Exception as e:
                print(f"error in {log} and {category}\nmessage:\n{e}")

        if succeed:
            print(f"succeed in {log} {category} (attempt {attempt})", flush=True)
            return True
        print(f"fail in {log} {category} (attempt {attempt}), see {log_path}", flush=True)
    return False


def main():
    parser = argparse.ArgumentParser(description="Generate the whole benchmark category by category")
    parser.add_argument("--log", nargs="*", help="only these datasets (default: all in MetaData.json)")
    parser.add_argument("--category", nargs="*", help="only these categories (default: all)")
    parser.add_argument("--retries", type=int, default=3, help="attempts per category (default: 3)")
    parser.add_argument("--skip-existing", action="store_true",
                        help="skip categories whose category/<log>-<category>.json already exists")
    a = parser.parse_args()

    with open(METADATA_PATH) as f:
        metadata = json.load(f)

    failed = []
    for entry in metadata:
        log, category = entry["log"], entry["category"]
        if a.log and log not in a.log:
            continue
        if a.category and category not in a.category:
            continue
        if a.skip_existing and os.path.isfile(os.path.join(CATEGORY_DIR, f"{log}-{category}.json")):
            continue
        if not gen_one(log, category, a.retries):
            failed.append(f"{log}-{category}")

    if failed:
        print(f"{len(failed)} categories failed: {' '.join(failed)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
