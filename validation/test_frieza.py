import hashlib,json,re,unittest
from pathlib import Path
from mq_subset import ROOT,load

class FriezaTests(unittest.TestCase):
 def setUp(self):
  from test_worldboss import WorldBossTests
  self.f=WorldBossTests();self.f.setUp();self.f.at(12);self.e=self.f.e
  self.e['Sys'].IsRunning=lambda p:True
  def match(n):self.f.now+=10;return self.f.match(n)
  self.e.update(MatchPattern=match,currentTask=80,friezaEnabled=True,friezaFailureMode=1,friezaIdleLimit=120000,friezaFailureLimit=2,friezaRestartOnTimeout=True,businessStarted=0,businessLimit=120000,ForegroundInterrupted=lambda:self.f.interrupt)
  load(['common/弗利萨状态.mq','common/运行计时.mq','flows/080_弗利萨军团/弗利萨军团.mq'],self.e)
  self.e['NewFriezaSession']();self.e['friezaRunning']=True;self.e['FriezaProgress']()
 def test_professional_config_defaults(self):
  self.e['ReadUIConfig']=lambda k,d:d;self.e['LoadFriezaSettings']()
  self.assertFalse(self.e['friezaEnabled']);self.assertEqual(self.e['friezaFailureMode'],1)
  self.assertEqual((self.e['friezaIdleLimit'],self.e['friezaFailureLimit'],self.e['friezaRestartOnTimeout']),(120000,2,True))
 def test_exact_config_keys_and_false_string(self):
  settings={'日常_弗利萨军团':'true','设置_重要_开战失败':0,'设置_重连_超时时间':300,'设置_重要_任务失败上限':4,'设置_重要_闪退':'false'}
  self.e['ReadUIConfig']=lambda k,d:settings.get(k,d);self.e['LoadFriezaSettings']()
  self.assertTrue(self.e['friezaEnabled']);self.assertEqual(self.e['friezaFailureMode'],0)
  self.assertEqual((self.e['friezaIdleLimit'],self.e['friezaFailureLimit'],self.e['friezaRestartOnTimeout']),(300000,4,False))
 def test_professional_hall_delay_zero_and_positive_only80(self):
  load(['common/大厅清障.mq'],self.e);self.e.update(friezaHallDelay=0,hallReturnDelaySeconds=9)
  self.assertEqual(self.e['HallActionWait'](),1000);self.e['friezaHallDelay']=3;self.assertEqual(self.e['HallActionWait'](),3000)
  self.e['currentTask']=79;self.assertEqual(self.e['HallActionWait'](),9000)
 def test_config_invalid_values_and_zero_preserved(self):
  for v in ['bad',-1,10000]:
   self.e['ReadUIConfig']=lambda k,d:v;self.e['LoadFriezaSettings']();self.assertEqual(self.e['friezaIdleLimit'],120000);self.assertEqual(self.e['friezaFailureLimit'],2)
  self.e['ReadUIConfig']=lambda k,d:0;self.e['LoadFriezaSettings']();self.assertEqual(self.e['friezaIdleLimit'],0);self.assertEqual(self.e['friezaFailureLimit'],0)
 def test_selection_and_completion_lock_no_imaginary_interval(self):
  self.assertEqual(self.e['SelectFrieza'](),80);self.e['CommitFriezaTask']();self.f.stamp+=86400
  self.assertEqual(self.e['SelectFrieza'](),0);self.e['NewFriezaSession']();self.assertEqual(self.e['SelectFrieza'](),80)
  self.e['friezaAbandoned']=True;self.assertEqual(self.e['SelectFrieza'](),0)
 def test_entry_priority_entrance_then_unopened_not_done(self):
  self.f.visible={'080_入口','080_未开启一','080_已完成','080_基地界面'}
  self.assertEqual(self.e['EnterFrieza'](),1);self.assertEqual(self.f.taps,[(600,900,200)])
  self.assertIn('未开启',self.e['friezaReason']);self.assertNotIn('080_已完成',self.f.lookups);self.assertEqual(self.f.now,420)
 def test_unopened_two_variants_and_no_click(self):
  for name in ['080_未开启一','080_未开启二']:
   self.setUp();self.f.visible={name};self.assertEqual(self.e['EnterFrieza'](),1)
   self.assertFalse(self.f.taps);self.assertTrue(self.e['terminalConfirmed']);self.assertEqual(self.e['friezaCount'],0)
 def test_completed_entry_has200_wait_not_notification1000(self):
  self.f.visible={'080_已完成'};self.assertEqual(self.e['EnterFrieza'](),1)
  self.assertEqual(self.f.now,240);self.assertFalse(self.f.taps)
 def test_entry_three_modes_and50ms_spacing(self):
  for n,mode,t in [('080_基地界面',1,250),('080_旧关入口一',2,310),('080_旧关入口二',2,320),('080_新关入口',3,380)]:
   self.setUp();self.f.visible={n};self.assertEqual(self.e['EnterFrieza'](),1)
   self.assertEqual(self.e['friezaEntryMode'],mode);self.assertEqual(self.f.now,t);self.assertFalse(self.e['terminalConfirmed'])
 def test_unknown_entry_only_watchdog_not_unopened_or_done(self):
  self.assertEqual(self.e['EnterFrieza'](),4);self.assertGreater(self.f.now,120000)
  self.assertTrue(self.e['friezaTimedOut']);self.assertFalse(self.e['terminalConfirmed'])
 def test_old_green_click_does_not_reset10sec_stage(self):
  self.f.visible={'080_旧关绿色一'}
  self.e['BusinessExpired']=lambda:self.f.now>=12000
  self.e['RunFriezaOld']();self.assertEqual(self.f.taps,[(600,900,200)]*14)
  self.assertIn('旧关后返回',self.e['friezaPhase']);self.assertFalse(self.e['terminalConfirmed'])
 def test_old_blue_resets_local_before200_wait_not_public(self):
  self.f.visible={'080_旧关蓝色一'}
  self.e['RunFriezaOld']();self.assertEqual(self.e['friezaPhase'],'弗利萨军团旧关处理')
  self.assertGreater(self.f.now,120000);self.assertEqual(self.e['friezaWatchdogAt'],0);self.assertFalse(self.e['terminalConfirmed'])
 def test_old_confirm_wait1500_then_second_pass200_then_done(self):
  self.f.visible={'080_旧关确定一','080_已完成'}
  self.assertEqual(self.e['RunFriezaOld'](),1);self.assertEqual(self.f.taps,[(600,900,0),(600,900,200)])
  self.assertEqual(self.e['friezaWatchdogAt'],1550);self.assertEqual(self.f.now,1990)
 def test_old_unknown10sec_transitions_not_completes(self):
  self.e['BusinessExpired']=lambda:self.f.now>=11000;self.e['RunFriezaOld']()
  self.assertIn('旧关后返回',self.e['friezaPhase']);self.assertFalse(self.e['terminalConfirmed'])
 def test_old_base_return_wait200_mode1_not_completed(self):
  self.f.visible={'080_旧关确定二','080_基地界面'};self.e['friezaEntryMode']=2
  self.assertEqual(self.e['RunFriezaOld'](),1);self.assertEqual(self.e['friezaEntryMode'],1);self.assertFalse(self.e['terminalConfirmed'])
 def test_auto_triple_ready_priority_no_extra3000(self):
  self.f.visible={'086_三倍已就绪','086_开启自动'}
  self.assertTrue(self.e['FriezaAutoTriple']());self.assertFalse(self.f.taps);self.assertEqual(self.f.now,10)
 def test_auto_triple_three_exact_offsets_false_until_ready(self):
  for n,x,y in [('086_开启自动',290,1070),('086_开启三倍',918,992),('086_战斗基准',918,916)]:
   self.setUp();self.f.visible={n};self.assertFalse(self.e['FriezaAutoTriple']());self.assertEqual(self.f.taps,[(x,y,50)])
 def test_new_actions_exact_order_then_done(self):
  self.f.visible={'080_新关入口','080_新关挑战','080_新关获得','152_开战图标6','086_三倍已就绪','080_已完成'}
  self.assertEqual(self.e['RunFriezaNew'](),1)
  self.assertEqual(self.f.taps,[(355,1100,500),(514,760,500),(150,50,500),(398,982,500),(587,982,500)])
  self.assertEqual(self.f.now,3260);self.assertEqual(self.e['friezaWatchdogAt'],3050)
 def test_new_base_transition_does_not_complete(self):
  self.f.visible={'080_基地界面'};self.assertEqual(self.e['RunFriezaNew'](),1);self.assertFalse(self.e['terminalConfirmed'])
 def test_new_opening_attempts_do_not_reset_public_timer(self):
  self.f.visible={'152_开战图标6'};self.assertEqual(self.e['RunFriezaNew'](),4)
  self.assertTrue(self.e['friezaTimedOut']);self.assertEqual(self.e['friezaWatchdogAt'],0);self.assertFalse(self.e['terminalConfirmed'])
 def test_native360sec_reachable_with_real_progress_and_no_false_done(self):
  self.f.visible={'086_三倍已就绪'};self.assertEqual(self.e['RunFriezaNew'](),4)
  self.assertGreater(self.f.now,360000);self.assertLess(self.f.now,361000)
  self.assertTrue(self.e['friezaTimedOut']);self.assertIn('360秒',self.e['friezaReason']);self.assertFalse(self.e['terminalConfirmed'])
 def test_base_full_action_order_and_end_not_terminal(self):
  self.f.visible={'080_基地界面','080_探索一','080_触发战斗二','152_开战图标6','078_跳过战斗','080_基地结束一'}
  self.assertEqual(self.e['RunFriezaBase'](),1)
  self.assertEqual(self.f.taps,[(467,134,200),(600,900,200),(600,900,200),(398,982,500),(587,982,500),(290,993,50),(600,900,0)])
  self.assertFalse(self.e['terminalConfirmed']);self.assertEqual(self.e['friezaWatchdogAt'],3710)
 def test_base_pair_priority_first_variant_anchor(self):
  self.f.visible={'080_基地结束一','080_基地结束二'};self.assertEqual(self.e['RunFriezaBase'](),1)
  self.assertNotIn('080_基地结束二',self.f.lookups);self.assertEqual(self.f.taps,[(600,900,0)])
 def test_native_counter_only_zero_stores_no_increment(self):
  p=json.loads((ROOT/'flows/080_弗利萨军团/evidence/root624原型.json').read_text('utf8'))
  writes=[]
  for pc,w in enumerate(p['code'],1):
   if pc>=32 and (w>>6)&255==4 and (w&63) in [28,29,30,31,32,34,35,8,9,10,11,12,13,14,15,16,17]:writes.append((pc,w))
  self.assertEqual([pc for pc,w in writes],[32,1011,1071,1131,1192])
  for pc,w in writes:self.assertEqual(w&63,29);self.assertEqual(p['constants'][w>>14],0)
  text=(ROOT/'flows/080_弗利萨军团/弗利萨军团.mq').read_text('utf-8-sig')
  self.assertNotRegex(text,r'counter\s*=\s*counter\s*\+')
 def test_base_repeated_starts_do_not_invent_failure_count(self):
  self.f.visible={'152_开战图标6'};self.assertEqual(self.e['RunFriezaBase'](),4)
  self.assertGreater(len(self.f.taps),20);self.assertFalse(self.e['friezaTerminal']);self.assertEqual(self.e['friezaFailures'],0)
 def test_latent_base_failure_guard_strict10_and_config(self):
  self.assertEqual(self.e['FriezaBaseFailure'](10),2)
  self.assertEqual(self.e['FriezaBaseFailure'](11),4);self.assertFalse(self.e['terminalConfirmed'])
  self.e['friezaFailureMode']=0;self.assertEqual(self.e['FriezaBaseFailure'](11),1);self.assertIn('不是胜利',self.e['friezaReason'])
 def test_final_confirmation_200_plus500_not_popup2000(self):
  self.f.visible={'080_已完成'};self.assertEqual(self.e['FinishFrieza'](),1)
  self.assertEqual(self.f.now,730);self.assertFalse(self.f.taps)
 def test_final_end_click_refresh_then200_then_done(self):
  self.f.visible={'080_基地结束二','080_已完成'};self.assertEqual(self.e['FinishFrieza'](),1)
  self.assertEqual(self.f.taps,[(600,900,0)]);self.assertEqual(self.e['friezaWatchdogAt'],20);self.assertEqual(self.f.now,930)
 def test_final_end_missing_done_never_commits_on_disappearance(self):
  self.f.visible={'080_基地结束一'};self.f.after=lambda *a:self.f.visible.clear()
  self.assertEqual(self.e['FinishFrieza'](),4);self.assertFalse(self.e['terminalConfirmed']);self.assertEqual(self.e['friezaCount'],0)
 def test_execute_old_success_still_needs_base_and_final(self):
  self.e['EnterGatherHall']=lambda:1;self.f.visible={'080_旧关入口一'};calls=[]
  def old():calls.append('old');self.e['friezaEntryMode']=1;return 1
  self.e.update(RunFriezaOld=old,RunFriezaBase=lambda:calls.append('base') or 1,FinishFrieza=lambda:calls.append('final') or 1)
  self.assertEqual(self.e['ExecuteFrieza'](),1);self.assertEqual(calls,['old','base','final'])
 def test_execute_new_timeout_never_enters_base(self):
  self.e['EnterGatherHall']=lambda:1;self.f.visible={'080_新关入口'}
  self.e['RunFriezaNew']=lambda:4;self.e['RunFriezaBase']=lambda:self.fail('new failure cannot enter base')
  self.assertEqual(self.e['ExecuteFrieza'](),4)
 def test_execute_unopened_skips_all_business_stages(self):
  self.e['EnterGatherHall']=lambda:1;self.f.visible={'080_未开启二'}
  self.e['RunFriezaBase']=lambda:self.fail('unopened');self.assertEqual(self.e['ExecuteFrieza'](),1)
 def test_watchdog_strict_boundary_and_explicit_progress(self):
  self.f.now=120000;self.assertFalse(self.e['BusinessExpired']());self.f.now+=1;self.assertTrue(self.e['BusinessExpired']())
  self.e['FriezaProgress']();self.assertTrue(self.e['BusinessExpired']())
 def test_progress_before_deadline_renews_only80_watchdog(self):
  self.f.now=119999;self.e['FriezaProgress']();self.f.now=200000
  self.assertFalse(self.e['BusinessExpired']());self.assertFalse(self.e['friezaTimedOut'])
 def test_late_progress_cannot_revive_expired_budget_without_poll(self):
  self.f.now=120001;self.e['FriezaProgress']();self.assertTrue(self.e['BusinessExpired']())
  self.assertTrue(self.e['friezaTimedOut']);self.assertFalse(self.e['terminalConfirmed'])
 def test_other_task_deadline_and_progress_unchanged(self):
  for t in [70,79,82]:
   self.e['currentTask']=t;self.f.now=120000
   # 79 now uses its evidenced strict-greater public timer boundary.
   self.assertEqual(self.e['BusinessExpired'](),t!=79)
   self.f.now=120001;self.assertTrue(self.e['BusinessExpired']())
   self.e['FriezaProgress']();self.assertTrue(self.e['BusinessExpired']())
 def test_interruption_all_stages_no_action_or_terminal(self):
  for name in ['EnterFrieza','RunFriezaOld','RunFriezaNew','RunFriezaBase','FinishFrieza']:
   self.setUp();self.f.interrupt=True;self.f.visible={'080_已完成','080_未开启一'}
   self.assertEqual(self.e[name](),4);self.assertFalse(self.f.taps);self.assertFalse(self.e['terminalConfirmed']);self.assertFalse(self.e['friezaTimedOut'])
 def public(self):
  load(['common/任务状态.mq','common/任务注册.mq','common/任务调度.mq'],self.e)
  self.e['RegisterTasks']();self.e['NewSession']();self.e['SaveCurrentTask'](80)
 def test_actual_dispatch_task80(self):
  load(['common/任务分派.mq'],self.e);self.e['EnterGatherHall']=lambda:1;self.f.visible={'080_已完成'}
  self.assertEqual(self.e['DispatchTask'](80),1);self.assertTrue(self.e['terminalConfirmed']);self.assertEqual(self.e['friezaCount'],0)
 def test_public_terminal_hall_and_foreground_commit_gates(self):
  self.public();self.assertFalse(self.e['CommitTask'](True));self.e['ConfirmFriezaTerminal']('已完成')
  self.assertFalse(self.e['CommitTask'](False));self.e['BeginForegroundCommit']=lambda:False;self.assertFalse(self.e['CommitTask'](True))
  self.e['BeginForegroundCommit']=lambda:True;self.assertTrue(self.e['CommitTask'](True));self.assertEqual(self.e['friezaCount'],1)
 def test_resume_preserves80_even_when_disabled(self):
  self.public();self.e['friezaEnabled']=False;self.assertEqual(self.e['SelectDueTask'](),80)
 def test_recovery_timeout_count_once_and_limit2_abandon_not_success(self):
  self.public();self.e['friezaTimedOut']=True;self.e['SaveRecovery']();self.e['SaveRecovery']()
  self.assertEqual(self.e['friezaFailures'],1);self.assertEqual(self.e['resumeTask'],80)
  self.e['SaveCurrentTask'](80);self.e['friezaTimedOut']=True;self.e['SaveRecovery']()
  self.assertEqual(self.e['friezaFailures'],2);self.assertTrue(self.e['friezaAbandoned']);self.assertFalse(self.e['friezaDone'])
  self.assertEqual(self.e['friezaCount'],0);self.assertEqual(self.e['resumeTask'],0);self.assertEqual(self.e['SelectFrieza'](),0)
 def test_foreground_recovery_not_timeout_failure(self):
  self.public();self.f.interrupt=True;self.e['SaveRecovery']()
  self.assertEqual(self.e['friezaFailures'],0);self.assertEqual(self.e['resumeTask'],80);self.assertFalse(self.e['friezaAbandoned'])
 def scheduler_timeout(self,restart,hall=1):
  self.public();events=[];self.e['friezaRestartOnTimeout']=restart
  def dispatch(t):self.e['friezaTimedOut']=True;return 4
  self.e.update(EnsureGameHall=lambda:1,DispatchTask=dispatch,ReturnToHall=lambda:events.append('hall') or hall,RestartGame=lambda:events.append('restart'))
  self.e['SchedulerStep']();return events
 def test_timeout_restart_true_uses_public_restart(self):
  self.assertEqual(self.scheduler_timeout(True),['restart']);self.assertEqual(self.e['resumeTask'],80);self.assertEqual(self.e['friezaFailures'],1)
 def test_timeout_restart_false_keeps_game_and_resumes_after_hall(self):
  self.assertEqual(self.scheduler_timeout(False),['hall']);self.assertEqual(self.e['resumeTask'],80);self.assertEqual(self.e['currentTask'],0)
 def test_timeout_false_hall_failure_never_claims_commit_or_forces_kill(self):
  self.assertEqual(self.scheduler_timeout(False,4),['hall']);self.assertEqual(self.e['resumeTask'],80);self.assertFalse(self.e['friezaDone'])
 def test_timeout_false_still_restarts_missing_game_like_public_handler(self):
  self.e['Sys'].IsRunning=lambda p:False
  self.assertEqual(self.scheduler_timeout(False),['restart'])
 def test_success_scheduler_hall_and_commit(self):
  self.public();events=[]
  self.e.update(EnsureGameHall=lambda:1,ReturnToHall=lambda:1,DispatchTask=lambda t:self.e['ConfirmFriezaTerminal']('已完成'),RestartGame=lambda:events.append('restart'))
  self.e['SchedulerStep']();self.assertFalse(events);self.assertEqual(self.e['friezaCount'],1);self.assertEqual(self.e['resumeTask'],0)
 def test_scheduler_terminal_but_hall_timeout_counts_failure_not_completion(self):
  self.public();events=[]
  self.e.update(EnsureGameHall=lambda:1,ReturnToHall=lambda:4,DispatchTask=lambda t:self.e['ConfirmFriezaTerminal']('已完成'),RestartGame=lambda:events.append('restart'))
  self.e['SchedulerStep']();self.assertEqual(events,['restart']);self.assertEqual(self.e['friezaFailures'],1)
  self.assertEqual(self.e['friezaCount'],0);self.assertFalse(self.e['friezaDone']);self.assertEqual(self.e['resumeTask'],80)
 def test_mode1_direct_base_does_not_enter_old_or_new(self):
  self.e['EnterGatherHall']=lambda:1;self.f.visible={'080_基地界面'};calls=[]
  self.e.update(RunFriezaOld=lambda:self.fail('mode1'),RunFriezaNew=lambda:self.fail('mode1'),RunFriezaBase=lambda:calls.append('base') or 1,FinishFrieza=lambda:calls.append('final') or 1)
  self.assertEqual(self.e['ExecuteFrieza'](),1);self.assertEqual(calls,['base','final'])
 def test_generic_entry_timeout_counts_but_foreground_interruption_does_not(self):
  self.e['EnterGatherHall']=lambda:4;self.assertEqual(self.e['ExecuteFrieza'](),4);self.assertTrue(self.e['friezaTimedOut'])
  self.setUp();self.f.interrupt=True;self.e['EnterGatherHall']=lambda:4
  self.assertEqual(self.e['ExecuteFrieza'](),4);self.assertFalse(self.e['friezaTimedOut'])
 def test_actual_foreground_monitor_routes80(self):
  from test_foreground import Foreground
  fg=Foreground();fg.setUp();fg.e.update(Time=lambda:1760000000,friezaIdleLimit=120000,friezaFailureLimit=2,friezaRestartOnTimeout=True)
  load(['common/弗利萨状态.mq'],fg.e);fg.e['WorldLog']=fg.logs.append;fg.e['NewFriezaSession']();fg.e['SaveCurrentTask'](80);fg.request()
  self.assertTrue(fg.e['HandleForegroundRecovery']());self.assertEqual(fg.e['resumeTask'],80);self.assertEqual(fg.e['SelectDueTask'](),80)
  self.assertEqual((fg.e['friezaRestarts'],fg.e['friezaRecoveries'],fg.e['friezaFailures'],fg.e['friezaCount']),(1,1,0,0))
  self.assertEqual(fg.events,[('kill','game'),('run','game')])
 def test_log_phase80_not_world70(self):
  before=self.e['worldPhase'];self.e['WorldStage']('秘密基地');self.assertEqual(self.e['worldPhase'],before)
  self.assertEqual(self.e['friezaPhase'],'秘密基地');self.assertIn('弗利萨军团80',self.f.logs[-1])
 def test_ui_original_key_default_and_same_row_memory(self):
  t=(ROOT/'ui/最小配置.uip').read_text('utf-8-sig')
  self.assertIn('名称:"日常_弗利萨军团",提示内容:"弗利萨军团     ",选中:false,文字大小:10',t)
  row=next(x for x in t.splitlines() if '名称:"日常_弗利萨军团"' in x);self.assertIn('名称:"日常_战士记忆"',row)
  for key in ['设置_重连_超时时间','设置_重要_任务失败上限','设置_重要_闪退','设置_重要_开战失败','设置_重要_返回大厅延迟']:self.assertEqual(t.count('名称:"'+key+'"'),1)
 def test_exact22_original_patterns_and_fixed_regions(self):
  ev=ROOT/'flows/080_弗利萨军团/evidence';rows=json.loads((ev/'图色唯一参数.json').read_text('utf8'));records=json.loads((ev/'图色转换.json').read_text('utf8'))
  self.assertEqual(len(rows),22);self.assertEqual(rows,[r['definition'] for r in records])
  cat=json.loads((ROOT/'evidence/图色参数.json').read_text('utf8'));self.assertEqual([r for r in cat if r['name'].startswith('080_')],records)
  self.assertEqual(rows[14][:4],[14,369,698,843]);self.assertEqual(rows[15][:4],[112,335,626,496])
  text=(ROOT/'common/图色参数.mq').read_text('utf-8-sig')
  for r in records:
   body=re.search(r'Case "'+r['name']+r'"(.*?)(?=\n    Case |\n    End Select)',text,re.S)[1]
   self.assertIn('FindMultiColor '+', '.join(json.dumps(v) for v in r['definition'])+', foundX, foundY',body)
 def test_no_new_api_or_business_public_mutation(self):
  t=(ROOT/'flows/080_弗利萨军团/弗利萨军团.mq').read_text('utf-8-sig')
  self.assertNotRegex(t,r'OcrEx|paddle|Image\.Ocr|KillApp|RunApp|CommitTask|SchedulerStep|InStr|businessStarted\s*=')
 def test_protected_build_and_assistant_unchanged(self):
  baseline=json.loads((ROOT/'flows/080_弗利萨军团/evidence/禁止构建同步基线.json').read_text('utf8'))
  from sync_boundary import authorized_sync_baseline
  baseline=authorized_sync_baseline(baseline)
  self.assertEqual(len(baseline),8)
  for p,h in baseline.items():self.assertEqual(hashlib.sha256(Path(p).read_bytes()).hexdigest(),h,p)

if __name__=='__main__':unittest.main()
