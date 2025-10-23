#!/bin/bash
# 一鍵快速開始腳本

echo "雲端基礎設施分析平台"
echo "=================================="

# 檢查當前目錄
if [ ! -f "main.py" ]; then
    echo "請在專案根目錄執行此腳本"
    exit 1
fi

# 檢查是否有分析結果文件
if [ -d "output" ] && [ "$(ls -A output/*.json 2>/dev/null)" ]; then
    echo "發現現有的分析結果文件"
    echo "請選擇操作:"
    echo "1) 重新執行完整分析流程"
    echo "2) 直接啟動儀表板 (使用現有分析結果)"
    echo "3) 載入新生成的資料到 Neo4j"
    echo "4) 退出"
    echo ""
    read -p "請輸入選項 (1-4): " choice
    
    case $choice in
        2)
            echo "啟動儀表板..."
            source venv/bin/activate
            python main.py --mode dashboard --host 0.0.0.0 --port 8050
            exit 0
            ;;
        3)
            echo "載入新生成的資料到 Neo4j..."
            source venv/bin/activate
            
            # 檢查新資料文件是否存在
            if [ ! -f "data/raw/mock_aws_resources.json" ]; then
                echo "新資料文件不存在，正在生成..."
                python scripts/create_enhanced_security_data.py
            fi
            
            python main.py --mode load --data-path data/raw/mock_aws_resources.json
            echo ""
            echo "資料載入完成！"
            echo "您現在可以在 Neo4j Browser 中執行查詢了"
            echo "Neo4j Aura Console: https://console.neo4j.io"
            exit 0
            ;;
        4)
            echo "退出"
            exit 0
            ;;
        1|*)
            echo "繼續執行完整分析流程..."
            ;;
    esac
fi

# 啟動虛擬環境
echo "啟動 Python 虛擬環境..."
source venv/bin/activate

# 檢查 Neo4j 連接
echo "檢查 Neo4j 連接..."
python -c "
import os
from neo4j import GraphDatabase

# 檢查是否使用 Aura
if os.path.exists('.env'):
    with open('.env', 'r') as f:
        env_content = f.read()
        if 'neo4j+s://' in env_content or 'neo4j+ssc://' in env_content:
            print('檢測到 Neo4j Aura 配置')
            print('')
            print('Neo4j Aura 設定說明:')
            print('1. 登入 Neo4j Aura Console: https://console.neo4j.io')
            print('2. 選擇您的實例')
            print('3. 複製連接 URI 和密碼')
            print('4. 更新 .env 檔案中的 NEO4J_URI 和 NEO4J_PASSWORD')
            print('5. 重新執行此腳本')
            exit(0)

# 檢查本地 Neo4j
try:
    driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'neo4j'))
    with driver.session() as session:
        result = session.run('RETURN 1 as test')
        print('Neo4j 本地連接成功')
    driver.close()
    exit(0)
except Exception as e:
    print('Neo4j 連接失敗')
    print('')
    print('請選擇連接方式:')
    print('')
    print('使用 Neo4j Aura (推薦):')
    print('1. 登入 Neo4j Aura Console: https://console.neo4j.io')
    print('2. 創建或選擇您的實例')
    print('3. 複製連接 URI 和密碼')
    print('4. 更新 .env 檔案:')
    print('   NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io')
    print('   NEO4J_PASSWORD=your-password')
    print('')
    print('使用本地 Neo4j:')
    print('1. 開啟瀏覽器: http://localhost:7474')
    print('2. 登入: 使用者名稱 neo4j, 密碼 neo4j')
    print('3. 設定新密碼')
    print('4. 更新 .env 檔案中的 NEO4J_PASSWORD')
    print('5. 重新執行此腳本')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo ""
    echo "開始執行完整分析流程..."
    echo "================================"
    
    # 執行完整分析
    echo "正在執行完整分析流程..."
    echo "這包括：資料載入、安全性分析、故障衝擊分析、成本優化分析"
    echo ""
    python main.py --mode comprehensive-analyze --mock
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "分析完成"
        echo "============="
        echo ""
        echo "查看結果:"
        echo "- 分析報告: output/ 目錄"
        echo "- 資料庫: Neo4j Aura Console (https://console.neo4j.io)"
        echo ""
        echo "啟動視覺化儀表板:"
        echo "python main.py --mode dashboard --host 0.0.0.0 --port 8050"
        echo "然後開啟瀏覽器: http://localhost:8050"
        echo ""
        echo "是否現在啟動儀表板? (y/n)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            echo "正在啟動儀表板..."
            python main.py --mode dashboard --host 0.0.0.0 --port 8050
        fi
        echo ""
        echo "其他命令:"
        echo "- 重新分析: python main.py --mode comprehensive-analyze --mock"
        echo "- 只載入資料: python main.py --mode load --data-path data/raw/mock_aws_resources.json"
        echo "- 只執行分析: python main.py --mode analyze"
        echo "- 啟動儀表板: python main.py --mode dashboard --host 0.0.0.0 --port 8050"
        echo "- 生成新資料: python scripts/create_enhanced_security_data.py"
        echo "- 查看報告: 開啟 output/ 目錄中的 PDF 文件"
    else
        echo "分析執行失敗，請檢查錯誤訊息"
    fi
else
    echo ""
    echo "請先設定 Neo4j 連接，然後重新執行此腳本"
    echo ""
    echo "提示:"
    echo "- 使用 Neo4j Aura: 更新 .env 檔案中的 NEO4J_URI 和 NEO4J_PASSWORD"
    echo "- 使用本地 Neo4j: 更新 .env 檔案中的 NEO4J_PASSWORD"
fi
