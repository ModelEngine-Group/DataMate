import os

def get_model_root(params=None) -> str:
    """
    模型根目录优先级：
      1) params['model_root']
      2) 环境变量 DATAMATE_MODEL_ROOT
      3) 默认 /mnt/models
    """
    params = params or {}
    return params.get("model_root") or os.environ.get("DATAMATE_MODEL_ROOT") or "/mnt/models"


def resolve_model_path(params, param_key: str, default_rel: str) -> str:
    """
    解析模型路径：
      - 如果 params[param_key] 是绝对路径：直接用
      - 如果是相对路径：拼到 model_root
      - 如果没传：用 model_root + default_rel
    """
    params = params or {}
    root = get_model_root(params)

    v = params.get(param_key)
    if v:
        return v if os.path.isabs(v) else os.path.join(root, v)

    return os.path.join(root, default_rel)