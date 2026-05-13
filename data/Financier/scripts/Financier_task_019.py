from typing import Any
import os
import yaml
import re
from pathlib import Path

def score(tools_history: list[dict[str, Any]]) -> dict[str, int]:
    # --- 1. 工作区路径解析 (保持不变) ---
    possible_paths = []
    config_path = Path("config") / "nanobot.yaml"
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            if config and 'nanobot' in config and 'workspace_dir' in config['nanobot']:
                workspace_dir = config['nanobot']['workspace_dir']
                workspace_dir = os.path.expanduser(workspace_dir)
                possible_paths.append(Path(workspace_dir) / "yield_curve_fitter.py")
        except Exception:
            pass
    
    content = None
    for file_path in possible_paths:
        if file_path.exists() and file_path.is_file():
            try:
                content = file_path.read_text(encoding='utf-8')
                break
            except Exception:
                pass
    
    # 如果没生成文件，直接全 0 判负
    if content is None:
        return {
            "dynamic_lambda_calibration": 0,
            "uses_advanced_ols": 0,
            "targeted_api_fetching": 0,
            "has_robust_cleaning": 0,
            "outputs_three_artifacts": 0
        }

# --- 2. 高阶量化与工程标准扫描 ---

    # 1. 动态 Decay 参数校准 (Dynamic Lambda Calibration)
    has_dynamic_loop = bool(re.search(r'for\s+[^:]+:\s*(?:.|\n){1,150}?(?:exp|ols|lstsq|fit)', content, re.IGNORECASE))
    has_hardcoded_lazy_lambda = bool(re.search(r'(LAMBDA|LAM|TAU)(_FIXED|FIXED_)?\s*=\s*0\.\d+|lam\s*=\s*0\.\d+', content, re.IGNORECASE))
    
    dynamic_lambda_calibration = 1 if (has_dynamic_loop and not has_hardcoded_lazy_lambda) else 0
    # 2. 高级 OLS 闭式解法 (Advanced OLS)
    uses_advanced_ols = 1 if 'linalg.lstsq' in content else 0

    # 3. 定向 API 获取 (Targeted API Fetching) [★ 本次核心更新]
    # 合理点：优质代码会通过循环年份拼接 URL，劣质代码会用 date_value=all 一次性拉取 30 年数据。
    # 正向：寻找按年份循环获取的特征 (例如 for year in..., for y in YEARS)
    has_year_loop = bool(re.search(r'for\s+[a-zA-Z_]+\s+in\s+([a-zA-Z_]+YEARS|range\(|\[2023)', content))
    # 反向：绝对不能出现傻瓜式的全量拉取参数
    has_lazy_all_fetch = 'date_value=all' in content
    targeted_api_fetching = 1 if (has_year_loop and not has_lazy_all_fetch) else 0

    # 4. 鲁棒的时序数据清洗 (Robust Data Preprocessing) [★ 本次核心更新]
    # 合理点：金融时序数据处理中，遇到缺失值必须先尝试前向填充 (ffill)，直接全删 (dropna) 是初级行为。
    # 升级：剔除了单纯包含 dropna 就给分的宽泛规则，强制要求代码中必须包含 ffill 动作。
    has_ffill_cleaning = 1 if ('.ffill(' in content or '.fillna(method=' in content or '.fillna(method=\"ffill\"' in content) else 0
    # 6. 三个交付物 (Outputs 3 Artifacts)
    outputs_three_artifacts = 1 if len(re.findall(r'\.to_csv\(', content)) >= 3 else 0

    return {
        "dynamic_lambda_calibration": dynamic_lambda_calibration,
        "uses_advanced_ols": uses_advanced_ols,
        "targeted_api_fetching": targeted_api_fetching,       # 替换了原来的 fallback 检查
        "has_robust_cleaning": has_ffill_cleaning,            # 变得更加严格
        "outputs_three_artifacts": outputs_three_artifacts
    }