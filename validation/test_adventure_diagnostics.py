import re
import unittest
from pathlib import Path
from types import SimpleNamespace
from mq_subset import load

ROOT = Path(__file__).resolve().parents[1]
FLOW = 'flows/018_冒险副本/冒险副本.mq'


class AdventureDiagnosticsTests(unittest.TestCase):
    def fixture(self, write=True):
        clock, logs, shots, matches, taps = [100], [], [], [], []
        files = {}
        def snapshot(path):
            shots.append(path)
            if write:
                files[path] = 1234
        def match(name):
            matches.append(name)
            return name in ('018_新图入口', '018_战斗返回标志')
        def tap(x, y, ms):
            taps.append((x, y, ms))
            clock[0] += ms
            return True
        env = dict(TickCount=lambda: clock[0], WorldLog=logs.append,
                   SnapShot=snapshot, Dir=SimpleNamespace(Exist=lambda p: p in files or p == '/sdcard/Pictures', Create=lambda p: True),
                   File=SimpleNamespace(Bytes=lambda p: files[p]), foundX=277, foundY=403,
                   BusinessExpired=lambda: False, EnterAdventureMode=lambda: 1,
                   WorldStage=lambda s: None, WorldResourcePrompt=lambda: None,
                   WorldMatch=match, WorldOffset=tap, WorldTap=tap,
                   WorldWait=lambda ms: clock.__setitem__(0, clock[0] + ms),
                   RESULT_OK=1, RESULT_TIMEOUT=4, normalAdventureProgressAt=0,
                   terminalConfirmed=False)
        load(['flows/017_英雄副本/英雄副本.mq', FLOW], env)
        return env, logs, shots, matches, taps

    def test_four_recoveries_five_markers_and_original_recognition_order(self):
        env, logs, shots, matches, taps = self.fixture()
        self.assertEqual(env['ExecuteNormalAdventureDungeon'](), 1)
        self.assertEqual(len(shots), 5)
        self.assertEqual(len(set(shots)), 5)
        self.assertEqual(sum('开始防卡' in s for s in logs), 4)
        self.assertIn('原防卡累计4次结束', env['normalAdventureReason'])
        self.assertTrue(env['terminalConfirmed'])
        start = matches.index('018_战斗返回标志')
        self.assertEqual(matches[start:start+14], [
            '018_战斗返回标志', '018_章节推进', '018_地图进度一', '018_地图进度二',
            '018_地图进度三', '018_黄色光环', '018_小怪', '018_首领', '018_需要购买体力',
            '017_开战界面一', '017_开战界面二', '032_少人提示', '012_AutoReady', '012_AutoOff'])
        self.assertTrue(any('018_首领 结果=未命中' in s for s in logs))
        self.assertEqual(sum(t == (100, 1200, 2000) for t in taps), 4)

    def test_snapshot_failure_does_not_change_business_outcome(self):
        env, logs, shots, matches, taps = self.fixture(False)
        self.assertEqual(env['ExecuteNormalAdventureDungeon'](), 1)
        self.assertEqual(len(shots), 5)
        self.assertEqual(sum('截图未确认写入' in s for s in logs), 5)

    def test_snapshot_preserves_anchor_and_does_not_act_or_match(self):
        env, logs, shots, matches, taps = self.fixture()
        env['NormalAdventureReturnSnapshot'](1, 0, 0, False)
        self.assertEqual((env['foundX'], env['foundY']), (277, 403))
        self.assertEqual(matches, [])
        self.assertEqual(taps, [])
        self.assertTrue(any('文件字节=1234' in s for s in logs))

    def test_recognition_wrapper_calls_once_and_returns_original_result(self):
        env, logs, shots, matches, taps = self.fixture()
        self.assertFalse(env['NormalAdventureRecognize']('018_首领', True))
        self.assertEqual(matches, ['018_首领'])
        self.assertEqual(shots, [])

    def test_snapshot_api_is_in_installed_command_catalogue(self):
        catalogue = Path(r'D:\ProgramData\按键精灵\按键精灵手机助手\Doc\command.xml')
        self.assertIn('insertinfo="SnapShot &quot;pic.png&quot;"', catalogue.read_text('gbk'))
        source = (ROOT/FLOW).read_text('utf-8-sig')
        self.assertNotIn('SnapShotEx', source)
        self.assertNotIn('KeepCapture', source)


if __name__ == '__main__':
    unittest.main()
