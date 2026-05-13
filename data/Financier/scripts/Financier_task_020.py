from typing import Any
import os
import yaml
import re
from pathlib import Path

def score(tools_history: list[dict[str, Any]]) -> dict[str, int]:
    # 路径解析逻辑保持不变...
    possible_paths = []
    config_path = Path("config") / "nanobot.yaml"
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            if config and 'nanobot' in config and 'workspace_dir' in config['nanobot']:
                workspace_dir = config['nanobot']['workspace_dir']
                possible_paths.append(Path(os.path.expanduser(workspace_dir)) / "Data_Pipeline.py")
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
    
    if content is None:
        return {
            "strict_tenor_adherence": 0,
            "has_deduplication": 0,
            "has_ffill": 0,
            "has_timeout": 0,
            "has_defensive_parsing": 0,          # 新增
            "correct_dropna_axis": 0,            # 新增
            "strictly_no_lookahead": 0           # 新增
        }

    # --- 1. 区分题：严格期限过滤 (优质得 1，劣质得 0) ---
    includes_short_tenors = bool(re.search(r'1\s*Mo|2\s*Mo|3\s*Mo', content, re.IGNORECASE))
    strict_tenor_adherence = 0 if includes_short_tenors else 1

    # --- 2. 区分题：防御性去重 (优质得 1，劣质得 0) ---
    has_deduplication = 1 if '.drop_duplicates(' in content else 0

    # --- 3. 送分题：前向填充与超时保护 (优质得 1，劣质得 1) ---
    has_ffill = 1 if bool(re.search(r'\.ffill\(|\.fillna\(method=[\'"]ffill[\'"]', content)) else 0
    has_timeout = 1 if bool(re.search(r'timeout\s*=\s*\d+', content)) else 0

    # --- 4. 送分题：防御性类型清洗 (优质得 1，劣质得 1) ---
    # 官方 CSV/HTML 经常有脏数据，两个回答都极其聪明地使用了 pd.to_numeric 来转 float
    has_defensive_parsing = 1 if bool(re.search(r'pd\.to_numeric|\.astype\(\s*float\s*\)', content)) else 0

    # --- 5. 区分题：正确的 Dropna 轴向 (优质得 1，劣质得 0) ---
    # 劣质回答写了匪夷所思的 `dropna(axis=1, how='all')` (如果一天没数据，它竟然把整列期限删了！这是致命逻辑错误)
    # 优质回答写了正确的 `.dropna(subset=..., how="all")` (删除全为空的行)
    has_fatal_axis1_drop = '.dropna(axis=1' in content.replace(' ', '')
    correct_dropna_axis = 0 if has_fatal_axis1_drop else 1

    # --- 7. 超纲题：绝对禁止前视偏差 (优质得 0，劣质得 1) ---
    # 极其讽刺！目前的“优质回答”为了偷懒，违规使用了 .bfill() 来倒填节假日，在这个超纲题上拿了 0 分！
    # 而“劣质回答”阴差阳错拉取了 2015 年数据并没用 bfill，反而在这一条上碰巧拿了 1 分 (虽然它别的全错)。
    # 这种戏剧性的得分点能极大地考验后续大模型在 Quant 领域的真实智商。
    uses_bfill = bool(re.search(r'\.bfill\(|\.fillna\(method=[\'"]bfill[\'"]|\.interpolate\(', content))
    strictly_no_lookahead = 0 if uses_bfill else 1

    return {
        "strict_tenor_adherence": strict_tenor_adherence,
        "has_deduplication": has_deduplication,
        "has_ffill": has_ffill,
        "has_timeout": has_timeout,
        "has_defensive_parsing": has_defensive_parsing,
        "correct_dropna_axis": correct_dropna_axis,
        "strictly_no_lookahead": strictly_no_lookahead
    }