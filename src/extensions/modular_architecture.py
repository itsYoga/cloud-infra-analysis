"""
基於 Cartography 架構的模組化擴展系統

這個模組實作了可擴展、模組化的架構，
允許輕鬆添加新的雲端提供商、分析規則和視覺化組件。
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Type, Callable
from enum import Enum
import importlib
import inspect

logger = logging.getLogger(__name__)


class ModuleType(Enum):
    """模組類型枚舉"""
    EXTRACTOR = "extractor"
    ANALYZER = "analyzer"
    VISUALIZER = "visualizer"
    RULE = "rule"
    LOADER = "loader"


@dataclass
class ModuleInfo:
    """模組資訊"""
    name: str
    module_type: ModuleType
    version: str
    description: str
    author: str
    dependencies: List[str]
    config_schema: Dict[str, Any]


class BaseModule(ABC):
    """基礎模組類"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def get_info(self) -> ModuleInfo:
        """獲取模組資訊"""
        pass
    
    @abstractmethod
    def initialize(self) -> bool:
        """初始化模組"""
        pass
    
    @abstractmethod
    def cleanup(self):
        """清理模組資源"""
        pass


class CloudExtractor(BaseModule):
    """雲端擷取器基類"""
    
    @abstractmethod
    def extract_resources(self, region: str = None) -> Dict[str, Any]:
        """擷取雲端資源"""
        pass
    
    @abstractmethod
    def get_supported_services(self) -> List[str]:
        """獲取支援的服務列表"""
        pass


class SecurityAnalyzer(BaseModule):
    """安全分析器基類"""
    
    @abstractmethod
    def analyze(self, neo4j_session) -> List[Dict[str, Any]]:
        """執行安全分析"""
        pass
    
    @abstractmethod
    def get_analysis_types(self) -> List[str]:
        """獲取分析類型列表"""
        pass


class Visualizer(BaseModule):
    """視覺化器基類"""
    
    @abstractmethod
    def create_visualization(self, data: Dict[str, Any]) -> Any:
        """創建視覺化"""
        pass
    
    @abstractmethod
    def get_visualization_types(self) -> List[str]:
        """獲取視覺化類型列表"""
        pass


class SecurityRule(BaseModule):
    """安全規則基類"""
    
    @abstractmethod
    def evaluate(self, neo4j_session) -> List[Dict[str, Any]]:
        """評估規則"""
        pass
    
    @abstractmethod
    def get_rule_info(self) -> Dict[str, Any]:
        """獲取規則資訊"""
        pass


class DataLoader(BaseModule):
    """資料載入器基類"""
    
    @abstractmethod
    def load_data(self, data: Dict[str, Any], target: Any) -> bool:
        """載入資料"""
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """獲取支援的格式列表"""
        pass


class ModuleRegistry:
    """模組註冊表"""
    
    def __init__(self):
        self.modules: Dict[str, Type[BaseModule]] = {}
        self.instances: Dict[str, BaseModule] = {}
        self.module_info: Dict[str, ModuleInfo] = {}
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def register_module(self, module_class: Type[BaseModule], 
                       module_info: ModuleInfo) -> bool:
        """註冊模組"""
        try:
            self.modules[module_info.name] = module_class
            self.module_info[module_info.name] = module_info
            self.logger.info(f"註冊模組: {module_info.name}")
            return True
        except Exception as e:
            self.logger.error(f"註冊模組失敗: {e}")
            return False
    
    def unregister_module(self, module_name: str) -> bool:
        """取消註冊模組"""
        try:
            if module_name in self.modules:
                del self.modules[module_name]
                del self.module_info[module_name]
                if module_name in self.instances:
                    del self.instances[module_name]
                self.logger.info(f"取消註冊模組: {module_name}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"取消註冊模組失敗: {e}")
            return False
    
    def get_module(self, module_name: str, config: Dict[str, Any] = None) -> Optional[BaseModule]:
        """獲取模組實例"""
        if module_name not in self.modules:
            self.logger.error(f"模組不存在: {module_name}")
            return None
        
        # 如果已有實例，返回現有實例
        if module_name in self.instances:
            return self.instances[module_name]
        
        # 創建新實例
        try:
            module_class = self.modules[module_name]
            instance = module_class(config or {})
            self.instances[module_name] = instance
            return instance
        except Exception as e:
            self.logger.error(f"創建模組實例失敗: {e}")
            return None
    
    def list_modules(self, module_type: ModuleType = None) -> List[ModuleInfo]:
        """列出模組"""
        if module_type is None:
            return list(self.module_info.values())
        else:
            return [
                info for info in self.module_info.values()
                if info.module_type == module_type
            ]
    
    def get_module_info(self, module_name: str) -> Optional[ModuleInfo]:
        """獲取模組資訊"""
        return self.module_info.get(module_name)


class ModuleLoader:
    """模組載入器"""
    
    def __init__(self, registry: ModuleRegistry):
        self.registry = registry
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def load_module_from_file(self, file_path: str, module_name: str) -> bool:
        """從檔案載入模組"""
        try:
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 查找模組類
            module_class = None
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, BaseModule) and 
                    obj != BaseModule):
                    module_class = obj
                    break
            
            if module_class is None:
                self.logger.error(f"檔案中未找到有效的模組類: {file_path}")
                return False
            
            # 獲取模組資訊
            module_info = module_class().get_info()
            
            # 註冊模組
            return self.registry.register_module(module_class, module_info)
            
        except Exception as e:
            self.logger.error(f"載入模組失敗: {e}")
            return False
    
    def load_module_from_package(self, package_name: str, module_name: str) -> bool:
        """從套件載入模組"""
        try:
            module = importlib.import_module(f"{package_name}.{module_name}")
            
            # 查找模組類
            module_class = None
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, BaseModule) and 
                    obj != BaseModule):
                    module_class = obj
                    break
            
            if module_class is None:
                self.logger.error(f"套件中未找到有效的模組類: {package_name}.{module_name}")
                return False
            
            # 獲取模組資訊
            module_info = module_class().get_info()
            
            # 註冊模組
            return self.registry.register_module(module_class, module_info)
            
        except Exception as e:
            self.logger.error(f"載入模組失敗: {e}")
            return False


