import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class NormalAdventureDungeonTests(unittest.TestCase):
    def test_registered_and_ordered(self):
        project = json.loads((ROOT / "project.json").read_text(encoding="utf-8-sig"))
        self.assertIn(18, project["registeredTasks"])
        self.assertIn("common/冒险副本状态.mq", project["modules"])
        self.assertIn("flows/018_冒险副本/冒险副本.mq", project["modules"])

    def test_professional_config_exactly_synced(self):
        ui = (ROOT / "ui/最小配置.uip").read_text(encoding="utf-8-sig")
        self.assertIn('名称:"RcMx1",提示内容:"冒险新图",选中:false', ui)

    def test_professional_boundaries_and_project_failure_rule(self):
        source = (ROOT / "flows/018_冒险副本/冒险副本.mq").read_text(encoding="utf-8-sig")
        self.assertIn('TickCount() - normalAdventureProgressAt > 15000', source)
        self.assertIn('TickCount() - normalAdventureProgressAt > 40000', source)
        self.assertIn('repeatedMapCount > 5', source)
        self.assertIn('恢复，不标完成', source)
        self.assertNotIn('normalAdventureDone = True', source)

    def test_all_recognition_patterns_registered(self):
        flow = (ROOT / "flows/018_冒险副本/冒险副本.mq").read_text(encoding="utf-8-sig")
        patterns = (ROOT / "common/图色参数.mq").read_text(encoding="utf-8-sig")
        names = set()
        marker = 'WorldMatch("'
        for part in flow.split(marker)[1:]:
            names.add(part.split('"', 1)[0])
        for name in names:
            self.assertIn(f'Case "{name}"', patterns, name)

    def test_38_compatible_calls_only(self):
        source = (ROOT / "flows/018_冒险副本/冒险副本.mq").read_text(encoding="utf-8-sig")
        self.assertNotIn("OcrEx", source)
        self.assertNotIn("paddle", source.lower())
        self.assertNotIn("LuaAuxLib", source)


if __name__ == "__main__":
    unittest.main()
