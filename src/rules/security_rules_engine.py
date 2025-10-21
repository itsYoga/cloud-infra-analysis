"""
基於 Cartography 架構的進階安全分析規則引擎

這個模組實作了模組化、可擴展的安全規則系統，
參考了 Cartography 的規則引擎最佳實踐。
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import neo4j

logger = logging.getLogger(__name__)


class Severity(Enum):
    """嚴重程度枚舉"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


@dataclass
class SecurityFinding:
    """安全發現"""
    rule_id: str
    rule_name: str
    severity: Severity
    description: str
    affected_resources: List[Dict[str, Any]]
    recommendation: str
    cypher_query: str
    metadata: Dict[str, Any] = None


class SecurityRule(ABC):
    """安全規則基類"""
    
    def __init__(self, rule_id: str, rule_name: str, description: str, 
                 severity: Severity, recommendation: str):
        self.rule_id = rule_id
        self.rule_name = rule_name
        self.description = description
        self.severity = severity
        self.recommendation = recommendation
    
    @abstractmethod
    def evaluate(self, neo4j_session: neo4j.Session) -> List[SecurityFinding]:
        """評估規則並返回發現"""
        pass
    
    @abstractmethod
    def get_cypher_query(self) -> str:
        """獲取 Cypher 查詢"""
        pass


class ExposedSSHRule(SecurityRule):
    """暴露 SSH 服務規則"""
    
    def __init__(self):
        super().__init__(
            rule_id="EXPOSED_SSH",
            rule_name="暴露的 SSH 服務",
            description="檢測暴露於公網的 SSH 服務（端口 22）",
            severity=Severity.HIGH,
            recommendation="限制 SSH 訪問來源 IP 或使用 VPN"
        )
    
    def get_cypher_query(self) -> str:
        return """
        MATCH (instance:EC2Instance)-[:IS_MEMBER_OF]->(sg:SecurityGroup),
              (sg)-[:HAS_RULE]->(rule:SecurityRule)
        WHERE rule.SourceCIDR = '0.0.0.0/0' 
          AND rule.PortRange CONTAINS '22'
          AND rule.Protocol = 'tcp'
          AND rule.Direction = 'inbound'
        RETURN instance, sg, rule
        """
    
    def evaluate(self, neo4j_session: neo4j.Session) -> List[SecurityFinding]:
        query = self.get_cypher_query()
        result = neo4j_session.run(query)
        
        findings = []
        affected_resources = []
        
        for record in result:
            instance = dict(record['instance'])
            sg = dict(record['sg'])
            rule = dict(record['rule'])
            
            affected_resources.append({
                'type': 'EC2Instance',
                'id': instance.get('id'),
                'name': instance.get('name'),
                'public_ip': instance.get('publicip'),
                'security_group': sg.get('name'),
                'rule': rule
            })
        
        if affected_resources:
            findings.append(SecurityFinding(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                severity=self.severity,
                description=self.description,
                affected_resources=affected_resources,
                recommendation=self.recommendation,
                cypher_query=self.get_cypher_query(),
                metadata={'count': len(affected_resources)}
            ))
        
        return findings


class ExposedRDPSRule(SecurityRule):
    """暴露 RDP 服務規則"""
    
    def __init__(self):
        super().__init__(
            rule_id="EXPOSED_RDP",
            rule_name="暴露的 RDP 服務",
            description="檢測暴露於公網的 RDP 服務（端口 3389）",
            severity=Severity.HIGH,
            recommendation="限制 RDP 訪問來源 IP 或使用 VPN"
        )
    
    def get_cypher_query(self) -> str:
        return """
        MATCH (instance:EC2Instance)-[:IS_MEMBER_OF]->(sg:SecurityGroup),
              (sg)-[:HAS_RULE]->(rule:SecurityRule)
        WHERE rule.SourceCIDR = '0.0.0.0/0' 
          AND rule.PortRange CONTAINS '3389'
          AND rule.Protocol = 'tcp'
          AND rule.Direction = 'inbound'
        RETURN instance, sg, rule
        """
    
    def evaluate(self, neo4j_session: neo4j.Session) -> List[SecurityFinding]:
        query = self.get_cypher_query()
        result = neo4j_session.run(query)
        
        findings = []
        affected_resources = []
        
        for record in result:
            instance = dict(record['instance'])
            sg = dict(record['sg'])
            rule = dict(record['rule'])
            
            affected_resources.append({
                'type': 'EC2Instance',
                'id': instance.get('id'),
                'name': instance.get('name'),
                'public_ip': instance.get('publicip'),
                'security_group': sg.get('name'),
                'rule': rule
            })
        
        if affected_resources:
            findings.append(SecurityFinding(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                severity=self.severity,
                description=self.description,
                affected_resources=affected_resources,
                recommendation=self.recommendation,
                cypher_query=self.get_cypher_query(),
                metadata={'count': len(affected_resources)}
            ))
        
        return findings


