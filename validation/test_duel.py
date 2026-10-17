import hashlib,json,re,unittest
from pathlib import Path
from mq_subset import ROOT,load

class DuelTests(unittest.TestCase):
 def setUp(self):
  from test_worldboss import WorldBossTests
  self.f=WorldBossTests();self.f.setUp();self.f.at(12);self.e=self.f.e;self.swipes=[]
  self.e['Sys'].IsRunning=lambda p:True
  def match(n):
   self.f.now+=10;v=self.f.match(n)
   if n=='081_P08' or n in ['081_P27','081_P28','081_P29']:self.e.update(foundX=100,foundY=1100)
   if n in [f'081_P{i}' for i in range(17,23)]:self.e.update(foundX=650,foundY=500)
   return v
  def tap(x,y,w):
   self.assertTrue(0<=x<=719 and 0<=y<=1279,(x,y));self.f.tap(x,y,w)
  def swipe(*p):self.swipes.append(p);self.f.now+=p[-1]
  self.e.update(MatchPattern=match,TouchPoint=tap,Swipe=swipe,currentTask=81,duelEnabled=True,duelStars=0,duelProphecy=0,duelQuickStars=0,duelQuickMultiple=0,duelFailureMode=1,duelIdleLimit=120000,duelFailureLimit=2,duelRestartOnTimeout=True,businessStarted=0,businessLimit=120000,ForegroundInterrupted=lambda:self.f.interrupt)
  load(['common/强者对决状态.mq','common/运行计时.mq','flows/081_强者对决/强者对决.mq'],self.e)
  self.e['NewDuelSession']();self.e['DuelProgress']();self.e['duelRunning']=True
 def p(self,*n):self.f.visible={f'081_P{i:02}' for i in n}
 def test_config_exact_defaults_off_free_no_prophecy_or_quick(self):
  self.e['ReadUIConfig']=lambda k,d:d;self.e['LoadDuelSettings']()
  self.assertFalse(self.e['duelEnabled']);self.assertEqual([self.e[k] for k in ['duelStars','duelProphecy','duelQuickStars','duelQuickMultiple']],[0]*4)
  self.assertEqual([self.e[k] for k in ['duelIdleLimit','duelFailureLimit','duelRestartOnTimeout','duelHallDelay']],[120000,2,True,0])
 def test_all_module_configuration_keys_are_consumed_independently(self):
  cfg={'日常_强者对决':True,'日常_强者对决_星级':3,'日常_强者对决_预言':2,'日常_强者对决_一键刷新_星级':1,'日常_强者对决_一键刷新_倍数':2}
  self.e['ReadUIConfig']=lambda k,d:cfg.get(k,d);self.e['LoadDuelSettings']()
  self.assertEqual([self.e[k] for k in ['duelEnabled','duelStars','duelProphecy','duelQuickStars','duelQuickMultiple']],[True,3,2,1,2])
 def test_select_done_and_abandon_latches_no_midnight_invention(self):
  self.assertEqual(self.e['SelectDuel'](),81);self.e['CommitDuelTask']();self.f.stamp+=86400
  self.assertEqual(self.e['SelectDuel'](),0);self.e['NewDuelSession']();self.e['duelAbandoned']=True;self.assertEqual(self.e['SelectDuel'](),0)
 def test_pair_first_match_priority_and_anchor(self):
  self.p(0,1);self.assertTrue(self.e['DuelPair'](0,1));self.assertEqual(self.f.lookups,['081_P00'])
 def test_entry_unopened_no_notification_wait(self):
  for n in [0,1]:
   self.setUp();self.p(n);self.assertEqual(self.e['EnterDuel'](),1)
   self.assertEqual(self.f.now,1310+10*n);self.assertFalse(self.f.taps);self.assertTrue(self.e['terminalConfirmed'])
 def test_entry_scan_down_down_up_original785(self):
  self.e['BusinessExpired']=lambda:len(self.swipes)>=3;self.e['EnterDuel']()
  self.assertEqual(self.swipes,[(370,1000,370,300,300)]*2+[(370,300,370,1000,300)])
 def test_entry_click_and_active_mode2(self):
  self.p(2,4);self.assertEqual(self.e['EnterDuel'](),1);self.assertEqual(self.e['duelEntryMode'],2)
  self.assertEqual(self.f.taps,[(600,900,300)]);self.assertFalse(self.e['terminalConfirmed'])
 def test_entry_completed_with_prophecy_disabled_vs_enabled(self):
  for mode in [0,1,2]:
   self.setUp();self.e['duelProphecy']=mode;self.p(5);self.assertEqual(self.e['EnterDuel'](),1)
   self.assertEqual(self.e['terminalConfirmed'],mode==0)
   if mode:self.assertEqual(self.e['duelEntryMode'],1)
 def test_entry_gray_completed1000_resets_and_no_prophecy(self):
  self.e['duelProphecy']=2;self.p(6);self.assertEqual(self.e['EnterDuel'](),1)
  self.assertTrue(self.e['terminalConfirmed']);self.assertEqual(self.e['duelWatchdogAt'],self.f.now)
 def test_unknown_entry_watchdog_no_guess_done(self):
  self.assertEqual(self.e['EnterDuel'](),4);self.assertTrue(self.e['duelTimedOut']);self.assertFalse(self.e['terminalConfirmed'])
 def test_free_modes_stop_when_no_free_refresh_template_matches(self):
  for mode in [0,1]:
   self.setUp();self.e['duelStars']=mode;self.p(7,8)
   self.assertEqual(self.e['RefreshDuelManual'](),1);self.assertFalse(self.f.taps)
 def test_free_modes_max_two_actual_refresh_clicks_not_two_loops(self):
  for mode in [0,1]:
   self.setUp();self.e['duelStars']=mode;self.p(8)
   self.assertEqual(self.e['RefreshDuelManual'](),1);self.assertEqual(self.f.taps,[(153,1003,0)]*2);self.assertFalse(self.e['terminalConfirmed'])
 def test_manual_cached_anchor_not_overwritten_by_failed_star_or_double(self):
  self.p(8);old=self.e['MatchPattern']
  def match(n):
   v=old(n)
   if n!='081_P08':self.e['foundX']=-1;self.e['foundY']=-1
   return v
  self.e['MatchPattern']=match;self.e['RefreshDuelManual']();self.assertEqual(self.f.taps,[(153,1003,0)]*2)
 def test_four_modes_target_exact_star_templates(self):
  for mode,p in [(0,9),(0,10),(1,13),(1,14),(2,13),(2,14),(3,15),(3,16)]:
   self.setUp();self.e['duelStars']=mode;self.p(8,p);self.assertEqual(self.e['RefreshDuelManual'](),1)
   self.assertFalse(self.f.taps);self.assertEqual(self.e['duelWatchdogAt'],self.f.now)
 def test_paid_modes_do_not_apply_two_free_refresh_limit_or_p07(self):
  for mode in [2,3]:
   self.setUp();self.e['duelStars']=mode;self.p(7,8)
   self.f.after=lambda *a:setattr(self.f,'interrupt',len(self.f.taps)>=3)
   self.assertEqual(self.e['RefreshDuelManual'](),4);self.assertEqual(self.f.taps,[(153,1003,0)]*3)
   self.assertNotIn('081_P07',self.f.lookups);self.assertFalse(self.e['terminalConfirmed'])
 def test_double_choice_wait1000_click_not_counted_as_refresh(self):
  self.p(8,11);self.f.after=lambda *a:setattr(self.f,'interrupt',len(self.f.taps)>=3)
  self.e['RefreshDuelManual']();self.assertEqual(self.f.taps,[(600,900,0)]*3);self.assertFalse(self.e['terminalConfirmed'])
 def test_quick_native_condition_branches_from_raw_vm(self):
  proto=json.loads((ROOT/'flows/081_强者对决/evidence/root625原型.json').read_text('utf8'));ks=proto['constants'];code=proto['code']
  records=json.loads((ROOT/'flows/081_强者对决/evidence/图色转换.json').read_text('utf8'))
  for star,multi,index in [(1,0,18),(1,1,19),(1,2,20),(0,1,21),(0,2,22)]:
   regs={1:{'强者对决':{'一键星级':star,'一键倍数':multi},'相似度':.9}};pc=1310
   def rk(x):return ks[x-256] if x>=256 else regs[x]
   for step in range(100):
    w=code[pc-1];op=w&63;a=(w>>6)&255;b=w>>23;c=(w>>14)&511;pc+=1
    if op==35:regs[a]=regs[b][rk(c)]
    elif op==34:regs[a]={'Find2':'find'}
    elif op==29:regs[a]=ks[w>>14]
    elif op==31:regs[a]=bool(b)
    elif op==19:
     if (rk(b)==rk(c))!=bool(a):pc+=1
    elif op==18:pc+=(w>>14)-131071
    elif op==43:
     self.assertEqual(regs[21],records[index]['definition'][5]);break
    else:self.fail(f'unhandled native opcode {op} at {pc-1}')
   else:self.fail('condition did not select a matcher')
 def test_quick_uses_exact_five_combination_templates(self):
  for star,multi,index in [(1,0,18),(1,1,19),(1,2,20),(0,1,21),(0,2,22)]:
   self.setUp();self.e.update(duelQuickStars=star,duelQuickMultiple=multi);self.p(index)
   self.assertTrue(self.e['DuelQuickCondition']());self.assertEqual(self.f.lookups,[f'081_P{index}'])
 def test_quick_seven_toggle_order_repeats_fourth252(self):
  self.p(17);self.f.after=lambda *a:setattr(self.f,'interrupt',len(self.f.taps)>=7)
  self.e['RefreshDuelQuick']();self.assertEqual(self.f.taps,[(560,500+y,0) for y in [114,188,252,252,114,188,252]])
 def test_quick_open_once_reappearing_main_exits_without_completion(self):
  self.p(8);self.assertEqual(self.e['RefreshDuelQuick'](),1);self.assertEqual(self.f.taps,[(360,1005,1000)])
  self.assertFalse(self.e['terminalConfirmed'])
 def test_quick_condition_stops_refresh_at_exact_anchor(self):
  self.e.update(duelQuickStars=1,duelQuickMultiple=0);self.p(18)
  self.f.after=lambda *a:self.p(8)
  self.assertEqual(self.e['RefreshDuelQuick'](),1);self.assertEqual(self.f.taps,[(362,820,500)])
 def test_battle_start_order1000_500_and11th_requests_restart(self):
  self.f.visible={'152_开战图标6'};self.assertEqual(self.e['RunDuelBattle'](),4)
  self.assertEqual(self.f.taps,[(398,982,1000),(587,982,500)]*11);self.assertFalse(self.e['terminalConfirmed']);self.assertFalse(self.e['duelTimedOut'])
 def test_battle_failure_end_choice_continues_confirmation_not_direct_commit(self):
  self.e['duelFailureMode']=0;self.f.visible={'152_开战图标6'}
  self.assertEqual(self.e['RunDuelBattle'](),1);self.assertFalse(self.e['terminalConfirmed'])
  self.assertTrue(self.e['duelEarlyStop'])
  proto=json.loads((ROOT/'flows/081_强者对决/evidence/root625原型.json').read_text('utf8'));w=proto['code'][1764]
  self.assertEqual(w&63,18);self.assertEqual(1766+(w>>14)-131071,1768)
 def test_skip50_plus1000_resets_starts_and_public_clock(self):
  self.f.visible={'078_跳过战斗'};self.f.after=lambda *a:self.f.visible.clear()
  self.e['BusinessExpired']=lambda:self.f.now>=2000;self.e['RunDuelBattle']()
  self.assertEqual(self.f.taps,[(290,993,50)]);self.assertEqual(self.e['duelWatchdogAt'],1100)
 def test_battle_result_wait500_click1000_is_only_phase_exit(self):
  self.p(25);self.assertEqual(self.e['RunDuelBattle'](),1);self.assertEqual(self.f.taps,[(600,900,1000)])
  self.assertFalse(self.e['terminalConfirmed']);self.assertEqual(self.e['duelWatchdogAt'],1560)
 def test_battle_completed_with_prophecy_is_not_task_terminal(self):
  self.e['duelProphecy']=1;self.p(5);self.assertEqual(self.e['RunDuelBattle'](),1);self.assertFalse(self.e['terminalConfirmed'])
 def test_battle_completed_without_prophecy_is_terminal(self):
  self.p(5);self.assertEqual(self.e['RunDuelBattle'](),1);self.assertTrue(self.e['terminalConfirmed'])
 def test_return_result_click0_and5ms_then_completed(self):
  self.p(25,5);self.assertEqual(self.e['ReturnDuelPage'](),1);self.assertEqual(self.f.taps,[(600,900,0)]);self.assertEqual(self.f.now,25)
 def test_return_gray1000_native_exit_even_when_prophecy_enabled(self):
  self.e['duelProphecy']=2;self.p(6);self.assertEqual(self.e['ReturnDuelPage'](),1);self.assertTrue(self.e['terminalConfirmed'])
 def test_unknown_return_never_completes(self):
  self.assertEqual(self.e['ReturnDuelPage'](),4);self.assertFalse(self.e['terminalConfirmed'])
 def test_prophecy_free_and_full_coordinates_only_configured_mode(self):
  for mode,x in [(1,193),(2,534)]:
   self.setUp();self.e['duelProphecy']=mode;self.p(28)
   self.f.after=lambda *a:self.p(32)
   self.assertEqual(self.e['RunDuelProphecy'](),1);self.assertEqual(self.f.taps,[(x,906,1000)])
   self.assertFalse(self.e['terminalConfirmed'])
 def test_prophecy_entry_other_button_rewards_and_exit_order(self):
  self.e['duelProphecy']=2;self.p(27,29,30,32)
  self.assertEqual(self.e['RunDuelProphecy'](),1)
  self.assertEqual(self.f.taps,[(561,130,500),(585,794,500),(600,900,500)])
 def test_free_prophecy_checks_close_immediately_not_after8sec(self):
  self.e['duelProphecy']=1;self.p(33);self.f.after=lambda *a:self.p(32)
  self.assertEqual(self.e['RunDuelProphecy'](),1);self.assertEqual(self.f.taps,[(600,900,0)]);self.assertLess(self.f.now,2000)
 def test_full_prophecy_strict8sec_close_not_timeout_or_completion(self):
  self.e['duelProphecy']=2;self.p(33);at=[]
  def after(*a):at.append(self.f.now);self.p(32)
  self.f.after=after;self.assertEqual(self.e['RunDuelProphecy'](),1)
  self.assertGreater(at[0],8500);self.assertFalse(self.e['terminalConfirmed'])
 def test_prophecy_blank_not_exhaustion_and_obtained_not_progress_reset(self):
  self.e['duelProphecy']=2;self.p(30)
  self.assertEqual(self.e['RunDuelProphecy'](),4);self.assertTrue(self.e['duelTimedOut']);self.assertFalse(self.e['terminalConfirmed'])
 def prepare_execute(self,mode=2):
  self.e['EnterGatherHall']=lambda:1
  def entry():self.e['duelEntryMode']=mode;return 1
  self.e['EnterDuel']=entry
 def test_execute_manual_and_quick_mutually_exclusive(self):
  for star,multi,path in [(0,0,'manual'),(1,0,'quick'),(0,1,'quick')]:
   self.setUp();self.prepare_execute();self.e.update(duelQuickStars=star,duelQuickMultiple=multi);calls=[]
   self.e.update(RefreshDuelManual=lambda:calls.append('manual') or 4,RefreshDuelQuick=lambda:calls.append('quick') or 4)
   self.assertEqual(self.e['ExecuteDuel'](),4);self.assertEqual(calls,[path])
 def test_execute_mode1_skips_refresh_and_battle_goes_prophecy(self):
  self.prepare_execute(1);self.e['duelProphecy']=1;self.e['RunDuelProphecy']=lambda:1
  self.e['RunDuelBattle']=lambda:self.fail('already completed');self.e['RefreshDuelManual']=lambda:self.fail('already completed')
  self.assertEqual(self.e['ExecuteDuel'](),1);self.assertEqual(self.f.now,500);self.assertTrue(self.e['terminalConfirmed'])
 def test_execute_failure_does_not_enter_return_or_prophecy(self):
  self.prepare_execute();self.e.update(RefreshDuelManual=lambda:1,RunDuelBattle=lambda:4,ReturnDuelPage=lambda:self.fail('failed battle'))
  self.assertEqual(self.e['ExecuteDuel'](),4);self.assertFalse(self.e['terminalConfirmed'])
 def test_all_phases_interruption_no_click_no_done(self):
  for name in ['EnterDuel','RefreshDuelManual','RefreshDuelQuick','RunDuelBattle','ReturnDuelPage','RunDuelProphecy']:
   self.setUp();self.f.interrupt=True;self.p(0,5,32)
   self.assertEqual(self.e[name](),4);self.assertFalse(self.f.taps);self.assertFalse(self.swipes);self.assertFalse(self.e['terminalConfirmed'])
 def public(self):
  load(['common/任务状态.mq','common/任务注册.mq','common/任务调度.mq'],self.e)
  self.e['RegisterTasks']();self.e['NewSession']();self.e['SaveCurrentTask'](81)
 def test_terminal_hall_and_foreground_commit_guards(self):
  self.public();self.assertFalse(self.e['CommitTask'](True));self.e['ConfirmDuelTerminal']('完成')
  self.assertFalse(self.e['CommitTask'](False));self.e['BeginForegroundCommit']=lambda:False;self.assertFalse(self.e['CommitTask'](True))
  self.e['BeginForegroundCommit']=lambda:True;self.assertTrue(self.e['CommitTask'](True));self.assertEqual(self.e['duelCount'],1)
 def test_resume81_not_discarded_by_disabled_checkbox(self):
  self.public();self.e['duelEnabled']=False;self.assertEqual(self.e['SelectDueTask'](),81)
 def test_timeout_count_once_limit2_abandon_not_win(self):
  self.public();self.e['duelTimedOut']=True;self.e['SaveRecovery']();self.e['SaveRecovery']();self.assertEqual(self.e['duelFailures'],1)
  self.e['SaveCurrentTask'](81);self.e['duelTimedOut']=True;self.e['SaveRecovery']()
  self.assertTrue(self.e['duelAbandoned']);self.assertEqual(self.e['resumeTask'],0);self.assertEqual(self.e['duelCount'],0);self.assertFalse(self.e['duelDone'])
 def test_early_stop_native_done_does_not_repeat_on_return_failure(self):
  self.public();self.e['duelEarlyStop']=True;self.e['SaveRecovery']()
  self.assertTrue(self.e['duelAbandoned']);self.assertEqual(self.e['resumeTask'],0);self.assertEqual(self.e['SelectDuel'](),0)
  self.assertEqual(self.e['duelCount'],0);self.assertFalse(self.e['terminalConfirmed'])
 def test_confirmed_native_exit_survives_hall_failure_no_repeat_paid_work(self):
  self.public();self.e['ConfirmDuelTerminal']('原已完成出口');self.e['SaveRecovery']();self.e['SaveCurrentTask'](81)
  self.e['EnterGatherHall']=lambda:self.fail('native done must not replay business')
  self.assertEqual(self.e['ExecuteDuel'](),1);self.assertEqual(self.e['duelCount'],0)
  self.assertTrue(self.e['CommitTask'](True));self.assertEqual(self.e['duelCount'],1);self.assertFalse(self.e['duelPendingTerminal'])
 def test_foreground_before_terminal_does_not_cache_unconfirmed_done(self):
  self.f.interrupt=True;self.assertEqual(self.e['ConfirmDuelTerminal']('猜测完成'),4);self.assertFalse(self.e['duelPendingTerminal'])
 def test_watchdog_strict_limit_and_late_progress_latched(self):
  self.f.now=120000;self.assertFalse(self.e['BusinessExpired']());self.f.now+=1;self.e['DuelProgress']()
  self.assertTrue(self.e['BusinessExpired']());self.assertTrue(self.e['duelTimedOut'])
 def test_public_80_81_progress_does_not_change_other_budget(self):
  self.e.update(currentTask=82);self.f.now=120000;self.e['DuelProgress']();self.assertTrue(self.e['BusinessExpired']())
 def test_hall_delay_scoped_to81(self):
  load(['common/大厅清障.mq'],self.e);self.e.update(duelHallDelay=0,hallReturnDelaySeconds=7)
  self.assertEqual(self.e['HallActionWait'](),1000);self.e['duelHallDelay']=2;self.assertEqual(self.e['HallActionWait'](),2000)
  self.e['currentTask']=82;self.assertEqual(self.e['HallActionWait'](),7000)
 def test_scheduler_success_actual_public_commit(self):
  self.public();events=[]
  self.e.update(EnsureGameHall=lambda:1,DispatchTask=lambda t:self.e['ConfirmDuelTerminal']('完成'),ReturnToHall=lambda:1,RestartGame=lambda:events.append('restart'))
  self.e['SchedulerStep']();self.assertFalse(events);self.assertEqual(self.e['duelCount'],1);self.assertEqual(self.e['resumeTask'],0)
 def test_scheduler_hall_failure_no_commit_and_failure_count(self):
  self.public();events=[]
  self.e.update(EnsureGameHall=lambda:1,DispatchTask=lambda t:self.e['ConfirmDuelTerminal']('完成'),ReturnToHall=lambda:4,RestartGame=lambda:events.append('restart'))
  self.e['SchedulerStep']();self.assertEqual(events,['restart']);self.assertEqual(self.e['duelCount'],0);self.assertEqual(self.e['duelFailures'],1)
 def test_timeout_false_with_running_game_returns_without_kill(self):
  self.public();self.e['duelRestartOnTimeout']=False;events=[]
  def dispatch(t):self.e['duelTimedOut']=True;return 4
  self.e.update(EnsureGameHall=lambda:1,DispatchTask=dispatch,ReturnToHall=lambda:events.append('hall') or 1,RestartGame=lambda:events.append('restart'))
  self.e['SchedulerStep']();self.assertEqual(events,['hall']);self.assertEqual(self.e['resumeTask'],81);self.assertEqual(self.e['currentTask'],0)
 def test_actual_foreground_recovery_preserves81_and_no_timeout_count(self):
  from test_foreground import Foreground
  fg=Foreground();fg.setUp();fg.e.update(Time=lambda:1760000000,duelIdleLimit=120000,duelFailureLimit=2,duelRestartOnTimeout=True)
  load(['common/强者对决状态.mq'],fg.e);fg.e['WorldLog']=fg.logs.append;fg.e['NewDuelSession']();fg.e['SaveCurrentTask'](81);fg.request()
  self.assertTrue(fg.e['HandleForegroundRecovery']());self.assertEqual(fg.e['resumeTask'],81);self.assertEqual(fg.e['SelectDueTask'](),81)
  self.assertEqual((fg.e['duelRestarts'],fg.e['duelRecoveries'],fg.e['duelFailures'],fg.e['duelCount']),(1,1,0,0))
 def test_log_attribution_only81(self):
  before=self.e['worldPhase'];self.e['WorldStage']('强者预言');self.assertEqual(self.e['worldPhase'],before);self.assertEqual(self.e['duelPhase'],'强者预言');self.assertIn('强者对决81',self.f.logs[-1])
 def test_original_ui_five_controls_and_options_default_zero(self):
  t=(ROOT/'ui/最小配置.uip').read_text('utf-8-sig')
  self.assertIn('名称:"日常_强者对决",提示内容:"强者对决[",选中:false',t)
  for key,options in [('星级','"免费3星","免费4星","龙石4星","龙石5星",'),('预言','"不抽","抽免费","抽满",'),('一键刷新_星级','"关闭","五星",'),('一键刷新_倍数','"关闭","二倍","三倍",')]:
   self.assertIn('名称:"日常_强者对决_'+key+'",选项:['+options+'],初始选项:0',t)
 def test_exact34_native_patterns_and_mq_registration(self):
  ev=ROOT/'flows/081_强者对决/evidence';rows=json.loads((ev/'图色唯一参数.json').read_text('utf8'));records=json.loads((ev/'图色转换.json').read_text('utf8'))
  self.assertEqual(len(rows),34);self.assertEqual(rows,[r['definition'] for r in records])
  cat=json.loads((ROOT/'evidence/图色参数.json').read_text('utf8'));self.assertEqual([r for r in cat if r['name'].startswith('081_')],records)
  text=(ROOT/'common/图色参数.mq').read_text('utf-8-sig')
  for r in records:
   body=re.search(r'Case "'+r['name']+r'"(.*?)(?=\n    Case |\n    End Select)',text,re.S)[1]
   self.assertIn('FindMultiColor '+', '.join(json.dumps(v) for v in r['definition'])+', foundX, foundY',body)
 def test_no_new_version_api_or_business_public_mutation(self):
  t=(ROOT/'flows/081_强者对决/强者对决.mq').read_text('utf-8-sig');self.assertNotRegex(t,r'OcrEx|paddle|Image\.Ocr|KillApp|RunApp|CommitTask|SchedulerStep|InStr|businessStarted\s*=')
 def test_build_and_assistant_protected_files_unchanged(self):
  ev=ROOT/'flows/081_强者对决/evidence';base=json.loads((ev/'禁止构建同步基线.json').read_text('utf8'));self.assertEqual(len(base),8)
  from sync_boundary import authorized_sync_baseline
  base=authorized_sync_baseline(base)
  for p,h in base.items():self.assertEqual(hashlib.sha256(Path(p).read_bytes()).hexdigest(),h,p)

if __name__=='__main__':unittest.main()
