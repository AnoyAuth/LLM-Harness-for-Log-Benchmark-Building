import os

from common import check_path


def cat(path: str, maximum=100) -> str:
    real, err = check_path(path)
    if err:
        return err

    # 校验存在性
    if not os.path.exists(real):
        return f"Error: file not found: {path}"
    if not os.path.isfile(real):
        return f"Error: not a regular file: {path}"

    # 读前 maximum 行
    try:
        with open(real, "r", errors="replace") as f:
            lines = []
            for i, line in enumerate(f):
                if i >= maximum:
                    break
                lines.append(line)
        if not lines:
            return "(empty file)"
        return "".join(lines)
    except PermissionError:
        return f"Error: permission denied: {path}"
    except OSError as e:
        return f"Error: {e}"
