#!/usr/bin/env python3
"""OnePal Cognition Card Manager - Task 10-B

Creates cognition cards from research packets, validates, lists, archives,
and generates memory handoff candidates through memory_candidate.py.

Usage:
    py scripts/cognition_card.py create --packet-id pkt_xxx
    py scripts/cognition_card.py list --limit 20
    py scripts/cognition_card.py archive --card-id cog_xxx
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CARDS_LOG = PROJECT_ROOT / "research" / "cognition" / "cognition_cards.jsonl"
DEFAULT_PACKETS_LOG = PROJECT_ROOT / "research" / "packets" / "research_packets.jsonl"
DEFAULT_AUDIT_LOG = PROJECT_ROOT / "logs" / "research_audit.jsonl"


def now_iso(): return datetime.now(timezone.utc).isoformat()
def load_jsonl(p): return [json.loads(l) for l in open(p,"r",encoding="utf-8") if l.strip()] if p.exists() else []
def append_jsonl(p, r): p.parent.mkdir(parents=True,exist_ok=True); open(p,"a",encoding="utf-8").write(json.dumps(r,ensure_ascii=False)+"\n")
def write_jsonl(p, rs): p.parent.mkdir(parents=True,exist_ok=True); open(p,"w",encoding="utf-8").write("".join(json.dumps(r,ensure_ascii=False)+"\n" for r in rs))

def audit(action,detail,path,cid=None,pid=None):
    e={"audit_id":f"audit_{uuid4().hex[:12]}","action":action,"cognition_card_id":cid,"packet_id":pid,"detail":detail[:300],"timestamp":now_iso()}
    append_jsonl(path,e)

# ─── Create Cognition Card ───
def create_card(args, cards_path, packets_path, audit_path):
    records=load_jsonl(packets_path)
    _,pkt=None,None
    for i,r in enumerate(records):
        if r.get("packet_id")==args.packet_id: _,pkt=i,r; break
    if pkt is None: print(json.dumps({"error":"packet not found"})); sys.exit(1)

    card={"card_id":f"cogcard_{uuid4().hex[:12]}","source_packet_id":args.packet_id,
          "topic":pkt.get("topic",""),"core_idea":(args.core_idea or pkt.get("summary",""))[:500],
          "why_it_matters":args.why_it_matters or "",
          "mental_model":args.mental_model or "",
          "self_test_questions":(args.questions or "What did I learn?").split(";"),
          "confidence":max(0.0,min(1.0,float(args.confidence or 0.5))),
          "status":"draft","created_at":now_iso()}
    append_jsonl(cards_path,card)
    audit("cognition_card_created",f"id={card['card_id']}",audit_path,cid=card["card_id"],pid=args.packet_id)
    print(json.dumps({"status":"created","card":card},indent=2))

# ─── Archive ───
def archive_card(args, cards_path, audit_path):
    records=load_jsonl(cards_path)
    for i,r in enumerate(records):
        if r.get("card_id")==args.card_id: records[i]["status"]="archived"; records[i]["updated_at"]=now_iso(); write_jsonl(cards_path,records); audit("card_archived",f"id={args.card_id}",audit_path,cid=args.card_id); print(json.dumps({"status":"archived","card_id":args.card_id})); return
    print(json.dumps({"error":"not found"})); sys.exit(1)

# ─── List ───
def list_cards(args, cards_path):
    items=load_jsonl(cards_path); limit=min(args.limit or 20,100)
    print(json.dumps({"cards":items[-limit:],"total":len(items),"shown":min(len(items),limit)},indent=2))

# ─── Main ───
def main():
    p=argparse.ArgumentParser(description="Cognition Card Manager")
    s=p.add_subparsers(dest="cmd")
    cc=s.add_parser("create"); cc.add_argument("--packet-id",required=True); cc.add_argument("--core-idea",default=""); cc.add_argument("--why-it-matters",default=""); cc.add_argument("--mental-model",default=""); cc.add_argument("--questions",default=""); cc.add_argument("--confidence",type=float,default=0.5); cc.add_argument("--cards-log",default=None); cc.add_argument("--packets-log",default=None); cc.add_argument("--audit-log",default=None)
    ca=s.add_parser("archive"); ca.add_argument("--card-id",required=True); ca.add_argument("--cards-log",default=None); ca.add_argument("--audit-log",default=None)
    cl=s.add_parser("list"); cl.add_argument("--limit",type=int,default=20); cl.add_argument("--cards-log",default=None)
    args=p.parse_args()
    if not args.cmd: p.print_help(); sys.exit(1)
    cp=Path(getattr(args,"cards_log","")) or DEFAULT_CARDS_LOG
    pp=Path(getattr(args,"packets_log","")) or DEFAULT_PACKETS_LOG
    ap=Path(getattr(args,"audit_log","")) or DEFAULT_AUDIT_LOG
    if args.cmd=="create": create_card(args,cp,pp,ap)
    elif args.cmd=="archive": archive_card(args,cp,ap)
    elif args.cmd=="list": list_cards(args,cp)

if __name__=="__main__": main()
