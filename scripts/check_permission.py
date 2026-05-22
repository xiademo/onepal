#!/usr/bin/env python3
"""OnePal Permission Check Script - Task 03-A

Reads action_registry.json and permission_profiles.json.
Given action_id and profile_id, returns permission decision.

Usage:
    py scripts/check_permission.py --action <action_id> --profile <profile_id>
"""

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ACTION_REGISTRY = PROJECT_ROOT / "registries" / "action_registry.json"
PERMISSION_PROFILES = PROJECT_ROOT / "policies" / "permission_profiles.json"


def load_json(path):
    """Load and parse a JSON file with UTF-8 encoding."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def find_action(registry, action_id):
    """Find action by action_id in the registry."""
    for action in registry.get("actions", []):
        if action["action_id"] == action_id:
            return action
    return None


def find_profile(profiles_data, profile_id):
    """Find profile by profile_id."""
    for profile in profiles_data.get("profiles", []):
        if profile["profile_id"] == profile_id:
            return profile
    return None


def check_permission(action, profile, action_id):
    """Determine permission level for an action under a profile."""
    if action is None:
        return "action_not_registered"

    if not action.get("enabled", False):
        return "action_disabled"

    if profile is None:
        return "profile_not_found"

    permissions = profile.get("permissions", {})
    perm = permissions.get(action_id, "deny")
    return perm


def main():
    parser = argparse.ArgumentParser(description="OnePal Permission Check")
    parser.add_argument("--action", required=True, help="Action ID (e.g. action.read_file)")
    parser.add_argument("--profile", required=True, help="Profile ID (e.g. safe_readonly)")
    parser.add_argument("--registry", default=None, help="Path to action_registry.json (default: registries/action_registry.json)")
    parser.add_argument("--profiles", default=None, help="Path to permission_profiles.json (default: policies/permission_profiles.json)")
    args = parser.parse_args()

    registry_path = Path(args.registry) if args.registry else ACTION_REGISTRY
    profiles_path = Path(args.profiles) if args.profiles else PERMISSION_PROFILES

    registry = load_json(registry_path)
    profiles_data = load_json(profiles_path)

    action = find_action(registry, args.action)
    profile = find_profile(profiles_data, args.profile)

    result = check_permission(action, profile, args.action)

    output = {
        "action_id": args.action,
        "profile_id": args.profile,
        "status": result,
        "action_registered": action is not None,
        "action_enabled": action.get("enabled", False) if action else False,
        "profile_found": profile is not None,
    }

    if action:
        output["risk_level"] = action.get("risk_level", "?")
        output["approval_required"] = action.get("approval_required", False)
        output["state_mutation"] = action.get("state_mutation", False)

    print(json.dumps(output, indent=2, ensure_ascii=False))

    if result == "allow":
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
