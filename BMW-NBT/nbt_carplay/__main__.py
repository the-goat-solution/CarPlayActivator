import argparse
import sys

from .identify import identify
from .plan import plan_for
from .profiles import CAPABILITIES, PROFILES, Cap
from .session_sim import connects, first_blocker, simulate


def print_simulation(profile):
    print(f"\nSimulated wireless CarPlay session on: {profile.name}")
    print(f"  SoC: {profile.soc}\n  OS:  {profile.os}")
    results = simulate(profile)
    for r in results:
        print(f"  [{r.status:10}] {r.stage}: {r.detail}")
    blocker = first_blocker(results)
    if connects(results):
        print("  => CarPlay session comes up.")
    elif blocker:
        print(f"  => Blocked at: {blocker.stage}")
    else:
        print("  => Nothing is ruled out, but some pieces are unconfirmed.")
    for cap, note in profile.notes.items():
        print(f"  note ({cap}): {note}")
    return results


def cmd_check(args):
    ident = identify(args.ecu, args.nav_version, args.istep, args.build_date)
    print(f"Head unit: {ident.profile.name if ident.profile else 'unknown'} (confidence: {ident.confidence})")
    for e in ident.evidence:
        print(f"  - {e}")
    if ident.profile:
        print_simulation(ident.profile)
    plan = plan_for(ident)
    print(f"\n{plan['headline']}")
    for i, step in enumerate(plan.get("steps", []), 1):
        print(f"  {i}. {step}")
    for title, points in plan.get("options", []):
        print(f"\n  Option: {title}")
        for p in points:
            print(f"    - {p}")
    return 0


def cmd_simulate(args):
    profile = PROFILES[args.profile]
    unknown = [c for c in args.add if c not in CAPABILITIES]
    if unknown:
        print(f"unknown capability: {', '.join(unknown)}; choose from {', '.join(CAPABILITIES)}", file=sys.stderr)
        return 2
    if args.add:
        profile = profile.with_caps(**{c: Cap.YES for c in args.add})
    results = print_simulation(profile)
    return 0 if connects(results) else 1


def main(argv=None):
    parser = argparse.ArgumentParser(prog="nbt_carplay", description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    check = sub.add_parser("check", help="identify your head unit and print what it takes to get CarPlay")
    check.add_argument("--ecu", help="ECU name E-Sys shows at 0x63: HU_NBT or HU_NBT2")
    check.add_argument("--nav-version", help="iDrive 'Navigation system version' text")
    check.add_argument("--istep", help="I-Step, e.g. F015-14-03-506")
    check.add_argument("--build-date", help="production month, YYYY-MM")
    check.set_defaults(func=cmd_check)

    sim = sub.add_parser("simulate", help="run the session simulation for one profile")
    sim.add_argument("profile", choices=sorted(PROFILES))
    sim.add_argument("--add", nargs="*", default=[], metavar="CAP",
                     help="pretend these capabilities are present (e.g. fsc_carplay coded_carplay wlan_antenna)")
    sim.set_defaults(func=cmd_simulate)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
