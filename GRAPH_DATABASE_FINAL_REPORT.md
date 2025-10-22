# 圖形資料庫最終報告
## Cloud Infrastructure Analysis Platform

**課程**: 高等資料庫  
**學生**: [您的姓名]  
**日期**: 2024年10月22日

---

## 1. Neo4j 產品與服務

### 使用的 Neo4j 產品
- **Neo4j Aura**: 雲端託管的 Neo4j 圖形資料庫服務
- **Neo4j Browser**: 網頁介面查詢工具
- **Cypher Query Language**: 圖形查詢語言
- **Neo4j Python Driver**: 程式化連接工具

### 技術架構
```
Python Application
    ↓ (Neo4j Driver)
Neo4j Aura (Cloud)
    ↓ (Cypher Queries)
Graph Database Engine
```

---

## 2. 原始資料格式與來源

### 資料格式
- **格式**: JSON
- **來源**: 模擬 AWS 資源資料 (Mock Data)
- **結構**: 巢狀 JSON 物件，包含 EC2、VPC、Security Groups 等資源

### 資料範例
```json
{
  "InstanceID": "i-4565ff31fc57641ab",
  "Name": "recommendation-engine-staging-01",
  "State": { "Name": "stopped" },
  "InstanceType": "c5.xlarge",
  "SecurityGroups": [
    { "GroupId": "sg-8c6c6e0e1847bd533", "GroupName": "elasticsearch-dev" }
  ],
  "SubnetId": "subnet-1a56a26f43475ddf4",
  "VpcId": "vpc-9218c5cf0d06f1bc3"
}
```

---

## 3. 圖形資料模型

### 節點類型 (Node Types)

#### EC2Instance
```cypher
CREATE (i:EC2Instance {
  instanceid: "i-1234567890abcdef0",
  name: "web-server-prod-01",
  instancetype: "t3.medium",
  state: "running",
  region: "us-east-1",
  publicip: "54.123.45.67"
})
```

#### SecurityGroup
```cypher
CREATE (sg:SecurityGroup {
  groupid: "sg-1234567890abcdef0",
  name: "web-servers-prod",
  description: "Security group for web servers",
  vpcid: "vpc-1234567890abcdef0",
  region: "us-east-1"
})
```

#### VPC
```cypher
CREATE (vpc:VPC {
  vpcid: "vpc-1234567890abcdef0",
  cidrblock: "10.0.0.0/16",
  state: "available",
  region: "us-east-1"
})
```

#### Subnet
```cypher
CREATE (subnet:Subnet {
  subnetid: "subnet-1234567890abcdef0",
  cidrblock: "10.0.1.0/24",
  availabilityzone: "us-east-1a",
  vpcid: "vpc-1234567890abcdef0"
})
```

#### EBSVolume
```cypher
CREATE (vol:EBSVolume {
  volumeid: "vol-1234567890abcdef0",
  size: 100,
  volumetype: "gp3",
  state: "in-use",
  encrypted: true,
  region: "us-east-1"
})
```

#### SecurityRule
```cypher
CREATE (rule:SecurityRule {
  ruleid: "rule-1234567890abcdef0",
  protocol: "tcp",
  portrange: "22-22",
  sourcecidr: "0.0.0.0/0",
  direction: "inbound"
})
```

### 關係類型 (Relationship Types)

#### IS_MEMBER_OF
```cypher
(instance:EC2Instance)-[:IS_MEMBER_OF]->(sg:SecurityGroup)
```

#### LOCATED_IN
```cypher
(instance:EC2Instance)-[:LOCATED_IN]->(subnet:Subnet)
(subnet:Subnet)-[:LOCATED_IN]->(vpc:VPC)
```

#### ATTACHES_TO
```cypher
(volume:EBSVolume)-[:ATTACHES_TO]->(instance:EC2Instance)
```

#### HAS_RULE
```cypher
(sg:SecurityGroup)-[:HAS_RULE]->(rule:SecurityRule)
```