class OverlyPermissiveRule(SecurityRule):
    """過度寬鬆規則"""
    
    def __init__(self):
        super().__init__(
            rule_id="OVERLY_PERMISSIVE",
            rule_name="過度寬鬆的安全群組規則",
            description="檢測允許所有流量的安全群組規則",
            severity=Severity.CRITICAL,
            recommendation="限制規則的來源 IP 範圍和端口範圍"
        )
    
    def get_cypher_query(self) -> str:
        return """
        MATCH (sg:SecurityGroup)-[:HAS_RULE]->(rule:SecurityRule)
        WHERE rule.SourceCIDR = '0.0.0.0/0'
          AND rule.PortRange = '0-65535'
          AND rule.Protocol = 'tcp'
          AND rule.Direction = 'inbound'
        RETURN sg, rule
        """
    
    def evaluate(self, neo4j_session: neo4j.Session) -> List[SecurityFinding]:
        query = self.get_cypher_query()
        result = neo4j_session.run(query)
        
        findings = []
        affected_resources = []
        
        for record in result:
            sg = dict(record['sg'])
            rule = dict(record['rule'])
            
            affected_resources.append({
                'type': 'SecurityGroup',
                'id': sg.get('id'),
                'name': sg.get('name'),
                'vpc_id': sg.get('vpcid'),
                'rule': rule
            })
        
        if affected_resources:
            findings.append(SecurityFinding(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                severity=self.severity,
                description=self.description,
                affected_resources=affected_resources,
                recommendation=self.recommendation,
                cypher_query=self.get_cypher_query(),
                metadata={'count': len(affected_resources)}
            ))
        
        return findings


class UnencryptedEBSRule(SecurityRule):
    """未加密 EBS 磁碟規則"""
    
    def __init__(self):
        super().__init__(
            rule_id="UNENCRYPTED_EBS",
            rule_name="未加密的 EBS 磁碟",
            description="檢測未加密的 EBS 磁碟",
            severity=Severity.MEDIUM,
            recommendation="啟用 EBS 磁碟加密"
        )
    
    def get_cypher_query(self) -> str:
        return """
        MATCH (volume:EBSVolume)
        WHERE volume.Encrypted = false
          AND volume.State = 'in-use'
        RETURN volume
        """
    
    def evaluate(self, neo4j_session: neo4j.Session) -> List[SecurityFinding]:
        query = self.get_cypher_query()
        result = neo4j_session.run(query)
        
        findings = []
        affected_resources = []
        
        for record in result:
            volume = dict(record['volume'])
            
            affected_resources.append({
                'type': 'EBSVolume',
                'id': volume.get('id'),
                'volume_id': volume.get('volumeid'),
                'size': volume.get('size'),
                'volume_type': volume.get('volumetype'),
                'state': volume.get('state')
            })
        
        if affected_resources:
            findings.append(SecurityFinding(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                severity=self.severity,
                description=self.description,
                affected_resources=affected_resources,
                recommendation=self.recommendation,
                cypher_query=self.get_cypher_query(),
                metadata={'count': len(affected_resources)}
            ))
        
        return findings


class OrphanedEBSRule(SecurityRule):
    """孤兒 EBS 磁碟規則"""
    
    def __init__(self):
        super().__init__(
            rule_id="ORPHANED_EBS",
            rule_name="孤兒 EBS 磁碟",
            description="檢測未附加到任何實例的 EBS 磁碟",
            severity=Severity.LOW,
            recommendation="刪除未使用的 EBS 磁碟以節省成本"
        )
    
    def get_cypher_query(self) -> str:
        return """
        MATCH (volume:EBSVolume)
        WHERE NOT (volume)-[:ATTACHES_TO]->(:EC2Instance)
          AND volume.State = 'available'
        RETURN volume
        """
    
    def evaluate(self, neo4j_session: neo4j.Session) -> List[SecurityFinding]:
        query = self.get_cypher_query()
        result = neo4j_session.run(query)
        
        findings = []
        affected_resources = []
        
        for record in result:
            volume = dict(record['volume'])
            
            affected_resources.append({
                'type': 'EBSVolume',
                'id': volume.get('id'),
                'volume_id': volume.get('volumeid'),
                'size': volume.get('size'),
                'volume_type': volume.get('volumetype'),
                'state': volume.get('state')
            })
        
        if affected_resources:
            findings.append(SecurityFinding(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                severity=self.severity,
                description=self.description,
                affected_resources=affected_resources,
                recommendation=self.recommendation,
                cypher_query=self.get_cypher_query(),
                metadata={'count': len(affected_resources)}
            ))
        
        return findings


