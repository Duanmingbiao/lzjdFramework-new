import unittest
from mq_subset import load


class HeroRuntimeBoundary(unittest.TestCase):
    def fixture(self):
        clock = [0]
        taps = []
        env = {'TickCount': lambda: clock[0], 'BusinessExpired': lambda: False,
               'WorldWait': lambda ms: clock.__setitem__(0, clock[0] + ms),
               'WorldStage': lambda s: None, 'WorldLog': lambda s: None,
               'WorldResourcePrompt': lambda: None, 'WorldMatch': lambda name: False,
               'WorldOffset': lambda x, y, ms: taps.append((x, y, ms)) or True,
               'RESULT_OK': 1, 'RESULT_TIMEOUT': 4, 'terminalConfirmed': False}
        load(['flows/017_英雄副本/英雄副本.mq'], env)
        env['HeroEnter'] = lambda: 1
        env['HeroAutoTriple'] = lambda: False
        return env, clock, taps

    def test_unknown_waits_past_120_until_strict_240_then_recovers(self):
        env, clock, taps = self.fixture()
        self.assertEqual(env['ExecuteHeroDungeon'](), 4)
        self.assertEqual(clock[0], 240100)
        self.assertFalse(env['terminalConfirmed'])
        self.assertFalse(env['heroDungeonRunning'])
        self.assertEqual(taps, [])

    def test_page_judgement_does_not_click_its_anchor(self):
        env, clock, taps = self.fixture()
        env['WorldMatch'] = lambda name: name == '017_英雄选择判断'
        self.assertEqual(env['ExecuteHeroDungeon'](), 4)
        self.assertEqual(taps, [])

    def test_two_and_three_are_independent_before_purchase_exit(self):
        env, clock, taps = self.fixture()
        seen = []
        def match(name):
            seen.append(name)
            return name in ('017_英雄选择判断', '017_点击两个英雄', '017_点击三个英雄', '017_购买体力')
        env['WorldMatch'] = match
        self.assertEqual(env['ExecuteHeroDungeon'](), 1)
        self.assertEqual(taps, [(0, 0, 500), (0, 0, 500)])
        self.assertLess(seen.index('017_点击两个英雄'), seen.index('017_点击三个英雄'))
        self.assertTrue(env['terminalConfirmed'])

    def test_foreground_and_public_timer_scope(self):
        env = {'currentTask': 17, 'heroDungeonRunning': True,
               'TickCount': lambda: 120001, 'businessStarted': 0,
               'businessLimit': 120000, 'ForegroundInterrupted': lambda: False}
        load(['common/运行计时.mq'], env)
        self.assertFalse(env['BusinessExpired']())
        env['ForegroundInterrupted'] = lambda: True
        self.assertTrue(env['BusinessExpired']())
        env['ForegroundInterrupted'] = lambda: False
        env['heroDungeonRunning'] = False
        self.assertTrue(env['BusinessExpired']())

    def test_entry_prioritizes_already_inside_without_clicking(self):
        env, clock, taps = self.fixture()
        load(['flows/017_英雄副本/英雄副本.mq'], env)
        env['WorldMatch'] = lambda name: name in ('017_已经在英雄副本一', '017_英雄入口一')
        self.assertEqual(env['HeroEnter'](), 1)
        self.assertEqual(taps, [])


if __name__ == '__main__':
    unittest.main()
