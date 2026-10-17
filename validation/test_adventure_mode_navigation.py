import unittest
from mq_subset import load


class AdventureNavigationTests(unittest.TestCase):
    def fixture(self, task=18):
        clock = [0]
        calls = []
        def wait(ms):
            clock[0] += ms
        def offset(x, y, ms):
            calls.append(('offset', x, y, ms))
            wait(ms)
            return True
        def swipe(*args):
            calls.append(('swipe', *args))
            wait(args[-1])
        env = {'TickCount': lambda: clock[0], 'BusinessExpired': lambda: False,
               'WorldWait': wait, 'WorldOffset': offset, 'WorldTap': offset,
               'WorldStage': lambda s: None, 'WorldLog': lambda s: None,
               'WorldResourcePrompt': lambda: None, 'ReturnToHall': lambda: 1,
               'WorldMatch': lambda name: False, 'Swipe': swipe,
               'RESULT_OK': 1, 'RESULT_WAIT': 2, 'RESULT_TIMEOUT': 4,
               'currentTask': task, 'terminalConfirmed': False,
               'powerTournamentQuickJoin': False, 'powerTournamentBuyRuntime': False}
        load(['common/冒险入口.mq', 'flows/017_英雄副本/英雄副本.mq',
              'flows/018_冒险副本/冒险副本.mq', 'flows/019_力之大会/力之大会.mq'], env)
        return env, clock, calls

    def test_shared_entry_waits_for_target_confirmation_and_extra_tournament_delay(self):
        for task, expected in [(18, 1020), (19, 4020)]:
            env, clock, calls = self.fixture(task)
            def match(name):
                return name in ('012_P30', '冒险_模式入口') or (bool(calls) and name == '018_新图入口')
            env['WorldMatch'] = match
            self.assertEqual(env['EnterAdventureMode'](), 1)
            self.assertEqual(calls, [('offset', 0, 0, 1000)])
            self.assertEqual(clock[0], expected)

    def test_unknown_navigation_alternates_five_swipes_and_does_not_complete(self):
        env, clock, calls = self.fixture()
        env['WorldMatch'] = lambda name: name == '012_P30'
        self.assertEqual(env['EnterAdventureMode'](), 4)
        self.assertEqual([row[1:5] for row in calls[:10]],
                         [(150, 545, 500, 545)] * 5 + [(500, 545, 150, 545)] * 5)
        self.assertGreater(clock[0], 62000)
        self.assertFalse(env['terminalConfirmed'])

    def test_failed_navigation_blocks_both_business_flows(self):
        for task, function in [(18, 'ExecuteNormalAdventureDungeon'), (19, 'ExecutePowerTournament')]:
            env, clock, calls = self.fixture(task)
            env['EnterAdventureMode'] = lambda: 4
            env['WorldMatch'] = lambda name: self.fail('Business recognition before successful navigation')
            self.assertEqual(env[function](), 4)
            self.assertEqual(calls, [])

    def test_foreground_interrupt_prevents_navigation_clicks(self):
        env, clock, calls = self.fixture()
        env['BusinessExpired'] = lambda: True
        self.assertEqual(env['EnterAdventureMode'](), 4)
        self.assertEqual(calls, [])

    def test_tournament_repeated_entry_hits_do_not_extend_ten_seconds(self):
        env, clock, calls = self.fixture(19)
        env['WorldMatch'] = lambda name: name == '019_入口彩色'
        self.assertEqual(env['PowerTournamentEnter'](), 4)
        self.assertGreater(clock[0], 10000)
        self.assertLess(clock[0], 11000)
        self.assertFalse(env['terminalConfirmed'])

    def test_tournament_unknown_battle_has_no_speculative_top_taps(self):
        env, clock, calls = self.fixture(19)
        self.assertEqual(env['PowerTournamentBattle'](), 4)
        self.assertGreater(clock[0], 60000)
        self.assertEqual(calls, [])
        self.assertFalse(env['terminalConfirmed'])

    def test_tournament_skip_uses_original_battle_anchor_before_gray_terminal(self):
        env, clock, calls = self.fixture(19)
        env['WorldMatch'] = lambda name: name == '012_BattleBase' or (bool(calls) and name == '019_终态灰色')
        self.assertEqual(env['PowerTournamentBattle'](), 1)
        self.assertEqual(calls, [('offset', -310, 93, 50)])
        self.assertTrue(env['terminalConfirmed'])

    def test_quick_join_disabled_is_explicit_exit_without_join_or_purchase(self):
        env, clock, calls = self.fixture(19)
        env['WorldMatch'] = lambda name: name == '019_加入界面'
        self.assertEqual(env['PowerTournamentEnter'](), 1)
        self.assertTrue(env['terminalConfirmed'])
        self.assertEqual(calls, [])

    def test_purchase_returns_to_wait_without_buying_twice(self):
        env, clock, calls = self.fixture(19)
        env['powerTournamentBuyRuntime'] = True
        env['WorldMatch'] = lambda name: (name == '019_等待界面' and len(calls) >= 5) or name == '019_购买界面'
        self.assertEqual(env['PowerTournamentPurchase'](), 2)
        self.assertEqual(calls[:4], [('offset', -285, 145, 200)] * 4)
        self.assertEqual(calls[4:], [('offset', -310, 324, 1000)])
        self.assertFalse(env['powerTournamentBuyRuntime'])
        self.assertEqual(env['PowerTournamentPurchase'](), 2)
        self.assertEqual(len(calls), 5)

    def test_adventure_unknown_forty_seconds_remains_recovery(self):
        env, clock, calls = self.fixture(18)
        env['EnterAdventureMode'] = lambda: 1
        self.assertEqual(env['ExecuteNormalAdventureDungeon'](), 4)
        self.assertGreater(clock[0], 40000)
        self.assertFalse(env['terminalConfirmed'])


if __name__ == '__main__':
    unittest.main()
