# Cypher 查詢範例

## 🔍 基本查詢

### 1. 節點查詢

#### 查詢所有 EC2 實例
```cypher
MATCH (n:EC2Instance)
RETURN n
LIMIT 10
```

#### 查詢特定實例
```cypher
MATCH (n:EC2Instance {InstanceID: 'i-1234567890abcdef0'})
RETURN n
```

#### 查詢實例屬性
```cypher
MATCH (n:EC2Instance)
RETURN n.Name, n.InstanceType, n.State
LIMIT 10
```

### 2. 關係查詢

#### 查詢實例與安全群組的關係
```cypher
MATCH (instance:EC2Instance)-[:IS_MEMBER_OF]->(sg:SecurityGroup)
RETURN instance.Name, sg.GroupName
```

#### 查詢 VPC 內的資源
```cypher
MATCH (vpc:VPC)-[:CONTAINS]->(resource)
RETURN vpc.VpcId, labels(resource), count(resource) as resource_count
```

## 🔒 安全分析查詢

### 1. 暴露服務檢測

#### 找出暴露的 SSH 服務
```cypher
MATCH (instance:EC2Instance)-[:IS_MEMBER_OF]->(sg:SecurityGroup),
      (sg)-[:HAS_RULE]->(rule:Rule)
WHERE rule.SourceCIDR = '0.0.0.0/0' 
  AND rule.PortRange CONTAINS '22'
  AND rule.Protocol = 'tcp'
  AND rule.Direction = 'inbound'
RETURN instance.Name, instance.PublicIP, sg.GroupName, rule.PortRange
```

#### 找出暴露的 RDP 服務
```cypher
MATCH (instance:EC2Instance)-[:IS_MEMBER_OF]->(sg:SecurityGroup),
      (sg)-[:HAS_RULE]->(rule:Rule)
WHERE rule.SourceCIDR = '0.0.0.0/0' 
  AND rule.PortRange CONTAINS '3389'
  AND rule.Protocol = 'tcp'
  AND rule.Direction = 'inbound'
RETURN instance.Name, instance.PublicIP, sg.GroupName, rule.PortRange
```

#### 找出暴露的 HTTP/HTTPS 服務
```cypher
MATCH (instance:EC2Instance)-[:IS_MEMBER_OF]->(sg:SecurityGroup),
      (sg)-[:HAS_RULE]->(rule:Rule)
WHERE rule.SourceCIDR = '0.0.0.0/0' 
  AND (rule.PortRange CONTAINS '80' OR rule.PortRange CONTAINS '443')
  AND rule.Protocol = 'tcp'
  AND rule.Direction = 'inbound'
RETURN instance.Name, instance.PublicIP, sg.GroupName, rule.PortRange
```

### 2. 過度寬鬆規則檢測

#### 找出允許所有流量的規則
```cypher
MATCH (sg:SecurityGroup)-[:HAS_RULE]->(rule:Rule)
WHERE rule.SourceCIDR = '0.0.0.0/0'
  AND rule.PortRange = '0-65535'
  AND rule.Protocol = 'tcp'
RETURN sg.GroupName, rule.RuleID, rule.Description
```

#### 找出允許所有協議的規則
```cypher
MATCH (sg:SecurityGroup)-[:HAS_RULE]->(rule:Rule)
WHERE rule.SourceCIDR = '0.0.0.0/0'
  AND rule.Protocol = 'all'
RETURN sg.GroupName, rule.RuleID, rule.Description
```

### 3. 網路分段分析

#### 分析 VPC 內的網路分段
```cypher
MATCH (vpc:VPC)-[:CONTAINS]->(subnet:Subnet)
OPTIONAL MATCH (subnet)-[:CONTAINS]->(instance:EC2Instance)
RETURN vpc.VpcId, subnet.SubnetId, 
       count(instance) as instance_count,
       subnet.CidrBlock
ORDER BY vpc.VpcId, subnet.SubnetId
```

#### 分析跨子網路的連接
```cypher
MATCH (instance1:EC2Instance)-[:CONNECTS_TO]->(instance2:EC2Instance)
WHERE instance1.SubnetId <> instance2.SubnetId
RETURN instance1.Name, instance1.SubnetId, 
       instance2.Name, instance2.SubnetId
```

## 🚨 故障衝擊分析查詢

### 1. 關鍵節點識別

#### 找出連接數最多的節點
```cypher
MATCH (n)
WITH n, size((n)--()) as connection_count
WHERE connection_count > 5
RETURN n.Name, n.InstanceID, connection_count
ORDER BY connection_count DESC
LIMIT 10
```

#### 找出度中心性最高的節點
```cypher
MATCH (n)
WITH n, size((n)--()) as degree
WHERE degree > 0
RETURN n.Name, n.InstanceID, degree
ORDER BY degree DESC
LIMIT 10
```

### 2. 依賴關係分析

#### 分析特定實例的依賴關係
```cypher
MATCH path = (start:EC2Instance {InstanceID: 'i-1234567890abcdef0'})-[:CONNECTS_TO*1..3]-(dependent)
RETURN path, length(path) as dependency_depth
ORDER BY dependency_depth
```

#### 找出所有依賴特定實例的資源
```cypher
MATCH (dependent)-[:CONNECTS_TO*1..5]->(critical:EC2Instance {InstanceID: 'i-1234567890abcdef0'})
RETURN DISTINCT dependent.Name, dependent.InstanceID, 
       length(shortestPath((dependent)-[:CONNECTS_TO*]-(critical))) as hop_count
ORDER BY hop_count
```

### 3. 故障傳播模擬

