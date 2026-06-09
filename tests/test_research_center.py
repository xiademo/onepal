#!/usr/bin/env python3
"""OnePal Research Center Tests - Task 10-B (27 tests)

Usage: py tests/test_research_center.py
"""

import json, subprocess, sys, tempfile
from pathlib import Path

PROJECT_ROOT=Path(__file__).resolve().parent.parent; PY=sys.executable
RP=PROJECT_ROOT/"scripts"/"research_packet.py"
CC=PROJECT_ROOT/"scripts"/"cognition_card.py"
passed,failed=0,0

def run(c,t=60):
    r=subprocess.run(c,capture_output=True,text=True,timeout=t,encoding="utf-8",errors="replace")
    return r.returncode,(r.stdout or ""),(r.stderr or "")
def tst(n,o,m=""):
    global passed,failed
    if o: passed+=1; print(f"  [PASS] {n}")
    else: failed+=1; print(f"  [FAIL] {n}"); [print(f"         {l}") for l in str(m).split("\n")[:2]]
def cnt(p):
    if not p.exists(): return 0
    c=0
    with open(p,"r",encoding="utf-8") as f:
        for l in f:
            if l.strip():
                try: json.loads(l); c+=1
                except: pass
    return c

def test_T1():
    print("\n--- T1: research/README.md exists ---")
    tst("T1: README exists",(PROJECT_ROOT/"research"/"README.md").exists())

def test_T2(td):
    print("\n--- T2: source create ---")
    sl=td/"s.jsonl"; al=td/"a.jsonl"
    ec,o,_=run([PY,str(RP),"source-create","--title","Test Source","--content-summary","A test source summary","--source-type","manual_text","--sources-log",str(sl),"--audit-log",str(al)])
    try: d=json.loads(o.strip())
    except: return tst("T2: create",False,o[:200])
    tst("T2: source created",d.get("status")=="created")

def test_T3(td):
    print("\n--- T3: source JSONL parseable ---")
    sl=td/"s.jsonl"; run([PY,str(RP),"source-create","--title","T3","--content-summary","Content","--source-type","manual_text","--sources-log",str(sl),"--audit-log",str(td/"a.jsonl")])
    tst("T3: JSONL parseable",cnt(sl)>0)

def test_T4(td):
    print("\n--- T4: missing content rejected ---")
    sl=td/"s.jsonl"; ec,o,_=run([PY,str(RP),"source-create","--title","No Content","--content-summary","","--sources-log",str(sl),"--audit-log",str(td/"a.jsonl")])
    tst("T4: empty rejected",ec!=0)

def test_T5(td):
    print("\n--- T5: D-trust source flagged ---")
    sl=td/"s.jsonl"; run([PY,str(RP),"source-create","--title","Low","--content-summary","Low quality","--source-level","D_low_quality_or_marketing","--sources-log",str(sl),"--audit-log",str(td/"a.jsonl")])
    srcs=[]
    with open(sl,"r",encoding="utf-8") as f:
        for l in f:
            if l.strip():
                try: srcs.append(json.loads(l))
                except: pass
    tst("T5: D-level source captured",srcs and srcs[-1].get("source_level","").startswith("D"))

def test_T6(td):
    print("\n--- T6: source evaluate ---")
    sl=td/"s6.jsonl"; run([PY,str(RP),"source-create","--title","Eval","--content-summary","Eval me","--sources-log",str(sl),"--audit-log",str(td/"a.jsonl")])
    srcs=[]
    with open(sl,"r",encoding="utf-8") as f:
        for l in f:
            if l.strip():
                try: srcs.append(json.loads(l))
                except: pass
    sid=srcs[-1]["source_id"]
    ec,o,_=run([PY,str(RP),"source-evaluate","--source-id",sid,"--trust-level","A","--credibility-score","0.9","--freshness","fresh","--sources-log",str(sl),"--audit-log",str(td/"a.jsonl")])
    try: d=json.loads(o.strip())
    except: return tst("T6: evaluate",False,o[:200])
    tst("T6: evaluated",d.get("status")=="evaluated")

