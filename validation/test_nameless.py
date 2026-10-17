import hashlib
import json
import unittest
from types import SimpleNamespace
from pathlib import Path
from mq_subset import load

ROOT = Path(__file__).resolve().parents[1]
FLOW = 'flows/020_无名星之战/无名星之战.mq'
STATE = 'common/无名星状态.mq'
E = ROOT/'flows/020_无名星之战/evidence'


class NamelessTests(unittest.TestCase):
    def fixture(self, active=(), deadline=120000):
        clock, calls, logs, probes = [0], [], [], []
        env = dict(RESULT_OK=1, RESULT_WAIT=2, RESULT_TIMEOUT=4,
                   currentTask=20, terminalConfirmed=False, namelessDone=False,
                   namelessReason='', businessStarted=0, foundX=100, foundY=200,
                   TickCount=lambda: clock[0], BusinessExpired=lambda: clock[0] > deadline,
                   WorldLog=logs.append, WorldStage=lambda s: None,
                   WorldResourcePrompt=lambda: None, ReturnToHall=lambda: 1,
                   WorldBoolean=lambda k: False, WorldText=lambda *a: '')
        def match(name):
            probes.append((name, clock[0]))
            clock[0] += 10
            return name in active
        def wait(ms):
            calls.append(('wait', ms))
            clock[0] += ms
        def tap(x, y, ms):
            calls.append(('tap', x, y, ms))
            clock[0] += ms
            return not env['BusinessExpired']()
        def offset(x, y, ms):
            calls.append(('offset', x, y, ms))
            clock[0] += ms
            return not env['BusinessExpired']()
        def swipe(*args):
            calls.append(('swipe', *args))
            clock[0] += args[-1]
        env.update(WorldMatch=match, WorldWait=wait, WorldTap=tap, WorldOffset=offset, Swipe=swipe)
        load(['flows/017_英雄副本/英雄副本.mq', STATE, FLOW], env)
        env['WorldPair'] = lambda b: env['WorldMatch'](b+'一') or env['WorldMatch'](b+'二')
        env['NewNamelessSession']()
        return env, clock, calls, logs, probes

    def test_original_checkbox_default_off_and_state_is_independent(self):
        env, *_ = self.fixture()
        keys = []
        env['WorldBoolean'] = lambda k: keys.append(k) or False
        env['LoadNamelessSettings']()
        self.assertEqual(keys, ['日常_无名星之战'])
        self.assertEqual(env['SelectNameless'](), 0)
        env['namelessEnabled'] = True
        self.assertEqual(env['SelectNameless'](), 20)
        env['CommitNamelessTask']()
        self.assertEqual(env['SelectNameless'](), 0)

    def test_ocr_roi_and_exact_branches(self):
        for text in ('', None, ' 报名', '报名\n', '已报名 ', '去战斗', '报 名', '未知'):
            for variant in (False, True):
                with self.subTest(text=text, variant=variant):
                    env, _, calls, _, _ = self.fixture()
                    areas = []
                    env['WorldText'] = lambda *a: areas.append(a) or text
                    self.assertEqual(env['NamelessRegistration'](variant), 2)
                    self.assertEqual(areas, [(301, 1108, 417, 1158)])
                    self.assertEqual(calls, [])
                    self.assertFalse(env['terminalConfirmed'])
                    self.assertFalse(env['namelessDone'])

    def test_exact_enroll_and_battle_clicks(self):
        for text, ms in [('报名', 0), ('战斗', 1000)]:
            env, _, calls, _, _ = self.fixture()
            env['WorldText'] = lambda *a: text
            self.assertEqual(env['NamelessRegistration'](False), 2)
            self.assertEqual(calls, [('tap', 360, 1140, ms)])
            self.assertFalse(env['terminalConfirmed'])

    def test_registered_is_terminal_only_in_second_original_layout(self):
        for variant, result in [(False, 2), (True, 1)]:
            env, _, calls, _, _ = self.fixture()
            env['WorldText'] = lambda *a: '已报名'
            self.assertEqual(env['NamelessRegistration'](variant), result)
            self.assertEqual(env['terminalConfirmed'], variant)
            self.assertEqual(calls, [])

    def test_not_enrolled_is_explicit_original_terminal_without_click(self):
        env, _, calls, _, _ = self.fixture()
        env['WorldText'] = lambda *a: '未报名'
        self.assertEqual(env['NamelessRegistration'](False), 1)
        self.assertTrue(env['terminalConfirmed'])
        self.assertFalse(env['namelessDone'])
        self.assertEqual(calls, [])

    def test_ocr_foreground_interruption_cannot_click_or_finish(self):
        env, _, calls, _, _ = self.fixture()
        interrupted = [False]
        env['BusinessExpired'] = lambda: interrupted[0]
        def text(*args):
            interrupted[0] = True
            return '未报名'
        env['WorldText'] = text
        self.assertEqual(env['NamelessRegistration'](True), 4)
        self.assertFalse(env['terminalConfirmed'])
        self.assertEqual(calls, [])

    def test_navigation_has_target_confirmation_and_original_1500_wait(self):
        env, _, calls, _, _ = self.fixture()
        def match(name):
            return name in ('012_P30', '020_模式入口一') or (bool(calls) and name == '020_入口')
        env['WorldMatch'] = match
        self.assertEqual(env['NamelessEnterMode'](), 1)
        self.assertEqual(calls, [('offset', 0, 0, 1500)])

    def test_unknown_mode_times_out_and_does_not_finish(self):
        env, clock, calls, _, _ = self.fixture(('012_P30',))
        self.assertEqual(env['NamelessEnterMode'](), 4)
        self.assertGreater(clock[0], 62000)
        swipes = [c for c in calls if c[0] == 'swipe']
        self.assertEqual([s[1:5] for s in swipes[:10]], [(150,545,500,545)]*5+[(500,545,150,545)]*5)
        self.assertFalse(env['terminalConfirmed'])

    def test_failed_mode_entry_prevents_business_recognition(self):
        env, *_ = self.fixture()
        env['NamelessEnterMode'] = lambda: 4
        env['WorldMatch'] = lambda n: self.fail('business recognition after navigation failure')
        self.assertEqual(env['ExecuteNamelessBattle'](), 4)

    def test_original_recognition_terminal_exits(self):
        for name in ('活动未开', '初赛结束', '非赛期', '赛季结束一', '赛季未开二'):
            env, _, calls, _, _ = self.fixture(('020_'+name,))
            env['NamelessEnterMode'] = lambda: 1
            self.assertEqual(env['ExecuteNamelessBattle'](), 1)
            self.assertTrue(env['terminalConfirmed'])
            self.assertFalse(env['namelessDone'])
            self.assertEqual(calls, [])

    def test_unknown_registration_does_not_click_or_mark_complete(self):
        env, _, calls, _, _ = self.fixture(('020_报名界面一',), deadline=1000)
        env['NamelessEnterMode'] = lambda: 1
        self.assertEqual(env['ExecuteNamelessBattle'](), 4)
        self.assertEqual(calls, [])
        self.assertFalse(env['terminalConfirmed'])

    def test_auto_off_click_reset_before_original_wait_then_independent_on_check(self):
        env, clock, calls, _, probes = self.fixture()
        env['WorldMatch'] = lambda n: n == ('020_自动已选一' if calls else '020_自动未选一')
        self.assertEqual(env['NamelessEnableAuto'](), 1)
        self.assertEqual(calls, [('offset', 0, 0, 0), ('wait', 1000)])

    def test_fifteen_switches_not_fifteen_recognition_hits(self):
        env, _, calls, logs, probes = self.fixture(('020_挑战过一','020_切换对手一','020_无奖励红点'))
        self.assertEqual(env['NamelessOpponents'](), 1)
        self.assertEqual(sum(c == ('offset',0,0,2000) for c in calls), 15)
        self.assertEqual(sum('原切换对手累计=' in s for s in logs), 15)
        self.assertIn('没有红点', env['namelessReason'])
        self.assertFalse(env['namelessDone'])

    def test_stone_branch_never_buys_or_clicks_challenge(self):
        env, _, calls, _, _ = self.fixture(('020_需要石头一','020_切换对手一','020_无奖励红点'))
        self.assertEqual(env['NamelessOpponents'](), 1)
        self.assertTrue(all(c in [('wait',1000),('wait',50),('offset',0,0,2000)] for c in calls))

    def test_no_action_switch_probe_starts_only_after_fifteen_seconds(self):
        env, _, _, _, probes = self.fixture(('020_切换对手一',), deadline=18000)
        self.assertEqual(env['NamelessOpponents'](), 4)
        checks = [at for n,at in probes if n.startswith('020_切换对手')]
        self.assertTrue(checks)
        self.assertGreater(checks[0], 15000)
        self.assertFalse(env['terminalConfirmed'])

    def test_challenge_wait_is_before_click_and_check_order_is_independent(self):
        env, _, calls, _, probes = self.fixture(('020_可挑战一',), deadline=1200)
        self.assertEqual(env['NamelessOpponents'](), 4)
        self.assertEqual(calls[:2], [('wait',1000),('offset',0,0,0)])
        self.assertEqual([n for n,_ in probes[:7]], ['020_可挑战一','020_挑战过一','020_挑战过二','020_需要石头一','020_需要石头二','020_挑战失败一','020_挑战失败二'])

    def test_result_clicks_do_not_finish_whole_task(self):
        for name in ('020_挑战失败一','020_挑战成功一'):
            env, _, calls, _, _ = self.fixture((name,), deadline=1200)
            self.assertEqual(env['NamelessOpponents'](), 4)
            self.assertFalse(env['terminalConfirmed'])
            self.assertFalse(env['namelessDone'])
            self.assertIn(('offset',0,0,0), calls)

    def test_reward_order_offsets_and_confirmed_exit(self):
        active = ('020_打开奖励','020_可领取','020_恭喜获得','020_已领取')
        env, _, calls, _, probes = self.fixture(active)
        self.assertEqual(env['NamelessRewards'](0), 1)
        self.assertEqual(calls, [('offset',360,-1074,0),('offset',252,-141,0),('offset',0,0,0)])
        self.assertEqual([n for n,_ in probes], ['020_无奖励红点',*active])
        self.assertTrue(env['terminalConfirmed'])

    def test_reward_unknown_fifteen_seconds_cannot_succeed(self):
        env, clock, calls, _, _ = self.fixture()
        self.assertEqual(env['NamelessRewards'](0), 4)
        self.assertGreater(clock[0],15000)
        self.assertLess(clock[0],15100)
        self.assertEqual(calls, [])
        self.assertFalse(env['terminalConfirmed'])

    def test_reward_actions_do_not_extend_original_stage_timer(self):
        env, clock, _, _, _ = self.fixture(('020_打开奖励',))
        self.assertEqual(env['NamelessRewards'](0), 4)
        self.assertLess(clock[0],15100)
        self.assertFalse(env['terminalConfirmed'])

    def test_recovery_preserves_pending_task_and_not_done(self):
        env, *_ = self.fixture()
        env['RecoverNamelessTask']()
        env['RestartNamelessTask']()
        self.assertEqual(env['namelessRecoveries'], 1)
        self.assertEqual(env['namelessRestarts'], 1)
        self.assertFalse(env['namelessDone'])
        self.assertFalse(env['terminalConfirmed'])

    def test_all_37_exact_patterns_registered_and_original_33_constants_preserved(self):
        records = json.loads((E/'图色转换.json').read_text('utf8'))
        proto = json.loads((E/'原型639.json').read_text('utf8'))
        catalogue = {r['name']: r for r in json.loads((ROOT/'evidence/图色参数.json').read_text('utf8'))}
        mq = (ROOT/'common/图色参数.mq').read_text('utf-8-sig')
        self.assertEqual(len(records),37)
        self.assertEqual(len(proto['code']),1369)
        for r in records:
            self.assertEqual(catalogue[r['name']], r)
            line = mq.split('Case "'+r['name']+'"',1)[1].splitlines()[1].strip()
            raw = line.removeprefix('FindMultiColor ').removesuffix(',foundX,foundY')
            self.assertEqual(json.loads('['+raw+']'), r['definition'])
            if 'constantIndices' in r:
                b,o = r['constantIndices']
                self.assertEqual(r['definition'][4:6], [proto['constants'][b], proto['constants'][o]])

    def test_public_commit_requires_terminal_hall_and_foreground_gate(self):
        env, *_ = self.fixture()
        env['Note'] = lambda s: None
        load(['common/任务状态.mq'], env)
        self.assertFalse(env['CommitTask'](True))
        env['terminalConfirmed'] = True
        self.assertFalse(env['CommitTask'](False))
        env['BeginForegroundCommit'] = lambda: False
        self.assertFalse(env['CommitTask'](True))
        self.assertFalse(env['namelessDone'])
        env['BeginForegroundCommit'] = lambda: True
        self.assertTrue(env['CommitTask'](True))
        self.assertTrue(env['namelessDone'])
        self.assertEqual(env['resumeTask'], 0)

    def test_foreground_recovery_keeps_task20_pending(self):
        env, *_ = self.fixture()
        env['Note'] = lambda s: None
        env['Thread'] = SimpleNamespace(GetShareVar=lambda k: 'outside')
        load(['common/任务状态.mq','common/前台监控.mq','common/任务注册.mq'], env)
        env['ForegroundInterrupted'] = lambda: True
        restarts = []
        env['RestartGame'] = lambda: restarts.append(20)
        self.assertTrue(env['HandleForegroundRecovery']())
        self.assertEqual(env['resumeTask'], 20)
        self.assertEqual(env['SelectDueTask'](), 20)
        self.assertFalse(env['namelessDone'])
        self.assertFalse(env['terminalConfirmed'])
        self.assertEqual(env['namelessRecoveries'], 1)
        self.assertEqual(restarts,[20])

    def test_ui_and_manifest_only_this_module_added(self):
        ui = (ROOT/'ui/最小配置.uip').read_text('utf-8-sig')
        self.assertIn('名称:"日常_无名星之战",提示内容:"无名星之战",选中:false',ui)
        self.assertIn('名称:"日常_联盟组队战",提示内容:"联盟组队战[",选中:false',ui)
        config = json.loads((ROOT/'project.json').read_text('utf8'))
        self.assertIn(20,config['registeredTasks'])
        self.assertIn(FLOW,config['modules'])
        self.assertIn(STATE,config['modules'])

    def test_existing_build_assistant_and_sync_records_unchanged(self):
        baseline = json.loads((E/'未同步基线.json').read_text('utf8'))
        for name, expected in baseline.items():
            self.assertEqual(hashlib.sha256(Path(name).read_bytes()).hexdigest(), expected, name)


if __name__ == '__main__':
    unittest.main()
