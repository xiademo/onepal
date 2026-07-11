/* OnePal Dashboard App - Task 07-B
 * API client, state management, and DOM rendering for 15 panels.
 * Uses fetch() exclusively. Zero external dependencies. Zero CDN.
 * Avoids eval / new Function / direct file access.
 */
(function() {
'use strict';

var API_BASE = window.location.origin;
var REFRESH_MS = 5000;
var refreshTimer = null;

// ─── DOM refs ───
var apiBadge = document.getElementById('api-badge');
var apiUrlEl = document.getElementById('api-url');
var refreshAllBtn = document.getElementById('refresh-all-btn');
var toastRegion = document.getElementById('toast-region');
var currentViewEl = document.getElementById('current-view');

function activatePanel(panelId, updateHash) {
  var panels = document.querySelectorAll('main .panel');
  var chips = document.querySelectorAll('.nav-chip');
  var target = document.getElementById(panelId);
  if (!target) return;

  panels.forEach(function(panel) {
    var active = panel.id === panelId;
    panel.classList.toggle('is-active', active);
    panel.setAttribute('aria-hidden', active ? 'false' : 'true');
  });
  target.classList.remove('panel-enter');
  void target.offsetWidth;
  target.classList.add('panel-enter');
  window.setTimeout(function() { target.classList.remove('panel-enter'); }, 520);
  chips.forEach(function(chip) {
    var active = chip.getAttribute('href') === '#' + panelId;
    chip.classList.toggle('is-active', active);
    if (active) chip.setAttribute('aria-current', 'page');
    else chip.removeAttribute('aria-current');
    if (active && currentViewEl) currentViewEl.textContent = chip.textContent;
  });
  if (updateHash) window.history.replaceState(null, '', '#' + panelId);
}

function initializePanelNavigation() {
  document.querySelectorAll('.nav-chip').forEach(function(chip) {
    chip.addEventListener('click', function(event) {
      event.preventDefault();
      activatePanel(chip.getAttribute('href').slice(1), true);
      window.scrollTo({top: 0, behavior: 'smooth'});
    });
  });
  window.addEventListener('hashchange', function() {
    activatePanel(window.location.hash.slice(1) || 'setup-panel', false);
  });
  activatePanel(window.location.hash.slice(1) || 'setup-panel', false);
}

function initializeMotionSystem() {
  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  var finePointer = window.matchMedia('(pointer: fine)');

  document.querySelectorAll('.panel').forEach(function(panel) {
    var frame = null;
    panel.addEventListener('pointermove', function(event) {
      if (reduceMotion.matches || !finePointer.matches) return;
      if (frame) window.cancelAnimationFrame(frame);
      frame = window.requestAnimationFrame(function() {
        var rect = panel.getBoundingClientRect();
        panel.style.setProperty('--pointer-x', (event.clientX - rect.left) + 'px');
        panel.style.setProperty('--pointer-y', (event.clientY - rect.top) + 'px');
        panel.classList.add('has-pointer');
      });
    });
    panel.addEventListener('pointerleave', function() {
      panel.classList.remove('has-pointer');
    });
  });

  document.addEventListener('pointerdown', function(event) {
    if (reduceMotion.matches) return;
    var target = event.target;
    if (!target || !target.closest) return;
    var button = target.closest('.btn');
    if (!button) return;
    var rect = button.getBoundingClientRect();
    button.style.setProperty('--ripple-x', (event.clientX - rect.left) + 'px');
    button.style.setProperty('--ripple-y', (event.clientY - rect.top) + 'px');
    button.classList.remove('is-rippling');
    void button.offsetWidth;
    button.classList.add('is-rippling');
    window.setTimeout(function() { button.classList.remove('is-rippling'); }, 620);
  });
}

var TEXT = {
  'Loading...': '正在加载...', 'No data': '暂无数据', 'Error loading data': '加载失败', 'Retry': '重试',
  'Action failed': '操作失败', 'Create': '创建', 'Created: ': '已创建：', 'Error: ': '错误：',
  'Content required': '请输入内容', 'Title required': '请输入标题', 'Routes': '模型路由', 'Cost Events': '成本事件',
  'Create Route': '创建路由', 'Task type': '任务类型', 'No model routes': '暂无模型路由', 'No cost events': '暂无成本事件',
  'ID': '编号', 'Task': '任务', 'Model': '模型', 'Status': '状态', 'Enabled': '启用', 'Disabled': '未启用',
  'enabled': '已启用', 'disabled': '未启用', 'yes': '是', 'no': '否', 'required': '需要审批', 'not required': '无需审批',
  'Quality Reviews': '质量评审', 'Conflicts': '冲突', 'Change Requests': '变更请求', 'Snapshots': '快照',
  'Create Workflow': '创建工作流', 'Workflow name': '工作流名称', 'Workflows': '工作流', 'Runs': '运行记录',
  'Create Candidate': '创建候选项', 'Create Source': '创建来源', 'Create Asset': '创建职业资产',
  'Create Skill Candidate': '创建技能候选', 'Skill name': '技能名称', 'Candidates': '候选项', 'Reviews': '评审记录',
  'Create Node': '创建知识节点', 'Node label': '节点名称', 'Nodes': '节点', 'Edges': '边', 'Boundaries': '边界候选',
  'State': '状态快照', 'MCP Profiles': 'MCP 配置', 'Tool Policies': '工具策略', 'Create MCP Profile': '创建 MCP 配置',
  'MCP profile name': 'MCP 配置名称', 'Memory content...': '记忆候选内容', 'Source content...': '来源内容',
  'Goal title': '目标标题', 'Reason': '原因', 'Asset title': '资产标题', 'Evidence refs, comma-separated': '证据引用，使用逗号分隔',
  'Auto Submit': '自动提交', 'LiteLLM': 'LiteLLM', 'Sandbox': '沙箱', 'Enabled After': '评审后启用', 'RAG': 'RAG',
  'Write': '写入', 'Approval': '审批', 'Outputs': '输出', 'Trust': '信任等级', 'Risk': '风险',
  'Source': '来源', 'Evidence': '证据', 'Summary': '摘要', 'Type': '类型', 'Name': '名称',
  'No JD evaluations': '暂无 JD 评估', 'No MCP profiles': '暂无 MCP 配置', 'No workflows': '暂无工作流',
  'No workflow runs': '暂无工作流运行记录', 'No skill candidates': '暂无技能候选项', 'No nodes': '暂无节点',
  'No edges': '暂无边', 'No boundaries': '暂无边界候选', 'No state snapshots': '暂无状态快照'
};

function zh(value) {
  return Object.prototype.hasOwnProperty.call(TEXT, value) ? TEXT[value] : value;
}

// ─── State ───
var state = {
  health: { status: 'loading', data: null, error: null },
  tasks:  { status: 'loading', data: [], error: null },
  taskTrees: { status: 'loading', data: [], error: null },
  taskRuns: { status: 'loading', data: [], error: null },
  masTrace: { status: 'loading', data: [], error: null },
  command: { status: 'idle', result: null, error: null }
};

// ─── API Client ───
function apiFetch(url, opts) {
  return fetch(url, opts).then(function(res) {
    if (!res.ok) {
      return res.json().then(function(body) {
        throw new Error(body && body.error ? body.error.message : ('HTTP ' + res.status));
      }).catch(function(e) {
        if (e.message && e.message.indexOf('HTTP ') === -1) throw e;
        throw new Error('HTTP ' + res.status);
      });
    }
    return res.json();
  });
}

function apiGet(path) {
  return apiFetch(API_BASE + path);
}

function apiPost(path, body) {
  return apiFetch(API_BASE + path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
}

// ─── DOM Helpers (safe — no innerHTML with untrusted data) ───
function el(tag, cls, text) {
  var e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text !== undefined) e.textContent = zh(text);
  return e;
}

function badge(text, cls) {
  var b = el('span', 'status-badge ' + (cls || ''));
  b.textContent = text;
  return b;
}

function showLoading(container) {
  container.innerHTML = '';
  container.appendChild(el('div', 'loading', '正在加载...'));
}

function showEmpty(container, msg) {
  container.innerHTML = '';
  container.appendChild(el('div', 'empty', msg || '暂无数据'));
}

function showError(container, msg, retryFn) {
  container.innerHTML = '';
  var div = el('div', 'error-state', msg || '加载失败');
  if (retryFn) {
    var btn = el('button', 'btn btn-sm retry-btn', '重试');
    btn.onclick = retryFn;
    div.appendChild(btn);
  }
  container.appendChild(div);
}

function showToast(message, type) {
  if (!toastRegion) return;
  var cls = 'toast toast-' + (type || 'info');
  var toast = el('div', cls, message || '操作失败');
  toastRegion.appendChild(toast);
  setTimeout(function() {
    if (toast.parentNode) toast.parentNode.removeChild(toast);
  }, 3600);
}

function handleActionError(error) {
  showToast(error && error.message ? error.message : '操作失败', 'error');
}

function buildTable(columns, rows) {
  var table = el('table');
  var thead = el('thead');
  var tr = el('tr');
  columns.forEach(function(col) {
    var th = el('th', '', col);
    tr.appendChild(th);
  });
  thead.appendChild(tr);
  table.appendChild(thead);

  var tbody = el('tbody');
  rows.forEach(function(row) {
    var r = el('tr');
    row.forEach(function(cell) {
      var td = el('td');
      if (cell && cell.nodeType) {
        td.appendChild(cell);
      } else {
        td.textContent = cell !== null && cell !== undefined ? String(cell) : '';
      }
      r.appendChild(td);
    });
    tbody.appendChild(r);
  });
  table.appendChild(tbody);
  return table;
}

// ─── Health Panel ───
function renderHealth(body) {
  var container = body || document.getElementById('health-body');
  var badgeEl = document.getElementById('health-status-badge');

  if (state.health.status === 'loading') { showLoading(container); return; }
  if (state.health.status === 'error') {
    showError(container, state.health.error, refreshHealth);
    if (badgeEl) { badgeEl.textContent = 'ERR'; badgeEl.className = 'status-badge status-not_ready'; }
    return;
  }

  container.innerHTML = '';
  var data = state.health.data || {};
  var status = data.status || 'unknown';

  if (badgeEl) {
    badgeEl.textContent = status.toUpperCase();
    badgeEl.className = 'status-badge status-' + status;
  }

  var detail = el('div', 'health-detail');
  detail.appendChild(el('span', '', 'source: ' + (data.source || 'none')));
  detail.appendChild(el('span', '', 'exists: ' + (data.exists ? 'yes' : 'no')));
  if (data.last_updated) {
    detail.appendChild(el('span', '', 'updated: ' + data.last_updated));
  }
  container.appendChild(detail);

  if (!data.exists) {
    container.appendChild(el('p', 'empty', 'Run startup smoke test to generate health status.'));
  }
  if (status === 'limited') {
    container.appendChild(el('p', '', 'System is functional with warnings.'));
  }
}

function refreshHealth() {
  state.health.status = 'loading';
  renderHealth();
  apiGet('/health').then(function(resp) {
    state.health.status = 'success';
    state.health.data = resp.data || {};
    state.health.error = null;
  }).catch(function(err) {
    state.health.status = 'error';
    state.health.error = err.message;
    state.health.data = null;
  }).finally(function() { renderHealth(); });
}

// ─── Command Panel ───
var cmdInput = document.getElementById('command-input');
var cmdError = document.getElementById('command-error');
var cmdResult = document.getElementById('command-result');
var cmdSubmit = document.getElementById('command-submit-btn');
var cmdClear = document.getElementById('command-clear-btn');
var profileSelect = document.getElementById('profile-select');

function renderCommandResult() {
  cmdError.textContent = '';
  cmdResult.innerHTML = '';

  if (state.command.status === 'submitting') {
    cmdResult.appendChild(el('div', 'loading', 'Submitting...'));
    return;
  }

  if (state.command.error) {
    cmdError.textContent = state.command.error;
    return;
  }

  if (state.command.result) {
    var r = state.command.result;
    var pre = el('pre');
    var text = JSON.stringify(r, null, 2);
    // Truncate long results
    if (text.length > 3000) text = text.substring(0, 3000) + '\n... (truncated)';
    pre.textContent = text;
    var cls = r.ok === false ? 'result-fail' : 'result-success';
    pre.className = cls;
    cmdResult.appendChild(pre);
  }
}

cmdSubmit.addEventListener('click', function() {
  var command = cmdInput.value.trim();
  var profile = profileSelect.value;

  // Validation
  if (!command) {
    cmdError.textContent = 'Command must not be empty.';
    return;
  }
  if (command.length > 2000) {
    cmdError.textContent = 'Command exceeds 2000 characters.';
    return;
  }

  state.command.status = 'submitting';
  state.command.error = null;
  state.command.result = null;
  renderCommandResult();
  cmdSubmit.disabled = true;

  apiPost('/command', { command: command, profile: profile }).then(function(resp) {
    state.command.status = 'idle';
    state.command.result = resp;
  }).catch(function(err) {
    state.command.status = 'idle';
    state.command.error = err.message;
  }).finally(function() {
    renderCommandResult();
    cmdSubmit.disabled = false;
  });
});

cmdClear.addEventListener('click', function() {
  cmdInput.value = '';
  cmdError.textContent = '';
  cmdResult.innerHTML = '';
  state.command = { status: 'idle', result: null, error: null };
});

// ─── Tasks Panel ───
function renderTasks(body) {
  var container = body || document.getElementById('tasks-body');
  if (state.tasks.status === 'loading') { showLoading(container); return; }
  if (state.tasks.status === 'error') { showError(container, state.tasks.error, refreshTasks); return; }

  var tasks = state.tasks.data || [];
  if (tasks.length === 0) { showEmpty(container, 'No tasks yet'); return; }

  container.innerHTML = '';
  container.appendChild(el('h3', '', 'Tasks (' + tasks.length + ')'));

  var cols = ['Task ID', 'Status', 'Type', 'Risk', 'Created'];
  var rows = tasks.slice(0, 20).map(function(t) {
    return [
      el('span', 'mono', (t.task_id || '').substring(0, 16)),
      badge(t.status || '?', 'status-' + (t.status || '')),
      t.execution_type || '?',
      t.risk_level || '?',
      (t.created_at || '').substring(0, 19)
    ];
  });
  container.appendChild(buildTable(cols, rows));

  // Task Trees sub-section
  var trees = state.taskTrees.data || [];
  if (trees.length > 0) {
    container.appendChild(el('h3', '', 'Task Trees (' + trees.length + ')'));
    var treeCols = ['Tree ID', 'Status', 'Risk', 'Created'];
    var treeRows = trees.slice(0, 20).map(function(tr) {
      return [
        el('span', 'mono', (tr.task_tree_id || '').substring(0, 16)),
        badge(tr.status || '?', 'status-' + (tr.status || '')),
        tr.risk_level || '?',
        (tr.created_at || '').substring(0, 19)
      ];
    });
    container.appendChild(buildTable(treeCols, treeRows));
  }
}

function refreshTasks() {
  state.tasks.status = 'loading';
  state.taskTrees.status = 'loading';
  renderTasks();

  Promise.all([
    apiGet('/tasks?limit=20').then(function(r) {
      state.tasks.status = 'success'; state.tasks.data = r.data.tasks || [];
    }).catch(function(e) {
      state.tasks.status = 'error'; state.tasks.error = e.message;
    }),
    apiGet('/task-trees?limit=20').then(function(r) {
      state.taskTrees.status = 'success'; state.taskTrees.data = r.data.task_trees || [];
    }).catch(function(e) {
      state.taskTrees.status = 'error'; state.taskTrees.error = e.message;
    })
  ]).finally(function() { renderTasks(); });
}

// ─── Task Runs Panel ───
function renderTaskRuns(body) {
  var container = body || document.getElementById('runs-body');
  if (state.taskRuns.status === 'loading') { showLoading(container); return; }
  if (state.taskRuns.status === 'error') { showError(container, state.taskRuns.error, refreshTaskRuns); return; }

  var runs = state.taskRuns.data || [];
  if (runs.length === 0) { showEmpty(container, 'No task runs yet'); return; }

  container.innerHTML = '';
  var cols = ['Run ID', 'Task ID', 'Status', 'Dry Run', 'Exit', 'Started'];
  var rows = runs.slice(0, 20).map(function(r) {
    return [
      el('span', 'mono', (r.task_run_id || '').substring(0, 16)),
      el('span', 'mono', (r.task_id || '').substring(0, 16)),
      badge(r.status || '?', 'status-' + (r.status || '')),
      r.dry_run ? 'yes' : 'no',
      r.exit_code !== undefined ? String(r.exit_code) : '-',
      (r.started_at || '').substring(0, 19)
    ];
  });
  container.appendChild(buildTable(cols, rows));
}

function refreshTaskRuns() {
  state.taskRuns.status = 'loading';
  renderTaskRuns();
  apiGet('/task-runs?limit=20').then(function(resp) {
    state.taskRuns.status = 'success';
    state.taskRuns.data = resp.data.task_runs || [];
  }).catch(function(err) {
    state.taskRuns.status = 'error';
    state.taskRuns.error = err.message;
  }).finally(function() { renderTaskRuns(); });
}

// ─── MAS Trace Panel ───
function renderTrace(body) {
  var container = body || document.getElementById('trace-body');
  if (state.masTrace.status === 'loading') { showLoading(container); return; }
  if (state.masTrace.status === 'error') { showError(container, state.masTrace.error, refreshTrace); return; }

  var traces = state.masTrace.data || [];
  if (traces.length === 0) { showEmpty(container, 'No trace entries yet'); return; }

  container.innerHTML = '';
  var cols = ['Time', 'Event', 'Command', 'Task', 'Detail'];
  var rows = traces.slice(0, 50).map(function(t) {
    var eventCls = 'event-badge';
    if (t.event && t.event.indexOf('runner_') === 0) eventCls += ' event-runner';
    else if (t.event && t.event.indexOf('routed') === 0) eventCls += ' event-routed';
    else if (t.event && t.event.indexOf('command_') === 0) eventCls += ' event-command';
    else if (t.event && t.event.indexOf('task_tree') === 0) eventCls += ' event-tree';

    return [
      (t.timestamp || '').substring(0, 19),
      el('span', eventCls, t.event || '?'),
      el('span', 'mono', (t.command_id || '').substring(0, 14)),
      el('span', 'mono', (t.task_id || '').substring(0, 14)),
      (t.detail || '').substring(0, 60)
    ];
  });
  container.appendChild(buildTable(cols, rows));
}

function refreshTrace() {
  state.masTrace.status = 'loading';
  renderTrace();
  apiGet('/mas-trace?limit=50').then(function(resp) {
    state.masTrace.status = 'success';
    state.masTrace.data = resp.data.mas_trace || [];
  }).catch(function(err) {
    state.masTrace.status = 'error';
    state.masTrace.error = err.message;
  }).finally(function() { renderTrace(); });
}

// ─── Local dashboard and remote provider setup ───
var localDashboardUrl = document.getElementById('local-dashboard-url');
var localApiResult = document.getElementById('local-api-result');
var testLocalApiBtn = document.getElementById('test-local-api-btn');
var providerForm = document.getElementById('provider-config-form');
var providerBaseUrl = document.getElementById('provider-base-url');
var providerModel = document.getElementById('provider-model');
var providerApiKey = document.getElementById('provider-api-key');
var providerInputPrice = document.getElementById('provider-input-price');
var providerOutputPrice = document.getElementById('provider-output-price');
var providerBudget = document.getElementById('provider-budget');
var providerResult = document.getElementById('provider-result');
var testProviderBtn = document.getElementById('test-provider-btn');

function providerPayload() {
  return {
    base_url: providerBaseUrl.value.trim(),
    model: providerModel.value.trim(),
    api_key: providerApiKey.value,
    input_price_per_million: providerInputPrice.value,
    output_price_per_million: providerOutputPrice.value,
    monthly_budget_usd: providerBudget.value
  };
}

function renderProviderStatus(data) {
  if (!providerResult) return;
  if (!data || !data.configured) {
    providerResult.textContent = '未配置远程模型。保存配置不会发起远程请求。';
    return;
  }
  providerBaseUrl.value = data.base_url || '';
  providerModel.value = data.model || '';
  providerInputPrice.value = data.input_price_per_million === null ? '' : (data.input_price_per_million || '');
  providerOutputPrice.value = data.output_price_per_million === null ? '' : (data.output_price_per_million || '');
  providerBudget.value = data.monthly_budget_usd === null ? '' : (data.monthly_budget_usd || '');
  providerApiKey.value = '';
  providerResult.textContent = '已配置 ' + (data.model || '远程模型') + '。API Key 已保存但不会显示；留空不会修改现有密钥。';
}

function refreshProviderStatus() {
  return apiGet('/model/provider').then(function(resp) {
    renderProviderStatus(resp.data || {});
  }).catch(function(error) {
    if (providerResult) providerResult.textContent = '无法读取远程模型配置：' + error.message;
  });
}

function testLocalApi() {
  if (localApiResult) localApiResult.textContent = '正在检测本地服务...';
  apiGet('/health').then(function(resp) {
    if (localApiResult) localApiResult.textContent = resp.ok ? '本地服务在线，可使用工作台。' : '本地服务返回了未就绪状态。';
  }).catch(function(error) {
    if (localApiResult) localApiResult.textContent = '本地服务不可用：' + error.message;
  });
}

if (localDashboardUrl) localDashboardUrl.textContent = window.location.href;
if (testLocalApiBtn) testLocalApiBtn.addEventListener('click', testLocalApi);
if (providerForm) providerForm.addEventListener('submit', function(event) {
  event.preventDefault();
  if (!providerApiKey.value) {
    providerResult.textContent = '首次保存必须填写 API Key。已配置后请重新填写完整表单以更新配置。';
    return;
  }
  providerResult.textContent = '正在保存本机私有配置...';
  apiPost('/model/provider', providerPayload()).then(function(resp) {
    renderProviderStatus(resp.data || {});
    showToast('远程模型配置已保存到本机私有目录。', 'success');
  }).catch(function(error) {
    providerResult.textContent = '保存失败：' + error.message;
  });
});
if (testProviderBtn) testProviderBtn.addEventListener('click', function() {
  providerResult.textContent = '正在检测远程模型连接...';
  apiPost('/model/provider/test', {}).then(function(resp) {
    providerResult.textContent = '远程模型连接成功。可见模型数：' + (resp.data.model_count === null ? '未提供' : resp.data.model_count) + '。';
  }).catch(function(error) {
    providerResult.textContent = '连接失败：' + error.message;
  });
});

// ─── API Status Check ───
function updateApiBadge() {
  if (state.health.status === 'error') {
    apiBadge.textContent = '离线';
    apiBadge.style.background = 'var(--red)';
  } else if (state.health.status === 'loading') {
    apiBadge.textContent = '检测中';
    apiBadge.style.background = 'var(--yellow)';
  } else {
    apiBadge.textContent = '在线';
    apiBadge.style.background = 'var(--green)';
  }
  apiUrlEl.textContent = API_BASE;
}

// ─── Refresh All ───
function refreshAll() {
  refreshHealth();
  refreshTasks();
  refreshTaskRuns();
  refreshTrace();
  refreshGrowth();
  refreshCareer();
  refreshAutomation();
  refreshSkills();
  refreshKnowledge();
  refreshModelCost();
  refreshProviderStatus();
  refreshMcpTools();
  setTimeout(updateApiBadge, 1000);
}

refreshAllBtn.addEventListener('click', function() {
  refreshAllBtn.classList.add('is-refreshing');
  refreshAll();
  window.setTimeout(function() { refreshAllBtn.classList.remove('is-refreshing'); }, 560);
});

// ─── Auto-refresh ───
function startAutoRefresh() {
  if (refreshTimer) clearInterval(refreshTimer);
  refreshTimer = setInterval(function() {
    refreshHealth();
    refreshTasks();
    refreshTaskRuns();
    refreshTrace();
    refreshGrowth();
    refreshCareer();
    refreshAutomation();
    refreshSkills();
    refreshKnowledge();
    refreshModelCost();
    refreshMcpTools();
    updateApiBadge();
  }, REFRESH_MS);
}

// ─── Memory Center Panel ───
var memoryRefreshBtn = document.getElementById('memory-refresh-btn');

state.memories = { status: 'loading', data: [], error: null };
state.memCandidates = { status: 'loading', data: [], error: null };
state.memProposals = { status: 'loading', data: [], error: null };
state.memReviews = { status: 'loading', data: [], error: null };
state.memConflicts = { status: 'loading', data: [], error: null };
state.memChanges = { status: 'loading', data: [], error: null };
state.memSnapshots = { status: 'loading', data: [], error: null };

function renderMemory(body) {
  var container = body || document.getElementById('memory-body');
  if (state.memories.status === 'loading') { showLoading(container); return; }
  if (state.memories.status === 'error') { showError(container, state.memories.error, refreshMemory); return; }

  var memories = state.memories.data || [];
  var candidates = state.memCandidates.data || [];
  var proposals = state.memProposals.data || [];
  var reviews = state.memReviews.data || [];
  var conflicts = state.memConflicts.data || [];
  var changes = state.memChanges.data || [];
  var snapshots = state.memSnapshots.data || [];

  container.innerHTML = '';

  // Create Candidate form
  var formDiv = el('div', 'memory-form');
  formDiv.appendChild(el('h3', '', 'Create Candidate'));
  var input = el('input');
  input.type = 'text'; input.id = 'mem-content'; input.placeholder = zh('Memory content...'); input.maxLength = 4000;
  formDiv.appendChild(input);
  var typeSel = el('select'); typeSel.id = 'mem-type';
  ['project_decision','user_preference','system_rule','workflow_preference'].forEach(function(t) {
    var o = el('option'); o.value = t; o.textContent = t; typeSel.appendChild(o);
  });
  formDiv.appendChild(typeSel);
  var submitBtn = el('button', 'btn btn-primary', 'Create');
  submitBtn.onclick = function() {
    var c = document.getElementById('mem-content').value.trim();
    var t = document.getElementById('mem-type').value;
    if (!c) { document.getElementById('mem-result').textContent = 'Content required'; return; }
    state.command.status = 'submitting';
    apiPost('/memory/candidates', {content: c, memory_type: t, source_type: 'manual', source_agent: 'user', sensitivity: 'personal'})
      .then(function(r) { document.getElementById('mem-result').textContent = 'Created: ' + (r.data && r.data.candidate_id); refreshMemory(); })
      .catch(function(e) { document.getElementById('mem-result').textContent = 'Error: ' + e.message; });
  };
  formDiv.appendChild(submitBtn);
  var resultSpan = el('span', ''); resultSpan.id = 'mem-result';
  formDiv.appendChild(resultSpan);
  container.appendChild(formDiv);

  // Active Memories
  container.appendChild(el('h3', '', 'Active Memories (' + memories.length + ')'));
  if (memories.length === 0) { container.appendChild(el('div', 'empty', 'No active memories')); }
  else {
  var memCols = ['ID', 'Type', 'Content', 'Status', 'Actions'];
  var memRows = memories.slice(0, 10).map(function(m) {
    return [
      el('span', 'mono', (m.memory_id || '').substring(0, 14)),
      m.memory_type || '?',
      (m.content || '').substring(0, 80),
      badge(m.status || '?', 'status-' + (m.status || '')),
      (function() {
        var wrap = el('span', 'action-row');
        var r = el('button', 'btn btn-sm', 'Review');
        r.onclick = function() { apiPost('/memory/reviews', {target_type: 'entry', target_ref: m.memory_id}).then(function() { refreshMemory(); }).catch(handleActionError); };
        var a = el('button', 'btn btn-sm', 'Archive');
        a.onclick = function() { apiPost('/memory/archive', {memory_id: m.memory_id, reason: 'manual'}).then(function() { refreshMemory(); }).catch(handleActionError); };
        wrap.appendChild(r); wrap.appendChild(a); return wrap;
      })()
    ];
  });
  container.appendChild(buildTable(memCols, memRows));
  }

  var snapshotBtn = el('button', 'btn btn-sm', 'Snapshot');
  snapshotBtn.onclick = function() {
    apiPost('/memory/snapshots', {reason: 'dashboard snapshot before memory change'})
      .then(function() { refreshMemory(); })
      .catch(handleActionError);
  };
  container.appendChild(snapshotBtn);

  // Candidates
  container.appendChild(el('h3', '', 'Candidates (' + candidates.length + ')'));
  var candCols = ['Candidate ID', 'Type', 'Summary', 'Status', 'Actions'];
  var candRows = candidates.slice(0, 10).map(function(c) {
    return [
      el('span', 'mono', (c.candidate_id || '').substring(0, 14)),
      c.memory_type || '?',
      (c.content_summary || '').substring(0, 60),
      badge(c.status || '?', 'status-' + (c.status || '')),
      (function() {
        var wrap = el('span', 'action-row');
        var review = el('button', 'btn btn-sm', 'Review');
        review.onclick = function() { apiPost('/memory/reviews', {target_type: 'candidate', target_ref: c.candidate_id}).then(function() { refreshMemory(); }).catch(handleActionError); };
        var check = el('button', 'btn btn-sm', 'Check');
        check.onclick = function() { apiPost('/memory/conflicts', {target_type: 'candidate', target_ref: c.candidate_id}).then(function() { refreshMemory(); }).catch(handleActionError); };
        wrap.appendChild(review); wrap.appendChild(check);
        if (c.status === 'captured' || c.status === 'draft') {
          var a = el('button', 'btn btn-sm', 'Propose');
          a.onclick = function() { apiPost('/memory/proposals', {candidate_id: c.candidate_id}).then(function() { refreshMemory(); }).catch(handleActionError); };
          wrap.appendChild(a);
        }
        return wrap;
      })()
    ];
  });
  container.appendChild(buildTable(candCols, candRows));

  // Proposals
  container.appendChild(el('h3', '', 'Proposals (' + proposals.length + ')'));
  var propCols = ['Proposal ID', 'Type', 'Status', 'Actions'];
  var propRows = proposals.slice(0, 10).map(function(p) {
    return [
      el('span', 'mono', (p.proposal_id || '').substring(0, 14)),
      p.memory_type || '?',
      badge(p.status || '?', 'status-' + (p.status || '')),
      (p.status === 'approved' ? (function() { var a = el('button', 'btn btn-sm', 'Store'); a.onclick = function() { apiPost('/memory/store', {proposal_id: p.proposal_id}).then(function() { refreshMemory(); }).catch(handleActionError); }; return a; })() : el('span', '', ''))
    ];
  });
  container.appendChild(buildTable(propCols, propRows));

  container.appendChild(el('h3', '', 'Quality Reviews (' + reviews.length + ')'));
  var reviewRows = reviews.slice(0, 10).map(function(r) {
    return [
      el('span', 'mono', (r.memory_quality_review_id || '').substring(0, 14)),
      r.target_type || '?',
      el('span', 'mono', (r.target_ref || '').substring(0, 14)),
      r.recommendation || '?',
      r.overall_score !== undefined ? String(r.overall_score) : ''
    ];
  });
  container.appendChild(buildTable(['Review ID', 'Target', 'Ref', 'Recommendation', 'Score'], reviewRows));

  container.appendChild(el('h3', '', 'Conflicts (' + conflicts.length + ')'));
  var conflictRows = conflicts.slice(0, 10).map(function(c) {
    return [
      el('span', 'mono', (c.memory_conflict_id || '').substring(0, 14)),
      c.conflict_type || '?',
      c.severity || '?',
      badge(c.status || '?', 'status-' + (c.status || '')),
      (c.existing_memory_refs || []).length
    ];
  });
  container.appendChild(buildTable(['Conflict ID', 'Type', 'Severity', 'Status', 'Refs'], conflictRows));

  container.appendChild(el('h3', '', 'Change Requests (' + changes.length + ')'));
  var changeRows = changes.slice(0, 10).map(function(c) {
    return [
      el('span', 'mono', (c.memory_change_request_id || '').substring(0, 14)),
      c.change_type || '?',
      c.risk_level || '?',
      badge(c.status || '?', 'status-' + (c.status || '')),
      c.requires_user_approval ? 'required' : 'not required'
    ];
  });
  container.appendChild(buildTable(['Change ID', 'Type', 'Risk', 'Status', 'Approval'], changeRows));

  container.appendChild(el('h3', '', 'Snapshots (' + snapshots.length + ')'));
  var snapRows = snapshots.slice(0, 10).map(function(s) {
    return [
      el('span', 'mono', (s.memory_snapshot_id || '').substring(0, 14)),
      s.entry_count !== undefined ? String(s.entry_count) : '',
      badge(s.status || '?', 'status-' + (s.status || '')),
      (s.created_at || '').substring(0, 19)
    ];
  });
  container.appendChild(buildTable(['Snapshot ID', 'Entries', 'Status', 'Created'], snapRows));
}

function refreshMemory() {
  state.memories.status = 'loading'; state.memCandidates.status = 'loading'; state.memProposals.status = 'loading';
  state.memReviews.status = 'loading'; state.memConflicts.status = 'loading'; state.memChanges.status = 'loading'; state.memSnapshots.status = 'loading';
  renderMemory();
  Promise.all([
    apiGet('/memory?limit=20').then(function(r) { state.memories.status = 'success'; state.memories.data = r.data.memories || []; })
      .catch(function(e) { state.memories.status = 'error'; state.memories.error = e.message; }),
    apiGet('/memory/candidates?limit=20').then(function(r) { state.memCandidates.status = 'success'; state.memCandidates.data = r.data.candidates || []; })
      .catch(function(e) { state.memCandidates.status = 'error'; state.memCandidates.error = e.message; }),
    apiGet('/memory/proposals?limit=20').then(function(r) { state.memProposals.status = 'success'; state.memProposals.data = r.data.proposals || []; })
      .catch(function(e) { state.memProposals.status = 'error'; state.memProposals.error = e.message; }),
    apiGet('/memory/reviews?limit=20').then(function(r) { state.memReviews.status = 'success'; state.memReviews.data = r.data.reviews || []; })
      .catch(function(e) { state.memReviews.status = 'error'; state.memReviews.error = e.message; }),
    apiGet('/memory/conflicts?limit=20').then(function(r) { state.memConflicts.status = 'success'; state.memConflicts.data = r.data.conflicts || []; })
      .catch(function(e) { state.memConflicts.status = 'error'; state.memConflicts.error = e.message; }),
    apiGet('/memory/changes?limit=20').then(function(r) { state.memChanges.status = 'success'; state.memChanges.data = r.data.changes || []; })
      .catch(function(e) { state.memChanges.status = 'error'; state.memChanges.error = e.message; }),
    apiGet('/memory/snapshots?limit=20').then(function(r) { state.memSnapshots.status = 'success'; state.memSnapshots.data = r.data.snapshots || []; })
      .catch(function(e) { state.memSnapshots.status = 'error'; state.memSnapshots.error = e.message; }),
  ]).finally(function() { renderMemory(); });
}

if (memoryRefreshBtn) { memoryRefreshBtn.addEventListener('click', refreshMemory); }

// ─── Research Panel ───
var researchRefreshBtn = document.getElementById('research-refresh-btn');
state.research = { sources: { status:'loading', data:[], error:null }, packets: { status:'loading', data:[], error:null }, cards: { status:'loading', data:[], error:null } };

function renderResearch(body) {
  var c = body || document.getElementById('research-body');
  if (state.research.sources.status === 'loading') { showLoading(c); return; }
  c.innerHTML = '';
  var srcs = state.research.sources.data || [], pkts = state.research.packets.data || [], cards = state.research.cards.data || [];
  var formDiv = el('div', 'memory-form');
  formDiv.appendChild(el('h3','','Create Source'));
  var inp = el('input'); inp.type='text'; inp.id='rsrc-content'; inp.placeholder=zh('Source content...'); inp.maxLength=2000; formDiv.appendChild(inp);
  var tsel = el('select'); tsel.id='rsrc-type'; ['manual_text','article_summary','paper_summary'].forEach(function(t){var o=el('option');o.value=t;o.textContent=t;tsel.appendChild(o)}); formDiv.appendChild(tsel);
  var btn = el('button','btn btn-primary','Create'); btn.onclick=function(){var ct=document.getElementById('rsrc-content').value.trim();if(!ct){showToast('Content required','error');return}apiPost('/research/sources',{title:'Research Source',content_summary:ct,source_type:document.getElementById('rsrc-type').value}).then(function(){refreshResearch()}).catch(handleActionError)}; formDiv.appendChild(btn);
  c.appendChild(formDiv);
  c.appendChild(el('h3','','Sources ('+srcs.length+')'));
  c.appendChild(el('h3','','Packets ('+pkts.length+')'));
  c.appendChild(el('h3','','Cognition Cards ('+cards.length+')'));
}

function refreshResearch() {
  state.research.sources.status='loading'; state.research.packets.status='loading'; state.research.cards.status='loading'; renderResearch();
  Promise.all([
    apiGet('/research/sources?limit=10').then(function(r){state.research.sources.status='success';state.research.sources.data=r.data.sources||[]}).catch(function(e){state.research.sources.status='error'}),
    apiGet('/research/packets?limit=10').then(function(r){state.research.packets.status='success';state.research.packets.data=r.data.packets||[]}).catch(function(e){state.research.packets.status='error'}),
    apiGet('/research/cognition-cards?limit=10').then(function(r){state.research.cards.status='success';state.research.cards.data=r.data.cards||[]}).catch(function(e){state.research.cards.status='error'})
  ]).finally(function(){renderResearch()});
}
if(researchRefreshBtn){researchRefreshBtn.addEventListener('click',refreshResearch)}

// Growth Center Panel
var growthRefreshBtn = document.getElementById('growth-refresh-btn');
state.growth = {
  candidates: { status:'loading', data:[], error:null },
  goals: { status:'loading', data:[], error:null },
  capacity: { status:'loading', data:[], error:null },
  weekly: { status:'loading', data:[], error:null },
  tasks: { status:'loading', data:[], error:null },
  reviews: { status:'loading', data:[], error:null },
  adjustments: { status:'loading', data:[], error:null },
  handoffs: { status:'loading', data:[], error:null }
};

function shortText(value, max) {
  var text = value !== null && value !== undefined ? String(value) : '';
  return text.length > max ? text.substring(0, max) : text;
}

function idCell(value) {
  return el('span', 'mono', shortText(value || '', 14));
}

function appendGrowthTable(container, title, columns, rows, emptyText) {
  var section = el('div', 'growth-section');
  section.appendChild(el('h3', '', title + ' (' + rows.length + ')'));
  if (rows.length === 0) {
    section.appendChild(el('div', 'empty', emptyText || 'No data'));
  } else {
    section.appendChild(buildTable(columns, rows));
  }
  container.appendChild(section);
}

function renderGrowth(body) {
  var container = body || document.getElementById('growth-body');
  if (state.growth.candidates.status === 'loading') { showLoading(container); return; }
  if (state.growth.candidates.status === 'error') { showError(container, state.growth.candidates.error, refreshGrowth); return; }

  var candidates = state.growth.candidates.data || [];
  var goals = state.growth.goals.data || [];
  var capacity = state.growth.capacity.data || [];
  var weekly = state.growth.weekly.data || [];
  var tasks = state.growth.tasks.data || [];
  var reviews = state.growth.reviews.data || [];
  var adjustments = state.growth.adjustments.data || [];

  container.innerHTML = '';

  var formDiv = el('div', 'memory-form');
  formDiv.appendChild(el('h3', '', 'Create Candidate'));
  var title = el('input'); title.type = 'text'; title.id = 'growth-title'; title.placeholder = zh('Goal title'); title.maxLength = 2000; formDiv.appendChild(title);
  var area = el('select'); area.id = 'growth-area';
  ['ai_engineering','data_analysis','career','research','communication','productivity','personal_project','other'].forEach(function(v){var o=el('option');o.value=v;o.textContent=v;area.appendChild(o)});
  formDiv.appendChild(area);
  var reason = el('input'); reason.type = 'text'; reason.id = 'growth-reason'; reason.placeholder = 'Reason'; reason.maxLength = 2000; formDiv.appendChild(reason);
  var btn = el('button', 'btn btn-primary', 'Create');
  btn.onclick = function() {
    var t = document.getElementById('growth-title').value.trim();
    var r = document.getElementById('growth-reason').value.trim();
    if (!t) { document.getElementById('growth-result').textContent = 'Title required'; return; }
    apiPost('/growth/candidates', {title: t, goal_area: document.getElementById('growth-area').value, reason: r, source_type: 'manual'})
      .then(function(resp){ document.getElementById('growth-result').textContent = 'Created: ' + (resp.data && resp.data.candidate_id); refreshGrowth(); })
      .catch(function(e){ document.getElementById('growth-result').textContent = 'Error: ' + e.message; });
  };
  formDiv.appendChild(btn);
  var result = el('span', ''); result.id = 'growth-result'; formDiv.appendChild(result);
  container.appendChild(formDiv);

  appendGrowthTable(container, 'Candidates', ['ID','Title','Area','Status','Action'], candidates.slice(0, 10).map(function(c) {
    return [
      idCell(c.candidate_id),
      shortText(c.title, 48),
      c.goal_area || '?',
      badge(c.status || '?', 'status-' + (c.status || '')),
      (c.status === 'captured' ? (function(){var a=el('button','btn btn-sm','Accept');a.onclick=function(){apiPost('/growth/candidates/accept',{candidate_id:c.candidate_id}).then(function(){refreshGrowth()}).catch(handleActionError)};return a;})() : el('span','',''))
    ];
  }), 'No growth candidates');

  appendGrowthTable(container, 'Goals', ['ID','Title','Area','Status','Priority'], goals.slice(0, 10).map(function(g) {
    return [idCell(g.goal_id), shortText(g.title, 54), g.goal_area || '?', badge(g.status || '?', 'status-' + (g.status || '')), g.priority || '?'];
  }), 'No active goals');

  appendGrowthTable(container, 'Capacity', ['ID','Hours','Energy','Overload','Created'], capacity.slice(0, 10).map(function(c) {
    return [idCell(c.budget_id), c.available_hours, c.energy_level || '?', c.overload_warning ? 'yes' : 'no', shortText(c.created_at, 19)];
  }), 'No capacity budgets');

  appendGrowthTable(container, 'Weekly Plans', ['ID','Week','Theme','Status','Goals'], weekly.slice(0, 10).map(function(w) {
    return [idCell(w.weekly_plan_id), w.week_start || '?', shortText(w.focus_theme, 32), badge(w.status || '?', 'status-' + (w.status || '')), (w.goal_ids || []).length];
  }), 'No weekly plans');

  appendGrowthTable(container, 'Daily Tasks', ['ID','Date','Title','Status','Minutes'], tasks.slice(0, 10).map(function(t) {
    return [idCell(t.task_id), t.date || '?', shortText(t.title, 48), badge(t.status || '?', 'status-' + (t.status || '')), t.estimated_minutes || ''];
  }), 'No daily tasks');

  appendGrowthTable(container, 'Reviews', ['ID','Goal','Rating','Status','Blockers'], reviews.slice(0, 10).map(function(r) {
    return [idCell(r.review_id), idCell(r.goal_id), r.self_rating || '', badge(r.status || '?', 'status-' + (r.status || '')), (r.blockers || []).length];
  }), 'No reviews');

  appendGrowthTable(container, 'Adjustments', ['ID','Goal','Type','Risk','Approval'], adjustments.slice(0, 10).map(function(a) {
    return [idCell(a.proposal_id), idCell(a.goal_id), a.proposal_type || '?', a.risk_level || '?', a.approval_required ? 'required' : 'not required'];
  }), 'No adjustments');
}

function refreshGrowth() {
  Object.keys(state.growth).forEach(function(k){ state.growth[k].status = 'loading'; });
  renderGrowth();
  Promise.all([
    apiGet('/growth/candidates?limit=20').then(function(r){state.growth.candidates.status='success';state.growth.candidates.data=r.data.candidates||[]}).catch(function(e){state.growth.candidates.status='error';state.growth.candidates.error=e.message}),
    apiGet('/growth/goals?limit=20').then(function(r){state.growth.goals.status='success';state.growth.goals.data=r.data.goals||[]}).catch(function(e){state.growth.goals.status='error';state.growth.goals.error=e.message}),
    apiGet('/growth/capacity?limit=20').then(function(r){state.growth.capacity.status='success';state.growth.capacity.data=r.data.capacity||[]}).catch(function(e){state.growth.capacity.status='error';state.growth.capacity.error=e.message}),
    apiGet('/growth/weekly-plans?limit=20').then(function(r){state.growth.weekly.status='success';state.growth.weekly.data=r.data.weekly_plans||[]}).catch(function(e){state.growth.weekly.status='error';state.growth.weekly.error=e.message}),
    apiGet('/growth/daily-tasks?limit=20').then(function(r){state.growth.tasks.status='success';state.growth.tasks.data=r.data.daily_tasks||[]}).catch(function(e){state.growth.tasks.status='error';state.growth.tasks.error=e.message}),
    apiGet('/growth/reviews?limit=20').then(function(r){state.growth.reviews.status='success';state.growth.reviews.data=r.data.reviews||[]}).catch(function(e){state.growth.reviews.status='error';state.growth.reviews.error=e.message}),
    apiGet('/growth/adjustments?limit=20').then(function(r){state.growth.adjustments.status='success';state.growth.adjustments.data=r.data.adjustments||[]}).catch(function(e){state.growth.adjustments.status='error';state.growth.adjustments.error=e.message}),
    apiGet('/growth/handoffs?limit=20').then(function(r){state.growth.handoffs.status='success';state.growth.handoffs.data=r.data.handoffs||[]}).catch(function(e){state.growth.handoffs.status='error';state.growth.handoffs.error=e.message})
  ]).finally(function(){renderGrowth()});
}

if(growthRefreshBtn){growthRefreshBtn.addEventListener('click',refreshGrowth)}

// Career Center Panel
var careerRefreshBtn = document.getElementById('career-refresh-btn');
state.career = {
  assets: { status:'loading', data:[], error:null },
  claims: { status:'loading', data:[], error:null },
  jds: { status:'loading', data:[], error:null },
  evaluations: { status:'loading', data:[], error:null },
  applications: { status:'loading', data:[], error:null },
  handoffs: { status:'loading', data:[], error:null }
};

function renderCareer(body) {
  var container = body || document.getElementById('career-body');
  if (state.career.assets.status === 'loading') { showLoading(container); return; }
  if (state.career.assets.status === 'error') { showError(container, state.career.assets.error, refreshCareer); return; }

  var assets = state.career.assets.data || [];
  var claims = state.career.claims.data || [];
  var jds = state.career.jds.data || [];
  var evaluations = state.career.evaluations.data || [];
  var applications = state.career.applications.data || [];
  var handoffs = state.career.handoffs.data || [];
  container.innerHTML = '';

  var formDiv = el('div', 'memory-form');
  formDiv.appendChild(el('h3', '', 'Create Asset'));
  var title = el('input'); title.type = 'text'; title.id = 'career-asset-title'; title.placeholder = zh('Asset title'); title.maxLength = 2000; formDiv.appendChild(title);
  var type = el('select'); type.id = 'career-asset-type';
  ['project','experience','education','certificate','portfolio','skill','other'].forEach(function(v){var o=el('option');o.value=v;o.textContent=v;type.appendChild(o)});
  formDiv.appendChild(type);
  var evidence = el('input'); evidence.type = 'text'; evidence.id = 'career-evidence'; evidence.placeholder = 'Evidence refs, comma-separated'; evidence.maxLength = 2000; formDiv.appendChild(evidence);
  var btn = el('button', 'btn btn-primary', 'Create');
  btn.onclick = function() {
    var t = document.getElementById('career-asset-title').value.trim();
    if (!t) { document.getElementById('career-result').textContent = 'Title required'; return; }
    apiPost('/career/assets', {title: t, asset_type: document.getElementById('career-asset-type').value, evidence_refs: document.getElementById('career-evidence').value})
      .then(function(resp){ document.getElementById('career-result').textContent = 'Created: ' + (resp.data && resp.data.asset_id); refreshCareer(); })
      .catch(function(e){ document.getElementById('career-result').textContent = 'Error: ' + e.message; });
  };
  formDiv.appendChild(btn);
  var result = el('span', ''); result.id = 'career-result'; formDiv.appendChild(result);
  container.appendChild(formDiv);

  appendGrowthTable(container, 'Assets', ['ID','Type','Title','Evidence','Status'], assets.slice(0, 10).map(function(a) {
    return [idCell(a.asset_id), a.asset_type || '?', shortText(a.title, 48), (a.evidence_refs || []).length, badge(a.status || '?', 'status-' + (a.status || ''))];
  }), 'No career assets');

  appendGrowthTable(container, 'Claims', ['ID','Claim','Assets','Confidence','Status'], claims.slice(0, 10).map(function(c) {
    return [idCell(c.claim_id), shortText(c.claim_text, 64), (c.asset_refs || []).length, c.confidence, badge(c.status || '?', 'status-' + (c.status || ''))];
  }), 'No resume claims');

  appendGrowthTable(container, 'Job Descriptions', ['ID','Title','Company','Requirements','Status'], jds.slice(0, 10).map(function(j) {
    return [idCell(j.jd_id), shortText(j.title, 42), shortText(j.company, 24), (j.requirements || []).length, badge(j.status || '?', 'status-' + (j.status || ''))];
  }), 'No job descriptions');

  appendGrowthTable(container, 'Evaluations', ['ID','JD','Score','Recommendation','Status'], evaluations.slice(0, 10).map(function(e) {
    return [idCell(e.evaluation_id), idCell(e.jd_ref), e.score, e.recommendation || '?', badge(e.status || '?', 'status-' + (e.status || ''))];
  }), 'No JD evaluations');

  appendGrowthTable(container, 'Applications', ['ID','JD','Status','Auto Submit','Created'], applications.slice(0, 10).map(function(a) {
    return [idCell(a.application_id), idCell(a.jd_ref), badge(a.status || '?', 'status-' + (a.status || '')), a.auto_submit ? 'yes' : 'no', shortText(a.created_at, 19)];
  }), 'No application records');

  appendGrowthTable(container, 'Career Handoffs', ['ID','Source','Summary','Status'], handoffs.slice(0, 10).map(function(h) {
    return [idCell(h.handoff_id), (h.source_type || '?') + ':' + shortText(h.source_id, 12), shortText(h.summary, 64), badge(h.status || '?', 'status-' + (h.status || ''))];
  }), 'No career handoffs');
}

function refreshCareer() {
  Object.keys(state.career).forEach(function(k){ state.career[k].status = 'loading'; });
  renderCareer();
  Promise.all([
    apiGet('/career/assets?limit=20').then(function(r){state.career.assets.status='success';state.career.assets.data=r.data.assets||[]}).catch(function(e){state.career.assets.status='error';state.career.assets.error=e.message}),
    apiGet('/career/claims?limit=20').then(function(r){state.career.claims.status='success';state.career.claims.data=r.data.claims||[]}).catch(function(e){state.career.claims.status='error';state.career.claims.error=e.message}),
    apiGet('/career/jds?limit=20').then(function(r){state.career.jds.status='success';state.career.jds.data=r.data.jds||[]}).catch(function(e){state.career.jds.status='error';state.career.jds.error=e.message}),
    apiGet('/career/evaluations?limit=20').then(function(r){state.career.evaluations.status='success';state.career.evaluations.data=r.data.evaluations||[]}).catch(function(e){state.career.evaluations.status='error';state.career.evaluations.error=e.message}),
    apiGet('/career/applications?limit=20').then(function(r){state.career.applications.status='success';state.career.applications.data=r.data.applications||[]}).catch(function(e){state.career.applications.status='error';state.career.applications.error=e.message}),
    apiGet('/career/handoffs?limit=20').then(function(r){state.career.handoffs.status='success';state.career.handoffs.data=r.data.handoffs||[]}).catch(function(e){state.career.handoffs.status='error';state.career.handoffs.error=e.message})
  ]).finally(function(){renderCareer()});
}

if(careerRefreshBtn){careerRefreshBtn.addEventListener('click',refreshCareer)}

// Readiness Center Panels
var automationRefreshBtn = document.getElementById('automation-refresh-btn');
var skillsRefreshBtn = document.getElementById('skills-refresh-btn');
var knowledgeRefreshBtn = document.getElementById('knowledge-refresh-btn');
var modelRefreshBtn = document.getElementById('model-refresh-btn');
var mcpRefreshBtn = document.getElementById('mcp-refresh-btn');

state.automation = { workflows: { status:'loading', data:[], error:null }, runs: { status:'loading', data:[], error:null } };
state.skills = { candidates: { status:'loading', data:[], error:null }, reviews: { status:'loading', data:[], error:null } };
state.knowledge = { nodes: { status:'loading', data:[], error:null }, edges: { status:'loading', data:[], error:null }, boundaries: { status:'loading', data:[], error:null }, state: { status:'loading', data:[], error:null } };
state.modelCost = { routes: { status:'loading', data:[], error:null }, costs: { status:'loading', data:[], error:null } };
state.mcpTools = { profiles: { status:'loading', data:[], error:null }, policies: { status:'loading', data:[], error:null } };

function renderAutomation(body) {
  var c = body || document.getElementById('automation-body');
  if (state.automation.workflows.status === 'loading') { showLoading(c); return; }
  if (state.automation.workflows.status === 'error') { showError(c, state.automation.workflows.error, refreshAutomation); return; }
  var workflows = state.automation.workflows.data || [], runs = state.automation.runs.data || [];
  c.innerHTML = '';
  var form = el('div', 'memory-form');
  form.appendChild(el('h3', '', 'Create Workflow'));
  var name = el('input'); name.type='text'; name.id='automation-name'; name.placeholder=zh('Workflow name'); form.appendChild(name);
  var create = el('button','btn btn-primary','Create');
  create.onclick=function(){var n=document.getElementById('automation-name').value.trim(); if(!n){return} apiPost('/automation/workflows',{name:n,action_refs:['read_file']}).then(function(){refreshAutomation()}).catch(handleActionError)};
  form.appendChild(create); c.appendChild(form);
  appendGrowthTable(c, 'Workflows', ['ID','Name','Enabled','Approval','Status'], workflows.slice(0,10).map(function(w){return [idCell(w.workflow_id), shortText(w.name,50), w.enabled?'yes':'no', w.approval_required?'required':'not required', badge(w.status||'?','status-'+(w.status||''))]}), 'No workflows');
  appendGrowthTable(c, 'Runs', ['ID','Workflow','Status','Outputs'], runs.slice(0,10).map(function(r){return [idCell(r.workflow_run_id), idCell(r.workflow_id), badge(r.status||'?','status-'+(r.status||'')), (r.output_refs||[]).join(', ')]}), 'No workflow runs');
}

function refreshAutomation() {
  state.automation.workflows.status='loading'; state.automation.runs.status='loading'; renderAutomation();
  Promise.all([
    apiGet('/automation/workflows?limit=20').then(function(r){state.automation.workflows.status='success';state.automation.workflows.data=r.data.workflows||[]}).catch(function(e){state.automation.workflows.status='error';state.automation.workflows.error=e.message}),
    apiGet('/automation/runs?limit=20').then(function(r){state.automation.runs.status='success';state.automation.runs.data=r.data.runs||[]}).catch(function(e){state.automation.runs.status='error';state.automation.runs.error=e.message})
  ]).finally(function(){renderAutomation()});
}

function renderSkills(body) {
  var c = body || document.getElementById('skills-body');
  if (state.skills.candidates.status === 'loading') { showLoading(c); return; }
  if (state.skills.candidates.status === 'error') { showError(c, state.skills.candidates.error, refreshSkills); return; }
  var skills = state.skills.candidates.data || [], reviews = state.skills.reviews.data || [];
  c.innerHTML = '';
  var form = el('div', 'memory-form');
  form.appendChild(el('h3', '', 'Create Skill Candidate'));
  var name = el('input'); name.type='text'; name.id='skill-name'; name.placeholder=zh('Skill name'); form.appendChild(name);
  var create = el('button','btn btn-primary','Create');
  create.onclick=function(){var n=document.getElementById('skill-name').value.trim(); if(!n){return} apiPost('/skills/candidates',{name:n}).then(function(){refreshSkills()}).catch(handleActionError)};
  form.appendChild(create); c.appendChild(form);
  appendGrowthTable(c, 'Candidates', ['ID','Name','Risk','Sandbox','Enabled'], skills.slice(0,10).map(function(s){return [idCell(s.skill_id), shortText(s.name,50), s.risk_level||'?', s.sandbox_status||'?', s.enabled?'yes':'no']}), 'No skill candidates');
  appendGrowthTable(c, 'Reviews', ['ID','Skill','Result','Enabled After'], reviews.slice(0,10).map(function(r){return [idCell(r.skill_review_id), idCell(r.skill_ref), r.result||'?', r.enabled_after_review?'yes':'no']}), 'No skill reviews');
}

function refreshSkills() {
  state.skills.candidates.status='loading'; state.skills.reviews.status='loading'; renderSkills();
  Promise.all([
    apiGet('/skills/candidates?limit=20').then(function(r){state.skills.candidates.status='success';state.skills.candidates.data=r.data.skills||[]}).catch(function(e){state.skills.candidates.status='error';state.skills.candidates.error=e.message}),
    apiGet('/skills/reviews?limit=20').then(function(r){state.skills.reviews.status='success';state.skills.reviews.data=r.data.skill_reviews||[]}).catch(function(e){state.skills.reviews.status='error';state.skills.reviews.error=e.message})
  ]).finally(function(){renderSkills()});
}

function renderKnowledge(body) {
  var c = body || document.getElementById('knowledge-body');
  if (state.knowledge.nodes.status === 'loading') { showLoading(c); return; }
  if (state.knowledge.nodes.status === 'error') { showError(c, state.knowledge.nodes.error, refreshKnowledge); return; }
  var nodes = state.knowledge.nodes.data || [], edges = state.knowledge.edges.data || [], boundaries = state.knowledge.boundaries.data || [], states = state.knowledge.state.data || [];
  c.innerHTML = '';
  var form = el('div', 'memory-form');
  form.appendChild(el('h3', '', 'Create Node'));
  var label = el('input'); label.type='text'; label.id='knowledge-label'; label.placeholder=zh('Node label'); form.appendChild(label);
  var create = el('button','btn btn-primary','Create');
  create.onclick=function(){var n=document.getElementById('knowledge-label').value.trim(); if(!n){return} apiPost('/knowledge/nodes',{label:n}).then(function(){refreshKnowledge()}).catch(handleActionError)};
  form.appendChild(create); c.appendChild(form);
  appendGrowthTable(c, 'Nodes', ['ID','Type','Label','Status'], nodes.slice(0,10).map(function(n){return [idCell(n.node_id), n.node_type||'?', shortText(n.label,56), badge(n.status||'?','status-'+(n.status||''))]}), 'No nodes');
  appendGrowthTable(c, 'Edges', ['ID','From','To','Relation'], edges.slice(0,10).map(function(e){return [idCell(e.edge_id), idCell(e.from_node_ref), idCell(e.to_node_ref), e.relation||'?']}), 'No edges');
  appendGrowthTable(c, 'Boundaries', ['ID','Type','Summary','Status'], boundaries.slice(0,10).map(function(b){return [idCell(b.boundary_id), b.boundary_type||'?', shortText(b.summary,64), badge(b.status||'?','status-'+(b.status||''))]}), 'No boundaries');
  appendGrowthTable(c, 'State', ['ID','Nodes','Edges','Boundaries','RAG'], states.slice(0,5).map(function(s){return [idCell(s.knowledge_state_id), s.node_count, s.edge_count, s.boundary_count, s.rag_enabled?'enabled':'disabled']}), 'No state snapshots');
}

function refreshKnowledge() {
  Object.keys(state.knowledge).forEach(function(k){state.knowledge[k].status='loading'}); renderKnowledge();
  Promise.all([
    apiGet('/knowledge/nodes?limit=20').then(function(r){state.knowledge.nodes.status='success';state.knowledge.nodes.data=r.data.nodes||[]}).catch(function(e){state.knowledge.nodes.status='error';state.knowledge.nodes.error=e.message}),
    apiGet('/knowledge/edges?limit=20').then(function(r){state.knowledge.edges.status='success';state.knowledge.edges.data=r.data.edges||[]}).catch(function(e){state.knowledge.edges.status='error';state.knowledge.edges.error=e.message}),
    apiGet('/knowledge/boundaries?limit=20').then(function(r){state.knowledge.boundaries.status='success';state.knowledge.boundaries.data=r.data.boundaries||[]}).catch(function(e){state.knowledge.boundaries.status='error';state.knowledge.boundaries.error=e.message}),
    apiGet('/knowledge/state?limit=20').then(function(r){state.knowledge.state.status='success';state.knowledge.state.data=r.data.knowledge_state||[]}).catch(function(e){state.knowledge.state.status='error';state.knowledge.state.error=e.message})
  ]).finally(function(){renderKnowledge()});
}

function renderModelCost(body) {
  var c = body || document.getElementById('model-body');
  if (state.modelCost.routes.status === 'loading') { showLoading(c); return; }
  if (state.modelCost.routes.status === 'error') { showError(c, state.modelCost.routes.error, refreshModelCost); return; }
  var routes = state.modelCost.routes.data || [], costs = state.modelCost.costs.data || [];
  c.innerHTML = '';
  var assistant = el('section', 'assistant-form');
  assistant.appendChild(el('h3', '', '提案助手'));
  assistant.appendChild(el('p', 'setup-copy', '仅生成可供审核的中文建议。模型无法执行命令、写入长期记忆、启用工具或提交外部操作。'));
  var prompt = el('textarea'); prompt.id = 'assistant-prompt'; prompt.maxLength = 4000; prompt.placeholder = '描述你需要分析或规划的事项，最多 4000 个字符。'; assistant.appendChild(prompt);
  var confirm = el('label', 'assistant-confirm');
  var check = el('input'); check.type = 'checkbox'; check.id = 'assistant-remote-confirm'; confirm.appendChild(check);
  confirm.appendChild(el('span', '', '我确认本次内容将发送到已配置的远程模型服务。'));
  assistant.appendChild(confirm);
  var submit = el('button', 'btn btn-primary', '生成提案'); submit.type = 'button';
  var result = el('div', 'assistant-result', '尚未生成提案。输出只在当前页面显示，需由你手动录入 OnePal 的受治理流程。'); result.id = 'assistant-result';
  submit.onclick = function() {
    var text = prompt.value.trim();
    if (!text) { result.textContent = '请输入需要生成建议的内容。'; return; }
    if (!check.checked) { result.textContent = '请先确认本次内容将发送到远程模型服务。'; return; }
    submit.disabled = true;
    result.textContent = '正在请求远程模型生成提案...';
    apiPost('/assistant/proposals', {prompt: text}).then(function(resp) {
      var data = resp.data || {};
      var priceNote = data.pricing_configured ? ('估算成本：$' + data.estimated_cost_usd) : '未配置价格，成本按 $0 记录。';
      result.textContent = (data.proposal_text || '远程模型未返回建议。') + '\n\n' + priceNote + '\n该输出未写入任务、记忆或外部系统。';
      refreshModelCost();
    }).catch(function(error) {
      result.textContent = '无法生成提案：' + error.message;
    }).finally(function() { submit.disabled = false; });
  };
  assistant.appendChild(submit); assistant.appendChild(result); c.appendChild(assistant);
  var form = el('div', 'memory-form');
  form.appendChild(el('h3', '', '创建路由'));
  var task = el('input'); task.type='text'; task.id='model-task-type'; task.placeholder='任务类型'; form.appendChild(task);
  var create = el('button','btn btn-primary','创建');
  create.onclick=function(){var t=document.getElementById('model-task-type').value.trim(); if(!t){return} apiPost('/model/routes',{task_type:t}).then(function(){refreshModelCost()}).catch(handleActionError)};
  form.appendChild(create); c.appendChild(form);
  appendGrowthTable(c, '模型路由', ['编号','任务','模型','LiteLLM','状态'], routes.slice(0,10).map(function(r){return [idCell(r.router_id), r.task_type||'?', r.default_model||'?', r.litellm_enabled?'已启用':'未启用', badge(r.status||'?','status-'+(r.status||''))]}), '暂无模型路由');
  appendGrowthTable(c, '成本事件', ['编号','任务','模型','USD'], costs.slice(0,10).map(function(e){return [idCell(e.cost_event_id), shortText(e.task_ref,24), e.model||'?', e.estimated_cost_usd]}), '暂无成本事件');
}

function refreshModelCost() {
  state.modelCost.routes.status='loading'; state.modelCost.costs.status='loading'; renderModelCost();
  Promise.all([
    apiGet('/model/routes?limit=20').then(function(r){state.modelCost.routes.status='success';state.modelCost.routes.data=r.data.model_routes||[]}).catch(function(e){state.modelCost.routes.status='error';state.modelCost.routes.error=e.message}),
    apiGet('/model/cost-events?limit=20').then(function(r){state.modelCost.costs.status='success';state.modelCost.costs.data=r.data.cost_events||[]}).catch(function(e){state.modelCost.costs.status='error';state.modelCost.costs.error=e.message})
  ]).finally(function(){renderModelCost()});
}

function renderMcpTools(body) {
  var c = body || document.getElementById('mcp-body');
  if (state.mcpTools.profiles.status === 'loading') { showLoading(c); return; }
  if (state.mcpTools.profiles.status === 'error') { showError(c, state.mcpTools.profiles.error, refreshMcpTools); return; }
  var profiles = state.mcpTools.profiles.data || [], policies = state.mcpTools.policies.data || [];
  c.innerHTML = '';
  var form = el('div', 'memory-form');
  form.appendChild(el('h3', '', 'Create MCP Profile'));
  var name = el('input'); name.type='text'; name.id='mcp-name'; name.placeholder=zh('MCP profile name'); form.appendChild(name);
  var create = el('button','btn btn-primary','Create');
  create.onclick=function(){var n=document.getElementById('mcp-name').value.trim(); if(!n){return} apiPost('/mcp/profiles',{name:n}).then(function(){refreshMcpTools()}).catch(handleActionError)};
  form.appendChild(create); c.appendChild(form);
  appendGrowthTable(c, 'MCP Profiles', ['ID','Name','Trust','Enabled','Write'], profiles.slice(0,10).map(function(p){return [idCell(p.mcp_profile_id), shortText(p.name,40), p.trust_level||'?', p.enabled?'yes':'no', p.write_actions_allowed?'yes':'no']}), 'No MCP profiles');
  appendGrowthTable(c, 'Tool Policies', ['ID','Tool','Trust','Write','Approval'], policies.slice(0,10).map(function(p){return [idCell(p.tool_trust_policy_id), shortText(p.tool_ref,30), p.trust_level||'?', p.write_allowed?'yes':'no', p.approval_required?'required':'not required']}), 'No tool policies');
}

function refreshMcpTools() {
  state.mcpTools.profiles.status='loading'; state.mcpTools.policies.status='loading'; renderMcpTools();
  Promise.all([
    apiGet('/mcp/profiles?limit=20').then(function(r){state.mcpTools.profiles.status='success';state.mcpTools.profiles.data=r.data.mcp_profiles||[]}).catch(function(e){state.mcpTools.profiles.status='error';state.mcpTools.profiles.error=e.message}),
    apiGet('/mcp/tool-policies?limit=20').then(function(r){state.mcpTools.policies.status='success';state.mcpTools.policies.data=r.data.tool_policies||[]}).catch(function(e){state.mcpTools.policies.status='error';state.mcpTools.policies.error=e.message})
  ]).finally(function(){renderMcpTools()});
}

if(automationRefreshBtn){automationRefreshBtn.addEventListener('click',refreshAutomation)}
if(skillsRefreshBtn){skillsRefreshBtn.addEventListener('click',refreshSkills)}
if(knowledgeRefreshBtn){knowledgeRefreshBtn.addEventListener('click',refreshKnowledge)}
if(modelRefreshBtn){modelRefreshBtn.addEventListener('click',refreshModelCost)}
if(mcpRefreshBtn){mcpRefreshBtn.addEventListener('click',refreshMcpTools)}

// ─── Init ───
refreshAll();
refreshMemory();
refreshResearch();
refreshCareer();
refreshAutomation();
refreshSkills();
refreshKnowledge();
refreshModelCost();
refreshMcpTools();
startAutoRefresh();
updateApiBadge();
initializePanelNavigation();
initializeMotionSystem();

// Periodically update API badge
setInterval(updateApiBadge, REFRESH_MS);

})();