def test_T7(td):
    print("\n--- T7: packet create ---")
    sl=td/"s.jsonl"; pl=td/"p.jsonl"; run([PY,str(RP),"source-create","--title","PktSrc","--content-summary","Packet source","--sources-log",str(sl),"--audit-log",str(td/"a.jsonl")])
    srcs=[]
    with open(sl,"r",encoding="utf-8") as f:
        for l in f:
            if l.strip():
                try: srcs.append(json.loads(l))
                except: pass
    sid=srcs[-1]["source_id"]
    ec,o,_=run([PY,str(RP),"packet-create","--topic","Test Packet","--source-ids",sid,"--sources-log",str(sl),"--packets-log",str(pl),"--audit-log",str(td/"a.jsonl")])
    try: d=json.loads(o.strip())
    except: return tst("T7: packet",False,o[:200])
    tst("T7: packet created",d.get("status")=="created")

def test_T8(td):
    print("\n--- T8: packet needs source_ids ---")
    pl=td/"p8.jsonl"; ec,o,_=run([PY,str(RP),"packet-create","--topic","NoSrc","--source-ids","","--packets-log",str(pl),"--audit-log",str(td/"a.jsonl")])
    tst("T8: no source rejected",ec!=0)

def test_T9(td):
    print("\n--- T9: evidence create ---")
    sl=td/"s.jsonl"; pl=td/"p.jsonl"; el=td/"e.jsonl"
    run([PY,str(RP),"source-create","--title","EvSrc","--content-summary","Evidence source","--sources-log",str(sl),"--audit-log",str(td/"a.jsonl")])
    srcs=[]
    with open(sl,"r",encoding="utf-8") as f:
        for l in f:
            if l.strip():
                try: srcs.append(json.loads(l))
                except: pass
    run([PY,str(RP),"packet-create","--topic","EvPkt","--source-ids",srcs[-1]["source_id"],"--sources-log",str(sl),"--packets-log",str(pl),"--audit-log",str(td/"a.jsonl")])
    pkts=[]
    with open(pl,"r",encoding="utf-8") as f:
        for l in f:
            if l.strip():
                try: pkts.append(json.loads(l))
                except: pass
    ec,o,_=run([PY,str(RP),"evidence-create","--packet-id",pkts[-1]["packet_id"],"--claim-text","Test claim","--claim-type","fact","--confidence","0.8","--packets-log",str(pl),"--evidence-log",str(el),"--audit-log",str(td/"a.jsonl")])
    try: d=json.loads(o.strip())
    except: return tst("T9: evidence",False,o[:200])
    tst("T9: evidence created",d.get("status")=="created")

def test_T10(td):
    print("\n--- T10: packet synthesize ---")
    sl=td/"s.jsonl"; pl=td/"p.jsonl"
    run([PY,str(RP),"source-create","--title","SynSrc","--content-summary","Synth source","--sources-log",str(sl),"--audit-log",str(td/"a.jsonl")])
    srcs=[]
    with open(sl,"r",encoding="utf-8") as f:
        for l in f:
            if l.strip():
                try: srcs.append(json.loads(l))
                except: pass
    run([PY,str(RP),"packet-create","--topic","SynPkt","--source-ids",srcs[-1]["source_id"],"--sources-log",str(sl),"--packets-log",str(pl),"--audit-log",str(td/"a.jsonl")])
    pkts=[]
    with open(pl,"r",encoding="utf-8") as f:
        for l in f:
            if l.strip():
                try: pkts.append(json.loads(l))
                except: pass
    ec,o,_=run([PY,str(RP),"packet-synthesize","--packet-id",pkts[-1]["packet_id"],"--summary","Key findings","--findings","Finding1;Finding2","--uncertainties","Uncertainty1","--packets-log",str(pl),"--audit-log",str(td/"a.jsonl")])
    try: d=json.loads(o.strip())
    except: return tst("T10: synth",False,o[:200])
    tst("T10: synthesized",d.get("status")=="synthesized")

