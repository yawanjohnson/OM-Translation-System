/* ═══════════════════════════════════════════════════════
   OM 多語言管理系統 - Frontend JavaScript
   ═══════════════════════════════════════════════════════ */

// ──────────────────────────────────────────────────────
// 語言代碼 & 名稱
// ──────────────────────────────────────────────────────
const LANG_CODES = [
  'ENG','GER','DUT','DAN','FRE','SPA','ITA','GRK',
  'POL','PRB','RUS','CHT','JPN','KOR','VTM','THI','ARB','TRK','CHS'
];
const LANG_NAMES = {};

// ──────────────────────────────────────────────────────
// 全域狀態
// ──────────────────────────────────────────────────────
let patchState = {
  tmpId: null,
  originalFilename: null,
  instructions: [],
  runId: null,
  idmlFile: null,
  excelFile: null,
};

let applyState = {
  tmpId: null,
  originalFilename: null,
  selectedLang: null,
  runId: null,
  idmlFile: null,
  excelFile: null,
};

let idmlImportState = {
  tmpId: null,
  langCode: null,
};

let dbState = {
  page: 1,
  perPage: 50,
  total: 0,
  query: '',
  lang: '',
};

let editingId = null;
let searchTimer = null;

// ──────────────────────────────────────────────────────
// 初始化
// ──────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  await loadLangInfo();
  initLangBadges();
  initLangSelects();
  initApplyLangSelector();
  loadDBStats();
  searchDB();
  updateConflictBadge();
});

async function loadLangInfo() {
  try {
    const res = await fetch('/api/lang-info');
    const data = await res.json();
    Object.assign(LANG_NAMES, data.names);
  } catch (e) { /* fallback */ }
}

function initLangBadges() {
  const container = document.getElementById('lang-badges');
  LANG_CODES.forEach(code => {
    const b = document.createElement('span');
    b.className = 'lang-badge';
    b.textContent = code;
    container.appendChild(b);
  });
}

function initLangSelects() {
  // 搜尋語言選擇
  const sel = document.getElementById('db-search-lang');
  LANG_CODES.forEach(code => {
    const opt = document.createElement('option');
    opt.value = code;
    opt.textContent = `${code} ${LANG_NAMES[code] || ''}`;
    sel.appendChild(opt);
  });

  // IDML 匯入語言選擇
  const isel = document.getElementById('idml-import-lang');
  LANG_CODES.forEach(code => {
    const opt = document.createElement('option');
    opt.value = code;
    opt.textContent = `${code} — ${LANG_NAMES[code] || code}`;
    isel.appendChild(opt);
  });
}

function initApplyLangSelector() {
  const container = document.getElementById('apply-lang-selector');
  LANG_CODES.forEach(code => {
    const btn = document.createElement('button');
    btn.className = 'lang-btn';
    btn.dataset.code = code;
    btn.title = LANG_NAMES[code] || code;
    btn.textContent = code;
    btn.onclick = () => selectApplyLang(code, btn);
    container.appendChild(btn);
  });
}

// ──────────────────────────────────────────────────────
// TAB 切換
// ──────────────────────────────────────────────────────
const TAB_TITLES = {
  patch:    'OM Content Updates',
  database: '多語言資料庫',
  import:   '匯入資料',
  apply:    '套用語言到 IDML',
  conflict: '翻譯衝突管理',
  extract:  '智慧文字提取與對照',
};

document.querySelectorAll('.nav-item').forEach(btn => {
  btn.addEventListener('click', () => {
    const tab = btn.dataset.tab;
    document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(`tab-${tab}`).classList.add('active');
    document.getElementById('topbar-title').textContent = TAB_TITLES[tab];
    if (tab === 'database') { searchDB(); loadDBStats(); }
    if (tab === 'conflict') {
      switchConflictSubTab('pending');
      loadConflictLogLanguages();
    }
    if (tab === 'extract') {
      initExtractWorkspace();
    }
  });
});

// ──────────────────────────────────────────────────────
// DRAG & DROP 處理
// ──────────────────────────────────────────────────────
function handleDrop(event, type) {
  event.preventDefault();
  document.querySelectorAll('.dropzone').forEach(d => d.classList.remove('drag-over'));
  const files = event.dataTransfer.files;
  if (!files.length) return;
  const file = files[0];

  if (type === 'idml') {
    uploadIdmlFromFile(file);
  } else if (type === 'instr') {
    uploadInstructionsFromFile(file);
  } else if (type === 'excel-import') {
    importExcelFromFile(file);
  } else if (type === 'idml-import') {
    importIdmlPreviewFromFile(file);
  } else if (type === 'apply') {
    uploadApplyIdmlFromFile(file);
  } else if (type === 'pm-reply') {
    uploadPMReplyFromFile(file);
  } else if (type === 'extract') {
    handleExtractUploadFromFiles(files);
  }
}

// ──────────────────────────────────────────────────────
// TAB 1: IDML 修正
// ──────────────────────────────────────────────────────
function uploadIdml(input) { if (input.files[0]) uploadIdmlFromFile(input.files[0]); }

async function uploadIdmlFromFile(file) {
  showLoading('上傳 IDML 中...');
  try {
    const fd = new FormData();
    fd.append('file', file);
    const res = await fetch('/api/patch/upload-idml', { method: 'POST', body: fd });
    const data = await res.json();
    hideLoading();
    if (!data.ok) { showToast('❌ ' + data.error, 'error'); return; }

    patchState.tmpId = data.tmp_id;
    patchState.originalFilename = file.name;

    const dz = document.getElementById('dz-idml');
    dz.style.borderColor = 'var(--success-text)';
    dz.querySelector('.dz-label').textContent = '✅ ' + file.name;
    dz.querySelector('.dz-sub').textContent = '';

    const info = document.getElementById('idml-info');
    info.style.display = 'block';
    document.getElementById('idml-filename').textContent = file.name;
    document.getElementById('idml-stories').textContent = (data.info?.story_count || '?') + ' 個 Story';
    document.getElementById('idml-version').textContent = 'DOMVersion ' + (data.info?.dom_version || '?');

    showToast('✅ IDML 上傳成功');
    checkPatchReady();
  } catch (e) {
    hideLoading();
    showToast('❌ 上傳失敗：' + e.message, 'error');
  }
}

function uploadInstructions(input) { if (input.files[0]) uploadInstructionsFromFile(input.files[0]); }

async function uploadInstructionsFromFile(file) {
  showLoading('解析修改指示中...');
  try {
    const fd = new FormData();
    fd.append('file', file);
    const res = await fetch('/api/patch/upload-instructions', { method: 'POST', body: fd });
    const data = await res.json();
    hideLoading();
    if (!data.ok) { showToast('❌ ' + data.error, 'error'); return; }

    patchState.instructions = data.instructions;

    const dz = document.getElementById('dz-instr');
    dz.style.borderColor = 'var(--success-text)';
    dz.querySelector('.dz-label').textContent = '✅ ' + file.name;
    dz.querySelector('.dz-sub').textContent = `共 ${data.count} 條修改指示`;

    document.getElementById('instr-summary').style.display = 'block';
    document.getElementById('instr-count-tag').textContent = `${data.count} 條指示`;

    renderInstrTable(data.instructions);
    showToast(`✅ 已解析 ${data.count} 條修改指示`);
    checkPatchReady();
  } catch (e) {
    hideLoading();
    showToast('❌ ' + e.message, 'error');
  }
}

function checkPatchReady() {
  const ready = patchState.tmpId && patchState.instructions.length > 0;
  const btn = document.getElementById('btn-run-patch');
  if (btn) btn.disabled = !ready;
}

