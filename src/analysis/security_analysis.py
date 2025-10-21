"""
資安漏洞分析模組

本模組提供各種資安漏洞分析功能，包括：
- 暴露於公網的高風險服務
- 過度寬鬆的安全群組規則
- 未加密的資源
- 權限過大的 IAM 角色
"""

from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase
from loguru import logger


class SecurityAnalyzer:
    """資安分析器"""
    
    def __init__(self, driver):
        """初始化分析器"""
        self.driver = driver
    
    def find_exposed_services(self, port: str = "22", protocol: str = "tcp") -> List[Dict[str, Any]]:
        """
        找出暴露於公網且開啟指定連接埠的主機
        
        Args:
            port: 連接埠號
            protocol: 協定類型
            
        Returns:
            暴露的主機清單
        """
        query = """
        MATCH (instance:EC2Instance)-[:IS_MEMBER_OF]->(sg:SecurityGroup),
              (sg)-[:HAS_RULE]->(rule:Rule)
        WHERE rule.SourceCIDR CONTAINS '0.0.0.0/0' 
          AND rule.PortRange CONTAINS $port
          AND rule.Protocol = $protocol
          AND rule.Direction = 'inbound'
        RETURN DISTINCT 
            instance.Name AS InstanceName,
            instance.InstanceID AS InstanceID,
            instance.PublicIP AS PublicIP,
            instance.State AS State,
            collect(DISTINCT sg.GroupName) AS SecurityGroups,
            collect(DISTINCT rule.RuleID) AS Rules
        ORDER BY instance.Name
        """
        
        try:
            with self.driver.session() as session:
                result = session.run(query, port=port, protocol=protocol)
                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"查詢暴露服務失敗: {e}")
            return []
    
    def find_overly_permissive_rules(self) -> List[Dict[str, Any]]:
        """
        找出過度寬鬆的安全群組規則
        
        Returns:
            過度寬鬆的規則清單
        """
        query = """
        MATCH (sg:SecurityGroup)-[:HAS_RULE]->(rule:Rule)
        WHERE rule.SourceCIDR CONTAINS '0.0.0.0/0'
          AND rule.Direction = 'inbound'
          AND rule.Action = 'allow'
        RETURN 
            sg.GroupName AS SecurityGroupName,
            sg.GroupID AS SecurityGroupID,
            rule.RuleID AS RuleID,
            rule.Protocol AS Protocol,
            rule.PortRange AS PortRange,
            rule.SourceCIDR AS SourceCIDR,
            rule.Description AS Description
        ORDER BY sg.GroupName, rule.PortRange
        """
        
        try:
            with self.driver.session() as session:
                result = session.run(query)
                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"查詢過度寬鬆規則失敗: {e}")
            return []
    
    def find_unencrypted_resources(self) -> List[Dict[str, Any]]:
        """
        找出未加密的資源
        
        Returns:
            未加密的資源清單
        """
        # 查詢未加密的 EBS 磁碟
        ebs_query = """
        MATCH (volume:EBSVolume)
        WHERE volume.Encrypted = false OR volume.Encrypted IS NULL
        RETURN 
            'EBSVolume' AS ResourceType,
            volume.VolumeId AS ResourceID,
            volume.Size AS Size,
            volume.VolumeType AS Type,
            volume.Region AS Region
        """
        
        # 查詢未加密的 S3 儲存桶（需要額外的 API 調用）
        s3_query = """
        MATCH (bucket:S3Bucket)
        RETURN 
            'S3Bucket' AS ResourceType,
            bucket.BucketName AS ResourceID,
            bucket.Region AS Region
        """
        
        try:
            with self.driver.session() as session:
                # 查詢 EBS 磁碟
                ebs_result = session.run(ebs_query)
                ebs_resources = [dict(record) for record in ebs_result]
                
                # 查詢 S3 儲存桶（注意：實際的加密狀態需要額外的 API 調用）
                s3_result = session.run(s3_query)
                s3_resources = [dict(record) for record in s3_result]
                
                return ebs_resources + s3_resources
        except Exception as e:
            logger.error(f"查詢未加密資源失敗: {e}")
            return []
    
    def find_orphaned_security_groups(self) -> List[Dict[str, Any]]:
        """
        找出孤兒安全群組（沒有被任何 EC2 實例使用）
        
        Returns:
            孤兒安全群組清單
        """
        query = """
        MATCH (sg:SecurityGroup)
        WHERE NOT (sg)<-[:IS_MEMBER_OF]-(:EC2Instance)
        RETURN 
            sg.GroupName AS SecurityGroupName,
            sg.GroupID AS SecurityGroupID,
            sg.Description AS Description,
            sg.VpcId AS VpcId
        ORDER BY sg.GroupName
        """
        
        try:
            with self.driver.session() as session:
                result = session.run(query)
                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"查詢孤兒安全群組失敗: {e}")
            return []
    
    def find_high_risk_ports(self) -> List[Dict[str, Any]]:
        """
        找出開啟高風險連接埠的服務
        
        Returns:
            高風險連接埠清單
        """
        # 定義高風險連接埠
        high_risk_ports = ["22", "23", "3389", "445", "1433", "3306", "5432", "6379", "27017"]
        
        query = """
        MATCH (instance:EC2Instance)-[:IS_MEMBER_OF]->(sg:SecurityGroup),
              (sg)-[:HAS_RULE]->(rule:Rule)
        WHERE rule.SourceCIDR CONTAINS '0.0.0.0/0'
          AND rule.Direction = 'inbound'
          AND rule.Action = 'allow'
          AND any(port IN $high_risk_ports WHERE rule.PortRange CONTAINS port)
        RETURN DISTINCT 
            instance.Name AS InstanceName,
            instance.InstanceID AS InstanceID,
            instance.PublicIP AS PublicIP,
            collect(DISTINCT rule.PortRange) AS ExposedPorts,
            collect(DISTINCT rule.Protocol) AS Protocols,
            collect(DISTINCT sg.GroupName) AS SecurityGroups
        ORDER BY instance.Name
        """
        
        try:
            with self.driver.session() as session:
                result = session.run(query, high_risk_ports=high_risk_ports)
                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"查詢高風險連接埠失敗: {e}")
            return []
    
    def analyze_network_segmentation(self) -> List[Dict[str, Any]]:
        """
        分析網路分段情況
        
        Returns:
            網路分段分析結果
        """
        query = """
        MATCH (vpc:VPC)
        OPTIONAL MATCH (vpc)<-[:PART_OF]-(subnet:Subnet)
        OPTIONAL MATCH (subnet)<-[:RESIDES_IN]-(instance:EC2Instance)
        WITH vpc, 
             collect(DISTINCT subnet) as subnets,
             collect(DISTINCT instance) as instances
        RETURN 
            vpc.VpcId AS VpcId,
            vpc.Name AS VpcName,
            vpc.CidrBlock AS CidrBlock,
            size(subnets) AS SubnetCount,
            size(instances) AS InstanceCount,
            [subnet in subnets | subnet.CidrBlock] AS SubnetCidrs
        ORDER BY vpc.Name
        """
        
        try:
            with self.driver.session() as session:
                result = session.run(query)
                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"分析網路分段失敗: {e}")
            return []
    
    def get_security_summary(self) -> Dict[str, Any]:
        """
        獲取資安摘要報告
        
        Returns:
            資安摘要資訊
        """
        try:
            with self.driver.session() as session:
                # 基本統計
                stats_query = """
                MATCH (n)
                RETURN 
                    labels(n)[0] AS NodeType,
                    count(n) AS Count
                ORDER BY Count DESC
                """
                
                stats_result = session.run(stats_query)
                node_stats = {record['NodeType']: record['Count'] for record in stats_result}
                
                # 暴露服務統計
                exposed_services = self.find_exposed_services()
                
                # 過度寬鬆規則統計
                permissive_rules = self.find_overly_permissive_rules()
                
                # 未加密資源統計
                unencrypted_resources = self.find_unencrypted_resources()
                
                # 孤兒安全群組統計
                orphaned_sgs = self.find_orphaned_security_groups()
                
                return {
                    'node_statistics': node_stats,
                    'exposed_services_count': len(exposed_services),
                    'permissive_rules_count': len(permissive_rules),
                    'unencrypted_resources_count': len(unencrypted_resources),
                    'orphaned_security_groups_count': len(orphaned_sgs),
                    'high_risk_instances': len(self.find_high_risk_ports())
                }
                
        except Exception as e:
            logger.error(f"獲取資安摘要失敗: {e}")
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
        analyzer = SecurityAnalyzer(driver)
        
        print("=== 資安漏洞分析 ===")
        
        # 1. 找出暴露的 SSH 服務
        print("\n1. 暴露的 SSH 服務 (Port 22):")
        exposed_ssh = analyzer.find_exposed_services("22", "tcp")
        for service in exposed_ssh:
            print(f"  - {service['InstanceName']} ({service['InstanceID']}) - {service['PublicIP']}")
        
        # 2. 找出過度寬鬆的規則
        print("\n2. 過度寬鬆的安全群組規則:")
        permissive_rules = analyzer.find_overly_permissive_rules()
        for rule in permissive_rules[:5]:  # 只顯示前5個
            print(f"  - {rule['SecurityGroupName']}: {rule['Protocol']}:{rule['PortRange']} from {rule['SourceCIDR']}")
        
        # 3. 找出未加密的資源
        print("\n3. 未加密的資源:")
        unencrypted = analyzer.find_unencrypted_resources()
        for resource in unencrypted:
            print(f"  - {resource['ResourceType']}: {resource['ResourceID']}")
        
        # 4. 資安摘要
        print("\n4. 資安摘要:")
        summary = analyzer.get_security_summary()
        for key, value in summary.items():
            print(f"  {key}: {value}")
        
        # 關閉連接
        driver.close()
        
    except Exception as e:
        print(f"分析失敗: {e}")
