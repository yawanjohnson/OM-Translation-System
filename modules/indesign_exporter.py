"""
indesign_exporter.py - 透過 macOS AppleScript 呼叫本機的 Adobe InDesign 匯出 PDF

此模組適用於設計師的 Mac 本機環境，直接呼叫 Adobe InDesign 引擎進行完美排版與 PDF 輸出。
"""

import os
import subprocess


def export_pdf_via_indesign(idml_path: str, pdf_path: str, lang_code: str = "") -> bool:
    """
    呼叫 Mac 本機安裝的 Adobe InDesign 開啟 IDML 並匯出為真實 PDF（100% 精確排版與字型）。

    Args:
        idml_path: 修改後的 IDML 絕對路徑
        pdf_path:  要產出的 PDF 絕對路徑
        lang_code: 當前翻譯語言代碼或名稱，用於判斷中日韓字型替代

    Returns:
        bool: 是否成功
    """
    abs_idml = os.path.abspath(idml_path)
    abs_pdf  = os.path.abspath(pdf_path)

    # 確保輸出目錄存在
    os.makedirs(os.path.dirname(abs_pdf), exist_ok=True)

    # 依語言決定替換的字型家族
    target_font = "Arial"
    if lang_code:
        l_code = lang_code.lower()
        if any(x in l_code for x in ['cht', 'chs', 'jpn', 'kor', 'zh', 'ja', 'ko', '繁', '簡', '中', '日', '韓', 'cjk']):
            target_font = "Noto Sans CJK JP"

    # AppleScript 指令
    applescript = f'''
    tell application id "com.adobe.InDesign"
        activate
        -- 關閉使用者互動以避免對話框（如缺字型、缺連結等）阻塞
        set oldLevel to user interaction level of script preferences
        set user interaction level of script preferences to never interact
        try
            -- 開啟 IDML 檔案
            set myDoc to open POSIX file "{abs_idml}"
            
            -- 自動字體替換（排除缺字型錯誤）
            tell myDoc
                set myFonts to every font
                repeat with aFont in myFonts
                    try
                        if status of aFont is not normal then
                            replace font aFont with "{target_font}"
                        end if
                    end try
                end repeat
            end tell
            
            -- 匯出為 PDF
            export myDoc to POSIX file "{abs_pdf}" format PDF type
            
            -- 關閉文件不存檔（以維持原本檔案乾淨）
            close myDoc saving no
            
            set user interaction level of script preferences to oldLevel
            return "SUCCESS"
        on error errMsg
            set user interaction level of script preferences to oldLevel
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
            timeout=120  # InDesign 讀取和匯出可能需要較長時間，給予 120 秒超時

        )
        
        output = res.stdout.strip()
        if "SUCCESS" in output:
            return True
        else:
            print("InDesign PDF 匯出失敗。Stdout:", output, "Stderr:", res.stderr.strip())
            return False
    except subprocess.TimeoutExpired:
        print("InDesign PDF 匯出超時（45 秒）")
        return False
    except Exception as e:
        print("執行 AppleScript 時發生異常：", e)
        return False
