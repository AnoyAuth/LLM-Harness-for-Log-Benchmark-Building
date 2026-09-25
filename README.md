# LLM Harness for Log Benchmark Building

This repository contains the LLM agent harness used to build the **query benchmark** for the paper
*LogIndex: Alleviating Query Bottleneck by Avoiding Index Inflation on Highly Compressed Logs*
(under double-blind review), together with the resulting benchmark.

The harness gives an LLM a small set of sandboxed, read-only tools over the raw log datasets. For each
*(dataset, query category)* pair, the agent explores the logs, proposes queries that an operator might
realistically issue, measures each query's exact frequency with a deterministic counter, and returns the
result as JSON. The agent never writes frequencies itself: every frequency comes from the counter, and
`merge.py` rejects zero-frequency queries.

The released benchmark (`benchmark.json`) has **63 categories and 1,154 queries** across 4 datasets.

## Repository layout

```
.
├── run.py              # agent loop for one (log, category): prompt + tool-calling loop
├── gen.py              # batch driver over MetaData.json, with retries and per-category trajectory logs
├── merge.py            # merges category/*.json into benchmark.json with consistency checks
├── config.py           # all paths / LLM endpoint settings (overridable by environment variables)
├── MetaData.json       # the 63 (dataset, category) definitions given to the agent
├── category/
│   └── example.json    # output JSON schema shown to the agent
├── benchmark.json      # the generated benchmark used in the paper
├── src/
│   ├── agent.py        # tool schemas (OpenAI function-calling format) and dispatch table
│   ├── common.py       # path sandbox + shard enumeration
│   ├── count.py        # count_query:  exact token-boundary frequency (calls src/O/counter)
│   ├── counter.cpp     # the token-boundary counter
│   ├── sample.py       # sample_logs:  random consecutive lines from every shard
│   ├── search.py       # search_file:  regex search returning whole log lines
│   ├── cat.py          # cat_file:     first N lines of a shard
│   ├── ls_dir.py       # list_dir
│   └── validate_json.py# validate_json: lets the agent self-check its final output
├── scripts/
│   └── split_logs.py   # splits a raw log into 0.log, 1.log, ... shards
└── Makefile            # builds src/O/counter
```

## Query semantics

All frequencies use **token-boundary matching**, the same semantics as the query engines evaluated in
the paper: an occurrence of a query string counts only if the characters immediately to its left and
right are both delimiters (or line start / end). The delimiter set is

```
'\0' (line start / end)   ' '   '\t'   ':'   '='   ','   '['   ']'
```

For example, `ERROR` matches in `... INFO ... ERROR ...`, but `blk_` does **not** match inside
`blk_1073741825_1001`. Queries are at most 99 characters long. `src/counter.cpp` implements this
exactly, and the prompt describes the same rule to the agent.

## Agent tools

| Tool | Description |
|---|---|
| `list_dir(path)` | List a directory under `LOG_ROOT`. |
| `cat_file(path, maximum=100)` | Return the first `maximum` lines of one shard. |
| `sample_logs(logpath, line=10)` | Return `line` random consecutive lines from **every** shard of a dataset. |
| `search_file(logpath, regex, maximum=100)` | Return up to `maximum` whole lines matching `regex`. Shards are scanned in parallel batches and the scan stops early. |
| `count_query(logpath, queries)` | Exact total token-boundary frequency of each query over all shards. |
| `validate_json(text)` | Check the final JSON and report the error line and column. |

Every path is resolved with `realpath` and must lie under `LOG_ROOT`. The agent cannot read anything
else on the machine.

## Benchmark

`MetaData.json` defines the categories. Each entry holds a dataset description and a category
description. The agent sees its own category plus the full category list for context.

