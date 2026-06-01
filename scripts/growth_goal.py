#!/usr/bin/env python3
"""OnePal Growth Goal Manager - Task 12-B

Goal candidate intake, accept/reject, goal contract creation.
No schema modifications needed — uses dict-based structures.

Usage:
    py scripts/growth_goal.py candidate-create --source-type manual --title "..." --goal-area ai_engineering --reason "..."
    py scripts/growth_goal.py candidate-accept --candidate-id gc_xxx
    py scripts/growth_goal.py goal-create --candidate-id gc_xxx
"""

import argparse, json, re, sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CANDS = ROOT / "growth" / "candidates" / "goal_candidates.jsonl"
DEFAULT_GOALS = ROOT / "growth" / "goals" / "goal_contracts.jsonl"
DEFAULT_AUDIT = ROOT / "logs" / "growth_audit.jsonl"

VALID_AREAS = {"ai_engineering","data_analysis","career","research","communication","health","finance","productivity","personal_project","other"}
SECRETS = [r'sk-[a-zA-Z0-9]{10,}',r'-----BEGIN',r'ghp_']
def now(): return datetime.now(timezone.utc).isoformat()
def load(p): return [json.loads(l) for l in open(p,"r",encoding="utf-8") if l.strip()] if p.exists() else []
def app(p,r): p.parent.mkdir(parents=True,exist_ok=True); open(p,"a",encoding="utf-8").write(json.dumps(r,ensure_ascii=False)+"\n")
def wrt(p,rs): p.parent.mkdir(parents=True,exist_ok=True); open(p,"w",encoding="utf-8").write("".join(json.dumps(r,ensure_ascii=False)+"\n" for r in rs))
def adt(a,d,p,cid=None,gid=None): app(p,{"audit_id":f"a_{uuid4().hex[:12]}","action":a,"candidate_id":cid,"goal_id":gid,"detail":d[:300],"timestamp":now()})
def sec(c): return any(re.search(pat,c or "",re.IGNORECASE) for pat in SECRETS)
def fnd(rs,rid,f):
    for i,r in enumerate(rs):
        if r.get(f)==rid: return i,r
    return None,None

# candidate-create
def cc(args,cp,ap):
    t=args.title.strip(); r=args.reason.strip()
    if not t: print(json.dumps({"error":"title required"})); sys.exit(1)
    if sec(t) or sec(r): adt("candidate_rejected_secret","secret",ap); print(json.dumps({"status":"rejected","reason":"secret"})); sys.exit(1)
    c={"candidate_id":f"gc_{uuid4().hex[:12]}","source_type":args.source_type,"title":t,"goal_area":args.goal_area,
       "reason":r,"confidence":max(0,min(1,float(args.confidence or 0.5))),"priority_hint":args.priority,
       "status":"captured","created_at":now()}
    app(cp,c); adt("candidate_created",f"id={c['candidate_id']}",ap,cid=c["candidate_id"])
    print(json.dumps({"status":"created","candidate":c},indent=2))

# candidate-accept / reject
def ca(args,cp,ap):
    _,c=fnd(load(cp),args.candidate_id,"candidate_id")
    if c is None: print(json.dumps({"error":"not found"})); sys.exit(1)
    rs=load(cp); idx,_=fnd(rs,args.candidate_id,"candidate_id"); rs[idx]["status"]="accepted"; rs[idx]["updated_at"]=now(); wrt(cp,rs)
    adt("candidate_accepted",f"id={args.candidate_id}",ap,cid=args.candidate_id)
    print(json.dumps({"status":"accepted","candidate_id":args.candidate_id}))

def cr(args,cp,ap):
    _,c=fnd(load(cp),args.candidate_id,"candidate_id")
    if c is None: print(json.dumps({"error":"not found"})); sys.exit(1)
    rs=load(cp); idx,_=fnd(rs,args.candidate_id,"candidate_id"); rs[idx]["status"]="rejected"; rs[idx]["reject_reason"]=args.reason; rs[idx]["updated_at"]=now(); wrt(cp,rs)
    adt("candidate_rejected",f"id={args.candidate_id} reason={args.reason}",ap,cid=args.candidate_id)
    print(json.dumps({"status":"rejected","candidate_id":args.candidate_id}))

