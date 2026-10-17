import hashlib
import json
import unittest
from pathlib import Path
from mq_subset import load

ROOT = Path(__file__).resolve().parents[1]
STATE = 'common/恐惧森林状态.mq'
FLOW = 'flows/022_恐惧森林/恐惧森林.mq'
E = ROOT/'flows/022_恐惧森林/evidence'


class ForestTests(unittest.TestCase):
    def fixture(self, active=(), deadline=300000):
        clock, calls, probes, logs = [100], [], [], []
        env = dict(RESULT_OK=1,RESULT_WAIT=2,RESULT_FAIL=3,RESULT_TIMEOUT=4,
                   currentTask=22,resumeTask=22,terminalConfirmed=False,
                   businessStarted=0,foundX=100,foundY=200,
                   Time=lambda:1700000000+clock[0]//1000,TickCount=lambda:clock[0],
                   BusinessExpired=lambda:clock[0]>deadline,
                   WorldBoolean=lambda k:False,WorldNumber=lambda k,d,u:d,
                   WorldLog=logs.append,Note=logs.append,WorldStage=lambda s:None,
                   WorldResourcePrompt=lambda:None,ReturnToHall=lambda:1,
                   WorldText=lambda *a:self.fail('forest must not use OCR'))
        def match(n):
            probes.append(n)
            clock[0] += 10
            return n in active
        def wait(ms):
            calls.append(('wait',ms));clock[0]+=ms
        def tap(x,y,ms):
            calls.append(('tap',x,y,ms));clock[0]+=ms
            return not env['BusinessExpired']()
        def offset(x,y,ms):
            calls.append(('offset',x,y,ms));clock[0]+=ms
            return not env['BusinessExpired']()
        env.update(WorldMatch=match,WorldWait=wait,WorldTap=tap,WorldOffset=offset)
        load(['flows/017_英雄副本/英雄副本.mq',STATE,FLOW],env)
        env['WorldPair']=lambda b:match(b+'一') or match(b+'二')
        env['NewForestSession']()
        env['LoadForestSettings']()
        env['ForestInitializeFight']()
        return env,clock,calls,probes,logs

    def test_original_configuration_defaults(self):
        e,*_=self.fixture()
        self.assertFalse(e['forestEnabled']);self.assertFalse(e['forestHeart']);self.assertFalse(e['forestBag'])
        self.assertEqual([e[k] for k in ['forestFrequency','forestMode','forestMinutes','forestFailureLimit','forestInterval']],[60,0,2,3,30])
        self.assertEqual(e['SelectForest'](),0)

    def test_due_selector_and_original_resume(self):
        e,*_=self.fixture();e['forestEnabled']=True
        self.assertEqual(e['SelectForest'](),22)
        e['forestDue']=e['Time']()+1
        self.assertEqual(e['SelectForest'](),0)
        e['forestDue']=e['Time']()
        self.assertEqual(e['SelectForest'](),22)

    def test_minimum_duration_and_frequency_original_cross_field_condition(self):
        for minutes,frequency,seconds in [(0,90,120),(1,3600,120),(2,3600,120),(4,3600,240)]:
            e,*_=self.fixture();e['forestMinutes']=minutes;e['ForestInitializeFight']()
            self.assertEqual(e['forestFrequencySeconds'],frequency)
            self.assertEqual(e['forestSeconds'],seconds)
        e['forestFailureLimit']=0;e['ForestInitializeFight']()
        self.assertEqual(e['forestRuntimeFailureLimit'],1)

    def test_prepare_four_independent_checks_and_waits(self):
        names=['022_入口','022_离线领取','022_离线关闭','022_主界面']
        e,_,c,p,_=self.fixture(names)
        self.assertEqual(e['ForestPrepare'](),1)
        self.assertEqual(p,names)
        self.assertEqual(c,[('offset',0,0,500),('offset',0,0,500),('tap',150,50,500),('wait',1000)])

    def test_unknown_prepare_never_completes_or_clicks(self):
        e,_,c,_,_=self.fixture(deadline=300)
        self.assertEqual(e['ForestPrepare'](),4)
        self.assertEqual(c,[]);self.assertFalse(e['terminalConfirmed']);self.assertFalse(e['forestDeferred'])

    def test_navigation_failure_blocks_prepare(self):
        e,_,c,p,_=self.fixture();e['ForestEnterMode']=lambda:4
        self.assertEqual(e['ExecuteForest'](),4);self.assertEqual(c,[]);self.assertEqual(p,[])

    def test_mode_strict_60seconds_defers_one_hour_without_2second_wait(self):
        e,clock,c,_,_=self.fixture()
        e['ReturnToHall']=lambda:clock.__setitem__(0,clock[0]+1000) or 1
        self.assertEqual(e['ForestEnterMode'](),2)
        self.assertGreater(clock[0],60100)
        self.assertEqual(e['forestRetryAt'],e['Time']()+3600)
        self.assertNotIn(('wait',2000),c);self.assertFalse(e['terminalConfirmed'])

    def test_mode_target_uses_original_dimensional_patterns(self):
        e,_,c,p,_=self.fixture(['020_模式灰色'])
        self.assertEqual(e['ForestEnterMode'](),1)
        self.assertEqual(p,['020_入口','020_模式灰色']);self.assertEqual(c,[])

    def test_pending_event_survives_recovery_and_does_not_reenter(self):
        e,_,c,p,_=self.fixture();e['ForestDefer'](1800,'本轮结束')
        due=e['forestRetryAt'];attack=e['forestAttackAt']
        e['RecoverForestTask']();e['StartForestTask']()
        self.assertEqual(e['ExecuteForest'](),2)
        self.assertEqual(e['forestRetryAt'],due);self.assertEqual(e['forestAttackAt'],attack)
        self.assertEqual(c,[]);self.assertEqual(p,[])

    def test_schedule_requires_hall_and_foreground_gate(self):
        e,*_=self.fixture();e['ForestDefer'](1800,'结束')
        e['BeginForegroundCommit']=lambda:False
        self.assertFalse(e['ScheduleForestRetry'](False));self.assertFalse(e['ScheduleForestRetry'](True))
        self.assertEqual(e['resumeTask'],22);self.assertTrue(e['forestDeferred'])
        e['BeginForegroundCommit']=lambda:True
        due=e['forestRetryAt'];self.assertTrue(e['ScheduleForestRetry'](True))
        self.assertEqual(e['forestDue'],due);self.assertFalse(e['forestAttackStarted'])
        self.assertEqual(e['currentTask'],0);self.assertEqual(e['resumeTask'],0);self.assertFalse(e['terminalConfirmed'])

    def test_attack_time_survives_reentry_but_local_counters_reset(self):
        e,clock,*_=self.fixture();at=e['forestAttackAt'];clock[0]+=10000
        e['forestFailures']=3;e['forestAttempts']=9;e['ForestInitializeFight']()
        self.assertEqual(e['forestAttackAt'],at);self.assertEqual(e['forestFailures'],0);self.assertEqual(e['forestAttempts'],0)

    def test_heart_priority_then_bag_and_original_delays(self):
        e,clock,c,_,_=self.fixture(['022_主界面']);e.update(forestHeart=True,forestBag=True)
        clock[0]+=1;e['ForestMainAction']()
        self.assertEqual(c,[('offset',560,-848,2000)])
        e['ForestMainAction']()
        self.assertEqual(c[-1],('offset',560,-733,2000))
        self.assertEqual(e['forestHeartDelay'],3600000);self.assertEqual(e['forestBagDelay'],3630000)

    def test_disabled_heart_and_bag_consume_priority_without_click(self):
        e,clock,c,_,_=self.fixture(['022_主界面']);clock[0]+=1
        e['ForestMainAction']();e['ForestMainAction']()
        self.assertEqual(c,[]);self.assertEqual(e['forestBagDelay'],3600000)

    def test_normal_attack_and_strict_30seconds_burst(self):
        for elapsed,expected in [(30000,[('offset',252,-350,1000),('wait',2000)]),(30001,[('offset',252,-78,200)]*5+[('wait',2000)])]:
            e,clock,c,_,_=self.fixture(['022_主界面']);e.update(forestHeartDelay=999999,forestBagDelay=999999)
            clock[0]+=elapsed-10
            self.assertTrue(e['ForestMainAction']());self.assertEqual(c,expected);self.assertEqual(e['forestAttempts'],1)

    def test_heart_panel_twenty_clicks_then_double_then_exit(self):
        e,_,c,_,_=self.fixture(['022_念力面板']);e['forestHeart']=True
        e['ForestPanels']();self.assertEqual(c,[('tap',570,1124,200)]*20)
        c.clear();e['ForestPanels']();self.assertEqual(c,[('tap',158,1122,500)]*2)
        c.clear();e['ForestPanels']();self.assertEqual(c,[('offset',0,0,700)])

    def test_bag_first_three_actions_then_exit_and_original_5ms_waits(self):
        e,_,c,_,_=self.fixture(['022_分解面板']);e['forestBag']=True
        for _ in range(3):e['ForestPanels']()
        self.assertEqual(c,([('offset',253,-42,0),('wait',5),('wait',5)])*3)
        c.clear();e['ForestPanels']();self.assertEqual(c,[('offset',0,0,1000),('wait',5),('wait',5)])

    def test_bag_confirm_and_exit_are_independent(self):
        e,_,c,p,_=self.fixture(['022_分解退出','022_分解确认']);e['forestBag']=True;e['forestAttempts']=8
        e['ForestPanels']();self.assertEqual(p,['022_分解面板','022_分解退出','022_分解确认'])
        self.assertEqual(c,[('wait',5),('offset',0,0,700),('wait',5),('offset',0,0,200)])
        self.assertEqual(e['forestAttempts'],0)

    def test_skip_pair_and_success_failure_order(self):
        e,_,c,p,_=self.fixture(['022_战斗二','022_战斗成功','022_战斗失败'])
        e['ForestBattleChecks']()
        self.assertEqual(c,[('offset',-311,87,2000),('offset',0,0,1000),('offset',0,0,1000)])
        self.assertEqual(e['forestFailures'],1)
        self.assertLess(p.index('022_战斗成功'),p.index('022_战斗失败'))

    def test_exit_mode_only_second_battle_and_exit_dialog(self):
        e,_,c,p,_=self.fixture(['022_战斗一','022_战斗二','022_退出战斗'])
        e.update(forestMode=1,forestFailures=3);e['ForestBattleChecks']()
        self.assertNotIn('022_战斗一',p)
        self.assertEqual(c,[('offset',-311,10,0),('offset',0,0,200)])
        self.assertEqual(e['forestFailures'],0)

    def test_fewer_players_resets_end_grace_not_attack_duration(self):
        e,clock,_,_,_=self.fixture(['022_开战少人']);at=e['forestAttackAt'];clock[0]+=5000
        e['ForestBattleChecks']()
        self.assertEqual(e['forestAttackAt'],at);self.assertGreater(e['forestEndAt'],at)

    def test_sixth_popup_clicks_original_return_coordinate(self):
        e,_,c,_,_=self.fixture(['022_图标6'])
        for _ in range(6):e['ForestBattleChecks']()
        self.assertEqual(c,[('tap',587,982,3000)]*6+[('offset',0,0,1000)])

    def test_thresholds_are_strict_not_equal_and_exit_wait_3000(self):
        for field,limit in [('forestAttempts',10),('forestFailures',3)]:
            e,_,c,_,_=self.fixture(['022_主界面'])
            original=e['ForestInitializeFight']
            def init():
                original();e[field]=limit
            e['ForestInitializeFight']=init
            def action():
                self.assertFalse(e['forestDeferred']);e[field]+=1;return True
            e['ForestMainAction']=action
            self.assertEqual(e['ForestFight'](),2)
            self.assertEqual(c,[('wait',3000)])
            self.assertEqual(e['forestRetryAt'],e['Time']()+1800)
            self.assertFalse(e['terminalConfirmed'])

    def test_ending_30seconds_grace_not_new_success(self):
        e,clock,c,_,_=self.fixture()
        original=e['ForestInitializeFight']
        def init():original();e['forestAttempts']=11
        e['ForestInitializeFight']=init
        self.assertEqual(e['ForestFight'](),2)
        self.assertGreater(clock[0],33100);self.assertEqual(c,[('wait',3000)])
        self.assertFalse(e['terminalConfirmed'])

    def test_unknown_battle_public_timeout_never_schedules_or_completes(self):
        e,_,c,_,_=self.fixture(deadline=1000)
        self.assertEqual(e['ForestFight'](),4)
        self.assertEqual(c,[]);self.assertFalse(e['forestDeferred']);self.assertFalse(e['terminalConfirmed'])

    def test_pattern_constants_and_source_catalog_are_exact(self):
        originals={'root.643':'原型643.json','root.775':'图标775原型.json','root.773':'少人773原型.json'}
        records=json.loads((E/'图色转换.json').read_text('utf8'))
        catalog={r['name']:r for r in json.loads((ROOT/'evidence/图色参数.json').read_text('utf8'))}
        source=(ROOT/'common/图色参数.mq').read_text('utf-8-sig')
        self.assertEqual(len(records),16)
        for r in records:
            k=json.loads((E/originals[r['source']]).read_text('utf8'))['constants'];a,b=r['constantIndices']
            self.assertEqual(r['definition'][4:6],[k[a],k[b]])
            self.assertEqual(catalog[r['name']],r)
            self.assertIn('Case '+json.dumps(r['name'],ensure_ascii=False),source)
            args=','.join(json.dumps(v,ensure_ascii=False) if isinstance(v,str) else str(v) for v in r['definition'])
            self.assertIn('FindMultiColor '+args+',foundX,foundY',source)
            self.assertEqual(r['definition'][-2:],[1,0.9])
        self.assertEqual(next(r for r in records if r['name']=='022_图标6')['definition'][:4],[152,362,597,557])

    def test_configuration_preserves_all_old_controls_and_all_checks_off(self):
        import sys
        sys.path.insert(0,str(ROOT/'tools'));from check_ui import inspect
        config=json.loads((ROOT/'project.json').read_text('utf8'))
        source='\n'.join((ROOT/f).read_text('utf-8-sig') for f in [config['entry'],*config['modules']])
        controls=inspect((ROOT/config['ui']).read_text('utf-8-sig'),source)
        before=json.loads((E/'原配置基线.json').read_text('utf8'))
        self.assertEqual(len(controls),225)
        for name,item in before.items():self.assertEqual(list(controls[name]),item)
        checks=[p for kind,p in controls.values() if kind=='多选框']
        self.assertEqual(len(checks),55);self.assertTrue(all(p['选中'] is False for p in checks))

    def test_protected_dist_and_assistant_artifacts_unchanged(self):
        for filename,digest in json.loads((E/'未同步基线.json').read_text('utf8')).items():
            self.assertEqual(hashlib.sha256(Path(filename).read_bytes()).hexdigest(),digest,filename)

    def test_public_timeout_strict_and_foreground_first(self):
        e,clock,*_=self.fixture();load(['common/运行计时.mq'],e)
        e.update(businessLimit=120000,businessStarted=0)
        clock[0]=120000;self.assertFalse(e['BusinessExpired']())
        clock[0]+=1;self.assertTrue(e['BusinessExpired']())
        clock[0]=0;e['ForegroundInterrupted']=lambda:True
        e['forestPublicTimedOut']=False
        self.assertTrue(e['BusinessExpired']())
        self.assertFalse(e['forestPublicTimedOut'])

    def test_public_timeout_stages_one_hour_and_not_on_foreground_interruption(self):
        e,*_=self.fixture();e['forestPublicTimedOut']=True
        e['ForegroundInterrupted']=lambda:True
        e['StageForestPublicTimeout']();self.assertFalse(e['forestDeferred'])
        e['ForegroundInterrupted']=lambda:False
        e['StageForestPublicTimeout']()
        self.assertTrue(e['forestTimeoutPending']);self.assertTrue(e['forestDeferred'])
        self.assertEqual(e['forestRetryAt'],e['Time']()+3600);self.assertFalse(e['terminalConfirmed'])

    def scheduler_fixture(self):
        from types import SimpleNamespace
        e,clock,c,p,logs=self.fixture()
        events=[]
        e.update(SelectDueTask=lambda:22,SaveCurrentTask=lambda t:None,
                 EnsureGameHall=lambda:1,SaveRecovery=lambda:events.append('recover'),
                 RestartGame=lambda:events.append('restart'),GAME_PACKAGE='game',
                 Sys=SimpleNamespace(IsRunning=lambda pkg:True))
        def dispatch(t):
            e['forestPublicTimedOut']=True
            return 4
        e['DispatchTask']=dispatch
        e['ReturnToHall']=lambda:events.append('hall') or 1
        load(['common/任务调度.mq'],e)
        return e,events

    def test_scheduler_timeout_releases_after_hall_and_default_no_restart(self):
        e,events=self.scheduler_fixture();e['SchedulerStep']()
        self.assertEqual(events,['hall']);self.assertEqual(e['currentTask'],0)
        self.assertEqual(e['forestDue'],e['Time']()-1+3600)
        self.assertFalse(e['terminalConfirmed'])

    def test_scheduler_configured_public_restart_after_release(self):
        e,events=self.scheduler_fixture();e['forestRestartOnTimeout']=True
        e['SchedulerStep']();self.assertEqual(events,['hall','restart'])
        self.assertEqual(e['resumeTask'],0);self.assertFalse(e['terminalConfirmed'])

    def test_failed_hall_keeps_original_task_and_pending_due(self):
        e,events=self.scheduler_fixture();e['ReturnToHall']=lambda:events.append('hall') or 4
        e['SchedulerStep']();self.assertEqual(events,['hall','recover','restart'])
        self.assertEqual(e['currentTask'],22);self.assertTrue(e['forestDeferred'])
        self.assertEqual(e['forestDue'],0);self.assertFalse(e['terminalConfirmed'])

    def test_registered_resume_dispatch_and_foreground_ownership(self):
        e,*_=self.fixture();load(['common/任务注册.mq','common/任务分派.mq'],e)
        self.assertEqual(e['SelectDueTask'](),22)
        e['ExecuteForest']=lambda:2
        self.assertEqual(e['DispatchTask'](22),2)
        foreground=(ROOT/'common/前台监控.mq').read_text('utf-8-sig')
        self.assertRegex(foreground,r'\bcurrentTask = 22(?: Or| Then)')

    def test_no_ocr_private_engine_launch_or_direct_completion(self):
        source=(ROOT/FLOW).read_text('utf-8-sig')
        for name in ['WorldText(','OcrText','OCREX','LuaAuxLib','GK.','RunApp','KillApp','RestartGame(','CommitTask(']:
            self.assertNotIn(name,source)
        self.assertNotIn('terminalConfirmed = True',source)

    def test_retained_native_comparisons_pin_strict_thresholds(self):
        p=json.loads((E/'原型643.json').read_text('utf8'))
        def instruction(pc):
            w=p['code'][pc]
            return w&63,w>>6&255,w>>23&511,w>>14&511
        self.assertEqual(instruction(296),(20,1,268,6))  # 10 < attempts
        self.assertEqual(instruction(298),(20,1,8,7))    # configured failures < failures
        self.assertEqual(instruction(306),(20,0,22,21)) # duration < elapsed
        self.assertEqual(instruction(276),(20,0,21,284))# challenge minutes < 2
        self.assertEqual(instruction(289),(20,0,21,267))# challenge minutes < 1, not frequency
        self.assertEqual(p['constants'][12],10)
        self.assertEqual(p['constants'][58],30000)


if __name__=='__main__':unittest.main()