def test_T11(td):
    print("\n--- T11: cognition card create ---")
    sl=td/"s.jsonl"; pl=td/"p.jsonl"; cl=td/"c.jsonl"
    run([PY,str(RP),"source-create","--title","CogSrc","--content-summary","Cog source","--sources-log",str(sl),"--audit-log",str(td/"a.jsonl")])
    srcs=[]
    with open(sl,"r",encoding="utf-8") as f:
        for l in f:
            if l.strip():
                try: srcs.append(json.loads(l))
                except: pass
    run([PY,str(RP),"packet-create","--topic","CogPkt","--source-ids",srcs[-1]["source_id"],"--sources-log",str(sl),"--packets-log",str(pl),"--audit-log",str(td/"a.jsonl")])
    pkts=[]
    with open(pl,"r",encoding="utf-8") as f:
        for l in f:
            if l.strip():
                try: pkts.append(json.loads(l))
                except: pass
    ec,o,_=run([PY,str(CC),"create","--packet-id",pkts[-1]["packet_id"],"--core-idea","Core","--why-it-matters","Important","--mental-model","Model","--questions","Q1;Q2;Q3","--confidence","0.8","--cards-log",str(cl),"--packets-log",str(pl),"--audit-log",str(td/"a.jsonl")])
    try: d=json.loads(o.strip())
    except: return tst("T11: card",False,o[:200])
    ok=d.get("status")=="created" and len(d["card"].get("self_test_questions",[]))>=2
    tst("T11: cognition card with questions",ok)

def test_T12(td):
    print("\n--- T12: handoff memory delegates to memory_candidate ---")
    sl=td/"s.jsonl"; pl=td/"p.jsonl"
    run([PY,str(RP),"source-create","--title","HoSrc","--content-summary","Handoff source","--sources-log",str(sl),"--audit-log",str(td/"a.jsonl")])
    srcs=[]
    with open(sl,"r",encoding="utf-8") as f:
        for l in f:
            if l.strip():
                try: srcs.append(json.loads(l))
                except: pass
    run([PY,str(RP),"packet-create","--topic","HoPkt","--source-ids",srcs[-1]["source_id"],"--sources-log",str(sl),"--packets-log",str(pl),"--audit-log",str(td/"a.jsonl")])
    pkts=[]
    with open(pl,"r",encoding="utf-8") as f:
        for l in f:
            if l.strip():
                try: pkts.append(json.loads(l))
                except: pass
    ec,o,_=run([PY,str(RP),"handoff-create","--packet-id",pkts[-1]["packet_id"],"--handoff-type","memory","--packets-log",str(pl),"--audit-log",str(td/"a.jsonl")])
    try: d=json.loads(o.strip())
    except: return tst("T12: handoff",False,o[:200])
    ok=isinstance(d,dict) and "delegated_to" in d
    tst("T12: memory handoff delegated",ok)

def test_T13(td):
    print("\n--- T13: handoff growth ---")
    sl=td/"s.jsonl"; pl=td/"p.jsonl"
    run([PY,str(RP),"source-create","--title","GrSrc","--content-summary","Growth source","--sources-log",str(sl),"--audit-log",str(td/"a.jsonl")])
    srcs=[]
    with open(sl,"r",encoding="utf-8") as f:
        for l in f:
            if l.strip():
                try: srcs.append(json.loads(l))
                except: pass
    run([PY,str(RP),"packet-create","--topic","GrPkt","--source-ids",srcs[-1]["source_id"],"--sources-log",str(sl),"--packets-log",str(pl),"--audit-log",str(td/"a.jsonl")])
    pkts=[]
    with open(pl,"r",encoding="utf-8") as f:
        for l in f:
            if l.strip():
                try: pkts.append(json.loads(l))
                except: pass
    ec,o,_=run([PY,str(RP),"handoff-create","--packet-id",pkts[-1]["packet_id"],"--handoff-type","growth","--packets-log",str(pl),"--audit-log",str(td/"a.jsonl")])
    try: d=json.loads(o.strip())
    except: return tst("T13: growth",False,o[:200])
    tst("T13: growth handoff created",d.get("status")=="created")