function renderInstrTable(instructions) {
  const panel = document.getElementById('instr-preview-panel');
  panel.style.display = 'block';
  const tbody = document.getElementById('instr-tbody');
  tbody.innerHTML = '';

  instructions.forEach((instr, i) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${i + 1}</td>
      <td><span class="tag tag-blue">${esc(instr.lang_code)}</span></td>
      <td><span class="cell-truncate mono text-del">${esc(instr.find)}</span></td>
      <td><span class="cell-truncate mono text-green">${esc(instr.replace)}</span></td>
      <td>${esc(instr.note)}</td>
      <td>
        <button class="action-btn del" onclick="removeInstruction(${i})" title="移除此條">🗑</button>
      </td>
    `;
    tbody.appendChild(tr);
  });

  const btn = document.getElementById('btn-run-patch');
  if (btn) btn.disabled = !(patchState.tmpId && instructions.length > 0);
}

function removeInstruction(idx) {
  patchState.instructions.splice(idx, 1);
  renderInstrTable(patchState.instructions);
  document.getElementById('instr-count-tag').textContent = `${patchState.instructions.length} 條指示`;
}

async function runPatch() {
  if (!patchState.tmpId) { showToast('請先上傳 IDML 檔案', 'error'); return; }
  if (!patchState.instructions.length) { showToast('請先上傳修改指示', 'error'); return; }

  showLoading('執行 IDML 修正中...\n正在搜尋並替換文字，請稍候');
  try {
    const res = await fetch('/api/patch/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        tmp_id: patchState.tmpId,
        instructions: patchState.instructions,
        original_filename: patchState.originalFilename,
      }),
    });
    const data = await res.json();
    hideLoading();

    if (!data.ok) { showToast('❌ ' + data.error, 'error'); return; }

    patchState.runId = data.run_id;
    patchState.idmlFile = data.idml_file;
    patchState.excelFile = data.excel_file;

    renderPatchResult(data);
    showToast(`✅ 修正完成！${data.changes.length} 處成功 / ${data.not_found.length} 條未找到`);
  } catch (e) {
    hideLoading();
    showToast('❌ ' + e.message, 'error');
  }
}

function renderPatchResult(data) {
  const panel = document.getElementById('patch-result-panel');
  panel.style.display = 'block';
  panel.scrollIntoView({ behavior: 'smooth', block: 'start' });

  // 儲存供 PM 確認使用
  patchState.lastChanges   = data.changes;
  patchState.lastNotFound  = data.not_found;
  patchState.layout        = data.layout;

  document.getElementById('res-success-count').textContent = data.changes.length;
  document.getElementById('res-error-count').textContent   = data.not_found.length;

  // 顯示 PM 確認頁、驗證按鈕、PDF 匠出按鈕
  const pmBtn = document.getElementById('dl-pm-html-btn');
  if (pmBtn) pmBtn.style.display = 'inline-flex';
  const pdfBtn = document.getElementById('export-pdf-btn');
  if (pdfBtn) pdfBtn.style.display = 'inline-flex';
  const verifyBtn = document.getElementById('btn-verify');
  if (verifyBtn) verifyBtn.style.display = 'inline-flex';

  // 未找到
  const notFoundSec = document.getElementById('not-found-section');
  if (data.not_found.length) {
    notFoundSec.style.display = 'block';
    const tbody = document.getElementById('not-found-tbody');
    tbody.innerHTML = '';
    data.not_found.forEach((nf, i) => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${i+1}</td>
        <td><span class="tag tag-orange">${esc(nf.lang_code)}</span></td>
        <td><span class="mono" style="color:var(--error-text)">${esc(nf.find)}</span></td>
        <td class="mono">${esc(nf.replace)}</td>
        <td>${esc(nf.note)}</td>
      `;
      tbody.appendChild(tr);
    });
  } else {
    notFoundSec.style.display = 'none';
  }

  // 成功清單
  const tbody2 = document.getElementById('success-tbody');
  tbody2.innerHTML = '';
  data.changes.forEach((c, i) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${i+1}</td>
      <td><span class="tag tag-green">${esc(c.lang_code)}</span></td>
      <td><span class="mono text-del">${esc(c.find)}</span></td>
      <td><span class="mono text-green">${esc(c.replace)}</span></td>
      <td>${esc(c.note)}</td>
    `;
    tbody2.appendChild(tr);
  });

  // 清除舊驗證結果
  const verifySec = document.getElementById('verify-section');
  if (verifySec) verifySec.style.display = 'none';
}

// ──────────────────────────────────────────────────────
// 驗證置換正確性
// ──────────────────────────────────────────────────────
async function runVerify() {
  if (!patchState.idmlFile) { showToast('請先執行修正', 'error'); return; }
  if (!patchState.lastChanges?.length) { showToast('沒有可驗證的修改記錄', 'error'); return; }

  const btn = document.getElementById('btn-verify');
  if (btn) { btn.disabled = true; btn.textContent = '🔄 驗證中...'; }

  try {
    const res = await fetch('/api/patch/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        idml_file: patchState.idmlFile,
        changes: patchState.lastChanges,
      }),
    });
    const data = await res.json();

    if (!data.ok) {
      showToast('❌ 驗證失敗：' + data.error, 'error');
    } else {
      renderVerifyResult(data);
      if (data.all_pass) {
        showToast(`✅ 驗證通過！全部 ${data.passed} 條置換均正確`);
      } else {
        showToast(`⚠️ 驗證完成：${data.passed} 通過 / ${data.failed} 失敗`, 'error');
      }
    }
  } catch (e) {
    showToast('❌ ' + e.message, 'error');
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = '🔍 驗證置換正確性'; }
  }
}

function renderVerifyResult(data) {
  const verifySec = document.getElementById('verify-section');
  verifySec.style.display = 'block';
  verifySec.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

  // 摘要列
  const summary = document.getElementById('verify-summary');
  const allIcon = data.all_pass ? '✅' : '❌';
  summary.innerHTML = `
    <div class="result-stat ${data.all_pass ? 'success' : 'error'}" style="min-width:100px">
      <span class="rs-num">${data.passed}</span>
      <span class="rs-label">驗證通過</span>
    </div>
    ${data.failed > 0 ? `
    <div class="result-stat error" style="min-width:100px">
      <span class="rs-num">${data.failed}</span>
      <span class="rs-label">驗證失敗</span>
    </div>` : ''}
    <div style="display:flex;align-items:center;gap:6px;padding:8px 14px;background:${data.all_pass ? 'rgba(16,185,129,0.08)' : 'rgba(239,68,68,0.08)'};border-radius:10px;border:1px solid ${data.all_pass ? 'rgba(16,185,129,0.3)' : 'rgba(239,68,68,0.3)'}">
      <span style="font-size:20px">${allIcon}</span>
      <span style="font-size:13px;font-weight:600;color:${data.all_pass ? 'var(--success-text)' : 'var(--error-text)'}">
        ${data.all_pass ? '所有置換均正確！' : '有部分置換未通過驗證'}
      </span>
    </div>
  `;

  // 詳細表格
  const tbody = document.getElementById('verify-tbody');
  tbody.innerHTML = '';
  data.results.forEach((r, i) => {
    const tr = document.createElement('tr');
    let badge, rowStyle;
    if (r.passed) {
      badge = '<span class="tag tag-green">✅ 通過</span>';
      rowStyle = '';
    } else if (!r.found) {
      badge = '<span class="tag tag-orange">❌ 未找到</span>';
      rowStyle = 'background:rgba(239,68,68,0.04)';
    } else if (r.orig_still_present) {
      badge = '<span class="tag tag-orange">⚠️ 原文殘留</span>';
      rowStyle = 'background:rgba(245,158,11,0.06)';
    } else {
      badge = '<span class="tag tag-orange">❌ 失敗</span>';
      rowStyle = 'background:rgba(239,68,68,0.04)';
    }
    tr.style.cssText = rowStyle;
    tr.innerHTML = `
      <td>${i+1}</td>
      <td><span class="tag tag-blue">${esc(r.lang_code)}</span></td>
      <td><span class="mono text-del" style="font-size:12px">${esc(r.find)}</span></td>
      <td><span class="mono text-green" style="font-size:12px">${esc(r.replace)}</span></td>
      <td style="text-align:center;font-weight:700;color:${r.count > 0 ? 'var(--success-text)' : 'var(--error-text)'}">${r.count}</td>
      <td>${badge}</td>
      <td style="font-size:11px;color:var(--text-muted)">${esc(r.note)}${r.orig_still_present ? ' <em style="color:var(--warning-text)">• 原文仍存在</em>' : ''}</td>
    `;
    tbody.appendChild(tr);
  });
}

// ──────────────────────────────────────────────────────
// PM 確認頁產生 & 回覆解析
// ──────────────────────────────────────────────────────
async function generatePMReview() {
  if (!patchState.runId) { showToast('請先執行修正', 'error'); return; }
  showLoading('產生 PM 確認頁...');
  try {
    const res = await fetch('/api/pm-review/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        run_id:            patchState.runId,
        changes:           patchState.lastChanges || [],
        not_found:         patchState.lastNotFound || [],
        original_filename: patchState.originalFilename,
        layout:            patchState.layout,
      }),
    });
    const data = await res.json();
    hideLoading();
    if (!data.ok) { showToast('❌ ' + data.error, 'error'); return; }

    // 直接下載 HTML
    window.location.href = `/api/patch/download/${encodeURIComponent(data.html_file)}`;

    // 顯示 PM 回覆解析區
    document.getElementById('pm-reply-panel').style.display = 'block';
    showToast('✅ PM 確認頁已下載！傳給 PM 後，等 PM 回傳 JSON 再上傳下方');
  } catch (e) {
    hideLoading();
    showToast('❌ ' + e.message, 'error');
  }
}
async function exportRealPDF() {
  if (!patchState.idmlFile) { showToast('請先執行修正', 'error'); return; }
  
  showLoading('正在呼叫本機 InDesign 轉存 PDF 中...\n這可能需要 10-20 秒，請勿關閉網頁。');
  try {
    const res = await fetch('/api/patch/export-pdf', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        idml_file: patchState.idmlFile
      })
    });
    const data = await res.json();
    hideLoading();
    if (!data.ok) {
      showToast('❌ ' + data.error, 'error');
      alert('PDF 匯出失敗：' + data.error + '\n\n【排解提示】\n1. 請確認您的 Mac 電腦上已安裝 Adobe InDesign。\n2. 請先打開 InDesign 應用程式後，再次點擊此按鈕。');
      return;
    }
    
    // 下載 PDF
    window.location.href = `/api/patch/download/${encodeURIComponent(data.pdf_file)}`;
    showToast('✅ PDF 匯出成功並已開始下載！');
  } catch (e) {
    hideLoading();
    showToast('❌ 連線失敗：' + e.message, 'error');
  }
}
function uploadPMReply(input) { if (input.files[0]) uploadPMReplyFromFile(input.files[0]); }

async function uploadPMReplyFromFile(file) {
  showLoading('解析 PM 回覆中...');
  const fd = new FormData();
  fd.append('file', file);
  try {
    const res  = await fetch('/api/pm-review/parse-reply', { method: 'POST', body: fd });
    const data = await res.json();
    hideLoading();
    if (!data.ok) { showToast('❌ ' + data.error, 'error'); return; }

    renderPMReplyResult(data);
    showToast('✅ PM 回覆解析完成');
  } catch (e) {
    hideLoading();
    showToast('❌ ' + e.message, 'error');
  }
}

function renderPMReplyResult(data) {
  const el = document.getElementById('pm-reply-result');
  const s  = data.summary;
  const meta = data.meta || {};

  let html = `
    <div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:16px">
      <div class="result-stat success" style="min-width:100px">
        <span class="rs-num">${s.confirmed}</span>
        <span class="rs-label">已確認</span>
      </div>
      <div class="result-stat" style="border-color:rgba(245,158,11,0.5);background:rgba(245,158,11,0.08);min-width:100px">
        <span class="rs-num" style="color:#d29922">${s.with_comments}</span>
        <span class="rs-label">確認含意見</span>
      </div>
      <div class="result-stat error" style="min-width:100px">
        <span class="rs-num">${s.needs_redo}</span>
        <span class="rs-label">需要重改</span>
      </div>
    </div>
  `;

  // 需要重改的清單
  if (data.needs_redo?.length) {
    html += `<div class="section-divider">🔄 以下條目 PM 尚未確認（需重改或確認）</div>
    <div class="table-wrap"><table class="data-table">
      <thead><tr><th>#</th><th>語言</th><th>原文</th><th>修改為</th><th>備註</th></tr></thead>
      <tbody>`;
    data.needs_redo.forEach((it, i) => {
      html += `<tr>
        <td>${it.index || i+1}</td>
        <td><span class="tag tag-orange">${esc(it.lang_code)}</span></td>
        <td class="mono">${esc(it.find)}</td>
        <td class="mono">${esc(it.replace)}</td>
        <td>${esc(it.note)}</td>
      </tr>`;
    });
    html += `</tbody></table></div>`;
  }

  // 有意見的清單
  if (data.with_comments?.length) {
    html += `<div class="section-divider">💬 PM 有意見的條目</div>
    <div class="table-wrap"><table class="data-table">
      <thead><tr><th>#</th><th>語言</th><th>修改後文字</th><th>PM 意見</th></tr></thead>
      <tbody>`;
    data.with_comments.forEach((it, i) => {
      html += `<tr>
        <td>${it.index || i+1}</td>
        <td><span class="tag tag-blue">${esc(it.lang_code)}</span></td>
        <td class="mono">${esc(it.replace)}</td>
        <td style="color:var(--warning-text)">${esc(it.comment)}</td>
      </tr>`;
    });
    html += `</tbody></table></div>`;
  }

  if (!data.needs_redo?.length && !data.with_comments?.length) {
    html += `<div class="alert alert-success">🎉 PM 已確認所有修改，無需重改！</div>`;
  }

  el.innerHTML = html;
}

function downloadResult(type) {
  let filename;
  if (type === 'idml')        filename = patchState.idmlFile;
  else if (type === 'excel')  filename = patchState.excelFile;
  else if (type === 'apply-idml')   filename = applyState.idmlFile;
  else if (type === 'apply-excel')  filename = applyState.excelFile;

  if (!filename) { showToast('檔案尚未產生', 'error'); return; }
  window.location.href = `/api/patch/download/${encodeURIComponent(filename)}`;
}

// ──────────────────────────────────────────────────────
// TAB 2: 多語言資料庫
// ──────────────────────────────────────────────────────
function debounceSearch() {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(searchDB, 300);
}

function clearSearch() {
  document.getElementById('db-search-input').value = '';
  document.getElementById('db-search-lang').value = '';
  dbState.query = '';
  dbState.lang  = '';
  dbState.page  = 1;
  searchDB();
}

async function searchDB() {
  const q    = document.getElementById('db-search-input').value;
  const lang = document.getElementById('db-search-lang').value;
  dbState.query = q;
  dbState.lang  = lang;
  dbState.page  = 1;
  await fetchAndRenderDB();
}

async function fetchAndRenderDB() {
  const params = new URLSearchParams({
    q:        dbState.query,
    lang:     dbState.lang,
    page:     dbState.page,
    per_page: dbState.perPage,
  });
  try {
    const res  = await fetch('/api/translations?' + params);
    const data = await res.json();
    dbState.total = data.total;
    renderDBTable(data.items);
    renderPagination(data.total, data.page, data.page_size);
  } catch (e) {
    document.getElementById('db-tbody').innerHTML =
      `<tr><td colspan="99" class="empty-cell">載入失敗：${e.message}</td></tr>`;
  }
}

function renderDBTable(items) {
  // 動態建立表頭（顯示有資料的語言欄位）
  const thead = document.getElementById('db-thead');
  const tbody = document.getElementById('db-tbody');

  // 固定顯示欄位：id, product, chapter, ENG, 其他語言（有資料者）
  const visibleLangs = ['ENG', ...LANG_CODES.filter(c => c !== 'ENG')];

  // Build header once
  thead.innerHTML = `
    <tr>
      <th style="width:50px">ID</th>
      <th style="width:100px">產品</th>
      <th style="width:100px">章節</th>
      ${visibleLangs.map(c => `<th style="min-width:120px">${c}</th>`).join('')}
      <th style="width:90px">操作</th>
    </tr>
  `;

  tbody.innerHTML = '';

  if (!items.length) {
    tbody.innerHTML = `<tr><td colspan="99" class="empty-cell">找不到資料</td></tr>`;
    return;
  }

  items.forEach(row => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td style="color:var(--text-muted);font-size:11px">${row.id}</td>
      <td>${esc(row.product || '')}</td>
      <td>${esc(row.chapter || '')}</td>
      ${visibleLangs.map(c => `
        <td title="${esc(row[c] || '')}">
          <span class="cell-truncate" style="max-width:200px">${esc(row[c] || '')}</span>
        </td>
      `).join('')}
      <td>
        <button class="action-btn" onclick="openEditModal(${row.id})" title="編輯">✏️</button>
        <button class="action-btn del" onclick="deleteEntry(${row.id})" title="刪除">🗑</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function renderPagination(total, page, perPage) {
  const container = document.getElementById('db-pagination');
  container.innerHTML = '';
  const totalPages = Math.ceil(total / perPage);
  if (totalPages <= 1) return;

  const info = document.createElement('span');
  info.className = 'page-info';
  info.textContent = `共 ${total} 筆`;
  container.appendChild(info);

  const maxBtns = 7;
  let start = Math.max(1, page - Math.floor(maxBtns / 2));
  let end   = Math.min(totalPages, start + maxBtns - 1);
  if (end - start < maxBtns - 1) start = Math.max(1, end - maxBtns + 1);

  if (start > 1) addPageBtn(container, 1, page);
  if (start > 2) { const s = document.createElement('span'); s.className = 'page-info'; s.textContent = '...'; container.appendChild(s); }

  for (let p = start; p <= end; p++) addPageBtn(container, p, page);

  if (end < totalPages - 1) { const s = document.createElement('span'); s.className = 'page-info'; s.textContent = '...'; container.appendChild(s); }
  if (end < totalPages) addPageBtn(container, totalPages, page);
}

function addPageBtn(container, p, current) {
  const btn = document.createElement('button');
  btn.className = 'page-btn' + (p === current ? ' active' : '');
  btn.textContent = p;
  btn.onclick = () => { dbState.page = p; fetchAndRenderDB(); };
  container.appendChild(btn);
}

async function loadDBStats() {
  try {
    const res  = await fetch('/api/translations/stats');
    const data = await res.json();
    document.getElementById('stats-count').textContent = data.total.toLocaleString();

    const row = document.getElementById('stats-row');
    row.innerHTML = '';
    LANG_CODES.forEach(code => {
      const cnt = data.by_language[code] || 0;
      const chip = document.createElement('div');
      chip.className = 'stat-chip' + (cnt > 0 ? ' has-data' : '');
      chip.innerHTML = `<span class="stat-chip-code">${code}</span><span class="stat-chip-count">${cnt}</span>`;
      chip.title = `${LANG_NAMES[code] || code}：${cnt} 筆`;
      row.appendChild(chip);
    });
  } catch (e) { /* silent */ }
}

// ── 新增 / 編輯 Modal ──
function openAddModal() {
  editingId = null;
  document.getElementById('modal-edit-title').textContent = '新增翻譯條目';
  document.getElementById('edit-product').value = '';
  document.getElementById('edit-chapter').value = '';
  buildLangFields({});
  openModal('modal-edit');
}

async function openEditModal(id) {
  editingId = id;
  document.getElementById('modal-edit-title').textContent = `編輯條目 #${id}`;
  try {
    const res  = await fetch(`/api/translations/${id}`);
    const data = await res.json();
    document.getElementById('edit-product').value = data.product || '';
    document.getElementById('edit-chapter').value = data.chapter || '';
    buildLangFields(data);
    openModal('modal-edit');
  } catch (e) { showToast('❌ 無法載入', 'error'); }
}

