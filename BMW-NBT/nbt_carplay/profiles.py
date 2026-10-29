"""Head unit capability profiles.

Each capability is YES, NO or UNKNOWN, with a note on where the claim comes
from. Hobbyist teardowns, BMWPost threads and vendor pages are the only public
sources for most of this, so anything not backed by more than one of them is
marked UNKNOWN rather than guessed.
"""

from dataclasses import dataclass, field
from enum import Enum


class Cap(Enum):
    YES = "yes"
    NO = "no"
    UNKNOWN = "unknown"


# What a head unit has to provide for a CarPlay session to come up.
CAPABILITIES = {
    "iap2_transport": "iAP2 link to the phone (USB host role switch or Bluetooth)",
    "mfi_auth_chip": "Apple MFi authentication coprocessor with an Apple-issued certificate",
    "carplay_stack": "Apple-licensed CarPlay communication plug-in in the firmware",
    "wifi_5ghz": "Wi-Fi radio able to host the 5 GHz link wireless CarPlay uses",
    "wlan_antenna": "WLAN antenna lead connected to the head unit",
    "h264_decode": "Hardware H.264 decode to the central display",
    "fsc_carplay": "BMW FSC (enabling code) for the CarPlay application imported",
    "coded_carplay": "HU coded for CarPlay (FA option + CARPLAY_SWT active)",
}


@dataclass
class Profile:
    key: str
    name: str
    years: str
    soc: str
    os: str
    caps: dict
    notes: dict = field(default_factory=dict)
    # True when the missing pieces can be added by coding alone (no parts).
    coding_only_fix: bool = False

    def cap(self, name):
        return self.caps.get(name, Cap.UNKNOWN)

    def with_caps(self, **overrides):
        caps = dict(self.caps)
        caps.update(overrides)
        return Profile(self.key, self.name, self.years, self.soc, self.os,
                       caps, dict(self.notes), self.coding_only_fix)


NBT = Profile(
    key="nbt",
    name="NBT (iDrive 4, HU_NBT)",
    years="2012-2016 (F15 X5 until roughly mid-2016)",
    soc="TI Jacinto-family processors (hakstuff teardown, B114); main application SoC not publicly confirmed",
    os="QNX 6.5",
    caps={
        "iap2_transport": Cap.UNKNOWN,
        "mfi_auth_chip": Cap.UNKNOWN,
        "carplay_stack": Cap.NO,
        "wifi_5ghz": Cap.UNKNOWN,
        "wlan_antenna": Cap.NO,
        "h264_decode": Cap.UNKNOWN,
        "fsc_carplay": Cap.NO,
        "coded_carplay": Cap.NO,
    },
    notes={
        "carplay_stack": "No NBT firmware release ever shipped CarPlay; every vendor and forum "
                         "source says NBT needs an interface box or a head-unit swap.",
        "fsc_carplay": "There is no CarPlay application ID in NBT firmware for an FSC to unlock.",
        "mfi_auth_chip": "NBT talks to iPhones for music over USB, but nothing public shows a "
                         "CarPlay-capable auth identity, and the chip alone would not be enough.",
    },
)

NBT_EVO_ID4 = Profile(
    key="evo_id4",
    name="NBT EVO with ID4 software (HU_NBT2)",
    years="about 07/2015-07/2016 in some series",
    soc="TI OMAP 5 @1.5 GHz + TI Jacinto 5, PowerVR SGX544MP2 (hakstuff teardown, B211)",
    os="QNX 6.5",
    caps={
        "iap2_transport": Cap.YES,
        "mfi_auth_chip": Cap.UNKNOWN,
        "carplay_stack": Cap.NO,
        "wifi_5ghz": Cap.YES,
        "wlan_antenna": Cap.UNKNOWN,
        "h264_decode": Cap.YES,
        "fsc_carplay": Cap.NO,
        "coded_carplay": Cap.NO,
    },
    notes={
        "carplay_stack": "ID4 software has no CarPlay. Flashing the unit to ID5/ID6 software "
                         "(E-Sys + PSdZData) is required first; 2 GB RAM units are reported to work.",
    },
)

NBT_EVO_ID5_6 = Profile(
    key="evo_id56",
    name="NBT EVO with ID5/ID6 software (HU_NBT2)",
    years="from about 07/2016",
    soc="TI OMAP 5 @1.5 GHz + TI Jacinto 5, PowerVR SGX544MP2 (hakstuff teardown, B211)",
    os="QNX 6.5",
    caps={
        "iap2_transport": Cap.YES,
        "mfi_auth_chip": Cap.YES,
        "carplay_stack": Cap.YES,
        "wifi_5ghz": Cap.YES,
        "wlan_antenna": Cap.UNKNOWN,
        "h264_decode": Cap.YES,
        "fsc_carplay": Cap.NO,
        "coded_carplay": Cap.NO,
    },
    notes={
        "wlan_antenna": "BMW's F-series CarPlay is wireless only and needs the WLAN antenna "
                        "lead; cars without the factory option need it fitted.",
        "fsc_carplay": "Import the CarPlay FSC with E-Sys (diagnostic address 0x63), then "
                       "'Check FSC Status' must show it as accepted.",
    },
    coding_only_fix=True,
)

PROFILES = {p.key: p for p in (NBT, NBT_EVO_ID4, NBT_EVO_ID5_6)}
