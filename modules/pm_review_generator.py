"""
pm_review_generator.py - 產生 PM 確認用獨立 HTML 報告

HTML 特色：
  - 完全獨立（不需網路/伺服器），PM 雙擊即可用瀏覽器開啟
  - 支援雙視圖：
    1. 📋 修改對照列表：文字修改前後並排對照，可勾選確認或填寫意見
    2. 🎨 說明書版面預覽：直接呈現 IDML 的頁面排版視覺，將文字方塊放置於頁面中，有修改的文字方塊會標紅框，點擊可看對照詳情！
  - PM 可逐條勾選 ✅ 確認 或 填寫 💬 修改意見
  - 頁面底部「完成確認」按鈕，下載 JSON 回覆檔
  - 支援列印 / 存 PDF
"""

import json
import os
from datetime import datetime


def generate_pm_review_html(
    changes: list,
    not_found: list,
    output_path: str,
    meta: dict = None,
    layout: dict = None,
) -> str:
    """
    產生 PM 確認用 HTML 檔案。
    """
    meta = meta or {}
    filename   = meta.get('filename', 'document.idml')
    date_str   = meta.get('date', datetime.now().strftime('%Y-%m-%d %H:%M'))
    run_id     = meta.get('run_id', '')
    has_pdf    = meta.get('has_pdf', False)
    pdf_filename = meta.get('pdf_filename', '')

    if has_pdf:
        # Split-screen view with PDF
        nf_html = ""
        if not_found:
            nf_html += '<div class="section-title" style="margin-top:20px; margin-bottom:0">❌ 未找到 — 請確認原文是否正確</div>'
            for nf in not_found:
                nf_html += f"""
                <div class="not-found-card" style="margin-top:0">
                  <div class="nf-icon">❌</div>
                  <div class="nf-body">
                    <div class="nf-lang">{_esc(nf.get("lang_code",""))}</div>
                    <div class="nf-text">搜尋原文：{_esc(nf.get("find",""))}</div>
                    <div class="nf-text" style="text-decoration:none;color:#374151">預計改為：{_esc(nf.get("replace",""))}</div>
                    <div class="nf-note">{_esc(nf.get("note",""))}</div>
                  </div>
                </div>"""
        
        views_html = f"""
        <!-- Split-screen view with PDF -->
        <div style="display: flex; gap: 20px; height: calc(100vh - 160px); padding: 0 40px 20px 40px; margin-top: 15px;">
          <!-- Left: PDF iframe -->
          <div style="flex: 1.3; background: white; border-radius: 12px; border: 1px solid #e2e8f0; overflow: hidden; height: 100%; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
            <iframe src="{pdf_filename}" style="width: 100%; height: 100%; border: none;"></iframe>
          </div>
          <!-- Right: Checklist / Cards -->
          <div style="flex: 0.7; height: 100%; overflow-y: auto; padding-right: 12px; display: flex; flex-direction: column; gap: 14px;">
            <div class="section-title" style="margin-bottom:0">✅ 修改清單（共 {len(changes)} 條）</div>
            <div id="cards-container"></div>
            {nf_html}
          </div>
        </div>
        """
    else:
        # Standard tabbed view
        nf_html = ""
        if not_found:
            nf_html += '<div class="section-title">❌ 未找到 — 請確認原文是否正確</div>'
            for nf in not_found:
                nf_html += f"""
                <div class="not-found-card">
                  <div class="nf-icon">❌</div>
                  <div class="nf-body">
                    <div class="nf-lang">{_esc(nf.get("lang_code",""))}</div>
                    <div class="nf-text">搜尋原文：{_esc(nf.get("find",""))}</div>
                    <div class="nf-text" style="text-decoration:none;color:#374151">預計改為：{_esc(nf.get("replace",""))}</div>
                    <div class="nf-note">{_esc(nf.get("note",""))}</div>
                  </div>
                </div>"""
        
        title_html = f'<div class="section-title">✅ 修改清單（共 {len(changes)} 條）</div>' if changes else ''
        
        views_html = f"""
        <!-- VIEW 1: List View -->
        <div class="view-container active" id="view-list">
          <div class="main">
            {title_html}
            <div id="cards-container"></div>
            {nf_html}
          </div>
        </div>

        <!-- VIEW 2: Layout View -->
        <div class="view-container" id="view-layout">
          <div class="layout-container">
            <div class="layout-sidebar" id="layout-pages-list">
              <!-- Page buttons injected by JS -->
            </div>
            <div class="layout-stage">
              <div class="layout-canvas-wrap" id="layout-canvas-container">
                <!-- Rendered page elements -->
              </div>
            </div>
          </div>
        </div>
        """

    # 將資料序列化給 JS 使用
    changes_json   = json.dumps(changes,   ensure_ascii=False)
    not_found_json = json.dumps(not_found, ensure_ascii=False)
    layout_json    = json.dumps(layout or {}, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>PM 修改確認 — {filename}</title>
<style>
/* ── Reset & Base ── */
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  background: #f0f2f5;
  color: #1a1a2e;
  font-size: 14px;
  line-height: 1.6;
}}
@media print {{
  body {{ background: white; }}
  .no-print {{ display: none !important; }}
  .card {{ break-inside: avoid; box-shadow: none; border: 1px solid #ddd; }}
  .action-bar {{ display: none; }}
  .view-tabs {{ display: none !important; }}
}}

/* ── Header ── */
.header {{
  background: linear-gradient(135deg, #1b2a4a 0%, #2d4a7a 100%);
  color: white;
  padding: 28px 40px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 16px;
}}
.header-left h1 {{
  font-size: 22px;
  font-weight: 700;
  margin-bottom: 6px;
}}
.header-meta {{
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
  margin-top: 8px;
}}
.meta-item {{
  font-size: 12px;
  color: rgba(255,255,255,0.75);
  display: flex;
  align-items: center;
  gap: 5px;
}}
.header-stats {{
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}}
.stat-box {{
  background: rgba(255,255,255,0.12);
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: 10px;
  padding: 12px 20px;
  text-align: center;
  min-width: 90px;
}}
.stat-num {{
  font-size: 26px;
  font-weight: 800;
  line-height: 1;
}}
.stat-label {{ font-size: 11px; color: rgba(255,255,255,0.7); margin-top: 4px; }}
.stat-box.success .stat-num {{ color: #6ee7a0; }}
.stat-box.warning .stat-num {{ color: #fcd34d; }}
.stat-box.pending .stat-num {{ color: #93c5fd; }}

/* ── View Switch Tabs ── */
.view-tabs {{
  display: flex;
  background: white;
  border-bottom: 1px solid #e2e8f0;
  padding: 0 40px;
  gap: 8px;
}}
.view-tab {{
  padding: 14px 24px;
  background: none;
  border: none;
  font-size: 13.5px;
  font-weight: 600;
  color: #64748b;
  cursor: pointer;
  border-bottom: 3px solid transparent;
  transition: all 0.15s;
}}
.view-tab:hover {{ color: #1b2a4a; }}
.view-tab.active {{
  color: #1b2a4a;
  border-bottom-color: #1b2a4a;
}}

/* ── Progress Bar ── */
.progress-wrap {{
  background: #1b2a4a;
  padding: 12px 40px;
  display: flex;
  align-items: center;
  gap: 14px;
}}
.progress-bar-bg {{
  flex: 1;
  height: 8px;
  background: rgba(255,255,255,0.15);
  border-radius: 4px;
  overflow: hidden;
}}
.progress-bar-fill {{
  height: 100%;
  background: linear-gradient(90deg, #34d399, #10b981);
  border-radius: 4px;
  transition: width 0.4s ease;
  width: 0%;
}}
.progress-text {{
  color: rgba(255,255,255,0.8);
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
}}

/* ── Main Layout ── */
.view-container {{ display: none; }}
.view-container.active {{ display: block; }}

.main {{
  max-width: 1020px;
  margin: 0 auto;
  padding: 24px 20px 120px;
}}

/* ── Section Title ── */
.section-title {{
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #6b7280;
  margin: 28px 0 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}}
.section-title::after {{
  content: '';
  flex: 1;
  height: 1px;
  background: #e5e7eb;
}}

/* ── Change Card ── */
.card {{
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
  margin-bottom: 12px;
  overflow: hidden;
  border: 2px solid transparent;
  transition: border-color 0.2s, box-shadow 0.2s;
}}
.card.confirmed  {{ border-color: #10b981; box-shadow: 0 0 0 3px rgba(16,185,129,0.1); }}
.card.has-comment {{ border-color: #f59e0b; box-shadow: 0 0 0 3px rgba(245,158,11,0.1); }}
.card.rejected   {{ border-color: #ef4444; box-shadow: 0 0 0 3px rgba(239,68,68,0.1); }}

.card-header {{
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: #f8fafc;
  border-bottom: 1px solid #f1f5f9;
}}
.lang-pill {{
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 700;
  font-family: monospace;
  background: #e0e7ff;
  color: #4338ca;
  letter-spacing: 0.04em;
}}
.note-text {{
  font-size: 12px;
  color: #6b7280;
  flex: 1;
}}
.card-num {{
  font-size: 11px;
  color: #9ca3af;
  font-weight: 600;
}}
.status-badge {{
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 600;
  display: none;
}}
.status-badge.show {{ display: inline-flex; align-items: center; gap: 4px; }}
.status-badge.confirmed {{ background: #d1fae5; color: #065f46; }}
.status-badge.has-comment {{ background: #fef3c7; color: #92400e; }}
.status-badge.rejected {{ background: #fee2e2; color: #991b1b; }}

.card-body {{
  padding: 16px;
}}
.diff-row {{
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 14px;
}}
@media (max-width: 600px) {{
  .diff-row {{ grid-template-columns: 1fr; }}
}}
.diff-label {{
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  margin-bottom: 6px;
}}
.diff-label.before {{ color: #dc2626; }}
.diff-label.after  {{ color: #059669; }}

.diff-text {{
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 13.5px;
  line-height: 1.7;
  word-break: break-word;
  min-height: 44px;
}}
.diff-text.before {{
  background: #fff5f5;
  border: 1px solid #fecaca;
  color: #991b1b;
}}
.diff-text.after {{
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #065f46;
  font-weight: 600;
}}

/* ── Card Actions ── */
.card-actions {{
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}}
.comment-wrap {{
  flex: 1;
  min-width: 200px;
}}
.comment-input {{
  width: 100%;
  padding: 9px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 13px;
  font-family: inherit;
  outline: none;
  transition: border-color 0.15s;
  resize: vertical;
  min-height: 40px;
  max-height: 120px;
  color: #374151;
}}
.comment-input:focus {{ border-color: #6366f1; }}
.comment-input::placeholder {{ color: #9ca3af; }}

.btn-action {{
  padding: 8px 18px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  border: none;
  cursor: pointer;
  transition: all 0.15s;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  white-space: nowrap;
}}
.btn-confirm {{
  background: #1b2a4a;
  color: white;
}}
.btn-confirm:hover {{ background: #2d4a7a; }}
.btn-confirm.active {{
  background: #d1fae5;
  color: #065f46;
  border: 2px solid #10b981;
}}

/* ── Not Found Section ── */
.not-found-card {{
  background: #fff8f8;
  border: 1px solid #fecaca;
  border-radius: 10px;
  padding: 14px 16px;
  margin-bottom: 8px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
}}
.nf-icon {{ font-size: 18px; flex-shrink: 0; margin-top: 2px; }}
.nf-body {{ flex: 1; }}
.nf-lang {{ font-size: 11px; font-weight: 700; color: #dc2626; font-family: monospace; }}
.nf-text {{ font-size: 13px; color: #7f1d1d; margin-top: 3px; word-break: break-word; }}
.nf-text" style="text-decoration:none;color:#374151" {{ tag-style }}
.nf-note {{ font-size: 11px; color: #9ca3af; margin-top: 4px; }}

/* ── Layout View Styling ── */
.layout-container {{
  display: flex;
  height: calc(100vh - 190px);
  background: #cbd5e1;
}}
.layout-sidebar {{
  width: 240px;
  background: #1b2a4a;
  overflow-y: auto;
  padding: 16px 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex-shrink: 0;
  border-right: 1px solid rgba(255,255,255,0.1);
}}
.layout-page-btn {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 14px;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.1);
  color: rgba(255,255,255,0.85);
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  text-align: left;
  transition: all 0.15s;
}}
.layout-page-btn:hover {{ background: rgba(255,255,255,0.12); color: white; }}
.layout-page-btn.active {{
  background: #4f8ef7;
  color: white;
  border-color: #4f8ef7;
  box-shadow: 0 4px 12px rgba(79, 142, 247, 0.3);
}}
.layout-page-btn.has-change .dot {{
  width: 8px; height: 8px;
  border-radius: 50%;
  background: #f85149;
  box-shadow: 0 0 6px #f85149;
  display: inline-block;
}}

.layout-stage {{
  flex: 1;
  overflow: auto;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 50px;
  position: relative;
}}
.layout-canvas-wrap {{
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}}
.page-canvas {{
  background: white;
  box-shadow: 0 12px 40px rgba(0,0,0,0.25);
  position: relative;
  border: 1px solid #94a3b8;
  transform-origin: center center;
}}

.layout-frame {{
  position: absolute;
  border: 1px dashed rgba(79, 142, 247, 0.4);
  padding: 4px 6px;
  color: #334155;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.82);
  white-space: pre-wrap;
  word-wrap: break-word;
  line-height: var(--frame-leading, 1.4);
  font-size: var(--frame-font-size, 9px);
  font-family: var(--frame-font-family, -apple-system, sans-serif);
  text-align: var(--frame-justify, left);
  transition: background 0.15s, border-color 0.15s;
  box-sizing: border-box;
}}
.layout-frame:hover {{
  border-color: #4f8ef7;
  background: rgba(255, 255, 255, 0.95);
  z-index: 10;
}}
.layout-frame.has-change {{
  border: 2px solid #ef4444;
  background: rgba(254, 242, 242, 0.9);
  box-shadow: 0 0 10px rgba(239,68,68,0.15);
  cursor: pointer;
  z-index: 5;
}}
.layout-frame.has-change:hover {{
  border-color: #dc2626;
  background: #fef2f2;
  box-shadow: 0 0 14px rgba(239,68,68,0.3);
  z-index: 12;
}}

/* 圖片框輪廓 */
.layout-image-frame {{
  position: absolute;
  border: 1.5px dashed rgba(148, 163, 184, 0.7);
  background: rgba(241, 245, 249, 0.5);
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 2px;
  overflow: hidden;
}}
.layout-image-frame .img-icon {{
  font-size: calc(var(--frame-font-size, 9px) * 1.6);
  opacity: 0.45;
  line-height: 1;
}}
.layout-image-frame .img-label {{
  font-size: calc(var(--frame-font-size, 9px) * 0.9);
  color: #94a3b8;
  text-align: center;
  line-height: 1.2;
}}

.frame-badge {{
  position: absolute;
  top: 2px;
  right: 2px;
  background: #dc2626;
  color: white;
  font-size: 8px;
  font-weight: 800;
  padding: 1px 4px;
  border-radius: 3px;
  line-height: 1;
}}

/* ── Modal Pop ── */
.modal-overlay {{
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(13, 17, 23, 0.65);
  align-items: center;
  justify-content: center;
  z-index: 5000;
  backdrop-filter: blur(2px);
}}
.modal-box {{
  background: white;
  border-radius: 12px;
  width: 600px;
  max-width: 90%;
  box-shadow: 0 20px 50px rgba(0,0,0,0.3);
  overflow: hidden;
  animation: modalPop 0.18s ease-out;
}}
@keyframes modalPop {{
  from {{ transform: scale(0.92); opacity: 0; }}
  to {{ transform: scale(1); opacity: 1; }}
}}
.modal-hdr {{
  padding: 14px 20px;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}}
.modal-hdr h3 {{ font-size: 15px; font-weight: 700; }}
.modal-close-btn {{
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  color: #94a3b8;
}}
.modal-close-btn:hover {{ color: #475569; }}
.modal-bdy {{ padding: 20px; max-height: 480px; overflow-y: auto; }}

/* ── Action Bar (fixed bottom) ── */
.action-bar {{
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: white;
  border-top: 1px solid #e5e7eb;
  padding: 14px 40px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  box-shadow: 0 -4px 20px rgba(0,0,0,0.1);
  z-index: 100;
  flex-wrap: wrap;
}}
.action-bar-left {{
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}}
.action-count {{
  font-size: 13px;
  color: #6b7280;
}}
.action-count strong {{ color: #1a1a2e; }}
.btn-confirm-all {{
  padding: 11px 28px;
  background: linear-gradient(135deg, #1b2a4a 0%, #2d4a7a 100%);
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: opacity 0.15s, transform 0.1s;
  display: flex;
  align-items: center;
  gap: 7px;
}}
.btn-confirm-all:hover {{ opacity: 0.9; transform: translateY(-1px); }}
.btn-confirm-all:active {{ transform: translateY(0); }}
.btn-print {{
  padding: 10px 20px;
  border: 1px solid #e5e7eb;
  background: white;
  color: #374151;
  border-radius: 8px;
  font-size: 13px;
  cursor: pointer;
  font-weight: 500;
  transition: background 0.15s;
}}
.btn-print:hover {{ background: #f9fafb; }}

/* ── Done Overlay ── */
.done-overlay {{
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.5);
  align-items: center;
  justify-content: center;
  z-index: 500;
}}
.done-box {{
  background: white;
  border-radius: 16px;
  padding: 40px;
  max-width: 460px;
  width: 90%;
  text-align: center;
  box-shadow: 0 20px 60px rgba(0,0,0,0.3);
  animation: pop 0.3s ease;
}}
@keyframes pop {{
  from {{ transform: scale(0.85); opacity: 0; }}
  to   {{ transform: scale(1); opacity: 1; }}
}}
.done-icon {{ font-size: 52px; margin-bottom: 16px; }}
.done-title {{ font-size: 20px; font-weight: 800; margin-bottom: 8px; }}
.done-desc {{ font-size: 13px; color: #6b7280; margin-bottom: 24px; line-height: 1.7; }}
.done-btn {{
  padding: 12px 32px;
  background: linear-gradient(135deg, #10b981, #059669);
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  width: 100%;
  margin-bottom: 10px;
  transition: opacity 0.15s;
}}
.done-btn:hover {{ opacity: 0.9; }}
</style>
</head>
<body>

<!-- Header -->
<div class="header">
  <div class="header-left">
    <h1>📋 修改確認報告</h1>
    <div style="font-size: 13px; color: rgba(255,255,255,0.85); margin-top: 6px; font-weight: 500; line-height: 1.5;">
      💡 如果您看到排版問題，請在網頁上留言。如果是翻譯文字翻錯，請您直接在 Excel 中修改該欄位，並提供新 Excel 給我。
    </div>
    <div class="header-meta">
      <span class="meta-item">📁 {filename}</span>
      <span class="meta-item">🕐 {date_str}</span>
      {'<span class="meta-item">🔑 ' + run_id + '</span>' if run_id else ''}
    </div>
  </div>
  <div class="header-stats">
    <div class="stat-box success">
      <div class="stat-num">{len(changes)}</div>
      <div class="stat-label">已修改</div>
    </div>
    {'<div class="stat-box warning"><div class="stat-num">' + str(len(not_found)) + '</div><div class="stat-label">未找到</div></div>' if not_found else ''}
    <div class="stat-box pending">
      <div class="stat-num" id="confirmed-count">0</div>
      <div class="stat-label">已確認</div>
    </div>
  </div>
</div>

{'' if has_pdf else '<div class="view-tabs no-print"><button class="view-tab active" id="tab-btn-list" onclick="switchView(\'list\')">📋 修改對照列表</button><button class="view-tab" id="tab-btn-layout" onclick="switchView(\'layout\')">🎨 說明書版面預覽</button></div>'}

<!-- Progress Bar -->
<div class="progress-wrap no-print">
  <div class="progress-bar-bg">
    <div class="progress-bar-fill" id="progress-fill"></div>
  </div>
  <div class="progress-text" id="progress-text">0 / {len(changes)} 已確認</div>
</div>

{views_html}

<!-- Review Popup Modal (for layout view) -->
<div class="modal-overlay" id="frame-modal" onclick="closeFrameModal()">
  <div class="modal-box" onclick="event.stopPropagation()">
    <div class="modal-hdr">
      <h3 id="modal-title">修改詳情</h3>
      <button class="modal-close-btn" onclick="closeFrameModal()">✕</button>
    </div>
    <div class="modal-bdy" id="modal-body-content">
      <!-- Changes details will be dynamically rendered here -->
    </div>
  </div>
</div>

<!-- Fixed Action Bar -->
<div class="action-bar no-print">
  <div class="action-bar-left">
    <div class="action-count">已確認 <strong id="action-confirmed">0</strong> / {len(changes)} 條</div>
    <button class="btn-print" onclick="window.print()">🖨 列印 / 存 PDF</button>
  </div>
  <button class="btn-confirm-all" onclick="finishReview()">
    ✅ 完成確認 — 下載回覆
  </button>
</div>

<!-- Done Overlay -->
<div class="done-overlay" id="done-overlay">
  <div class="done-box">
    <div class="done-icon">🎉</div>
    <div class="done-title">確認完成！</div>
    <div class="done-desc">
      回覆檔已下載。<br/>請將 <strong id="done-filename"></strong><br/>傳給設計師處理。
    </div>
    <button class="done-btn" onclick="document.getElementById('done-overlay').style.display='none'">
      👍 好的，關閉
    </button>
  </div>
</div>

<script>
const CHANGES    = {changes_json};
const NOT_FOUND  = {not_found_json};
const LAYOUT     = {layout_json};
const FILENAME   = {json.dumps(filename)};
const RUN_ID     = {json.dumps(run_id)};

// 狀態：{{ id: {{ confirmed: bool, comment: '' }} }}
const state = {{}};
let pagesList = [];

// 初始化狀態
CHANGES.forEach((ch, i) => {{
  state[i] = {{ confirmed: false, comment: '' }};
}});

// 1. 切換分頁視圖
function switchView(viewType) {{
  document.querySelectorAll('.view-tab').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.view-container').forEach(c => c.classList.remove('active'));
  
  if (viewType === 'list') {{
    document.getElementById('tab-btn-list').classList.add('active');
    document.getElementById('view-list').classList.add('active');
  }} else {{
    document.getElementById('tab-btn-layout').classList.add('active');
    document.getElementById('view-layout').classList.add('active');
    // 如果是第一次切換版面，初始化版面按鈕並渲染首頁
    if (pagesList.length === 0) {{
      initLayoutView();
    }} else {{
      setTimeout(fitPage, 50);
    }}
  }}
}}

// 2. 建立修改列表卡片
function buildCards() {{
  const container = document.getElementById('cards-container');
  if (!CHANGES.length) {{
    container.innerHTML = '<p style="color:#9ca3af;text-align:center;padding:40px">無修改記錄</p>';
    return;
  }}

  CHANGES.forEach((ch, i) => {{
    const card = document.createElement('div');
    card.className = 'card';
    card.id = `card-${{i}}`;
    card.innerHTML = `
      <div class="card-header">
        <span class="card-num">#${{i+1}}</span>
        <span class="lang-pill">${{esc(ch.lang_code || '')}}</span>
        <span class="note-text">${{esc(ch.note || '')}}</span>
        <span class="status-badge" id="badge-${{i}}"></span>
      </div>
      <div class="card-body">
        <div class="diff-row">
          <div>
            <div class="diff-label before">修改前（原文）</div>
            <div class="diff-text before">${{esc(ch.find || '')}}</div>
          </div>
          <div>
            <div class="diff-label after">修改後（新文字）</div>
            <div class="diff-text after">${{esc(ch.replace || '')}}</div>
          </div>
        </div>
        <div class="card-actions">
          <div class="comment-wrap">
            <textarea
              class="comment-input"
              id="comment-${{i}}"
              placeholder="💬 填寫意見（選填）：如有問題請在此說明..."
              oninput="onCommentChange(${{i}}, this.value)"
              rows="1"
            ></textarea>
          </div>
          <button class="btn-action btn-confirm" id="btn-${{i}}" onclick="toggleConfirm(${{i}})">
            ✅ 確認
          </button>
        </div>
      </div>
    `;
    container.appendChild(card);
  }});
}}

function toggleConfirm(i) {{
  state[i].confirmed = !state[i].confirmed;
  updateCard(i);
  updateProgress();
  
  // 如果版面視圖已載入，同步更新版面視圖中的卡片彈出視窗
  const openModalId = document.getElementById('frame-modal').dataset.openStoryId;
  if (openModalId) {{
    const frameChanges = getChangesForStory(openModalId);
    renderModalContent(openModalId, frameChanges);
  }}
}}

function onCommentChange(i, val) {{
  state[i].comment = val.trim();
  updateCard(i);
}}

function updateCard(i) {{
  const card   = document.getElementById(`card-${{i}}`);
  const btn    = document.getElementById(`btn-${{i}}`);
  const badge  = document.getElementById(`badge-${{i}}`);
  const commentInput = document.getElementById(`comment-${{i}}`);
  
  if (commentInput) {{
    commentInput.value = state[i].comment;
  }}
  
  const hasComment = state[i].comment.length > 0;

  card.classList.remove('confirmed', 'has-comment', 'rejected');
  badge.classList.remove('show', 'confirmed', 'has-comment', 'rejected');
  btn.classList.remove('active');

  if (state[i].confirmed && hasComment) {{
    card.classList.add('has-comment');
    badge.className = 'status-badge show has-comment';
    badge.innerHTML = '💬 確認含意見';
    btn.classList.add('active');
    btn.textContent = '✅ 已確認';
  }} else if (state[i].confirmed) {{
    card.classList.add('confirmed');
    badge.className = 'status-badge show confirmed';
    badge.innerHTML = '✅ 已確認';
    btn.classList.add('active');
    btn.textContent = '✅ 已確認';
  }} else if (hasComment) {{
    card.classList.add('has-comment');
    badge.className = 'status-badge show has-comment';
    badge.innerHTML = '💬 有意見';
    btn.textContent = '✅ 確認';
  }} else {{
    btn.textContent = '✅ 確認';
  }}
}}

function updateProgress() {{
  const confirmed = Object.values(state).filter(s => s.confirmed).length;
  const total     = CHANGES.length;
  const pct       = total > 0 ? (confirmed / total * 100) : 0;

  document.getElementById('progress-fill').style.width = pct + '%';
  document.getElementById('progress-text').textContent = `${{confirmed}} / ${{total}} 已確認`;
  document.getElementById('confirmed-count').textContent = confirmed;
  document.getElementById('action-confirmed').textContent = confirmed;
}}

// 3. 版面編排預覽 (IDML Layout Layout View) 邏輯
function initLayoutView() {{
  if (!LAYOUT.spreads || LAYOUT.spreads.length === 0) {{
    document.getElementById('layout-canvas-container').innerHTML = 
      '<p style="color:#64748b;text-align:center;padding:40px">說明書版面配置讀取失敗或此檔案無版面資訊</p>';
    return;
  }}

  // 整理 Page 列表
  pagesList = [];
  LAYOUT.spreads.forEach(spread => {{
    spread.pages.forEach(page => {{
      const frames = spread.text_frames.filter(f => f.page_id === page.id);
      pagesList.push({{
        ...page,
        spread_id: spread.id,
        text_frames: frames
      }});
    }});
  }});

  // 排序
  pagesList.sort((a, b) => a.page_num - b.page_num);

  // 渲染 Sidebar 的頁面按鈕
  const sidebar = document.getElementById('layout-pages-list');
  sidebar.innerHTML = '';
  
  pagesList.forEach((page, idx) => {{
    const btn = document.createElement('button');
    btn.className = 'layout-page-btn';
    btn.id = `page-btn-${{idx}}`;
    
    // 檢查此頁是否有修改項目
    let pageHasChange = false;
    for (let frame of page.text_frames) {{
      if (getChangesForStory(frame.story_id).length > 0) {{
        pageHasChange = true;
        break;
      }}
    }}
    
    btn.innerHTML = `<span>Page ${{page.page_num}}</span> <span class="dot"></span>`;
    if (pageHasChange) {{
      btn.classList.add('has-change');
    }}
    btn.onclick = () => selectPage(idx);
    sidebar.appendChild(btn);
  }});

  // 預設選擇第一頁
  if (pagesList.length > 0) {{
    selectPage(0);
  }}

  // 監聽視窗縮放
  window.addEventListener('resize', fitPage);
}}

function selectPage(idx) {{
  document.querySelectorAll('.layout-page-btn').forEach(b => b.classList.remove('active'));
  document.getElementById(`page-btn-${{idx}}`).classList.add('active');
  renderPage(idx);
}}

function renderPage(idx) {{
  const page = pagesList[idx];
  const container = document.getElementById('layout-canvas-container');
  container.innerHTML = '';

  const canvas = document.createElement('div');
  canvas.className = 'page-canvas';
  canvas.id = 'page-canvas-el';
  canvas.style.width = page.width + 'px';
  canvas.style.height = page.height + 'px';

  // 取得每頁的 spread 中的圖片框
  const spreadData = LAYOUT.spreads ? LAYOUT.spreads.find(s => s.pages && s.pages.some(p => p.id === page.id)) : null;
  const imageFrames = spreadData ? (spreadData.image_frames || []).filter(f => f.page_id === page.id) : [];

  // 1. 先畫圖片框（在最底層）
  imageFrames.forEach(imgf => {{
    const fb = imgf.bounds;
    const pb = page.bounds;
    const top    = fb[0] - pb[0];
    const left   = fb[1] - pb[1];
    const width  = fb[3] - fb[1];
    const height = fb[2] - fb[0];

    const frameEl = document.createElement('div');
    frameEl.className = 'layout-image-frame';
    frameEl.style.top    = top + 'px';
    frameEl.style.left   = left + 'px';
    frameEl.style.width  = width + 'px';
    frameEl.style.height = height + 'px';

    // 圖標和標籤
    const icon = document.createElement('div');
    icon.className = 'img-icon';
    icon.textContent = imgf.has_image ? '🖼️' : '□';
    const label = document.createElement('div');
    label.className = 'img-label';
    label.textContent = imgf.has_image ? 'Image' : imgf.type || 'Rect';

    frameEl.appendChild(icon);
    frameEl.appendChild(label);
    canvas.appendChild(frameEl);
  }});

  // 2. 畫文字框
  page.text_frames.forEach(frame => {{
    const fb = frame.bounds;
    const pb = page.bounds;
    const top    = fb[0] - pb[0];
    const left   = fb[1] - pb[1];
    const width  = fb[3] - fb[1];
    const height = fb[2] - fb[0];

    const frameEl = document.createElement('div');
    frameEl.className = 'layout-frame';
    frameEl.style.top    = top + 'px';
    frameEl.style.left   = left + 'px';
    frameEl.style.width  = width + 'px';
    frameEl.style.height = height + 'px';

    // 套用字型樣式
    const sty = (LAYOUT.story_styles || {{}})[frame.story_id];
    if (sty) {{
      const ptToPx = 1.0;  // 1pt = 1px (配合 scale 收縮)
      const fontPx = sty.font_size * ptToPx;
      const leadPx = sty.leading  * ptToPx;
      frameEl.style.setProperty('--frame-font-size', fontPx + 'px');
      frameEl.style.setProperty('--frame-leading',   leadPx + 'px');
      if (sty.font_family) {{
        frameEl.style.setProperty('--frame-font-family', `"${{sty.font_family}}", -apple-system, sans-serif`);
      }}
      const justMap = {{
        'LeftAlign':      'left',
        'RightAlign':     'right',
        'CenterAlign':    'center',
        'FullyJustified': 'justify',
        'Justified':      'justify',
      }};
      frameEl.style.setProperty('--frame-justify', justMap[sty.justification] || 'left');
    }}

    const rawText = LAYOUT.stories[frame.story_id] || '';
    frameEl.textContent = rawText;

    // 檢查此文字框是否有修改
    const frameChanges = getChangesForStory(frame.story_id);
    if (frameChanges.length > 0) {{
      frameEl.classList.add('has-change');

      const badge = document.createElement('span');
      badge.className = 'frame-badge';
      badge.textContent = `★ ${{frameChanges.length}} 處修改`;
      frameEl.appendChild(badge);

      frameEl.onclick = (e) => {{
        e.stopPropagation();
        openFrameModal(frame.story_id, rawText, frameChanges);
      }};
    }}

    canvas.appendChild(frameEl);
  }});

  container.appendChild(canvas);
  setTimeout(fitPage, 30);
}}

function fitPage() {{
  const canvas = document.getElementById('page-canvas-el');
  if (!canvas) return;
  const stage = document.querySelector('.layout-stage');
  
  // 自動縮放以完整呈現 A4 等版面
  const pad = 60;
  const sw = (stage.clientWidth - pad) / canvas.clientWidth;
  const sh = (stage.clientHeight - pad) / canvas.clientHeight;
  const scale = Math.min(sw, sh, 1.0); // 最大不超過 100%
  
  canvas.style.transform = `scale(${{scale}})`;
}}

function getChangesForStory(storyId) {{
  return CHANGES.map((ch, idx) => ({{ ...ch, originalIndex: idx }})).filter(ch => {{
    const chStoryId = ch.story.replace('Stories/', '').replace('.xml', '');
    return chStoryId === storyId;
  }});
}}

// 彈出對照視窗
function openFrameModal(storyId, rawText, frameChanges) {{
  const modal = document.getElementById('frame-modal');
  modal.dataset.openStoryId = storyId;
  modal.style.display = 'flex';
  renderModalContent(storyId, frameChanges);
}}

function renderModalContent(storyId, frameChanges) {{
  const container = document.getElementById('modal-body-content');
  container.innerHTML = '';
  
  document.getElementById('modal-title').textContent = `修改項目對照 (${{frameChanges.length}} 處)`;

  frameChanges.forEach(ch => {{
    const card = document.createElement('div');
    card.className = 'card';
    card.style.boxShadow = 'none';
    card.style.border = '1px solid #e2e8f0';
    card.style.marginBottom = '12px';
    
    const isConfirmed = state[ch.originalIndex].confirmed;
    const currentComment = state[ch.originalIndex].comment;
    
    card.innerHTML = `
      <div class="card-header" style="background:#f8fafc">
        <span class="card-num">#${{ch.originalIndex + 1}}</span>
        <span class="lang-pill">${{esc(ch.lang_code)}}</span>
        <span class="note-text">${{esc(ch.note || '')}}</span>
        <span class="status-badge ${{isConfirmed ? 'show confirmed' : (currentComment ? 'show has-comment' : '')}}" id="modal-badge-${{ch.originalIndex}}">
          ${{isConfirmed ? '✅ 已確認' : (currentComment ? '💬 有意見' : '')}}
        </span>
      </div>
      <div class="card-body" style="padding:12px">
        <div class="diff-row" style="margin-bottom:8px">
          <div>
            <div class="diff-label before">修改前</div>
            <div class="diff-text before" style="font-size:12px; padding:6px 10px">${{esc(ch.find)}}</div>
          </div>
          <div>
            <div class="diff-label after">修改後</div>
            <div class="diff-text after" style="font-size:12px; padding:6px 10px">${{esc(ch.replace)}}</div>
          </div>
        </div>
        <div class="card-actions" style="margin-top:8px">
          <div class="comment-wrap">
            <textarea
              class="comment-input"
              id="modal-comment-${{ch.originalIndex}}"
              placeholder="💬 填寫意見（選填）..."
              oninput="onModalCommentInput(${{ch.originalIndex}}, this.value)"
              rows="1"
              style="padding:6px 10px; min-height:34px"
            >${{esc(currentComment)}}</textarea>
          </div>
          <button class="btn-action btn-confirm ${{isConfirmed ? 'active' : ''}}" 
                  id="modal-btn-${{ch.originalIndex}}" 
                  onclick="toggleConfirm(${{ch.originalIndex}})"
                  style="padding:6px 14px">
            ${{isConfirmed ? '✅ 已確認' : '✅ 確認'}}
          </button>
        </div>
      </div>
    `;
    container.appendChild(card);
  }});
}}

function onModalCommentInput(origIdx, val) {{
  state[origIdx].comment = val.trim();
  
  // 同步更新背後的列表卡片與本彈窗樣式
  updateCard(origIdx);
  
  // 更新彈窗內的 badge
  const badge = document.getElementById(`modal-badge-${{origIdx}}`);
  const isConfirmed = state[origIdx].confirmed;
  
  badge.classList.remove('show', 'confirmed', 'has-comment');
  if (isConfirmed && val.trim()) {{
    badge.className = 'status-badge show has-comment';
    badge.innerHTML = '💬 確認含意見';
  }} else if (isConfirmed) {{
    badge.className = 'status-badge show confirmed';
    badge.innerHTML = '✅ 已確認';
  }} else if (val.trim()) {{
    badge.className = 'status-badge show has-comment';
    badge.innerHTML = '💬 有意見';
  }}
}}

function closeFrameModal() {{
  const modal = document.getElementById('frame-modal');
  modal.style.display = 'none';
  delete modal.dataset.openStoryId;
}}

function finishReview() {{
  const confirmed = Object.values(state).filter(s => s.confirmed).length;
  const total     = CHANGES.length;

  const reply = {{
    meta: {{
      filename:      FILENAME,
      run_id:        RUN_ID,
      review_date:   new Date().toLocaleString('zh-TW'),
      total:         total,
      confirmed:     confirmed,
      with_comments: Object.values(state).filter(s => s.confirmed && s.comment).length,
      pending:       total - confirmed,
    }},
    items: CHANGES.map((ch, i) => ({{
      index:     i + 1,
      lang_code: ch.lang_code || '',
      find:      ch.find      || '',
      replace:   ch.replace   || '',
      note:      ch.note      || '',
      confirmed: state[i].confirmed,
      comment:   state[i].comment,
      page:      ch.page      || '',
    }})),
    not_found: NOT_FOUND,
  }};

  const blob     = new Blob([JSON.stringify(reply, null, 2)], {{ type: 'application/json' }});
  const url      = URL.createObjectURL(blob);
  const a        = document.createElement('a');
  const baseName = FILENAME.replace(/\\.idml$/i, '');
  const replyName = `PM確認回覆_${{baseName}}_${{new Date().toISOString().slice(0,10)}}.json`;
  a.href         = url;
  a.download     = replyName;
  a.click();
  URL.revokeObjectURL(url);

  // 顯示完成畫面
  document.getElementById('done-overlay').style.display = 'flex';
}}

function esc(str) {{
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}}

// 初始化
buildCards();
updateProgress();
</script>
</body>
</html>"""

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    return output_path


def _esc(s: str) -> str:
    if not s:
        return ''
    return (str(s)
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;'))
