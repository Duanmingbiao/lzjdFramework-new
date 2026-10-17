import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class PowerTournamentTests(unittest.TestCase):
    def test_registered(self):
        project = json.loads((ROOT / "project.json").read_text(encoding="utf-8-sig"))
        self.assertIn(19, project["registeredTasks"])
        self.assertIn("common/力之大会状态.mq", project["modules"])
        self.assertIn("flows/019_力之大会/力之大会.mq", project["modules"])

    def test_professional_ui_exactly_synced(self):
        ui = (ROOT / "ui/最小配置.uip").read_text(encoding="utf-8-sig")
        self.assertIn('名称:"RcMx2",提示内容:"冒险力之大会[",选中:false', ui)
        self.assertIn('名称:"RcMx2买",提示内容:"买5次",选中:false', ui)
        self.assertIn('名称:"RcMx2加入",提示内容:"快速加入",选中:false', ui)

    def test_boundaries_and_failure_rule(self):
        source = (ROOT / "flows/019_力之大会/力之大会.mq").read_text(encoding="utf-8-sig")
        self.assertIn("TickCount() - enteredAt > 10000", source)
        self.assertIn("TickCount() - purchaseAt > 10000", source)
        self.assertIn("TickCount() - progressAt > 60000", source)
        self.assertIn("恢复，不标完成", source)
        self.assertNotIn("powerTournamentDone = True", source)

    def test_patterns_registered(self):
        flow = (ROOT / "flows/019_力之大会/力之大会.mq").read_text(encoding="utf-8-sig")
        patterns = (ROOT / "common/图色参数.mq").read_text(encoding="utf-8-sig")
        for part in flow.split('WorldMatch("')[1:]:
            name = part.split('"', 1)[0]
            self.assertIn(f'Case "{name}"', patterns, name)

    def test_38_compatible_calls_only(self):
        source = (ROOT / "flows/019_力之大会/力之大会.mq").read_text(encoding="utf-8-sig")
        self.assertNotIn("OcrEx", source)
        self.assertNotIn("paddle", source.lower())
        self.assertNotIn("LuaAuxLib", source)


if __name__ == "__main__":
    unittest.main()
