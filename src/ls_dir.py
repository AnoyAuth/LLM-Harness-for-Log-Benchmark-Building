import os

from common import check_path


def ls_dir(path: str) -> str:
    real, err = check_path(path)
    if err:
        return err

    # 校验存在性
    if not os.path.exists(real):
        return f"Error: path not found: {path}"
    if not os.path.isdir(real):
        return f"Error: not a directory: {path}"

    # 列举
    try:
        entries = sorted(os.listdir(real))
    except PermissionError:
        return f"Error: permission denied: {path}"
    except OSError as e:
        return f"Error: {e}"

    if not entries:
        return f"(empty directory: {path})"

    lines = []
    for name in entries:
        full = os.path.join(real, name)
        try:
            st = os.stat(full)
        except OSError:
            continue
        if os.path.isdir(full):
            lines.append(f"[DIR]  {name}/")
        else:
            lines.append(f"[FILE] {name}  ({st.st_size:,} bytes)")
    return "\n".join(lines)
