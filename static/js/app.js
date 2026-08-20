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
    const res  = await fetch('/api/import/excel', { method: 'POST', body: fd });
    const data = await res.json();
    hideLoading();
    const el = document.getElementById('excel-import-result');
    if (data.ok) {
      let html = `<div class="alert alert-success">
        ✅ 匯入完成：新增 ${data.added} 筆 / 更新 ${data.updated} 筆 / 略過 ${data.skipped} 筆
      </div>`;
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

// ESC 關閉
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal-overlay').forEach(m => {
      if (m.style.display !== 'none') closeModal(m.id);
    });
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
