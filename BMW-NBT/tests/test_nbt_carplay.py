import io
import unittest
from contextlib import redirect_stdout

from nbt_carplay.__main__ import main
from nbt_carplay.identify import identify, parse_istep
from nbt_carplay.plan import plan_for
from nbt_carplay.profiles import NBT, NBT_EVO_ID4, NBT_EVO_ID5_6, Cap
from nbt_carplay.session_sim import FAIL, PASS, AppleRootOfTrust, connects, first_blocker, simulate


class IdentifyTests(unittest.TestCase):
    def test_ecu_name_wins(self):
        ident = identify(ecu_name="HU_NBT", nav_version="NBT EVO 2020-1", build_date="2017-03")
        self.assertEqual(ident.profile_key, "nbt")
        self.assertEqual(ident.confidence, "high")

    def test_2014_x5_is_nbt(self):
        ident = identify(build_date="2014-05")
        self.assertEqual(ident.profile_key, "nbt")
        self.assertEqual(ident.confidence, "medium")

    def test_map_version_names_nbt(self):
        self.assertEqual(identify(nav_version="Road Map North America NBT 2019-2").profile_key, "nbt")

    def test_evo_with_old_istep_is_id4(self):
        self.assertEqual(identify(ecu_name="HU_NBT2", istep="F015-16-03-505").profile_key, "evo_id4")

    def test_evo_with_new_istep_is_id56(self):
        self.assertEqual(identify(ecu_name="HU_NBT2", istep="F015-17-11-505").profile_key, "evo_id56")

    def test_changeover_window_is_unknown(self):
        self.assertEqual(identify(build_date="2016-06").profile_key, "unknown")

    def test_nothing_given(self):
        self.assertEqual(identify().profile_key, "unknown")

    def test_bad_istep(self):
        with self.assertRaises(ValueError):
            parse_istep("16-07")


class SimulationTests(unittest.TestCase):
    def test_nbt_never_connects(self):
        results = simulate(NBT)
        self.assertFalse(connects(results))
        self.assertIn("carplay_stack", first_blocker(results).detail)

    def test_nbt_blocked_even_with_coding_and_antenna(self):
        # Coding and an antenna are all a software-only hack could add; the stack is still missing.
        patched = NBT.with_caps(fsc_carplay=Cap.YES, coded_carplay=Cap.YES, wlan_antenna=Cap.YES)
        self.assertFalse(connects(simulate(patched)))

    def test_evo_id4_needs_flash(self):
        self.assertIn("carplay_stack", first_blocker(simulate(NBT_EVO_ID4)).detail)

    def test_evo_id56_blocked_only_by_coding_and_antenna(self):
        failed = [r for r in simulate(NBT_EVO_ID5_6) if r.status != PASS]
        self.assertEqual([r.stage[0] for r in failed], ["3", "4"])

    def test_evo_id56_connects_once_coded(self):
        coded = NBT_EVO_ID5_6.with_caps(fsc_carplay=Cap.YES, coded_carplay=Cap.YES, wlan_antenna=Cap.YES)
        self.assertTrue(connects(simulate(coded)))

    def test_software_key_fails_mfi(self):
        no_chip = NBT_EVO_ID5_6.with_caps(mfi_auth_chip=Cap.NO)
        mfi = simulate(no_chip)[1]
        self.assertEqual(mfi.status, FAIL)

    def test_root_of_trust_rejects_unprovisioned(self):
        apple = AppleRootOfTrust()
        self.assertFalse(apple.verify("nope", b"n", b"r"))


class PlanAndCliTests(unittest.TestCase):
    def test_nbt_plan_offers_options_not_coding(self):
        plan = plan_for(identify(ecu_name="HU_NBT"))
        self.assertNotIn("steps", plan)
        self.assertEqual(len(plan["options"]), 2)

    def test_id4_plan_starts_with_flash(self):
        plan = plan_for(identify(ecu_name="HU_NBT2", istep="F015-16-03-505"))
        self.assertIn("Flash", plan["steps"][0])

    def run_cli(self, *argv):
        out = io.StringIO()
        with redirect_stdout(out):
            code = main(list(argv))
        return code, out.getvalue()

    def test_cli_check(self):
        code, out = self.run_cli("check", "--build-date", "2014-05")
        self.assertEqual(code, 0)
        self.assertIn("Original NBT", out)

    def test_cli_simulate_exit_codes(self):
        self.assertEqual(self.run_cli("simulate", "nbt")[0], 1)
        code, _ = self.run_cli("simulate", "evo_id56", "--add", "fsc_carplay", "coded_carplay", "wlan_antenna")
        self.assertEqual(code, 0)

    def test_cli_bad_input(self):
        self.assertEqual(self.run_cli("check", "--istep", "garbage")[0], 2)


if __name__ == "__main__":
    unittest.main()
