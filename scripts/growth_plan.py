#!/usr/bin/env python3
"""OnePal Growth Plan Manager - Task 12-B

Capacity budgets, weekly plans, daily tasks, overload detection.

Usage:
    py scripts/growth_plan.py capacity-create --period-type weekly --available-hours 8
    py scripts/growth_plan.py weekly-create --week-start 2026-06-01 --goal-ids goal_1
    py scripts/growth_plan.py task-create --date 2026-06-01 --goal-id goal_1 --title "..."
    py scripts/growth_plan.py task-status --task-id task_xxx --status done
"""

import argparse, json, sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CAP = ROOT / "growth" / "capacity" / "capacity_budgets.jsonl"
DEFAULT_WKLY = ROOT / "growth" / "plans" / "weekly_plans.jsonl"
DEFAULT_TASKS = ROOT / "growth" / "plans" / "daily_tasks.jsonl"
DEFAULT_AUDIT = ROOT / "logs" / "growth_audit.jsonl"

VALID_TYPES = {"study","build","review","write","practice","research","job_search","maintenance","other"}
VALID_STATUS = {"planned","doing","done","skipped","blocked","cancelled"}
def now(): return datetime.now(timezone.utc).isoformat()
def load(p): return [json.loads(l) for l in open(p,"r",encoding="utf-8") if l.strip()] if p.exists() else []
def app(p,r): p.parent.mkdir(parents=True,exist_ok=True); open(p,"a",encoding="utf-8").write(json.dumps(r,ensure_ascii=False)+"\n")
def wrt(p,rs): p.parent.mkdir(parents=True,exist_ok=True); open(p,"w",encoding="utf-8").write("".join(json.dumps(r,ensure_ascii=False)+"\n" for r in rs))
def adt(a,d,p): app(p,{"audit_id":f"a_{uuid4().hex[:12]}","action":a,"detail":d[:300],"timestamp":now()})

# capacity-create
def cap(args,cp,ap):
    hrs=float(args.available_hours); goals=[g.strip() for g in (args.active_goal_ids or "").split(",") if g.strip()]
    n=len(goals); overload=hrs/n<2 if n else False
    c={"budget_id":f"cap_{uuid4().hex[:12]}","period_type":args.period_type,"available_hours":hrs,
       "focus_slots":int(args.focus_slots or 2),"energy_level":args.energy_level or "medium",
       "active_goal_ids":goals,"overload_warning":overload,"created_at":now()}
    app(cp,c); adt("capacity_created",f"budget={c['budget_id']} overload={overload}",ap)
    print(json.dumps({"status":"created","budget":c,"overload_warning":overload},indent=2))

# weekly-create
def wkly(args,wp,ap):
    w={"weekly_plan_id":f"wp_{uuid4().hex[:12]}","week_start":args.week_start,
       "goal_ids":[g.strip() for g in (args.goal_ids or "").split(",") if g.strip()],
       "focus_theme":args.focus_theme or "","status":"planned","created_at":now()}
    app(wp,w); adt("weekly_created",f"week={args.week_start}",ap)
    print(json.dumps({"status":"created","weekly_plan":w},indent=2))

# task-create
def tc(args,tp,ap):
    t={"task_id":f"task_{uuid4().hex[:12]}","date":args.date,"goal_id":args.goal_id,
       "title":args.title,"estimated_minutes":int(args.estimated_minutes or 30),
       "task_type":args.task_type,"status":"planned","created_at":now(),"completed_at":None}
    app(tp,t); adt("task_created",f"task={t['task_id']} goal={args.goal_id}",ap)
    print(json.dumps({"status":"created","task":t},indent=2))

# task-status
def ts(args,tp,ap):
    rs=load(tp); found=False
    for i,r in enumerate(rs):
        if r.get("task_id")==args.task_id:
            rs[i]["status"]=args.status; found=True
            if args.status=="done": rs[i]["completed_at"]=now()
            rs[i]["updated_at"]=now()
            break
    if not found: print(json.dumps({"error":"not found"})); sys.exit(1)
    wrt(tp,rs); adt("task_status",f"task={args.task_id} status={args.status}",ap)
    print(json.dumps({"status":"updated","task_id":args.task_id,"new_status":args.status}))

# list
def li(args,lp,label):
    items=load(lp); limit=min(args.limit or 20,100)
    print(json.dumps({label:items[-limit:],"total":len(items),"shown":min(len(items),limit)},indent=2))

def main():
    p=argparse.ArgumentParser(description="Growth Plan Manager")
    s=p.add_subparsers(dest="cmd")
    sc=s.add_parser("capacity-create"); sc.add_argument("--period-type",default="weekly"); sc.add_argument("--available-hours",default=8); sc.add_argument("--focus-slots",default=2); sc.add_argument("--energy-level",default="medium"); sc.add_argument("--active-goal-ids",default=""); sc.add_argument("--capacity-log",default=None); sc.add_argument("--audit-log",default=None)
    sw=s.add_parser("weekly-create"); sw.add_argument("--week-start",required=True); sw.add_argument("--goal-ids",default=""); sw.add_argument("--focus-theme",default=""); sw.add_argument("--weekly-log",default=None); sw.add_argument("--audit-log",default=None)
    st=s.add_parser("task-create"); st.add_argument("--date",required=True); st.add_argument("--goal-id",required=True); st.add_argument("--title",required=True); st.add_argument("--task-type",default="study"); st.add_argument("--estimated-minutes",default=30); st.add_argument("--tasks-log",default=None); st.add_argument("--audit-log",default=None)
    ss=s.add_parser("task-status"); ss.add_argument("--task-id",required=True); ss.add_argument("--status",required=True,choices=list(VALID_STATUS)); ss.add_argument("--tasks-log",default=None); ss.add_argument("--audit-log",default=None)
    sl=s.add_parser("list"); sl.add_argument("--limit",type=int,default=20); sl.add_argument("--capacity-log",default=None); sl.add_argument("--weekly-log",default=None); sl.add_argument("--tasks-log",default=None); sl.add_argument("--type",default="tasks")
    args=p.parse_args()
    if not args.cmd: p.print_help(); sys.exit(1)
    cp=Path(getattr(args,"capacity_log","")) or DEFAULT_CAP
    wp=Path(getattr(args,"weekly_log","")) or DEFAULT_WKLY
    tp=Path(getattr(args,"tasks_log","")) or DEFAULT_TASKS
    ap=Path(getattr(args,"audit_log","")) or DEFAULT_AUDIT
    if args.cmd=="capacity-create": cap(args,cp,ap)
    elif args.cmd=="weekly-create": wkly(args,wp,ap)
    elif args.cmd=="task-create": tc(args,tp,ap)
    elif args.cmd=="task-status": ts(args,tp,ap)
    elif args.cmd=="list": li(args,tp if args.type=="tasks" else (wp if args.type=="weekly" else cp), args.type)

if __name__=="__main__": main()
