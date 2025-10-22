"""
簡化的雲端基礎設施儀表板
基於 Flask 的輕量級 Web 儀表板 - 增強版
"""

import json
import os
from flask import Flask, render_template_string, jsonify
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class SimpleDashboard:
    """簡化的儀表板類別 (專業 UI 版本 + 詳細資料)"""
    
    def __init__(self, analysis_file: str = None):
        """
        初始化儀表板
        
        Args:
            analysis_file: 分析結果文件路徑
        """
        self.analysis_file = analysis_file
        self.analysis_data = None
        self.app = None
        
        # 載入分析數據
        self._load_analysis_data()
    
    def _load_analysis_data(self):
        """載入分析數據"""
        if self.analysis_file and os.path.exists(self.analysis_file):
            try:
                with open(self.analysis_file, 'r', encoding='utf-8') as f:
                    self.analysis_data = json.load(f)
                logger.info(f"成功載入分析數據: {self.analysis_file}")
            except Exception as e:
                logger.error(f"載入分析數據失敗: {e}")
                self.analysis_data = None
        else:
            # 尋找最新的分析文件
            output_dir = "output"
            if os.path.exists(output_dir):
                files = [f for f in os.listdir(output_dir) if f.startswith('comprehensive_analysis_') and f.endswith('.json')]
                if files:
                    latest_file = max(files, key=lambda x: os.path.getctime(os.path.join(output_dir, x)))
                    self.analysis_file = os.path.join(output_dir, latest_file)
                    # 遞歸調用以載入文件
                    self._load_analysis_data()
    
    def create_app(self) -> Flask:
        """創建 Flask 應用程式"""
        self.app = Flask(__name__)
        
        # 設定路由
        self.app.route('/')(self.index)
        self.app.route('/api/data')(self.api_data)
        self.app.route('/api/security')(self.api_security)
        self.app.route('/api/failure')(self.api_failure)
        self.app.route('/api/cost')(self.api_cost)
        
        return self.app
    
    def index(self):
        """主頁面"""
        return render_template_string(self._get_html_template())
    
    def api_data(self):
        """API: 獲取所有數據"""
        if not self.analysis_data:
            self._load_analysis_data() # 嘗試重新載入
            if not self.analysis_data:
                 return jsonify({"error": "沒有分析數據"}), 404
        
        return jsonify(self.analysis_data)
    
    def api_security(self):
        """API: 獲取安全分析數據"""
        if not self.analysis_data or 'results' not in self.analysis_data:
            return jsonify({"error": "沒有安全分析數據"}), 404
        
        security_data = self.analysis_data['results'].get('security', {})
        return jsonify(security_data)
    
    def api_failure(self):
        """API: 獲取故障分析數據"""
        if not self.analysis_data or 'results' not in self.analysis_data:
            return jsonify({"error": "沒有故障分析數據"}), 404
        
        failure_data = self.analysis_data['results'].get('failure_impact', {})
        return jsonify(failure_data)
    
    def api_cost(self):
        """API: 獲取成本分析數據"""
        if not self.analysis_data or 'results' not in self.analysis_data:
            return jsonify({"error": "沒有成本分析數據"}), 404
        
        cost_data = self.analysis_data['results'].get('cost_optimization', {})
        return jsonify(cost_data)
    
    def _get_html_template(self):
        """獲取 HTML 模板 (專業 UI 版本 + 詳細資料)"""
        return """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>雲端基礎設施分析儀表板</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" />
    
    <!-- vis-network 圖形視覺化庫 -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.9/vis-network.min.js"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.9/vis-network.min.css" rel="stylesheet" type="text/css" />
    <style>
        :root {
            --sidebar-bg: #2c3e50;
            --sidebar-text: #ecf0f1;
            --sidebar-active: #3498db;
            --main-bg: #f8f9fa;
            --card-bg: #ffffff;
            --text-color: #343a40;
            --text-muted: #6c757d;
            --border-color: #e9ecef;
            --shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            --primary: #3498db;
            --success: #2ecc71;
            --warning: #f39c12;
            --danger: #e74c3c;
        }
        
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Nunito', sans-serif;
            background-color: var(--main-bg);
            color: var(--text-color);
            display: flex;
        }

        .sidebar {
            width: 240px;
            background: var(--sidebar-bg);
            color: var(--sidebar-text);
            height: 100vh;
            position: fixed;
            left: 0;
            top: 0;
            padding: 20px;
            display: flex;
            flex-direction: column;
        }
        .sidebar-header {
            font-size: 1.5em;
            font-weight: 700;
            text-align: center;
            margin-bottom: 30px;
        }
        .sidebar-header i {
            margin-right: 10px;
        }
        .sidebar-nav {
            list-style: none;
        }
        .sidebar-nav li {
            margin-bottom: 10px;
        }
        .sidebar-nav a {
            color: var(--sidebar-text);
            text-decoration: none;
            display: block;
            padding: 12px 15px;
            border-radius: 6px;
            transition: background 0.2s;
            font-weight: 600;
        }
        .sidebar-nav a i {
            margin-right: 12px;
            width: 20px;
            text-align: center;
        }
        .sidebar-nav a:hover {
            background: rgba(255, 255, 255, 0.1);
        }
        .sidebar-nav a.active {
            background: var(--primary);
            color: white;
        }

        .main-content {
            margin-left: 240px;
            flex-grow: 1;
            padding: 30px;
            max-width: calc(100% - 240px);
        }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
        }
        .header h1 {
            font-size: 2.2em;
            font-weight: 700;
        }
        
        .refresh-btn {
            background: var(--primary);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            transition: background 0.2s;
        }
        .refresh-btn:hover {
            background: #2980b9;
        }
        .refresh-btn i {
            margin-right: 8px;
        }

        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 25px;
            margin-bottom: 30px;
        }

        .card {
            background: var(--card-bg);
            border-radius: 10px;
            box-shadow: var(--shadow);
            padding: 25px;
            display: flex;
            flex-direction: column;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .card:hover {
            transform: translateY(-3px);
            box-shadow: 0 6px 16px rgba(0, 0, 0, 0.08);
        }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 15px;
            border-bottom: 1px solid var(--border-color);
            margin-bottom: 15px;
        }
        .card-header h3 {
            margin: 0;
            font-size: 1.25em;
            font-weight: 700;
            display: flex;
            align-items: center;
        }
        .card-header h3 i {
            margin-right: 12px;
            font-size: 1.2em;
        }
        .icon-security { color: var(--danger); }
        .icon-failure { color: var(--warning); }
        .icon-cost { color: var(--success); }
        .icon-stats { color: var(--primary); }
        .icon-chart { color: #9b59b6; }
        .icon-graph { color: #e74c3c; }
        
        .status-badge {
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 700;
            color: white;
        }
        .status-success { background: var(--success); }
        .status-warning { background: var(--warning); }
        .status-danger { background: var(--danger); }
        .status-info { background: var(--primary); }
        .status-muted { background: var(--text-muted); }

        .card-body {
            flex-grow: 1;
        }

        .stat-item {
            display: flex;
            justify-content: space-between;
            margin: 12px 0;
            padding-bottom: 8px;
            border-bottom: 1px dashed var(--border-color);
        }
        .stat-item:last-child {
            border-bottom: none;
        }
        .stat-label {
            font-weight: 600;
            color: var(--text-muted);
        }
        .stat-value {
            font-weight: 700;
            color: var(--text-color);
        }

        .details-section {
            margin-top: 20px;
            padding-top: 15px;
            border-top: 2px solid var(--border-color);
        }
        .details-header {
            font-weight: 700;
            color: var(--text-color);
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            cursor: pointer;
            user-select: none;
            padding: 8px 0;
        }
        .details-header i {
            margin-right: 8px;
            transition: transform 0.2s;
        }
        .details-header.expanded i {
            transform: rotate(90deg);
        }
        .details-content {
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease;
        }
        .details-content.expanded {
            max-height: 1000px;
            overflow-y: auto; /* 允許垂直滾動 */
        }
        .detail-item {
            background: var(--main-bg);
            padding: 8px 12px;
            margin: 5px 0;
            border-radius: 6px;
            border-left: 3px solid var(--primary);
            font-size: 0.9em;
        }
        .detail-item.warning {
            border-left-color: var(--warning);
        }
        .detail-item.danger {
            border-left-color: var(--danger);
        }
        .detail-item.success {
            border-left-color: var(--success);
        }
        .detail-id {
            font-weight: 700;
            color: var(--text-color);
        }
        .detail-info {
            color: var(--text-muted);
            font-size: 0.85em;
            margin-top: 2px;
        }
        
        .chart-container {
            position: relative;
            height: 350px;
            margin-top: 20px;
        }
        
        .graph-controls {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }
        .btn-small {
            background: var(--primary);
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.85em;
            font-weight: 600;
            transition: background 0.2s;
        }
        .btn-small:hover {
            background: #2980b9;
        }
        .btn-small.active {
            background: var(--success);
        }
        
        .graph-container {
            position: relative;
            height: 500px;
            margin-top: 20px;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            background: var(--main-bg);
            overflow: hidden;
        }
        #graphVisualization {
            width: 100%;
            height: 100%;
            position: relative;
        }
        
        /* vis-network 工具提示樣式 */
        .vis-tooltip {
            position: absolute;
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 10px;
            box-shadow: var(--shadow);
            font-family: 'Nunito', sans-serif;
            font-size: 14px;
            color: var(--text-color);
            z-index: 100;
            max-width: 300px;
        }
        
        .graph-info {
            padding: 15px;
            background: var(--card-bg);
            border-bottom: 1px solid var(--border-color);
        }
        .graph-info h4 {
            margin: 0 0 10px 0;
            color: var(--text-color);
            font-size: 1.1em;
        }
        .graph-legend {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }
        .legend-item {
            display: flex;
            align-items: center;
            gap: 5px;
            font-size: 0.85em;
        }
        .legend-color {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
        }
        .graph-canvas {
            padding: 15px;
            height: calc(100% - 80px);
            overflow: auto;
        }

        .loading-spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid var(--primary);
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 50px auto;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .alert-message {
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
            font-weight: 600;
        }
        .alert-danger {
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
        }

    </style>
</head>
<body>

    <div class="sidebar">
        <h2 class="sidebar-header"><i class="fas fa-cloud"></i> Cloud Analyzer</h2>
        <ul class="sidebar-nav">
            <li><a href="#" class="active"><i class="fas fa-tachometer-alt"></i> Dashboard</a></li>
            <li><a href="#"><i class="fas fa-server"></i> Resources</a></li>
            <li><a href="#"><i class="fas fa-shield-alt"></i> Security</a></li>
            <li><a href="#"><i class="fas fa-dollar-sign"></i> Cost</a></li>
            <li><a href="#"><i class="fas fa-cogs"></i> Settings</a></li>
        </ul>
    </div>

    <div class="main-content">
        <div class="header">
            <h1>分析儀表板</h1>
            <button class="refresh-btn" onclick="loadData()">
                <i class="fas fa-sync-alt"></i> 重新載入數據
            </button>
        </div>
        
        <div class="dashboard-grid">
            <div class="card">
                <div class="card-header">
                    <h3><i class="fas fa-shield-alt icon-security"></i> 安全分析</h3>
                    <div id="security-status-badge" class="status-badge status-muted">...</div>
                </div>
                <div id="security-stats" class="card-body">
                    <div class="loading-spinner"></div>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <h3><i class="fas fa-bolt icon-failure"></i> 故障衝擊分析</h3>
                    <div id="failure-status-badge" class="status-badge status-muted">...</div>
                </div>
                <div id="failure-stats" class="card-body">
                    <div class="loading-spinner"></div>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <h3><i class="fas fa-coins icon-cost"></i> 成本優化分析</h3>
                    <div id="cost-status-badge" class="status-badge status-muted">...</div>
                </div>
                <div id="cost-stats" class="card-body">
                    <div class="loading-spinner"></div>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <h3><i class="fas fa-sitemap icon-stats"></i> 節點統計</h3>
                </div>
                <div id="node-stats" class="card-body">
                    <div class="loading-spinner"></div>
                </div>
            </div>
        </div>
        
               <div class="card">
                   <div class="card-header">
                       <h3><i class="fas fa-chart-pie icon-chart"></i> 分析結果圖表</h3>
                   </div>
                   <div class="chart-container">
                       <canvas id="analysisChart"></canvas>
                   </div>
               </div>
               
               <div class="card">
                   <div class="card-header">
                       <h3><i class="fas fa-project-diagram icon-graph"></i> 基礎設施圖形視覺化</h3>
                       <div class="graph-controls">
                           <button class="btn-small" onclick="loadGraphView('critical')">關鍵節點</button>
                           <button class="btn-small" onclick="loadGraphView('security')">安全風險</button>
                           <button class="btn-small" onclick="loadGraphView('cost')">成本優化</button>
                           <button class="btn-small active" onclick="loadGraphView('full')">完整圖形</button>
                       </div>
                   </div>
                   <div class="graph-container">
                       <div class="graph-info">
                           <h4 id="graph-title">完整基礎設施圖形</h4>
                           <div id="graph-legend" class="graph-legend"></div>
                       </div>
                       <div id="graphVisualization"></div>
                   </div>
               </div>
    </div>

    <script>
        let analysisData = null;
        let myChart = null; // 用於保存 Chart 實例
        let networkGraph = null; // 保存 vis-network 實例
        
        // 輔助函數：設置狀態徽章
        function setStatusBadge(elementId, text, type) {
            const badge = document.getElementById(elementId);
            if (badge) {
                badge.textContent = text;
                badge.className = 'status-badge ' + type;
            }
        }

        // 輔助函數：創建詳細資料區塊
        function createDetailsSection(title, items, type = 'primary') {
            if (!items || items.length === 0) {
                return '';
            }
            
            const sectionId = title.toLowerCase().replace(/\\s+/g, '-');
            const itemsHtml = items.map(item => {
                const itemClass = type === 'danger' ? 'danger' : type === 'warning' ? 'warning' : 'primary';
                return `
                    <div class="detail-item ${itemClass}">
                        <div class="detail-id">${item.id || item.name || 'Unknown'}</div>
                        <div class="detail-info">${item.info || item.description || ''}</div>
                    </div>
                `;
            }).join('');
            
            return `
                <div class="details-section">
                    <div class="details-header" onclick="toggleDetails('${sectionId}')">
                        <i class="fas fa-chevron-right"></i>
                        ${title} (${items.length} 項)
                    </div>
                    <div id="${sectionId}" class="details-content">
                        ${itemsHtml}
                    </div>
                </div>
            `;
        }

        // 切換詳細資料顯示
        function toggleDetails(sectionId) {
            const content = document.getElementById(sectionId);
            const header = content.previousElementSibling;
            
            if (content.classList.contains('expanded')) {
                content.classList.remove('expanded');
                header.classList.remove('expanded');
            } else {
                content.classList.add('expanded');
                header.classList.add('expanded');
            }
        }
        
        // 計算實例成本
        function getInstanceCost(instanceType) {
            const costMap = {
                't3.micro': 8.5,
                't3.small': 17.0,
                't3.medium': 34.0,
                't3.large': 68.0,
                't3.xlarge': 136.0,
                'm5.large': 96.0,
                'm5.xlarge': 192.0,
                'm5.2xlarge': 384.0,
                'c5.large': 77.0,
                'c5.xlarge': 154.0,
                'c5.2xlarge': 308.0,
                'r5.large': 126.0,
                'r5.xlarge': 252.0,
                'r5.2xlarge': 504.0
            };
            return costMap[instanceType] || 50.0; // 預設成本
        }

        async function loadData() {
            // 在加載前顯示 spinner
            document.getElementById('security-stats').innerHTML = '<div class="loading-spinner"></div>';
            document.getElementById('failure-stats').innerHTML = '<div class="loading-spinner"></div>';
            document.getElementById('cost-stats').innerHTML = '<div class="loading-spinner"></div>';
            document.getElementById('node-stats').innerHTML = '<div class="loading-spinner"></div>';
            setStatusBadge('security-status-badge', '...', 'status-muted');
            setStatusBadge('failure-status-badge', '...', 'status-muted');
            setStatusBadge('cost-status-badge', '...', 'status-muted');

            try {
                const response = await fetch('/api/data');
                analysisData = await response.json();
                
                if (analysisData.error) {
                    showError('載入數據失敗: ' + analysisData.error);
                    return;
                }
                
                updateSecurityStats();
                updateFailureStats();
                updateCostStats();
                updateNodeStats();
                updateChart();
                
                // 生成圖形數據並載入完整圖形
                if (!analysisData.graph_data) {
                    console.log('Generating graph data...');
                    analysisData.graph_data = generateGraphData(analysisData);
                    console.log('Graph data generated:', analysisData.graph_data);
                }
                loadGraphView('full');
                
            } catch (error) {
                showError('載入數據時發生錯誤: ' + error.message);
            }
        }
        
        function updateSecurityStats() {
            const container = document.getElementById('security-stats');
            if (!analysisData || !analysisData.results || !analysisData.results.security) {
                container.innerHTML = '<div class="stat-item"><span class="stat-label">沒有安全分析數據</span></div>';
                setStatusBadge('security-status-badge', 'N/A', 'status-muted');
                return;
            }
            
            const security = analysisData.results.security;
            const summary = security.summary || {};
            const exposedCount = summary.exposed_services_count || 0;
            
            // 準備詳細資料
            const permissiveRules = security.permissive_rules || [];
            const unencryptedVolumes = security.unencrypted_volumes || [];
            const orphanedSecurityGroups = security.orphaned_security_groups || [];
            
            container.innerHTML = `
                <div class="stat-item">
                    <span class="stat-label">暴露服務:</span>
                    <span class="stat-value">${exposedCount}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">過度寬鬆規則:</span>
                    <span class="stat-value">${summary.permissive_rules_count || 0}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">未加密資源:</span>
                    <span class="stat-value">${summary.unencrypted_resources_count || 0}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">孤兒安全群組:</span>
                    <span class="stat-value">${summary.orphaned_security_groups_count || 0}</span>
                </div>
                
                ${createDetailsSection('過度寬鬆規則', permissiveRules.map(rule => ({
                    id: rule.SecurityGroupID || rule.RuleID,
                    info: `${rule.SecurityGroupName || ''} - ${rule.Protocol || ''}:${rule.PortRange || ''} (${rule.SourceCIDR || ''})`
                })), 'danger')}
                
                ${createDetailsSection('未加密磁碟', unencryptedVolumes.map(vol => ({
                    id: vol.VolumeID || vol.volumeid,
                    info: `${vol.Region || vol.region || ''} - ${vol.Size || vol.size || 0}GB - ${vol.State || vol.state || ''}`
                })), 'warning')}
                
                ${createDetailsSection('孤兒安全群組', orphanedSecurityGroups.map(sg => ({
                    id: sg.SecurityGroupID || sg.groupid,
                    info: `${sg.SecurityGroupName || sg.name || ''} - ${sg.VPCID || sg.vpcid || ''}`
                })), 'warning')}
            `;
            
            if (exposedCount > 0 || (summary.permissive_rules_count || 0) > 0) {
                setStatusBadge('security-status-badge', '⚠️ Risk', 'status-danger');
            } else {
                setStatusBadge('security-status-badge', '✅ OK', 'status-success');
            }
        }
        
        function updateFailureStats() {
            const container = document.getElementById('failure-stats');
            if (!analysisData || !analysisData.results || !analysisData.results.failure_impact) {
                container.innerHTML = '<div class="stat-item"><span class="stat-label">沒有故障分析數據</span></div>';
                setStatusBadge('failure-status-badge', 'N/A', 'status-muted');
                return;
            }
            
            const failure = analysisData.results.failure_impact;
            const summary = failure.summary || {};
            const spofCount = summary.single_points_of_failure_count || 0;
            
            // 準備詳細資料
            const criticalNodes = failure.critical_nodes || [];
            const singlePointsOfFailure = failure.single_points_of_failure || [];
            const networkRedundancy = failure.network_redundancy_analysis || [];
            
            container.innerHTML = `
                <div class="stat-item">
                    <span class="stat-label">關鍵節點:</span>
                    <span class="stat-value">${summary.critical_nodes_count || 0}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">單點故障:</span>
                    <span class="stat-value">${spofCount}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">VPC 數量:</span>
                    <span class="stat-value">${networkRedundancy.length}</span>
                </div>
                
                ${createDetailsSection('關鍵節點', criticalNodes.map(node => {
                    const nodeData = node.node || node;
                    return {
                        id: nodeData.name || nodeData.groupid || nodeData.instanceid || nodeData.volumeid || 'Unknown',
                        info: `${nodeData.groupid ? 'SecurityGroup' : nodeData.instanceid ? 'EC2Instance' : nodeData.volumeid ? 'EBSVolume' : 'Unknown'} - 連接數: ${node.connection_count || node.ConnectionCount || 0}`
                    };
                }), 'warning')}
                
                ${createDetailsSection('單點故障', singlePointsOfFailure.map(node => {
                    const nodeData = node.node || node;
                    return {
                        id: nodeData.name || nodeData.groupid || nodeData.instanceid || nodeData.volumeid || 'Unknown',
                        info: `${nodeData.groupid ? 'SecurityGroup' : nodeData.instanceid ? 'EC2Instance' : nodeData.volumeid ? 'EBSVolume' : 'Unknown'} - 連接數: ${node.connection_count || node.ConnectionCount || 0}`
                    };
                }), 'danger')}
                
                ${createDetailsSection('網路冗餘分析', networkRedundancy.map(vpc => ({
                    id: vpc.VpcId || vpc.vpcid || 'Unknown',
                    info: `子網路: ${vpc.SubnetCount || 0} - 實例: ${vpc.InstanceCount || 0}`
                })), 'primary')}
            `;
            
            if (spofCount > 0) {
                setStatusBadge('failure-status-badge', '⚠️ Warning', 'status-warning');
            } else {
                setStatusBadge('failure-status-badge', '✅ OK', 'status-success');
            }
        }
        
        function updateCostStats() {
            const container = document.getElementById('cost-stats');
            if (!analysisData || !analysisData.results || !analysisData.results.cost_optimization) {
                container.innerHTML = '<div class="stat-item"><span class="stat-label">沒有成本分析數據</span></div>';
                setStatusBadge('cost-status-badge', 'N/A', 'status-muted');
                return;
            }
            
            const cost = analysisData.results.cost_optimization;
            const summary = cost.summary || {};
            const savings = summary.total_potential_savings || 0;
            
            // 準備詳細資料
            const orphanedVolumes = cost.orphaned_ebs_volumes || [];
            const unusedSecurityGroups = cost.unused_security_groups || [];
            const stoppedInstances = cost.stopped_instances || [];
            
            // 獲取潛在節省數據
            const potentialSavings = summary.potential_savings || {};
            const orphanedVolumesSavings = potentialSavings.orphaned_ebs_volumes || {};
            const unusedSecurityGroupsSavings = potentialSavings.unused_security_groups || {};
            const stoppedInstancesSavings = potentialSavings.stopped_instances || {};
            
            // 計算總潛在節省
            const totalSavings = (orphanedVolumesSavings.estimated_monthly_cost || 0) + 
                                (unusedSecurityGroupsSavings.potential_savings || 0) + 
                                (stoppedInstancesSavings.potential_savings || 0);
            
            container.innerHTML = `
                <div class="stat-item">
                    <span class="stat-label">孤兒 EBS 磁碟:</span>
                    <span class="stat-value">${orphanedVolumesSavings.count || 0}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">未使用安全群組:</span>
                    <span class="stat-value">${unusedSecurityGroupsSavings.count || 0}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">停止的實例:</span>
                    <span class="stat-value">${stoppedInstancesSavings.count || 0}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">潛在節省:</span>
                    <span class="stat-value">$${totalSavings.toFixed(2)} /月</span>
                </div>
                
                ${createDetailsSection('孤兒 EBS 磁碟', orphanedVolumes.map(vol => ({
                    id: vol.VolumeID || vol.volumeid,
                    info: `${vol.Region || vol.region || ''} - ${vol.Size || vol.size || 0}GB - ${vol.State || vol.state || ''} - 預估成本: $${((vol.Size || vol.size || 0) * 0.1).toFixed(2)}/月`
                })), 'warning')}
                
                ${createDetailsSection('未使用安全群組', unusedSecurityGroups.map(sg => {
                    const sgData = sg.security_group || sg;
                    return {
                        id: sgData.groupid || sgData.SecurityGroupID || 'Unknown',
                        info: `${sgData.name || sgData.SecurityGroupName || ''} - ${sgData.vpcid || sgData.VPCID || ''} - 預估節省: $0.10/月`
                    };
                }), 'warning')}
                
                ${createDetailsSection('停止的實例', stoppedInstances.map(inst => {
                    const instType = inst.InstanceType || inst.instancetype || '';
                    const estimatedCost = getInstanceCost(instType);
                    return {
                        id: inst.InstanceID || inst.instanceid,
                        info: `${inst.InstanceName || inst.name || ''} - ${instType} - ${inst.Region || inst.region || ''} - 預估節省: $${estimatedCost}/月`
                    };
                }), 'warning')}
                
                ${createDetailsSection('成本分析摘要', [{
                    id: '總潛在節省',
                    info: `EBS 磁碟: $${(orphanedVolumesSavings.estimated_monthly_cost || 0).toFixed(2)}/月 | 安全群組: $${(unusedSecurityGroupsSavings.potential_savings || 0).toFixed(2)}/月 | 停止實例: $${(stoppedInstancesSavings.potential_savings || 0).toFixed(2)}/月`
                }], 'success')}
            `;
            
            if (totalSavings > 0) {
                setStatusBadge('cost-status-badge', '💰 Optimize', 'status-info');
            } else {
                setStatusBadge('cost-status-badge', '✅ OK', 'status-success');
            }
        }
        
        function updateNodeStats() {
            const container = document.getElementById('node-stats');
            if (!analysisData || !analysisData.results || !analysisData.results.security) {
                container.innerHTML = '<div class="stat-item"><span class="stat-label">沒有節點統計數據</span></div>';
                return;
            }
            
            const nodeStats = analysisData.results.security.summary?.node_statistics || {};
            
            let html = '';
            const entries = Object.entries(nodeStats);
            
            if (entries.length === 0) {
                 container.innerHTML = '<div class="stat-item"><span class="stat-label">沒有節點統計數據</span></div>';
                 return;
            }
            
            for (const [nodeType, count] of entries) {
                html += `
                    <div class="stat-item">
                        <span class="stat-label">${nodeType}:</span>
                        <span class="stat-value">${count}</span>
                    </div>
                `;
            }
            
            container.innerHTML = html;
        }
        
        function updateChart() {
            const ctx = document.getElementById('analysisChart').getContext('2d');
            
            if (!analysisData || !analysisData.results) {
                return;
            }
            
            // 獲取樣式變量
            const style = getComputedStyle(document.documentElement);
            const colorDanger = style.getPropertyValue('--danger');
            const colorWarning = style.getPropertyValue('--warning');
            const colorSuccess = style.getPropertyValue('--success'); // 用於成本
            const colorPrimary = style.getPropertyValue('--primary');
            
            const security = analysisData.results.security?.summary || {};
            const failure = analysisData.results.failure_impact?.summary || {};
            const cost = analysisData.results.cost_optimization?.summary || {};
            
            const data = {
                labels: ['安全問題', '故障風險', '成本浪費'],
                datasets: [{
                    data: [
                        (security.permissive_rules_count || 0) + (security.unencrypted_resources_count || 0) + (security.exposed_services_count || 0),
                        (failure.single_points_of_failure_count || 0),
                        (cost.orphaned_ebs_volumes_count || 0) + (cost.unused_security_groups_count || 0)
                    ],
                    backgroundColor: [
                        colorDanger,
                        colorWarning,
                        colorPrimary 
                    ],
                    borderColor: '#ffffff',
                    borderWidth: 2
                }]
            };

            // 如果圖表已存在，先銷毀
            if (myChart) {
                myChart.destroy();
            }
            
            myChart = new Chart(ctx, {
                type: 'doughnut',
                data: data,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                font: {
                                    family: "'Nunito', sans-serif",
                                    size: 14
                                }
                            }
                        },
                        title: {
                            display: true,
                            text: '分析結果分布',
                            font: {
                                family: "'Nunito', sans-serif",
                                size: 18,
                                weight: '600'
                            },
                            padding: {
                                top: 10,
                                bottom: 20
                            }
                        },
                        tooltip: {
                            titleFont: {
                                family: "'Nunito', sans-serif",
                            },
                            bodyFont: {
                                family: "'Nunito', sans-serif",
                            }
                        }
                    },
                    cutout: '60%'
                }
            });
        }
        
        function showError(message) {
            // 在第一個卡片顯示錯誤
            const container = document.getElementById('security-stats');
            container.innerHTML = `<div class="alert-message alert-danger">${message}</div>`;
            // 隱藏其他 spinner
            document.getElementById('failure-stats').innerHTML = '';
            document.getElementById('cost-stats').innerHTML = '';
            document.getElementById('node-stats').innerHTML = '';
        }
        
        // 生成圖形數據
        function generateGraphData(data) {
            const nodes = [];
            const edges = [];
            
            // 從分析結果中獲取節點信息
            const nodeStats = data.results?.security?.summary?.node_statistics || {};
            const criticalNodes = data.results?.failure_impact?.critical_nodes || [];
            const spofNodes = data.results?.failure_impact?.single_points_of_failure || [];
            const permissiveRules = data.results?.security?.permissive_rules || [];
            const orphanedVolumes = data.results?.cost_optimization?.orphaned_volumes || [];
            
            console.log('Node stats:', nodeStats);
            console.log('Critical nodes:', criticalNodes.length);
            console.log('SPOF nodes:', spofNodes.length);
            
            // 創建 VPC 節點
            nodes.push({
                id: 'vpc-main',
                label: 'Main VPC',
                group: 'VPC',
                title: '主要 VPC<br>CIDR: 10.0.0.0/16<br>Region: us-east-1'
            });
            
            // 創建子網路節點
            for (let i = 1; i <= 3; i++) {
                nodes.push({
                    id: `subnet-${i}`,
                    label: `Subnet-${i}`,
                    group: 'Subnet',
                    title: `子網路 ${i}<br>AZ: us-east-1${String.fromCharCode(96+i)}<br>CIDR: 10.0.${i}.0/24`
                });
                edges.push({ from: 'vpc-main', to: `subnet-${i}` });
            }
            
            // 創建 EC2 實例節點
            const ec2Count = nodeStats.EC2Instance || 0;
            for (let i = 1; i <= Math.min(ec2Count, 8); i++) {
                // 檢查是否為關鍵節點或單點故障
                const isCritical = criticalNodes.some(n => {
                    const nodeData = n.node || n;
                    return nodeData.instanceid || nodeData.name || nodeData.groupid;
                });
                const isSpof = spofNodes.some(n => {
                    const nodeData = n.node || n;
                    return nodeData.instanceid || nodeData.name || nodeData.groupid;
                });
                
                nodes.push({
                    id: `ec2-${i}`,
                    label: `EC2-${i}`,
                    group: 'EC2Instance',
                    title: `EC2 實例 ${i}<br>Type: t3.micro<br>State: running`,
                    is_critical: isCritical,
                    is_spof: isSpof,
                    security_risk: 'none',
                    cost_waste: 0
                });
                
                // 連接到子網路
                edges.push({ from: `subnet-${((i-1) % 3) + 1}`, to: `ec2-${i}` });
            }
            
            // 創建安全群組節點
            const sgCount = nodeStats.SecurityGroup || 0;
            for (let i = 1; i <= Math.min(sgCount, 5); i++) {
                const hasRisk = permissiveRules.length > 0; // 如果有過度寬鬆規則，標記為高風險
                
                nodes.push({
                    id: `sg-${i}`,
                    label: `SG-${i}`,
                    group: 'SecurityGroup',
                    title: `安全群組 ${i}<br>Description: Web servers`,
                    security_risk: hasRisk ? 'high' : 'none'
                });
                
                // 連接到 EC2 實例
                if (i <= 3) {
                    edges.push({ from: `ec2-${i}`, to: `sg-${i}` });
                }
            }
            
            // 創建 EBS 磁碟節點
            const volumeCount = nodeStats.EBSVolume || 0;
            for (let i = 1; i <= Math.min(volumeCount, 6); i++) {
                const isOrphaned = orphanedVolumes.length > 0; // 如果有孤兒磁碟，標記為成本浪費
                
                nodes.push({
                    id: `vol-${i}`,
                    label: `Vol-${i}`,
                    group: 'EBSVolume',
                    title: `EBS 磁碟 ${i}<br>Size: 100GB<br>Type: gp3`,
                    cost_waste: isOrphaned ? 10.0 : 0
                });
                
                // 連接到 EC2 實例
                if (i <= 3) {
                    edges.push({ from: `vol-${i}`, to: `ec2-${i}` });
                }
            }
            
            console.log('Generated nodes:', nodes.length);
            console.log('Generated edges:', edges.length);
            
            return { nodes, edges };
        }
        
        // 圖形視覺化功能
        function loadGraphView(type) {
            console.log('Loading graph view:', type);
            const container = document.getElementById('graphVisualization');
            container.innerHTML = '<div class="loading-spinner"></div>';
            
            // 更新按鈕狀態
            document.querySelectorAll('.btn-small').forEach(btn => btn.classList.remove('active'));
            if (event && event.target) {
                event.target.classList.add('active');
            } else {
                // 如果是代碼調用，手動查找按鈕
                const button = Array.from(document.querySelectorAll('.btn-small')).find(btn => 
                    btn.onclick && btn.onclick.toString().includes(`'${type}'`));
                if (button) button.classList.add('active');
            }
            
            console.log('Analysis data:', analysisData);
            console.log('Graph data:', analysisData?.graph_data);
            
            if (!analysisData || !analysisData.graph_data) {
                container.innerHTML = '<div class="alert-message alert-danger">沒有圖形數據</div>';
                return;
            }

            // 根據類型生成不同的圖形視覺化
            setTimeout(() => {
                generateGraphVisualization(type);
            }, 100);
        }
        
        function generateGraphVisualization(type) {
            const allNodes = analysisData.graph_data.nodes;
            const allEdges = analysisData.graph_data.edges;
            
            let filteredNodes = [];
            let title = '';

            switch(type) {
                case 'critical':
                    title = '關鍵節點與單點故障';
                    filteredNodes = allNodes.filter(n => n.is_critical || n.is_spof);
                    break;
                case 'security':
                    title = '安全風險分析';
                    filteredNodes = allNodes.filter(n => n.security_risk === 'high');
                    break;
                case 'cost':
                    title = '成本優化分析';
                    filteredNodes = allNodes.filter(n => n.cost_waste > 0);
                    break;
                case 'full':
                default:
                    title = '完整基礎設施圖形';
                    renderGraph(allNodes, allEdges, title);
                    return;
            }

            // 對於過濾視圖，我們顯示目標節點 + 它們的一級鄰居
            const primaryNodeIds = new Set(filteredNodes.map(n => n.id));
            const neighborNodeIds = new Set();
            
            const filteredEdges = allEdges.filter(edge => {
                const fromPrimary = primaryNodeIds.has(edge.from);
                const toPrimary = primaryNodeIds.has(edge.to);
                
                if (fromPrimary || toPrimary) {
                    if (fromPrimary && !toPrimary) neighborNodeIds.add(edge.to);
                    if (toPrimary && !fromPrimary) neighborNodeIds.add(edge.from);
                    return true;
                }
                return false;
            });

            const neighborNodes = allNodes.filter(n => neighborNodeIds.has(n.id) && !primaryNodeIds.has(n.id));
            const finalNodes = [...filteredNodes, ...neighborNodes];

            renderGraph(finalNodes, filteredEdges, title);
        }
        
        function renderGraph(nodes, edges, title) {
            const container = document.getElementById('graphVisualization');
            
            if (nodes.length === 0) {
                container.innerHTML = '<div class="alert-message alert-info" style="margin: 20px;">沒有可視覺化的數據</div>';
                document.getElementById('graph-title').textContent = title;
                document.getElementById('graph-legend').innerHTML = '';
                return;
            }
            
            // 更新標題和圖例
            document.getElementById('graph-title').textContent = `${title} (${nodes.length} 個節點)`;
            generateLegend(nodes);

            const data = {
                nodes: new vis.DataSet(nodes),
                edges: new vis.DataSet(edges)
            };
            
            const options = getVisNetworkOptions();
            
            // 銷毀舊實例
            if (networkGraph) {
                networkGraph.destroy();
            }
            
            networkGraph = new vis.Network(container, data, options);
            
            // 添加工具提示
            networkGraph.on("hoverNode", function (params) {
                if (params.node !== undefined) {
                    const nodeId = params.node;
                    const node = data.nodes.get(nodeId);
                    if (node && node.title) {
                        const tooltip = document.createElement("div");
                        tooltip.className = "vis-tooltip";
                        tooltip.innerHTML = node.title;
                        document.body.appendChild(tooltip);
                        
                        // 定位
                        const canvas = container.getElementsByTagName("canvas")[0];
                        const rect = canvas.getBoundingClientRect();
                        const pos = networkGraph.getPositions(nodeId)[nodeId];
                        const domPos = networkGraph.canvasToDOM({ x: pos.x, y: pos.y });
                        
                        tooltip.style.left = rect.left + domPos.x + 20 + "px";
                        tooltip.style.top = rect.top + domPos.y - 10 + "px";
                    }
                }
            });

            networkGraph.on("blurNode", function () {
                const tooltips = document.getElementsByClassName("vis-tooltip");
                while (tooltips.length > 0) {
                    tooltips[0].parentNode.removeChild(tooltips[0]);
                }
            });
        }
        
        function getVisNetworkOptions() {
            const style = getComputedStyle(document.documentElement);
            
            // 定義節點組 (類型)
            const groups = {
                VPC: {
                    shape: 'icon',
                    icon: { face: 'FontAwesome', code: '\\uf0c2', size: 50, color: style.getPropertyValue('--primary') }
                },
                Subnet: {
                    shape: 'icon',
                    icon: { face: 'FontAwesome', code: '\\uf1e0', size: 40, color: style.getPropertyValue('--success') }
                },
                EC2Instance: {
                    shape: 'icon',
                    icon: { face: 'FontAwesome', code: '\\uf233', size: 50, color: style.getPropertyValue('--text-color') }
                },
                SecurityGroup: {
                    shape: 'icon',
                    icon: { face: 'FontAwesome', code: '\\uf3ed', size: 40, color: style.getPropertyValue('--danger') }
                },
                EBSVolume: {
                    shape: 'icon',
                    icon: { face: 'FontAwesome', code: '\\uf0a0', size: 30, color: style.getPropertyValue('--warning') }
                }
            };

            return {
                autoResize: true,
                nodes: {
                    font: {
                        family: 'Nunito',
                        size: 14,
                        color: style.getPropertyValue('--text-color')
                    },
                    borderWidth: 2,
                    shadow: true
                },
                edges: {
                    width: 2,
                    arrows: {
                        to: { enabled: true, scaleFactor: 0.5 }
                    },
                    color: {
                        color: '#aaa',
                        highlight: style.getPropertyValue('--primary'),
                        hover: style.getPropertyValue('--primary')
                    },
                    smooth: {
                        type: 'cubicBezier',
                        forceDirection: 'vertical',
                        roundness: 0.4
                    }
                },
                physics: {
                    enabled: true,
                    solver: 'forceAtlas2Based',
                    forceAtlas2Based: {
                        gravitationalConstant: -50,
                        centralGravity: 0.01,
                        springLength: 100,
                        springConstant: 0.08,
                        avoidOverlap: 0.5
                    },
                    stabilization: {
                        iterations: 200,
                        fit: true
                    }
                },
                interaction: {
                    dragNodes: true,
                    dragView: true,
                    hover: true,
                    zoomView: true,
                    tooltipDelay: 300
                },
                groups: groups
            };
        }

        function generateLegend(nodes) {
            const legendContainer = document.getElementById('graph-legend');
            const options = getVisNetworkOptions();
            const groups = options.groups;
            
            const usedGroups = new Set(nodes.map(n => n.group));
            
            let html = '';
            Object.entries(groups).forEach(([groupName, groupOptions]) => {
                if (usedGroups.has(groupName)) {
                    html += `
                        <div class="legend-item">
                            <i class="${groupOptions.icon.face === 'FontAwesome' ? 'fas' : ''} ${groupOptions.icon.code.replace('\\f', 'fa-')}" 
                               style="color: ${groupOptions.icon.color}"></i>
                            <span>${groupName}</span>
                        </div>
                    `;
                }
            });
            
            // 處理 FontAwesome 5/6 的 code -> class 轉換
            html = html.replace('fa-233', 'fa-server')
                       .replace('fa-0c2', 'fa-cloud')
                       .replace('fa-1e0', 'fa-sitemap')
                       .replace('fa-3ed', 'fa-shield-alt')
                       .replace('fa-0a0', 'fa-hdd');
            
            legendContainer.innerHTML = html;
        }
        
        // 頁面載入時自動載入數據
        document.addEventListener('DOMContentLoaded', loadData);
    </script>
</body>
</html>
        """
    
    def run(self, host='127.0.0.1', port=8050, debug=False):
        """運行儀表板"""
        if not self.app:
            self.create_app()
        
        logger.info(f"啟動儀表板: http://{host}:{port}")
        self.app.run(host=host, port=port, debug=debug)