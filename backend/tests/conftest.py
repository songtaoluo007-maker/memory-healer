"""pytest 配置"""
import sys
from pathlib import Path

# 确保 backend 包可导入
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
