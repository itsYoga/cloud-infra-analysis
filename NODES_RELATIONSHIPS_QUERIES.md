# 🗂️ 圖形資料模型：節點、關係與查詢句介紹

## 📊 Mock 資料分析

基於 `enhanced_mock_aws_resources.json` 的實際資料結構，我們的圖形資料模型包含以下元素：

## 🔵 節點類型 (Node Types)

### 1. EC2Instance 節點
**代表：** AWS EC2 虛擬機器實例

**屬性範例：**
```json
{
  "InstanceID": "i-4565ff31fc57641ab",
  "Name": "recommendation-engine-staging-01",
  "State": "stopped",
  "InstanceType": "c5.xlarge",
  "PublicIpAddress": null,
  "PrivateIpAddress": "10.84.98.41",
  "LaunchTime": "2025-09-27T07:59:55.576648",
  "AvailabilityZone": "us-west-2a",
  "SubnetId": "subnet-1a56a26f43475ddf4",
  "VpcId": "vpc-9218c5cf0d06f1bc3"
}
```

### 2. SecurityGroup 節點
**代表：** AWS 安全群組（防火牆規則群組）

**屬性範例：**
```json
{
  "GroupId": "sg-8c6c6e0e1847bd533",
  "GroupName": "elasticsearch-dev",
  "Description": "Security group for elasticsearch cluster",
  "VpcId": "vpc-9218c5cf0d06f1bc3"
}
```

### 3. SecurityRule 節點
**代表：** 安全群組中的具體規則

**屬性範例：**
```json
{
  "RuleId": "rule-50e48bc22b12ee324",
  "Protocol": "tcp",
  "PortRange": "3389-3389",
  "SourceCIDR": "0.0.0.0/0",
  "Direction": "ingress",
  "Action": "allow"
}
```

### 4. VPC 節點
**代表：** AWS 虛擬私有雲

**屬性範例：**
```json
{
  "VpcId": "vpc-fdf266d12af0785b1",
  "Name": "production-vpc",
  "CidrBlock": "10.0.0.0/16",
  "State": "available"
}
```

### 5. Subnet 節點
**代表：** VPC 中的子網路

**屬性範例：**
```json
{
  "SubnetId": "subnet-1a56a26f43475ddf4",
  "VpcId": "vpc-9218c5cf0d06f1bc3",
  "AvailabilityZone": "us-west-2a",
  "CidrBlock": "10.0.1.0/24"
}
```

### 6. EBSVolume 節點
**代表：** AWS 彈性區塊儲存磁碟

**屬性範例：**
```json
{
  "VolumeId": "vol-82d8b32673cb6e005",
  "Size": 605,
  "VolumeType": "gp3",
  "State": "in-use",
  "Encrypted": true,
  "Iops": 3000
}
```

### 7. S3Bucket 節點
**代表：** AWS S3 儲存桶

**屬性範例：**
```json
{
  "BucketName": "company-backups-6261",
  "CreationDate": "2023-10-05T07:59:55.577233",
  "Arn": "arn:aws:s3:::company-backups-6261"
}
```

## 🔗 關係類型 (Relationship Types)

### 1. IS_MEMBER_OF
**用途：** EC2 實例屬於安全群組
**方向：** `(EC2Instance)-[:IS_MEMBER_OF]->(SecurityGroup)`

**範例：**
```cypher
// EC2 實例 i-4565ff31fc57641ab 屬於安全群組 sg-8c6c6e0e1847bd533
(i-4565ff31fc57641ab)-[:IS_MEMBER_OF]->(sg-8c6c6e0e1847bd533)
```

### 2. HAS_RULE
**用途：** 安全群組包含規則
**方向：** `(SecurityGroup)-[:HAS_RULE]->(SecurityRule)`

**範例：**
```cypher
// 安全群組 sg-8c6c6e0e1847bd533 包含規則 rule-50e48bc22b12ee324
(sg-8c6c6e0e1847bd533)-[:HAS_RULE]->(rule-50e48bc22b12ee324)
```

### 3. LOCATED_IN
**用途：** 資源位於子網路或 VPC 中
**方向：** `(EC2Instance)-[:LOCATED_IN]->(Subnet)-[:LOCATED_IN]->(VPC)`

**範例：**
```cypher
// EC2 實例位於子網路，子網路位於 VPC
(i-4565ff31fc57641ab)-[:LOCATED_IN]->(subnet-1a56a26f43475ddf4)
(subnet-1a56a26f43475ddf4)-[:LOCATED_IN]->(vpc-9218c5cf0d06f1bc3)
```

### 4. ATTACHES_TO
**用途：** EBS 磁碟附加到 EC2 實例
**方向：** `(EBSVolume)-[:ATTACHES_TO]->(EC2Instance)`

**範例：**
```cypher
// EBS 磁碟 vol-82d8b32673cb6e005 附加到 EC2 實例
(vol-82d8b32673cb6e005)-[:ATTACHES_TO]->(i-4565ff31fc57641ab)
```

## 🔍 核心查詢句 (Core Queries)

### 1. 安全分析查詢

#### 1.1 暴露的服務檢測
```cypher
// 找出所有允許從任何 IP (0.0.0.0/0) 存取 22 號連接埠的主機
MATCH (instance:EC2Instance)-[:IS_MEMBER_OF]->(sg:SecurityGroup),
      (sg)-[:HAS_RULE]->(rule:SecurityRule)
WHERE rule.sourcecidr = '0.0.0.0/0' 
  AND rule.portrange CONTAINS '22'
RETURN instance.name, instance.instanceid, instance.publicip,
       sg.name, rule.portrange, rule.protocol
```

