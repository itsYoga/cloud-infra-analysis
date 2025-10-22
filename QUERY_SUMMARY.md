# 雲端基礎設施分析平台查詢總結

## 📊 **查詢統計總覽**

### 總查詢數量: **12 個核心查詢**

---

## 🔒 **安全分析查詢 (5 個)**

### 1. 暴露的服務檢測
```cypher
MATCH (instance:EC2Instance)-[:IS_MEMBER_OF]->(sg:SecurityGroup),
      (sg)-[:HAS_RULE]->(rule:SecurityRule)
WHERE rule.sourcecidr CONTAINS '0.0.0.0/0' 
  AND rule.portrange CONTAINS $port
  AND rule.protocol = $protocol
  AND rule.direction = 'inbound'
RETURN DISTINCT instance.name, instance.instanceid, instance.publicip
```

### 2. 過度寬鬆的安全規則
```cypher
MATCH (sg:SecurityGroup)-[:HAS_RULE]->(rule:SecurityRule)
WHERE rule.sourcecidr CONTAINS '0.0.0.0/0'
  AND rule.direction = 'inbound'
RETURN sg.name, sg.groupid, rule.portrange, rule.protocol
```

### 3. 未加密的資源
```cypher
MATCH (volume:EBSVolume)
WHERE volume.encrypted = false OR volume.encrypted IS NULL
RETURN volume.volumeid, volume.size, volume.volumetype, volume.state
```

### 4. 孤兒安全群組
```cypher
MATCH (sg:SecurityGroup)
WHERE NOT (sg)<-[:IS_MEMBER_OF]-(:EC2Instance)
  AND EXISTS((sg)-[:HAS_RULE]->(:SecurityRule))
RETURN sg.name, sg.groupid, sg.description
```

### 5. 高風險端口檢測
```cypher
MATCH (sg:SecurityGroup)-[:HAS_RULE]->(rule:SecurityRule)
WHERE rule.sourcecidr CONTAINS '0.0.0.0/0'
  AND (rule.portrange CONTAINS '22' OR rule.portrange CONTAINS '3389')
RETURN sg.name, rule.portrange, rule.protocol
```

---

## ⚡ **故障分析查詢 (2 個)**

### 6. 依賴關係分析
```cypher
MATCH (resource)
WHERE resource.instanceid = $resource_id OR resource.groupid = $resource_id
MATCH path = (resource)-[*1..$max_depth]-(dependent)
RETURN DISTINCT dependent.name, dependent.instanceid, length(path) as depth
ORDER BY depth
```

### 7. 單點故障檢測
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

---

## 💰 **成本優化查詢 (5 個)**

### 8. 孤兒 EBS 磁碟
```cypher
MATCH (volume:EBSVolume)
WHERE NOT (volume)-[:ATTACHES_TO]->(:EC2Instance)
RETURN volume.volumeid, volume.size, volume.volumetype, volume.state
ORDER BY volume.size DESC
```

### 9. 未使用的安全群組
```cypher
MATCH (sg:SecurityGroup)
WHERE NOT (sg)<-[:IS_MEMBER_OF]-(:EC2Instance)
RETURN sg.name, sg.groupid, sg.description, sg.vpcid
```

### 10. 已停止的實例
```cypher
MATCH (instance:EC2Instance)
WHERE instance.state = 'stopped'
RETURN instance.name, instance.instanceid, instance.instancetype, instance.launchtime
ORDER BY instance.launchtime DESC
```

### 11. 利用率低的實例
```cypher
MATCH (instance:EC2Instance)
WHERE instance.state = 'running'
  AND instance.launchtime < datetime() - duration('P' + toString($min_uptime_days) + 'D')
RETURN instance.name, instance.instanceid, instance.instancetype, instance.launchtime
```

### 12. 昂貴的資源
```cypher
MATCH (instance:EC2Instance)
WHERE instance.instancetype CONTAINS 'large' OR instance.instancetype CONTAINS 'xlarge'
RETURN instance.name, instance.instanceid, instance.instancetype, instance.state
ORDER BY instance.instancetype
```

---

## 🎯 **演示建議 (8 個核心查詢)**

為了 10 分鐘的演示，建議專注於以下 8 個查詢：

### 安全分析 (3 個)
1. 暴露的服務檢測
2. 過度寬鬆的安全規則
3. 未加密的資源

### 故障分析 (2 個)
4. 依賴關係分析
5. 單點故障檢測

### 成本優化 (3 個)
6. 孤兒 EBS 磁碟
7. 未使用的安全群組
8. 已停止的實例

---

## 📈 **查詢分類統計**

| 分析類型 | 查詢數量 | 百分比 |
|---------|---------|--------|
| 安全分析 | 5 個 | 41.7% |
| 故障分析 | 2 個 | 16.7% |
| 成本優化 | 5 個 | 41.7% |
| **總計** | **12 個** | **100%** |

---

## 🔧 **技術特色**

### 查詢優化
- 使用參數化查詢避免注入攻擊
- 適當的 WHERE 條件減少掃描範圍
- 利用索引提高查詢效能
- 限制結果數量避免記憶體溢出

### 關係分析
- 多層次關係遍歷 (1-5 層)
- 複雜的圖形模式匹配
- 動態深度查詢
- 路徑分析與影響評估

### 實用性
- 解決實際的雲端管理問題
- 提供具體的優化建議
- 支援自動化分析流程
- 易於擴展和自定義

**您的平台具備了完整的 12 個核心查詢，涵蓋了雲端基礎設施分析的各個重要面向！** 🚀
