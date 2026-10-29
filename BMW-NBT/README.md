# CarPlay on a BMW NBT (iDrive 4) head unit

Research notes, a feasibility simulator and step-by-step instructions for getting
Apple CarPlay into an F-series BMW (written for a 2014 X5 F15).

## Short answer

**A 2014 X5 almost certainly has the original NBT (`HU_NBT`). No coding, FSC or firmware
change gives that unit CarPlay.** BMW's built-in CarPlay exists only in NBT EVO
(`HU_NBT2`) running ID5/ID6 software. On those units it is turned on by coding, with no
extra hardware. Check which unit you have first (below), because a few late-2016 F15s
left the factory with EVO.

## Why the CarPlay Activator tweak in this repo can't do it

`CarPlayActivator/` is an iOS 8 jailbreak tweak. It runs on the **iPhone** and makes
SpringBoard draw Apple's CarPlay ("Stark") interface on the phone's own screen. It has no
code that runs in a car, and nothing in it can be moved to a head unit. CarPlay doesn't
work by the phone pushing a UI to any screen: the car has to run its own CarPlay receiver.

## What a head unit needs for CarPlay

A wireless CarPlay session (the only kind BMW F-series supports) comes up in this order:

| # | Stage | What the head unit must have |
|---|-------|------------------------------|
| 1 | Bluetooth iAP2 identification | iAP2 stack that announces CarPlay support |
| 2 | MFi authentication | Apple authentication coprocessor with an Apple-issued certificate. The phone challenges it and checks the signed answer |
| 3 | BMW feature gate | CarPlay FSC imported + HU coded (`6CP`, `CARPLAY_SWT`) |
| 4 | Wi-Fi hand-off | Wi-Fi radio + WLAN antenna. iAP2 passes the Wi-Fi credentials to the phone |
| 5 | Session setup | Apple's licensed CarPlay communication plug-in (Bonjour, RTSP, MFi-SAP AES-128 keys) |
| 6 | Streams | H.264 decode to the display, audio routing, mic |

Stages 2 and 5 can't be done in software by anyone outside the head unit maker. The
authentication key is inside an Apple chip and never leaves it. The CarPlay plug-in is
Apple-licensed code that Harman shipped only in NBT EVO ID5/ID6 firmware.

## How the hardware compares

| | NBT (`HU_NBT`) | NBT EVO (`HU_NBT2`) |
|---|---|---|
| Years (F15) | 2013 – ~mid-2016 | ~mid-2016 on |
| Processors | TI Jacinto family (teardown); main SoC not publicly confirmed | TI OMAP 5 1.5 GHz + TI Jacinto 5, PowerVR SGX544MP2 |
| RAM | not published | 2 GB (ID4), 4 GB (ID5/ID6) |
| OS | QNX 6.5 | QNX 6.5 |
| CarPlay in any firmware | **never** | ID5/ID6 |

The NBT's limit isn't processing power. Plenty of cheaper chips decode a CarPlay stream.
The problem is that the unit has no CarPlay software and no authentication path the
iPhone will accept, and BMW never released firmware for it that adds them. A modified
firmware would still fail at stage 2. The simulator below shows this.

## Step 1: identify your head unit

Use any of these, strongest first:

1. **E-Sys:** connect with an ENET cable and read the SVT. The ECU at `0x63` is `HU_NBT`
   (NBT) or `HU_NBT2` (EVO).
2. **iDrive:** open the navigation map > Options > *Navigation system version*. The version
   string says `NBT` or `NBT EVO`.
3. **Build date / I-Step:** before 06/2016 means NBT. After 07/2016 means EVO with ID5/ID6.

Then run the checker (Python 3.9+, no dependencies):

```sh
cd BMW-NBT
python3 -m nbt_carplay check --ecu HU_NBT --build-date 2014-05
python3 -m nbt_carplay check --nav-version "NBT EVO 2020-1" --istep F015-17-03-503
```

It tells you which unit you have, simulates the CarPlay session on it, and prints the
steps for your case.

