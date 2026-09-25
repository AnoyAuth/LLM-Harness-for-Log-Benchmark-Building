"""把一个原始日志文件按行边界切成 0.log, 1.log, ... 分片（harness 要求的目录格式）。

用法: python scripts/split_logs.py <raw_log_file> <out_dir> [--size-mb 64]

由于计数是在所有分片上求和、且只在行边界处切分，分片大小不影响 benchmark 中的 frequency。
"""
import argparse
import os


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("src", help="raw log file")
    parser.add_argument("out_dir", help="output directory, e.g. $LOG_ROOT/Spark")
    parser.add_argument("--size-mb", type=int, default=64, help="approximate shard size in MB (default 64)")
    a = parser.parse_args()

    os.makedirs(a.out_dir, exist_ok=True)
    limit = a.size_mb * 1024 * 1024
    idx, size = 0, 0
    out = open(os.path.join(a.out_dir, f"{idx}.log"), "wb")
    with open(a.src, "rb") as f:
        for line in f:
            if size >= limit:
                out.close()
                idx, size = idx + 1, 0
                out = open(os.path.join(a.out_dir, f"{idx}.log"), "wb")
            out.write(line)
            size += len(line)
    out.close()
    print(f"wrote {idx + 1} shards to {a.out_dir}")


if __name__ == "__main__":
    main()
