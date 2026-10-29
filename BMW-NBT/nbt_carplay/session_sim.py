"""Step a wireless CarPlay session through the gates a BMW head unit must pass.

The order follows how a wireless CarPlay session comes up (Apple WWDC 2017
"Developing Wireless CarPlay Systems"; Apple Platform Security): Bluetooth
iAP2 identification, MFi authentication, Wi-Fi credential hand-off, then the
AirPlay-style session with MFi-SAP encrypted video and audio. BMW adds its own
gate in front: the CarPlay application has to be enabled by FSC and coding.

The MFi step is a model, not Apple's real protocol: an HMAC stands in for the
signature the Apple chip makes with a key that never leaves the chip. It is
there to show why software cannot stand in for the chip: without a key Apple
provisioned, no response the head unit can compute will verify.
"""

import hashlib
import hmac
import os
from dataclasses import dataclass

from .profiles import Cap

PASS, FAIL, UNVERIFIED = "PASS", "FAIL", "UNVERIFIED"


class AppleRootOfTrust:
    """Stands in for Apple: provisions chips and checks their responses."""

    def __init__(self):
        self._chips = {}

    def provision_chip(self, serial):
        secret = os.urandom(32)
        self._chips[serial] = secret
        return secret

    def verify(self, serial, nonce, response):
        secret = self._chips.get(serial)
        if secret is None:
            return False
        return hmac.compare_digest(hmac.new(secret, nonce, hashlib.sha256).digest(), response)


@dataclass
class StageResult:
    stage: str
    status: str
    detail: str


def _need(profile, *caps):
    """PASS if every cap is YES, FAIL if any is NO, otherwise UNVERIFIED."""
    states = [profile.cap(c) for c in caps]
    missing = [c for c, s in zip(caps, states) if s is Cap.NO]
    unknown = [c for c, s in zip(caps, states) if s is Cap.UNKNOWN]
    if missing:
        return FAIL, "missing: " + ", ".join(missing)
    if unknown:
        return UNVERIFIED, "not confirmed: " + ", ".join(unknown)
    return PASS, "ok"


def _mfi_handshake(profile, apple):
    serial = f"{profile.key}-hu"
    # A unit with the chip has a key Apple provisioned; one without can only
    # make one up in software, which is what a firmware hack would have to do.
    key = apple.provision_chip(serial) if profile.cap("mfi_auth_chip") is Cap.YES else os.urandom(32)
    nonce = os.urandom(20)
    response = hmac.new(key, nonce, hashlib.sha256).digest()
    if apple.verify(serial, nonce, response):
        return PASS, "iPhone accepted the challenge response"
    if profile.cap("mfi_auth_chip") is Cap.UNKNOWN:
        return UNVERIFIED, "no confirmed Apple-provisioned key; a software-made key failed verification"
    return FAIL, "challenge response did not verify: no Apple-provisioned key"


def simulate(profile, apple=None):
    apple = apple or AppleRootOfTrust()
    results = []

    status, detail = _need(profile, "iap2_transport", "carplay_stack")
    results.append(StageResult("1. Bluetooth iAP2 identification (HU announces CarPlay)", status, detail))

    status, detail = _mfi_handshake(profile, apple)
    results.append(StageResult("2. MFi authentication challenge", status, detail))

    status, detail = _need(profile, "fsc_carplay", "coded_carplay")
    results.append(StageResult("3. BMW feature gate (FSC + coding)", status, detail))

    status, detail = _need(profile, "wifi_5ghz", "wlan_antenna")
    results.append(StageResult("4. Wi-Fi credential hand-off and join", status, detail))

    status, detail = _need(profile, "carplay_stack")
    results.append(StageResult("5. Session setup (Bonjour, RTSP, MFi-SAP keys)", status, detail))

    status, detail = _need(profile, "h264_decode", "carplay_stack")
    results.append(StageResult("6. H.264 video + audio streams to iDrive", status, detail))

    return results


def connects(results):
    return all(r.status == PASS for r in results)


def first_blocker(results):
    for r in results:
        if r.status == FAIL:
            return r
    return None
