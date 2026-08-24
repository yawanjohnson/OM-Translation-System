#!/bin/bash
# OM 多語言管理系統 — Mac 啟動腳本
# 雙擊此檔案即可在瀏覽器開啟工具

# 取得腳本所在目錄
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo "══════════════════════════════════════"
echo "  OM 多語言管理系統 正在啟動..."
echo "══════════════════════════════════════"
echo ""

# 檢查 Python 3
if ! command -v python3 &> /dev/null; then
    echo "❌ 找不到 Python 3，請先安裝："
    echo "   https://www.python.org/downloads/"
    read -p "按 Enter 關閉..."
    exit 1
fi

echo "✅ Python 版本：$(python3 --version)"

# 建立虛擬環境（如未存在）
if [ ! -d ".venv" ]; then
    echo ""
    echo "⚙  第一次啟動，建立虛擬環境..."
    python3 -m venv .venv
fi

# 啟動虛擬環境
source .venv/bin/activate

# 安裝套件（如未安裝）
pip show flask > /dev/null 2>&1 || {
    echo ""
    echo "📦 安裝必要套件（只需第一次）..."
    pip install -r requirements.txt -q
    echo "✅ 套件安裝完成"
}

echo ""
echo "🚀 啟動伺服器..."
echo "   請在瀏覽器開啟：http://127.0.0.1:5001"
echo "   關閉此視窗可停止伺服器"
echo ""

# 延遲 1.5 秒後開啟瀏覽器
(sleep 1.5 && open "http://127.0.0.1:5001") &

# 啟動 Flask
python3 app.py
