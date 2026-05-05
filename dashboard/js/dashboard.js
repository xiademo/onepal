(function(){
'use strict';
const agents = [
  {icon:'🔄',name:'Coordinator',role:'总调度'},
  {icon:'🧠',name:'Memory Curator',role:'记忆管理'},
  {icon:'🔧',name:'OpenCode Builder',role:'工程执行'},
  {icon:'👤',name:'Capability HR',role:'技能招聘'},
  {icon:'📥',name:'Input Manager',role:'输入处理'},
  {icon:'🔍',name:'Research Scout',role:'情报搜索'},
  {icon:'📚',name:'Deep Research',role:'深度研究'},
  {icon:'🌱',name:'Growth Planner',role:'成长规划'},
  {icon:'💼',name:'Career Agent',role:'职业资产'}
];
function renderAgents(){
  const grid = document.getElementById('agent-grid');
  if(!grid)return;
  grid.innerHTML = agents.map(a => `
    <div class="agent-card">
      <div class="agent-card-icon">${a.icon}</div>
      <div class="agent-card-name">${a.name}</div>
      <div class="agent-card-role">${a.role}</div>
      <div class="agent-card-status">● active</div>
    </div>
  `).join('');
}
function updateClock(){
  const el = document.getElementById('clock');
  if(el) el.textContent = new Date().toLocaleString('zh-CN',{hour12:false});
}
renderAgents();
updateClock();
setInterval(updateClock,1000);
console.log('OnePal Dashboard P0 initialized.');
})();
