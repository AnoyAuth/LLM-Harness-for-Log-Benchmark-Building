import argparse
import json
import os
import sys

from openai import OpenAI

from config import (
    BASE, CATEGORY_DIR, EXAMPLE_PATH, LLM_API_KEY, LLM_BASE_URL, LLM_MODEL,
    LLM_REASONING_EFFORT, LOG_ROOT, MAX_TURNS, METADATA_PATH,
)

sys.path.insert(0, f"{BASE}/src")
from agent import tools, tool_map

_client = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        if not LLM_API_KEY:
            raise RuntimeError("LLM_API_KEY is not set")
        _client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
    return _client


def build_prompt(entry: dict, metadata: list, example: dict, logpath: str) -> str:
    return f"""

    你是一个日志 benchmark 生成器。通过 tools 分析日志并生成可能的查询串，这些查询串应当是 ops 在真实查询过程中可能会使用的、有一定实际意义的。它们被用来分析一些日志查询工具的性能。

    你生成的查询 query 属于日志数据集 {entry["log"]} 的 category {entry["category"]}。下面是该 category 的信息，你需要保证你生成的所有 query 尽可能符合该 category 的描述：
    {json.dumps(entry, ensure_ascii=False, indent=2)}

    你生成的 query 需要满足以下具体格式：
    - 搜索引擎（counter）使用**分词边界匹配**：query 的左右两侧必须同时是分隔符才会被计数。
    - 分隔符集合为：'\\0'（行首/行尾）、空格 ' '、制表符 '\\t'、冒号 ':'、等号 '='、逗号 ','、左方括号 '['、右方括号 ']'
    - 示例：「ERROR」在 "2015-08-21 11:08:11,947 INFO ... ERROR ..." 中可以被匹配，因为左右都是空格
    - 反例：「blk_」在 "blk_1073741825_1001" 中不会被匹配，因为 'blk_' 右侧是数字，不是分隔符，不构成一个独立 token
    - query 长度不超过 99 字符
    - query 必须在日志原文中能找到**满足分隔符边界条件的**出现。如果 count_query 返回 0，说明该 query 不满足边界条件或不存在于日志中，你需要根据分隔符规则调整

    你可以阅读的日志目录。除了该目录之外，你不得阅读任何目录。你可以使用 list_dir 和 cat_file 工具来阅读相关目录：
    {logpath}

    你要输出的 json 格式，你需要严格参考该 json 格式：
    {json.dumps(example, ensure_ascii=False, indent=2)}

    你的基本工作流程：
    1. list_dir 确认目录
    2. sample_logs 采样原文理解格式
    3. 充分利用 cat_file search_file sample_logs 等工具，搜索当前 category 的高质量 query，生成 1 条 ~ 20 条符合条件的 query 文本
    4. 对于每一条 query 文本，调用 count_query 获取准确频次
    5. cat_file 抽查确认
    6. validate_json 自检输出，如果 json 校验不通过，你需要修改并重新生成 json

    细节与风格
    - **由于内核资源受限的原因，sample_logs / search_file / count_query 每次只能调用一个，最大线程数为20，并且需要串行等待**
    - **由于 token 限制的原因，你只有 30 轮 tool 交互次数上限。你需要妥善管理你的交互次数**
    - 对于本次生成，你需要生成 1 条 ~ 20 条符合条件的query。如果query 本身数量极少，那么你可以生成 1~5 条，但如果 query 本身数量较多（如 ip 地址等），可以生成满 20 条
    - query 是日志原文真实子串，frequency 必须由 count_query 实测。如果 count_query 对你的生成返回 0 ，那么说明该query 需要重新生成
    - description 字段要简明扼要、记录有用的信息
    - 在你的最后一次输出（也就是不发起 tool 调用，作为最终的结果的输出里，你只需要输出 JSON，不要输出其他的东西。我会直接调用如下代码将你的最后一次输出放到文件里，所以你需要确保你的输出符合要求
    ```python
        resp = client.chat.completions.create(
            model="deepseek-v4-pro",
            reasoning_effort="high",
            messages=messages,
            tools=tools,
        )
        msg = resp.choices[0].message

        if msg.content and not msg.tool_calls:
            raw = msg.content.strip()
            # 去掉 markdown 代码块包裹
            if raw.startswith("```"):
                raw = raw.split("\\n", 1)[-1]
                if raw.endswith("```"):
                    raw = raw[:-3]
            raw = raw.strip()

            out_path = f"" # some output path here
            with open(out_path, "w") as f:
                f.write(raw)
    ```

    最后，你要生成的 category 只是整个benchmark 的一个小子集。
    为了方便你理解benchmark 生成的全貌，以下是整个 benchmark 里其他 category 的信息，作为参考：
    {json.dumps(metadata, ensure_ascii=False, indent=2)}

    你只需要生成指定的 category 中的信息即可。为了防止你忘记，再一次提示你的 category：
    {json.dumps(entry, ensure_ascii=False, indent=2)}
    """


def run(log: str, category: str) -> bool:
    """为 (log, category) 跑一次 agent，成功时写出 category/<log>-<category>.json 并返回 True"""
    # 1. 读 MetaData，找匹配条目
    with open(METADATA_PATH) as f:
        metadata = json.load(f)
    entry = next(
        (m for m in metadata if m["log"] == log and m["category"] == category), None
    )
    if not entry:
        print(f"❌ No entry for log={log} category={category}")
        return False

    # 2. 读输出格式样例
    with open(EXAMPLE_PATH) as f:
        example = json.load(f)

    logpath = os.path.join(LOG_ROOT, log)

    # 3. 构建 prompt
    prompt = build_prompt(entry, metadata, example, logpath)

    # 4. Agent loop
    client = get_client()
    messages = [{"role": "user", "content": prompt}]

    for _ in range(MAX_TURNS):
        resp = client.chat.completions.create(
            model=LLM_MODEL,
            reasoning_effort=LLM_REASONING_EFFORT,
            messages=messages,
            tools=tools,
        )
        msg = resp.choices[0].message

        if msg.content and not msg.tool_calls:
            raw = msg.content.strip()
            # 去掉 markdown 代码块包裹
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[-1]
                if raw.endswith("```"):
                    raw = raw[:-3]
            raw = raw.strip()

            out_path = os.path.join(CATEGORY_DIR, f"{log}-{category}.json")
            with open(out_path, "w") as f:
                f.write(raw)

            print(f"✅ Written to {out_path}")
            return True

        messages.append(msg)
        for tc in msg.tool_calls or []:
            fn = tc.function.name
            args = json.loads(tc.function.arguments)
            print(f"  🔧 {fn}({json.dumps(args, ensure_ascii=False)})")
            result = tool_map[fn](**args)
            short = result if len(result) < 400 else result[:400] + "..."
            print(f"  ✅ {short}")
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result,
            })

    print("⚠️  Max turns exceeded")
    return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate queries for one (log, category) pair")
    parser.add_argument("log", help="dataset name, e.g. Spark")
    parser.add_argument("category", help="category name from MetaData.json, e.g. ip_address")
    parser.add_argument("--print-prompt", action="store_true", help="only print the prompt, do not call the LLM")
    a = parser.parse_args()

    if a.print_prompt:
        with open(METADATA_PATH) as f:
            md = json.load(f)
        with open(EXAMPLE_PATH) as f:
            ex = json.load(f)
        e = next(m for m in md if m["log"] == a.log and m["category"] == a.category)
        print(build_prompt(e, md, ex, os.path.join(LOG_ROOT, a.log)))
    else:
        sys.exit(0 if run(a.log, a.category) else 1)
