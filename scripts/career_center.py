#!/usr/bin/env python3
"""OnePal Career Center - Task 15.

File-driven career assets, resume claims, JD matching, and manual application
planning. This script never sends messages, submits applications, or calls the
network.
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ASSETS = ROOT / "career" / "assets" / "career_assets.jsonl"
DEFAULT_CLAIMS = ROOT / "career" / "claims" / "resume_claims.jsonl"
DEFAULT_JDS = ROOT / "career" / "jds" / "jd_items.jsonl"
DEFAULT_EVALS = ROOT / "career" / "evaluations" / "jd_evaluations.jsonl"
DEFAULT_APPS = ROOT / "career" / "applications" / "application_records.jsonl"
DEFAULT_HANDOFFS = ROOT / "career" / "handoffs" / "career_handoffs.jsonl"
DEFAULT_AUDIT = ROOT / "logs" / "career_audit.jsonl"

VALID_ASSET_TYPES = {"project", "experience", "education", "certificate", "portfolio", "skill", "other"}
SECRET_PATTERNS = [
    r"sk-[a-zA-Z0-9]{10,}",
    r"-----BEGIN",
    r"ghp_[a-zA-Z0-9]{20,}",
    r"(?:api[_-]?key|password|token|secret)\s*[:=]\s*\S{8,}",
]


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def load_jsonl(path):
    if not path.exists():
        return []
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return rows


def append_jsonl(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def audit(action, detail, audit_path, **refs):
    entry = {
        "audit_id": f"audit_{uuid4().hex[:12]}",
        "action": action,
        "detail": detail[:300],
        "timestamp": now_iso(),
    }
    entry.update({k: v for k, v in refs.items() if v})
    append_jsonl(audit_path, entry)


def fail(message, status="error"):
    print(json.dumps({"status": status, "error": message}, ensure_ascii=False))
    sys.exit(1)


def csv(value):
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    return [v.strip() for v in str(value or "").split(",") if v.strip()]


def has_secret(*values):
    text = " ".join(str(v or "") for v in values)
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in SECRET_PATTERNS)


def find(rows, key, value):
    for row in rows:
        if row.get(key) == value:
            return row
    return None


def asset_create(args, assets_path, audit_path):
    title = args.title.strip()
    summary = args.summary.strip()
    if not title:
        fail("title required")
    if args.asset_type not in VALID_ASSET_TYPES:
        fail(f"invalid asset_type: {args.asset_type}")
    if has_secret(title, summary):
        audit("career_asset_rejected_secret", "secret-like content", audit_path)
        fail("secret-like content rejected", "rejected")
    evidence_refs = csv(args.evidence_refs)
    asset = {
        "asset_id": f"careerasset_{uuid4().hex[:12]}",
        "asset_type": args.asset_type,
        "title": title,
        "summary": summary,
        "evidence_refs": evidence_refs,
        "source_refs": csv(args.source_refs),
        "status": "ready" if evidence_refs else "needs_evidence",
        "created_at": now_iso(),
        "updated_at": None,
    }
    append_jsonl(assets_path, asset)
    audit("career_asset_created", f"asset={asset['asset_id']}", audit_path, asset_id=asset["asset_id"])
    print(json.dumps({"status": "created", "asset": asset}, indent=2, ensure_ascii=False))


def claim_create(args, claims_path, audit_path):
    text = args.claim_text.strip()
    if not text:
        fail("claim_text required")
    if has_secret(text):
        audit("resume_claim_rejected_secret", "secret-like content", audit_path)
        fail("secret-like content rejected", "rejected")
    evidence_refs = csv(args.evidence_refs)
    asset_refs = csv(args.asset_refs)
    backed = bool(evidence_refs or asset_refs)
    claim = {
        "claim_id": f"claim_{uuid4().hex[:12]}",
        "claim_text": text,
        "evidence_refs": evidence_refs,
        "asset_refs": asset_refs,
        "confidence": 0.85 if backed else 0.35,
        "status": "ready" if backed else "needs_evidence",
        "created_at": now_iso(),
        "updated_at": None,
    }
    append_jsonl(claims_path, claim)
    audit("resume_claim_created", f"claim={claim['claim_id']}", audit_path, claim_id=claim["claim_id"])
    print(json.dumps({"status": "created", "claim": claim}, indent=2, ensure_ascii=False))


def jd_create(args, jds_path, audit_path):
    title = args.title.strip()
    if not title:
        fail("title required")
    if has_secret(title, args.company, args.description_summary):
        fail("secret-like content rejected", "rejected")
    jd = {
        "jd_id": f"jd_{uuid4().hex[:12]}",
        "title": title,
        "company": args.company.strip(),
        "description_summary": args.description_summary.strip(),
        "requirements": csv(args.requirements),
        "source_ref": args.source_ref,
        "status": "active",
        "created_at": now_iso(),
        "updated_at": None,
    }
    append_jsonl(jds_path, jd)
    audit("jd_created", f"jd={jd['jd_id']}", audit_path, jd_id=jd["jd_id"])
    print(json.dumps({"status": "created", "jd": jd}, indent=2, ensure_ascii=False))


def normalize_words(text):
    return set(re.findall(r"[a-z0-9+#.-]+", (text or "").lower()))


def jd_evaluate(args, jds_path, claims_path, evaluations_path, audit_path):
    jd = find(load_jsonl(jds_path), "jd_id", args.jd_id)
    if jd is None:
        fail(f"jd '{args.jd_id}' not found", "not_found")
    claims = load_jsonl(claims_path)
    matched = []
    missing = []
    for req in jd.get("requirements", []):
        req_words = normalize_words(req)
        found = None
        for claim in claims:
            claim_words = normalize_words(claim.get("claim_text", ""))
            if req_words and len(req_words.intersection(claim_words)) >= max(1, min(2, len(req_words))):
                found = claim
                break
        if found and found.get("status") == "ready":
            matched.append(found.get("claim_id"))
        else:
            missing.append(req)
    req_count = max(1, len(jd.get("requirements", [])))
    score = round(len(set(matched)) / req_count, 3)
    if not claims or missing:
        recommendation = "needs_evidence"
        status = "needs_evidence"
    elif score >= 0.75:
        recommendation = "strong_match"
        status = "ready"
    elif score >= 0.4:
        recommendation = "possible_match"
        status = "ready"
    else:
        recommendation = "manual_review"
        status = "draft"
    evaluation = {
        "evaluation_id": f"jdeval_{uuid4().hex[:12]}",
        "jd_ref": args.jd_id,
        "matched_claim_refs": sorted(set(matched)),
        "missing_requirements": missing,
        "score": score,
        "recommendation": recommendation,
        "status": status,
        "created_at": now_iso(),
    }
    append_jsonl(evaluations_path, evaluation)
    audit("jd_evaluated", f"evaluation={evaluation['evaluation_id']}", audit_path, evaluation_id=evaluation["evaluation_id"])
    print(json.dumps({"status": "created", "evaluation": evaluation}, indent=2, ensure_ascii=False))


def application_create(args, jds_path, applications_path, audit_path):
    jd = find(load_jsonl(jds_path), "jd_id", args.jd_id)
    if jd is None:
        fail(f"jd '{args.jd_id}' not found", "not_found")
    notes = args.notes.strip()
    if has_secret(notes):
        fail("secret-like content rejected", "rejected")
    app = {
        "application_id": f"apprec_{uuid4().hex[:12]}",
        "jd_ref": args.jd_id,
        "asset_refs": csv(args.asset_refs),
        "claim_refs": csv(args.claim_refs),
        "status": "manual_review",
        "auto_submit": False,
        "notes": notes or None,
        "created_at": now_iso(),
        "updated_at": None,
    }
    append_jsonl(applications_path, app)
    audit("application_record_created", f"application={app['application_id']}", audit_path, application_id=app["application_id"])
    print(json.dumps({"status": "created", "application": app, "note": "manual review only; no auto-submit"}, indent=2, ensure_ascii=False))


def handoff_create(args, handoffs_path, audit_path):
    if args.source_type not in {"growth", "research", "memory", "manual"}:
        fail("source_type must be growth, research, memory, or manual")
    if not args.source_id.strip():
        fail("source_id required")
    if has_secret(args.summary):
        fail("secret-like content rejected", "rejected")
    handoff = {
        "handoff_id": f"careerhandoff_{uuid4().hex[:12]}",
        "source_type": args.source_type,
        "source_id": args.source_id.strip(),
        "summary": args.summary.strip(),
        "status": "captured",
        "created_at": now_iso(),
    }
    append_jsonl(handoffs_path, handoff)
    audit("career_handoff_created", f"handoff={handoff['handoff_id']}", audit_path, handoff_id=handoff["handoff_id"])
    print(json.dumps({"status": "created", "handoff": handoff}, indent=2, ensure_ascii=False))


def list_records(args):
    paths = {
        "assets": Path(args.assets_log) if args.assets_log else DEFAULT_ASSETS,
        "claims": Path(args.claims_log) if args.claims_log else DEFAULT_CLAIMS,
        "jds": Path(args.jds_log) if args.jds_log else DEFAULT_JDS,
        "evaluations": Path(args.evaluations_log) if args.evaluations_log else DEFAULT_EVALS,
        "applications": Path(args.applications_log) if args.applications_log else DEFAULT_APPS,
        "handoffs": Path(args.handoffs_log) if args.handoffs_log else DEFAULT_HANDOFFS,
    }
    rows = load_jsonl(paths[args.record_type])
    limit = min(args.limit or 20, 100)
    print(json.dumps({args.record_type: rows[-limit:], "total": len(rows), "shown": min(limit, len(rows))},
                     indent=2, ensure_ascii=False))


def add_paths(parser):
    parser.add_argument("--assets-log", default=None)
    parser.add_argument("--claims-log", default=None)
    parser.add_argument("--jds-log", default=None)
    parser.add_argument("--evaluations-log", default=None)
    parser.add_argument("--applications-log", default=None)
    parser.add_argument("--handoffs-log", default=None)
    parser.add_argument("--audit-log", default=None)


def main():
    parser = argparse.ArgumentParser(description="OnePal Career Center")
    sub = parser.add_subparsers(dest="cmd")

    asset = sub.add_parser("asset-create")
    asset.add_argument("--asset-type", default="project")
    asset.add_argument("--title", required=True)
    asset.add_argument("--summary", default="")
    asset.add_argument("--evidence-refs", default="")
    asset.add_argument("--source-refs", default="")
    add_paths(asset)

    claim = sub.add_parser("claim-create")
    claim.add_argument("--claim-text", required=True)
    claim.add_argument("--evidence-refs", default="")
    claim.add_argument("--asset-refs", default="")
    add_paths(claim)

    jd = sub.add_parser("jd-create")
    jd.add_argument("--title", required=True)
    jd.add_argument("--company", default="")
    jd.add_argument("--description-summary", default="")
    jd.add_argument("--requirements", default="")
    jd.add_argument("--source-ref", default=None)
    add_paths(jd)

    eval_cmd = sub.add_parser("jd-evaluate")
    eval_cmd.add_argument("--jd-id", required=True)
    add_paths(eval_cmd)

    app = sub.add_parser("application-create")
    app.add_argument("--jd-id", required=True)
    app.add_argument("--asset-refs", default="")
    app.add_argument("--claim-refs", default="")
    app.add_argument("--notes", default="")
    add_paths(app)

    handoff = sub.add_parser("handoff-create")
    handoff.add_argument("--source-type", default="manual")
    handoff.add_argument("--source-id", required=True)
    handoff.add_argument("--summary", default="")
    add_paths(handoff)

    listing = sub.add_parser("list")
    listing.add_argument("--record-type", required=True, choices=["assets", "claims", "jds", "evaluations", "applications", "handoffs"])
    listing.add_argument("--limit", type=int, default=20)
    add_paths(listing)

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        sys.exit(1)

    assets_path = Path(args.assets_log) if getattr(args, "assets_log", None) else DEFAULT_ASSETS
    claims_path = Path(args.claims_log) if getattr(args, "claims_log", None) else DEFAULT_CLAIMS
    jds_path = Path(args.jds_log) if getattr(args, "jds_log", None) else DEFAULT_JDS
    evaluations_path = Path(args.evaluations_log) if getattr(args, "evaluations_log", None) else DEFAULT_EVALS
    applications_path = Path(args.applications_log) if getattr(args, "applications_log", None) else DEFAULT_APPS
    handoffs_path = Path(args.handoffs_log) if getattr(args, "handoffs_log", None) else DEFAULT_HANDOFFS
    audit_path = Path(args.audit_log) if getattr(args, "audit_log", None) else DEFAULT_AUDIT

    if args.cmd == "asset-create":
        asset_create(args, assets_path, audit_path)
    elif args.cmd == "claim-create":
        claim_create(args, claims_path, audit_path)
    elif args.cmd == "jd-create":
        jd_create(args, jds_path, audit_path)
    elif args.cmd == "jd-evaluate":
        jd_evaluate(args, jds_path, claims_path, evaluations_path, audit_path)
    elif args.cmd == "application-create":
        application_create(args, jds_path, applications_path, audit_path)
    elif args.cmd == "handoff-create":
        handoff_create(args, handoffs_path, audit_path)
    elif args.cmd == "list":
        list_records(args)


if __name__ == "__main__":
    main()
