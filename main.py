"""
基於 Cartography 架構的改進主程式

這個主程式整合了所有基於 Cartography 分析的改進，
包括模組化架構、改進的資料模型、進階安全分析等。
"""

import argparse
import logging
import os
import sys
import time
from typing import Dict, Any, Optional

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.data_models import create_indexes, get_all_schemas
from src.neo4j_loader.neo4j_loader import ImprovedNeo4jLoader, LoadConfig
from src.rules.security_rules_engine import SecurityRulesEngine
from src.extensions.modular_architecture import ExtensionManager, ModuleType
# 導入分析模組
from src.analysis.security_analysis import SecurityAnalyzer
from src.analysis.failure_impact_analysis import FailureImpactAnalyzer
from src.analysis.cost_optimization import CostOptimizationAnalyzer

# 動態導入 AWS 提取器（如果可用）
try:
    from src.extractors.aws_extractor import AWSExtractor
    AWS_AVAILABLE = True
except ImportError:
    AWSExtractor = None
    AWS_AVAILABLE = False

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s:%(funcName)s:%(lineno)d - %(message)s'
)
logger = logging.getLogger(__name__)


class ImprovedCloudInfrastructureAnalyzer:
    """改進的雲端基礎設施分析器"""
    
    def __init__(self, config_path: str = '.env'):
        self.config = self._load_config(config_path)
        self.neo4j_loader = None
        self.rules_engine = None
        self.extension_manager = ExtensionManager()
        # 初始化分析器
        self.security_analyzer = None
        self.failure_analyzer = None
        self.cost_analyzer = None
        
        # 初始化組件
        self._initialize_components()
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """載入配置"""
        config = {
            'neo4j_uri': os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
            'neo4j_username': os.getenv('NEO4J_USERNAME', 'neo4j'),
            'neo4j_password': os.getenv('NEO4J_PASSWORD', 'password'),
            'neo4j_database': os.getenv('NEO4J_DATABASE', 'neo4j'),
            'aws_region': os.getenv('AWS_REGION', 'us-east-1'),
            'use_mock_data': os.getenv('USE_MOCK_DATA', 'false').lower() == 'true',
            'data_dir': os.getenv('DATA_DIR', 'data'),
            'output_dir': os.getenv('OUTPUT_DIR', 'output'),
            'log_level': os.getenv('LOG_LEVEL', 'INFO')
        }
        
        # 從檔案載入配置（如果存在）
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        config[key.lower()] = value
        
        return config
    
    def _initialize_components(self):
        """初始化組件"""
        try:
            # 初始化 Neo4j 載入器
            self.neo4j_loader = ImprovedNeo4jLoader(
                uri=self.config['neo4j_uri'],
                username=self.config['neo4j_username'],
                password=self.config['neo4j_password'],
                database=self.config['neo4j_database']
            )
            
            # 連接 Neo4j
            if not self.neo4j_loader.connect():
                raise RuntimeError("無法連接到 Neo4j")
            
            # 設定架構
            self.neo4j_loader.setup_schema()
            
            # 移除已刪除的模組初始化
            
            # 初始化安全規則引擎
            self.rules_engine = SecurityRulesEngine(self.neo4j_loader.session)
            
            # 初始化分析器
            self.security_analyzer = SecurityAnalyzer(self.neo4j_loader.driver)
            self.failure_analyzer = FailureImpactAnalyzer(self.neo4j_loader.driver)
            self.cost_analyzer = CostOptimizationAnalyzer(self.neo4j_loader.driver)
            
            # 載入擴展模組
            self._load_extensions()
            
            logger.info("所有組件初始化完成")
            
        except Exception as e:
            logger.error(f"初始化組件失敗: {e}")
            raise
    
    def _load_extensions(self):
        """載入擴展模組"""
        try:
            # 載入內建擴展
            from src.extensions.modular_architecture import (
                AWSExtractor, GCPExtractor, NetworkAnalyzer, DashboardVisualizer
            )
            
            # 註冊內建模組
            self.extension_manager.registry.register_module(
                AWSExtractor, AWSExtractor().get_info()
            )
            self.extension_manager.registry.register_module(
                GCPExtractor, GCPExtractor().get_info()
            )
            self.extension_manager.registry.register_module(
                NetworkAnalyzer, NetworkAnalyzer().get_info()
            )
            self.extension_manager.registry.register_module(
                DashboardVisualizer, DashboardVisualizer().get_info()
            )
            
            logger.info("擴展模組載入完成")
            
        except Exception as e:
            logger.warning(f"載入擴展模組失敗: {e}")
    
    def extract_data(self, provider: str = 'aws', region: str = None, 
                    use_mock: bool = False) -> bool:
        """擷取雲端資料"""
        try:
            if use_mock:
                logger.info("使用模擬資料模式...")
                return self._extract_mock_data()
            else:
                logger.info(f"擷取 {provider.upper()} 真實資料...")
                return self._extract_real_data(provider, region)
                
        except Exception as e:
            logger.error(f"資料擷取失敗: {e}")
            return False
    
    def _extract_mock_data(self) -> bool:
        """擷取模擬資料"""
        try:
            # 檢查是否已有增強版模擬資料
            mock_data_path = f"{self.config['data_dir']}/raw/enhanced_mock_aws_resources.json"
            if os.path.exists(mock_data_path):
                logger.info(f"找到現有增強版模擬資料: {mock_data_path}")
                return True
            
            # 生成增強版模擬資料
            logger.info("生成增強版模擬資料...")
            from scripts.create_mock_data import EnhancedMockAWSDataGenerator
            
            generator = EnhancedMockAWSDataGenerator()
            dataset = generator.generate_complete_dataset()
            
            # 儲存模擬資料
            os.makedirs(os.path.dirname(mock_data_path), exist_ok=True)
            import json
            with open(mock_data_path, 'w', encoding='utf-8') as f:
                json.dump(dataset, f, indent=2, ensure_ascii=False)
            
            logger.info(f"模擬資料已生成: {mock_data_path}")
            return True
            
        except Exception as e:
            logger.error(f"生成模擬資料失敗: {e}")
            return False
    
    def _extract_real_data(self, provider: str, region: str) -> bool:
        """擷取真實資料"""
        try:
            if provider.lower() == 'aws':
                if not AWS_AVAILABLE:
                    logger.error("AWS 提取器不可用，請安裝 boto3: pip install boto3")
                    return False
                
                # 使用真實 AWS 提取器
                extractor = AWSExtractor(region or self.config['aws_region'])
                resources = extractor.extract_all_resources()
                
                # 儲存到檔案
                output_path = f"data/raw/real_aws_resources_{region or self.config['aws_region']}_{int(time.time())}.json"
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                import json
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(resources, f, indent=2, ensure_ascii=False)
                
                logger.info(f"真實 AWS 資料已儲存至: {output_path}")
                return True
            else:
                logger.error(f"不支援的雲端提供商: {provider}")
                return False
            
        except Exception as e:
            logger.error(f"擷取真實資料失敗: {e}")
            return False
    
    def load_to_neo4j(self, data_path: str = None) -> bool:
        """載入資料到 Neo4j"""
        try:
            if not self.neo4j_loader:
                logger.error("Neo4j 載入器未初始化")
                return False
            
            # 確定資料路徑
            if not data_path:
                # 尋找最新的資料檔案
                data_dir = f"{self.config['data_dir']}/raw"
                if os.path.exists(data_dir):
                    files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
                    if files:
                        data_path = os.path.join(data_dir, sorted(files)[-1])
                    else:
                        logger.error("未找到資料檔案")
                        return False
                else:
                    logger.error("資料目錄不存在")
                    return False
            
            # 載入資料
            import json
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 使用改進的載入器
            success = self.neo4j_loader.load_aws_data(
                data, 
                region=self.config['aws_region'],
                account_id='123456789012'  # 模擬帳戶 ID
            )
            
            if success:
                # 獲取統計資訊
                stats = self.neo4j_loader.get_statistics()
                logger.info(f"資料載入完成，統計資訊: {stats}")
            
            return success
            
        except Exception as e:
            logger.error(f"載入資料到 Neo4j 失敗: {e}")
            return False
    
    def run_analysis(self, rule_ids: list = None) -> Optional[Dict[str, Any]]:
        """執行安全分析"""
        try:
            if not self.rules_engine:
                logger.error("安全規則引擎未初始化")
                return None
            
            logger.info("開始執行安全分析...")
            
            # 執行分析
            findings = self.rules_engine.run_analysis(rule_ids)
            
            # 獲取摘要
            summary = self.rules_engine.get_summary(findings)
            
            # 儲存結果
            output_path = f"{self.config['output_dir']}/analysis_results_{int(time.time())}.json"
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            import json
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'summary': summary,
                    'findings': [
                        {
                            'rule_id': finding.rule_id,
                            'rule_name': finding.rule_name,
                            'severity': finding.severity.value,
                            'description': finding.description,
                            'affected_resources': finding.affected_resources,
                            'recommendation': finding.recommendation,
                            'metadata': finding.metadata
                        }
                        for finding in findings
                    ]
                }, f, indent=2, ensure_ascii=False)
            
            logger.info(f"安全分析完成，結果儲存至: {output_path}")
            logger.info(f"分析摘要: {summary}")
            
            return {
                'summary': summary,
                'findings': findings,
                'output_path': output_path
            }
            
        except Exception as e:
            logger.error(f"執行安全分析失敗: {e}")
            return None
    
    def run_advanced_analysis(self, analysis_type: str = 'security') -> Dict[str, Any]:
        """執行進階分析（基於 Cartography 架構）"""
        try:
            logger.info(f"開始執行進階 {analysis_type} 分析")
            
            if not self.neo4j_loader:
                logger.error("Neo4j 載入器未初始化")
                return {}
            
            # 使用整合後的進階分析功能
            findings = self.neo4j_loader.run_analysis_advanced(analysis_type)
            
            # 儲存結果
            output_path = f"{self.config['output_dir']}/advanced_analysis_{analysis_type}_{int(time.time())}.json"
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            import json
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'analysis_type': analysis_type,
                    'findings': findings,
                    'timestamp': time.time()
                }, f, indent=2, ensure_ascii=False)
            
            logger.info(f"進階分析完成，結果儲存至: {output_path}")
            return {'findings': findings, 'output_path': output_path}
                
        except Exception as e:
            logger.error(f"進階分析執行失敗: {e}")
            return {}
    
    def run_comprehensive_analysis(self) -> Dict[str, Any]:
        """執行綜合分析（資安、故障衝擊、成本優化）"""
        try:
            logger.info("開始執行綜合分析")
            
            if not all([self.security_analyzer, self.failure_analyzer, self.cost_analyzer]):
                logger.error("分析器未完全初始化")
                return {}
            
            results = {}
            
            # 1. 資安漏洞分析
            logger.info("執行資安漏洞分析...")
            security_summary = self.security_analyzer.get_security_summary()
            exposed_services = self.security_analyzer.find_exposed_services()
            permissive_rules = self.security_analyzer.find_overly_permissive_rules()
            unencrypted_resources = self.security_analyzer.find_unencrypted_resources()
            
            results['security'] = {
                'summary': security_summary,
                'exposed_services': exposed_services,
                'permissive_rules': permissive_rules,
                'unencrypted_resources': unencrypted_resources
            }
            
            # 2. 故障衝擊分析
            logger.info("執行故障衝擊分析...")
            failure_summary = self.failure_analyzer.get_failure_impact_summary()
            critical_nodes = self.failure_analyzer.identify_critical_nodes()
            single_points = self.failure_analyzer.find_single_points_of_failure()
            
            results['failure_impact'] = {
                'summary': failure_summary,
                'critical_nodes': critical_nodes,
                'single_points_of_failure': single_points
            }
            
            # 3. 成本優化分析
            logger.info("執行成本優化分析...")
            cost_summary = self.cost_analyzer.get_cost_summary()
            orphaned_volumes = self.cost_analyzer.find_orphaned_ebs_volumes()
            unused_sgs = self.cost_analyzer.find_unused_security_groups()
            stopped_instances = self.cost_analyzer.find_stopped_instances()
            recommendations = self.cost_analyzer.get_cost_optimization_recommendations()
            
            results['cost_optimization'] = {
                'summary': cost_summary,
                'orphaned_volumes': orphaned_volumes,
                'unused_security_groups': unused_sgs,
                'stopped_instances': stopped_instances,
                'recommendations': recommendations
            }
            
            # 儲存綜合分析結果
            output_path = f"{self.config['output_dir']}/comprehensive_analysis_{int(time.time())}.json"
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            import json
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'analysis_type': 'comprehensive',
                    'results': results,
                    'timestamp': time.time()
                }, f, indent=2, ensure_ascii=False)
            
            logger.info(f"綜合分析完成，結果儲存至: {output_path}")
            return {'results': results, 'output_path': output_path}
                
        except Exception as e:
            logger.error(f"綜合分析執行失敗: {e}")
            return {}
    
    def start_dashboard(self, host: str = '127.0.0.1', port: int = 8050):
        """啟動視覺化儀表板"""
        try:
            # 獲取視覺化器
            visualizer = self.extension_manager.get_visualizer('dashboard')
            if not visualizer:
                logger.error("儀表板視覺化器不可用")
                return False
            
            # 初始化視覺化器
            if not visualizer.initialize():
                logger.error("儀表板視覺化器初始化失敗")
                return False
            
            logger.info(f"啟動儀表板: http://{host}:{port}")
            
            # 這裡應該啟動實際的儀表板
            # 由於這是範例，我們只是記錄日誌
            logger.info("儀表板已啟動（範例模式）")
            
            return True
            
        except Exception as e:
            logger.error(f"啟動儀表板失敗: {e}")
            return False
    
    def run_full_pipeline(self, provider: str = 'aws', region: str = None, 
                         use_mock: bool = False) -> bool:
        """執行完整分析流程"""
        try:
            logger.info("開始執行完整分析流程...")
            
            # 1. 擷取資料
            if not self.extract_data(provider, region, use_mock):
                return False
            
            # 2. 載入到 Neo4j
            if not self.load_to_neo4j():
                return False
            
            # 3. 執行分析
            results = self.run_analysis()
            if not results:
                return False
            
            # 4. 啟動儀表板（可選）
            # self.start_dashboard()
            
            logger.info("完整分析流程執行完成")
            return True
            
        except Exception as e:
            logger.error(f"執行完整流程失敗: {e}")
            return False
    
    def cleanup(self):
        """清理資源"""
        try:
            if self.neo4j_loader:
                self.neo4j_loader.close()
            
            logger.info("資源清理完成")
            
        except Exception as e:
            logger.error(f"資源清理失敗: {e}")