#### 1.2 過度寬鬆的安全群組
```cypher
// 找出所有允許從任何 IP 存取的安全群組規則
MATCH (sg:SecurityGroup)-[:HAS_RULE]->(rule:SecurityRule)
WHERE rule.sourcecidr = '0.0.0.0/0'
  AND rule.direction = 'ingress'
RETURN sg.name, sg.groupid, rule.portrange, 
       rule.protocol, rule.sourcecidr
```

#### 1.3 未加密的資源
```cypher
// 找出所有未加密的 EBS 磁碟
MATCH (volume:EBSVolume)
WHERE volume.encrypted = false OR volume.encrypted IS NULL
RETURN volume.volumeid, volume.size, volume.volumetype, 
       volume.state, volume.region
```

### 2. 故障分析查詢

#### 2.1 關鍵節點識別
```cypher
// 找出連接數最多的節點（關鍵節點）
MATCH (n)
WITH n, COUNT { (n)--() } as connection_count
WHERE connection_count > 2
RETURN labels(n)[0] as node_type, n.instanceid, 
       n.name, n.vpcid, connection_count
ORDER BY connection_count DESC
```

#### 2.2 單點故障檢測
```cypher
// 找出只有一個連接的節點（單點故障）
MATCH (n)
WITH n, COUNT { (n)--() } as connection_count
WHERE connection_count = 1
RETURN labels(n)[0] as node_type, n.instanceid,
       n.volumeid, n.name, connection_count
```

#### 2.3 網路拓撲分析
```cypher
// 分析 VPC 和子網路的結構
MATCH (vpc:VPC)
OPTIONAL MATCH (subnet:Subnet)-[:LOCATED_IN]->(vpc)
OPTIONAL MATCH (instance:EC2Instance)-[:LOCATED_IN]->(subnet)
RETURN vpc.vpcid, collect(DISTINCT subnet.subnetid) as subnets,
       collect(DISTINCT instance.instanceid) as instances,
       size(collect(DISTINCT subnet)) as subnet_count,
       size(collect(DISTINCT instance)) as instance_count
```

### 3. 成本優化查詢

#### 3.1 孤兒 EBS 磁碟
```cypher
// 找出未附加到任何實例的 EBS 磁碟
MATCH (volume:EBSVolume)
WHERE NOT (volume)-[:ATTACHES_TO]->(:EC2Instance)
  AND volume.state = 'available'
RETURN volume.volumeid, volume.size, volume.volumetype,
       volume.region, volume.iops
ORDER BY volume.size DESC
```

#### 3.2 未使用的安全群組
```cypher
// 找出沒有關聯任何實例的安全群組
MATCH (sg:SecurityGroup)
WHERE NOT (sg)<-[:IS_MEMBER_OF]-(:EC2Instance)
RETURN sg.name, sg.groupid, sg.description, sg.vpcid
```

#### 3.3 S3 儲存桶分析
```cypher
// 分析 S3 儲存桶資源
MATCH (bucket:S3Bucket)
RETURN bucket.name, bucket.region, bucket.creationdate,
       bucket.arn
ORDER BY bucket.creationdate DESC
```

## 🎯 實際資料統計

基於我們的 Mock 資料：

### 節點統計
- **EC2Instance**: 41 個實例
- **SecurityGroup**: 30 個安全群組
- **SecurityRule**: 12 個安全規則
- **VPC**: 8 個虛擬私有雲
- **Subnet**: 37 個子網路
- **EBSVolume**: 43 個磁碟
- **S3Bucket**: 包含多個儲存桶

### 關係統計
- **IS_MEMBER_OF**: EC2 實例與安全群組的關聯
- **HAS_RULE**: 安全群組與規則的關聯
- **LOCATED_IN**: 資源的地理位置關聯
- **ATTACHES_TO**: 磁碟與實例的關聯

## 🚀 查詢效能優化

### 索引建議
```cypher
// 為常用查詢屬性建立索引
CREATE INDEX FOR (n:EC2Instance) ON (n.instanceid)
CREATE INDEX FOR (n:SecurityGroup) ON (n.groupid)
CREATE INDEX FOR (n:VPC) ON (n.vpcid)
CREATE INDEX FOR (n:Subnet) ON (n.subnetid)
CREATE INDEX FOR (n:EBSVolume) ON (n.volumeid)
```

### 查詢最佳化
- 使用 `WHERE` 子句限制搜尋範圍
- 使用 `LIMIT` 限制結果數量
- 使用 `ORDER BY` 排序結果
- 使用 `WITH` 子句優化複雜查詢

---

## 📝 演示建議

### 1. 展示節點類型
```cypher
// 顯示所有節點類型
MATCH (n)
RETURN DISTINCT labels(n) as node_types
```

### 2. 展示關係類型
```cypher
// 顯示所有關係類型
MATCH ()-[r]->()
RETURN DISTINCT type(r) as relationship_types
```

### 3. 展示網路拓撲
```cypher
// 展示完整的網路拓撲
MATCH (vpc:VPC)-[:LOCATED_IN*0..1]-(subnet:Subnet)-[:LOCATED_IN*0..1]-(instance:EC2Instance)
RETURN vpc, subnet, instance
LIMIT 20
```

這個圖形資料模型完美地展現了雲端基礎設施的複雜關係，為安全分析、故障檢測和成本優化提供了強大的查詢能力！ 🎯
