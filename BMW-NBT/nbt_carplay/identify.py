"""Work out which head unit a car has from what the owner can read off it.

Strongest evidence first: the ECU name E-Sys shows at address 0x63 (HU_NBT vs
HU_NBT2), then the map version string in iDrive, then the I-Step and build
date. Dates only give a likelihood; the F15 changed over around mid-2016 and
the month varies by market.
"""

import re
from dataclasses import dataclass, field

from .profiles import PROFILES

# The F15 picked up NBT EVO around 06-07/2016 (BMWPost, autommi). Before the
# window it is NBT, after it EVO with ID5 software or later.
EVO_WINDOW_START = (2016, 6)
EVO_WINDOW_END = (2016, 7)
ID5_FIRST_ISTEP = (2016, 7)

ISTEP_RE = re.compile(r"^([A-Z]\d{3})-(\d{2})-(\d{2})-(\d{3})$")
DATE_RE = re.compile(r"^(\d{4})-(\d{1,2})$")


@dataclass
class Identification:
    profile_key: str  # "nbt", "evo_id4", "evo_id56" or "unknown"
    confidence: str  # "high", "medium", "low"
    evidence: list = field(default_factory=list)

    @property
    def profile(self):
        return PROFILES.get(self.profile_key)


def parse_istep(istep):
    """'F015-16-07-503' -> (2016, 7). Raises ValueError on bad input."""
    m = ISTEP_RE.match(istep.strip().upper())
    if not m:
        raise ValueError(f"I-Step {istep!r} is not in the form F015-16-07-503")
    return 2000 + int(m.group(2)), int(m.group(3))


def parse_month(value):
    """'2014-05' -> (2014, 5). Raises ValueError on bad input."""
    m = DATE_RE.match(value.strip())
    if not m or not 1 <= int(m.group(2)) <= 12:
        raise ValueError(f"date {value!r} is not in the form YYYY-MM")
    return int(m.group(1)), int(m.group(2))


def identify(ecu_name=None, nav_version=None, istep=None, build_date=None):
    evidence = []
    family = None  # "nbt" or "evo"
    confidence = "low"

    if ecu_name:
        name = ecu_name.strip().upper()
        if name == "HU_NBT2":
            family, confidence = "evo", "high"
            evidence.append("E-Sys reports HU_NBT2 at 0x63: NBT EVO hardware.")
        elif name == "HU_NBT":
            family, confidence = "nbt", "high"
            evidence.append("E-Sys reports HU_NBT at 0x63: original NBT hardware.")
        else:
            evidence.append(f"ECU name {ecu_name!r} is neither HU_NBT nor HU_NBT2; ignored.")

    if nav_version:
        says_evo = "EVO" in nav_version.upper()
        says_nbt = "NBT" in nav_version.upper()
        if says_nbt or says_evo:
            nav_family = "evo" if says_evo else "nbt"
            evidence.append(f"Map version {nav_version!r} names {'NBT EVO' if says_evo else 'NBT'}.")
            if family is None:
                family, confidence = nav_family, "medium"
            elif family != nav_family:
                evidence.append("Map version disagrees with the ECU name; trusting the ECU name.")

    istep_ym = None
    if istep:
        istep_ym = parse_istep(istep)
        evidence.append(f"I-Step {istep} = {istep_ym[0]}-{istep_ym[1]:02d}.")

    date_ym = parse_month(build_date) if build_date else None
    when = date_ym or istep_ym
    if family is None and when:
        if when < EVO_WINDOW_START:
            family = "nbt"
            evidence.append("Built before the mid-2016 EVO changeover: almost certainly NBT.")
        elif when > EVO_WINDOW_END:
            family = "evo"
            evidence.append("Built after the mid-2016 EVO changeover: most likely NBT EVO.")
        else:
            evidence.append("Built inside the mid-2016 changeover window: check E-Sys or the map version.")
        # A date well clear of 2016 is a fair bet; one close to the window is not.
        confidence = "medium" if when < (2016, 1) or when > (2016, 12) else "low"

    if family == "nbt":
        return Identification("nbt", confidence, evidence)
    if family == "evo":
        if istep_ym is None:
            evidence.append("No I-Step given: assuming ID5/ID6 software; confirm before buying an FSC.")
            return Identification("evo_id56", "low" if confidence == "low" else "medium", evidence)
        if istep_ym < ID5_FIRST_ISTEP:
            evidence.append("I-Step older than 16-07: the unit runs ID4 software.")
            return Identification("evo_id4", confidence, evidence)
        evidence.append("I-Step 16-07 or newer: ID5/ID6 software.")
        return Identification("evo_id56", confidence, evidence)
    return Identification("unknown", "low", evidence or ["Nothing to go on: give the E-Sys ECU name or the map version."])
