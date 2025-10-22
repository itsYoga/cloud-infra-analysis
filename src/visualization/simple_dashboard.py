"""
簡化的雲端基礎設施儀表板
基於 Flask 的輕量級 Web 儀表板
"""

import json
import os
from flask import Flask, render_template_string, jsonify
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class SimpleDashboard:
    """簡化的儀表板類別"""
    
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
        """獲取 HTML 模板"""
        return """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>雲端基礎設施分析儀表板</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
        }
        .header p {
            margin: 10px 0 0 0;
            font-size: 1.2em;
            opacity: 0.9;
        }
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: transform 0.2s;
        }
        .card:hover {
            transform: translateY(-2px);
        }
        .card h3 {
            margin-top: 0;
            color: #333;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }
        .stat-item {
            display: flex;
            justify-content: space-between;
            margin: 10px 0;
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }
        .stat-label {
            font-weight: 500;
            color: #666;
        }
        .stat-value {
            font-weight: bold;
            color: #333;
        }
        .chart-container {
            position: relative;
            height: 300px;
            margin: 20px 0;
        }
        .alert {
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
        }
        .alert-warning {
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            color: #856404;
        }
        .alert-danger {
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
        }
        .alert-success {
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
        }
        .loading {
            text-align: center;
            padding: 50px;
            color: #666;
        }
        .refresh-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            margin: 10px 0;
        }
        .refresh-btn:hover {
            background: #5a6fd8;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 雲端基礎設施分析儀表板</h1>
            <p>基於 Neo4j 圖形資料庫的智能分析平台</p>
        </div>
        
        <div class="dashboard-grid">
            <!-- 安全分析卡片 -->
            <div class="card">
                <h3>🔒 安全分析</h3>
                <div id="security-stats">
                    <div class="loading">載入中...</div>
                </div>
            </div>
            
            <!-- 故障分析卡片 -->
            <div class="card">
                <h3>⚡ 故障衝擊分析</h3>
                <div id="failure-stats">
                    <div class="loading">載入中...</div>
                </div>
            </div>
            
            <!-- 成本優化卡片 -->
            <div class="card">
                <h3>💰 成本優化分析</h3>
                <div id="cost-stats">
                    <div class="loading">載入中...</div>
                </div>
            </div>
            
            <!-- 節點統計卡片 -->
            <div class="card">
                <h3>📊 節點統計</h3>
                <div id="node-stats">
                    <div class="loading">載入中...</div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h3>📈 分析結果圖表</h3>
            <button class="refresh-btn" onclick="loadData()">🔄 重新載入數據</button>
            <div class="chart-container">
                <canvas id="analysisChart"></canvas>
            </div>
        </div>
    </div>

    <script>
        let analysisData = null;
        
        async function loadData() {
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
                
            } catch (error) {
                showError('載入數據時發生錯誤: ' + error.message);
            }
        }
        
        function updateSecurityStats() {
            const container = document.getElementById('security-stats');
            if (!analysisData || !analysisData.results || !analysisData.results.security) {
                container.innerHTML = '<div class="alert alert-warning">沒有安全分析數據</div>';
                return;
            }
            
            const security = analysisData.results.security;
            const summary = security.summary || {};
            
            container.innerHTML = `
                <div class="stat-item">
                    <span class="stat-label">暴露服務:</span>
                    <span class="stat-value">${summary.exposed_services_count || 0}</span>
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
                ${summary.exposed_services_count > 0 ? '<div class="alert alert-danger">⚠️ 發現安全風險！</div>' : '<div class="alert alert-success">✅ 安全狀況良好</div>'}
            `;
        }
        
        function updateFailureStats() {
            const container = document.getElementById('failure-stats');
            if (!analysisData || !analysisData.results || !analysisData.results.failure_impact) {
                container.innerHTML = '<div class="alert alert-warning">沒有故障分析數據</div>';
                return;
            }
            
            const failure = analysisData.results.failure_impact;
            const summary = failure.summary || {};
            
            container.innerHTML = `
                <div class="stat-item">
                    <span class="stat-label">關鍵節點:</span>
                    <span class="stat-value">${summary.critical_nodes_count || 0}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">單點故障:</span>
                    <span class="stat-value">${summary.single_points_of_failure_count || 0}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">VPC 數量:</span>
                    <span class="stat-value">${summary.network_redundancy_analysis ? summary.network_redundancy_analysis.length : 0}</span>
                </div>
                ${(summary.single_points_of_failure_count || 0) > 0 ? '<div class="alert alert-warning">⚠️ 發現單點故障風險</div>' : '<div class="alert alert-success">✅ 網路冗餘性良好</div>'}
            `;
        }
        
        function updateCostStats() {
            const container = document.getElementById('cost-stats');
            if (!analysisData || !analysisData.results || !analysisData.results.cost_optimization) {
                container.innerHTML = '<div class="alert alert-warning">沒有成本分析數據</div>';
                return;
            }
            
            const cost = analysisData.results.cost_optimization;
            const summary = cost.summary || {};
            
            container.innerHTML = `
                <div class="stat-item">
                    <span class="stat-label">孤兒 EBS 磁碟:</span>
                    <span class="stat-value">${summary.orphaned_ebs_volumes_count || 0}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">未使用安全群組:</span>
                    <span class="stat-value">${summary.unused_security_groups_count || 0}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">停止的實例:</span>
                    <span class="stat-value">${summary.stopped_instances_count || 0}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">潛在節省:</span>
                    <span class="stat-value">$${summary.total_potential_savings || 0}/月</span>
                </div>
                ${(summary.total_potential_savings || 0) > 0 ? '<div class="alert alert-warning">💰 發現成本優化機會</div>' : '<div class="alert alert-success">✅ 成本控制良好</div>'}
            `;
        }
        
        function updateNodeStats() {
            const container = document.getElementById('node-stats');
            if (!analysisData || !analysisData.results || !analysisData.results.security) {
                container.innerHTML = '<div class="alert alert-warning">沒有節點統計數據</div>';
                return;
            }
            
            const nodeStats = analysisData.results.security.summary?.node_statistics || {};
            
            let html = '';
            for (const [nodeType, count] of Object.entries(nodeStats)) {
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
            
            const security = analysisData.results.security?.summary || {};
            const failure = analysisData.results.failure_impact?.summary || {};
            const cost = analysisData.results.cost_optimization?.summary || {};
            
            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['安全問題', '故障風險', '成本浪費'],
                    datasets: [{
                        data: [
                            (security.permissive_rules_count || 0) + (security.unencrypted_resources_count || 0),
                            (failure.single_points_of_failure_count || 0),
                            (cost.orphaned_ebs_volumes_count || 0) + (cost.unused_security_groups_count || 0)
                        ],
                        backgroundColor: [
                            '#ff6384',
                            '#ff9f40',
                            '#4bc0c0'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: '分析結果分布'
                        }
                    }
                }
            });
        }
        
        function showError(message) {
            const container = document.getElementById('security-stats');
            container.innerHTML = `<div class="alert alert-danger">${message}</div>`;
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