class ExtensionManager:
    """擴展管理器"""
    
    def __init__(self):
        self.registry = ModuleRegistry()
        self.loader = ModuleLoader(self.registry)
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def load_extension(self, extension_path: str) -> bool:
        """載入擴展"""
        try:
            # 嘗試載入擴展
            if extension_path.endswith('.py'):
                return self.loader.load_module_from_file(extension_path, 
                                                        extension_path.split('/')[-1].replace('.py', ''))
            else:
                # 假設是套件路徑
                parts = extension_path.split('.')
                module_name = parts[-1]
                package_name = '.'.join(parts[:-1])
                return self.loader.load_module_from_package(package_name, module_name)
        except Exception as e:
            self.logger.error(f"載入擴展失敗: {e}")
            return False
    
    def get_extractor(self, provider: str, config: Dict[str, Any] = None) -> Optional[CloudExtractor]:
        """獲取雲端擷取器"""
        extractors = self.registry.list_modules(ModuleType.EXTRACTOR)
        for extractor_info in extractors:
            if provider.lower() in extractor_info.name.lower():
                module = self.registry.get_module(extractor_info.name, config)
                if isinstance(module, CloudExtractor):
                    return module
        return None
    
    def get_analyzer(self, analysis_type: str, config: Dict[str, Any] = None) -> Optional[SecurityAnalyzer]:
        """獲取安全分析器"""
        analyzers = self.registry.list_modules(ModuleType.ANALYZER)
        for analyzer_info in analyzers:
            if analysis_type.lower() in analyzer_info.name.lower():
                module = self.registry.get_module(analyzer_info.name, config)
                if isinstance(module, SecurityAnalyzer):
                    return module
        return None
    
    def get_visualizer(self, viz_type: str, config: Dict[str, Any] = None) -> Optional[Visualizer]:
        """獲取視覺化器"""
        visualizers = self.registry.list_modules(ModuleType.VISUALIZER)
        for viz_info in visualizers:
            if viz_type.lower() in viz_info.name.lower():
                module = self.registry.get_module(viz_info.name, config)
                if isinstance(module, Visualizer):
                    return module
        return None
    
    def get_rule(self, rule_name: str, config: Dict[str, Any] = None) -> Optional[SecurityRule]:
        """獲取安全規則"""
        rules = self.registry.list_modules(ModuleType.RULE)
        for rule_info in rules:
            if rule_name.lower() in rule_info.name.lower():
                module = self.registry.get_module(rule_info.name, config)
                if isinstance(module, SecurityRule):
                    return module
        return None
    
    def list_available_extensions(self) -> Dict[str, List[ModuleInfo]]:
        """列出可用擴展"""
        return {
            'extractors': self.registry.list_modules(ModuleType.EXTRACTOR),
            'analyzers': self.registry.list_modules(ModuleType.ANALYZER),
            'visualizers': self.registry.list_modules(ModuleType.VISUALIZER),
            'rules': self.registry.list_modules(ModuleType.RULE),
            'loaders': self.registry.list_modules(ModuleType.LOADER)
        }