class UnusedSecurityGroupRule(SecurityRule):
    """未使用安全群組規則"""
    
    def __init__(self):
        super().__init__(
            rule_id="UNUSED_SECURITY_GROUP",
            rule_name="未使用的安全群組",
            description="檢測未附加到任何資源的安全群組",
            severity=Severity.LOW,
            recommendation="刪除未使用的安全群組"
        )
    
    def get_cypher_query(self) -> str:
        return """
        MATCH (sg:SecurityGroup)
        WHERE NOT (sg)<-[:IS_MEMBER_OF]-(:EC2Instance)
        RETURN sg
        """
    
    def evaluate(self, neo4j_session: neo4j.Session) -> List[SecurityFinding]:
        query = self.get_cypher_query()
        result = neo4j_session.run(query)
        
        findings = []
        affected_resources = []
        
        for record in result:
            sg = dict(record['sg'])
            
            affected_resources.append({
                'type': 'SecurityGroup',
                'id': sg.get('id'),
                'name': sg.get('name'),
                'description': sg.get('description'),
                'vpc_id': sg.get('vpcid')
            })
        
        if affected_resources:
            findings.append(SecurityFinding(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                severity=self.severity,
                description=self.description,
                affected_resources=affected_resources,
                recommendation=self.recommendation,
                cypher_query=self.get_cypher_query(),
                metadata={'count': len(affected_resources)}
            ))
        
        return findings


class NetworkSegmentationRule(SecurityRule):
    """網路分段規則"""
    
    def __init__(self):
        super().__init__(
            rule_id="NETWORK_SEGMENTATION",
            rule_name="網路分段分析",
            description="分析網路分段情況和跨 VPC 連接",
            severity=Severity.MEDIUM,
            recommendation="實施適當的網路分段策略"
        )
    
    def get_cypher_query(self) -> str:
        return """
        MATCH (vpc:VPC)-[:CONTAINS]->(subnet:Subnet)
        OPTIONAL MATCH (subnet)-[:CONTAINS]->(instance:EC2Instance)
        RETURN vpc, subnet, count(instance) as instance_count
        ORDER BY vpc.id, subnet.id
        """
    
    def evaluate(self, neo4j_session: neo4j.Session) -> List[SecurityFinding]:
        query = self.get_cypher_query()
        result = neo4j_session.run(query)
        
        findings = []
        affected_resources = []
        
        for record in result:
            vpc = dict(record['vpc'])
            subnet = dict(record['subnet'])
            instance_count = record['instance_count']
            
            affected_resources.append({
                'type': 'NetworkSegment',
                'vpc_id': vpc.get('id'),
                'vpc_name': vpc.get('name'),
                'subnet_id': subnet.get('id'),
                'subnet_cidr': subnet.get('cidrblock'),
                'availability_zone': subnet.get('availabilityzone'),
                'instance_count': instance_count
            })
        
        if affected_resources:
            findings.append(SecurityFinding(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                severity=self.severity,
                description=self.description,
                affected_resources=affected_resources,
                recommendation=self.recommendation,
                cypher_query=self.get_cypher_query(),
                metadata={'count': len(affected_resources)}
            ))
        
        return findings