#### 模擬特定節點故障的影響範圍
```cypher
MATCH (failed:EC2Instance {InstanceID: 'i-1234567890abcdef0'})
MATCH path = (failed)-[:CONNECTS_TO*1..5]-(affected)
RETURN DISTINCT affected.Name, affected.InstanceID, 
       length(path) as impact_level
ORDER BY impact_level
```

#### 找出故障會影響的關鍵服務
```cypher
MATCH (failed:EC2Instance {InstanceID: 'i-1234567890abcdef0'})
MATCH path = (failed)-[:CONNECTS_TO*1..3]-(affected)
WHERE affected.Name CONTAINS 'database' OR affected.Name CONTAINS 'api'
RETURN DISTINCT affected.Name, affected.InstanceID, 
       length(path) as impact_level
ORDER BY impact_level
```

## 💰 成本優化查詢

### 1. 孤兒資源檢測

#### 找出未附加的 EBS 磁碟
```cypher
MATCH (volume:EBSVolume)
WHERE NOT (volume)-[:ATTACHES_TO]->(:EC2Instance)
  AND volume.State = 'available'
RETURN volume.VolumeId, volume.Size, volume.VolumeType,
       volume.CreationDate
ORDER BY volume.Size DESC
```

#### 找出未使用的安全群組
```cypher
MATCH (sg:SecurityGroup)
WHERE NOT (sg)<-[:IS_MEMBER_OF]-(:EC2Instance)
RETURN sg.GroupName, sg.GroupID, sg.Description
```

#### 找出未使用的 VPC
```cypher
MATCH (vpc:VPC)
WHERE NOT (vpc)-[:CONTAINS]->(:Subnet)
RETURN vpc.VpcId, vpc.Name, vpc.CidrBlock
```

### 2. 資源利用率分析

#### 分析不同實例類型的分布
```cypher
MATCH (instance:EC2Instance)
RETURN instance.InstanceType, count(instance) as count,
       collect(instance.State) as states
ORDER BY count DESC
```

#### 分析不同狀態的實例分布
```cypher
MATCH (instance:EC2Instance)
RETURN instance.State, count(instance) as count,
       collect(instance.InstanceType) as types
ORDER BY count DESC
```

#### 分析磁碟使用情況
```cypher
MATCH (volume:EBSVolume)
RETURN volume.VolumeType, count(volume) as count,
       sum(volume.Size) as total_size,
       avg(volume.Size) as avg_size
ORDER BY count DESC
```

### 3. 成本分配分析

#### 按環境分析資源分布
```cypher
MATCH (instance:EC2Instance)
WHERE instance.Tags IS NOT NULL
UNWIND instance.Tags as tag
WHERE tag.Key = 'Environment'
RETURN tag.Value as environment, count(instance) as instance_count
ORDER BY instance_count DESC
```

#### 按團隊分析資源分布
```cypher
MATCH (instance:EC2Instance)
WHERE instance.Tags IS NOT NULL
UNWIND instance.Tags as tag
WHERE tag.Key = 'Team'
RETURN tag.Value as team, count(instance) as instance_count
ORDER BY instance_count DESC
```

## 📊 統計分析查詢

### 1. 資源統計

#### 總體資源統計
```cypher
MATCH (n)
RETURN labels(n)[0] as resource_type, count(n) as count
ORDER BY count DESC
```

#### 按區域統計資源
```cypher
MATCH (n)
WHERE n.Region IS NOT NULL
RETURN n.Region, labels(n)[0] as resource_type, count(n) as count
ORDER BY n.Region, count DESC
```

### 2. 關係統計

#### 關係類型統計
```cypher
MATCH ()-[r]->()
RETURN type(r) as relationship_type, count(r) as count
ORDER BY count DESC
```

#### 節點連接度統計
```cypher
MATCH (n)
WITH n, size((n)--()) as degree
WHERE degree > 0
RETURN labels(n)[0] as node_type, 
       avg(degree) as avg_degree,
       max(degree) as max_degree,
       min(degree) as min_degree
ORDER BY avg_degree DESC
```

### 3. 網路拓撲分析

#### 找出網路中的孤立節點
```cypher
MATCH (n)
WHERE size((n)--()) = 0
RETURN labels(n)[0] as node_type, count(n) as count
ORDER BY count DESC
```

#### 找出網路中的橋接節點
```cypher
MATCH (n)
WHERE size((n)--()) = 2
RETURN labels(n)[0] as node_type, count(n) as count
ORDER BY count DESC
```

## 🔧 進階查詢技巧

### 1. 使用參數化查詢
```cypher
// 使用參數
MATCH (n:EC2Instance {InstanceID: $instance_id})
RETURN n
```

### 2. 使用條件查詢
```cypher
// 條件查詢
MATCH (n:EC2Instance)
WHERE n.State = 'running' AND n.PublicIP IS NOT NULL
RETURN n.Name, n.PublicIP
```

### 3. 使用聚合函數
```cypher
// 聚合查詢
MATCH (n:EC2Instance)
RETURN count(n) as total_instances,
       count(CASE WHEN n.State = 'running' THEN 1 END) as running_instances,
       count(CASE WHEN n.State = 'stopped' THEN 1 END) as stopped_instances
```

### 4. 使用排序和分頁
```cypher
// 排序和分頁
MATCH (n:EC2Instance)
RETURN n.Name, n.InstanceType, n.State
ORDER BY n.Name
SKIP 0 LIMIT 10
```

### 5. 使用正則表達式
```cypher
// 正則表達式查詢
MATCH (n:EC2Instance)
WHERE n.Name =~ '.*prod.*'
RETURN n.Name, n.InstanceType
```

---

*這些 Cypher 查詢範例涵蓋了雲端基礎設施分析的主要場景，可以根據具體需求進行調整和擴展。*