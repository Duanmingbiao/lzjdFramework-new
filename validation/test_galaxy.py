import hashlib
import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from mq_subset import load

ROOT = Path(__file__).resolve().parents[1]
FLOW = 'flows/021_跨银河大赛/跨银河大赛.mq'
STATE = 'common/跨银河状态.mq'
E = ROOT/'flows/021_跨银河大赛/evidence'


class GalaxyTests(unittest.TestCase):
    def fixture(self, active=(), deadline=120000):
        clock, calls, probes, logs = [0], [], [], []
        env = dict(RESULT_OK=1, RESULT_WAIT=2, RESULT_FAIL=3, RESULT_TIMEOUT=4,
                   currentTask=21, resumeTask=21, terminalConfirmed=False,
                   businessStarted=0, foundX=100, foundY=200,
                   Time=lambda: 1700000000+clock[0]//1000,
                   TickCount=lambda: clock[0], BusinessExpired=lambda: clock[0] > deadline,
                   WorldBoolean=lambda k: False, WorldNumber=lambda k,d,u: d,
                   WorldLog=logs.append, Note=logs.append, WorldStage=lambda s: None,
                   WorldResourcePrompt=lambda: None, ReturnToHall=lambda: 1,
                   WorldText=lambda *a: self.fail('cross galaxy must not invoke OCR'))
        def match(name):
            probes.append((name, clock[0]))
            clock[0] += 10
            return name in active
        def wait(ms):
            calls.append(('wait',ms))
            clock[0] += ms
        def tap(x,y,ms):
            calls.append(('tap',x,y,ms))
            clock[0] += ms
            return not env['BusinessExpired']()
        def offset(x,y,ms):
            calls.append(('offset',x,y,ms))
            clock[0] += ms
            return not env['BusinessExpired']()
        env.update(WorldMatch=match, WorldWait=wait, WorldTap=tap, WorldOffset=offset)
        load(['flows/017_英雄副本/英雄副本.mq','flows/020_无名星之战/无名星之战.mq',STATE,FLOW],env)
        env['WorldPair'] = lambda b: env['WorldMatch'](b+'一') or env['WorldMatch'](b+'二')
        env['NewGalaxySession']()
        env.update(galaxyEnabled=True, galaxyEnroll=False, galaxyRegion=0)
        return env, clock, calls, probes, logs

    def test_original_three_configuration_keys_and_defaults(self):
        env, *_ = self.fixture()
        keys = []
        env['WorldBoolean'] = lambda k: keys.append(k) or False
        env['WorldNumber'] = lambda k,d,u: keys.append((k,d,u)) or d
        env['LoadGalaxySettings']()
        self.assertEqual(keys,['日常_跨银河大赛','日常_跨银河大赛_报名',('日常_跨银河大赛_报名赛区',0,3)])
        self.assertFalse(env['galaxyEnabled'])
        self.assertFalse(env['galaxyEnroll'])
        self.assertEqual(env['galaxyRegion'],0)
        self.assertEqual(env['SelectGalaxy'](),0)

    def test_failed_mode_navigation_blocks_all_business(self):
        env, _, calls, probes, _ = self.fixture()
        env['NamelessEnterMode'] = lambda: 4
        self.assertEqual(env['ExecuteGalaxyBattle'](),4)
        self.assertEqual(calls,[])
        self.assertEqual(probes,[])

    def test_shared_dimensional_navigation_does_not_change_task20_state(self):
        env, *_ = self.fixture(('020_入口','021_活动未开'))
        env.update(namelessDone=True,namelessReason='preserved')
        self.assertEqual(env['ExecuteGalaxyBattle'](),1)
        self.assertTrue(env['namelessDone'])
        self.assertEqual(env['namelessReason'],'preserved')

    def test_original_entry_terminal_templates(self):
        for name in ['021_活动未开','021_未报名一','021_决赛阶段二','021_未开赛二']:
            env, _, calls, _, _ = self.fixture((name,))
            env['NamelessEnterMode'] = lambda: 1
            self.assertEqual(env['ExecuteGalaxyBattle'](),1)
            self.assertTrue(env['terminalConfirmed'])
            self.assertFalse(env['galaxyDone'])
            self.assertEqual(calls,[])

    def test_entry_checks_are_ordered_and_challenge_wait_is_200_not_1000(self):
        env, _, calls, probes, _ = self.fixture(('021_挑战按钮一','021_战斗准备一'))
        env['NamelessEnterMode'] = lambda: 1
        env['GalaxyPrepare'] = lambda: 4
        self.assertEqual(env['ExecuteGalaxyBattle'](),4)
        self.assertEqual(calls,[('wait',50),('offset',0,0,200)])
        self.assertEqual([n for n,_ in probes],['021_活动未开','021_入口一','021_入口二','021_未报名一','021_未报名二','021_决赛阶段一','021_决赛阶段二','021_未开赛一','021_未开赛二','021_挑战按钮一','021_战斗准备一'])

    def test_enrollment_disabled_is_explicit_exit_only_after_stage_match(self):
        env, _, calls, _, _ = self.fixture(('021_报名阶段一',))
        self.assertEqual(env['GalaxyPrepare'](),1)
        self.assertTrue(env['terminalConfirmed'])
        self.assertIn('未选择自动报名',env['galaxyReason'])
        self.assertEqual(calls,[])
        env, _, calls, _, _ = self.fixture()
        self.assertEqual(env['GalaxySignup'](),4)
        self.assertFalse(env['terminalConfirmed'])
        self.assertEqual(calls,[])

    def test_enrollment_enabled_selects_signup_without_completing(self):
        env, *_ = self.fixture(('021_报名阶段二',))
        env['galaxyEnroll'] = True
        self.assertEqual(env['GalaxyPrepare'](),2)
        self.assertFalse(env['terminalConfirmed'])

    def test_prepare_known_terminal_exits(self):
        for name in ['021_已报名二','021_决赛阶段一','021_本届结束一']:
            env, *_ = self.fixture((name,))
            self.assertEqual(env['GalaxyPrepare'](),1)
            self.assertTrue(env['terminalConfirmed'])

    def test_auto_off_click_reset_then_wait_and_independent_auto_on_check(self):
        env, _, calls, probes, _ = self.fixture(('021_自动未选一','021_自动已选二'))
        self.assertEqual(env['GalaxyPrepare'](),1)
        self.assertEqual(calls,[('offset',0,0,0),('wait',1000)])
        self.assertFalse(env['terminalConfirmed'])
        self.assertLess([n for n,_ in probes].index('021_自动未选一'),[n for n,_ in probes].index('021_自动已选一'))

    def test_prepare_local_15seconds_is_not_extended_by_challenge_clicks(self):
        env, clock, calls, _, _ = self.fixture(('021_挑战按钮一',))
        self.assertEqual(env['GalaxyPrepare'](),4)
        self.assertGreater(clock[0],15000)
        self.assertLess(clock[0],17000)
        self.assertTrue(calls)
        self.assertFalse(env['terminalConfirmed'])

    def test_unknown_prepare_has_no_click_or_completion(self):
        env, clock, calls, _, _ = self.fixture()
        self.assertEqual(env['GalaxyPrepare'](),4)
        self.assertGreater(clock[0],15000)
        self.assertEqual(calls,[])
        self.assertFalse(env['terminalConfirmed'])

    def test_four_original_signup_region_offsets_and_independent_order(self):
        active = ('021_报名阶段一','021_报名按钮一','021_报名确认一','021_已报名一')
        for region,delta in enumerate([(270,-210),(0,0),(-150,-210),(70,-480)]):
            env, _, calls, probes, _ = self.fixture(active)
            env.update(galaxyEnroll=True,galaxyRegion=region)
            self.assertEqual(env['GalaxySignup'](),1)
            self.assertEqual(calls,[('offset',*delta,0),('wait',2000),('wait',50),('offset',0,0,1000),('wait',50),('offset',0,0,1000),('wait',50),('wait',1000)])
            self.assertEqual([n for n,_ in probes],list(active))
            self.assertTrue(env['terminalConfirmed'])
            self.assertFalse(env['galaxyDone'])

    def test_signup_unknown_only_original_50ms_waits_and_no_completion(self):
        env, _, calls, _, _ = self.fixture(deadline=1000)
        env['galaxyEnroll'] = True
        self.assertEqual(env['GalaxySignup'](),4)
        self.assertTrue(all(c==('wait',50) for c in calls))
        self.assertFalse(env['terminalConfirmed'])

    def test_battle_unknown_exits_phase_only_after_strict_8seconds(self):
        env, clock, calls, _, _ = self.fixture()
        self.assertEqual(env['GalaxyFight'](),1)
        self.assertGreater(clock[0],8000)
        self.assertLess(clock[0],8100)
        self.assertEqual(calls,[])
        self.assertFalse(env['terminalConfirmed'])
        self.assertFalse(env['galaxyDone'])
        self.assertFalse(env['galaxyDeferred'])

    def test_battle_five_checks_are_independent_and_ordered(self):
        active = ('021_玩家列表','021_玩家挑战左','021_玩家挑战右','021_挑战失败','021_挑战成功一')
        env, _, calls, probes, _ = self.fixture(active,deadline=5100)
        self.assertEqual(env['GalaxyFight'](),4)
        self.assertEqual([n for n,_ in probes[:5]],list(active))
        self.assertEqual(calls[:7],[('tap',655,415,1000),('offset',0,0,1000),('offset',0,0,1000),('wait',1000),('offset',0,0,0),('wait',1000),('offset',0,0,0)])
        self.assertFalse(env['terminalConfirmed'])

    def test_sixteenth_action_not_fifteenth_defers_exactly_one_hour(self):
        env, _, calls, _, _ = self.fixture(('021_玩家挑战左',))
        self.assertEqual(env['GalaxyFight'](),2)
        self.assertEqual(len(calls),16)
        self.assertEqual(calls,[('offset',0,0,1000)]*16)
        self.assertEqual(env['galaxyRetryAt'],env['Time']()+3600)
        self.assertTrue(env['galaxyDeferred'])
        self.assertFalse(env['terminalConfirmed'])
        self.assertFalse(env['galaxyDone'])

    def test_deferred_event_does_not_reenter_mode_on_recovery(self):
        env, _, calls, probes, _ = self.fixture()
        env.update(galaxyDeferred=True,galaxyRetryAt=1700003600)
        env['RecoverGalaxyTask']()
        env['StartGalaxyTask']()
        env['NamelessEnterMode'] = lambda: self.fail('must preserve pending deferred event')
        self.assertEqual(env['ExecuteGalaxyBattle'](),2)
        self.assertEqual(env['galaxyRetryAt'],1700003600)
        self.assertTrue(env['galaxyDeferred'])
        self.assertEqual(calls,[])
        self.assertEqual(probes,[])

    def test_retry_cleanup_requires_hall_and_foreground_and_does_not_finish(self):
        env, clock, *_ = self.fixture()
        env.update(galaxyDeferred=True,galaxyRetryAt=1700003600)
        self.assertFalse(env['ScheduleGalaxyRetry'](False))
        env['BeginForegroundCommit'] = lambda: False
        self.assertFalse(env['ScheduleGalaxyRetry'](True))
        self.assertTrue(env['galaxyDeferred'])
        env['BeginForegroundCommit'] = lambda: True
        self.assertTrue(env['ScheduleGalaxyRetry'](True))
        self.assertEqual(env['resumeTask'],0)
        self.assertEqual(env['currentTask'],0)
        self.assertFalse(env['galaxyDone'])
        self.assertEqual(env['SelectGalaxy'](),0)
        clock[0] = 3599999
        self.assertEqual(env['SelectGalaxy'](),0)
        clock[0] = 3600000
        self.assertEqual(env['SelectGalaxy'](),21)

    def test_return_inherits_battle_time_and_mail_requires_gray_confirmation(self):
        env, clock, calls, probes, _ = self.fixture(('021_邮件已领取',))
        env['galaxyActionAt'] = -8001
        self.assertEqual(env['GalaxyReturnAndMail'](),1)
        self.assertLess(clock[0],100)
        self.assertEqual([n for n,_ in probes],['021_自动已选一','021_挑战按钮一','021_挑战按钮一','021_邮件可领取','021_邮件已领取'])
        self.assertEqual(calls,[('offset',293,-840,0)])
        self.assertTrue(env['terminalConfirmed'])

    def test_return_and_mail_do_not_broaden_to_second_variants(self):
        env, _, calls, probes, _ = self.fixture(('021_自动已选二','021_挑战按钮二'),deadline=6000)
        self.assertEqual(env['GalaxyReturnAndMail'](),4)
        self.assertEqual(calls,[])
        self.assertNotIn('021_自动已选二',[n for n,_ in probes])
        self.assertNotIn('021_挑战按钮二',[n for n,_ in probes])

    def test_mail_open_claim_gray_offsets_and_order(self):
        env, _, calls, probes, _ = self.fixture(('021_挑战按钮一','021_邮件可领取','021_邮件已领取','021_恭喜获得'))
        self.assertEqual(env['GalaxyReturnAndMail'](),1)
        self.assertEqual(calls,[('offset',166,-1021,500),('offset',0,0,0),('offset',293,-840,0)])
        self.assertNotIn('021_恭喜获得',[n for n,_ in probes])

    def test_reward_popup_alone_is_not_task_completion(self):
        env, _, calls, _, _ = self.fixture(('021_恭喜获得',),deadline=1000)
        env['galaxyActionAt'] = -8001
        self.assertEqual(env['GalaxyReturnAndMail'](),4)
        self.assertTrue(calls)
        self.assertFalse(env['terminalConfirmed'])

    def test_public_commit_terminal_hall_and_foreground_gates(self):
        env, *_ = self.fixture()
        load(['common/任务状态.mq'],env)
        self.assertFalse(env['CommitTask'](True))
        env['terminalConfirmed'] = True
        self.assertFalse(env['CommitTask'](False))
        env['BeginForegroundCommit'] = lambda: False
        self.assertFalse(env['CommitTask'](True))
        env['BeginForegroundCommit'] = lambda: True
        self.assertTrue(env['CommitTask'](True))
        self.assertTrue(env['galaxyDone'])
        self.assertEqual(env['resumeTask'],0)

    def test_public_scheduler_handles_defer_before_generic_wait_redispatch(self):
        env, _, _, _, _ = self.fixture()
        load(['common/任务调度.mq'],env)
        events = []
        env.update(SelectDueTask=lambda:21, SaveCurrentTask=lambda t:None,
                   EnsureGameHall=lambda:1, HandleForegroundRecovery=lambda:False,
                   ReturnToHall=lambda: events.append('hall') or 1,
                   RestartGame=lambda:events.append('restart'))
        def dispatch(task):
            self.assertEqual(task,21)
            env.update(galaxyDeferred=True,galaxyRetryAt=1700003600)
            events.append('dispatch')
            return 2
        env['DispatchTask'] = dispatch
        env['SchedulerStep']()
        self.assertEqual(events,['dispatch','hall','restart'])
        self.assertFalse(env['galaxyDone'])
        self.assertEqual(env['galaxyDue'],1700003600)
        self.assertEqual(env['resumeTask'],0)

    def test_foreground_recovery_preserves_task21_and_deferred_time(self):
        env, *_ = self.fixture()
        env['Thread'] = SimpleNamespace(GetShareVar=lambda k:'outside')
        load(['common/前台监控.mq','common/任务状态.mq','common/任务注册.mq'],env)
        env['ForegroundInterrupted'] = lambda: True
        env['RestartGame'] = lambda:None
        env.update(galaxyDeferred=True,galaxyRetryAt=1700003600)
        self.assertTrue(env['HandleForegroundRecovery']())
        self.assertEqual(env['resumeTask'],21)
        self.assertEqual(env['SelectDueTask'](),21)
        self.assertTrue(env['galaxyDeferred'])
        self.assertEqual(env['galaxyRetryAt'],1700003600)
        self.assertFalse(env['galaxyDone'])

    def test_business_interrupt_has_no_click_or_completion(self):
        for fn,args in [('GalaxyPrepare',()),('GalaxyFight',()),('GalaxyReturnAndMail',()),('GalaxySignup',())]:
            env, _, calls, _, _ = self.fixture()
            env['galaxyEnroll'] = True
            env['BusinessExpired'] = lambda:True
            self.assertEqual(env[fn](*args),4)
            self.assertEqual(calls,[])
            self.assertFalse(env['terminalConfirmed'])

    def test_36_patterns_exact_and_left_right_regions_not_full_screen(self):
        records = json.loads((E/'图色转换.json').read_text('utf8'))
        proto = json.loads((E/'原型640.json').read_text('utf8'))
        catalogue = {r['name']:r for r in json.loads((ROOT/'evidence/图色参数.json').read_text('utf8'))}
        mq = (ROOT/'common/图色参数.mq').read_text('utf-8-sig')
        self.assertEqual(len(records),36)
        self.assertEqual(len(proto['code']),1914)
        for r in records:
            b,o = r['constantIndices']
            self.assertEqual(r['definition'][4:6],[proto['constants'][b],proto['constants'][o]])
            self.assertEqual(catalogue[r['name']],r)
            line = mq.split('Case "'+r['name']+'"',1)[1].splitlines()[1].strip()
            self.assertEqual(json.loads('['+line.removeprefix('FindMultiColor ').removesuffix(',foundX,foundY')+']'),r['definition'])
        self.assertEqual(catalogue['021_玩家挑战左']['definition'][:4],[0,238,172,1053])
        self.assertEqual(catalogue['021_玩家挑战右']['definition'][:4],[550,246,717,1024])

    def test_old_198_controls_preserved_and_original_three_galaxy_controls(self):
        import sys
        sys.path.insert(0,str(ROOT/'tools'))
        from check_ui import inspect
        project = json.loads((ROOT/'project.json').read_text('utf8'))
        source = '\n'.join((ROOT/p).read_text('utf-8-sig') for p in [project['entry'],*project['modules']])
        controls = inspect((ROOT/'ui/最小配置.uip').read_text('utf-8-sig'),source)
        old = json.loads((E/'原配置基线.json').read_text('utf8'))
        self.assertEqual(len(old),198)
        for name,(kind,props) in old.items():
            self.assertEqual(controls[name],(kind,props))
        added = {n for n in set(controls)-set(old) if n.startswith('日常_跨银河大赛')}
        self.assertEqual(added,{'日常_跨银河大赛','日常_跨银河大赛_报名','日常_跨银河大赛_报名赛区'})
        self.assertEqual(controls['日常_跨银河大赛'][1]['选中'],False)
        self.assertEqual(controls['日常_跨银河大赛_报名'][1]['选中'],False)
        self.assertEqual(controls['日常_跨银河大赛_报名赛区'][1]['选项'],['东赛区','南赛区','西赛区','北赛区'])
        self.assertEqual(controls['日常_跨银河大赛_报名赛区'][1]['初始选项'],0)
        self.assertIn(FLOW,project['modules'])
        self.assertIn(STATE,project['modules'])
        self.assertIn(21,project['registeredTasks'])

    def test_no_ocr_new_engine_private_apis_or_business_restart(self):
        source = (ROOT/FLOW).read_text('utf-8-sig')
        for name in ['WorldText(', 'Image.OcrText', 'LuaAuxLib','OCREX','KillApp','RunApp','RestartGame(','CommitTask(']:
            self.assertNotIn(name,source)

    def test_no_assistant_build_or_sync_record_mutation(self):
        baseline = json.loads((E/'未同步基线.json').read_text('utf8'))
        for name,digest in baseline.items():
            self.assertEqual(hashlib.sha256(Path(name).read_bytes()).hexdigest(),digest,name)


if __name__ == '__main__':
    unittest.main()