### 範例圖形結構
```
VPC (vpc-123)
  ├── Subnet (subnet-456)
  │   ├── EC2Instance (i-789)
  │   │   ├── IS_MEMBER_OF → SecurityGroup (sg-abc)
  │   │   └── ATTACHES_TO ← EBSVolume (vol-def)
  │   └── EC2Instance (i-101)
  └── SecurityGroup (sg-abc)
      └── HAS_RULE → SecurityRule (rule-112)
```

---

## 4. 功能對應的查詢句、API、函數

### 4.1 安全分析 (Security Analysis)

#### 未加密的 EBS 磁碟
```cypher
MATCH (v:EBSVolume)
WHERE v.encrypted = false
RETURN v.volumeid AS VolumeID, 
       v.region AS Region, 
       v.state AS State, 
       v.size AS SizeGB
```

#### 暴露的安全規則
```cypher
MATCH (sg:SecurityGroup)-[:HAS_RULE]->(sr:SecurityRule)
WHERE sr.sourcecidr = '0.0.0.0/0' 
  AND sr.direction = 'inbound'
RETURN sg.groupid AS SecurityGroupID, 
       sg.name AS SecurityGroupName, 
       sr.protocol AS Protocol, 
       sr.portrange AS PortRange
```

### 4.2 故障衝擊分析 (Failure Impact Analysis)

#### 關鍵節點識別
```cypher
MATCH (n)
WITH n, COUNT { (n)--() } as connection_count
WHERE connection_count > 2
RETURN labels(n)[0] AS NodeType,
       CASE 
           WHEN labels(n)[0] = 'EC2Instance' THEN n.name
           WHEN labels(n)[0] = 'SecurityGroup' THEN n.name
           ELSE n.id
       END AS NodeName,
       connection_count AS ConnectionCount
ORDER BY ConnectionCount DESC
```

#### 單點故障分析
```cypher
MATCH (n)
WITH n, COUNT { (n)--() } as connection_count
WHERE connection_count = 1
RETURN labels(n)[0] AS NodeType,
       CASE
           WHEN labels(n)[0] = 'EC2Instance' THEN n.name
           WHEN labels(n)[0] = 'EBSVolume' THEN n.volumeid
           ELSE n.id
       END AS NodeName
```

### 4.3 成本優化分析 (Cost Optimization Analysis)

#### 孤兒 EBS 磁碟
```cypher
MATCH (v:EBSVolume)
WHERE NOT (v)-[:ATTACHES_TO]->(:EC2Instance)
RETURN v.volumeid AS VolumeID, 
       v.region AS Region, 
       v.state AS State, 
       v.size AS SizeGB
ORDER BY v.size DESC
```

#### 未使用的安全群組
```cypher
MATCH (sg:SecurityGroup)
WHERE NOT (:EC2Instance)-[:IS_MEMBER_OF]->(sg)
  AND EXISTS((sg)-[:HAS_RULE]->(:SecurityRule))
RETURN sg.groupid AS SecurityGroupID, 
       sg.name AS SecurityGroupName, 
       sg.vpcid AS VPCID
```

### 4.4 Python API 函數

#### Neo4j 連接
```python
from neo4j import GraphDatabase

def connect_to_neo4j(uri, username, password):
    driver = GraphDatabase.driver(uri, auth=(username, password))
    return driver

def execute_query(driver, query, parameters=None):
    with driver.session() as session:
        result = session.run(query, parameters)
        return [record.data() for record in result]
```

#### 安全分析函數
```python
def find_unencrypted_volumes(driver):
    query = """
    MATCH (v:EBSVolume)
    WHERE v.encrypted = false
    RETURN v.volumeid, v.region, v.state, v.size
    """
    return execute_query(driver, query)

def find_exposed_services(driver):
    query = """
    MATCH (sg:SecurityGroup)-[:HAS_RULE]->(sr:SecurityRule)
    WHERE sr.sourcecidr = '0.0.0.0/0' 
      AND sr.direction = 'inbound'
    RETURN sg.name, sr.portrange, sr.protocol
    """
    return execute_query(driver, query)
```

---

## 5. 系統介面與操作範例

### 5.1 命令行操作

