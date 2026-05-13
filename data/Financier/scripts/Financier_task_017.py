from typing import Any
import os
import yaml
import re
from pathlib import Path

def score(tools_history: list[dict[str, Any]]) -> dict[str, int]:
    possible_paths = []
    config_path = Path("config") / "nanobot.yaml"
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            if config and 'nanobot' in config and 'workspace_dir' in config['nanobot']:
                workspace_dir = os.path.expanduser(config['nanobot']['workspace_dir'])
                possible_paths.append(Path(workspace_dir) / "risk_correlation_pipeline.py")
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
            "has_volatility_annualization": 0,
            "uses_zipfile_extraction": 0,
            "uses_spark_distributed_read": 0
        }

    # 1. 修复后的年化波动率检测 (包容嵌套的 F.lit(252))
    # 只要在同一行或紧挨着的地方出现了 sqrt 并且后面跟着 250/252，就算对
    has_volatility_annualization = 1 if bool(re.search(r'sqrt[^\n]*?25[02]|25[02]\.?0?\s*\*\*\s*0\.5', content)) else 0

    # 2. 压缩包预处理常识 (保持不变)
    uses_zipfile_extraction = 1 if bool(re.search(r'import\s+zipfile|from\s+zipfile', content)) else 0

    # 3. 修复后的 Spark 分布式读取检测 (包容链式调用的 .option())
    # 只要出现了 spark.read 并且后续调用链中出现了 .csv( 或 .format( 就算对
    uses_spark_distributed_read = 1 if bool(re.search(r'spark\.read(?:(?:[\r\n\s\\]*\.)[a-zA-Z0-9_]+(?:\([^)]*\)))*[\r\n\s\\]*\.(?:csv|format)\s*\(', content)) else 0

    return {
        "has_volatility_annualization": has_volatility_annualization,
        "uses_zipfile_extraction": uses_zipfile_extraction,
        "uses_spark_distributed_read": uses_spark_distributed_read
    }