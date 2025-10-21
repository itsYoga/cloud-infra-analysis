#!/bin/bash
# 一鍵快速開始腳本

echo "🚀 雲端基礎設施分析平台 - 快速開始"
echo "=================================="

# 檢查當前目錄
if [ ! -f "main.py" ]; then
    echo "❌ 請在專案根目錄執行此腳本"
    exit 1
fi

# 啟動虛擬環境
echo "📦 啟動 Python 虛擬環境..."
source venv/bin/activate

# 檢查 Neo4j 連接
echo "🔍 檢查 Neo4j 連接..."
python -c "
from neo4j import GraphDatabase
try:
    driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'neo4j'))
    with driver.session() as session:
        result = session.run('RETURN 1 as test')
        print('✅ Neo4j 連接成功，使用預設密碼')
    driver.close()
    exit(0)
except Exception as e:
    print('⚠️  Neo4j 需要設定密碼')
    print('')
    print('請按照以下步驟設定:')
    print('1. 開啟瀏覽器: http://localhost:7474')
    print('2. 登入: 使用者名稱 neo4j, 密碼 neo4j')
    print('3. 設定新密碼')
    print('4. 更新 .env 檔案中的 NEO4J_PASSWORD')
    print('5. 重新執行此腳本')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo ""
    echo "🎯 開始執行完整分析流程..."
    echo "================================"
    
    # 執行完整分析
    python main.py --mode full --mock
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "🎉 分析完成！"
        echo "============="
        echo ""
        echo "📊 查看結果:"
        echo "- 分析報告: output/ 目錄"
        echo "- 資料庫: Neo4j Browser (http://localhost:7474)"
        echo ""
        echo "🚀 啟動視覺化儀表板:"
        echo "python main.py --mode dashboard"
        echo "然後開啟瀏覽器: http://127.0.0.1:8050"
        echo ""
        echo "💡 其他命令:"
        echo "- 重新分析: python main.py --mode full --mock"
        echo "- 只載入資料: python main.py --mode load --data-path data/raw/mock_aws_resources.json"
        echo "- 只執行分析: python main.py --mode analyze"
    else
        echo "❌ 分析執行失敗，請檢查錯誤訊息"
    fi
else
    echo ""
    echo "🔧 請先設定 Neo4j 密碼，然後重新執行此腳本"
fi