def test_T14(td):
    print("\n--- T14: source archive ---")
    sl=td/"s.jsonl"; run([PY,str(RP),"source-create","--title","ArchSrc","--content-summary","Archive me","--sources-log",str(sl),"--audit-log",str(td/"a.jsonl")])
    srcs=[]
    with open(sl,"r",encoding="utf-8") as f:
        for l in f:
            if l.strip():
                try: srcs.append(json.loads(l))
                except: pass
    ec,o,_=run([PY,str(RP),"source-archive","--source-id",srcs[-1]["source_id"],"--sources-log",str(sl),"--audit-log",str(td/"a.jsonl")])
    try: d=json.loads(o.strip())
    except: return tst("T14: archive",False,o[:200])
    tst("T14: archived",d.get("status")=="archived")

def test_T15(td):
    print("\n--- T15: audit log parseable ---")
    al=td/"a.jsonl"; sl=td/"s.jsonl"
    run([PY,str(RP),"source-create","--title","AudSrc","--content-summary","Audit source","--sources-log",str(sl),"--audit-log",str(al)])
    tst("T15: audit parseable",cnt(al)>0)

def test_T16(td):
    print("\n--- T16: secret content rejected ---")
    sl=td/"s.jsonl"; ec,o,_=run([PY,str(RP),"source-create","--title","SecretSrc","--content-summary","sk-abc123def456","--sources-log",str(sl),"--audit-log",str(td/"a.jsonl")])
    tst("T16: secret rejected",ec!=0)

def test_T17():
    print("\n--- T17: research JSONL gitignored ---")
    ok=True
    for p in ["research/sources/research_sources.jsonl","research/packets/research_packets.jsonl","logs/research_audit.jsonl"]:
        ec,o,_=run(["git","check-ignore","-v",p],t=10)
        if ec!=0: ok=False; print(f"  NOT IGNORED: {p}")
    tst("T17: research JSONL gitignored",ok)

def test_T18():
    print("\n--- T18: cognition card not storing full text ---")
    # Verify cognition_card.py has no reference to storing article/full text
    with open(PROJECT_ROOT/"scripts"/"cognition_card.py","r",encoding="utf-8") as f:
        c=f.read()
    tst("T18: card no full text storage","full_text" not in c and "article" not in c.lower())

def test_T19(td):
    """T19: source evaluate trust levels A/B/C/D."""
    print("\n--- T19: source trust levels ---")
    sl=td/"s19.jsonl"
    run([PY,str(RP),"source-create","--title","TL","--content-summary","Trust level test","--sources-log",str(sl),"--audit-log",str(td/"a.jsonl")])
    srcs=[]
    with open(sl,"r",encoding="utf-8") as f:
        for l in f:
            if l.strip():
                try: srcs.append(json.loads(l))
                except: pass
    sid=srcs[-1]["source_id"]
    for lvl in ["A","B","C","D"]:
        ec,o,_=run([PY,str(RP),"source-evaluate","--source-id",sid,"--trust-level",lvl,"--sources-log",str(sl),"--audit-log",str(td/"a.jsonl")])
    recs=[]
    with open(sl,"r",encoding="utf-8") as f:
        for l in f:
            if l.strip():
                try: recs.append(json.loads(l))
                except: pass
    tst("T19: trust level D applied",recs[-1].get("trust_level")=="D")

def test_T20(td):
    """T20: evidence claim types fact/opinion/prediction/risk."""
    print("\n--- T20: evidence claim types ---")
    sl=td/"s20.jsonl"; pl=td/"p20.jsonl"; el=td/"e20.jsonl"
    run([PY,str(RP),"source-create","--title","CT","--content-summary","Claim type test","--sources-log",str(sl),"--audit-log",str(td/"a.jsonl")])
    srcs=[]
    with open(sl,"r",encoding="utf-8") as f:
        for l in f:
            if l.strip():
                try: srcs.append(json.loads(l))
                except: pass
    run([PY,str(RP),"packet-create","--topic","CTPkt","--source-ids",srcs[-1]["source_id"],"--sources-log",str(sl),"--packets-log",str(pl),"--audit-log",str(td/"a.jsonl")])
    pkts=[]
    with open(pl,"r",encoding="utf-8") as f:
        for l in f:
            if l.strip():
                try: pkts.append(json.loads(l))
                except: pass
    for ct in ["fact","opinion","prediction","risk"]:
        run([PY,str(RP),"evidence-create","--packet-id",pkts[-1]["packet_id"],"--claim-text",f"{ct} claim","--claim-type",ct,"--packets-log",str(pl),"--evidence-log",str(el),"--audit-log",str(td/"a.jsonl")])
    tst("T20: claim types created",cnt(el)>=4)