| Dataset | #Queries | Categories |
|---|---:|---|
| Hadoop (HDFS) | 310 | `block_id`, `bp_block_pool`, `rpc_op`, `hex_guid_uuid`, `ip_address`, `port_number`, `hostname`, `component_module`, `log_level`, `timestamp`, `version_string`, `filepath_url`, `numeric_id`, `error_message_phrase`, `long_phrase`, `high_frequency_token`, `rare_unique_token` |
| Spark | 283 | `attempt_id`, `rdd_block`, `hex_guid_uuid`, `stage_task`, `filepath_url`, `timestamp`, `ip_address`, `hostname`, `version_string`, `log_level`, `component_module`, `numeric_id`, `error_message_phrase`, `long_phrase`, `rare_unique_token`, `high_frequency_token` |
| Thunderbird | 318 | `ip_address`, `numeric_id`, `hostname`, `timestamp`, `log_level`, `syslog_facility`, `component_module`, `process_pid`, `mail_queue_id`, `mac_ib_addr`, `hex_guid_uuid`, `filepath_url`, `version_string`, `error_message_phrase`, `long_phrase`, `rare_unique_token`, `high_frequency_token` |
| Windows | 243 | `kb_update`, `package_id`, `csi_seq`, `timestamp`, `component_module`, `hex_guid_uuid`, `filepath_url`, `version_string`, `numeric_id`, `error_message_phrase`, `long_phrase`, `rare_unique_token`, `high_frequency_token` |

`benchmark.json` is a list of categories. Each category has this shape:

```json
{
  "log": "Hadoop",
  "log description": "Apache Hadoop HDFS logs (DataNode/NameNode).",
  "category": "ip_address",
  "description": "IPv4 addresses of cluster nodes.",
  "scenario": "",
  "benchmark": [
    { "query": "10.10.34.11", "frequency": 1960756, "description": "..." }
  ]
}
```

`frequency` is the exact number of token-boundary occurrences in the whole dataset.

## Reproducing

### 1. Requirements

- Linux, `g++` (C++11), Python ≥ 3.10
- `pip install -r requirements.txt`
- An OpenAI-compatible chat-completions endpoint with tool calling. The paper used
  `deepseek-v4-flash` with `reasoning_effort=high`.

### 2. Prepare the datasets

We use the `Hadoop` (HDFS_v2), `Spark`, `Thunderbird` and `Windows` datasets from
[Loghub](https://github.com/logpai/loghub) (download them from Loghub; they are not redistributed here).
The harness expects each dataset split into consecutively numbered shards:

```
$LOG_ROOT/
├── Hadoop/       0.log 1.log 2.log ...
├── Spark/        0.log 1.log ...
├── Thunderbird/  ...
└── Windows/      ...
```

For a dataset that ships as several raw files, concatenate them first, then run:

```bash
python scripts/split_logs.py Spark_all.log $LOG_ROOT/Spark --size-mb 64
```

Shards are cut only at line boundaries and frequencies are summed over all shards, so the shard size
does not change any frequency.

### 3. Build and configure

```bash
make                                    # builds src/O/counter
export LOG_ROOT=/path/to/logs           # default: ./logs
export LLM_API_KEY=...                  # required
export LLM_BASE_URL=https://api.deepseek.com   # default
export LLM_MODEL=deepseek-v4-flash             # default
```

### 4. Generate and merge

```bash
python run.py Spark ip_address --print-prompt   # inspect the exact prompt, no LLM call
python run.py Spark ip_address                  # one category -> category/Spark-ip_address.json

python gen.py                                   # all 63 categories (trajectories in runtime-log/)
python gen.py --log Spark Windows --retries 3 --skip-existing

python merge.py                                 # category/*.json -> benchmark.json
```

`merge.py` checks that each agent output's metadata matches `MetaData.json`. It also flags any query
with zero frequency. Such a category should be regenerated, for example with
`python gen.py --log Spark --category long_phrase`.

LLM outputs are non-deterministic, so a re-run produces a different but statistically similar query
set. The benchmark used in the paper is `benchmark.json`. To verify its frequencies without an LLM, call
the counter tool directly:

```bash
cd src && python -c "from count import count_all; print(count_all('$LOG_ROOT/Spark', ['Finished task']))"
```

## Notes

- The prompt in `run.py` and the tool descriptions in `src/agent.py` are kept **verbatim**, in their
  original language (Chinese), as they were used to generate the benchmark. Only machine-specific paths
  were replaced by `LOG_ROOT`.
- The prompt tells the agent it has 30 tool rounds and that the heavy tools must be called one at a
  time. The harness itself stops after 40 LLM turns (`MAX_TURNS` in `config.py`).
- Tools that scan the logs use 20 threads each (`NUM_THREADS` in `config.py`).

## License

MIT, see [LICENSE](LICENSE).
