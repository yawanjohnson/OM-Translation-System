"""
indesign_exporter.py - 透過 macOS AppleScript 呼叫本機的 Adobe InDesign 匯出 PDF

此模組適用於設計師的 Mac 本機環境，直接呼叫 Adobe InDesign 引擎進行完美排版與 PDF 輸出。
"""

import os
import subprocess


def export_pdf_via_indesign(idml_path: str, pdf_path: str) -> bool:
    """
    呼叫 Mac 本機安裝的 Adobe InDesign 開啟 IDML 並匯出為真實 PDF（100% 精確排版與字型）。

    Args:
        idml_path: 修改後的 IDML 絕對路徑
        pdf_path:  要產出的 PDF 絕對路徑

    Returns:
        bool: 是否成功
    """
    abs_idml = os.path.abspath(idml_path)
    abs_pdf  = os.path.abspath(pdf_path)

    # 確保輸出目錄存在
    os.makedirs(os.path.dirname(abs_pdf), exist_ok=True)

    # AppleScript 指令
    # 這裡使用 general "Adobe InDesign" 名稱，macOS 會自動導向目前安裝的 InDesign 版本（如 InDesign 2024）
    applescript = f'''
    tell application "Adobe InDesign"
        activate
        try
            -- 開啟 IDML 檔案
            set myDoc to open POSIX file "{abs_idml}"
            
            -- 匯出為 PDF
            export myDoc to POSIX file "{abs_pdf}" format PDF export
            
            -- 關閉文件不存檔（以維持原本檔案乾淨）
            close myDoc saving no
            
            return "SUCCESS"
        on error errMsg
            return "ERROR: " & errMsg
        end try
    end tell
    '''

    try:
        # 執行 macOS 內建的 osascript
        res = subprocess.run(
            ['osascript', '-e', applescript],
            capture_output=True,
            text=True,
            timeout=45  # InDesign 讀取和匯出可能需要一點時間，給予 45 秒超時
        )
        
        output = res.stdout.strip()
        if "SUCCESS" in output:
            return True
        else:
            print("InDesign PDF 匯出失敗：", output)
            return False
    except subprocess.TimeoutExpired:
        print("InDesign PDF 匯出超時（45 秒）")
        return False
    except Exception as e:
        print("執行 AppleScript 時發生異常：", e)
        return False