def test_T21(td):
    """T21: cognition card archive."""
    print("\n--- T21: cognition card archive ---")
    sl=td/"s21.jsonl"; pl=td/"p21.jsonl"; cl=td/"c21.jsonl"
    run([PY,str(RP),"source-create","--title","Arc","--content-summary","Archive test","--sources-log",str(sl),"--audit-log",str(td/"a.jsonl")])
    srcs=[]
    with open(sl,"r",encoding="utf-8") as f:
        for l in f:
            if l.strip():
                try: srcs.append(json.loads(l))
                except: pass
    run([PY,str(RP),"packet-create","--topic","ArcPkt","--source-ids",srcs[-1]["source_id"],"--sources-log",str(sl),"--packets-log",str(pl),"--audit-log",str(td/"a.jsonl")])
    pkts=[]
    with open(pl,"r",encoding="utf-8") as f:
        for l in f:
            if l.strip():
                try: pkts.append(json.loads(l))
                except: pass
    run([PY,str(CC),"create","--packet-id",pkts[-1]["packet_id"],"--cards-log",str(cl),"--packets-log",str(pl),"--audit-log",str(td/"a.jsonl")])
    cards=[]
    with open(cl,"r",encoding="utf-8") as f:
        for l in f:
            if l.strip():
                try: cards.append(json.loads(l))
                except: pass
    ec,o,_=run([PY,str(CC),"archive","--card-id",cards[-1]["card_id"],"--cards-log",str(cl),"--audit-log",str(td/"a.jsonl")])
    try: d=json.loads(o.strip())
    except: return tst("T21: archive",False,o[:200])
    tst("T21: cognition card archived",d.get("status")=="archived")

def test_T22(td):
    """T22: malformed JSONL handled gracefully."""
    print("\n--- T22: malformed JSONL handled ---")
    sl=td/"s22.jsonl"
    with open(sl,"w",encoding="utf-8") as f: f.write('{"valid":1}\nnot json\n{"valid":2}\n')
    ec,o,_=run([PY,str(RP),"source-list","--sources-log",str(sl)])
    try: d=json.loads(o.strip())
    except: return tst("T22: list",False,o[:200])
    tst("T22: malformed JSONL handled",d.get("sources") and len(d["sources"])>=1)

def test_T23(td):
    """T23: handoff career."""
    print("\n--- T23: handoff career ---")
    sl=td/"s23.jsonl"; pl=td/"p23.jsonl"
    run([PY,str(RP),"source-create","--title","Car","--content-summary","Career source","--sources-log",str(sl),"--audit-log",str(td/"a.jsonl")])
    srcs=[]
    with open(sl,"r",encoding="utf-8") as f:
        for l in f:
            if l.strip():
                try: srcs.append(json.loads(l))
                except: pass
    run([PY,str(RP),"packet-create","--topic","CarPkt","--source-ids",srcs[-1]["source_id"],"--sources-log",str(sl),"--packets-log",str(pl),"--audit-log",str(td/"a.jsonl")])
    pkts=[]
    with open(pl,"r",encoding="utf-8") as f:
        for l in f:
            if l.strip():
                try: pkts.append(json.loads(l))
                except: pass
    ec,o,_=run([PY,str(RP),"handoff-create","--packet-id",pkts[-1]["packet_id"],"--handoff-type","career","--packets-log",str(pl),"--audit-log",str(td/"a.jsonl")])
    try: d=json.loads(o.strip())
    except: return tst("T23: career",False,o[:200])
    tst("T23: career handoff created",d.get("status")=="created")

