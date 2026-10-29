"""Turn an identification into the steps that actually get CarPlay working."""

EVO_ID56_STEPS = [
    "Connect a battery support charger (the car must hold 13+ V for the whole session) and an ENET cable.",
    "In E-Sys with PSdZData matching the car's I-Step: read the FA and the SVT, and save both.",
    "Read and save the HU_NBT2 coding (CAFD) and its current FSCs so you can roll back.",
    "Import the CarPlay FSC for HU_NBT2 (diagnostic address 0x63). Run 'Check FSC Status': "
    "the CarPlay entry must read accepted. Use a genuine FSC from a BMW dealer or a reputable "
    "coder; generated codes need a patched unit and can disappear after a flash.",
    "Edit the FA: add option 6CP (Apple CarPlay preparation, as BMWPost owners report it). "
    "Save the FA and write it to the car.",
    "VO-code HU_NBT2. If CarPlay still does not appear, set CARPLAY_SWT to 'aktiv' in the "
    "HU_NBT2 CAFD (FDL editor) and code again.",
    "Make sure the WLAN antenna lead is connected to the head unit; BMW's F-series CarPlay is "
    "wireless only. Fit it if the car never had it.",
    "Restart the head unit: hold the volume/power knob for about 30 seconds until it reboots.",
    "On the iPhone: Settings > General > CarPlay, with Bluetooth and Wi-Fi on. In iDrive: "
    "Media/Mobile devices > Connect new device > Apple CarPlay.",
]

EVO_ID4_STEPS = [
    "Flash HU_NBT2 to ID5/ID6 software with E-Sys and current PSdZData (support charger, "
    "ENET, and a full backup first; budget several hours).",
    "Then follow the NBT EVO ID5/ID6 steps.",
]

NBT_OPTIONS = [
    ("Swap to an NBT EVO ID5/ID6 head unit (the only route to BMW's built-in CarPlay)",
     ["A used HU_NBT2 with ID5/ID6 software, plus the adapter cabling owners list for "
      "NBT-to-EVO swaps (screen voltage/APIX lead, WLAN antenna).",
      "Code the unit to the car's VIN, VO-code it, load its FSCs (navigation, CarPlay, etc.).",
      "Then follow the NBT EVO ID5/ID6 steps.",
      "Expect a half day of work and some FDL coding; screen and cable compatibility depend on "
      "exact part numbers, so check them against your car before buying."]),
    ("Fit a CarPlay interface module behind the screen",
     ["Plugs in between the NBT and the central display and switches the screen to CarPlay.",
      "Keeps the factory iDrive and controller; some use the factory mic, some need their own.",
      "No coding, reversible, cheapest. It is extra hardware, which you wanted to avoid, but it "
      "is the only route that keeps your current head unit."]),
]


def plan_for(identification):
    key = identification.profile_key
    if key == "evo_id56":
        return {"headline": "Your unit can run BMW's own CarPlay: it needs coding, not hardware.",
                "steps": EVO_ID56_STEPS}
    if key == "evo_id4":
        return {"headline": "NBT EVO on ID4 software: flash to ID5/ID6, then code CarPlay.",
                "steps": EVO_ID4_STEPS + EVO_ID56_STEPS}
    if key == "nbt":
        return {"headline": "Original NBT: no coding, FSC or firmware unlocks CarPlay on this unit.",
                "options": NBT_OPTIONS}
    return {"headline": "Head unit not identified yet.",
            "steps": ["Connect E-Sys and read the SVT: the ECU at 0x63 is HU_NBT (NBT) or HU_NBT2 (EVO).",
                      "Or open the navigation map, Options > Navigation system version: "
                      "the version names NBT or NBT EVO."]}
