#!/bin/bash
# 免費測試環境設定腳本

echo "=== 雲端基礎設施分析平台 - 免費測試環境設定 ==="

# 檢查 Neo4j
echo "1. 檢查 Neo4j 狀態..."
if curl -s http://localhost:7474 > /dev/null; then
    echo "   ✅ Neo4j 正在運行 (http://localhost:7474)"
    echo "   預設連接: bolt://localhost:7687"
    echo "   預設使用者: neo4j"
    echo "   預設密碼: neo4j (首次登入後需要修改)"
else
    echo "   ❌ Neo4j 未運行，請先啟動 Neo4j"
    echo "   啟動方式:"
    echo "   - Neo4j Desktop: 啟動資料庫"
    echo "   - 命令列: neo4j start"
    exit 1
fi

# 檢查 Python 環境
echo ""
echo "2. 檢查 Python 環境..."
if command -v python3 &> /dev/null; then
    echo "   ✅ Python 3 已安裝: $(python3 --version)"
else
    echo "   ❌ 未找到 Python 3，請先安裝"
    exit 1
fi

# 設定虛擬環境
echo ""
echo "3. 設定 Python 虛擬環境..."
if [ ! -d "venv" ]; then
    echo "   創建虛擬環境..."
    python3 -m venv venv
fi

echo "   啟動虛擬環境..."
source venv/bin/activate

# 安裝套件
echo ""
echo "4. 安裝 Python 套件..."
pip install --upgrade pip
pip install -r requirements.txt

# 創建目錄結構
echo ""
echo "5. 創建目錄結構..."
mkdir -p data/{raw,processed}
mkdir -p output
mkdir -p logs
mkdir -p config

# 創建環境變數檔案
echo ""
echo "6. 設定環境變數..."
cat > .env << EOF
# Neo4j 設定 (免費本地版本)
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=neo4j
NEO4J_DATABASE=neo4j

# 使用模擬資料 (不需要 AWS 憑證)
USE_MOCK_DATA=true

# 資料目錄設定
DATA_DIR=data
OUTPUT_DIR=output
LOG_DIR=logs

# 儀表板設定
DASHBOARD_HOST=127.0.0.1
DASHBOARD_PORT=8050
DASHBOARD_DEBUG=false

# 日誌設定
LOG_LEVEL=INFO
LOG_ROTATION=1 day
LOG_RETENTION=7 days
EOF

echo "   ✅ 已創建 .env 檔案"

# 生成模擬資料
echo ""
echo "7. 生成模擬 AWS 資料..."
python scripts/create_mock_data.py

# 測試 Neo4j 連接
echo ""
echo "8. 測試 Neo4j 連接..."
python -c "
from neo4j import GraphDatabase
try:
    driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'neo4j'))
    with driver.session() as session:
        result = session.run('RETURN 1 as test')
        print('   ✅ Neo4j 連接成功')
    driver.close()
except Exception as e:
    print(f'   ❌ Neo4j 連接失敗: {e}')
    print('   請檢查 Neo4j 是否正在運行，並確認密碼是否正確')
"

echo ""
echo "=== 設定完成 ==="
echo ""
echo "🎉 免費測試環境已準備就緒！"
echo ""
echo "下一步操作："
echo ""
echo "1. 載入模擬資料到 Neo4j:"
echo "   python main.py --mode load --data-path data/raw/mock_aws_resources.json"
echo ""
echo "2. 執行分析:"
echo "   python main.py --mode analyze"
echo ""
echo "3. 啟動視覺化儀表板:"
echo "   python main.py --mode dashboard"
echo "   然後開啟瀏覽器: http://127.0.0.1:8050"
echo ""
echo "4. 或執行完整流程:"
echo "   python main.py --mode full"
echo ""
echo "📊 模擬資料包含:"
echo "- 15 個 EC2 實例"
echo "- 8 個安全群組"
echo "- 3 個 VPC 和子網路"
echo "- 5 個 S3 儲存桶"
echo "- 12 個 EBS 磁碟"
echo "- 3 個 RDS 實例"
echo "- 4 個 Lambda 函數"
echo ""
echo "💡 提示:"
echo "- 所有資料都是模擬的，不會產生任何費用"
echo "- 可以修改 scripts/create_mock_data.py 來調整模擬資料"
echo "- 測試完成後可以刪除所有模擬資料"
