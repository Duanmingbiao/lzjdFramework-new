import hashlib,json,re,unittest
from mq_subset import ROOT,load

class MemoryTests(unittest.TestCase):
 def setUp(self):
  from test_worldboss import WorldBossTests
  self.f=WorldBossTests();self.f.setUp();self.f.at(12);self.e=self.f.e
  def match(n):
   self.f.now+=10
   # Ordinary portrait anchors must permit the exact original negative offsets.
   v=self.f.match(n)
   if n!='078_跳过战斗':self.e['foundX']=100;self.e['foundY']=1200
   return v
  self.e['MatchPattern']=match
  self.e.update(currentTask=82,memoryEnabled=True,memoryFailureMode=1,memoryInitial=0)
  load(['common/战士记忆状态.mq','flows/082_战士记忆/战士记忆.mq'],self.e)
  self.e['NewMemorySession']()
 def test_config_exact_one_checkbox_and_shared_selector(self):
  self.e['ReadUIConfig']=lambda k,d:{'日常_战士记忆':'true','设置_重要_开战失败':0}.get(k,d)
  self.e['LoadMemorySettings']();self.assertTrue(self.e['memoryEnabled']);self.assertEqual(self.e['memoryFailureMode'],0)
  self.e['ReadUIConfig']=lambda k,d:d;self.e['LoadMemorySettings']()
  self.assertFalse(self.e['memoryEnabled']);self.assertEqual(self.e['memoryFailureMode'],1)
 def test_selection_latch_and_no_invented_daily_reset(self):
  self.assertEqual(self.e['SelectMemory'](),82);self.e['CommitMemoryTask']();self.f.stamp+=86400
  self.assertEqual(self.e['SelectMemory'](),0);self.e['NewMemorySession']();self.assertEqual(self.e['SelectMemory'](),82)
 def test_unopened_200ms_no_click_no_commit(self):
  self.f.visible={'082_未开启'};self.assertEqual(self.e['EnterMemory'](),1)
  self.assertEqual(self.f.now,210);self.assertFalse(self.f.taps);self.assertTrue(self.e['memoryTerminal']);self.assertEqual(self.e['memoryCount'],0)
 def test_five_states_in_original_priority(self):
  for state in range(5):
   self.setUp();self.f.visible={f'082_完成状态{i}' for i in range(state,5)}
   self.assertEqual(self.e['EnterMemory'](),1);self.assertEqual(self.e['memoryInitial'],state)
   self.assertFalse(self.e['terminalConfirmed']);self.assertEqual(self.f.now,230+10*state)
 def test_entry_anchor200_and_timer_refresh_not_arbitrary_exit(self):
  self.f.visible={'082_入口'}
  self.assertEqual(self.e['EnterMemory'](),4);self.assertGreaterEqual(self.f.now,120000);self.assertFalse(self.e['terminalConfirmed'])
  self.assertTrue(all(t==(100,1200,200) for t in self.f.taps))
 def test_entry_unknown5sec_goes_to_rewards_not_terminal(self):
  self.assertEqual(self.e['EnterMemory'](),1);self.assertEqual(self.e['memoryInitial'],4)
  self.assertGreater(self.f.now,5000);self.assertLess(self.f.now,5100);self.assertFalse(self.e['terminalConfirmed'])
 def test_branch_progression_all_and_single_sides(self):
  self.e.update(memorySide=0,memoryAnswer=0)
  self.assertFalse(self.e['AdvanceMemoryBranch']());self.assertEqual((self.e['memorySide'],self.e['memoryAnswer']),(0,1))
  self.assertFalse(self.e['AdvanceMemoryBranch']());self.assertEqual((self.e['memorySide'],self.e['memoryAnswer']),(1,0))
  self.assertFalse(self.e['AdvanceMemoryBranch']());self.assertEqual((self.e['memorySide'],self.e['memoryAnswer']),(1,1))
  self.assertTrue(self.e['AdvanceMemoryBranch']())
  self.e.update(memorySide=2,memoryAnswer=0);self.assertFalse(self.e['AdvanceMemoryBranch']());self.assertTrue(self.e['AdvanceMemoryBranch']())
 def test_main_side_offsets_for_three_initial_states(self):
  for state,offset in [(0,26),(1,480),(2,26)]:
   self.setUp();self.e['memoryInitial']=state;self.f.visible={'082_主界面'}
   self.f.after=lambda *a:setattr(self.f,'interrupt',True)
   self.e['RunMemory']();self.assertEqual(self.f.taps,[(100+offset,675,0)])
 def test_next_step_four_cached_anchor_clicks(self):
  self.f.visible={'082_下一步'}
  self.f.after=lambda *a:setattr(self.f,'interrupt',len(self.f.taps)>=4)
  self.e['RunMemory']();self.assertEqual(self.f.taps,[(100,1200,100)]*4)
 def test_original_failure_and_success_jumps_to582(self):
  p=json.loads((ROOT/'flows/082_战士记忆/evidence/root626原型.json').read_text('utf8'))
  for pc in [338,395,412,558]:
   w=p['code'][pc-1];self.assertEqual(w&63,18);self.assertEqual(pc+1+(w>>14)-131071,582)
 def test_failure_success_blue_priority_cleanup_not_terminal(self):
  for name in ['082_蓝按钮','082_失败','082_胜利']:
   self.setUp();self.f.visible={name,'082_主界面','082_答案','152_开战图标6'};calls=[]
   self.e['ReturnMemoryPage']=lambda:calls.append('return') or 4
   self.assertEqual(self.e['RunMemory'](),4);self.assertEqual(calls,['return']);self.assertFalse(self.f.taps);self.assertFalse(self.e['terminalConfirmed'])
 def test_answer0_back_goes_cleanup_without_skip(self):
  self.f.visible={'152_开战图标6','078_跳过战斗'};self.e['ReturnMemoryPage']=lambda:4
  self.e['RunMemory']();self.assertEqual(self.f.taps,[(128,1228,0)]);self.assertNotIn('078_跳过战斗',self.f.lookups)
 def prepare_answer1(self):
  self.f.visible={'152_开战图标6'}
  self.e['ReturnMemoryPage']=lambda:1;self.e['ReenterMemory']=lambda:1
 def test_second_answer_and21_starts_end_or_restart(self):
  for mode,result in [(0,2),(1,4)]:
   self.setUp();self.prepare_answer1();self.e['memoryFailureMode']=mode
   self.assertEqual(self.e['RunMemory'](),result)
   self.assertEqual(self.f.taps,[(128,1228,0)]+[(398,982,500),(587,982,500)]*21)
   self.assertEqual(self.e['memoryStarts'],21);self.assertEqual(self.e['memoryUncompleted'],mode==0)
   self.assertFalse(self.e['terminalConfirmed']);self.assertFalse(self.e['memoryDone'])
 def test_answer1_anchor195_and_skip550_resets_starts(self):
  self.prepare_answer1()
  def after(x,y,w):
   if x==128:self.f.visible={'082_答案','078_跳过战斗'}
   elif w==50:self.f.interrupt=True
  self.f.after=after;self.e['RunMemory']()
  self.assertEqual(self.f.taps,[(128,1228,0),(295,1200,0),(290,993,50)])
  self.assertEqual(self.e['memoryStarts'],0)
 def test_return_actions_exact_order_and_answer_override(self):
  self.e.update(memoryAnswer=0,memoryStarted=0)
  self.f.visible={'082_蓝按钮','082_失败','082_胜利','082_返回界面','082_主界面','082_入口'}
  self.assertEqual(self.e['ReturnMemoryPage'](),1);self.assertEqual(self.e['memoryAnswer'],1)
  self.assertEqual(self.f.taps,[(100,1200,1000)]+[(100,1200,500)]*4);self.assertFalse(self.e['terminalConfirmed'])
 def test_reenter_actions500_wait_for_main(self):
  self.e['memoryStarted']=0;self.f.visible={'082_大厅入口','082_入口','082_主界面'}
  self.assertEqual(self.e['ReenterMemory'](),1);self.assertEqual(self.f.taps,[(100,1200,500)]*2)
 def test_native180sec_shared_clock_in_three_phases(self):
  for name in ['RunMemory','ReturnMemoryPage','ReenterMemory']:
   self.setUp();self.e.update(memoryStarted=0,BusinessExpired=lambda:self.f.now>=300000)
   self.assertEqual(self.e[name](),1);self.assertGreater(self.f.now,180000);self.assertLess(self.f.now,180100)
   self.assertTrue(self.e['memoryTerminal']);self.assertIn('180秒',self.e['memoryReason'])
 def test_shared180_clock_not_refreshed_on_return_and_reentry(self):
  self.e.update(memoryStarted=0,BusinessExpired=lambda:False);self.f.now=179900;self.f.visible={'082_入口'}
  self.e['ReturnMemoryPage']();self.assertEqual(self.e['memoryStarted'],0)
  self.f.visible.clear();self.e['ReenterMemory']();self.assertTrue(self.e['memoryTerminal']);self.assertLess(self.f.now,180100)
 def test_public120_limit_wins_no_native_completion(self):
  self.assertEqual(self.e['RunMemory'](),4);self.assertFalse(self.e['terminalConfirmed']);self.assertGreaterEqual(self.f.now,120000)
 def test_reward_stage1_unknown_native5sec_terminal_no_stage2(self):
  self.assertEqual(self.e['FinishMemoryRewards'](),1);self.assertTrue(self.e['terminalConfirmed'])
  self.assertNotIn('082_获得二',self.f.lookups);self.assertGreater(self.f.now,5000);self.assertLess(self.f.now,5100)
 def test_stage1_actions_refresh_and_exact_reward_offset(self):
  self.f.visible={'082_获得一','082_完成状态3'}
  def after(*a):
   if len(self.f.taps)==2:self.f.visible={'082_完成状态4','082_最终界面'}
  self.f.after=after;self.assertEqual(self.e['FinishMemoryRewards'](),1)
  self.assertEqual(self.f.taps,[(100,1200,500),(348,763,200)]);self.assertEqual(self.f.now,770)
 def test_stage2_three_actions_and_final_exact_order(self):
  self.f.visible={'082_完成状态4','082_获得二','082_主界面','082_奖励面板','082_最终界面'}
  self.assertEqual(self.e['FinishMemoryRewards'](),1)
  self.assertEqual(self.f.taps,[(100,1200,200),(454,126,50),(600,416,50)]);self.assertEqual(self.f.now,370)
 def test_stage2_unknown_native5sec_terminal(self):
  self.f.visible={'082_完成状态4'};self.assertEqual(self.e['FinishMemoryRewards'](),1)
  self.assertIn('附加奖励5秒',self.e['memoryReason']);self.assertGreater(self.f.now,5000)
 def test_reward_activity_never_resets_public_deadline(self):
  self.f.visible={'082_完成状态4','082_获得二'};self.assertEqual(self.e['FinishMemoryRewards'](),4)
  self.assertFalse(self.e['terminalConfirmed']);self.assertGreaterEqual(self.f.now,120000)
 def test_execute_complete_states_skip_challenge(self):
  for state in [3,4]:
   self.setUp();self.e['EnterGatherHall']=lambda:1;self.f.visible={f'082_完成状态{state}'}
   self.e['RunMemory']=lambda:self.fail('already complete sides')
   self.e['FinishMemoryRewards']=lambda:7
   self.assertEqual(self.e['ExecuteMemory'](),7)
 def test_interruption_blocks_all_phase_exits(self):
  for name in ['EnterMemory','ReturnMemoryPage','ReenterMemory','RunMemory','FinishMemoryRewards']:
   self.setUp();self.f.interrupt=True;self.f.visible={'082_未开启','082_最终界面'}
   self.assertEqual(self.e[name](),4);self.assertFalse(self.f.taps);self.assertFalse(self.e['terminalConfirmed'])
 def public(self):
  load(['common/任务状态.mq','common/任务注册.mq','common/任务调度.mq'],self.e)
  self.e['RegisterTasks']();self.e['NewSession']();self.e['SaveCurrentTask'](82)
 def test_terminal_and_hall_commit_guards(self):
  self.public();self.assertFalse(self.e['CommitTask'](True));self.e['ConfirmMemoryTerminal']('专业版出口')
  self.assertFalse(self.e['CommitTask'](False));self.assertTrue(self.e['CommitTask'](True))
  self.assertTrue(self.e['memoryDone']);self.assertEqual(self.e['memoryCount'],1);self.assertEqual(self.e['SelectMemory'](),0)
 def test_resume82_ignores_checkbox_off_after_interrupt(self):
  self.public();self.e['memoryEnabled']=False;self.assertEqual(self.e['SelectDueTask'](),82)
 def test_uncompleted_release_guards_no_fake_done_or_cooldown(self):
  self.public();self.e['memoryUncompleted']=True
  self.assertFalse(self.e['ReleaseMemoryUncompleted'](False));self.assertEqual(self.e['resumeTask'],82)
  self.assertTrue(self.e['ReleaseMemoryUncompleted'](True));self.assertEqual(self.e['resumeTask'],0)
  self.assertFalse(self.e['memoryDone']);self.assertEqual(self.e['memoryCount'],0);self.assertEqual(self.e['SelectMemory'](),82)
 def test_scheduler_end_mode_returns_hall_without_restart_or_commit(self):
  self.public();calls=[]
  def dispatch(t):self.e['memoryUncompleted']=True;return 2
  self.e.update(EnsureGameHall=lambda:1,DispatchTask=dispatch,ReturnToHall=lambda:1,RestartGame=lambda:calls.append('restart'))
  self.e['SchedulerStep']();self.assertFalse(calls);self.assertEqual(self.e['resumeTask'],0);self.assertFalse(self.e['memoryDone'])
 def test_scheduler_hall_failure_recovers82(self):
  self.public();calls=[]
  def dispatch(t):self.e['memoryUncompleted']=True;return 2
  self.e.update(EnsureGameHall=lambda:1,DispatchTask=dispatch,ReturnToHall=lambda:4,RestartGame=lambda:calls.append(self.e['resumeTask']))
  self.e['SchedulerStep']();self.assertEqual(calls,[82]);self.assertFalse(self.e['memoryDone'])
 def test_actual_dispatch_uses82_no_other_feature_state(self):
  load(['common/任务分派.mq'],self.e)
  self.e['EnterGatherHall']=lambda:1;self.f.visible={'082_未开启'}
  self.assertEqual(self.e['DispatchTask'](82),1);self.assertTrue(self.e['memoryTerminal'])
  self.assertEqual(self.e['currentTask'],82);self.assertEqual(self.e['memoryCount'],0)
 def test_execute_unknown_entry_and_first_reward_native_exits(self):
  self.e['EnterGatherHall']=lambda:1
  self.assertEqual(self.e['ExecuteMemory'](),1);self.assertTrue(self.e['memoryTerminal'])
  self.assertGreater(self.f.now,10000);self.assertLess(self.f.now,10200);self.assertFalse(self.f.taps)
  self.assertEqual(self.e['memoryCount'],0);self.assertFalse(self.e['memoryDone'])
 def test_answer1_plus_skip_uses550ms_and_resets_counter(self):
  self.prepare_answer1()
  self.f.after=lambda x,y,w:self.f.visible.add('078_跳过战斗') if x==587 else None
  old_delay=self.e['Delay']
  def delay(n):
   old_delay(n)
   if n==500:self.f.interrupt=True
  self.e['Delay']=delay;self.e['RunMemory']()
  self.assertEqual(self.f.taps,[(128,1228,0),(398,982,500),(587,982,500),(290,993,50)])
  self.assertEqual(self.e['memoryStarts'],0);self.assertFalse(self.e['terminalConfirmed'])
 def test_completion_and_uncompleted_release_block_foreground_commit(self):
  self.public();self.e['BeginForegroundCommit']=lambda:False
  self.e['ConfirmMemoryTerminal']('出口');self.assertFalse(self.e['CommitTask'](True))
  self.e['memoryUncompleted']=True;self.assertFalse(self.e['ReleaseMemoryUncompleted'](True))
  self.assertEqual(self.e['resumeTask'],82);self.assertEqual(self.e['memoryCount'],0)
 def test_terminal_helper_cannot_turn_public_timeout_to_complete(self):
  self.f.interrupt=True
  self.assertEqual(self.e['ConfirmMemoryTerminal']('未开启'),4);self.assertFalse(self.e['terminalConfirmed'])
 def test_scheduler_success_only_after_hall_confirmation(self):
  self.public();calls=[]
  def dispatch(t):return self.e['ConfirmMemoryTerminal']('原生出口')
  self.e.update(EnsureGameHall=lambda:1,DispatchTask=dispatch,ReturnToHall=lambda:1,RestartGame=lambda:calls.append('restart'))
  self.e['SchedulerStep']();self.assertFalse(calls);self.assertEqual(self.e['memoryCount'],1)
  self.assertTrue(self.e['memoryDone']);self.assertEqual(self.e['resumeTask'],0)
 def test_actual_foreground_recovery_routes82(self):
  from test_foreground import Foreground
  fg=Foreground();fg.setUp();fg.e.update(Time=lambda:1760000000,memoryFailureMode=1)
  load(['common/战士记忆状态.mq'],fg.e);fg.e['WorldLog']=fg.logs.append;fg.e['NewMemorySession']()
  fg.e['SaveCurrentTask'](82);fg.request();self.assertTrue(fg.e['HandleForegroundRecovery']())
  self.assertEqual(fg.e['resumeTask'],82);self.assertEqual(fg.e['SelectDueTask'](),82)
  self.assertEqual((fg.e['memoryRestarts'],fg.e['memoryRecoveries'],fg.e['memoryCount']),(1,1,0))
  self.assertEqual(fg.events,[('kill','game'),('run','game')])
 def test_log_stage82_not70(self):
  before=self.e['worldPhase'];self.e['WorldStage']('挑战阶段')
  self.assertEqual(self.e['worldPhase'],before);self.assertEqual(self.e['memoryPhase'],'挑战阶段');self.assertIn('战士记忆82',self.f.logs[-1])
 def test_ui_single_default_off_no_unsupported_callback(self):
  t=(ROOT/'ui/最小配置.uip').read_text('utf-8-sig');key='名称:"日常_战士记忆",提示内容:"战士记忆",选中:false,文字大小:10,高度:0,宽度:0'
  self.assertIn(key,t);self.assertEqual(t.count('名称:"日常_战士记忆"'),1)
  self.assertLess(t.index('名称:"异时空标题"'),t.index(key));self.assertNotIn('点击响应:"战士记忆"',t)
 def test_recognition_full_exact_catalog_and_mq_parameters(self):
  ev=ROOT/'flows/082_战士记忆/evidence';rows=json.loads((ev/'图色唯一参数.json').read_text('utf8'));records=json.loads((ev/'图色转换.json').read_text('utf8'))
  self.assertEqual(len(rows),19);self.assertEqual([x['definition'] for x in records],rows)
  cat=json.loads((ROOT/'evidence/图色参数.json').read_text('utf8'));self.assertEqual([x for x in cat if x['name'].startswith('082_')],records)
  source=(ROOT/'common/图色参数.mq').read_text('utf-8-sig')
  for x in records:
   body=re.search(r'Case "'+x['name']+r'"(.*?)(?=\n    Case |\n    End Select)',source,re.S)[1]
   self.assertIn('FindMultiColor '+', '.join(json.dumps(v) for v in x['definition'])+', foundX, foundY',body)
  self.assertEqual(rows[0][-1],.95);self.assertEqual(rows[7][:4],[19,911,718,1000]);self.assertEqual(rows[7][-1],.9)
 def test_no_version_specific_or_cross_boundary_api(self):
  t=(ROOT/'flows/082_战士记忆/战士记忆.mq').read_text('utf-8-sig')
  self.assertNotRegex(t,r'OcrEx|paddle|Image\.Ocr|KillApp|RunApp|CommitTask|SchedulerStep|InStr')
 def test_no_build_or_sync_artifact_changed(self):
  baseline=json.loads((ROOT/'flows/082_战士记忆/evidence/禁止构建同步基线.json').read_text('utf8'))
  from sync_boundary import authorized_sync_baseline
  baseline=authorized_sync_baseline(baseline)
  from pathlib import Path
  self.assertEqual(len(baseline),8)
  for path,digest in baseline.items():self.assertEqual(hashlib.sha256(Path(path).read_bytes()).hexdigest(),digest,path)

if __name__=='__main__':unittest.main()
