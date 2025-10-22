"""
故障衝擊分析模組

本模組提供故障衝擊分析功能，包括：
- 依賴關係分析
- 故障傳播路徑
- 關鍵節點識別
- 影響範圍評估
"""

from typing import List, Dict, Any, Optional, Tuple
from neo4j import GraphDatabase
from loguru import logger


class FailureImpactAnalyzer:
    """故障衝擊分析器"""
    
    def __init__(self, driver):
        """初始化分析器"""
        self.driver = driver
    
    def find_dependencies(self, resource_id: str, max_depth: int = 5) -> List[Dict[str, Any]]:
        """
        找出指定資源的所有依賴關係
        
        Args:
            resource_id: 資源 ID
            max_depth: 最大搜尋深度
            
        Returns:
            依賴關係清單
        """
        query = """
        MATCH path = (start)-[*1..$max_depth]-(dependent)
        WHERE start.InstanceID = $resource_id OR start.GroupID = $resource_id OR start.VpcId = $resource_id
        RETURN 
            start,
            dependent,
            length(path) as depth,
            relationships(path) as relationships
        ORDER BY depth
        """
        
        try:
            with self.driver.session() as session:
                result = session.run(query, resource_id=resource_id, max_depth=max_depth)
                dependencies = []
                
                for record in result:
                    start_node = dict(record['start'])
                    dependent_node = dict(record['dependent'])
                    depth = record['depth']
                    relationships = [dict(rel) for rel in record['relationships']]
                    
                    dependencies.append({
                        'start_resource': start_node,
                        'dependent_resource': dependent_node,
                        'depth': depth,
                        'relationships': relationships
                    })
                
                return dependencies
                
        except Exception as e:
            logger.error(f"查詢依賴關係失敗: {e}")
            return []
    
    def analyze_failure_propagation(self, failed_resource_id: str) -> List[Dict[str, Any]]:
        """
        分析故障傳播路徑
        
        Args:
            failed_resource_id: 故障資源 ID
            
        Returns:
            故障傳播路徑清單
        """
        query = """
        MATCH path = (failed)-[*1..10]->(affected)
        WHERE failed.InstanceID = $failed_resource_id 
           OR failed.GroupID = $failed_resource_id
           OR failed.VpcId = $failed_resource_id
        RETURN 
            failed,
            affected,
            length(path) as propagation_depth,
            [node in nodes(path) | {
                id: coalesce(node.InstanceID, node.GroupID, node.VpcId, node.SubnetId),
                type: labels(node)[0],
                name: coalesce(node.Name, node.GroupName, node.BucketName)
            }] as propagation_path
        ORDER BY propagation_depth
        """
        
        try:
            with self.driver.session() as session:
                result = session.run(query, failed_resource_id=failed_resource_id)
                propagation_paths = []
                
                for record in result:
                    failed_node = dict(record['failed'])
                    affected_node = dict(record['affected'])
                    depth = record['propagation_depth']
                    path = record['propagation_path']
                    
                    propagation_paths.append({
                        'failed_resource': failed_node,
                        'affected_resource': affected_node,
                        'propagation_depth': depth,
                        'propagation_path': path
                    })
                
                return propagation_paths
                
        except Exception as e:
            logger.error(f"分析故障傳播失敗: {e}")
            return []
    
    def identify_critical_nodes(self, min_connections: int = 5) -> List[Dict[str, Any]]:
        """
        識別關鍵節點（連接度高的節點）
        
        Args:
            min_connections: 最小連接數
            
        Returns:
            關鍵節點清單
        """
        query = """
        MATCH (n)
        WITH n, COUNT { (n)--() } as connection_count
        WHERE connection_count >= $min_connections
        RETURN 
            n,
            connection_count,
            labels(n)[0] as node_type
        ORDER BY connection_count DESC
        """
        
        try:
            with self.driver.session() as session:
                result = session.run(query, min_connections=min_connections)
                critical_nodes = []
                
                for record in result:
                    node = dict(record['n'])
                    connection_count = record['connection_count']
                    node_type = record['node_type']
                    
                    critical_nodes.append({
                        'node': node,
                        'connection_count': connection_count,
                        'node_type': node_type
                    })
                
                return critical_nodes
                
        except Exception as e:
            logger.error(f"識別關鍵節點失敗: {e}")
            return []
    
    def find_single_points_of_failure(self) -> List[Dict[str, Any]]:
        """
        找出單點故障（只有一個連接的節點）
        
        Returns:
            單點故障清單
        """
        query = """
        MATCH (n)
        WITH n, COUNT { (n)--() } as connection_count
        WHERE connection_count = 1
        RETURN 
            n,
            connection_count,
            labels(n)[0] as node_type,
            [(n)--(connected) | connected] as connected_nodes
        ORDER BY node_type
        """
        
        try:
            with self.driver.session() as session:
                result = session.run(query)
                single_points = []
                
                for record in result:
                    node = dict(record['n'])
                    connection_count = record['connection_count']
                    node_type = record['node_type']
                    connected_nodes = [dict(connected) for connected in record['connected_nodes']]
                    
                    single_points.append({
                        'node': node,
                        'connection_count': connection_count,
                        'node_type': node_type,
                        'connected_nodes': connected_nodes
                    })
                
                return single_points
                
        except Exception as e:
            logger.error(f"找出單點故障失敗: {e}")
            return []
    
    def analyze_network_redundancy(self) -> List[Dict[str, Any]]:
        """
        分析網路冗餘性
        
        Returns:
            網路冗餘性分析結果
        """
        query = """
        MATCH (vpc:VPC)
        OPTIONAL MATCH (subnet:Subnet)-[:LOCATED_IN]->(vpc)
        OPTIONAL MATCH (instance:EC2Instance)-[:LOCATED_IN]->(subnet)
        WITH vpc, 
             collect(DISTINCT subnet) as subnets,
             collect(DISTINCT instance) as instances
        RETURN 
            vpc.VpcId as VpcId,
            vpc.Name as VpcName,
            size(subnets) as SubnetCount,
            size(instances) as InstanceCount,
            [subnet in subnets | {
                id: subnet.SubnetId,
                az: subnet.AvailabilityZone,
                cidr: subnet.CidrBlock,
                instance_count: COUNT { (instance:EC2Instance)-[:LOCATED_IN]->(subnet) }
            }] as subnet_details
        ORDER BY vpc.vpcid
        """
        
        try:
            with self.driver.session() as session:
                result = session.run(query)
                return [dict(record) for record in result]
                
        except Exception as e:
            logger.error(f"分析網路冗餘性失敗: {e}")
            return []
    
    def calculate_impact_score(self, resource_id: str) -> Dict[str, Any]:
        """
        計算資源的影響分數
        
        Args:
            resource_id: 資源 ID
            
        Returns:
            影響分數資訊
        """
        try:
            with self.driver.session() as session:
                # 計算直接連接數
                direct_connections_query = """
                MATCH (n)
                WHERE n.InstanceID = $resource_id OR n.GroupID = $resource_id OR n.VpcId = $resource_id
                RETURN size((n)--()) as direct_connections
                """
                
                # 計算間接影響範圍
                indirect_impact_query = """
                MATCH (n)-[*1..3]-(affected)
                WHERE n.InstanceID = $resource_id OR n.GroupID = $resource_id OR n.VpcId = $resource_id
                RETURN count(DISTINCT affected) as indirect_impact
                """
                
                # 計算關鍵性指標
                criticality_query = """
                MATCH (n)
                WHERE n.InstanceID = $resource_id OR n.GroupID = $resource_id OR n.VpcId = $resource_id
                WITH n, size((n)--()) as connections
                MATCH (n)-[*1..2]-(related)
                WITH n, connections, count(DISTINCT related) as reachable_nodes
                RETURN 
                    connections as direct_connections,
                    reachable_nodes as reachable_nodes,
                    connections * reachable_nodes as impact_score
                """
                
                result = session.run(criticality_query, resource_id=resource_id)
                record = result.single()
                
                if record:
                    return {
                        'resource_id': resource_id,
                        'direct_connections': record['direct_connections'],
                        'reachable_nodes': record['reachable_nodes'],
                        'impact_score': record['impact_score']
                    }
                else:
                    return {
                        'resource_id': resource_id,
                        'direct_connections': 0,
                        'reachable_nodes': 0,
                        'impact_score': 0
                    }
                    
        except Exception as e:
            logger.error(f"計算影響分數失敗: {e}")
            return {}
    
    def get_failure_impact_summary(self) -> Dict[str, Any]:
        """
        獲取故障衝擊摘要報告
        
        Returns:
            故障衝擊摘要資訊
        """
        try:
            with self.driver.session() as session:
                # 基本統計
                stats_query = """
                MATCH (n)
                WITH labels(n)[0] AS NodeType, n, COUNT { (n)--() } as connections
                RETURN 
                    NodeType,
                    count(n) AS Count,
                    avg(connections) AS AvgConnections
                ORDER BY Count DESC
                """
                
                stats_result = session.run(stats_query)
                node_stats = [dict(record) for record in stats_result]
                
                # 關鍵節點統計
                critical_nodes = self.identify_critical_nodes(min_connections=3)
                
                # 單點故障統計
                single_points = self.find_single_points_of_failure()
                
                # 網路冗餘性分析
                network_redundancy = self.analyze_network_redundancy()
                
                return {
                    'node_statistics': node_stats,
                    'critical_nodes_count': len(critical_nodes),
                    'single_points_of_failure_count': len(single_points),
                    'network_redundancy_analysis': network_redundancy,
                    'top_critical_nodes': critical_nodes[:10]  # 前10個關鍵節點
                }
                
        except Exception as e:
            logger.error(f"獲取故障衝擊摘要失敗: {e}")
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
        analyzer = FailureImpactAnalyzer(driver)
        
        print("=== 故障衝擊分析 ===")
        
        # 1. 找出關鍵節點
        print("\n1. 關鍵節點 (連接數 >= 3):")
        critical_nodes = analyzer.identify_critical_nodes(min_connections=3)
        for node_info in critical_nodes[:5]:  # 只顯示前5個
            node = node_info['node']
            print(f"  - {node.get('Name', node.get('GroupName', 'Unknown'))}: {node_info['connection_count']} 連接")
        
        # 2. 找出單點故障
        print("\n2. 單點故障:")
        single_points = analyzer.find_single_points_of_failure()
        for sp in single_points[:5]:  # 只顯示前5個
            node = sp['node']
            print(f"  - {node.get('Name', node.get('GroupName', 'Unknown'))} ({sp['node_type']})")
        
        # 3. 分析特定資源的影響
        if critical_nodes:
            test_resource = critical_nodes[0]['node']
            resource_id = test_resource.get('InstanceID', test_resource.get('GroupID', test_resource.get('VpcId')))
            if resource_id:
                print(f"\n3. 資源 {resource_id} 的影響分析:")
                impact_score = analyzer.calculate_impact_score(resource_id)
                print(f"  - 直接連接: {impact_score.get('direct_connections', 0)}")
                print(f"  - 可達節點: {impact_score.get('reachable_nodes', 0)}")
                print(f"  - 影響分數: {impact_score.get('impact_score', 0)}")
        
        # 4. 故障衝擊摘要
        print("\n4. 故障衝擊摘要:")
        summary = analyzer.get_failure_impact_summary()
        print(f"  - 關鍵節點數量: {summary.get('critical_nodes_count', 0)}")
        print(f"  - 單點故障數量: {summary.get('single_points_of_failure_count', 0)}")
        
        # 關閉連接
        driver.close()
        
    except Exception as e:
        print(f"分析失敗: {e}")
