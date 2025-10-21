"""
基於 Cartography 架構的改進資料模型

這個模組實作了更結構化、可擴展的資料模型，
參考了 Cartography 的最佳實踐。
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum


class PropertyRef:
    """屬性引用類，用於定義節點屬性"""
    
    def __init__(self, field_name: str, extra_index: bool = False, set_in_kwargs: bool = False):
        self.field_name = field_name
        self.extra_index = extra_index
        self.set_in_kwargs = set_in_kwargs


class LinkDirection(Enum):
    """關係方向枚舉"""
    INWARD = "INWARD"
    OUTWARD = "OUTWARD"
    BIDIRECTIONAL = "BIDIRECTIONAL"


@dataclass(frozen=True)
class CartographyNodeProperties:
    """基礎節點屬性類"""
    pass


@dataclass(frozen=True)
class CartographyRelProperties:
    """基礎關係屬性類"""
    pass


@dataclass(frozen=True)
class CartographyNodeSchema:
    """節點架構基類"""
    label: str
    properties: CartographyNodeProperties
    sub_resource_relationship: Optional['CartographyRelSchema'] = None
    other_relationships: Optional[List['CartographyRelSchema']] = None


@dataclass(frozen=True)
class CartographyRelSchema:
    """關係架構基類"""
    target_node_label: str
    target_node_matcher: Dict[str, PropertyRef]
    direction: LinkDirection
    rel_label: str
    properties: CartographyRelProperties


# ============================================================================
# EC2 實例模型
# ============================================================================

@dataclass(frozen=True)
class EC2InstanceNodeProperties(CartographyNodeProperties):
    """EC2 實例節點屬性"""
    id: PropertyRef = PropertyRef("InstanceId")
    instanceid: PropertyRef = PropertyRef("InstanceId", extra_index=True)
    name: PropertyRef = PropertyRef("Name")
    state: PropertyRef = PropertyRef("State")
    instancetype: PropertyRef = PropertyRef("InstanceType")
    publicip: PropertyRef = PropertyRef("PublicIpAddress")
    privateip: PropertyRef = PropertyRef("PrivateIpAddress")
    imageid: PropertyRef = PropertyRef("ImageId")
    launchtime: PropertyRef = PropertyRef("LaunchTime")
    availabilityzone: PropertyRef = PropertyRef("AvailabilityZone")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    platform: PropertyRef = PropertyRef("Platform")
    architecture: PropertyRef = PropertyRef("Architecture")
    ebsoptimized: PropertyRef = PropertyRef("EbsOptimized")
    tenancy: PropertyRef = PropertyRef("Tenancy")


@dataclass(frozen=True)
class EC2InstanceToAWSAccountRelProperties(CartographyRelProperties):
    """EC2 實例到 AWS 帳戶關係屬性"""
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2InstanceToAWSAccountRel(CartographyRelSchema):
    """EC2 實例到 AWS 帳戶關係"""
    target_node_label: str = "AWSAccount"
    target_node_matcher: Dict[str, PropertyRef] = None
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EC2InstanceToAWSAccountRelProperties = EC2InstanceToAWSAccountRelProperties()
    
    def __post_init__(self):
        if self.target_node_matcher is None:
            object.__setattr__(self, 'target_node_matcher', {
                "id": PropertyRef("AWS_ID", set_in_kwargs=True)
            })


@dataclass(frozen=True)
class EC2InstanceToSecurityGroupRelProperties(CartographyRelProperties):
    """EC2 實例到安全群組關係屬性"""
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2InstanceToSecurityGroupRel(CartographyRelSchema):
    """EC2 實例到安全群組關係"""
    target_node_label: str = "SecurityGroup"
    target_node_matcher: Dict[str, PropertyRef] = None
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "IS_MEMBER_OF"
    properties: EC2InstanceToSecurityGroupRelProperties = EC2InstanceToSecurityGroupRelProperties()
    
    def __post_init__(self):
        if self.target_node_matcher is None:
            object.__setattr__(self, 'target_node_matcher', {
                "groupid": PropertyRef("GroupId")
            })


@dataclass(frozen=True)
class EC2InstanceToSubnetRelProperties(CartographyRelProperties):
    """EC2 實例到子網路關係屬性"""
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2InstanceToSubnetRel(CartographyRelSchema):
    """EC2 實例到子網路關係"""
    target_node_label: str = "Subnet"
    target_node_matcher: Dict[str, PropertyRef] = None
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "LOCATED_IN"
    properties: EC2InstanceToSubnetRelProperties = EC2InstanceToSubnetRelProperties()
    
    def __post_init__(self):
        if self.target_node_matcher is None:
            object.__setattr__(self, 'target_node_matcher', {
                "subnetid": PropertyRef("SubnetId")
            })


@dataclass(frozen=True)
class EC2InstanceSchema(CartographyNodeSchema):
    """EC2 實例架構"""
    label: str = "EC2Instance"
    properties: EC2InstanceNodeProperties = EC2InstanceNodeProperties()
    sub_resource_relationship: EC2InstanceToAWSAccountRel = EC2InstanceToAWSAccountRel()
    other_relationships: List[CartographyRelSchema] = None
    
    def __post_init__(self):
        if self.other_relationships is None:
            object.__setattr__(self, 'other_relationships', [
                EC2InstanceToSecurityGroupRel(),
                EC2InstanceToSubnetRel()
            ])


# ============================================================================
# 安全群組模型
# ============================================================================

@dataclass(frozen=True)
class SecurityGroupNodeProperties(CartographyNodeProperties):
    """安全群組節點屬性"""
    id: PropertyRef = PropertyRef("GroupId")
    groupid: PropertyRef = PropertyRef("GroupId", extra_index=True)
    name: PropertyRef = PropertyRef("GroupName")
    description: PropertyRef = PropertyRef("Description")
    vpcid: PropertyRef = PropertyRef("VpcId")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SecurityGroupToVpcRelProperties(CartographyRelProperties):
    """安全群組到 VPC 關係屬性"""
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SecurityGroupToVpcRel(CartographyRelSchema):
    """安全群組到 VPC 關係"""
    target_node_label: str = "VPC"
    target_node_matcher: Dict[str, PropertyRef] = None
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_OF_VPC"
    properties: SecurityGroupToVpcRelProperties = SecurityGroupToVpcRelProperties()
    
    def __post_init__(self):
        if self.target_node_matcher is None:
            object.__setattr__(self, 'target_node_matcher', {
                "vpcid": PropertyRef("VpcId")
            })


@dataclass(frozen=True)
class SecurityGroupSchema(CartographyNodeSchema):
    """安全群組架構"""
    label: str = "SecurityGroup"
    properties: SecurityGroupNodeProperties = SecurityGroupNodeProperties()
    sub_resource_relationship: EC2InstanceToAWSAccountRel = EC2InstanceToAWSAccountRel()
    other_relationships: List[CartographyRelSchema] = None
    
    def __post_init__(self):
        if self.other_relationships is None:
            object.__setattr__(self, 'other_relationships', [
                SecurityGroupToVpcRel()
            ])


# ============================================================================
# VPC 模型
# ============================================================================

@dataclass(frozen=True)
class VPCNodeProperties(CartographyNodeProperties):
    """VPC 節點屬性"""
    id: PropertyRef = PropertyRef("VpcId")
    vpcid: PropertyRef = PropertyRef("VpcId", extra_index=True)
    name: PropertyRef = PropertyRef("Name")
    cidrblock: PropertyRef = PropertyRef("CidrBlock")
    state: PropertyRef = PropertyRef("State")
    isdefault: PropertyRef = PropertyRef("IsDefault")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class VPCSchema(CartographyNodeSchema):
    """VPC 架構"""
    label: str = "VPC"
    properties: VPCNodeProperties = VPCNodeProperties()
    sub_resource_relationship: EC2InstanceToAWSAccountRel = EC2InstanceToAWSAccountRel()


# ============================================================================
# 子網路模型
# ============================================================================

@dataclass(frozen=True)
class SubnetNodeProperties(CartographyNodeProperties):
    """子網路節點屬性"""
    id: PropertyRef = PropertyRef("SubnetId")
    subnetid: PropertyRef = PropertyRef("SubnetId", extra_index=True)
    name: PropertyRef = PropertyRef("Name")
    cidrblock: PropertyRef = PropertyRef("CidrBlock")
    availabilityzone: PropertyRef = PropertyRef("AvailabilityZone")
    vpcid: PropertyRef = PropertyRef("VpcId")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SubnetToVpcRelProperties(CartographyRelProperties):
    """子網路到 VPC 關係屬性"""
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SubnetToVpcRel(CartographyRelSchema):
    """子網路到 VPC 關係"""
    target_node_label: str = "VPC"
    target_node_matcher: Dict[str, PropertyRef] = None
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_OF_VPC"
    properties: SubnetToVpcRelProperties = SubnetToVpcRelProperties()
    
    def __post_init__(self):
        if self.target_node_matcher is None:
            object.__setattr__(self, 'target_node_matcher', {
                "vpcid": PropertyRef("VpcId")
            })


@dataclass(frozen=True)
class SubnetSchema(CartographyNodeSchema):
    """子網路架構"""
    label: str = "Subnet"
    properties: SubnetNodeProperties = SubnetNodeProperties()
    sub_resource_relationship: EC2InstanceToAWSAccountRel = EC2InstanceToAWSAccountRel()
    other_relationships: List[CartographyRelSchema] = None
    
    def __post_init__(self):
        if self.other_relationships is None:
            object.__setattr__(self, 'other_relationships', [
                SubnetToVpcRel()
            ])


# ============================================================================
# EBS 磁碟模型
# ============================================================================

@dataclass(frozen=True)
class EBSVolumeNodeProperties(CartographyNodeProperties):
    """EBS 磁碟節點屬性"""
    id: PropertyRef = PropertyRef("VolumeId")
    volumeid: PropertyRef = PropertyRef("VolumeId", extra_index=True)
    size: PropertyRef = PropertyRef("Size")
    volumetype: PropertyRef = PropertyRef("VolumeType")
    state: PropertyRef = PropertyRef("State")
    encrypted: PropertyRef = PropertyRef("Encrypted")
    kmskeyid: PropertyRef = PropertyRef("KmsKeyId")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EBSVolumeToEC2InstanceRelProperties(CartographyRelProperties):
    """EBS 磁碟到 EC2 實例關係屬性"""
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EBSVolumeToEC2InstanceRel(CartographyRelSchema):
    """EBS 磁碟到 EC2 實例關係"""
    target_node_label: str = "EC2Instance"
    target_node_matcher: Dict[str, PropertyRef] = None
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ATTACHES_TO"
    properties: EBSVolumeToEC2InstanceRelProperties = EBSVolumeToEC2InstanceRelProperties()
    
    def __post_init__(self):
        if self.target_node_matcher is None:
            object.__setattr__(self, 'target_node_matcher', {
                "instanceid": PropertyRef("InstanceId")
            })


@dataclass(frozen=True)
class EBSVolumeSchema(CartographyNodeSchema):
    """EBS 磁碟架構"""
    label: str = "EBSVolume"
    properties: EBSVolumeNodeProperties = EBSVolumeNodeProperties()
    sub_resource_relationship: EC2InstanceToAWSAccountRel = EC2InstanceToAWSAccountRel()
    other_relationships: List[CartographyRelSchema] = None
    
    def __post_init__(self):
        if self.other_relationships is None:
            object.__setattr__(self, 'other_relationships', [
                EBSVolumeToEC2InstanceRel()
            ])


# ============================================================================
# 安全規則模型
# ============================================================================

@dataclass(frozen=True)
class SecurityRuleNodeProperties(CartographyNodeProperties):
    """安全規則節點屬性"""
    id: PropertyRef = PropertyRef("RuleId")
    ruleid: PropertyRef = PropertyRef("RuleId", extra_index=True)
    protocol: PropertyRef = PropertyRef("Protocol")
    portrange: PropertyRef = PropertyRef("PortRange")
    sourcecidr: PropertyRef = PropertyRef("SourceCIDR")
    direction: PropertyRef = PropertyRef("Direction")
    action: PropertyRef = PropertyRef("Action")
    description: PropertyRef = PropertyRef("Description")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SecurityRuleToSecurityGroupRelProperties(CartographyRelProperties):
    """安全規則到安全群組關係屬性"""
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SecurityRuleToSecurityGroupRel(CartographyRelSchema):
    """安全規則到安全群組關係"""
    target_node_label: str = "SecurityGroup"
    target_node_matcher: Dict[str, PropertyRef] = None
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_RULE"
    properties: SecurityRuleToSecurityGroupRelProperties = SecurityRuleToSecurityGroupRelProperties()
    
    def __post_init__(self):
        if self.target_node_matcher is None:
            object.__setattr__(self, 'target_node_matcher', {
                "groupid": PropertyRef("GroupId")
            })


@dataclass(frozen=True)
class SecurityRuleSchema(CartographyNodeSchema):
    """安全規則架構"""
    label: str = "SecurityRule"
    properties: SecurityRuleNodeProperties = SecurityRuleNodeProperties()
    sub_resource_relationship: EC2InstanceToAWSAccountRel = EC2InstanceToAWSAccountRel()
    other_relationships: List[CartographyRelSchema] = None
    
    def __post_init__(self):
        if self.other_relationships is None:
            object.__setattr__(self, 'other_relationships', [
                SecurityRuleToSecurityGroupRel()
            ])


# ============================================================================
# 索引定義
# ============================================================================

INDEXES = [
    # EC2 實例索引
    "CREATE INDEX IF NOT EXISTS FOR (n:EC2Instance) ON (n.id)",
    "CREATE INDEX IF NOT EXISTS FOR (n:EC2Instance) ON (n.lastupdated)",
    "CREATE INDEX IF NOT EXISTS FOR (n:EC2Instance) ON (n.instanceid)",
    "CREATE INDEX IF NOT EXISTS FOR (n:EC2Instance) ON (n.state)",
    "CREATE INDEX IF NOT EXISTS FOR (n:EC2Instance) ON (n.region)",
    
    # 安全群組索引
    "CREATE INDEX IF NOT EXISTS FOR (n:SecurityGroup) ON (n.id)",
    "CREATE INDEX IF NOT EXISTS FOR (n:SecurityGroup) ON (n.lastupdated)",
    "CREATE INDEX IF NOT EXISTS FOR (n:SecurityGroup) ON (n.groupid)",
    "CREATE INDEX IF NOT EXISTS FOR (n:SecurityGroup) ON (n.vpcid)",
    
    # VPC 索引
    "CREATE INDEX IF NOT EXISTS FOR (n:VPC) ON (n.id)",
    "CREATE INDEX IF NOT EXISTS FOR (n:VPC) ON (n.lastupdated)",
    "CREATE INDEX IF NOT EXISTS FOR (n:VPC) ON (n.vpcid)",
    "CREATE INDEX IF NOT EXISTS FOR (n:VPC) ON (n.region)",
    
    # 子網路索引
    "CREATE INDEX IF NOT EXISTS FOR (n:Subnet) ON (n.id)",
    "CREATE INDEX IF NOT EXISTS FOR (n:Subnet) ON (n.lastupdated)",
    "CREATE INDEX IF NOT EXISTS FOR (n:Subnet) ON (n.subnetid)",
    "CREATE INDEX IF NOT EXISTS FOR (n:Subnet) ON (n.vpcid)",
    "CREATE INDEX IF NOT EXISTS FOR (n:Subnet) ON (n.availabilityzone)",
    
    # EBS 磁碟索引
    "CREATE INDEX IF NOT EXISTS FOR (n:EBSVolume) ON (n.id)",
    "CREATE INDEX IF NOT EXISTS FOR (n:EBSVolume) ON (n.lastupdated)",
    "CREATE INDEX IF NOT EXISTS FOR (n:EBSVolume) ON (n.volumeid)",
    "CREATE INDEX IF NOT EXISTS FOR (n:EBSVolume) ON (n.state)",
    
    # 安全規則索引
    "CREATE INDEX IF NOT EXISTS FOR (n:SecurityRule) ON (n.id)",
    "CREATE INDEX IF NOT EXISTS FOR (n:SecurityRule) ON (n.lastupdated)",
    "CREATE INDEX IF NOT EXISTS FOR (n:SecurityRule) ON (n.ruleid)",
    "CREATE INDEX IF NOT EXISTS FOR (n:SecurityRule) ON (n.protocol)",
    "CREATE INDEX IF NOT EXISTS FOR (n:SecurityRule) ON (n.direction)",
]


def create_indexes(neo4j_session):
    """創建所有索引"""
    for index_query in INDEXES:
        try:
            neo4j_session.run(index_query)
        except Exception as e:
            print(f"創建索引失敗: {index_query}, 錯誤: {e}")


# ============================================================================
# 架構註冊表
# ============================================================================

SCHEMA_REGISTRY = {
    "EC2Instance": EC2InstanceSchema(),
    "SecurityGroup": SecurityGroupSchema(),
    "VPC": VPCSchema(),
    "Subnet": SubnetSchema(),
    "EBSVolume": EBSVolumeSchema(),
    "SecurityRule": SecurityRuleSchema(),
}


def get_schema(node_type: str) -> CartographyNodeSchema:
    """根據節點類型獲取架構"""
    return SCHEMA_REGISTRY.get(node_type)


def get_all_schemas() -> Dict[str, CartographyNodeSchema]:
    """獲取所有架構"""
    return SCHEMA_REGISTRY
