"""
成本優化分析模組

本模組提供成本優化分析功能，包括：
- 孤兒資源識別
- 未使用資源檢測
- 資源利用率分析
- 成本優化建議
"""

from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase
from loguru import logger


class CostOptimizationAnalyzer:
    """成本優化分析器"""
    
    def __init__(self, driver):
        """初始化分析器"""
        self.driver = driver
    
    def find_orphaned_ebs_volumes(self) -> List[Dict[str, Any]]:
        """
        找出孤兒 EBS 磁碟（未附加到任何 EC2 實例）
        
        Returns:
            孤兒 EBS 磁碟清單
        """
        query = """
        MATCH (volume:EBSVolume)
        WHERE NOT (volume)-[:ATTACHES_TO]->(:EC2Instance)
        RETURN 
            volume.volumeid AS VolumeId,
            volume.size AS Size,
            volume.volumetype AS VolumeType,
            volume.state AS State,
            volume.region AS Region
        ORDER BY volume.size DESC
        """
        
        try:
            with self.driver.session() as session:
                result = session.run(query)
                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"查詢孤兒 EBS 磁碟失敗: {e}")
            return []
    
    def find_unused_security_groups(self) -> List[Dict[str, Any]]:
        """
        找出未使用的安全群組
        
        Returns:
            未使用安全群組清單
        """
        query = """
        MATCH (sg:SecurityGroup)
        WHERE NOT (sg)<-[:IS_MEMBER_OF]-(:EC2Instance)
        RETURN 
            sg.name AS GroupName,
            sg.groupid AS GroupID,
            sg.description AS Description,
            sg.vpcid AS VpcId,
            COUNT { (sg)-[:HAS_RULE]->() } AS RuleCount
        ORDER BY sg.name
        """
        
        try:
            with self.driver.session() as session:
                result = session.run(query)
                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"查詢未使用安全群組失敗: {e}")
            return []
    
    def find_stopped_instances(self) -> List[Dict[str, Any]]:
        """
        找出已停止的 EC2 實例
        
        Returns:
            已停止實例清單
        """
        query = """
        MATCH (instance:EC2Instance)
        WHERE instance.state = 'stopped'
        RETURN 
            instance.name AS InstanceName,
            instance.instanceid AS InstanceID,
            instance.instancetype AS InstanceType,
            instance.launchtime AS LaunchTime,
            instance.region AS Region
        ORDER BY instance.launchtime DESC
        """
        
        try:
            with self.driver.session() as session:
                result = session.run(query)
                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"查詢已停止實例失敗: {e}")
            return []
    
    def find_underutilized_instances(self, min_uptime_days: int = 7) -> List[Dict[str, Any]]:
        """
        找出可能未充分利用的實例（需要結合監控資料）
        
        Args:
            min_uptime_days: 最小運行天數
            
        Returns:
            可能未充分利用的實例清單
        """
        query = """
        MATCH (instance:EC2Instance)
        WHERE instance.state = 'running'
        RETURN 
            instance.name AS InstanceName,
            instance.instanceid AS InstanceID,
            instance.instancetype AS InstanceType,
            instance.launchtime AS LaunchTime,
            instance.region AS Region
        ORDER BY instance.launchtime
        """
        
        try:
            with self.driver.session() as session:
                result = session.run(query)
                instances = [dict(record) for record in result]
                
                # 這裡可以加入更多邏輯來分析利用率
                # 例如：檢查實例類型、運行時間等
                return instances
        except Exception as e:
            logger.error(f"查詢未充分利用實例失敗: {e}")
            return []
    
    def analyze_storage_costs(self) -> List[Dict[str, Any]]:
        """
        分析儲存成本
        
        Returns:
            儲存成本分析結果
        """
        # EBS 磁碟分析
        ebs_query = """
        MATCH (volume:EBSVolume)
        RETURN 
            volume.volumetype AS VolumeType,
            sum(volume.size) AS TotalSize,
            count(volume) AS VolumeCount,
            avg(volume.size) AS AvgSize
        ORDER BY TotalSize DESC
        """
        
        # S3 儲存桶分析
        s3_query = """
        MATCH (bucket:S3Bucket)
        RETURN 
            bucket.region AS Region,
            count(bucket) AS BucketCount
        ORDER BY BucketCount DESC
        """
        
        try:
            with self.driver.session() as session:
                # 分析 EBS 磁碟
                ebs_result = session.run(ebs_query)
                ebs_analysis = [dict(record) for record in ebs_result]
                
                # 分析 S3 儲存桶
                s3_result = session.run(s3_query)
                s3_analysis = [dict(record) for record in s3_result]
                
                return {
                    'ebs_analysis': ebs_analysis,
                    's3_analysis': s3_analysis
                }
        except Exception as e:
            logger.error(f"分析儲存成本失敗: {e}")
            return {}
    
    def find_expensive_resources(self) -> List[Dict[str, Any]]:
        """
        找出可能昂貴的資源
        
        Returns:
            昂貴資源清單
        """
        # 大型實例
        large_instances_query = """
        MATCH (instance:EC2Instance)
        WHERE instance.state = 'running'
          AND (instance.instancetype CONTAINS 'large' 
               OR instance.instancetype CONTAINS 'xlarge'
               OR instance.instancetype CONTAINS '2xlarge'
               OR instance.instancetype CONTAINS '4xlarge')
        RETURN 
            instance.name AS InstanceName,
            instance.instanceid AS InstanceID,
            instance.instancetype AS InstanceType,
            instance.region AS Region
        ORDER BY instance.instancetype
        """
        
        # 高 IOPS 磁碟
        high_iops_volumes_query = """
        MATCH (volume:EBSVolume)
        WHERE volume.size > 100
        RETURN 
            volume.volumeid AS VolumeId,
            volume.volumetype AS VolumeType,
            volume.size AS Size,
            volume.region AS Region
        ORDER BY volume.size DESC
        """
        
        try:
            with self.driver.session() as session:
                # 查詢大型實例
                large_instances = session.run(large_instances_query)
                large_instances_list = [dict(record) for record in large_instances]
                
                # 查詢高 IOPS 磁碟
                high_iops_volumes = session.run(high_iops_volumes_query)
                high_iops_volumes_list = [dict(record) for record in high_iops_volumes]
                
                return {
                    'large_instances': large_instances_list,
                    'high_iops_volumes': high_iops_volumes_list
                }
        except Exception as e:
            logger.error(f"查詢昂貴資源失敗: {e}")
            return {}
    
    def calculate_potential_savings(self) -> Dict[str, Any]:
        """
        計算潛在節省成本
        
        Returns:
            潛在節省分析
        """
        try:
            with self.driver.session() as session:
                # 孤兒 EBS 磁碟
                orphaned_volumes = self.find_orphaned_ebs_volumes()
                orphaned_storage_gb = sum(vol.get('Size', 0) or 0 for vol in orphaned_volumes)
                
                # 未使用安全群組
                unused_sgs = self.find_unused_security_groups()
                
                # 已停止實例
                stopped_instances = self.find_stopped_instances()
                
                # 昂貴資源
                expensive_resources = self.find_expensive_resources()
                
                return {
                    'orphaned_ebs_volumes': {
                        'count': len(orphaned_volumes),
                        'total_size_gb': orphaned_storage_gb,
                        'estimated_monthly_cost': orphaned_storage_gb * 0.1  # 假設每 GB $0.1/月
                    },
                    'unused_security_groups': {
                        'count': len(unused_sgs),
                        'potential_savings': len(unused_sgs) * 0.1  # 假設每個安全群組 $0.1/月
                    },
                    'stopped_instances': {
                        'count': len(stopped_instances),
                        'potential_savings': len(stopped_instances) * 50  # 假設每個實例 $50/月
                    },
                    'expensive_resources': {
                        'large_instances_count': len(expensive_resources.get('large_instances', [])),
                        'high_iops_volumes_count': len(expensive_resources.get('high_iops_volumes', []))
                    }
                }
        except Exception as e:
            logger.error(f"計算潛在節省失敗: {e}")
            return {}
    
    def get_cost_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """
        獲取成本優化建議
        
        Returns:
            成本優化建議清單
        """
        recommendations = []
        
        try:
            # 孤兒 EBS 磁碟建議
            orphaned_volumes = self.find_orphaned_ebs_volumes()
            if orphaned_volumes:
                recommendations.append({
                    'type': 'orphaned_ebs_volumes',
                    'priority': 'high',
                    'title': '刪除孤兒 EBS 磁碟',
                    'description': f'發現 {len(orphaned_volumes)} 個未使用的 EBS 磁碟',
                    'action': '檢查並刪除未使用的 EBS 磁碟',
                    'potential_savings': f'約 ${len(orphaned_volumes) * 10}/月'
                })
            
            # 未使用安全群組建議
            unused_sgs = self.find_unused_security_groups()
            if unused_sgs:
                recommendations.append({
                    'type': 'unused_security_groups',
                    'priority': 'medium',
                    'title': '清理未使用安全群組',
                    'description': f'發現 {len(unused_sgs)} 個未使用的安全群組',
                    'action': '檢查並刪除未使用的安全群組',
                    'potential_savings': f'約 ${len(unused_sgs) * 0.1}/月'
                })
            
            # 已停止實例建議
            stopped_instances = self.find_stopped_instances()
            if stopped_instances:
                recommendations.append({
                    'type': 'stopped_instances',
                    'priority': 'high',
                    'title': '處理已停止實例',
                    'description': f'發現 {len(stopped_instances)} 個已停止的實例',
                    'action': '決定是否終止或重新啟動這些實例',
                    'potential_savings': f'約 ${len(stopped_instances) * 50}/月'
                })
            
            # 昂貴資源建議
            expensive_resources = self.find_expensive_resources()
            large_instances = expensive_resources.get('large_instances', [])
            if large_instances:
                recommendations.append({
                    'type': 'large_instances',
                    'priority': 'medium',
                    'title': '檢視大型實例使用情況',
                    'description': f'發現 {len(large_instances)} 個大型實例',
                    'action': '檢查這些實例是否真的需要如此大的規格',
                    'potential_savings': '視情況而定，可能節省 30-50% 成本'
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"獲取成本優化建議失敗: {e}")
            return []
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """
        獲取成本摘要報告
        
        Returns:
            成本摘要資訊
        """
        try:
            with self.driver.session() as session:
                # 基本統計
                stats_query = """
                MATCH (n)
                RETURN 
                    labels(n)[0] AS ResourceType,
                    count(n) AS Count
                ORDER BY Count DESC
                """
                
                stats_result = session.run(stats_query)
                resource_stats = {record['ResourceType']: record['Count'] for record in stats_result}
                
                # 潛在節省分析
                potential_savings = self.calculate_potential_savings()
                
                # 成本優化建議
                recommendations = self.get_cost_optimization_recommendations()
                
                return {
                    'resource_statistics': resource_stats,
                    'potential_savings': potential_savings,
                    'recommendations': recommendations,
                    'total_recommendations': len(recommendations)
                }
                
        except Exception as e:
            logger.error(f"獲取成本摘要失敗: {e}")
            return {}


# 使用範例
if __name__ == "__main__":
    from neo4j import GraphDatabase
    
    # 連接設定
    NEO4J_URI = "bolt://localhost:7687"
    NEO4J_USERNAME = "neo4j"
    NEO4J_PASSWORD = "password"
    
    try:
        # 創建驅動程式
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
        
        # 創建分析器
        analyzer = CostOptimizationAnalyzer(driver)
        
        print("=== 成本優化分析 ===")
        
        # 1. 孤兒 EBS 磁碟
        print("\n1. 孤兒 EBS 磁碟:")
        orphaned_volumes = analyzer.find_orphaned_ebs_volumes()
        for volume in orphaned_volumes[:5]:  # 只顯示前5個
            print(f"  - {volume['VolumeId']}: {volume['Size']}GB ({volume['VolumeType']})")
        
        # 2. 未使用安全群組
        print("\n2. 未使用安全群組:")
        unused_sgs = analyzer.find_unused_security_groups()
        for sg in unused_sgs[:5]:  # 只顯示前5個
            print(f"  - {sg['GroupName']} ({sg['GroupID']}): {sg['RuleCount']} 規則")
        
        # 3. 已停止實例
        print("\n3. 已停止實例:")
        stopped_instances = analyzer.find_stopped_instances()
        for instance in stopped_instances[:5]:  # 只顯示前5個
            print(f"  - {instance['InstanceName']} ({instance['InstanceID']}): {instance['InstanceType']}")
        
        # 4. 成本優化建議
        print("\n4. 成本優化建議:")
        recommendations = analyzer.get_cost_optimization_recommendations()
        for rec in recommendations:
            print(f"  - [{rec['priority'].upper()}] {rec['title']}: {rec['description']}")
            print(f"    建議: {rec['action']}")
            print(f"    潛在節省: {rec['potential_savings']}")
            print()
        
        # 5. 成本摘要
        print("5. 成本摘要:")
        summary = analyzer.get_cost_summary()
        print(f"  - 總建議數: {summary.get('total_recommendations', 0)}")
        
        # 關閉連接
        driver.close()
        
    except Exception as e:
        print(f"分析失敗: {e}")