# 範例擴展模組
class AWSExtractor(CloudExtractor):
    """AWS 擷取器範例"""
    
    def get_info(self) -> ModuleInfo:
        return ModuleInfo(
            name="AWS Extractor",
            module_type=ModuleType.EXTRACTOR,
            version="1.0.0",
            description="AWS 雲端資源擷取器",
            author="Cloud Infrastructure Team",
            dependencies=["boto3"],
            config_schema={
                "aws_access_key_id": {"type": "string", "required": True},
                "aws_secret_access_key": {"type": "string", "required": True},
                "aws_region": {"type": "string", "default": "us-east-1"}
            }
        )
    
    def initialize(self) -> bool:
        try:
            import boto3
            self.aws_session = boto3.Session(
                aws_access_key_id=self.config.get('aws_access_key_id'),
                aws_secret_access_key=self.config.get('aws_secret_access_key'),
                region_name=self.config.get('aws_region', 'us-east-1')
            )
            return True
        except Exception as e:
            self.logger.error(f"AWS 擷取器初始化失敗: {e}")
            return False
    
    def cleanup(self):
        self.aws_session = None
    
    def extract_resources(self, region: str = None) -> Dict[str, Any]:
        # 實作 AWS 資源擷取邏輯
        return {}
    
    def get_supported_services(self) -> List[str]:
        return ["EC2", "VPC", "SecurityGroup", "S3", "RDS"]


class GCPExtractor(CloudExtractor):
    """GCP 擷取器範例"""
    
    def get_info(self) -> ModuleInfo:
        return ModuleInfo(
            name="GCP Extractor",
            module_type=ModuleType.EXTRACTOR,
            version="1.0.0",
            description="Google Cloud Platform 資源擷取器",
            author="Cloud Infrastructure Team",
            dependencies=["google-cloud-compute"],
            config_schema={
                "project_id": {"type": "string", "required": True},
                "credentials_path": {"type": "string", "required": False}
            }
        )
    
    def initialize(self) -> bool:
        try:
            from google.cloud import compute_v1
            self.compute_client = compute_v1.InstancesClient()
            return True
        except Exception as e:
            self.logger.error(f"GCP 擷取器初始化失敗: {e}")
            return False
    
    def cleanup(self):
        self.compute_client = None
    
    def extract_resources(self, region: str = None) -> Dict[str, Any]:
        # 實作 GCP 資源擷取邏輯
        return {}
    
    def get_supported_services(self) -> List[str]:
        return ["Compute", "VPC", "Firewall", "Storage", "SQL"]


class NetworkAnalyzer(SecurityAnalyzer):
    """網路分析器範例"""
    
    def get_info(self) -> ModuleInfo:
        return ModuleInfo(
            name="Network Analyzer",
            module_type=ModuleType.ANALYZER,
            version="1.0.0",
            description="網路安全分析器",
            author="Security Team",
            dependencies=["neo4j"],
            config_schema={
                "analysis_depth": {"type": "integer", "default": 3},
                "include_internal": {"type": "boolean", "default": True}
            }
        )
    
    def initialize(self) -> bool:
        return True
    
    def cleanup(self):
        pass
    
    def analyze(self, neo4j_session) -> List[Dict[str, Any]]:
        # 實作網路分析邏輯
        return []
    
    def get_analysis_types(self) -> List[str]:
        return ["network_segmentation", "traffic_flow", "security_groups"]


class DashboardVisualizer(Visualizer):
    """儀表板視覺化器範例"""
    
    def get_info(self) -> ModuleInfo:
        return ModuleInfo(
            name="Dashboard Visualizer",
            module_type=ModuleType.VISUALIZER,
            version="1.0.0",
            description="互動式儀表板視覺化器",
            author="UI Team",
            dependencies=["dash", "plotly"],
            config_schema={
                "theme": {"type": "string", "default": "light"},
                "port": {"type": "integer", "default": 8050}
            }
        )
    
    def initialize(self) -> bool:
        try:
            import dash
            import plotly
            return True
        except Exception as e:
            self.logger.error(f"儀表板視覺化器初始化失敗: {e}")
            return False
    
    def cleanup(self):
        pass
    
    def create_visualization(self, data: Dict[str, Any]) -> Any:
        """創建儀表板視覺化"""
        try:
            # 導入 SimpleDashboard
            from src.visualization.simple_dashboard import SimpleDashboard
            
            # 尋找最新的分析文件
            output_dir = "output"
            if os.path.exists(output_dir):
                files = [f for f in os.listdir(output_dir) if f.startswith('comprehensive_analysis_') and f.endswith('.json')]
                if files:
                    latest_file = max(files, key=lambda x: os.path.getctime(os.path.join(output_dir, x)))
                    analysis_file = os.path.join(output_dir, latest_file)
                    
                    # 創建儀表板實例
                    dashboard = SimpleDashboard(analysis_file)
                    return dashboard
                else:
                    self.logger.warning("未找到分析結果文件")
                    return None
            else:
                self.logger.warning("輸出目錄不存在")
                return None
                
        except Exception as e:
            self.logger.error(f"創建儀表板視覺化失敗: {e}")
            return None
    
    def get_visualization_types(self) -> List[str]:
        return ["network_topology", "security_dashboard", "cost_analysis"]


# 全域擴展管理器實例
extension_manager = ExtensionManager()

# 註冊視覺化模組
dashboard_viz = DashboardVisualizer()
extension_manager.registry.register_module(DashboardVisualizer, dashboard_viz.get_info())
