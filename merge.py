"""把 category/<log>-<category>.json 按 MetaData.json 的顺序合并成 benchmark.json，并做一致性检查"""
import json
import os

from config import BENCHMARK_PATH, CATEGORY_DIR, METADATA_PATH


def main():
    with open(METADATA_PATH) as f:
        metadata = json.load(f)

    result = []
    for entry in metadata:
        log, category = entry["log"], entry["category"]
        json_path = os.path.join(CATEGORY_DIR, f"{log}-{category}.json")

        if not os.path.isfile(json_path):
            print(f"{log} {category} does not exist")
            continue
        with open(json_path) as f:
            benchmark = json.load(f)

        # agent 输出的元信息必须与 MetaData.json 一致，且每条 query 的频次非 0
        for key in ("log", "log description", "category", "description", "scenario"):
            if benchmark.get(key) != entry[key]:
                print(f"{log} {category}: field '{key}' mismatches MetaData.json")
        for query in benchmark["benchmark"]:
            if int(query["frequency"]) == 0:
                print(f"{log} {category}: zero frequency for query {query['query']!r}")

        benchmark["scenario"] = ""
        for query in benchmark["benchmark"]:
            query["frequency"] = int(query["frequency"])

        result.append(benchmark)

    with open(BENCHMARK_PATH, "w") as f:
        json.dump(result, f, indent=4)
    print(f"merged {len(result)} categories, "
          f"{sum(len(b['benchmark']) for b in result)} queries -> {BENCHMARK_PATH}")


if __name__ == "__main__":
    main()
