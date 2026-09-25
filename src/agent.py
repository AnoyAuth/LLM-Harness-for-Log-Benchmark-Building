import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cat import cat
from config import LOG_ROOT
from count import count_all
from ls_dir import ls_dir
from sample import sample
from search import search
from validate_json import validate_json

EXAMPLE_DIR = os.path.join(LOG_ROOT, "Hadoop") + os.sep

tools = [
    {
        "type": "function",
        "function": {
            "name": "count_query",
            "description": "批量查询一组字符串在所有日志文件中的总出现次数。返回 JSON 对象 {query: count, ...}。20 线程并行，**不可与 sample_logs / search_file 同时调用。**",
            "parameters": {
                "type": "object",
                "properties": {
                    "logpath": {
                        "type": "string",
                        "description": f"日志文件所在目录，如 {EXAMPLE_DIR}",
                    },
                    "queries": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "要统计的一组查询串，如 [\"ERROR\", \"WARN\", \"blk_\"]",
                    },
                },
                "required": ["logpath", "queries"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "sample_logs",
            "description": "从每个日志文件中随机采样连续的若干行，返回拼接后的原文。20 线程并行，**不可与 count_query / search_file 同时调用。**",
            "parameters": {
                "type": "object",
                "properties": {
                    "logpath": {
                        "type": "string",
                        "description": f"日志文件所在目录，如 {EXAMPLE_DIR}",
                    },
                    "line": {
                        "type": "integer",
                        "description": "每个文件采样的行数，默认 10",
                    },
                },
                "required": ["logpath"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cat_file",
            "description": f"读取指定日志文件的前 N 行（截取原文）。path 必须是 {LOG_ROOT}/ 下的文件路径。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": f"日志文件的完整路径，必须在 {LOG_ROOT}/ 目录下",
                    },
                    "maximum": {
                        "type": "integer",
                        "description": "最多读取的行数，默认 100",
                    },
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_dir",
            "description": f"列举白名单目录下的所有文件和子目录。path 必须在 {LOG_ROOT}/ 下。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": f"目录路径，必须在 {LOG_ROOT}/ 下，如 {EXAMPLE_DIR}",
                    },
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_file",
            "description": "在指定目录的所有日志文件中用正则分批并行搜索，返回前 N 条**完整的日志行**（非仅匹配子串）。每批 20 文件，命中 maximum 即提前截断退出。20 线程并行，**不可与 count_query / sample_logs 同时调用。**",
            "parameters": {
                "type": "object",
                "properties": {
                    "logpath": {
                        "type": "string",
                        "description": f"日志目录路径，必须在 {LOG_ROOT}/ 下，如 {EXAMPLE_DIR}",
                    },
                    "regex": {
                        "type": "string",
                        "description": "正则表达式，匹配的**整行**会返回。如 ERROR|WARN、\\d{4}-\\d{2}-\\d{2}",
                    },
                    "maximum": {
                        "type": "integer",
                        "description": "最多返回的整行条数，命中则提前退出。默认 100",
                    },
                },
                "required": ["logpath", "regex"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "validate_json",
            "description": "校验 JSON 字符串是否合法。返回原文本或错误信息（含行列号和具体错误原因）。不会修改输入。",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "需要校验的 JSON 字符串",
                    },
                },
                "required": ["text"],
            },
        },
    },
]

tool_map = {
    "cat_file": lambda **kw: cat(kw["path"], kw.get("maximum", 100)),
    "count_query": lambda **kw: count_all(kw["logpath"], kw["queries"]),
    "list_dir": lambda **kw: ls_dir(kw["path"]),
    "sample_logs": lambda **kw: sample(kw["logpath"], kw.get("line", 10)),
    "search_file": lambda **kw: search(kw["logpath"], kw["regex"], kw.get("maximum", 100)),
    "validate_json": lambda **kw: validate_json(kw["text"]),
}