def test_T24(td):
    """T24: handoff capability."""
    print("\n--- T24: handoff capability ---")
    sl=td/"s24.jsonl"; pl=td/"p24.jsonl"
    run([PY,str(RP),"source-create","--title","Cap","--content-summary","Capability source","--sources-log",str(sl),"--audit-log",str(td/"a.jsonl")])
    srcs=[]
    with open(sl,"r",encoding="utf-8") as f:
        for l in f:
            if l.strip():
                try: srcs.append(json.loads(l))
                except: pass
    run([PY,str(RP),"packet-create","--topic","CapPkt","--source-ids",srcs[-1]["source_id"],"--sources-log",str(sl),"--packets-log",str(pl),"--audit-log",str(td/"a.jsonl")])
    pkts=[]
    with open(pl,"r",encoding="utf-8") as f:
        for l in f:
            if l.strip():
                try: pkts.append(json.loads(l))
                except: pass
    ec,o,_=run([PY,str(RP),"handoff-create","--packet-id",pkts[-1]["packet_id"],"--handoff-type","capability","--packets-log",str(pl),"--audit-log",str(td/"a.jsonl")])
    try: d=json.loads(o.strip())
    except: return tst("T24: capability",False,o[:200])
    tst("T24: capability handoff created",d.get("status")=="created")

def test_T25(td):
    """T25: packet list."""
    print("\n--- T25: packet list ---")
    pl=td/"p25.jsonl"; sl=td/"s25.jsonl"
    run([PY,str(RP),"source-create","--title","PL","--content-summary","Packet list src","--sources-log",str(sl),"--audit-log",str(td/"a.jsonl")])
    srcs=[]
    with open(sl,"r",encoding="utf-8") as f:
        for l in f:
            if l.strip():
                try: srcs.append(json.loads(l))
                except: pass
    run([PY,str(RP),"packet-create","--topic","PLPkt","--source-ids",srcs[-1]["source_id"],"--sources-log",str(sl),"--packets-log",str(pl),"--audit-log",str(td/"a.jsonl")])
    ec,o,_=run([PY,str(RP),"packet-list","--packets-log",str(pl)])
    try: d=json.loads(o.strip())
    except: return tst("T25: list",False,o[:200])
    tst("T25: packet list works",d.get("packets") and len(d["packets"])>=1)

def test_T26(td):
    """T26: CLI path override works (test isolation)."""
    print("\n--- T26: CLI path override ---")
    sl=td/"custom_sources.jsonl"; al=td/"custom_audit.jsonl"
    run([PY,str(RP),"source-create","--title","Override","--content-summary","Custom path","--sources-log",str(sl),"--audit-log",str(al)])
    ok=sl.exists() and cnt(sl)>0
    tst("T26: path override works",ok)

def test_T27(td):
    """T27: no shell or network in source code."""
    print("\n--- T27: no shell/network in research scripts ---")
    for fname in ["research_packet.py","cognition_card.py"]:
        with open(PROJECT_ROOT/"scripts"/fname,"r",encoding="utf-8") as f:
            c=f.read()
        ok_shell="shell=True" not in c
        ok_url="http://" not in c and "https://" not in c
        tst(f"T27-{fname}: no shell=True",ok_shell)
        tst(f"T27-{fname}: no hardcoded URLs",ok_url)

def test_T28(td):
    """T28: overlong content rejected."""
    print("\n--- T28: overlong content rejected ---")
    sl=td/"s28.jsonl"; ec,o,_=run([PY,str(RP),"source-create","--title","Long","--content-summary","x"*3000,"--sources-log",str(sl),"--audit-log",str(td/"a.jsonl")])
    tst("T28: overlong rejected",ec!=0)

def main():
    global passed,failed
    print("="*60); print("OnePal Research Center Tests (T1-T18)"); print("="*60)
    test_T1()
    with tempfile.TemporaryDirectory(prefix="onepal_research_") as td:
        td=Path(td); test_T2(td); test_T3(td); test_T4(td); test_T5(td); test_T6(td)
        test_T7(td); test_T8(td); test_T9(td); test_T10(td); test_T11(td)
        test_T12(td); test_T13(td); test_T14(td); test_T15(td); test_T16(td)
        test_T19(td); test_T20(td); test_T21(td); test_T22(td)
        test_T23(td); test_T24(td); test_T25(td); test_T26(td); test_T27(td); test_T28(td)
    test_T17(); test_T18()
    print("\n"+"="*60); total=passed+failed; print(f"Results: {passed}/{total} PASS, {failed}/{total} FAIL"); print("="*60)
    sys.exit(0 if failed==0 else 1)

if __name__=="__main__": main()
