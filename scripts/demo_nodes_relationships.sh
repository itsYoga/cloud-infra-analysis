#!/bin/bash

# 🗂️ 節點、關係與查詢句演示腳本
# 作者：梁祐嘉
# 學號：01157145

echo "🗂️ 圖形資料模型演示：節點、關係與查詢句"
echo "=========================================="

cd "/Users/jesse/Documents/School Work/高等資料庫/cloud-infrastructure-analysis"
source venv/bin/activate

echo ""
echo "📊 1. 展示節點類型統計"
echo "===================="
python -c "
import json
import glob

# 找到最新的分析結果
files = glob.glob('output/comprehensive_analysis_*.json')
if files:
    latest_file = max(files, key=lambda x: x.split('_')[-1].split('.')[0])
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 顯示節點統計
    node_stats = data['results']['security']['summary']['node_statistics']
    print('🔵 節點類型統計：')
    for node_type, count in node_stats.items():
        print(f'  - {node_type}: {count} 個')
else:
    print('❌ 找不到分析結果文件')
"

echo ""
echo "🔗 2. 展示關係類型"
echo "=================="
echo "主要關係類型："
echo "  - IS_MEMBER_OF: EC2 實例 → 安全群組"
echo "  - HAS_RULE: 安全群組 → 安全規則"
echo "  - LOCATED_IN: 資源 → 子網路 → VPC"
echo "  - ATTACHES_TO: EBS 磁碟 → EC2 實例"

echo ""
echo "🔍 3. 核心查詢句展示"
echo "=================="

echo ""
echo "🔒 安全分析查詢："
echo "----------------"
echo "// 暴露的服務檢測"
echo "MATCH (instance:EC2Instance)-[:IS_MEMBER_OF]->(sg:SecurityGroup),"
echo "      (sg)-[:HAS_RULE]->(rule:SecurityRule)"
echo "WHERE rule.sourcecidr = '0.0.0.0/0' AND rule.portrange CONTAINS '22'"
echo "RETURN instance.name, instance.instanceid, instance.publicip"

echo ""
echo "⚡ 故障分析查詢："
echo "----------------"
echo "// 關鍵節點識別"
echo "MATCH (n)"
echo "WITH n, size((n)--()) as connection_count"
echo "WHERE connection_count > 2"
echo "RETURN labels(n)[0] as node_type, connection_count"
echo "ORDER BY connection_count DESC"

echo ""
echo "💰 成本優化查詢："
echo "----------------"
echo "// 孤兒 EBS 磁碟"
echo "MATCH (volume:EBSVolume)"
echo "WHERE NOT (volume)-[:ATTACHES_TO]->(:EC2Instance)"
echo "  AND volume.state = 'available'"
echo "RETURN volume.volumeid, volume.size, volume.volumetype"

echo ""
echo "📈 4. 實際分析結果"
echo "=================="
python -c "
import json
import glob

# 找到最新的分析結果
files = glob.glob('output/comprehensive_analysis_*.json')
if files:
    latest_file = max(files, key=lambda x: x.split('_')[-1].split('.')[0])
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 安全分析結果
    security = data['results']['security']['summary']
    print('🔒 安全分析結果：')
    print(f'  - 過度寬鬆規則: {security[\"permissive_rules_count\"]} 個')
    print(f'  - 未加密資源: {security[\"unencrypted_resources_count\"]} 個')
    print(f'  - 孤兒安全群組: {security[\"orphaned_security_groups_count\"]} 個')
    
    # 故障分析結果
    failure = data['results']['failure_impact']['summary']
    print('⚡ 故障分析結果：')
    print(f'  - 關鍵節點: {failure[\"critical_nodes_count\"]} 個')
    print(f'  - 單點故障: {failure[\"single_points_of_failure_count\"]} 個')
    
    # 成本優化結果
    cost = data['results']['cost_optimization']['summary']
    orphaned_ebs = cost['potential_savings']['orphaned_ebs_volumes']
    print('💰 成本優化結果：')
    print(f'  - 孤兒 EBS 磁碟: {orphaned_ebs[\"count\"]} 個')
    print(f'  - 總大小: {orphaned_ebs[\"total_size_gb\"]} GB')
    print(f'  - 預估月成本: \${orphaned_ebs[\"estimated_monthly_cost\"]}')
"

echo ""
echo "🎯 5. 圖形資料模型優勢"
echo "===================="
echo "✅ 直觀表達複雜關係"
echo "✅ 支援深度查詢分析"
echo "✅ 自動化問題檢測"
echo "✅ 提供具體優化建議"

echo ""
echo "📄 完整文件請查看："
echo "  - NODES_RELATIONSHIPS_QUERIES.md (詳細說明)"
echo "  - Report/final_report.pdf (完整報告)"
echo "  - DEMO_GUIDE.md (演示指南)"

echo ""
echo "🎉 演示完成！"
echo "============="
