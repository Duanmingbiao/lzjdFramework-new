import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class HeroDungeonTests(unittest.TestCase):
    def test_registered_and_ordered(self):
        project = json.loads((ROOT / "project.json").read_text(encoding="utf-8-sig"))
        self.assertIn(17, project["registeredTasks"])
        self.assertIn("common/英雄副本状态.mq", project["modules"])
        self.assertIn("flows/017_英雄副本/英雄副本.mq", project["modules"])

    def test_professional_boundary(self):
        source = (ROOT / "flows/017_英雄副本/英雄副本.mq").read_text(encoding="utf-8-sig")
        self.assertIn('TickCount() - started > 240000', source)
        self.assertIn('恢复，不标完成', source)
        self.assertNotIn('heroDungeonDone = True', source)
        self.assertIn('terminalConfirmed = True', source)

    def test_config_and_foreground_integration(self):
        ui = (ROOT / "ui/最小配置.uip").read_text(encoding="utf-8-sig")
        monitor = (ROOT / "common/前台监控.mq").read_text(encoding="utf-8-sig")
        self.assertIn('名称:"日常_英雄副本"', ui)
        self.assertIn('currentTask = 17 Or currentTask = 18 Or currentTask = 19 Or currentTask = 92', monitor)

    def test_all_professional_patterns_registered(self):
        flow = (ROOT / "flows/017_英雄副本/英雄副本.mq").read_text(encoding="utf-8-sig")
        patterns = (ROOT / "common/图色参数.mq").read_text(encoding="utf-8-sig")
        names = set()
        marker = 'WorldMatch("'
        for part in flow.split(marker)[1:]:
            names.add(part.split('"', 1)[0])
        for name in names:
            self.assertIn(f'Case "{name}"', patterns, name)


if __name__ == "__main__":
    unittest.main()
