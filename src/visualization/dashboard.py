"""
雲端基礎設施視覺化儀表板

本模組提供基於 Dash 的互動式視覺化儀表板，
支援圖形網路視覺化、統計圖表和即時分析。
"""

import dash
from dash import dcc, html, Input, Output, callback_context
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import json
from typing import Dict, List, Any, Optional
from neo4j import GraphDatabase
import networkx as nx
from loguru import logger


class CloudInfrastructureDashboard:
    """雲端基礎設施儀表板"""
    
    def __init__(self, neo4j_uri: str, neo4j_username: str, neo4j_password: str):
        """
        初始化儀表板
        
        Args:
            neo4j_uri: Neo4j 連接 URI
            neo4j_username: 使用者名稱
            neo4j_password: 密碼
        """
        self.neo4j_uri = neo4j_uri
        self.neo4j_username = neo4j_username
        self.neo4j_password = neo4j_password
        self.driver = None
        self.app = None
        
    def connect_neo4j(self) -> bool:
        """連接到 Neo4j 資料庫"""
        try:
            self.driver = GraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.neo4j_username, self.neo4j_password)
            )
            
            # 測試連接
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                result.single()
            
            logger.info("成功連接到 Neo4j")
            return True
            
        except Exception as e:
            logger.error(f"連接 Neo4j 失敗: {e}")
            return False
    
    def create_app(self) -> dash.Dash:
        """創建 Dash 應用程式"""
        self.app = dash.Dash(__name__)
        
        # 設定應用程式佈局
        self.app.layout = self._create_layout()
        
        # 註冊回調函數
        self._register_callbacks()
        
        return self.app
    
    def _create_layout(self) -> html.Div:
        """創建應用程式佈局"""
        return html.Div([
            # 標題
            html.H1("雲端基礎設施視覺化分析平台", 
                   style={'textAlign': 'center', 'marginBottom': 30}),
            
            # 控制面板
            html.Div([
                html.Div([
                    html.Label("分析類型:"),
                    dcc.Dropdown(
                        id='analysis-type',
                        options=[
                            {'label': '資安漏洞分析', 'value': 'security'},
                            {'label': '故障衝擊分析', 'value': 'failure'},
                            {'label': '成本優化分析', 'value': 'cost'},
                            {'label': '網路拓撲視覺化', 'value': 'topology'}
                        ],
                        value='security',
                        style={'width': '100%'}
                    )
                ], style={'width': '30%', 'display': 'inline-block'}),
                
                html.Div([
                    html.Label("資源類型:"),
                    dcc.Dropdown(
                        id='resource-type',
                        options=[
                            {'label': '全部', 'value': 'all'},
                            {'label': 'EC2 實例', 'value': 'EC2Instance'},
                            {'label': '安全群組', 'value': 'SecurityGroup'},
                            {'label': 'VPC', 'value': 'VPC'},
                            {'label': '子網路', 'value': 'Subnet'}
                        ],
                        value='all',
                        style={'width': '100%'}
                    )
                ], style={'width': '30%', 'display': 'inline-block', 'marginLeft': '5%'}),
                
                html.Div([
                    html.Button('重新整理', id='refresh-button', n_clicks=0,
                               style={'marginTop': '25px'})
                ], style={'width': '30%', 'display': 'inline-block', 'marginLeft': '5%'})
            ], style={'marginBottom': 30}),
            
            # 主要內容區域
            html.Div([
                # 左側：統計圖表
                html.Div([
                    html.H3("統計概覽"),
                    dcc.Graph(id='statistics-chart'),
                    html.H3("資源分佈"),
                    dcc.Graph(id='resource-distribution')
                ], style={'width': '50%', 'display': 'inline-block', 'verticalAlign': 'top'}),
                
                # 右側：網路視覺化
                html.Div([
                    html.H3("網路拓撲"),
                    dcc.Graph(id='network-graph'),
                    html.H3("分析結果"),
                    html.Div(id='analysis-results')
                ], style={'width': '50%', 'display': 'inline-block', 'verticalAlign': 'top'})
            ]),
            
            # 底部：詳細資訊
            html.Div([
                html.H3("詳細資訊"),
                html.Div(id='detailed-info')
            ], style={'marginTop': 30})
        ])
    
    def _register_callbacks(self):
        """註冊回調函數"""
        
        @self.app.callback(
            [Output('statistics-chart', 'figure'),
             Output('resource-distribution', 'figure'),
             Output('network-graph', 'figure'),
             Output('analysis-results', 'children'),
             Output('detailed-info', 'children')],
            [Input('analysis-type', 'value'),
             Input('resource-type', 'value'),
             Input('refresh-button', 'n_clicks')]
        )
        def update_dashboard(analysis_type, resource_type, refresh_clicks):
            """更新儀表板內容"""
            try:
                # 獲取統計資料
                stats_fig = self._create_statistics_chart()
                distribution_fig = self._create_resource_distribution_chart()
                network_fig = self._create_network_graph(resource_type)
                
                # 根據分析類型獲取分析結果
                analysis_results = self._get_analysis_results(analysis_type)
                detailed_info = self._get_detailed_info(analysis_type, resource_type)
                
                return stats_fig, distribution_fig, network_fig, analysis_results, detailed_info
                
            except Exception as e:
                logger.error(f"更新儀表板失敗: {e}")
                return {}, {}, {}, f"錯誤: {e}", ""
    
    def _create_statistics_chart(self) -> go.Figure:
        """創建統計圖表"""
        try:
            with self.driver.session() as session:
                # 獲取節點統計
                query = """
                MATCH (n)
                RETURN labels(n)[0] as NodeType, count(n) as Count
                ORDER BY Count DESC
                """
                
                result = session.run(query)
                data = [dict(record) for record in result]
                
                if not data:
                    return go.Figure()
                
                df = pd.DataFrame(data)
                
                fig = px.bar(df, x='NodeType', y='Count', 
                           title='資源類型統計',
                           color='Count',
                           color_continuous_scale='viridis')
                
                fig.update_layout(
                    xaxis_title="資源類型",
                    yaxis_title="數量",
                    showlegend=False
                )
                
                return fig
                
        except Exception as e:
            logger.error(f"創建統計圖表失敗: {e}")
            return go.Figure()
    
    def _create_resource_distribution_chart(self) -> go.Figure:
        """創建資源分佈圖表"""
        try:
            with self.driver.session() as session:
                # 獲取區域分佈
                query = """
                MATCH (n)
                WHERE n.Region IS NOT NULL
                RETURN n.Region as Region, count(n) as Count
                ORDER BY Count DESC
                """
                
                result = session.run(query)
                data = [dict(record) for record in result]
                
                if not data:
                    return go.Figure()
                
                df = pd.DataFrame(data)
                
                fig = px.pie(df, values='Count', names='Region', 
                           title='資源區域分佈')
                
                return fig
                
        except Exception as e:
            logger.error(f"創建資源分佈圖表失敗: {e}")
            return go.Figure()
    
    def _create_network_graph(self, resource_type: str) -> go.Figure:
        """創建網路圖"""
        try:
            with self.driver.session() as session:
                # 根據資源類型構建查詢
                if resource_type == 'all':
                    query = """
                    MATCH (n)-[r]->(m)
                    RETURN n, r, m
                    LIMIT 100
                    """
                else:
                    query = f"""
                    MATCH (n:{resource_type})-[r]->(m)
                    RETURN n, r, m
                    LIMIT 100
                    """
                
                result = session.run(query)
                data = [dict(record) for record in result]
                
                if not data:
                    return go.Figure()
                
                # 構建 NetworkX 圖
                G = nx.Graph()
                
                for record in data:
                    n = record['n']
                    m = record['m']
                    r = record['r']
                    
                    # 添加節點
                    G.add_node(n.get('InstanceID', n.get('GroupID', n.get('VpcId', 'unknown'))), 
                             label=n.get('Name', n.get('GroupName', 'Unknown')))
                    G.add_node(m.get('InstanceID', m.get('GroupID', m.get('VpcId', 'unknown'))), 
                             label=m.get('Name', m.get('GroupName', 'Unknown')))
                    
                    # 添加邊
                    G.add_edge(
                        n.get('InstanceID', n.get('GroupID', n.get('VpcId', 'unknown'))),
                        m.get('InstanceID', m.get('GroupID', m.get('VpcId', 'unknown')))
                    )
                
                # 使用 spring layout
                pos = nx.spring_layout(G, k=1, iterations=50)
                
                # 創建邊的軌跡
                edge_x = []
                edge_y = []
                for edge in G.edges():
                    x0, y0 = pos[edge[0]]
                    x1, y1 = pos[edge[1]]
                    edge_x.extend([x0, x1, None])
                    edge_y.extend([y0, y1, None])
                
                edge_trace = go.Scatter(
                    x=edge_x, y=edge_y,
                    line=dict(width=0.5, color='#888'),
                    hoverinfo='none',
                    mode='lines'
                )
                
                # 創建節點的軌跡
                node_x = []
                node_y = []
                node_text = []
                for node in G.nodes():
                    x, y = pos[node]
                    node_x.append(x)
                    node_y.append(y)
                    node_text.append(f"{node}<br>{G.nodes[node].get('label', '')}")
                
                node_trace = go.Scatter(
                    x=node_x, y=node_y,
                    mode='markers+text',
                    hoverinfo='text',
                    text=node_text,
                    textposition="middle center",
                    marker=dict(
                        size=10,
                        color='lightblue',
                        line=dict(width=2, color='darkblue')
                    )
                )
                
                fig = go.Figure(data=[edge_trace, node_trace],
                              layout=go.Layout(
                                  title='網路拓撲圖',
                                  titlefont_size=16,
                                  showlegend=False,
                                  hovermode='closest',
                                  margin=dict(b=20,l=5,r=5,t=40),
                                  annotations=[ dict(
                                      text="",
                                      showarrow=False,
                                      xref="paper", yref="paper",
                                      x=0.005, y=-0.002,
                                      xanchor='left', yanchor='bottom',
                                      font=dict(color='#2E86AB', size=12)
                                  )],
                                  xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                  yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                )
                
                return fig
                
        except Exception as e:
            logger.error(f"創建網路圖失敗: {e}")
            return go.Figure()
    
    def _get_analysis_results(self, analysis_type: str) -> List[html.Div]:
        """獲取分析結果"""
        try:
            with self.driver.session() as session:
                if analysis_type == 'security':
                    # 資安分析
                    query = """
                    MATCH (instance:EC2Instance)-[:IS_MEMBER_OF]->(sg:SecurityGroup),
                          (sg)-[:HAS_RULE]->(rule:Rule)
                    WHERE rule.SourceCIDR CONTAINS '0.0.0.0/0'
                    RETURN DISTINCT 
                        instance.Name AS InstanceName,
                        instance.PublicIP AS PublicIP,
                        collect(DISTINCT rule.PortRange) AS ExposedPorts
                    LIMIT 10
                    """
                    
                    result = session.run(query)
                    data = [dict(record) for record in result]
                    
                    results = []
                    for item in data:
                        results.append(html.Div([
                            html.H4(f"🔒 {item['InstanceName']}"),
                            html.P(f"Public IP: {item['PublicIP']}"),
                            html.P(f"暴露連接埠: {', '.join(item['ExposedPorts'])}"),
                            html.Hr()
                        ]))
                    
                    return results
                
                elif analysis_type == 'cost':
                    # 成本分析
                    query = """
                    MATCH (volume:EBSVolume)
                    WHERE NOT (volume)-[:ATTACHES_TO]->(:EC2Instance)
                    RETURN volume.VolumeId AS VolumeId, volume.Size AS Size
                    LIMIT 10
                    """
                    
                    result = session.run(query)
                    data = [dict(record) for record in result]
                    
                    results = []
                    for item in data:
                        results.append(html.Div([
                            html.H4(f"💰 孤兒磁碟: {item['VolumeId']}"),
                            html.P(f"大小: {item['Size']} GB"),
                            html.Hr()
                        ]))
                    
                    return results
                
                else:
                    return [html.Div("選擇分析類型以查看結果")]
                    
        except Exception as e:
            logger.error(f"獲取分析結果失敗: {e}")
            return [html.Div(f"錯誤: {e}")]
    
    def _get_detailed_info(self, analysis_type: str, resource_type: str) -> html.Div:
        """獲取詳細資訊"""
        try:
            with self.driver.session() as session:
                # 獲取基本統計
                query = """
                MATCH (n)
                RETURN labels(n)[0] as NodeType, count(n) as Count
                ORDER BY Count DESC
                """
                
                result = session.run(query)
                data = [dict(record) for record in result]
                
                # 創建統計表格
                table_rows = []
                for item in data:
                    table_rows.append(html.Tr([
                        html.Td(item['NodeType']),
                        html.Td(item['Count'])
                    ]))
                
                table = html.Table([
                    html.Thead([
                        html.Tr([
                            html.Th("資源類型"),
                            html.Th("數量")
                        ])
                    ]),
                    html.Tbody(table_rows)
                ], style={'width': '100%', 'border': '1px solid black'})
                
                return html.Div([
                    html.H4("資源統計"),
                    table
                ])
                
        except Exception as e:
            logger.error(f"獲取詳細資訊失敗: {e}")
            return html.Div(f"錯誤: {e}")
    
    def run(self, host: str = '127.0.0.1', port: int = 8050, debug: bool = True):
        """運行儀表板"""
        if not self.driver:
            if not self.connect_neo4j():
                logger.error("無法連接到 Neo4j，無法啟動儀表板")
                return
        
        if not self.app:
            self.create_app()
        
        logger.info(f"啟動儀表板: http://{host}:{port}")
        self.app.run(host=host, port=port, debug=debug)
    
    def close(self):
        """關閉連接"""
        if self.driver:
            self.driver.close()


# 使用範例
if __name__ == "__main__":
    # Neo4j 連接設定
    NEO4J_URI = "bolt://localhost:7687"
    NEO4J_USERNAME = "neo4j"
    NEO4J_PASSWORD = "password"
    
    try:
        # 創建儀表板
        dashboard = CloudInfrastructureDashboard(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
        
        # 運行儀表板
        dashboard.run(host='127.0.0.1', port=8050, debug=True)
        
    except Exception as e:
        logger.error(f"啟動儀表板失敗: {e}")
        print(f"啟動儀表板失敗: {e}")