class SecurityRulesEngine:
    """安全規則引擎"""
    
    def __init__(self, neo4j_session: neo4j.Session):
        self.session = neo4j_session
        self.rules = self._load_default_rules()
    
    def _load_default_rules(self) -> List[SecurityRule]:
        """載入預設規則"""
        return [
            ExposedSSHRule(),
            ExposedRDPSRule(),
            OverlyPermissiveRule(),
            UnencryptedEBSRule(),
            OrphanedEBSRule(),
            UnusedSecurityGroupRule(),
            NetworkSegmentationRule()
        ]
    
    def add_rule(self, rule: SecurityRule):
        """添加自定義規則"""
        self.rules.append(rule)
        logger.info(f"添加安全規則: {rule.rule_name}")
    
    def remove_rule(self, rule_id: str):
        """移除規則"""
        self.rules = [rule for rule in self.rules if rule.rule_id != rule_id]
        logger.info(f"移除安全規則: {rule_id}")
    
    def get_rule(self, rule_id: str) -> Optional[SecurityRule]:
        """獲取規則"""
        for rule in self.rules:
            if rule.rule_id == rule_id:
                return rule
        return None
    
    def list_rules(self) -> List[Dict[str, Any]]:
        """列出所有規則"""
        return [
            {
                'rule_id': rule.rule_id,
                'rule_name': rule.rule_name,
                'description': rule.description,
                'severity': rule.severity.value,
                'recommendation': rule.recommendation
            }
            for rule in self.rules
        ]
    
    def run_analysis(self, rule_ids: List[str] = None) -> List[SecurityFinding]:
        """執行安全分析"""
        if rule_ids is None:
            rules_to_run = self.rules
        else:
            rules_to_run = [rule for rule in self.rules if rule.rule_id in rule_ids]
        
        logger.info(f"執行 {len(rules_to_run)} 個安全規則...")
        
        all_findings = []
        for rule in rules_to_run:
            try:
                logger.info(f"執行規則: {rule.rule_name}")
                findings = rule.evaluate(self.session)
                all_findings.extend(findings)
                logger.info(f"規則 {rule.rule_name} 完成，發現 {len(findings)} 個問題")
            except Exception as e:
                logger.error(f"執行規則 {rule.rule_name} 失敗: {e}")
        
        logger.info(f"安全分析完成，總共發現 {len(all_findings)} 個問題")
        return all_findings
    
    def get_findings_by_severity(self, findings: List[SecurityFinding]) -> Dict[str, List[SecurityFinding]]:
        """按嚴重程度分組發現"""
        grouped = {}
        for finding in findings:
            severity = finding.severity.value
            if severity not in grouped:
                grouped[severity] = []
            grouped[severity].append(finding)
        return grouped
    
    def get_summary(self, findings: List[SecurityFinding]) -> Dict[str, Any]:
        """獲取分析摘要"""
        summary = {
            'total_findings': len(findings),
            'by_severity': {},
            'by_rule': {},
            'affected_resources': 0
        }
        
        # 按嚴重程度統計
        for finding in findings:
            severity = finding.severity.value
            if severity not in summary['by_severity']:
                summary['by_severity'][severity] = 0
            summary['by_severity'][severity] += 1
        
        # 按規則統計
        for finding in findings:
            rule_id = finding.rule_id
            if rule_id not in summary['by_rule']:
                summary['by_rule'][rule_id] = 0
            summary['by_rule'][rule_id] += 1
        
        # 統計受影響資源
        for finding in findings:
            summary['affected_resources'] += len(finding.affected_resources)
        
        return summary
    
    def export_findings(self, findings: List[SecurityFinding], format: str = 'json') -> str:
        """導出發現結果"""
        if format == 'json':
            import json
            return json.dumps([
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
            ], indent=2, ensure_ascii=False)
        else:
            raise ValueError(f"不支援的導出格式: {format}")


# 自定義規則範例
class CustomSecurityRule(SecurityRule):
    """自定義安全規則範例"""
    
    def __init__(self):
        super().__init__(
            rule_id="CUSTOM_RULE",
            rule_name="自定義安全規則",
            description="這是一個自定義安全規則的範例",
            severity=Severity.MEDIUM,
            recommendation="根據您的需求調整此規則"
        )
    
    def get_cypher_query(self) -> str:
        return """
        MATCH (instance:EC2Instance)
        WHERE instance.State = 'running'
          AND instance.PublicIpAddress IS NOT NULL
        RETURN instance
        """
    
    def evaluate(self, neo4j_session: neo4j.Session) -> List[SecurityFinding]:
        query = self.get_cypher_query()
        result = neo4j_session.run(query)
        
        findings = []
        affected_resources = []
        
        for record in result:
            instance = dict(record['instance'])
            
            affected_resources.append({
                'type': 'EC2Instance',
                'id': instance.get('id'),
                'name': instance.get('name'),
                'public_ip': instance.get('publicip'),
                'state': instance.get('state')
            })
        
        if affected_resources:
            findings.append(SecurityFinding(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                severity=self.severity,
                description=self.description,
                affected_resources=affected_resources,
                recommendation=self.recommendation,
                cypher_query=self.get_cypher_query(),
                metadata={'count': len(affected_resources)}
            ))
        
        return findings