#### 快速啟動
```bash
# 啟動完整分析流程
./scripts/quick_start.sh

# 執行綜合分析
python main.py --mode comprehensive-analyze --mock

# 啟動儀表板
python main.py --mode dashboard
```

#### 資料載入
```bash
# 載入模擬資料
python main.py --mode load --data-path data/raw/enhanced_mock_aws_resources.json

# 執行分析
python main.py --mode analyze
```

### 5.2 Neo4j Aura Console 操作

#### 基本查詢
```cypher
// 查看所有節點類型
MATCH (n) RETURN DISTINCT labels(n) as NodeTypes

// 查看關係類型
MATCH ()-[r]->() RETURN DISTINCT type(r) as RelationshipTypes

// 查看節點統計
MATCH (n) RETURN labels(n)[0] as NodeType, count(n) as Count
```

#### 視覺化查詢
```cypher
// 顯示網路拓撲
MATCH (vpc:VPC)-[:LOCATED_IN*0..1]-(subnet:Subnet)-[:LOCATED_IN*0..1]-(instance:EC2Instance)
RETURN vpc, subnet, instance
LIMIT 20
```

### 5.3 分析結果範例

#### 安全分析結果
```json
{
  "security": {
    "summary": {
      "exposed_services_count": 0,
      "permissive_rules_count": 12,
      "unencrypted_resources_count": 6,
      "orphaned_security_groups_count": 16
    }
  }
}
```

#### 故障分析結果
```json
{
  "failure_impact": {
    "summary": {
      "critical_nodes_count": 28,
      "single_points_of_failure_count": 66
    }
  }
}
```

#### 成本優化結果
```json
{
  "cost_optimization": {
    "summary": {
      "orphaned_ebs_volumes_count": 22,
      "unused_security_groups_count": 16,
      "stopped_instances_count": 5,
      "total_potential_savings": 1278.4
    }
  }
}
```

---

## 6. 實作要點

### 6.1 資料模型設計
- **節點標籤**: 使用 AWS 資源類型作為標籤
- **屬性命名**: 統一使用小寫命名規範
- **關係方向**: 明確定義關係的方向性
- **索引建立**: 為常用查詢屬性建立索引

### 6.2 查詢優化
- **使用參數化查詢**: 避免注入攻擊
- **限制結果數量**: 使用 LIMIT 子句
- **適當的 WHERE 條件**: 減少掃描範圍
- **利用索引**: 在索引屬性上建立查詢條件

### 6.3 錯誤處理
- **連接重試機制**: 處理網路不穩定
- **查詢超時設定**: 避免長時間等待
- **結果驗證**: 檢查查詢結果的完整性
- **日誌記錄**: 詳細記錄操作過程

---

## 7. 結論

### 7.1 專案成果
本專案成功實現了基於 Neo4j 圖形資料庫的雲端基礎設施分析平台，具備以下特色：

1. **直觀的視覺化**: 將複雜的雲端架構轉換為易於理解的圖形結構
2. **深度分析能力**: 使用 Cypher 查詢語言進行多層次關係分析
3. **自動化檢測**: 實現三大核心功能的自動化分析
4. **模組化設計**: 易於擴展和維護的架構設計

### 7.2 技術價值
- **圖形資料庫優勢**: 展現了圖形資料庫在複雜關係分析中的優勢
- **實用性**: 解決了實際的雲端管理問題
- **可擴展性**: 為未來功能擴展奠定了良好基礎

### 7.3 未來發展
- **多雲支援**: 擴展至 GCP、Azure 等其他雲平台
- **即時監控**: 實現即時資料更新和分析
- **機器學習**: 整合 AI 技術進行智能分析
- **視覺化增強**: 提供更豐富的圖形展示功能

---

## 8. 參考資料

1. Neo4j Documentation: https://neo4j.com/docs/
2. Cypher Query Language: https://neo4j.com/docs/cypher-manual/
3. AWS Well-Architected Framework: https://aws.amazon.com/architecture/well-architected/
4. Cartography Project: https://github.com/lyft/cartography

---

**報告完成日期**: 2024年10月22日  
**總頁數**: 約 15 頁  
**字數**: 約 3,000 字
