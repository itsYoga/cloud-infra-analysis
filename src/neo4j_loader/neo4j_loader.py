"""
基於 Cartography 架構的改進 Neo4j 載入器

這個模組實作了更高效、可擴展的資料載入機制，
參考了 Cartography 的批次處理和事務管理最佳實踐。
"""

import time
import logging
from typing import Dict, List, Any, Optional, Union
from functools import wraps
from dataclasses import dataclass

import neo4j
from neo4j import GraphDatabase

# 嘗試導入 backoff 用於重試機制
try:
    import backoff
    from neo4j.exceptions import ServiceUnavailable, SessionExpired, TransientError
    BACKOFF_AVAILABLE = True
except ImportError:
    BACKOFF_AVAILABLE = False
    # 提供虛擬類別以避免導入錯誤
    class ServiceUnavailable(Exception): pass
    class SessionExpired(Exception): pass
    class TransientError(Exception): pass
    def backoff(*args, **kwargs): return lambda x: x

from ..data_models import (
    CartographyNodeSchema, 
    CartographyRelSchema,
    create_indexes,
    get_schema,
    get_all_schemas
)

logger = logging.getLogger(__name__)


def timeit(func):
    """計時裝飾器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        logger.info(f"{func.__name__} 執行時間: {end_time - start_time:.2f} 秒")
        return result
    return wrapper


@dataclass
class LoadConfig:
    """載入配置"""
    batch_size: int = 10000  # 增加批次大小
    max_retries: int = 5     # 增加重試次數
    retry_delay: float = 1.0
    create_indexes: bool = True
    cleanup_old_data: bool = True
    use_advanced_loading: bool = True  # 啟用進階載入功能


class ImprovedNeo4jLoader:
    """改進的 Neo4j 載入器，基於 Cartography 架構"""
    
    def __init__(self, uri: str, username: str, password: str, database: str = "neo4j"):
        self.uri = uri
        self.username = username
        self.password = password
        self.database = database
        self.driver = None
        self.session = None
        self.update_tag = int(time.time())
        
    def connect(self) -> bool:
        """連接到 Neo4j"""
        try:
            self.driver = GraphDatabase.driver(
                self.uri, 
                auth=(self.username, self.password)
            )
            self.session = self.driver.session(database=self.database)
            
            # 測試連接
            self.session.run("RETURN 1")
            logger.info("成功連接到 Neo4j")
            return True
            
        except Exception as e:
            logger.error(f"連接 Neo4j 失敗: {e}")
            return False
    
    def close(self):
        """關閉連接"""
        if self.session:
            self.session.close()
        if self.driver:
            self.driver.close()
        logger.info("Neo4j 連接已關閉")
    
    def setup_schema(self):
        """設定資料庫架構"""
        if not self.session:
            raise RuntimeError("未連接到 Neo4j")
        
        logger.info("設定資料庫架構...")
        
        # 創建索引
        create_indexes(self.session)
        
        # 創建約束
        self._create_constraints()
        
        logger.info("資料庫架構設定完成")
    
    def _create_constraints(self):
        """創建約束"""
        # 先刪除現有的索引，避免與約束衝突
        drop_indexes = [
            "DROP INDEX IF EXISTS FOR (n:EC2Instance) ON (n.id)",
            "DROP INDEX IF EXISTS FOR (n:SecurityGroup) ON (n.id)",
            "DROP INDEX IF EXISTS FOR (n:VPC) ON (n.id)",
            "DROP INDEX IF EXISTS FOR (n:Subnet) ON (n.id)",
            "DROP INDEX IF EXISTS FOR (n:EBSVolume) ON (n.id)",
            "DROP INDEX IF EXISTS FOR (n:SecurityRule) ON (n.id)",
            "DROP INDEX IF EXISTS FOR (n:S3Bucket) ON (n.id)",
        ]
        
        for drop_index in drop_indexes:
            try:
                self.session.run(drop_index)
            except Exception as e:
                logger.debug(f"刪除索引: {drop_index}, 錯誤: {e}")
        
        # 創建約束
        constraints = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:EC2Instance) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:SecurityGroup) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:VPC) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Subnet) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:EBSVolume) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:SecurityRule) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:S3Bucket) REQUIRE n.id IS UNIQUE",
        ]
        
        for constraint in constraints:
            try:
                self.session.run(constraint)
            except Exception as e:
                logger.warning(f"創建約束失敗: {constraint}, 錯誤: {e}")
    
    @timeit
    def load_nodes(self, node_type: str, data: List[Dict[str, Any]], 
                   region: str = None, account_id: str = None) -> bool:
        """載入節點資料"""
        if not self.session:
            raise RuntimeError("未連接到 Neo4j")
        
        schema = get_schema(node_type)
        if not schema:
            logger.error(f"未知的節點類型: {node_type}")
            return False
        
        logger.info(f"載入 {len(data)} 個 {node_type} 節點...")
        
        try:
            # 批次處理
            batch_size = 1000
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                self._load_node_batch(schema, batch, region, account_id)
            
            logger.info(f"成功載入 {len(data)} 個 {node_type} 節點")
            return True
            
        except Exception as e:
            logger.error(f"載入 {node_type} 節點失敗: {e}")
            return False
    
    def _load_node_batch(self, schema: CartographyNodeSchema, batch: List[Dict], 
                        region: str = None, account_id: str = None):
        """載入節點批次"""
        # 構建 Cypher 查詢
        query = self._build_node_query(schema)
        
        # 準備參數
        params = {
            'batch': batch,
            'region': region,
            'account_id': account_id,
            'lastupdated': self.update_tag
        }
        
        # 執行查詢
        self.session.run(query, params)
    
    def _build_node_query(self, schema: CartographyNodeSchema) -> str:
        """構建節點查詢"""
        # 獲取屬性列表
        properties = schema.properties.__dict__
        
        # 構建 MERGE 查詢 - 使用動態屬性載入
        query = f"""
        UNWIND $batch as item
        MERGE (n:{schema.label} {{id: item.id}})
        SET n += item
        SET n.lastupdated = $lastupdated
        """
        
        # 添加區域和帳戶 ID
        if hasattr(schema.properties, 'region'):
            query += "SET n.region = $region\n"
        if hasattr(schema.properties, 'account_id'):
            query += "SET n.account_id = $account_id\n"
        
        return query
    
    @timeit
    def load_relationships(self, rel_type: str, data: List[Dict[str, Any]]) -> bool:
        """載入關係資料"""
        if not self.session:
            raise RuntimeError("未連接到 Neo4j")
        
        logger.info(f"載入 {len(data)} 個 {rel_type} 關係...")
        
        try:
            # 批次處理
            batch_size = 1000
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                self._load_relationship_batch(rel_type, batch)
            
            logger.info(f"成功載入 {len(data)} 個 {rel_type} 關係")
            return True
            
        except Exception as e:
            logger.error(f"載入 {rel_type} 關係失敗: {e}")
            return False
    
    def _load_relationship_batch(self, rel_type: str, batch: List[Dict]):
        """載入關係批次"""
        # 根據關係類型構建查詢
        if rel_type == "IS_MEMBER_OF":
            query = """
            UNWIND $batch as item
            MATCH (instance:EC2Instance {id: item.instance_id})
            MATCH (sg:SecurityGroup {id: item.group_id})
            MERGE (instance)-[r:IS_MEMBER_OF]->(sg)
            SET r.lastupdated = $lastupdated
            """
        elif rel_type == "LOCATED_IN":
            query = """
            UNWIND $batch as item
            MATCH (instance:EC2Instance {id: item.instance_id})
            MATCH (subnet:Subnet {id: item.subnet_id})
            MERGE (instance)-[r:LOCATED_IN]->(subnet)
            SET r.lastupdated = $lastupdated
            """
        elif rel_type == "ATTACHES_TO":
            query = """
            UNWIND $batch as item
            MATCH (volume:EBSVolume {id: item.volume_id})
            MATCH (instance:EC2Instance {id: item.instance_id})
            MERGE (volume)-[r:ATTACHES_TO]->(instance)
            SET r.lastupdated = $lastupdated
            """
        elif rel_type == "HAS_RULE":
            query = """
            UNWIND $batch as item
            MATCH (sg:SecurityGroup {id: item.group_id})
            MATCH (rule:SecurityRule {id: item.rule_id})
            MERGE (sg)-[r:HAS_RULE]->(rule)
            SET r.lastupdated = $lastupdated
            """
        else:
            logger.warning(f"未知的關係類型: {rel_type}")
            return
        
        # 執行查詢
        params = {
            'batch': batch,
            'lastupdated': self.update_tag
        }
        self.session.run(query, params)
    
    @timeit
    def cleanup_old_data(self, node_types: List[str] = None):
        """清理舊資料"""
        if not self.session:
            raise RuntimeError("未連接到 Neo4j")
        
        if node_types is None:
            node_types = list(get_all_schemas().keys())
        
        logger.info(f"清理舊資料: {node_types}")
        
        for node_type in node_types:
            try:
                query = f"""
                MATCH (n:{node_type})
                WHERE n.lastupdated < $update_tag
                DETACH DELETE n
                """
                self.session.run(query, {'update_tag': self.update_tag})
                logger.info(f"清理 {node_type} 舊資料完成")
            except Exception as e:
                logger.error(f"清理 {node_type} 舊資料失敗: {e}")
    
    @timeit
    def load_aws_data(self, data: Dict[str, Any], region: str = None, 
                     account_id: str = None) -> bool:
        """載入 AWS 資料"""
        if not self.session:
            raise RuntimeError("未連接到 Neo4j")
        
        logger.info("開始載入 AWS 資料...")
        
        try:
            # 載入節點
            self._load_aws_nodes(data, region, account_id)
            
            # 載入關係
            self._load_aws_relationships(data)
            
            logger.info("AWS 資料載入完成")
            return True
            
        except Exception as e:
            logger.error(f"載入 AWS 資料失敗: {e}")
            return False
    
    def _load_aws_nodes(self, data: Dict[str, Any], region: str, account_id: str):
        """載入 AWS 節點"""
        # 載入 EC2 實例
        if 'ec2_instances' in data:
            instances = self._extract_ec2_instances(data['ec2_instances'])
            if instances:
                self.load_nodes("EC2Instance", instances, region, account_id)
        
        # 載入安全群組
        if 'security_groups' in data:
            security_groups = self._extract_security_groups(data['security_groups'])
            if security_groups:
                self.load_nodes("SecurityGroup", security_groups, region, account_id)
        
        # 載入 VPC
        if 'vpcs' in data:
            vpcs = self._extract_vpcs(data['vpcs'])
            if vpcs:
                self.load_nodes("VPC", vpcs, region, account_id)
        
        # 載入子網路
        if 'subnets' in data:
            subnets = self._extract_subnets(data['subnets'])
            if subnets:
                self.load_nodes("Subnet", subnets, region, account_id)
        
        # 載入 EBS 磁碟
        if 'ebs_volumes' in data:
            volumes = self._extract_ebs_volumes(data['ebs_volumes'])
            if volumes:
                self.load_nodes("EBSVolume", volumes, region, account_id)
        
        # 載入 S3 儲存桶
        if 's3_buckets' in data:
            buckets = self._extract_s3_buckets(data['s3_buckets'])
            if buckets:
                self.load_nodes("S3Bucket", buckets, region, account_id)
    
    def _extract_ec2_instances(self, ec2_data: Dict) -> List[Dict]:
        """提取 EC2 實例資料"""
        instances = []
        
        if isinstance(ec2_data, dict) and 'Reservations' in ec2_data:
            for reservation in ec2_data['Reservations']:
                for instance in reservation['Instances']:
                    instances.append({
                        'id': instance.get('InstanceId'),  # 添加 id 欄位
                        'InstanceId': instance.get('InstanceId'),
                        'Name': instance.get('Name'),
                        'State': instance.get('State', {}).get('Name', 'unknown'),
                        'InstanceType': instance.get('InstanceType'),
                        'PublicIpAddress': instance.get('PublicIpAddress'),
                        'PrivateIpAddress': instance.get('PrivateIpAddress'),
                        'ImageId': instance.get('ImageId'),
                        'LaunchTime': instance.get('LaunchTime'),
                        'AvailabilityZone': instance.get('Placement', {}).get('AvailabilityZone'),
                        'Region': instance.get('Region', 'unknown')
                    })
        
        return instances
    
    def _extract_security_groups(self, sg_data: Dict) -> List[Dict]:
        """提取安全群組資料"""
        security_groups = []
        
        if isinstance(sg_data, dict) and 'SecurityGroups' in sg_data:
            for sg in sg_data['SecurityGroups']:
                security_groups.append({
                    'id': sg.get('GroupId'),  # 添加 id 欄位
                    'GroupId': sg.get('GroupId'),
                    'GroupName': sg.get('GroupName'),
                    'Description': sg.get('Description'),
                    'VpcId': sg.get('VpcId'),
                    'Region': sg.get('Region', 'unknown')
                })
        
        return security_groups
    
    def _extract_vpcs(self, vpc_data: Dict) -> List[Dict]:
        """提取 VPC 資料"""
        vpcs = []
        
        if isinstance(vpc_data, dict) and 'Vpcs' in vpc_data:
            for vpc in vpc_data['Vpcs']:
                vpcs.append({
                    'id': vpc.get('VpcId'),  # 添加 id 欄位
                    'VpcId': vpc.get('VpcId'),
                    'Name': vpc.get('Name'),
                    'CidrBlock': vpc.get('CidrBlock'),
                    'State': vpc.get('State'),
                    'IsDefault': vpc.get('IsDefault', False),
                    'Region': vpc.get('Region', 'unknown')
                })
        
        return vpcs
    
    def _extract_subnets(self, subnet_data: Dict) -> List[Dict]:
        """提取子網路資料"""
        subnets = []
        
        if isinstance(subnet_data, dict) and 'Subnets' in subnet_data:
            for subnet in subnet_data['Subnets']:
                subnets.append({
                    'id': subnet.get('SubnetId'),  # 添加 id 欄位
                    'SubnetId': subnet.get('SubnetId'),
                    'Name': subnet.get('Name'),
                    'CidrBlock': subnet.get('CidrBlock'),
                    'AvailabilityZone': subnet.get('AvailabilityZone'),
                    'VpcId': subnet.get('VpcId'),
                    'Region': subnet.get('Region', 'unknown')
                })
        
        return subnets
    
    def _extract_ebs_volumes(self, volume_data: Dict) -> List[Dict]:
        """提取 EBS 磁碟資料"""
        volumes = []
        
        if isinstance(volume_data, dict) and 'Volumes' in volume_data:
            for volume in volume_data['Volumes']:
                volumes.append({
                    'id': volume.get('VolumeId'),  # 添加 id 欄位
                    'VolumeId': volume.get('VolumeId'),
                    'Size': volume.get('Size'),
                    'VolumeType': volume.get('VolumeType'),
                    'State': volume.get('State'),
                    'Encrypted': volume.get('Encrypted', False),
                    'Iops': volume.get('Iops'),
                    'CreationDate': volume.get('CreationDate'),
                    'KmsKeyId': volume.get('KmsKeyId'),
                    'Region': volume.get('Region', 'unknown')
                })
        
        return volumes
    
    def _extract_s3_buckets(self, bucket_data: Dict) -> List[Dict]:
        """提取 S3 儲存桶資料"""
        buckets = []
        
        if isinstance(bucket_data, dict) and 'Buckets' in bucket_data:
            for bucket in bucket_data['Buckets']:
                buckets.append({
                    'id': bucket.get('BucketName'),  # 使用 BucketName 作為 id
                    'Name': bucket.get('BucketName'),
                    'CreationDate': bucket.get('CreationDate'),
                    'Arn': bucket.get('Arn'),
                    'Region': bucket.get('Region', 'us-east-1')
                })
        
        return buckets
    
    def _load_aws_relationships(self, data: Dict[str, Any]):
        """載入 AWS 關係"""
        # 載入 EC2 實例到安全群組的關係
        if 'ec2_instances' in data and 'security_groups' in data:
            self._load_ec2_security_group_relationships(data)
        
        # 載入 EC2 實例到子網路的關係
        if 'ec2_instances' in data and 'subnets' in data:
            self._load_ec2_subnet_relationships(data)
        
        # 載入 EBS 磁碟到 EC2 實例的關係
        if 'ebs_volumes' in data and 'ec2_instances' in data:
            self._load_ebs_ec2_relationships(data)
        
        # 載入安全規則節點和關係
        if 'security_rules' in data:
            self._load_security_rules_and_relationships(data)
    
    def _load_ec2_security_group_relationships(self, data: Dict):
        """載入 EC2 實例到安全群組的關係"""
        relationships = []
        
        if isinstance(data['ec2_instances'], dict) and 'Reservations' in data['ec2_instances']:
            for reservation in data['ec2_instances']['Reservations']:
                for instance in reservation['Instances']:
                    instance_id = instance.get('InstanceID')
                    if instance.get('SecurityGroups'):
                        for sg in instance['SecurityGroups']:
                            relationships.append({
                                'instance_id': instance_id,
                                'group_id': sg.get('GroupId')
                            })
        
        if relationships:
            self.load_relationships("IS_MEMBER_OF", relationships)
    
    def _load_ec2_subnet_relationships(self, data: Dict):
        """載入 EC2 實例到子網路的關係"""
        relationships = []
        
        if isinstance(data['ec2_instances'], dict) and 'Reservations' in data['ec2_instances']:
            for reservation in data['ec2_instances']['Reservations']:
                for instance in reservation['Instances']:
                    instance_id = instance.get('InstanceID')
                    subnet_id = instance.get('SubnetId')
                    if instance_id and subnet_id:
                        relationships.append({
                            'instance_id': instance_id,
                            'subnet_id': subnet_id
                        })
        
        if relationships:
            self.load_relationships("LOCATED_IN", relationships)
    
    def _load_ebs_ec2_relationships(self, data: Dict):
        """載入 EBS 磁碟到 EC2 實例的關係"""
        relationships = []
        
        if isinstance(data['ebs_volumes'], dict) and 'Volumes' in data['ebs_volumes']:
            for volume in data['ebs_volumes']['Volumes']:
                volume_id = volume.get('VolumeId')
                if volume.get('Attachments'):
                    for attachment in volume['Attachments']:
                        instance_id = attachment.get('InstanceId')
                        if volume_id and instance_id:
                            relationships.append({
                                'volume_id': volume_id,
                                'instance_id': instance_id
                            })
        
        if relationships:
            self.load_relationships("ATTACHES_TO", relationships)
    
    def _load_security_rules_and_relationships(self, data: Dict):
        """載入安全規則節點和關係"""
        # 載入安全規則節點
        if 'security_rules' in data and 'Rules' in data['security_rules']:
            rules = []
            for rule in data['security_rules']['Rules']:
                rules.append({
                    'id': rule.get('RuleId'),
                    'RuleId': rule.get('RuleId'),
                    'GroupId': rule.get('GroupId'),
                    'Protocol': rule.get('Protocol'),
                    'PortRange': rule.get('PortRange'),
                    'SourceCIDR': rule.get('SourceCIDR'),
                    'Direction': rule.get('Direction'),
                    'Action': rule.get('Action'),
                    'Description': rule.get('Description')
                })
            
            if rules:
                self.load_nodes("SecurityRule", rules)
        
        # 載入安全群組到安全規則的關係
        if 'security_rules' in data and 'Rules' in data['security_rules']:
            relationships = []
            for rule in data['security_rules']['Rules']:
                relationships.append({
                    'group_id': rule.get('GroupId'),
                    'rule_id': rule.get('RuleId')
                })
            
            if relationships:
                self.load_relationships("HAS_RULE", relationships)
    
    def get_statistics(self) -> Dict[str, int]:
        """獲取資料庫統計資訊"""
        if not self.session:
            raise RuntimeError("未連接到 Neo4j")
        
        stats = {}
        
        # 獲取節點數量
        node_types = list(get_all_schemas().keys())
        for node_type in node_types:
            result = self.session.run(f"MATCH (n:{node_type}) RETURN count(n) as count")
            stats[node_type] = result.single()['count']
        
        # 獲取關係數量
        relationship_types = ["IS_MEMBER_OF", "LOCATED_IN", "ATTACHES_TO", "HAS_RULE"]
        for rel_type in relationship_types:
            result = self.session.run(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count")
            stats[rel_type] = result.single()['count']
        
        return stats
    
    # ===== 進階功能（基於 Cartography 架構） =====
    
    def load_with_schema_advanced(self, schema: CartographyNodeSchema, data: List[Dict[str, Any]], **kwargs) -> None:
        """使用 Schema 進階載入資料（批次處理 + 重試機制）"""
        if not data:
            logger.info(f"沒有 {schema.label} 資料需要載入")
            return
        
        if not self.config.use_advanced_loading:
            # 使用原始載入方法
            return self._load_nodes_basic(schema.label, data)
        
        # 確保索引存在
        self._ensure_indexes_advanced(schema)
        
        # 批次載入
        self._load_data_in_batches_advanced(schema, data, **kwargs)
        
        logger.info(f"成功載入 {len(data)} 個 {schema.label} 節點")
    
    def _ensure_indexes_advanced(self, schema: CartographyNodeSchema) -> None:
        """確保索引存在（進階版本）"""
        if not self.config.create_indexes:
            return
        
        # 建立基本索引
        index_queries = [
            f"CREATE INDEX IF NOT EXISTS FOR (n:{schema.label}) ON (n.id)",
            f"CREATE INDEX IF NOT EXISTS FOR (n:{schema.label}) ON (n.lastupdated)"
        ]
        
        # 建立額外索引
        for attr_name, prop_ref in schema.properties.__dict__.items():
            if hasattr(prop_ref, 'extra_index') and prop_ref.extra_index:
                index_queries.append(f"CREATE INDEX IF NOT EXISTS FOR (n:{schema.label}) ON (n.{attr_name})")
        
        for query in index_queries:
            try:
                self._run_index_query_with_retry(query)
            except Exception as e:
                logger.warning(f"建立索引失敗: {e}")
    
    def _run_index_query_with_retry(self, query: str) -> None:
        """執行索引查詢並重試"""
        if BACKOFF_AVAILABLE:
            @backoff.on_exception(
                backoff.expo,
                (ServiceUnavailable, SessionExpired, TransientError),
                max_tries=3
            )
            def _run_query():
                self.session.run(query)
            _run_query()
        else:
            self.session.run(query)
    
    def _load_data_in_batches_advanced(self, schema: CartographyNodeSchema, data: List[Dict[str, Any]], **kwargs) -> None:
        """批次載入資料（進階版本）"""
        batch_size = self.config.batch_size
        
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            
            def _load_batch_tx(tx: neo4j.Transaction) -> None:
                # 建構批次載入查詢
                query = self._build_batch_query(schema, batch)
                tx.run(query, **kwargs)
            
            if BACKOFF_AVAILABLE:
                @backoff.on_exception(
                    backoff.expo,
                    (ServiceUnavailable, SessionExpired, TransientError),
                    max_tries=self.config.max_retries,
                    on_backoff=lambda details: logger.warning(f"重試載入，第 {details['tries']} 次嘗試")
                )
                def _load_with_retry():
                    self.session.write_transaction(_load_batch_tx)
                _load_with_retry()
            else:
                self.session.write_transaction(_load_batch_tx)
            
            logger.debug(f"載入批次 {i//batch_size + 1}/{(len(data)-1)//batch_size + 1}")
    
    def _build_batch_query(self, schema: CartographyNodeSchema, batch: List[Dict[str, Any]]) -> str:
        """建構批次載入查詢"""
        node_label = schema.label
        id_property = schema.properties.id.source
        
        # 建構 UNWIND 查詢
        query = f"""
        UNWIND $DictList AS item
        MERGE (n:{node_label} {{id: item.{id_property}}})
        SET n += item
        """
        
        # 添加額外屬性設定
        set_clauses = []
        for attr_name, prop_ref in schema.properties.__dict__.items():
            if attr_name in ['id', 'lastupdated']:
                continue
            if hasattr(prop_ref, 'set_in_kwargs') and prop_ref.set_in_kwargs:
                set_clauses.append(f"n.{attr_name} = ${prop_ref.source}")
            else:
                set_clauses.append(f"n.{attr_name} = item.{prop_ref.source}")
        
        if set_clauses:
            query += ",\n        ".join(set_clauses)
        
        return query
    
    def cleanup_old_data_advanced(self, node_labels: List[str], limit_size: int = 1000) -> None:
        """清理舊資料（進階版本）"""
        update_tag = int(time.time())
        
        for label in node_labels:
            query = f"""
            MATCH (n:{label}) 
            WHERE n.lastupdated <> $UPDATE_TAG 
            WITH n LIMIT $LIMIT_SIZE 
            DETACH DELETE (n)
            """
            
            def _cleanup_tx(tx: neo4j.Transaction) -> None:
                result = tx.run(query, UPDATE_TAG=update_tag, LIMIT_SIZE=limit_size)
                return result.consume()
            
            try:
                if BACKOFF_AVAILABLE:
                    @backoff.on_exception(
                        backoff.expo,
                        (ServiceUnavailable, SessionExpired, TransientError),
                        max_tries=3
                    )
                    def _cleanup_with_retry():
                        self.session.write_transaction(_cleanup_tx)
                    _cleanup_with_retry()
                else:
                    self.session.write_transaction(_cleanup_tx)
                
                logger.info(f"清理 {label} 舊資料完成")
            except Exception as e:
                logger.error(f"清理 {label} 失敗: {e}")
    
    def run_analysis_advanced(self, analysis_type: str) -> List[Dict[str, Any]]:
        """執行進階分析查詢"""
        analysis_queries = {
            'security': """
                MATCH (instance:EC2Instance)-[:MEMBER_OF]->(sg:SecurityGroup),
                      (sg)-[:HAS_RULE]->(rule:Rule)
                WHERE rule.SourceCIDR = '0.0.0.0/0' 
                  AND rule.PortRange CONTAINS '22'
                  AND rule.Protocol = 'tcp'
                SET instance.exposed_ssh = true
                RETURN instance.Name, instance.PublicIP, sg.GroupName
            """,
            'exposed_ssh': """
                MATCH (instance:EC2Instance)-[:MEMBER_OF]->(sg:SecurityGroup),
                      (sg)-[:HAS_RULE]->(rule:Rule)
                WHERE rule.SourceCIDR = '0.0.0.0/0' 
                  AND rule.PortRange CONTAINS '22'
                  AND rule.Protocol = 'tcp'
                SET instance.exposed_ssh = true
                RETURN instance.Name, instance.PublicIP, sg.GroupName
            """,
            'overly_permissive': """
                MATCH (sg:SecurityGroup)-[:HAS_RULE]->(rule:Rule)
                WHERE rule.SourceCIDR = '0.0.0.0/0'
                  AND rule.PortRange = '0-65535'
                  AND rule.Protocol = 'tcp'
                SET sg.overly_permissive = true
                RETURN sg.GroupName, rule.RuleID, rule.Description
            """,
            'unused_security_groups': """
                MATCH (sg:SecurityGroup)
                WHERE NOT (sg)<-[:MEMBER_OF]-(:EC2Instance)
                  AND NOT (sg)<-[:SOURCE_SECURITY_GROUP]-(:SecurityGroup)
                SET sg.unused = true
                RETURN sg.GroupName, sg.Description
            """,
            'orphaned_volumes': """
                MATCH (volume:EBSVolume)
                WHERE NOT (volume)-[:ATTACHES_TO]->(:EC2Instance)
                  AND volume.State = 'available'
                SET volume.orphaned = true
                RETURN volume.VolumeId, volume.Size, volume.VolumeType
                ORDER BY volume.Size DESC
            """,
            'cost': """
                MATCH (instance:EC2Instance)
                WHERE instance.State = 'stopped'
                  AND instance.LaunchTime < datetime() - duration('P30D')
                SET instance.cost_optimization_candidate = true
                RETURN instance.Name, instance.InstanceType, instance.LaunchTime
                ORDER BY instance.LaunchTime ASC
            """,
            'cost_optimization': """
                MATCH (instance:EC2Instance)
                WHERE instance.State = 'stopped'
                  AND instance.LaunchTime < datetime() - duration('P30D')
                SET instance.cost_optimization_candidate = true
                RETURN instance.Name, instance.InstanceType, instance.LaunchTime
                ORDER BY instance.LaunchTime ASC
            """
        }
        
        query = analysis_queries.get(analysis_type)
        if not query:
            logger.error(f"未知的分析類型: {analysis_type}")
            return []
        
        def _run_analysis_tx(tx: neo4j.Transaction) -> List[Dict[str, Any]]:
            result = tx.run(query)
            return [record.data() for record in result]
        
        try:
            # 使用 execute_write 因為查詢中包含 SET 操作
            findings = self.session.execute_write(_run_analysis_tx)
            logger.info(f"分析 {analysis_type} 完成，發現 {len(findings)} 個問題")
            return findings
        except Exception as e:
            logger.error(f"分析 {analysis_type} 失敗: {e}")
            return []