# goal-create
def gc(args,cp,gp,ap):
    _,c=fnd(load(cp),args.candidate_id,"candidate_id")
    if c is None: print(json.dumps({"error":"candidate not found"})); sys.exit(1)
    if c.get("status")!="accepted": print(json.dumps({"error":"candidate not accepted"})); sys.exit(1)
    g={"goal_id":f"goal_{uuid4().hex[:12]}","title":c["title"],"goal_area":c["goal_area"],"why_it_matters":c.get("reason",""),
       "success_criteria":[args.success_criteria or "Complete goal objectives"],"minimum_viable_result":args.minimum_result or "Baseline completed",
       "priority":args.priority,"status":"active","source_candidate_id":args.candidate_id,"created_at":now(),"updated_at":None}
    app(gp,g); adt("goal_created",f"id={g['goal_id']}",ap,gid=g["goal_id"])
    # Update candidate status
    rs=load(cp); idx,_=fnd(rs,args.candidate_id,"candidate_id"); rs[idx]["status"]="converted_to_goal"; wrt(cp,rs)
    print(json.dumps({"status":"created","goal":g},indent=2))

# archive
def ga(args,gp,ap):
    rs=load(gp); idx,g=fnd(rs,args.goal_id,"goal_id")
    if g is None: print(json.dumps({"error":"not found"})); sys.exit(1)
    rs[idx]["status"]="archived"; rs[idx]["updated_at"]=now(); wrt(gp,rs)
    adt("goal_archived",f"id={args.goal_id}",ap,gid=args.goal_id)
    print(json.dumps({"status":"archived","goal_id":args.goal_id}))

# list
def li(args,lp,label):
    items=load(lp); limit=min(args.limit or 20,100)
    if args.status: items=[i for i in items if i.get("status")==args.status]
    print(json.dumps({label:items[-limit:],"total":len(items),"shown":min(len(items),limit)},indent=2))

def main():
    p=argparse.ArgumentParser(description="Growth Goal Manager")
    s=p.add_subparsers(dest="cmd")
    sc=s.add_parser("candidate-create"); sc.add_argument("--source-type",default="manual"); sc.add_argument("--title",required=True); sc.add_argument("--goal-area",default="other"); sc.add_argument("--reason",default=""); sc.add_argument("--confidence",type=float,default=0.5); sc.add_argument("--priority",default="P2"); sc.add_argument("--candidates-log",default=None); sc.add_argument("--audit-log",default=None)
    sa=s.add_parser("candidate-accept"); sa.add_argument("--candidate-id",required=True); sa.add_argument("--candidates-log",default=None); sa.add_argument("--audit-log",default=None)
    sr=s.add_parser("candidate-reject"); sr.add_argument("--candidate-id",required=True); sr.add_argument("--reason",default="rejected"); sr.add_argument("--candidates-log",default=None); sr.add_argument("--audit-log",default=None)
    sg=s.add_parser("goal-create"); sg.add_argument("--candidate-id",required=True); sg.add_argument("--success-criteria",default=""); sg.add_argument("--minimum-result",default=""); sg.add_argument("--priority",default="P2"); sg.add_argument("--candidates-log",default=None); sg.add_argument("--goals-log",default=None); sg.add_argument("--audit-log",default=None)
    sga=s.add_parser("goal-archive"); sga.add_argument("--goal-id",required=True); sga.add_argument("--goals-log",default=None); sga.add_argument("--audit-log",default=None)
    sl=s.add_parser("list"); sl.add_argument("--limit",type=int,default=20); sl.add_argument("--status",default=None); sl.add_argument("--candidates-log",default=None); sl.add_argument("--goals-log",default=None); sl.add_argument("--type",default="candidates")
    args=p.parse_args()
    if not args.cmd: p.print_help(); sys.exit(1)
    cp=Path(getattr(args,"candidates_log","")) or DEFAULT_CANDS
    gp=Path(getattr(args,"goals_log","")) or DEFAULT_GOALS
    ap=Path(getattr(args,"audit_log","")) or DEFAULT_AUDIT
    if args.cmd=="candidate-create": cc(args,cp,ap)
    elif args.cmd=="candidate-accept": ca(args,cp,ap)
    elif args.cmd=="candidate-reject": cr(args,cp,ap)
    elif args.cmd=="goal-create": gc(args,cp,gp,ap)
    elif args.cmd=="goal-archive": ga(args,gp,ap)
    elif args.cmd=="list": li(args,cp if args.type=="candidates" else gp,args.type)

if __name__=="__main__": main()
