#!/usr/bin/env python3
"""OnePal Growth Review Manager - Task 12-B

Growth reviews, repeated blocker detection, adjustment proposals, memory handoff.

Usage:
    py scripts/growth_review.py review-create --goal-id goal_xxx --period-type weekly --self-rating 3
    py scripts/growth_review.py adjustment-create --goal-id goal_xxx --proposal-type reduce_scope --reason "..."
"""

import argparse, json, sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REVIEWS = ROOT / "growth" / "reviews" / "growth_reviews.jsonl"
DEFAULT_ADJUST = ROOT / "growth" / "adjustments" / "plan_adjustment_proposals.jsonl"
DEFAULT_AUDIT = ROOT / "logs" / "growth_audit.jsonl"

VALID_ADJUST = {"pause_goal","resume_goal","reduce_scope","increase_scope","change_deadline","change_priority","archive_goal","split_goal","merge_goal","adjust_capacity"}
def now(): return datetime.now(timezone.utc).isoformat()
def load(p): return [json.loads(l) for l in open(p,"r",encoding="utf-8") if l.strip()] if p.exists() else []
def app(p,r): p.parent.mkdir(parents=True,exist_ok=True); open(p,"a",encoding="utf-8").write(json.dumps(r,ensure_ascii=False)+"\n")
def wrt(p,rs): p.parent.mkdir(parents=True,exist_ok=True); open(p,"w",encoding="utf-8").write("".join(json.dumps(r,ensure_ascii=False)+"\n" for r in rs))
def adt(a,d,p,gid=None): app(p,{"audit_id":f"a_{uuid4().hex[:12]}","action":a,"goal_id":gid,"detail":d[:300],"timestamp":now()})

# review-create
def rc(args,rp,ap):
    r={"review_id":f"rev_{uuid4().hex[:12]}","goal_id":args.goal_id,"period_type":args.period_type,
       "self_rating":int(args.self_rating),"blockers":(args.blockers or "").split(";") if args.blockers else [],
       "lessons_learned":args.lessons or "","evidence_summary":args.evidence or "",
       "adjustment_needed":bool(args.adjustment_needed), "completed_tasks":0,"missed_tasks":0,
       "status":"completed","created_at":now()}
    app(rp,r); adt("review_created",f"goal={args.goal_id}",ap,gid=args.goal_id)

    # Detect repeated blocker
    prev=[pr for pr in load(rp) if pr.get("goal_id")==args.goal_id and pr.get("adjustment_needed")]
    if len(prev)>=2: adt("repeated_blocker",f"goal={args.goal_id} count={len(prev)+1}",ap,gid=args.goal_id)

    print(json.dumps({"status":"created","review":r,"repeated_blocker":len(prev)>=2},indent=2))

# adjustment-create
def ac(args,ap_path,ap):
    impact=args.impact or "medium"
    a={"proposal_id":f"adj_{uuid4().hex[:12]}","proposal_type":args.proposal_type,"goal_id":args.goal_id,
       "reason":args.reason,"proposed_change":args.proposed_change or args.proposal_type,
       "impact":impact,"risk_level":"R1" if impact=="low" else ("R3" if impact=="high" else "R2"),
       "approval_required":impact=="high","status":"draft","created_at":now()}
    app(ap_path,a); adt("adjustment_created",f"type={args.proposal_type} impact={impact}",ap,gid=args.goal_id)
    print(json.dumps({"status":"created","adjustment":a},indent=2))

# memory-handoff
def mh(args,ap):
    import subprocess
    scr = str(ROOT / "scripts" / "memory_candidate.py")
    res = subprocess.run(["py",scr,"create","--content",f"[Growth handoff] Goal: {args.goal_id} - {args.notes or 'Review feedback'}",
                          "--memory-type","project_decision","--sensitivity","internal","--source-type","manual","--source-agent","growth_center"],
                         capture_output=True,text=True,timeout=30,encoding="utf-8",errors="replace")
    adt("memory_handoff","delegated to memory_candidate.py",ap,gid=args.goal_id)
    print(json.dumps({"status":"delegated","delegated_to":"memory_candidate.py","note":"NOT written to memory store"},indent=2))

# list
def li(args,lp,label):
    items=load(lp); limit=min(args.limit or 20,100)
    print(json.dumps({label:items[-limit:],"total":len(items),"shown":min(len(items),limit)},indent=2))

def main():
    p=argparse.ArgumentParser(description="Growth Review Manager")
    s=p.add_subparsers(dest="cmd")
    sr=s.add_parser("review-create"); sr.add_argument("--goal-id",required=True); sr.add_argument("--period-type",default="weekly"); sr.add_argument("--self-rating",type=int,default=3); sr.add_argument("--blockers",default=""); sr.add_argument("--lessons",default=""); sr.add_argument("--evidence",default=""); sr.add_argument("--adjustment-needed",type=int,default=0); sr.add_argument("--reviews-log",default=None); sr.add_argument("--audit-log",default=None)
    sa=s.add_parser("adjustment-create"); sa.add_argument("--goal-id",required=True); sa.add_argument("--proposal-type",required=True,choices=list(VALID_ADJUST)); sa.add_argument("--reason",default=""); sa.add_argument("--proposed-change",default=""); sa.add_argument("--impact",default="medium",choices=["low","medium","high"]); sa.add_argument("--adjustments-log",default=None); sa.add_argument("--audit-log",default=None)
    sm=s.add_parser("memory-handoff"); sm.add_argument("--goal-id",required=True); sm.add_argument("--notes",default=""); sm.add_argument("--audit-log",default=None)
    sl=s.add_parser("list"); sl.add_argument("--limit",type=int,default=20); sl.add_argument("--reviews-log",default=None); sl.add_argument("--adjustments-log",default=None); sl.add_argument("--type",default="reviews")
    args=p.parse_args()
    if not args.cmd: p.print_help(); sys.exit(1)
    rp=Path(getattr(args,"reviews_log","")) or DEFAULT_REVIEWS
    ap=Path(getattr(args,"adjustments_log","")) or DEFAULT_ADJUST
    aud=Path(getattr(args,"audit_log","")) or DEFAULT_AUDIT
    if args.cmd=="review-create": rc(args,rp,aud)
    elif args.cmd=="adjustment-create": ac(args,ap,aud)
    elif args.cmd=="memory-handoff": mh(args,aud)
    elif args.cmd=="list": li(args,rp if args.type=="reviews" else ap,args.type)

if __name__=="__main__": main()
