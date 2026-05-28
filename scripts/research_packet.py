#!/usr/bin/env python3
"""OnePal Research Packet Manager - Task 10-B

Source records, source evaluation, research packet assembly,
evidence pack creation, and handoff candidate generation.

Usage:
    py scripts/research_packet.py source-create --source-type manual_text --title "..." --content "..."
    py scripts/research_packet.py source-evaluate --source-id src_xxx --trust-level B
    py scripts/research_packet.py packet-create --topic "..." --source-ids src_1,src_2
    py scripts/research_packet.py evidence-create --packet-id pkt_xxx
    py scripts/research_packet.py handoff-create --packet-id pkt_xxx --handoff-type memory
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_SOURCES_LOG = PROJECT_ROOT / "research" / "sources" / "research_sources.jsonl"
DEFAULT_PACKETS_LOG = PROJECT_ROOT / "research" / "packets" / "research_packets.jsonl"
DEFAULT_EVIDENCE_LOG = PROJECT_ROOT / "research" / "evidence" / "evidence_packs.jsonl"
DEFAULT_HANDOFFS_LOG = PROJECT_ROOT / "research" / "handoffs"
DEFAULT_AUDIT_LOG = PROJECT_ROOT / "logs" / "research_audit.jsonl"

VALID_SOURCE_TYPES = {"manual_text","article_summary","paper_summary","report_summary",
    "github_readme","book_note","course_note","news_summary","dataset_note","other"}
VALID_TRUST_LEVELS = {"A","B","C","D","unknown"}
VALID_PACKET_STATUSES = {"draft","reviewed","synthesized","converted_to_cognition_card","archived"}
VALID_SOURCE_STATUSES = {"captured","evaluated","rejected","used_in_packet","archived"}
VALID_HANDOFF_TYPES = {"memory","growth","career","capability"}
MAX_CONTENT_LENGTH = 2000

SECRET_PATTERNS = [r'sk-[a-zA-Z0-9]{10,}', r'-----BEGIN', r'ghp_[a-zA-Z0-9]{20,}',
    r'eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}',
    r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
    r'(?:api[_-]?key)\s*[:=]\s*\S{10,}', r'(?:password)\s*[:=]\s*\S{8,}',
    r'(?:token)\s*[:=]\s*\S{10,}', r'(?:secret)\s*[:=]\s*\S{8,}']


def now_iso(): return datetime.now(timezone.utc).isoformat()
def load_jsonl(p):
    if not p.exists(): return []
    recs=[]
    with open(p,"r",encoding="utf-8") as f:
        for l in f:
            if l.strip():
                try: recs.append(json.loads(l))
                except json.JSONDecodeError: pass
    return recs
def append_jsonl(p, r): p.parent.mkdir(parents=True,exist_ok=True); open(p,"a",encoding="utf-8").write(json.dumps(r,ensure_ascii=False)+"\n")
def write_jsonl(p, rs): p.parent.mkdir(parents=True,exist_ok=True); open(p,"w",encoding="utf-8").write("".join(json.dumps(r,ensure_ascii=False)+"\n" for r in rs))
def detect_secrets(c): return [p[:40] for p in SECRET_PATTERNS if re.search(p,c or "",re.IGNORECASE)]

def audit(action,detail,path,cid=None,pid=None,sid=None):
    e={"audit_id":f"audit_{uuid4().hex[:12]}","action":action,"candidate_id":cid,"packet_id":pid,"source_id":sid,"detail":detail[:300],"timestamp":now_iso()}
    append_jsonl(path,e)

def find_by_id(records,rid,field):
    for i,r in enumerate(records):
        if r.get(field)==rid: return i,r
    return None,None

# ─── Source Create ───
def source_create(args, log_path, audit_path):
    content = (args.content_summary or "").strip()
    if not content: print(json.dumps({"error":"content required"})); sys.exit(1)
    if len(content) > MAX_CONTENT_LENGTH: print(json.dumps({"error":f"max {MAX_CONTENT_LENGTH} chars"})); sys.exit(1)
    secrets = detect_secrets(content)
    if secrets: audit("source_rejected_secret","secrets detected",audit_path); print(json.dumps({"status":"rejected","reason":"secret_content"})); sys.exit(1)
    src={"source_id":f"src_{uuid4().hex[:12]}","source_type":args.source_type,"title":args.title,
         "content_summary":content,"source_level":args.source_level,"trust_level":"unknown",
         "freshness":"unknown","bias_notes":args.bias_notes or "","status":"captured","created_at":now_iso()}
    append_jsonl(log_path,src); audit("source_created",f"id={src['source_id']}",audit_path,sid=src["source_id"])
    print(json.dumps({"status":"created","source":src},indent=2))

# ─── Source Evaluate ───
def source_evaluate(args, log_path, audit_path):
    records=load_jsonl(log_path); idx,src=find_by_id(records,args.source_id,"source_id")
    if src is None: print(json.dumps({"error":"not found"})); sys.exit(1)
    records[idx]["trust_level"]=args.trust_level; records[idx]["credibility_score"]=args.credibility_score
    records[idx]["freshness"]=args.freshness; records[idx]["bias_notes"]=args.bias_notes or records[idx].get("bias_notes","")
    records[idx]["status"]="evaluated"; records[idx]["updated_at"]=now_iso()
    write_jsonl(log_path,records); audit("source_evaluated",f"trust={args.trust_level}",audit_path,sid=args.source_id)
    print(json.dumps({"status":"evaluated","source":records[idx]},indent=2))

# ─── Packet Create ───
def packet_create(args, src_path, pkt_path, audit_path):
    topic=args.topic.strip(); src_ids=[s.strip() for s in (args.source_ids or "").split(",") if s.strip()]
    if not topic or not src_ids: print(json.dumps({"error":"topic and source_ids required"})); sys.exit(1)
    sources=load_jsonl(src_path)
    valid=[s for s in sources if s["source_id"] in src_ids]
    if len(valid)!=len(src_ids): print(json.dumps({"error":"some source_ids not found"})); sys.exit(1)
    for s in valid:
        if s.get("status") in ("rejected","archived"):
            print(json.dumps({"error":f"source {s['source_id']} is {s['status']}"})); sys.exit(1)
    pkt={"packet_id":f"pkt_{uuid4().hex[:12]}","topic":topic,"question":args.question or topic,
         "source_ids":src_ids,"status":"draft","created_at":now_iso()}
    append_jsonl(pkt_path,pkt); audit("packet_created",f"id={pkt['packet_id']}",audit_path,pid=pkt["packet_id"])
    for s in valid:
        idx,_=find_by_id(load_jsonl(src_path),s["source_id"],"source_id")
        if idx is not None:
            recs=load_jsonl(src_path); recs[idx]["status"]="used_in_packet"; write_jsonl(src_path,recs)
    print(json.dumps({"status":"created","packet":pkt},indent=2))

# ─── Evidence Create ───
def evidence_create(args, pkt_path, ev_path, audit_path):
    records=load_jsonl(pkt_path); _,pkt=find_by_id(records,args.packet_id,"packet_id")
    if pkt is None: print(json.dumps({"error":"packet not found"})); sys.exit(1)
    claims=[{"claim_text":args.claim_text,"claim_type":args.claim_type,"confidence":args.confidence}]
    ev={"evidence_pack_id":f"ev_{uuid4().hex[:12]}","packet_id":args.packet_id,"topic":pkt.get("topic",""),
        "claims":claims,"created_at":now_iso()}
    append_jsonl(ev_path,ev); audit("evidence_created",f"id={ev['evidence_pack_id']}",audit_path,pid=args.packet_id)
    print(json.dumps({"status":"created","evidence":ev},indent=2))

# ─── Packet Synthesize ───
def packet_synthesize(args, pkt_path, audit_path):
    records=load_jsonl(pkt_path); idx,pkt=find_by_id(records,args.packet_id,"packet_id")
    if pkt is None: print(json.dumps({"error":"not found"})); sys.exit(1)
    records[idx]["summary"]=args.summary; records[idx]["key_findings"]=(args.findings or "").split(";") if args.findings else []
    records[idx]["uncertainties"]=(args.uncertainties or "").split(";") if args.uncertainties else []
    records[idx]["status"]="synthesized"; records[idx]["updated_at"]=now_iso()
    write_jsonl(pkt_path,records); audit("packet_synthesized",f"id={args.packet_id}",audit_path,pid=args.packet_id)
    print(json.dumps({"status":"synthesized","packet":records[idx]},indent=2))

# ─── Handoff Create ───
def handoff_create(args, pkt_path, audit_path):
    htype=args.handoff_type
    if htype not in VALID_HANDOFF_TYPES: print(json.dumps({"error":f"invalid: {htype}"})); sys.exit(1)
    records=load_jsonl(pkt_path); _,pkt=find_by_id(records,args.packet_id,"packet_id")
    if pkt is None: print(json.dumps({"error":"packet not found"})); sys.exit(1)

    # Memory handoff: delegate to memory_candidate.py create
    if htype=="memory":
        import subprocess
        script = str(PROJECT_ROOT / "scripts" / "memory_candidate.py")
        result = subprocess.run(["py", script, "create", "--content",
            f"[Research handoff] {pkt.get('topic','')} - {pkt.get('summary','')[:200]}",
            "--memory-type","project_decision","--sensitivity","internal","--source-type","manual","--source-agent","research_center"],
            capture_output=True,text=True,timeout=30,encoding="utf-8",errors="replace")
        out={"handoff_type":"memory","packet_id":args.packet_id,"delegated_to":"memory_candidate.py",
             "delegated_result":(result.stdout or "")[:500],"source_script":"memory_candidate.py","note":"Candidate created. NOT written to memory store directly."}
        audit("handoff_memory",f"packet={args.packet_id}",audit_path,pid=args.packet_id)
        print(json.dumps(out,indent=2))
        return

    hpath = DEFAULT_HANDOFFS_LOG / f"{htype}_handoffs.jsonl"
    ho={"handoff_id":f"ho_{uuid4().hex[:12]}","handoff_type":htype,"packet_id":args.packet_id,
        "topic":pkt.get("topic",""),"summary":(pkt.get("summary") or pkt.get("topic",""))[:300],
        "status":"created","created_at":now_iso()}
    append_jsonl(hpath,ho); audit(f"handoff_{htype}",f"id={ho['handoff_id']}",audit_path,pid=args.packet_id)
    print(json.dumps({"status":"created","handoff":ho},indent=2))

# ─── Source Archive ───
def source_archive(args, log_path, audit_path):
    records=load_jsonl(log_path); idx,src=find_by_id(records,args.source_id,"source_id")
    if src is None: print(json.dumps({"error":"not found"})); sys.exit(1)
    records[idx]["status"]="archived"; records[idx]["updated_at"]=now_iso(); write_jsonl(log_path,records)
    audit("source_archived",f"id={args.source_id}",audit_path,sid=args.source_id)
    print(json.dumps({"status":"archived","source_id":args.source_id}))

# ─── List ───
def list_items(args, log_path, label):
    items=load_jsonl(log_path); limit=min(args.limit or 20,100)
    print(json.dumps({label:items[-limit:],"total":len(items),"shown":min(len(items),limit)},indent=2))

# ─── Main ───
def main():
    p=argparse.ArgumentParser(description="Research Packet Manager")
    s=p.add_subparsers(dest="cmd")
    sc=s.add_parser("source-create"); sc.add_argument("--source-type",default="manual_text"); sc.add_argument("--title",required=True); sc.add_argument("--content-summary",required=True); sc.add_argument("--source-level",default="unknown"); sc.add_argument("--bias-notes",default=""); sc.add_argument("--sources-log",default=None); sc.add_argument("--audit-log",default=None)
    se=s.add_parser("source-evaluate"); se.add_argument("--source-id",required=True); se.add_argument("--trust-level",default="B"); se.add_argument("--credibility-score",type=float,default=0.5); se.add_argument("--freshness",default="acceptable"); se.add_argument("--bias-notes",default=""); se.add_argument("--sources-log",default=None); se.add_argument("--audit-log",default=None)
    sa=s.add_parser("source-archive"); sa.add_argument("--source-id",required=True); sa.add_argument("--sources-log",default=None); sa.add_argument("--audit-log",default=None)
    sl=s.add_parser("source-list"); sl.add_argument("--limit",type=int,default=20); sl.add_argument("--sources-log",default=None)
    pc=s.add_parser("packet-create"); pc.add_argument("--topic",required=True); pc.add_argument("--question",default=""); pc.add_argument("--source-ids",required=True); pc.add_argument("--sources-log",default=None); pc.add_argument("--packets-log",default=None); pc.add_argument("--audit-log",default=None)
    psyn=s.add_parser("packet-synthesize"); psyn.add_argument("--packet-id",required=True); psyn.add_argument("--summary",required=True); psyn.add_argument("--findings",default=""); psyn.add_argument("--uncertainties",default=""); psyn.add_argument("--packets-log",default=None); psyn.add_argument("--audit-log",default=None)
    pl=s.add_parser("packet-list"); pl.add_argument("--limit",type=int,default=20); pl.add_argument("--packets-log",default=None)
    ec=s.add_parser("evidence-create"); ec.add_argument("--packet-id",required=True); ec.add_argument("--claim-text",required=True); ec.add_argument("--claim-type",default="fact"); ec.add_argument("--confidence",type=float,default=0.5); ec.add_argument("--packets-log",default=None); ec.add_argument("--evidence-log",default=None); ec.add_argument("--audit-log",default=None)
    hc=s.add_parser("handoff-create"); hc.add_argument("--packet-id",required=True); hc.add_argument("--handoff-type",required=True,choices=list(VALID_HANDOFF_TYPES)); hc.add_argument("--packets-log",default=None); hc.add_argument("--audit-log",default=None)
    args=p.parse_args()
    if not args.cmd: p.print_help(); sys.exit(1)
    sp=Path(getattr(args,"sources_log","")) or DEFAULT_SOURCES_LOG
    pp=Path(getattr(args,"packets_log","")) or DEFAULT_PACKETS_LOG
    ep=Path(getattr(args,"evidence_log","")) or DEFAULT_EVIDENCE_LOG
    ap=Path(getattr(args,"audit_log","")) or DEFAULT_AUDIT_LOG
    if args.cmd=="source-create": source_create(args,sp,ap)
    elif args.cmd=="source-evaluate": source_evaluate(args,sp,ap)
    elif args.cmd=="source-archive": source_archive(args,sp,ap)
    elif args.cmd=="source-list": list_items(args,sp,"sources")
    elif args.cmd=="packet-create": packet_create(args,sp,pp,ap)
    elif args.cmd=="packet-synthesize": packet_synthesize(args,pp,ap)
    elif args.cmd=="packet-list": list_items(args,pp,"packets")
    elif args.cmd=="evidence-create": evidence_create(args,pp,ep,ap)
    elif args.cmd=="handoff-create": handoff_create(args,pp,ap)

if __name__=="__main__": main()
