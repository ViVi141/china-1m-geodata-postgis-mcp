"""
数据规格加载器：加载和管理数据规格配置
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

try:
    import yaml

    HAS_YAML = True
except ImportError:
    HAS_YAML = False

logger = logging.getLogger(__name__)


class SpecLoader:
    """数据规格加载器"""

    def __init__(self, specs_dir: Optional[str] = None):
        """
        初始化规格加载器

        Args:
            specs_dir: 规格文件目录，默认为项目根目录下的specs目录
        """
        if specs_dir is None:
            self.specs_dir = Path(__file__).parent.parent / "specs"
        else:
            self.specs_dir = Path(specs_dir)

        self.specs_dir.mkdir(exist_ok=True)

    def list_specs(self) -> List[str]:
        """
        列出所有可用的数据规格

        Returns:
            规格名称列表
        """
        specs = []
        for file_path in self.specs_dir.glob("*.json"):
            specs.append(file_path.stem)
        for file_path in self.specs_dir.glob("*.yaml"):
            specs.append(file_path.stem)
        for file_path in self.specs_dir.glob("*.yml"):
            specs.append(file_path.stem)
        return sorted(set(specs))

    def load_spec(self, spec_name: str) -> Dict[str, Any]:
        """
        加载指定的数据规格

        Args:
            spec_name: 规格名称（不含扩展名）

        Returns:
            规格配置字典
        """
        # 尝试加载JSON格式
        json_path = self.specs_dir / f"{spec_name}.json"
        if json_path.exists():
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)

        # 尝试加载YAML格式
        if HAS_YAML:
            yaml_path = self.specs_dir / f"{spec_name}.yaml"
            if yaml_path.exists():
                with open(yaml_path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f)

            yml_path = self.specs_dir / f"{spec_name}.yml"
            if yml_path.exists():
                with open(yml_path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f)

        raise FileNotFoundError(f"数据规格 '{spec_name}' 不存在")

    def save_spec(
        self, spec_name: str, spec_config: Dict[str, Any], format: str = "json"
    ):
        """
        保存数据规格配置

        Args:
            spec_name: 规格名称
            spec_config: 规格配置字典
            format: 保存格式（json或yaml）
        """
        if format.lower() == "json":
            file_path = self.specs_dir / f"{spec_name}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(spec_config, f, ensure_ascii=False, indent=2)
        elif format.lower() in ["yaml", "yml"]:
            if not HAS_YAML:
                raise ImportError("需要安装pyyaml库以支持YAML格式")
            file_path = self.specs_dir / f"{spec_name}.yaml"
            with open(file_path, "w", encoding="utf-8") as f:
                yaml.dump(
                    spec_config,
                    f,
                    allow_unicode=True,
                    default_flow_style=False,
                    indent=2,
                )
        else:
            raise ValueError(f"不支持的格式: {format}")

    def detect_spec(self, data_path: str) -> Optional[str]:
        """
        根据数据路径自动检测数据规格

        Args:
            data_path: 数据文件路径

        Returns:
            检测到的规格名称，如果无法检测则返回None
        """
        path = Path(data_path)

        # 检查文件名模式
        name = path.stem.upper()

        # 检查是否是1:100万数据（F49, G49等图幅代码）
        if len(name) == 3 and name[0] in ["F", "G"] and name[1:].isdigit():
            return "china_1m_2021"

        # 检查目录结构
        if path.is_dir():
            # 检查是否包含.gdb文件
            gdb_files = list(path.glob("*.gdb"))
            if gdb_files:
                # 可以进一步检查图层结构
                return "china_1m_2021"

        # 默认返回None，让用户指定
        return None