function buildLangFields(data) {
  const container = document.getElementById('lang-fields');
  container.innerHTML = '';
  LANG_CODES.forEach(code => {
    const fg = document.createElement('div');
    fg.className = 'form-group';
    fg.innerHTML = `
      <label class="form-label">${code} — ${LANG_NAMES[code] || code}</label>
      <textarea id="lang-field-${code}" class="form-textarea" rows="2">${esc(data[code] || '')}</textarea>
    `;
    container.appendChild(fg);
  });
}

async function saveEntry() {
  const payload = {
    product: document.getElementById('edit-product').value.trim(),
    chapter: document.getElementById('edit-chapter').value.trim(),
  };
  LANG_CODES.forEach(code => {
    const el = document.getElementById(`lang-field-${code}`);
    if (el) payload[code] = el.value.trim();
  });

  try {
    let res;
    if (editingId) {
      res = await fetch(`/api/translations/${editingId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
    } else {
      res = await fetch('/api/translations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
    }
    const data = await res.json();
    if (data.ok !== false) {
      closeModal('modal-edit');
      showToast(editingId ? '✅ 已更新' : '✅ 已新增');
      fetchAndRenderDB();
      loadDBStats();
    } else {
      showToast('❌ ' + (data.error || '儲存失敗'), 'error');
    }
  } catch (e) { showToast('❌ ' + e.message, 'error'); }
}

async function deleteEntry(id) {
  if (!confirm(`確定要刪除條目 #${id}？`)) return;
  try {
    const res  = await fetch(`/api/translations/${id}`, { method: 'DELETE' });
    const data = await res.json();
    if (data.ok) {
      showToast('已刪除');
      fetchAndRenderDB();
      loadDBStats();
    }
  } catch (e) { showToast('❌ ' + e.message, 'error'); }
}

function exportDB() {
  showToast('⬇ 匯出中...');
  window.location.href = '/api/export/excel';
}

function downloadDbTemplate() {
  window.location.href = '/api/export/template';
}

// ──────────────────────────────────────────────────────
// TAB 3: 匯入
// ──────────────────────────────────────────────────────
function importExcel(input) { if (input.files[0]) importExcelFromFile(input.files[0]); }

async function importExcelFromFile(file) {
  showLoading('匯入 Excel 中...');
  const fd = new FormData();
  fd.append('file', file);
  try {
    const res  = await fetch('/api/import/excel-with-conflicts', { method: 'POST', body: fd });
    const data = await res.json();
    hideLoading();
    const el = document.getElementById('excel-import-result');
    if (data.ok) {
      let html = `<div class="alert alert-success">
        ✅ 處理完成：已匯入/更新 ${data.imported_count} 筆。
      </div>`;
      if (data.conflict_count > 0) {
        html += `<div class="alert alert-error mt" style="text-align: left; background: rgba(248,81,73,0.1); border-left: 4px solid var(--error-text); padding: 12px; border-radius: 4px;">
          ⚠️ 有 <strong>${data.conflict_count}</strong> 筆翻譯與資料庫現存內容發生衝突，已被移至左側選單的 <strong style="color: var(--error-text);">「衝突管理」</strong> 佇列，待您稍後解決。
        </div>`;
      }
      if (data.skipped_details && data.skipped_details.length > 0) {
        html += `<div class="import-skipped-details mt12" style="background: rgba(245, 158, 11, 0.1); border-left: 4px solid var(--warning-text); padding: 12px; border-radius: 4px; max-height: 250px; overflow-y: auto; text-align: left;">
          <h4 style="margin: 0 0 8px 0; color: var(--warning-text); font-size: 14px; font-weight: bold; display: flex; align-items: center; gap: 6px;">
            ⚠️ 略過項目明細：
          </h4>
          <ul style="margin: 0; padding-left: 20px; font-size: 13px; color: var(--text-primary); line-height: 1.6; list-style-type: disc;">
            ${data.skipped_details.map(detail => `<li>${detail}</li>`).join('')}
          </ul>
        </div>`;
      }
      el.innerHTML = html;
      loadDBStats();
      updateConflictBadge();
      showToast('✅ Excel 匯入成功');
    } else {
      el.innerHTML = `<div class="alert alert-error">❌ ${data.error}</div>`;
    }
  } catch (e) {
    hideLoading();
    document.getElementById('excel-import-result').innerHTML = `<div class="alert alert-error">❌ ${e.message}</div>`;
  }
}

function importIdmlPreview(input) { if (input.files[0]) importIdmlPreviewFromFile(input.files[0]); }

async function importIdmlPreviewFromFile(file) {
  const lang = document.getElementById('idml-import-lang').value;
  if (!lang) { showToast('請先選擇語言代碼', 'error'); return; }

  showLoading('萃取 IDML 文字中...');
  const fd = new FormData();
  fd.append('file', file);
  fd.append('lang_code', lang);
  try {
    const res  = await fetch('/api/import/idml-preview', { method: 'POST', body: fd });
    const data = await res.json();
    hideLoading();

    const el = document.getElementById('idml-import-result');
    if (!data.ok) {
      el.innerHTML = `<div class="alert alert-error">❌ ${data.error}</div>`;
      return;
    }

    idmlImportState.tmpId    = data.tmp_id;
    idmlImportState.langCode = lang;

    el.innerHTML = `<div class="alert alert-info">
      共萃取 <strong>${data.total}</strong> 個段落（${data.lang_code}）
    </div>`;

    // 顯示預覽
    const prevSec  = document.getElementById('idml-preview-section');
    const prevTbody = document.getElementById('idml-preview-tbody');
    prevSec.style.display = 'block';
    prevTbody.innerHTML = '';

    data.preview.slice(0, 50).forEach((row, i) => {
      const text = row[lang] || '';
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${i+1}</td>
        <td><span class="cell-truncate">${esc(text)}</span></td>
        <td style="color:var(--text-muted);font-size:11px">${esc(row.chapter || '')}</td>
      `;
      prevTbody.appendChild(tr);
    });
  } catch (e) {
    hideLoading();
    document.getElementById('idml-import-result').innerHTML = `<div class="alert alert-error">❌ ${e.message}</div>`;
  }
}

async function confirmIdmlImport() {
  if (!idmlImportState.tmpId) { showToast('請先上傳 IDML', 'error'); return; }

  const product = document.getElementById('idml-import-product').value.trim();
  showLoading('儲存到資料庫中...');
  try {
    const res = await fetch('/api/import/idml-confirm', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        tmp_id:    idmlImportState.tmpId,
        lang_code: idmlImportState.langCode,
        product:   product,
      }),
    });
    const data = await res.json();
    hideLoading();

    const el = document.getElementById('idml-import-result');
    if (data.ok) {
      el.innerHTML = `<div class="alert alert-success">
        ✅ 匯入完成：新增 ${data.added} 筆 / 更新 ${data.updated} 筆 / 略過 ${data.skipped} 筆
      </div>`;
      document.getElementById('idml-preview-section').style.display = 'none';
      loadDBStats();
      showToast('✅ IDML 文字已存入資料庫');
    } else {
      el.innerHTML = `<div class="alert alert-error">❌ ${data.error}</div>`;
    }
  } catch (e) {
    hideLoading();
    document.getElementById('idml-import-result').innerHTML = `<div class="alert alert-error">❌ ${e.message}</div>`;
  }
}

// ──────────────────────────────────────────────────────
// TAB 4: 套用語言
// ──────────────────────────────────────────────────────
function uploadApplyIdml(input) { if (input.files[0]) uploadApplyIdmlFromFile(input.files[0]); }

async function uploadApplyIdmlFromFile(file) {
  showLoading('上傳 IDML...');
  const fd = new FormData();
  fd.append('file', file);
  try {
    const res  = await fetch('/api/patch/upload-idml', { method: 'POST', body: fd });
    const data = await res.json();
    hideLoading();
    if (!data.ok) { showToast('❌ ' + data.error, 'error'); return; }

    applyState.tmpId = data.tmp_id;
    applyState.originalFilename = file.name;

    const infoDiv = document.getElementById('apply-idml-info');
    infoDiv.style.display = 'block';
    document.getElementById('apply-idml-filename').textContent = file.name;

    const dz = document.getElementById('dz-apply');
    dz.style.borderColor = 'var(--success-text)';
    dz.querySelector('.dz-sub')?.remove();
    dz.querySelector('button').textContent = '✅ ' + file.name;

    checkApplyReady();
    showToast('✅ IDML 上傳成功');
  } catch (e) {
    hideLoading();
    showToast('❌ ' + e.message, 'error');
  }
}

function selectApplyLang(code, btn) {
  document.querySelectorAll('#apply-lang-selector .lang-btn').forEach(b => b.classList.remove('selected'));
  btn.classList.add('selected');
  applyState.selectedLang = code;
  checkApplyReady();
}

function checkApplyReady() {
  const btn = document.getElementById('btn-apply-run');
  btn.disabled = !(applyState.tmpId && applyState.selectedLang);
}

async function runApply() {
  if (!applyState.tmpId)       { showToast('請先上傳 IDML', 'error'); return; }
  if (!applyState.selectedLang){ showToast('請選擇目標語言', 'error'); return; }

  showLoading(`套用 ${applyState.selectedLang} 翻譯中...`);
  try {
    const res = await fetch('/api/apply/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        tmp_id:            applyState.tmpId,
        lang_code:         applyState.selectedLang,
        original_filename: applyState.originalFilename,
      }),
    });
    const data = await res.json();
    hideLoading();
    if (!data.ok) { showToast('❌ ' + data.error, 'error'); return; }

    applyState.idmlFile  = data.idml_file;
    applyState.excelFile = data.excel_file;

    document.getElementById('apply-result').style.display = 'block';
    document.getElementById('apply-success-count').textContent = data.applied;
    document.getElementById('apply-notfound-count').textContent = data.not_found;
    showToast(`✅ 套用完成！${data.applied} 段落已替換`);
  } catch (e) {
    hideLoading();
    showToast('❌ ' + e.message, 'error');
  }
}

// ──────────────────────────────────────────────────────
// PM 範本
// ──────────────────────────────────────────────────────
function downloadPMTemplate() {
  closeModal('modal-pm-template');
  window.location.href = '/api/patch/instruction-template';
}

// ──────────────────────────────────────────────────────
// MODAL 工具
// ──────────────────────────────────────────────────────
function openModal(id) {
  document.getElementById(id).style.display = 'flex';
  document.body.style.overflow = 'hidden';
}

function closeModal(id) {
  document.getElementById(id).style.display = 'none';
  document.body.style.overflow = '';
}

// 點擊遮罩關閉
document.querySelectorAll('.modal-overlay').forEach(overlay => {
  overlay.addEventListener('click', e => {
    if (e.target === overlay) closeModal(overlay.id);
  });
});

// ESC 關閉與 Ctrl+Z 復原快捷鍵
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal-overlay').forEach(m => {
      if (m.style.display !== 'none') closeModal(m.id);
    });
  }
  
  // Ctrl+Z or Cmd+Z for Undo in Smart Extractor
  const isZ = e.key === 'z' || e.key === 'Z';
  const isMetaOrCtrl = e.metaKey || e.ctrlKey;
  if (isZ && isMetaOrCtrl) {
    const extractTab = document.getElementById('tab-extract');
    if (extractTab && extractTab.classList.contains('active')) {
      // Do not block default browser undo when user is typing inside textareas or inputs
      if (document.activeElement.tagName !== 'TEXTAREA' && document.activeElement.tagName !== 'INPUT') {
        e.preventDefault();
        undoExtractMerge();
      }
    }
  }
});

// ──────────────────────────────────────────────────────
// TOAST
// ──────────────────────────────────────────────────────
let toastTimer;
function showToast(msg, type = 'success') {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.style.borderColor = type === 'error' ? 'var(--error-text)' : 'var(--border)';
  el.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove('show'), 3000);
}

// ──────────────────────────────────────────────────────
// LOADING
// ──────────────────────────────────────────────────────
function showLoading(text = '處理中...') {
  document.getElementById('loading-text').textContent = text;
  document.getElementById('loading-overlay').style.display = 'flex';
}

function hideLoading() {
  document.getElementById('loading-overlay').style.display = 'none';
}

// ──────────────────────────────────────────────────────
// 工具
// ──────────────────────────────────────────────────────
function esc(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ──────────────────────────────────────────────────────
// TAB 5: 衝突管理 (Conflict Management)
// ──────────────────────────────────────────────────────
let conflictLogPage = 1;

function switchConflictSubTab(subTab) {
  const pendingPanel = document.getElementById('conflict-pending-panel');
  const historyPanel = document.getElementById('conflict-history-panel');
  const btnPending = document.getElementById('btn-show-pending');
  const btnHistory = document.getElementById('btn-show-history');

  if (subTab === 'pending') {
    pendingPanel.style.display = 'block';
    historyPanel.style.display = 'none';
    btnPending.className = 'btn btn-primary btn-sm';
    btnHistory.className = 'btn btn-outline btn-sm';
    loadPendingConflicts();
  } else {
    pendingPanel.style.display = 'none';
    historyPanel.style.display = 'block';
    btnPending.className = 'btn btn-outline btn-sm';
    btnHistory.className = 'btn btn-primary btn-sm';
    searchConflictLogs();
  }
}

async function updateConflictBadge() {
  try {
    const res = await fetch('/api/import/pending-conflicts');
    const data = await res.json();
    const badge = document.getElementById('conflict-badge');
    if (data.ok && data.count > 0) {
      badge.textContent = data.count;
      badge.style.display = 'inline-block';
    } else {
      badge.style.display = 'none';
    }
  } catch (e) { console.error('Failed to update conflict badge:', e); }
}

async function loadPendingConflicts() {
  try {
    const res = await fetch('/api/import/pending-conflicts');
    const data = await res.json();
    const tbody = document.getElementById('conflict-pending-tbody');
    tbody.innerHTML = '';
    
    if (data.ok && data.conflicts.length > 0) {
      data.conflicts.forEach((c, idx) => {
        const tr = document.createElement('tr');
        
        // Context model / chapter
        const context = `<div style="font-size: 11px; color: var(--text-secondary);">
          <strong>型號:</strong> ${esc(c.product || '—')}<br/>
          <strong>章節:</strong> ${esc(c.chapter || '—')}
        </div>`;
        
        // Highlight diff in DB vs Import
        const dbDiff = diffHighlight(c.db_val, c.import_val, 'diff-del');
        const importDiff = diffHighlight(c.import_val, c.db_val, 'diff-ins');
        
        tr.innerHTML = `
          <td>${idx + 1}</td>
          <td>${context}</td>
          <td style="font-size:13px; font-weight:500; text-align: left;">${esc(c.eng_text)}</td>
          <td><span class="tag tag-blue">${esc(c.lang_code)}</span></td>
          <td style="font-size: 12px; line-height: 1.5; text-align: left;">${dbDiff}</td>
          <td style="font-size: 12px; line-height: 1.5; text-align: left;">${importDiff}</td>
          <td>
            <div style="display: flex; gap: 12px; justify-content: center; align-items: center;">
              <label style="cursor: pointer; display: flex; align-items: center; gap: 4px; font-size: 12px; color: var(--text-muted);">
                <input type="radio" name="res-${c.id}" value="PENDING" checked style="cursor: pointer;"/>
                暫緩處理
              </label>
              <label style="cursor: pointer; display: flex; align-items: center; gap: 4px; font-size: 12px;">
                <input type="radio" name="res-${c.id}" value="KEEP_DB" style="cursor: pointer;"/>
                保留現有 (DB)
              </label>
              <label style="cursor: pointer; display: flex; align-items: center; gap: 4px; font-size: 12px;">
                <input type="radio" name="res-${c.id}" value="KEEP_IMPORT" style="cursor: pointer;"/>
                覆蓋匯入 (Import)
              </label>
            </div>
          </td>
        `;
        // Store pending_id on the row object
        tr.dataset.pendingId = c.id;
        tbody.appendChild(tr);
      });
      filterPendingConflicts();
    } else {
      tbody.innerHTML = '<tr><td colspan="7" class="empty-cell">🎉 尚無待處理的衝突項目</td></tr>';
    }
  } catch (e) {
    showToast('❌ 載入衝突失敗: ' + e.message, 'error');
  }
}

function setAllPendingDecisions(decision) {
  const inputs = document.querySelectorAll('#conflict-pending-tbody input[type="radio"]');
  inputs.forEach(input => {
    if (input.value === decision) {
      input.checked = true;
    }
  });
}

async function submitResolutions() {
  const rows = document.querySelectorAll('#conflict-pending-tbody tr');
  const resolutions = [];
  
  rows.forEach(tr => {
    const pid = tr.dataset.pendingId;
    if (!pid) return;
    const checkedRadio = tr.querySelector(`input[name="res-${pid}"]:checked`);
    if (checkedRadio && checkedRadio.value !== 'PENDING') {
      resolutions.push({
        pending_id: parseInt(pid),
        decision: checkedRadio.value
      });
    }
  });
  
  if (resolutions.length === 0) {
    showToast('請先將至少一個項目的決策選為「保留現有」或「覆蓋匯入」', 'error');
    return;
  }
  
  showLoading('解決衝突並套用中...');
  try {
    const res = await fetch('/api/import/resolve-conflicts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ resolutions })
    });
    const data = await res.json();
    hideLoading();
    if (data.ok) {
      showToast(`已成功解決 ${data.resolved_count} 筆翻譯衝突！`);
      loadPendingConflicts();
      updateConflictBadge();
      fetchAndRenderDB();
      loadDBStats();
    } else {
      showToast('❌ ' + data.error, 'error');
    }
  } catch (e) {
    hideLoading();
    showToast('❌ 提交決策失敗: ' + e.message, 'error');
  }
}

function loadConflictLogLanguages() {
  const sel = document.getElementById('conflict-log-lang');
  if (!sel) return;
  sel.innerHTML = '<option value="">全部語言</option>';
  LANG_CODES.forEach(code => {
    const opt = document.createElement('option');
    opt.value = code;
    opt.textContent = `${code} ${LANG_NAMES[code] || ''}`;
    sel.appendChild(opt);
  });
}

async function searchConflictLogs() {
  const qInput = document.getElementById('conflict-log-search');
  const langSel = document.getElementById('conflict-log-lang');
  if (!qInput || !langSel) return;
  const q = qInput.value;
  const lang = langSel.value;
  
  try {
    const url = `/api/import/conflict-logs?q=${encodeURIComponent(q)}&lang=${lang}&page=${conflictLogPage}&per_page=15`;
    const res = await fetch(url);
    const data = await res.json();
    const tbody = document.getElementById('conflict-history-tbody');
    tbody.innerHTML = '';
    
    if (data.ok && data.items.length > 0) {
      data.items.forEach((log, idx) => {
        const tr = document.createElement('tr');
        
        const decisionText = log.decision === 'KEEP_IMPORT' 
          ? '<span class="tag tag-orange">覆蓋新版</span>' 
          : '<span class="tag tag-blue">保留舊版</span>';
          
        const dbDiff = diffHighlight(log.db_val, log.chosen_val, 'diff-del');
        const importDiff = diffHighlight(log.import_val, log.chosen_val, 'diff-ins');
        const chosenText = log.decision === 'KEEP_IMPORT' 
          ? `<strong style="color:var(--success-text);">${esc(log.chosen_val)}</strong>`
          : `<strong>${esc(log.chosen_val)}</strong>`;
          
        tr.innerHTML = `
          <td>${(conflictLogPage - 1) * 15 + idx + 1}</td>
          <td style="font-size:11px; white-space:nowrap;">${esc(log.resolved_at)}</td>
          <td class="mono" style="font-size:11px;">${esc(log.batch_id)}</td>
          <td style="font-size:13px; text-align: left;">${esc(log.eng_text)}</td>
          <td><span class="tag tag-blue">${esc(log.lang_code)}</span></td>
          <td style="font-size:12px; color:var(--text-secondary); text-align: left;">${dbDiff}</td>
          <td style="font-size:12px; color:var(--text-secondary); text-align: left;">${importDiff}</td>
          <td style="font-size:12px; text-align: left;">${chosenText}</td>
          <td>${decisionText}</td>
        `;
        tbody.appendChild(tr);
      });
      renderConflictLogPagination(data.total, data.page, data.per_page);
    } else {
      tbody.innerHTML = '<tr><td colspan="9" class="empty-cell">無歷史解決紀錄</td></tr>';
      document.getElementById('conflict-log-pagination').innerHTML = '';
    }
  } catch (e) {
    showToast('❌ 載入歷史日誌失敗: ' + e.message, 'error');
  }
}

function renderConflictLogPagination(total, page, perPage) {
  const container = document.getElementById('conflict-log-pagination');
  container.innerHTML = '';
  const totalPages = Math.ceil(total / perPage);
  if (totalPages <= 1) return;
  
  const addBtn = (label, targetPage, active=false, disabled=false) => {
    const btn = document.createElement('button');
    btn.className = `page-btn${active ? ' active' : ''}`;
    btn.disabled = disabled;
    btn.textContent = label;
    btn.onclick = () => {
      conflictLogPage = targetPage;
      searchConflictLogs();
    };
    container.appendChild(btn);
  };
  
  addBtn('◀', page - 1, false, page === 1);
  for (let p = 1; p <= totalPages; p++) {
    if (p === 1 || p === totalPages || (p >= page - 2 && p <= page + 2)) {
      addBtn(p, p, p === page);
    } else if (p === page - 3 || p === page + 3) {
      const span = document.createElement('span');
      span.className = 'page-info';
      span.textContent = '...';
      container.appendChild(span);
    }
  }
  addBtn('▶', page + 1, false, page === totalPages);
}

function tokenize(str) {
  // If CJK characters are present, split by character
  if (/[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uff66-\uff9f]/.test(str)) {
    return str.split('');
  }
  // Otherwise, split by words and whitespaces
  return str.split(/(\s+|\b)/).filter(Boolean);
}

function diffHighlight(targetStr, otherStr, highlightClass) {
  if (!targetStr) return '';
  if (!otherStr) return `<span class="${highlightClass}">${esc(targetStr)}</span>`;
  
  let targetWords = tokenize(targetStr);
  let otherWords = tokenize(otherStr);
  
  let dp = Array(targetWords.length + 1).fill(0).map(() => Array(otherWords.length + 1).fill(0));
  for (let i = 1; i <= targetWords.length; i++) {
    for (let j = 1; j <= otherWords.length; j++) {
      if (targetWords[i-1] === otherWords[j-1]) {
        dp[i][j] = dp[i-1][j-1] + 1;
      } else {
        dp[i][j] = Math.max(dp[i-1][j], dp[i][j-1]);
      }
    }
  }
  
  let i = targetWords.length, j = otherWords.length;
  let matches = Array(targetWords.length).fill(false);
  while (i > 0 && j > 0) {
    if (targetWords[i-1] === otherWords[j-1]) {
      matches[i-1] = true;
      i--; j--;
    } else if (dp[i][j-1] >= dp[i-1][j]) {
      j--;
    } else {
      i--;
    }
  }
  
  let result = [];
  let currentGroup = [];
  let currentIsMatch = null;
  
  for (let idx = 0; idx < targetWords.length; idx++) {
    let isMatch = matches[idx];
    if (currentIsMatch === null) {
      currentIsMatch = isMatch;
      currentGroup.push(targetWords[idx]);
    } else if (currentIsMatch === isMatch) {
      currentGroup.push(targetWords[idx]);
    } else {
      let text = currentGroup.join('');
      if (currentIsMatch) {
        result.push(esc(text));
      } else {
        result.push(`<span class="${highlightClass}">${esc(text)}</span>`);
      }
      currentGroup = [targetWords[idx]];
      currentIsMatch = isMatch;
    }
  }
  
  if (currentGroup.length > 0) {
    let text = currentGroup.join('');
    if (currentIsMatch) {
      result.push(esc(text));
    } else {
      result.push(`<span class="${highlightClass}">${esc(text)}</span>`);
    }
  }
  
  return result.join('');
}

function diffString(oldStr, newStr) {
  if (!oldStr) return `<span class="diff-ins">${esc(newStr)}</span>`;
  if (!newStr) return `<span class="diff-del">${esc(oldStr)}</span>`;
  
  let oldWords = tokenize(oldStr);
  let newWords = tokenize(newStr);
  
  let dp = Array(oldWords.length + 1).fill(0).map(() => Array(newWords.length + 1).fill(0));
  for (let i = 1; i <= oldWords.length; i++) {
    for (let j = 1; j <= newWords.length; j++) {
      if (oldWords[i-1] === newWords[j-1]) {
        dp[i][j] = dp[i-1][j-1] + 1;
      } else {
        dp[i][j] = Math.max(dp[i-1][j], dp[i][j-1]);
      }
    }
  }
  
  let i = oldWords.length, j = newWords.length;
  let diffs = [];
  while (i > 0 || j > 0) {
    if (i > 0 && j > 0 && oldWords[i-1] === newWords[j-1]) {
      diffs.push({ type: 'common', text: oldWords[i-1] });
      i--; j--;
    } else if (j > 0 && (i === 0 || dp[i][j-1] >= dp[i-1][j])) {
      diffs.push({ type: 'ins', text: newWords[j-1] });
      j--;
    } else {
      diffs.push({ type: 'del', text: oldWords[i-1] });
      i--;
    }
  }
  diffs.reverse();
  
  return diffs.map(d => {
    if (d.type === 'ins') return `<span class="diff-ins">${esc(d.text)}</span>`;
    if (d.type === 'del') return `<span class="diff-del">${esc(d.text)}</span>`;
    return esc(d.text);
  }).join('');
}

// Revert last merge action
function undoExtractMerge() {
  if (extractState.historyStack.length === 0) return;
  
  const prevState = extractState.historyStack.pop();
  
  // 1. Restore file state
  if (prevState.fileId) {
    const file = extractState.uploadedFiles[prevState.fileId];
    if (file) {
      if (prevState.pdfPages) file.pdfPages = prevState.pdfPages;
      if (prevState.ocrBlocks) file.ocrBlocks = prevState.ocrBlocks;
      
      if (extractState.activeFileId === prevState.fileId) {
        extractState.fileType = file.fileType;
        extractState.pdfPages = file.pdfPages;
        extractState.ocrBlocks = file.ocrBlocks;
      }
    }
  }
  
  // 2. Restore table rows
  if (prevState.tableRows) {
    clearExtractEditor();
    prevState.tableRows.forEach(row => {
      addExtractRow(row);
    });
  }
  
  updateUndoButtonVisibility();
  updateRepopulateButtonVisibility();
  renderExtractPreview();
  showToast('↩ 已復原上一步操作！', 'info');
}

// Save current state of both file preview blocks and table rows to history
function saveExtractHistory() {
  const fileId = extractState.activeFileId;
  const file = extractState.uploadedFiles[fileId];
  
  if (extractState.historyStack.length >= 20) {
    extractState.historyStack.shift();
  }
  
  extractState.historyStack.push({
    fileId: fileId,
    pdfPages: file ? JSON.parse(JSON.stringify(file.pdfPages)) : null,
    ocrBlocks: file ? JSON.parse(JSON.stringify(file.ocrBlocks)) : null,
    tableRows: getExtractTableRowsData()
  });
  
  updateUndoButtonVisibility();
}

// Update undo button display state
function updateUndoButtonVisibility() {
  const btn = document.getElementById('extract-undo-btn');
  if (!btn) return;
  
  // Show undo button if there's any history entry
  btn.style.display = extractState.historyStack.length > 0 ? 'inline-block' : 'none';
}

// Update repopulate button display state
function updateRepopulateButtonVisibility() {
  const btn = document.getElementById('extract-repopulate-btn');
  if (!btn) return;
  btn.style.display = extractState.activeFileId ? 'inline-block' : 'none';
}

// Clear all values of a single column/language dynamically
function clearExtractColumn(code) {
  if (!confirm(`⚠️ 確定要清空 ${LANG_NAMES[code] || code} (${code}) 欄位的所有內容嗎？\n此操作不會影響其他語言直欄。`)) {
    return;
  }
  
  saveExtractHistory();
  
  const rows = getExtractTableRowsData();
  const lowerCode = code.toLowerCase();
  
  rows.forEach(row => {
    row[code] = '';
  });
  
  // Rebuild tbody
  clearExtractEditor();
  rows.forEach(row => {
    addExtractRow(row);
  });
  
  showToast(`🧹 已清空 ${code} 直欄的所有文字！`, 'info');
}

// Update the text of a preview card (from editable textarea)
function updateExtractBlockText(index, newText) {
  const fileId = extractState.activeFileId;
  const file = extractState.uploadedFiles[fileId];
  if (!file) return;
  
  if (file.fileType === 'pdf') {
    const pageData = file.pdfPages[extractState.currentPage - 1];
    if (pageData && pageData.paragraphs[index] !== undefined) {
      pageData.paragraphs[index] = newText;
      extractState.pdfPages = file.pdfPages;
    }
  } else if (file.fileType === 'image') {
    if (file.ocrBlocks[index] !== undefined) {
      file.ocrBlocks[index].text = newText;
      extractState.ocrBlocks = file.ocrBlocks;
    }
  }
}

// Delete a preview card (click on X button)
function deleteExtractBlock(index) {
  saveExtractHistory();
  const fileId = extractState.activeFileId;
  const file = extractState.uploadedFiles[fileId];
  if (!file) return;
  
  if (file.fileType === 'pdf') {
    const pageData = file.pdfPages[extractState.currentPage - 1];
    if (pageData && pageData.paragraphs[index] !== undefined) {
      pageData.paragraphs.splice(index, 1);
      extractState.pdfPages = file.pdfPages;
    }
  } else if (file.fileType === 'image') {
    if (file.ocrBlocks[index] !== undefined) {
      file.ocrBlocks.splice(index, 1);
      extractState.ocrBlocks = file.ocrBlocks;
    }
  }
  
  renderExtractPreview();
  showToast('🗑️ 已刪除該提取段落！', 'info');
}

// User-facing Reset Table action with double-confirmation and auto-backup
function userResetExtractTable() {
  const rows = getExtractTableRowsData();
  const hasData = rows.some(r => Object.values(r).some(v => v));
  
  if (hasData) {
    if (!confirm("⚠️ 確定要重置並清空對照表嗎？\n這將會清除您目前編輯的所有多國語言對照資料！")) {
      return;
    }
    // Save backup to history stack so they can undo!
    saveExtractHistory();
  }
  
  clearExtractEditor();
  // Add 3 blank rows by default
  for (let i = 0; i < 3; i++) {
    addExtractRow();
  }
  showToast("💡 表格已重置。如果不小心按錯，可以點選左上角 [復原] 還原！", "info");
}

function filterPendingConflicts() {
  const input = document.getElementById('conflict-pending-search');
  if (!input) return;
  const query = input.value.toLowerCase().trim();
  const rows = document.querySelectorAll('#conflict-pending-tbody tr');
  
  rows.forEach(tr => {
    if (tr.querySelector('.empty-cell')) return;
    
    const engText = tr.cells[2] ? tr.cells[2].textContent.toLowerCase() : '';
    const dbVal = tr.cells[4] ? tr.cells[4].textContent.toLowerCase() : '';
    const importVal = tr.cells[5] ? tr.cells[5].textContent.toLowerCase() : '';
    
    if (engText.includes(query) || dbVal.includes(query) || importVal.includes(query)) {
      tr.style.display = '';
    } else {
      tr.style.display = 'none';
    }
  });
}

function clearPendingConflictSearch() {
  const input = document.getElementById('conflict-pending-search');
  if (input) {
    input.value = '';
    filterPendingConflicts();
  }
}

// ──────────────────────────────────────────────────────
// 智慧文字提取 & OCR 互動 (Smart Extractor)
// ──────────────────────────────────────────────────────

let extractState = {
  uploadedFiles: {}, // { fileId: { name, fileType, pdfPages, ocrBlocks, ocrDetectedLang, imageSrc } }
  activeFileId: null,
  fileType: null, // 'pdf' or 'image'
  pdfPages: [],   // [ { page: 1, paragraphs: [...] }, ... ]
  ocrBlocks: [],  // [ { text: "...", box: [x, y, w, h] }, ... ]
  currentPage: 1,
  activeInputId: null, // ID of currently focused text input in table (e.g. 'extract-row-0-eng')
  rowCount: 0,
  visibleLangs: [], // Default: empty array (NO CHT checked by default!)
  historyStack: [] // A stack of previous states for reverting merge operations: [ { fileId, pdfPages: [...], ocrBlocks: [...] } ]
};

// Initialize workspace when switching to tab
function initExtractWorkspace() {
  // Render checkboxes dynamically
  renderExtractLangCheckboxes();
  // Update Table headers dynamically
  updateExtractTableHeader();
  // Update dropdown options
  updateAutoPopulateLangOptions();
  // Render file gallery
  renderExtractFilesGallery();

  if (extractState.rowCount === 0) {
    clearExtractEditor();
    // Add 3 blank rows by default
    for (let i = 0; i < 3; i++) {
      addExtractRow();
    }
  }
  // Setup overlay resizer on window resize
  window.addEventListener('resize', resizeOcrOverlays);
}

// Render horizontal capsule tabs of uploaded files
function renderExtractFilesGallery() {
  const container = document.getElementById('extract-files-gallery');
  if (!container) return;
  
  const keys = Object.keys(extractState.uploadedFiles);
  if (keys.length === 0) {
    container.style.display = 'none';
    return;
  }
  
  container.style.display = 'flex';
  container.innerHTML = '';
  
  keys.forEach(fileId => {
    const file = extractState.uploadedFiles[fileId];
    const pill = document.createElement('div');
    pill.className = `gallery-pill ${fileId === extractState.activeFileId ? 'active' : ''}`;
    pill.onclick = () => switchActiveExtractFile(fileId);
    
    pill.innerHTML = `
      <span>${esc(file.name)}</span>
      <button class="gallery-pill-delete" onclick="deleteExtractFile(event, '${fileId}')">✕</button>
    `;
    container.appendChild(pill);
  });
}

// Switch current preview file
function switchActiveExtractFile(fileId) {
  extractState.activeFileId = fileId;
  const file = extractState.uploadedFiles[fileId];
  if (file) {
    extractState.fileType = file.fileType;
    extractState.pdfPages = file.pdfPages;
    extractState.ocrBlocks = file.ocrBlocks;
    extractState.currentPage = 1;
    extractState.ocrDetectedLang = file.ocrDetectedLang;
    
    if (file.fileType === 'image' && file.imageSrc) {
      const img = document.getElementById('extract-ocr-img');
      img.src = file.imageSrc;
      img.onload = () => {
        resizeOcrOverlays();
      };
    }
  }
  renderExtractFilesGallery();
  updateUndoButtonVisibility();
  renderExtractPreview();
}

// Delete file from gallery
function deleteExtractFile(event, fileId) {
  event.stopPropagation();
  delete extractState.uploadedFiles[fileId];
  
  // Remove associated history entries
  extractState.historyStack = extractState.historyStack.filter(h => h.fileId !== fileId);
  
  if (extractState.activeFileId === fileId) {
    const keys = Object.keys(extractState.uploadedFiles);
    if (keys.length > 0) {
      switchActiveExtractFile(keys[0]);
    } else {
      extractState.activeFileId = null;
      extractState.fileType = null;
      extractState.pdfPages = [];
      extractState.ocrBlocks = [];
      
      // Reset preview
      document.getElementById('extract-viewer-placeholder').style.display = 'block';
      document.getElementById('extract-canvas-container').style.display = 'none';
      document.getElementById('extract-pdf-list').style.display = 'none';
      document.getElementById('extract-page-controls').style.display = 'none';
      document.getElementById('extract-viewer-title').textContent = '📄 檔案預覽 (未上傳)';
    }
  }
  updateUndoButtonVisibility();
  renderExtractFilesGallery();
  if (extractState.activeFileId) {
    renderExtractPreview();
  }
}

// Render dynamic checkboxes for translation columns
function renderExtractLangCheckboxes() {
  const container = document.getElementById('extract-lang-checkboxes');
  if (!container) return;
  container.innerHTML = '';
  LANG_CODES.forEach(code => {
    if (code === 'ENG') return;
    const label = document.createElement('label');
    label.style.display = 'flex';
    label.style.alignItems = 'center';
    label.style.gap = '4px';
    label.style.cursor = 'pointer';
    label.style.userSelect = 'none';
    
    const isChecked = extractState.visibleLangs.includes(code);
    label.innerHTML = `
      <input type="checkbox" value="${code}" ${isChecked ? 'checked' : ''} onchange="handleExtractLangToggle(this)"/>
      <span>${code}</span>
    `;
    container.appendChild(label);
  });
}

function updateExtractTableHeader() {
  const row = document.getElementById('extract-table-header-row');
  if (!row) return;
  row.innerHTML = `
    <th style="width: 35px; text-align: center;"><input type="checkbox" id="extract-select-all" checked onchange="toggleSelectAllExtract(this)"/></th>
    <th id="extract-header-eng">英文原文 (ENG) <span class="header-action-btn populate-btn" onclick="populateExtractColumn('ENG')" title="將左側整理好的文字填入此欄">📥</span> <span class="header-action-btn clear-btn" onclick="clearExtractColumn('ENG')" title="清空此欄所有文字">🧹</span></th>
    ${extractState.visibleLangs.map(code => `<th>${LANG_NAMES[code] || code} (${code}) <span class="header-action-btn populate-btn" onclick="populateExtractColumn('${code}')" title="將左側整理好的文字填入此欄">📥</span> <span class="header-action-btn clear-btn" onclick="clearExtractColumn('${code}')" title="清空此欄所有文字">🧹</span></th>`).join('')}
    <th style="width: 50px; text-align: center; white-space: nowrap;">操作</th>
  `;
}

// Render options list for auto-populate dropdown
function updateAutoPopulateLangOptions() {
  const select = document.getElementById('extract-auto-populate-lang');
  if (!select) return;
  const currentVal = select.value;
  
  let html = `<option value="ENG">英文原文 (ENG)</option>`;
  extractState.visibleLangs.forEach(code => {
    html += `<option value="${code}">${LANG_NAMES[code] || code} (${code})</option>`;
  });
  select.innerHTML = html;
  
  if (select.querySelector(`option[value="${currentVal}"]`)) {
    select.value = currentVal;
  } else {
    select.value = 'ENG';
  }
}

// Synchronized Hover highlighters
function highlightTableRow(idx, active) {
  const row = document.getElementById(`extract-row-${idx}`);
  if (row) {
    if (active) {
      row.classList.add('row-highlight');
    } else {
      row.classList.remove('row-highlight');
    }
  }
}

function highlightOcrBox(idx, active) {
  if (extractState.fileType === 'image') {
    const box = document.querySelector(`.ocr-box[data-idx="${idx}"]`);
    if (box) {
      if (active) {
        box.classList.add('box-highlight');
      } else {
        box.classList.remove('box-highlight');
      }
    }
  } else if (extractState.fileType === 'pdf') {
    const pdfList = document.getElementById('extract-pdf-list');
    if (pdfList) {
      const items = pdfList.querySelectorAll('.pdf-para-item');
      if (items[idx]) {
        if (active) {
          items[idx].classList.add('box-highlight');
          items[idx].scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        } else {
          items[idx].classList.remove('box-highlight');
        }
      }
    }
  }
}

// Toggle translation languages and rebuild table dynamically
function handleExtractLangToggle(checkbox) {
  const code = checkbox.value;
  if (checkbox.checked) {
    if (!extractState.visibleLangs.includes(code)) {
      extractState.visibleLangs.push(code);
    }
  } else {
    extractState.visibleLangs = extractState.visibleLangs.filter(c => c !== code);
  }
  
  // Save current data in rows before rebuilding
  const currentRowsData = getExtractTableRowsData();
  
  updateExtractTableHeader();
  updateAutoPopulateLangOptions();
  
  // Rebuild tbody
  clearExtractEditor();
  currentRowsData.forEach(row => {
    addExtractRow(row);
  });
  
  if (currentRowsData.length === 0) {
    for (let i = 0; i < 3; i++) {
      addExtractRow();
    }
  }
}

// Get all rows data dynamically
function getExtractTableRowsData() {
  const tbody = document.getElementById('extract-editor-tbody');
  const trs = tbody.querySelectorAll('tr');
  const list = [];
  trs.forEach(tr => {
    const rowData = {};
    const engInput = tr.querySelector(`input[id$="-eng"]`);
    if (engInput) {
      rowData['ENG'] = engInput.value;
    }
    extractState.visibleLangs.forEach(code => {
      const input = tr.querySelector(`input[id$="-${code.toLowerCase()}"]`);
      if (input) {
        rowData[code] = input.value;
      }
    });
    list.push(rowData);
  });
  return list;
}

// Clear or Reset editor
function clearExtractEditor() {
  document.getElementById('extract-editor-tbody').innerHTML = '';
  extractState.rowCount = 0;
  extractState.activeInputId = null;
}

// Add a row to the matching editor table (langsData is {ENG: '...', CHT: '...', GER: '...'})
function addExtractRow(langsData = {}) {
  const tbody = document.getElementById('extract-editor-tbody');
  const idx = extractState.rowCount;
  
  const tr = document.createElement('tr');
  tr.id = `extract-row-${idx}`;
  
  // Bind mouse hover sync events!
  tr.onmouseenter = () => highlightOcrBox(idx, true);
  tr.onmouseleave = () => highlightOcrBox(idx, false);
  
  let colsHtml = `
    <td>
      <input type="text" id="extract-row-${idx}-eng" class="form-input" autocomplete="off" value="${esc(langsData['ENG'] || '')}" onfocus="setActiveInput(this.id)" placeholder="點擊格或雙擊選取文字..."/>
    </td>
  `;
  
  extractState.visibleLangs.forEach(code => {
    const lowerCode = code.toLowerCase();
    colsHtml += `
      <td>
        <input type="text" id="extract-row-${idx}-${lowerCode}" class="form-input" autocomplete="off" value="${esc(langsData[code] || '')}" onfocus="setActiveInput(this.id)" placeholder="點擊格填入 ${code} 翻譯..."/>
      </td>
    `;
  });
  
  tr.innerHTML = `
    <td style="text-align: center; vertical-align: middle;">
      <input type="checkbox" class="extract-row-checkbox" checked />
    </td>
    ${colsHtml}
    <td style="text-align: center; vertical-align: middle;">
      <button class="btn btn-ghost btn-sm" onclick="removeExtractRowById('extract-row-${idx}')" style="color: var(--error); padding: 2px 6px;">✕</button>
    </td>
  `;
  
  tbody.appendChild(tr);
  extractState.rowCount++;
  
  // Auto-focus the ENG field of the new row (only if we manually added a row)
  if (Object.keys(langsData).length === 0) {
    setActiveInput(`extract-row-${idx}-eng`);
  }
}

function removeExtractRowById(rowId) {
  const row = document.getElementById(rowId);
  if (row) {
    row.remove();
  }
}

// Toggle check all rows
function toggleSelectAllExtract(cb) {
  document.querySelectorAll('.extract-row-checkbox').forEach(chk => {
    chk.checked = cb.checked;
  });
}

// Track currently active/focused input cell in the editor table
function setActiveInput(inputId) {
  // Remove highlight class from previous
  if (extractState.activeInputId) {
    const prev = document.getElementById(extractState.activeInputId);
    if (prev) prev.classList.remove('editor-input-active');
  }
  
  extractState.activeInputId = inputId;
  
  // Highlight the current active input
  const curr = document.getElementById(inputId);
  if (curr) {
    curr.classList.add('editor-input-active');
  }
}

// Populate the selected input field with clicked text snippet (handles substring highlights)
function grabTextToActiveInput(text) {
  if (!extractState.activeInputId) {
    showToast('💡 請先在右側對照編輯器中，點選一個輸入框儲存格！', 'info');
    return;
  }
  
  // Selection Override (C scheme): Check if user highlighted a specific string
  const selectedText = window.getSelection().toString().trim();
  const textToUse = selectedText ? selectedText : text;
  
  const activeInput = document.getElementById(extractState.activeInputId);
  if (activeInput) {
    activeInput.value = textToUse;
    
    // Add a visual indicator (blink) that the value has been grabbed
    activeInput.style.transition = 'background-color 0.2s';
    activeInput.style.backgroundColor = 'rgba(0, 200, 80, 0.2)';
    setTimeout(() => {
      activeInput.style.backgroundColor = '';
    }, 400);
    
    // Clear selection range
    window.getSelection().removeAllRanges();
    
    // Auto-advance cursor intelligently
    const idParts = extractState.activeInputId.split('-');
    const rowIdx = parseInt(idParts[2], 10);
    const colName = idParts[3];
    
    if (colName === 'eng') {
      if (extractState.visibleLangs.length > 0) {
        const firstLang = extractState.visibleLangs[0].toLowerCase();
        const nextId = `extract-row-${rowIdx}-${firstLang}`;
        if (document.getElementById(nextId)) {
          setActiveInput(nextId);
        }
      }
    } else {
      const currLangIdx = extractState.visibleLangs.findIndex(l => l.toLowerCase() === colName);
      if (currLangIdx !== -1 && currLangIdx < extractState.visibleLangs.length - 1) {
        // Next translation column of the same row
        const nextLang = extractState.visibleLangs[currLangIdx + 1].toLowerCase();
        const nextId = `extract-row-${rowIdx}-${nextLang}`;
        if (document.getElementById(nextId)) {
          setActiveInput(nextId);
        }
      } else {
        // Next row ENG
        const nextId = `extract-row-${rowIdx + 1}-eng`;
        if (document.getElementById(nextId)) {
          setActiveInput(nextId);
        } else {
          addExtractRow();
        }
      }
    }
  }
}

// Render Preview Area
function renderExtractPreview() {
  const placeholder = document.getElementById('extract-viewer-placeholder');
  const canvasContainer = document.getElementById('extract-canvas-container');
  const pdfList = document.getElementById('extract-pdf-list');
  const title = document.getElementById('extract-viewer-title');
  const pageControls = document.getElementById('extract-page-controls');
  
  placeholder.style.display = 'none';
  canvasContainer.style.display = 'none';
  pdfList.style.display = 'none';
  pageControls.style.display = 'none';
  
  if (extractState.fileType === 'pdf') {
    title.textContent = `📄 PDF 段落預覽 (共 ${extractState.pdfPages.length} 頁)`;
    pageControls.style.display = 'flex';
    pdfList.style.display = 'flex';
    
    // Update Page text
    document.getElementById('extract-page-num').textContent = `第 ${extractState.currentPage} 頁 / ${extractState.pdfPages.length} 頁`;
    
    const pageData = extractState.pdfPages[extractState.currentPage - 1];
    pdfList.innerHTML = '';
    
    if (pageData && pageData.paragraphs.length > 0) {
      pageData.paragraphs.forEach((para, index) => {
        const div = document.createElement('div');
        div.className = 'pdf-para-item';
        div.setAttribute('data-idx', index);
        
        // Editable textarea for direct modification
        const textarea = document.createElement('textarea');
        textarea.className = 'pdf-para-textarea';
        textarea.value = para;
        textarea.rows = Math.max(1, Math.ceil(para.length / 50));
        textarea.oninput = (e) => {
          updateExtractBlockText(index, e.target.value);
        };
        textarea.onclick = (e) => {
          e.stopPropagation();
        };
        div.appendChild(textarea);
        
        div.onclick = () => grabTextToActiveInput(para);
        
        // Actions wrapper
        const actionsDiv = document.createElement('div');
        actionsDiv.style.display = 'flex';
        actionsDiv.style.alignItems = 'center';
        actionsDiv.style.gap = '6px';
        
        // Merge button (if not last item)
        if (index < pageData.paragraphs.length - 1) {
          const btn = document.createElement('button');
          btn.className = 'btn btn-ghost btn-sm';
          btn.style.padding = '2px 6px';
          btn.style.fontSize = '10px';
          btn.style.height = 'auto';
          btn.style.color = 'var(--accent)';
          btn.style.border = '1px solid rgba(0, 102, 255, 0.15)';
          btn.style.borderRadius = '4px';
          btn.innerHTML = '🔗 合併下句';
          btn.onclick = (e) => {
            e.stopPropagation();
            mergeExtractBlockWithNext(index);
          };
          actionsDiv.appendChild(btn);
        }
        
        // Delete block button
        const delBtn = document.createElement('button');
        delBtn.className = 'pdf-para-delete';
        delBtn.innerHTML = '✕';
        delBtn.title = '刪除此段落';
        delBtn.onclick = (e) => {
          e.stopPropagation();
          deleteExtractBlock(index);
        };
        actionsDiv.appendChild(delBtn);
        
        div.appendChild(actionsDiv);
        
        // Synchronize Hover
        div.onmouseenter = () => highlightTableRow(index, true);
        div.onmouseleave = () => highlightTableRow(index, false);
        
        pdfList.appendChild(div);
      });
    } else {
      pdfList.innerHTML = '<div class="empty-cell" style="padding: 20px;">本頁無可辨識文字段落</div>';
    }
    
  } else if (extractState.fileType === 'image') {
    title.textContent = `🖼️ 截圖 OCR 標記與文字清單`;
    canvasContainer.style.display = 'block';
    pdfList.style.display = 'flex'; // Display cards underneath image
    
    // Clear old overlays
    const overlays = document.getElementById('extract-ocr-overlays');
    overlays.innerHTML = '';
    
    // Add overlays
    extractState.ocrBlocks.forEach((block, index) => {
      const box = block.box; // [x, y, w, h] normalized
      const div = document.createElement('div');
      div.className = 'ocr-box';
      div.setAttribute('data-idx', index);
      div.style.left = `${box[0] * 100}%`;
      div.style.top = `${box[1] * 100}%`;
      div.style.width = `${box[2] * 100}%`;
      div.style.height = `${box[3] * 100}%`;
      div.title = block.text;
      
      div.style.pointerEvents = 'auto';
      
      div.onclick = (e) => {
        e.stopPropagation();
        grabTextToActiveInput(block.text);
      };
      
      // Synchronize Hover
      div.onmouseenter = () => highlightTableRow(index, true);
      div.onmouseleave = () => highlightTableRow(index, false);
      
      overlays.appendChild(div);
    });
    
    // Render text cards under the image!
    pdfList.innerHTML = '';
    if (extractState.ocrBlocks.length > 0) {
      const headerLabel = document.createElement('div');
      headerLabel.style.fontSize = '11px';
      headerLabel.style.color = 'var(--text-muted)';
      headerLabel.style.marginBottom = '6px';
      headerLabel.style.textTransform = 'uppercase';
      headerLabel.style.letterSpacing = '0.5px';
      headerLabel.textContent = '圖片文字清單 (OCR Blocks List)';
      pdfList.appendChild(headerLabel);
      
      extractState.ocrBlocks.forEach((block, index) => {
        const div = document.createElement('div');
        div.className = 'pdf-para-item';
        div.setAttribute('data-idx', index);
        
        // Editable textarea for OCR cards
        const textarea = document.createElement('textarea');
        textarea.className = 'pdf-para-textarea';
        textarea.value = block.text;
        textarea.rows = Math.max(1, Math.ceil(block.text.length / 50));
        textarea.oninput = (e) => {
          updateExtractBlockText(index, e.target.value);
        };
        textarea.onclick = (e) => {
          e.stopPropagation();
        };
        div.appendChild(textarea);
        
        div.onclick = () => grabTextToActiveInput(block.text);
        
        // Actions wrapper
        const actionsDiv = document.createElement('div');
        actionsDiv.style.display = 'flex';
        actionsDiv.style.alignItems = 'center';
        actionsDiv.style.gap = '6px';
        
        // Merge button (if not last item)
        if (index < extractState.ocrBlocks.length - 1) {
          const btn = document.createElement('button');
          btn.className = 'btn btn-ghost btn-sm';
          btn.style.padding = '2px 6px';
          btn.style.fontSize = '10px';
          btn.style.height = 'auto';
          btn.style.color = 'var(--accent)';
          btn.style.border = '1px solid rgba(0, 102, 255, 0.15)';
          btn.style.borderRadius = '4px';
          btn.innerHTML = '🔗 合併下句';
          btn.onclick = (e) => {
            e.stopPropagation();
            mergeExtractBlockWithNext(index);
          };
          actionsDiv.appendChild(btn);
        }
        
        // Delete block button
        const delBtn = document.createElement('button');
        delBtn.className = 'pdf-para-delete';
        delBtn.innerHTML = '✕';
        delBtn.title = '刪除此段落';
        delBtn.onclick = (e) => {
          e.stopPropagation();
          deleteExtractBlock(index);
        };
        actionsDiv.appendChild(delBtn);
        
        div.appendChild(actionsDiv);
        
        // Synchronize Hover
        div.onmouseenter = () => highlightTableRow(index, true);
        div.onmouseleave = () => highlightTableRow(index, false);
        
        pdfList.appendChild(div);
      });
    } else {
      pdfList.innerHTML = '<div class="empty-cell" style="padding: 20px;">圖片中無可辨識文字段落</div>';
    }
    
    // Recalculate overlay layout coordinates over the scale image
    setTimeout(resizeOcrOverlays, 100);
  }
  
  // Append target language selection and populate button at the very bottom of left cards list!
  if (extractState.fileType === 'pdf' || extractState.fileType === 'image') {
    const popDiv = document.createElement('div');
    popDiv.className = 'pdf-para-item';
    popDiv.style.background = 'rgba(0, 102, 255, 0.05)';
    popDiv.style.border = '1px dashed var(--accent)';
    popDiv.style.display = 'flex';
    popDiv.style.alignItems = 'center';
    popDiv.style.justifyContent = 'space-between';
    popDiv.style.padding = '12px';
    popDiv.style.marginTop = '15px';
    popDiv.style.marginBottom = '20px';
    
    popDiv.innerHTML = `
      <div style="display: flex; align-items: center; gap: 8px;">
        <span style="font-size: 12px; font-weight: bold; color: var(--text-primary);">📥 匯入右側表格</span>
        <span style="font-size: 11px; color: var(--text-muted);">選擇填入語系：</span>
        <select id="extract-populate-target-lang" style="background: var(--bg-secondary); color: var(--text-primary); border: 1px solid var(--border); border-radius: 4px; padding: 4px 8px; font-size: 12px; outline: none;">
          ${LANG_CODES.map(code => `<option value="${code}" ${code === (extractState.ocrDetectedLang || 'ENG') ? 'selected' : ''}>${LANG_NAMES[code] || code} (${code})</option>`).join('')}
        </select>
      </div>
      <button class="btn btn-primary btn-sm" onclick="populateFromBottom()" style="padding: 6px 14px; font-size: 12px;">確認填入</button>
    `;
    pdfList.appendChild(popDiv);
  }
}

// Bottom populate selector trigger helper
function populateFromBottom() {
  const select = document.getElementById('extract-populate-target-lang');
  if (!select) return;
  const targetLang = select.value;
  populateExtractColumn(targetLang);
}

// Handle file upload
async function handleExtractUpload(input) {
  if (input.files && input.files.length > 0) {
    await handleExtractUploadFromFiles(input.files);
  }
}

async function handleExtractUploadFromFiles(files) {
  showLoading('讀取與解析多個檔案中...');
  try {
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      await processSingleExtractFile(file);
    }
    hideLoading();
  } catch (e) {
    hideLoading();
    showToast('❌ 批次提取失敗：' + e.message, 'error');
  }
}

async function processSingleExtractFile(file) {
  const fileId = 'file-' + Date.now() + '-' + Math.random().toString(36).substr(2, 5);
  const name = file.name.toLowerCase();
  const fd = new FormData();
  fd.append('file', file);
  
  if (name.endsWith('.pdf')) {
    const res = await fetch('/api/extract/pdf', { method: 'POST', body: fd });
    const data = await res.json();
    if (!data.ok) { throw new Error(data.error); }
    
    extractState.uploadedFiles[fileId] = {
      id: fileId,
      name: file.name,
      fileType: 'pdf',
      pdfPages: data.pages,
      ocrBlocks: [],
      ocrDetectedLang: 'ENG'
    };
    
    switchActiveExtractFile(fileId);
    
  } else if (name.endsWith('.png') || name.endsWith('.jpg') || name.endsWith('.jpeg')) {
    const imageSrc = await new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = (e) => resolve(e.target.result);
      reader.readAsDataURL(file);
    });
    
    const res = await fetch('/api/extract/ocr', { method: 'POST', body: fd });
    const data = await res.json();
    if (!data.ok) { throw new Error(data.error); }
    
    extractState.uploadedFiles[fileId] = {
      id: fileId,
      name: file.name,
      fileType: 'image',
      pdfPages: [],
      ocrBlocks: data.blocks,
      ocrDetectedLang: data.detected_lang || 'ENG',
      imageSrc: imageSrc
    };
    
    switchActiveExtractFile(fileId);
  }
}

// Extract keywords inside parenthesis or uppercase words
function extractKeywords(text) {
  const keywords = [];
  const parenMatches = text.match(/\(([^)]+)\)/g);
  if (parenMatches) {
    parenMatches.forEach(m => {
      const word = m.slice(1, -1).trim().toUpperCase();
      if (word.length >= 3) {
        keywords.push(word);
      }
    });
  }
  const upperMatches = text.match(/[A-Z]{3,}/g);
  if (upperMatches) {
    upperMatches.forEach(w => {
      if (!keywords.includes(w)) {
        keywords.push(w);
      }
    });
  }
  return keywords;
}

// Manually align and populate active file's left text cards into the target language column
function populateExtractColumn(langCode) {
  const fileId = extractState.activeFileId;
  if (!fileId) {
    showToast('⚠️ 請先在上方上傳或切換至欲填入的語系檔案！', 'warning');
    return;
  }
  const file = extractState.uploadedFiles[fileId];
  if (!file) return;
  
  saveExtractHistory();
  
  // Enable column checkbox if not already visible
  if (!extractState.visibleLangs.includes(langCode) && langCode !== 'ENG') {
    extractState.visibleLangs.push(langCode);
    updateExtractTableHeader();
    renderExtractLangCheckboxes();
    updateAutoPopulateLangOptions();
  }
  
  let blocks = [];
  if (file.fileType === 'pdf') {
    const pageData = file.pdfPages[extractState.currentPage - 1];
    if (pageData) {
      blocks = pageData.paragraphs.map(p => ({ text: p }));
    }
  } else if (file.fileType === 'image') {
    blocks = file.ocrBlocks;
  }
  
  if (blocks.length === 0) {
    showToast('⚠️ 當前檔案無可用的文字段落可供填入！', 'warning');
    return;
  }
  
  const currentRows = getExtractTableRowsData();
  const isTableEmpty = currentRows.length === 0 || 
                       (currentRows.length === 3 && currentRows.every(r => !r['ENG'] && !Object.values(r).some(v => v)));
                       
  const alignedRows = isTableEmpty ? [] : [...currentRows];
  
  blocks.forEach(block => {
    const text = block.text;
    let matchedIdx = -1;
    
    if (alignedRows.length > 0) {
      const keywords = extractKeywords(text);
      const blockParens = [];
      const parenMatches = text.match(/\(([^)]+)\)/g);
      if (parenMatches) {
        parenMatches.forEach(m => {
          const word = m.slice(1, -1).trim().toUpperCase();
          if (word.length >= 3) blockParens.push(word);
        });
      }
      
      let bestScore = 0;
      for (let i = 0; i < alignedRows.length; i++) {
        let score = 0;
        
        if (langCode !== 'ENG') {
          // Aligning a translation (e.g. GER) to the ENG column
          const engText = (alignedRows[i]['ENG'] || '');
          const engUpper = engText.toUpperCase();
          const engLabel = engText.split(':')[0].trim().toUpperCase();
          
          blockParens.forEach(bp => {
            if (engLabel.includes(bp)) score += 100;
          });
          keywords.forEach(kw => {
            if (engUpper.includes(kw)) score += 10;
          });
        } else {
          // Aligning ENG to an existing translation column (e.g. GER, DUT)
          // Find the first available translation text in this row to match against
          let refText = '';
          for (const key in alignedRows[i]) {
            if (key !== 'ENG' && alignedRows[i][key]) {
              refText = alignedRows[i][key];
              break;
            }
          }
          
          if (refText) {
            const refUpper = refText.toUpperCase();
            const refLabel = refText.split(':')[0].trim().toUpperCase();
            
            // Extract parenthesis from reference text
            const refParens = [];
            const refParenMatches = refText.match(/\(([^)]+)\)/g);
            if (refParenMatches) {
              refParenMatches.forEach(m => {
                const word = m.slice(1, -1).trim().toUpperCase();
                if (word.length >= 3) refParens.push(word);
              });
            }
            
            // If ENG parenthesis (like TIME) matches reference label/parenthesis (like ZEIT (TIME))
            blockParens.forEach(bp => {
              if (refLabel.includes(bp) || refParens.includes(bp)) {
                score += 100;
              }
            });
            
            // If ENG general keywords match reference text
            keywords.forEach(kw => {
              if (refUpper.includes(kw)) {
                score += 10;
              }
            });
          }
        }
        
        if (score > bestScore) {
          bestScore = score;
          matchedIdx = i;
        }
      }
    }
    
    if (matchedIdx !== -1) {
      alignedRows[matchedIdx][langCode] = text;
    } else {
      const newRow = {};
      newRow[langCode] = text;
      alignedRows.push(newRow);
    }
  });
  
  clearExtractEditor();
  alignedRows.forEach(row => {
    addExtractRow(row);
  });
  
  showToast(`📥 已將當前檔案文字成功填入 ${langCode} 直欄！`, 'success');
}

// Merge a preview text block with the next one sequentially
function mergeExtractBlockWithNext(index) {
  saveExtractHistory();
  const fileId = extractState.activeFileId;
  const file = extractState.uploadedFiles[fileId];
  if (!file) return;
  
  if (file.fileType === 'pdf') {
    const pageData = file.pdfPages[extractState.currentPage - 1];
    if (pageData && pageData.paragraphs[index] && pageData.paragraphs[index + 1]) {
      const t1 = pageData.paragraphs[index];
      const t2 = pageData.paragraphs[index + 1];
      const needsSpace = /[a-zA-Z\u00C0-\u024F]$/.test(t1) && /^[a-zA-Z\u00C0-\u024F]/.test(t2);
      pageData.paragraphs[index] = t1 + (needsSpace ? ' ' : '') + t2;
      pageData.paragraphs.splice(index + 1, 1);
      
      extractState.pdfPages = file.pdfPages;
    }
  } else if (file.fileType === 'image') {
    if (file.ocrBlocks[index] && file.ocrBlocks[index + 1]) {
      const b1 = file.ocrBlocks[index];
      const b2 = file.ocrBlocks[index + 1];
      const needsSpace = /[a-zA-Z\u00C0-\u024F]$/.test(b1.text) && /^[a-zA-Z\u00C0-\u024F]/.test(b2.text);
      b1.text = b1.text + (needsSpace ? ' ' : '') + b2.text;
      
      // Combine bounding box rectangles
      const box1 = b1.box;
      const box2 = b2.box;
      const x1 = Math.min(box1[0], box2[0]);
      const y1 = Math.min(box1[1], box2[1]);
      const x2 = Math.max(box1[0] + box1[2], box2[0] + box2[2]);
      const y2 = Math.max(box1[1] + box1[3], box2[1] + box2[3]);
      b1.box = [x1, y1, x2 - x1, y2 - y1];
      
      file.ocrBlocks.splice(index + 1, 1);
      extractState.ocrBlocks = file.ocrBlocks;
    }
  }
  
  renderExtractPreview();
}

// Adjust overlays to match scaling of responsive image preview
function resizeOcrOverlays() {
  const img = document.getElementById('extract-ocr-img');
  const overlays = document.getElementById('extract-ocr-overlays');
  if (!img || !overlays || img.style.display === 'none') return;
  
  overlays.style.width = img.clientWidth + 'px';
  overlays.style.height = img.clientHeight + 'px';
  overlays.style.left = img.offsetLeft + 'px';
  overlays.style.top = img.offsetTop + 'px';
}

// PDF Pagination Controls
function prevExtractPage() {
  if (extractState.currentPage > 1) {
    extractState.currentPage--;
    renderExtractPreview();
  }
}

// Next page
function nextExtractPage() {
  if (extractState.currentPage < extractState.pdfPages.length) {
    extractState.currentPage++;
    renderExtractPreview();
  }
}

// Submit aligned translation rows to SQLite Database via backend JSON API
async function submitExtractToDB() {
  const product = document.getElementById('extract-default-product').value.trim();
  const chapter = document.getElementById('extract-default-chapter').value.trim();
  
  if (!product || !chapter) {
    showToast('⚠️ 請先填入預設的「產品型號」與「章節」！', 'warning');
    return;
  }
  
  const rows = [];
  const tbody = document.getElementById('extract-editor-tbody');
  const trs = tbody.querySelectorAll('tr');
  
  trs.forEach(tr => {
    const chk = tr.querySelector('.extract-row-checkbox');
    if (chk && chk.checked) {
      const engInput = tr.querySelector(`input[id$="-eng"]`);
      const eng = engInput ? engInput.value.trim() : '';
      
      if (eng) {
        const rowData = {
          product: product,
          chapter: chapter,
          ENG: eng
        };
        
        extractState.visibleLangs.forEach(code => {
          const input = tr.querySelector(`input[id$="-${code.toLowerCase()}"]`);
          rowData[code] = input ? input.value.trim() : '';
        });
        
        rows.push(rowData);
      }
    }
  });
  
  if (rows.length === 0) {
    showToast('⚠️ 表格中無勾選或填寫的有效對照條目！', 'warning');
    return;
  }
  
  showLoading('正匯入對照翻譯至資料庫...');
  try {
    const res = await fetch('/api/extract/import', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ rows: rows })
    });
    const data = await res.json();
    hideLoading();
    
    if (!data.ok) {
      showToast('❌ 匯入失敗：' + data.error, 'error');
      return;
    }
    
    showToast(`✅ ${data.message}`);
    
    // Refresh parent statistics and table view if database is active
    loadDBStats();
    searchDB();
    updateConflictBadge();
    
    // Clear and reset matching table upon successful import
    clearExtractEditor();
    for (let i = 0; i < 3; i++) {
      addExtractRow();
    }
    
  } catch (e) {
    hideLoading();
    showToast('❌ 連線伺服器發生異常：' + e.message, 'error');
  }
}