## Step 2a: you have NBT EVO with ID5/ID6 software (coding only)

1. Connect a battery support charger (keep 13+ V throughout) and an ENET cable.
2. In E-Sys, with PSdZData that matches your I-Step, read and save the FA and SVT.
3. Back up the `HU_NBT2` coding (CAFD) and its existing FSCs.
4. Import the CarPlay FSC for `HU_NBT2` (diagnostic address `0x63`). Run *Check FSC Status*:
   CarPlay must show **accepted**. Use a genuine FSC from a dealer or a reputable coder.
   Generated codes need a patched unit and can disappear after a firmware flash.
5. Edit the FA: add option `6CP` (Apple CarPlay preparation, as BMWPost owners report it).
   Write the FA to the car.
6. VO-code `HU_NBT2`. If CarPlay still doesn't show up, set `CARPLAY_SWT` = `aktiv` in the
   FDL editor and code again.
7. Make sure the WLAN antenna lead is connected to the head unit. Fit one if the car never had it.
8. Reboot the head unit by holding the volume/power knob for about 30 seconds.
9. On the iPhone, open Settings > General > CarPlay with Bluetooth and Wi-Fi on. In iDrive,
   go to Mobile devices > Connect new device > Apple CarPlay.

**NBT EVO on ID4 software:** first flash it to ID5/ID6 with E-Sys and current PSdZData
(back up first, keep the charger on, allow several hours), then follow the steps above.

## Step 2b: you have the original NBT (most 2014 X5s)

There's no way to do it without hardware. These are the real options:

1. **Swap in an NBT EVO ID5/ID6 head unit.** This is the only route to BMW's own
   CarPlay, with the factory look and the iDrive controller. Owners doing NBT-to-EVO
   swaps in the F15 list: a used `HU_NBT2`, a screen voltage/APIX adapter lead, a WLAN
   antenna, and coding (VIN, VO, FSCs for navigation and CarPlay, some FDL). Check part
   numbers for screen and cable compatibility before you buy. Then do Step 2a.
2. **Fit a CarPlay interface module** between the NBT and the screen. You'd be adding
   hardware, but you keep the current head unit and no coding is needed. It's the
   cheapest option and can be undone.

## Simulator

```sh
python3 -m nbt_carplay simulate nbt
python3 -m nbt_carplay simulate nbt --add fsc_carplay coded_carplay wlan_antenna wifi_5ghz mfi_auth_chip iap2_transport h264_decode
python3 -m nbt_carplay simulate evo_id56 --add fsc_carplay coded_carplay wlan_antenna
python3 -m unittest discover -s tests -v
```

The second command shows the key result. Even if an NBT got every piece of hardware and
coding a hack could give it, the session still stops at stages 1, 5 and 6 because the
CarPlay stack is missing. The MFi stage is modelled with an HMAC standing in for the
Apple chip's signature. A head unit without an Apple-provisioned key can only make one
up, and that never verifies.

Capabilities are marked `yes` / `no` / `unknown` in `nbt_carplay/profiles.py`, each with
a note on its source. Things that aren't publicly confirmed (for example whether NBT has
an auth chip) stay `unknown` and show as `UNVERIFIED` instead of being guessed.

## Sources and caveats

Most details about BMW head units come from hobbyist teardowns, BMWPost threads and
vendor pages, not from BMW or Harman. Check option codes and part numbers against your
own car's FA and build sheet before you buy or code anything. Back up before every write.

- F15 BMWPost: "Apple CarPlay Enabling" (FSC import at 0x63, 6CP, CARPLAY_SWT), "F15 NBT Evo Retrofit", "NBT to NBT Evo"
- hakstuff.net: teardowns of the NBT (B114) and NBT EVO (B211) head units
- Apple Platform Security guide (MFi authentication, MFi-SAP); WWDC 2017 session 717 "Developing Wireless CarPlay Systems"
- Vendor activation pages (MAK Coding, bimmernavigation, kdrcoding): software activation is EVO ID5/ID6 only
