import hashlib
import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from mq_subset import load

ROOT = Path(__file__).resolve().parents[1]
STATE = 'common/联盟组队状态.mq'
FLOW = 'flows/023_联盟组队战/联盟组队战.mq'
E = ROOT/'flows/023_联盟组队战/evidence'


class AllianceTests(unittest.TestCase):
    def fixture(self,active=(),deadline=400000):
        clock,calls,probes,logs=[100],[],[],[]
        e=dict(RESULT_OK=1,RESULT_WAIT=2,RESULT_FAIL=3,RESULT_TIMEOUT=4,
               currentTask=23,resumeTask=23,terminalConfirmed=False,businessStarted=100,businessLimit=120000,
               Time=lambda:1700000000+clock[0]//1000,TickCount=lambda:clock[0],
               BusinessExpired=lambda:clock[0]>deadline,
               WorldBoolean=lambda k:False,WorldNumber=lambda k,d,u:d,
               WorldLog=logs.append,WriteMainLog=logs.append,Note=logs.append,
               WorldStage=lambda s:logs.append(s),WorldResourcePrompt=lambda:None,
               WorldDayStart=lambda t:(t+28800)//86400*86400-28800,
               DateTime=SimpleNamespace(WeekDay=lambda:3),
               Sys=SimpleNamespace(AppIsFront=lambda p:True,IsRunning=lambda p:True),
               GAME_PACKAGE='game',ReturnToHall=lambda:1,ShowMessage=logs.append,
               NamelessEnterMode=lambda:1)
        def match(n):
            probes.append((n,clock[0]));clock[0]+=10
            return n in active
        def wait(ms):calls.append(('wait',ms));clock[0]+=ms
        def offset(x,y,ms):
            calls.append(('offset',x,y,ms));clock[0]+=ms
            return not e['BusinessExpired']()
        def tap(x,y,ms):
            calls.append(('tap',x,y,ms));clock[0]+=ms
            return not e['BusinessExpired']()
        def swipe(*args):calls.append(('swipe',*args));clock[0]+=args[-1]
        e.update(WorldMatch=match,WorldWait=wait,WorldOffset=offset,WorldTap=tap,Swipe=swipe,Delay=wait)
        load([STATE,FLOW],e);e['LoadAllianceSettings']();e['NewAllianceSession']()
        return e,clock,calls,probes,logs

    def test_defaults_all_off_and_original_choice_indices(self):
        e,*_=self.fixture()
        self.assertFalse(e['allianceEnabled']);self.assertFalse(e['allianceEnroll'])
        self.assertEqual(e['allianceTimeChoice'],1);self.assertEqual(e['allianceProcessChoice'],1)
        self.assertEqual(e['allianceFailureLimit'],2);self.assertFalse(e['allianceRestartOnTimeout'])
        self.assertEqual(e['SelectAlliance'](),0)

    def test_time_choice_does_not_invent_18_hour_schedule(self):
        for choice in [0,1]:
            e,*_=self.fixture();e['allianceTimeChoice']=choice;e['NewAllianceSession']()
            self.assertEqual(e['allianceDue'],e['Time']())
            e['allianceEnabled']=True;self.assertEqual(e['SelectAlliance'](),23)

    def test_process_choice_not_consumed_by_business(self):
        source=(ROOT/FLOW).read_text('utf-8-sig')
        self.assertNotIn('allianceProcessChoice',source)
        self.assertNotIn('642',source)
        for value in [0,1]:
            e,_,c,_,_=self.fixture(['023_自动未选','023_自动已选'])
            e['allianceProcessChoice']=value
            self.assertEqual(e['AllianceEnableAuto'](),1)
            self.assertEqual(c,[('tap',358,1230,500)])

    def test_due_and_abandonment_guards(self):
        e,*_=self.fixture();e['allianceEnabled']=True
        e['allianceDue']=e['Time']()+1;self.assertEqual(e['SelectAlliance'](),0)
        e['allianceDue']-=1;self.assertEqual(e['SelectAlliance'](),23)
        e['allianceAbandoned']=True;self.assertEqual(e['SelectAlliance'](),0)
        self.assertEqual(e['ExecuteAllianceBattle'](),4)

    def test_find_ex_two_rechecks_autoclick_and_original_wait(self):
        e,_,c,_,_=self.fixture(['023_入口'])
        self.assertFalse(e['AllianceEnterIcon']())
        self.assertEqual(c,[('offset',0,0,0),('wait',1000),('offset',0,0,0),('wait',1000),('offset',0,0,0)])

    def test_find_ex_disappearing_icon_returns_without_extra_click(self):
        e,_,c,_,_=self.fixture();hits=iter([True,False])
        e['WorldMatch']=lambda n:next(hits)
        self.assertTrue(e['AllianceEnterIcon']());self.assertEqual(c,[('offset',0,0,0),('wait',1000)])

    def test_entry_priority_short_circuits_original_phase_checks(self):
        names=['023_未参加','023_决赛排行','023_准备挑战','023_已组队等报名','023_组队阶段','023_报名阶段']
        for i,n in enumerate(names[:4]):
            e,_,c,p,_=self.fixture(names[i:])
            self.assertEqual(e['AlliancePrepare'](),1)
            self.assertEqual([n for n,t in p],['023_入口',*names[:i+1]])
            self.assertEqual(e['allianceMode'],1 if i==2 else 0)
            self.assertEqual(c,[('wait',1000)] if i in [1,3] else [])

    def test_group_weekday_two_compares_scheduled_time_not_current_clock(self):
        e,clock,_,_,_=self.fixture(['023_组队阶段']);e['DateTime'].WeekDay=lambda:2
        today=e['WorldDayStart'](e['Time']());e['allianceDue']=today+57599
        self.assertEqual(e['AlliancePrepare'](),2)
        self.assertEqual(e['allianceRetryAt'],today+57600);self.assertFalse(e['terminalConfirmed'])
        e['allianceDeferred']=False;e['allianceDue']=today+57600
        self.assertEqual(e['AlliancePrepare'](),1);self.assertEqual(e['allianceMode'],2)

    def test_group_and_signup_other_weekday_are_known_terminal_not_counted_round(self):
        for n,week in [('023_组队阶段',3),('023_报名阶段',2)]:
            e,*_=self.fixture([n]);e['DateTime'].WeekDay=lambda:week
            self.assertEqual(e['AlliancePrepare'](),1)
            self.assertTrue(e['terminalConfirmed']);self.assertTrue(e['alliancePendingPermanent'])
            self.assertFalse(e['alliancePendingRound']);self.assertEqual(e['allianceCount'],0)

    def test_signup_weekday_three_reaches_mode_three(self):
        e,*_=self.fixture(['023_报名阶段']);self.assertEqual(e['AlliancePrepare'](),1)
        self.assertEqual(e['allianceMode'],3);self.assertFalse(e['terminalConfirmed'])

    def test_unknown_entry_strict_30_seconds_no_completion_or_click(self):
        e,clock,c,_,_=self.fixture();self.assertEqual(e['AlliancePrepare'](),4)
        self.assertGreater(clock[0],30100);self.assertLess(clock[0],30200)
        self.assertEqual(c,[]);self.assertFalse(e['terminalConfirmed']);self.assertFalse(e['allianceExitPending'])

    def test_auto_independent_order_and_sixth_not_fifth_click_limit(self):
        e,_,c,p,_=self.fixture(['023_准备挑战','023_自动未选'])
        self.assertEqual(e['AllianceEnableAuto'](),1)
        self.assertEqual(c,[('tap',438,1020,1000),('tap',358,1230,500)]*6)
        self.assertEqual([n for n,t in p[:3]],['023_准备挑战','023_自动未选','023_自动已选'])
        self.assertFalse(e['terminalConfirmed'])

    def test_unknown_auto_30_seconds_not_success(self):
        e,clock,c,_,_=self.fixture();self.assertEqual(e['AllianceEnableAuto'](),4)
        self.assertGreater(clock[0],30100);self.assertEqual(c,[]);self.assertFalse(e['terminalConfirmed'])

    def test_four_original_swipes_and_nine_scans_without_target(self):
        e,_,c,p,_=self.fixture(['023_挑战主界面'])
        self.assertEqual(e['AllianceFight'](),1)
        self.assertEqual(c,[('swipe',245,980,245,680,1000),('wait',1000)]*4+[('wait',1000)]+[('wait',200)]*9)
        cells=[n for n,t in p if n.startswith('023_玩家格')]
        self.assertEqual(cells,['023_玩家格'+str(i) for i in range(1,10)])
        self.assertTrue(e['alliancePendingPermanent']);self.assertEqual(e['allianceCount'],0)

    def test_nine_cell_flags_selected_once_then_original_round_exit(self):
        e,_,c,p,_=self.fixture(['023_挑战主界面','023_玩家格1'])
        self.assertEqual(e['AllianceFight'](),1)
        self.assertEqual(c.count(('offset',0,0,200)),1)
        self.assertFalse(e['AllianceHasCell'](1));self.assertTrue(e['alliancePendingRound'])
        self.assertFalse(e['alliancePendingPermanent']);self.assertEqual(e['allianceCount'],0)

    def test_unknown_fight_exits_25_seconds_without_count_or_success(self):
        e,clock,c,_,_=self.fixture();self.assertEqual(e['AllianceFight'](),2)
        self.assertGreater(clock[0],25100);self.assertLess(clock[0],25300)
        self.assertEqual(c,[]);self.assertFalse(e['terminalConfirmed']);self.assertEqual(e['allianceCount'],0)
        self.assertEqual(e['allianceRetryAt'],e['Time']()+3600)
        self.assertGreater(e['businessStarted'],13100)

    def test_fight_180_seconds_absolute_despite_repeated_settlement_actions(self):
        e,clock,_,_,_=self.fixture(['023_结算一'])
        self.assertEqual(e['AllianceFight'](),2);self.assertGreater(clock[0],180100)
        self.assertIn('180秒',e['allianceReason']);self.assertFalse(e['terminalConfirmed'])

    def test_battle_checks_independent_duplicate_and_exact_reset_points(self):
        names=['023_结算一','023_结算二','023_图标6','023_暂停战斗','023_退出战斗']
        e,clock,c,p,_=self.fixture(names)
        self.assertTrue(e['AllianceBattleChecks']())
        self.assertEqual([n for n,t in p],['023_结算一','023_结算二','023_结算一','023_图标6','023_暂停战斗','023_退出战斗'])
        self.assertEqual(c,[('offset',0,0,3000),('offset',0,0,3000),('offset',0,0,1000),('tap',587,982,2000),('offset',-311,10,200),('offset',0,0,200)])
        self.assertFalse(e['allianceCanChallenge']);self.assertGreater(e['allianceActionAt'],e['businessStarted'])

    def test_settlement_two_does_not_reset_activity_or_public_timer(self):
        e,_,_,_,_=self.fixture(['023_结算二']);e['allianceActionAt']=11
        e['AllianceBattleChecks']();self.assertEqual(e['allianceActionAt'],11);self.assertEqual(e['businessStarted'],100)

    def test_enroll_disabled_exits_each_original_branch_without_click(self):
        for name in ['AllianceFormTeam','AllianceSignup']:
            e,_,c,_,_=self.fixture();self.assertEqual(e[name](),1)
            self.assertEqual(c,[]);self.assertTrue(e['alliancePendingRound']);self.assertFalse(e['allianceDone'])

    def test_group_original_independent_checks_and_eleventh_confirmation_limit(self):
        e,_,c,_,_=self.fixture(['023_组队阶段','023_组队确认']);e['allianceEnroll']=True
        self.assertEqual(e['AllianceFormTeam'](),1)
        self.assertEqual(c,[('offset',107,-145,200),('offset',0,0,300)]*11)
        self.assertFalse(e['allianceDone']);self.assertEqual(e['allianceCount'],0)

    def test_signup_original_sixth_click_limit(self):
        e,_,c,_,_=self.fixture(['023_报名阶段']);e['allianceEnroll']=True
        self.assertEqual(e['AllianceSignup'](),1);self.assertEqual(c,[('offset',420,-190,500)]*6)

    def test_already_signed_up_wait_1000_and_short_circuit_registration(self):
        e,_,c,p,_=self.fixture(['023_已报名','023_报名阶段']);e['allianceEnroll']=True
        self.assertEqual(e['AllianceSignup'](),1);self.assertEqual(c,[('wait',1000)])
        self.assertEqual([n for n,t in p],['023_已报名'])

    def test_group_and_signup_idle_10_seconds_are_not_success(self):
        for name in ['AllianceFormTeam','AllianceSignup']:
            e,clock,c,_,_=self.fixture();e['allianceEnroll']=True
            self.assertEqual(e[name](),2);self.assertGreater(clock[0],10100);self.assertLess(clock[0],10200)
            self.assertEqual(c,[]);self.assertFalse(e['terminalConfirmed']);self.assertEqual(e['allianceCount'],0)

    def test_group_absolute_100_seconds_with_continued_group_action(self):
        e,clock,_,_,_=self.fixture(['023_组队阶段']);e['allianceEnroll']=True
        self.assertEqual(e['AllianceFormTeam'](),2);self.assertGreater(clock[0],100100)
        self.assertEqual(e['allianceCount'],0);self.assertFalse(e['terminalConfirmed'])

    def test_mode_failure_prevents_business_checks(self):
        e,_,c,p,_=self.fixture();e['NamelessEnterMode']=lambda:4
        self.assertEqual(e['ExecuteAllianceBattle'](),4);self.assertEqual(c,[]);self.assertEqual(p,[])

    def test_deferred_and_terminal_events_survive_recovery_without_refighting(self):
        for deferred in [False,True]:
            e,_,c,p,_=self.fixture()
            if deferred:e['AllianceDefer'](e['Time']()+3600,'阶段边界')
            else:e['AllianceFinish']('明确页面出口',False,True)
            e['RecoverAllianceTask']();e['StartAllianceTask']()
            e['NamelessEnterMode']=lambda:self.fail('pending cleanup must not reenter business')
            self.assertEqual(e['ExecuteAllianceBattle'](),2 if deferred else 1)
            self.assertEqual(c,[]);self.assertEqual(p,[]);self.assertEqual(e['allianceCount'],0)

    def test_public_commit_requires_terminal_event_hall_and_foreground(self):
        e,*_=self.fixture();load(['common/任务状态.mq'],e)
        e['terminalConfirmed']=True;self.assertFalse(e['CommitTask'](True))
        e['AllianceFinish']('原业务出口',False,True);due=e['alliancePendingDue']
        self.assertFalse(e['CommitTask'](False));self.assertEqual(e['allianceCount'],0)
        e['BeginForegroundCommit']=lambda:False
        self.assertFalse(e['CommitTask'](True));self.assertEqual(e['allianceCount'],0)
        e['BeginForegroundCommit']=lambda:True
        self.assertTrue(e['CommitTask'](True));self.assertEqual(e['allianceCount'],1);self.assertEqual(e['allianceDue'],due)
        self.assertEqual(e['resumeTask'],0);self.assertFalse(e['allianceDone']);self.assertFalse(e['CommitTask'](True))

    def test_defer_release_gate_does_not_increment_or_permanently_complete(self):
        e,*_=self.fixture();e['AllianceDefer'](e['Time']()+3600,'非成功')
        self.assertFalse(e['ReleaseAllianceRetry'](False));e['BeginForegroundCommit']=lambda:False
        self.assertFalse(e['ReleaseAllianceRetry'](True));self.assertEqual(e['currentTask'],23)
        e['BeginForegroundCommit']=lambda:True;self.assertTrue(e['ReleaseAllianceRetry'](True))
        self.assertEqual(e['currentTask'],0);self.assertEqual(e['allianceCount'],0);self.assertFalse(e['allianceDone'])

    def test_public_timeout_strict_boundary_and_foreground_priority(self):
        e,clock,*_=self.fixture();load(['common/运行计时.mq'],e);e['businessLimit']=120000
        clock[0]=120100;self.assertFalse(e['BusinessExpired']())
        clock[0]+=1;self.assertTrue(e['BusinessExpired']());self.assertTrue(e['alliancePublicTimedOut'])
        e['alliancePublicTimedOut']=False;e['ForegroundInterrupted']=lambda:True
        self.assertTrue(e['BusinessExpired']());self.assertFalse(e['alliancePublicTimedOut'])

    def test_public_failure_limit_two_not_foreground_and_no_success(self):
        e,*_=self.fixture()
        e['alliancePublicTimedOut']=True;e['ForegroundInterrupted']=lambda:True;e['RecoverAllianceTask']()
        self.assertEqual(e['allianceFailures'],0)
        e['ForegroundInterrupted']=lambda:False
        for n in [1,2]:
            e['alliancePublicTimedOut']=True;e['RecoverAllianceTask']()
            self.assertEqual(e['allianceFailures'],n);self.assertEqual(e['allianceAbandoned'],n==2)
        self.assertEqual(e['resumeTask'],0);self.assertEqual(e['allianceCount'],0);self.assertFalse(e['allianceDone'])

    def scheduler_fixture(self):
        e,clock,c,p,logs=self.fixture();events=[]
        e.update(SelectDueTask=lambda:23,SaveCurrentTask=lambda t:None,EnsureGameHall=lambda:1,
                 SaveRecovery=lambda:events.append('recover'),RestartGame=lambda:events.append('restart'),
                 ReturnToHall=lambda:events.append('hall') or 1)
        load(['common/任务调度.mq','common/任务状态.mq'],e)
        # Preserve the real forest-independent public commit; custom recovery tracks failure.
        e['SaveRecovery']=lambda:events.append('recover')
        e['SaveCurrentTask']=lambda t:None
        return e,clock,c,events

    def test_scheduler_commits_only_after_existing_continuous_hall_check(self):
        e,_,_,events=self.scheduler_fixture();load(['common/返回大厅.mq'],e)
        e.update(stageName='联盟23',SetStage=lambda s:None,ResetHallCheck=lambda:events.append('reset-hall'),
                 ResetHallClearing=lambda:None,ClearHallObstacle=lambda:False)
        count=[0]
        def confirm():count[0]+=1;events.append('hall-sample');return count[0]>=3
        e['ConfirmHall']=confirm
        e['DispatchTask']=lambda t:e['AllianceFinish']('原明确出口',False,True)
        e['SchedulerStep']();self.assertEqual(count[0],3);self.assertEqual(e['allianceCount'],1)
        self.assertEqual(events,['reset-hall','hall-sample','hall-sample','hall-sample'])

    def test_scheduler_hall_failure_keeps_pending_event_and_no_count(self):
        e,_,_,events=self.scheduler_fixture();e['ReturnToHall']=lambda:events.append('hall') or 4
        e['DispatchTask']=lambda t:e['AllianceFinish']('明确出口',False,True)
        e['SchedulerStep']();self.assertEqual(events,['hall','recover','restart'])
        self.assertTrue(e['allianceExitPending']);self.assertEqual(e['allianceCount'],0)

    def test_registered_dispatch_priority_before_forest_and_resume(self):
        from test_control import ControlFlow
        f=ControlFlow();f.setUp();e=f.e
        e.update(Time=lambda:1700000000,WorldStage=lambda s:None,WorldLog=lambda s:None)
        load([STATE,'common/任务分派.mq'],e);e['NewAllianceSession']();e['allianceEnabled']=True
        e['SelectForest']=lambda:22
        self.assertEqual(e['SelectDueTask'](),23)
        e['resumeTask']=23;e['allianceEnabled']=False;self.assertEqual(e['SelectDueTask'](),23)
        e['ExecuteAllianceBattle']=lambda:2;self.assertEqual(e['DispatchTask'](23),2)
        e['allianceAbandoned']=True;self.assertNotEqual(e['SelectDueTask'](),23)

    def test_shared_foreground_restores_original_task_and_pending_terminal_without_count(self):
        from test_foreground import Foreground
        f=Foreground();f.setUp();e=f.e
        e.update(Time=lambda:1700000000,WorldStage=lambda s:None,WorldLog=f.logs.append,
                 WorldNumber=lambda k,d,u:d,WorldBoolean=lambda k:False,WriteMainLog=f.logs.append)
        load([STATE,FLOW],e);e['NewAllianceSession']();e['SaveCurrentTask'](23)
        e['AllianceFinish']('原业务出口',False,True)
        f.sample('launcher',0);f.sample('launcher',5000)
        self.assertTrue(e['HandleForegroundRecovery']());self.assertEqual(e['resumeTask'],23)
        self.assertEqual(e['allianceCount'],0);self.assertEqual(e['allianceFailures'],0)
        self.assertTrue(e['allianceExitPending']);self.assertEqual(e['allianceRestarts'],1)

    def test_exact_26_patterns_native_constants_and_actual_mq(self):
        records=json.loads((E/'图色转换.json').read_text('utf8'))
        p=json.loads((E/'原型641.json').read_text('utf8'))
        icon=json.loads((E/'图标775原型.json').read_text('utf8'))
        catalog={r['name']:r for r in json.loads((ROOT/'evidence/图色参数.json').read_text('utf8'))}
        mq=(ROOT/'common/图色参数.mq').read_text('utf-8-sig')
        self.assertEqual(len(records),26)
        for r in records:
            k=(icon if r['source']=='root.775' else p)['constants'];a,b=r['constantIndices']
            self.assertEqual(r['definition'][4:6],[k[a],k[b]]);self.assertEqual(catalog[r['name']],r)
            args=','.join(json.dumps(v,ensure_ascii=False) if isinstance(v,str) else str(v) for v in r['definition'])
            self.assertIn('FindMultiColor '+args+',foundX,foundY',mq)
        rects=[r['definition'][:4] for r in records if r['name'].startswith('023_玩家格')]
        self.assertEqual(rects,[[x[0],y[0],x[1],y[1]] for y in [(165,219),(588,665),(1026,1101)] for x in [(30,210),(261,455),(497,685)]])
        self.assertTrue(all(r['definition'][-2:]==[1,0.9] for r in records))

    def test_retained_native_thresholds_and_no_watch_consumption(self):
        p=json.loads((E/'原型641.json').read_text('utf8'));k=p['constants']
        self.assertNotIn('观看过程',k)
        for pc,value in [(350,30000),(450,5),(458,30000),(951,13000),(961,25000),(968,180000),(1059,10),(1067,10000),(1074,100000),(1167,5)]:
            w=p['code'][pc];self.assertEqual(w&63,20)
            self.assertEqual(k[(w>>23&511)-256],value)

    def test_ui_preserves_218_controls_and_all_55_checks_off(self):
        import sys
        sys.path.insert(0,str(ROOT/'tools'));from check_ui import inspect
        p=json.loads((ROOT/'project.json').read_text('utf8'))
        source='\n'.join((ROOT/f).read_text('utf-8-sig') for f in [p['entry'],*p['modules']])
        controls=inspect((ROOT/p['ui']).read_text('utf-8-sig'),source)
        old=json.loads((E/'原配置基线.json').read_text('utf8'))
        for n,(kind,props) in old.items():self.assertEqual(controls[n],(kind,props))
        self.assertEqual(len(controls),225)
        checks=[v for k,v in controls.values() if k=='多选框']
        self.assertEqual(len(checks),55);self.assertTrue(all(v['选中'] is False for v in checks))
        self.assertEqual(controls['日常_联盟组队战_时间'][1]['选项'],['18:00','立即'])
        self.assertEqual(controls['日常_联盟组队战_过程'][1]['选项'],['观看','不看'])
        self.assertEqual(controls['日常_联盟组队战_提示'][1]['点击响应'],'AllianceHelp')

    def test_no_private_engine_no_business_launch_commit_or_root642(self):
        source=(ROOT/FLOW).read_text('utf-8-sig')
        for token in ['root.642','OCREX','OcrText','LuaAuxLib','GK.','RunApp','KillApp','RestartGame(','CommitTask(']:
            self.assertNotIn(token,source)
        self.assertNotIn('allianceProcessChoice',source)

    def test_protected_artifacts_unchanged(self):
        for f,h in json.loads((E/'未同步基线.json').read_text('utf8')).items():
            self.assertEqual(hashlib.sha256(Path(f).read_bytes()).hexdigest(),h,f)


if __name__=='__main__':unittest.main()
