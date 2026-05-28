/* OnePal Dashboard App - Task 07-B
 * API client, state management, and DOM rendering for 5 panels.
 * Uses fetch() exclusively. Zero external dependencies. Zero CDN.
 * Avoids eval / new Function / direct file access.
 */
(function() {
'use strict';

var API_BASE = 'http://127.0.0.1:18790';
var REFRESH_MS = 5000;
var refreshTimer = null;

// ─── DOM refs ───
var apiBadge = document.getElementById('api-badge');
var apiUrlEl = document.getElementById('api-url');
var refreshAllBtn = document.getElementById('refresh-all-btn');

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
  if (text !== undefined) e.textContent = text;
  return e;
}

function badge(text, cls) {
  var b = el('span', 'status-badge ' + (cls || ''));
  b.textContent = text;
  return b;
}

function showLoading(container) {
  container.innerHTML = '';
  container.appendChild(el('div', 'loading', 'Loading...'));
}

function showEmpty(container, msg) {
  container.innerHTML = '';
  container.appendChild(el('div', 'empty', msg || 'No data'));
}

function showError(container, msg, retryFn) {
  container.innerHTML = '';
  var div = el('div', 'error-state', msg || 'Error loading data');
  if (retryFn) {
    var btn = el('button', 'btn btn-sm retry-btn', 'Retry');
    btn.onclick = retryFn;
    div.appendChild(btn);
  }
  container.appendChild(div);
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

// ─── API Status Check ───
function updateApiBadge() {
  if (state.health.status === 'error') {
    apiBadge.textContent = 'OFF';
    apiBadge.style.background = 'var(--red)';
  } else if (state.health.status === 'loading') {
    apiBadge.textContent = '...';
    apiBadge.style.background = 'var(--yellow)';
  } else {
    apiBadge.textContent = 'API';
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
  setTimeout(updateApiBadge, 1000);
}

refreshAllBtn.addEventListener('click', refreshAll);

// ─── Auto-refresh ───
function startAutoRefresh() {
  if (refreshTimer) clearInterval(refreshTimer);
  refreshTimer = setInterval(function() {
    refreshHealth();
    refreshTasks();
    refreshTaskRuns();
    refreshTrace();
    updateApiBadge();
  }, REFRESH_MS);
}

// ─── Memory Center Panel ───
var memoryRefreshBtn = document.getElementById('memory-refresh-btn');

state.memories = { status: 'loading', data: [], error: null };
state.memCandidates = { status: 'loading', data: [], error: null };
state.memProposals = { status: 'loading', data: [], error: null };

function renderMemory(body) {
  var container = body || document.getElementById('memory-body');
  if (state.memories.status === 'loading') { showLoading(container); return; }
  if (state.memories.status === 'error') { showError(container, state.memories.error, refreshMemory); return; }

  var memories = state.memories.data || [];
  var candidates = state.memCandidates.data || [];
  var proposals = state.memProposals.data || [];

  container.innerHTML = '';

  // Create Candidate form
  var formDiv = el('div', 'memory-form');
  formDiv.appendChild(el('h3', '', 'Create Candidate'));
  var input = el('input');
  input.type = 'text'; input.id = 'mem-content'; input.placeholder = 'Memory content...'; input.maxLength = 4000;
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
        (function() { var a = el('button', 'btn btn-sm', 'Archive'); a.onclick = function() { apiPost('/memory/archive', {memory_id: m.memory_id, reason: 'manual'}).then(function() { refreshMemory(); }).catch(function(e) { alert(e.message); }); }; return a; })()
      ];
    });
    container.appendChild(buildTable(memCols, memRows));
  }

  // Candidates
  container.appendChild(el('h3', '', 'Candidates (' + candidates.length + ')'));
  var candCols = ['Candidate ID', 'Type', 'Summary', 'Status', 'Actions'];
  var candRows = candidates.slice(0, 10).map(function(c) {
    return [
      el('span', 'mono', (c.candidate_id || '').substring(0, 14)),
      c.memory_type || '?',
      (c.content_summary || '').substring(0, 60),
      badge(c.status || '?', 'status-' + (c.status || '')),
      (c.status === 'captured' || c.status === 'draft' ? (function() { var a = el('button', 'btn btn-sm', 'Propose'); a.onclick = function() { apiPost('/memory/proposals', {candidate_id: c.candidate_id}).then(function() { refreshMemory(); }).catch(function(e) { alert(e.message); }); }; return a; })() : el('span', '', ''))
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
      (p.status === 'approved' ? (function() { var a = el('button', 'btn btn-sm', 'Store'); a.onclick = function() { apiPost('/memory/store', {proposal_id: p.proposal_id}).then(function() { refreshMemory(); }).catch(function(e) { alert(e.message); }); }; return a; })() : el('span', '', ''))
    ];
  });
  container.appendChild(buildTable(propCols, propRows));
}

function refreshMemory() {
  state.memories.status = 'loading'; state.memCandidates.status = 'loading'; state.memProposals.status = 'loading';
  renderMemory();
  Promise.all([
    apiGet('/memory?limit=20').then(function(r) { state.memories.status = 'success'; state.memories.data = r.data.memories || []; })
      .catch(function(e) { state.memories.status = 'error'; state.memories.error = e.message; }),
    apiGet('/memory/candidates?limit=20').then(function(r) { state.memCandidates.status = 'success'; state.memCandidates.data = r.data.candidates || []; })
      .catch(function(e) { state.memCandidates.status = 'error'; state.memCandidates.error = e.message; }),
    apiGet('/memory/proposals?limit=20').then(function(r) { state.memProposals.status = 'success'; state.memProposals.data = r.data.proposals || []; })
      .catch(function(e) { state.memProposals.status = 'error'; state.memProposals.error = e.message; }),
  ]).finally(function() { renderMemory(); });
}

if (memoryRefreshBtn) { memoryRefreshBtn.addEventListener('click', refreshMemory); }

// ─── Init ───
refreshAll();
refreshMemory();
startAutoRefresh();
updateApiBadge();

// Periodically update API badge
setInterval(updateApiBadge, REFRESH_MS);

})();