def main():
    """主程式入口"""
    parser = argparse.ArgumentParser(description='改進的雲端基礎設施視覺化分析平台')
    parser.add_argument('--mode', choices=['extract', 'load', 'analyze', 'advanced-analyze', 'comprehensive-analyze', 'dashboard', 'full'],
                       default='full', help='執行模式')
    parser.add_argument('--provider', default='aws', help='雲端提供商 (aws, gcp, azure)')
    parser.add_argument('--region', default='us-east-1', help='雲端區域')
    parser.add_argument('--data-path', help='資料檔案路徑')
    parser.add_argument('--host', default='127.0.0.1', help='儀表板主機位址')
    parser.add_argument('--port', type=int, default=8050, help='儀表板連接埠')
    parser.add_argument('--config', default='.env', help='設定檔路徑')
    parser.add_argument('--mock', action='store_true', default=True, help='使用模擬資料（免費測試）')
    parser.add_argument('--rules', nargs='*', help='指定要執行的安全規則')
    parser.add_argument('--analysis-type', choices=['security', 'cost'], default='security', 
                       help='進階分析類型')
    
    args = parser.parse_args()
    
    # 創建分析器
    analyzer = ImprovedCloudInfrastructureAnalyzer(args.config)
    
    try:
        if args.mode == 'extract':
            success = analyzer.extract_data(args.provider, args.region, use_mock=args.mock)
        elif args.mode == 'load':
            success = analyzer.load_to_neo4j(args.data_path)
        elif args.mode == 'analyze':
            success = analyzer.run_analysis(args.rules) is not None
        elif args.mode == 'advanced-analyze':
            result = analyzer.run_advanced_analysis(args.analysis_type)
            success = bool(result)
        elif args.mode == 'comprehensive-analyze':
            result = analyzer.run_comprehensive_analysis()
            success = bool(result)
        elif args.mode == 'dashboard':
            analyzer.start_dashboard(args.host, args.port)
            success = True
        elif args.mode == 'full':
            success = analyzer.run_full_pipeline(args.provider, args.region, use_mock=args.mock)
        else:
            logger.error(f"未知的執行模式: {args.mode}")
            success = False
        
        if success:
            logger.info("執行成功")
        else:
            logger.error("執行失敗")
            sys.exit(1)
    
    except KeyboardInterrupt:
        logger.info("使用者中斷執行")
    except Exception as e:
        logger.error(f"執行失敗: {e}")
        sys.exit(1)
    finally:
        analyzer.cleanup()


if __name__ == '__main__':
    main()
