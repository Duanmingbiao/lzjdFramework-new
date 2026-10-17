import unittest,json,hashlib,math,re
from mq_subset import ROOT,load
E=ROOT/'flows/084_消灭红绸军/evidence'
class RedArmyTests(unittest.TestCase):
 def setUp(self):
  from test_worldboss import WorldBossTests
  self.f=WorldBossTests();self.f.setUp();self.e=self.f.e
  self.e.update(currentTask=84,redEnabled=False,redMap=0,red84Hour=12,red84Minute=30,red85Hour=20,red85Minute=0)
  load(['common/红绸军状态.mq','flows/084_消灭红绸军/消灭红绸军.mq'],self.e);self.e['NewRedArmySession']()
 def public(self):
  load(['common/任务状态.mq','common/任务注册.mq','common/任务调度.mq'],self.e);self.e['RegisterTasks']();self.e['NewSession']()
 def test_config_bool_normalization_and_map_numeric(self):
  self.e['ReadUIConfig']=lambda k,d:{'红绸军启用':'false','红绸军地图':'2','红绸军中午时':'13','红绸军中午分':'15'}.get(k,d);self.e['LoadRedArmySettings']();self.assertFalse(self.e['redEnabled']);self.assertEqual(self.e['redMap'],2);self.assertEqual(self.e['RedArmyTime'](84),47700)
 def test_default_times_and_disabled_no_immediate_run(self):
  self.f.at(11);self.e['NewRedArmySession']();self.e['redEnabled']=True;self.assertEqual(self.e['SelectRedArmy'](),0);day=self.e['WorldDayStart'](self.f.stamp);self.assertEqual((self.e['red84Due'],self.e['red85Due']),(day+45000,day+72000))
 def test_noon_due_then_evening_due(self):
  self.f.at(12,30);self.e['NewRedArmySession']();self.e['redEnabled']=True;self.assertEqual(self.e['SelectRedArmy'](),84);self.e['CommitRedArmyTask'](84);self.assertEqual(self.e['SelectRedArmy'](),0);self.f.at(20);self.assertEqual(self.e['SelectRedArmy'](),85)
 def test_config_time_bounds_inclusive(self):
  for task,h,m,seconds in [(84,11,30,41400),(84,13,30,48600),(85,18,30,66600),(85,20,30,73800)]:
   self.e[f'red{task}Hour']=h;self.e[f'red{task}Minute']=m;self.assertEqual(self.e['RedArmyTime'](task),seconds)
 def test_out_of_window_random_ranges(self):
  self.e.update(red84Hour=1,red85Hour=22)
  for rnd,m in [(0,10),(.99999,50)]:
   self.e['Rnd']=lambda v=rnd:v;self.assertEqual(self.e['RedArmyTime'](84),46800+m*60);self.assertEqual(self.e['RedArmyTime'](85),68400+m*60)
 def test_cutoff_exact_time_still_eligible_then_skip_without_commit(self):
  self.f.at(14);self.e['NewRedArmySession']();self.e['redEnabled']=True;self.assertEqual(self.e['SelectRedArmy'](),84);self.f.now=1000;self.assertEqual(self.e['SelectRedArmy'](),0);self.assertEqual(self.e['red84Count'],0)
  self.f.at(21);self.assertEqual(self.e['SelectRedArmy'](),85);self.f.now=1000;self.assertEqual(self.e['SelectRedArmy'](),0);self.assertEqual(self.e['red85Count'],0)
 def test_midnight_waits_and_daily_commit_independent(self):
  self.f.at(13);self.e['NewRedArmySession']();self.e.update(red85Count=4,currentTask=84);self.e['CommitRedArmyTask'](84);self.assertEqual((self.e['red84Count'],self.e['red85Count']),(1,4));self.assertEqual(self.e['red84Due'],self.e['WorldDayStart'](self.f.stamp)+86400+45000);self.f.stamp=self.e['WorldDayStart'](self.f.stamp)+86400;self.e['redEnabled']=True;self.assertEqual(self.e['SelectRedArmy'](),0)
 def test_business_finished_day_used_when_hall_crosses_midnight(self):
  self.f.at(23,59);day=self.e['WorldDayStart'](self.f.stamp);self.e.update(red85FinishedAt=self.f.stamp,currentTask=85);self.f.stamp=day+86460;self.e['CommitRedArmyTask'](85);self.assertEqual(self.e['red85Due'],day+86400+72000)
 def test_new_session_resets_states_but_keeps_config(self):
  self.e.update(red84Count=6,red85Count=8,red84Restarts=2,red85Recoveries=3,redMap=2);self.e['NewRedArmySession']();self.assertEqual((self.e['red84Count'],self.e['red85Count'],self.e['red84Restarts'],self.e['red85Recoveries']),(0,0,0,0));self.assertEqual(self.e['redMap'],2)
 def test_entry_priority_and_original_2000_click(self):
  self.f.visible={'084_入口'};self.f.after=lambda *a:self.f.visible.add('084_主界面');self.assertEqual(self.e['EnterRedArmy'](),1);self.assertEqual(self.f.taps,[(600,900,2000)]);self.assertEqual(self.f.now,2500)
 def test_gray_priority_and_current_task_only(self):
  self.e['EnterEnemyHall']=lambda:1;self.f.visible={'084_未开启','084_时间已过','084_主界面'};self.e['red85Done']=False;self.assertEqual(self.e['ExecuteRedArmy'](84),1);self.assertIn('未开启',self.e['red84Reason']);self.assertTrue(self.e['red84Terminal']);self.assertFalse(self.e['red85Done']);self.assertFalse(self.e['red85Terminal']);self.assertFalse(self.f.taps);self.assertEqual(self.f.now,2000)
 def test_expired_entry_explicit_terminal(self):
  self.f.visible={'084_时间已过'};self.assertEqual(self.e['EnterRedArmy'](),1);self.assertIn('时间已过',self.e['redReason']);self.assertEqual(self.f.now,2000)
 def test_unknown_entry_never_success(self):
  self.assertEqual(self.e['EnterRedArmy'](),4);self.assertFalse(self.e['terminalConfirmed']);self.assertTrue(any('超时' in x for x in self.f.logs))
 def test_three_maps_already_selected_no_click(self):
  for m,t in [(0,'一'),(1,'二'),(2,'三')]:
   self.setUp();self.e['redMap']=m;self.f.visible={'084_图'+t+'已选二'};self.assertEqual(self.e['SelectRedArmyMap'](),1);self.assertFalse(self.f.taps);self.assertEqual(self.f.now,500)
 def test_three_map_entry_anchor_500_after50(self):
  for m,t in [(0,'一'),(1,'二'),(2,'三')]:
   self.setUp();self.e['redMap']=m;self.f.visible={'084_图'+t+'入口二'};self.f.after=lambda *a,t=t:self.f.visible.add('084_图'+t+'已选一');self.assertEqual(self.e['SelectRedArmyMap'](),1);self.assertEqual(self.f.taps,[(600,900,500)]);self.assertEqual(self.f.now,1050)
 def test_map_selected_priority_over_unselected(self):
  self.f.visible={'084_图一已选一','084_图一入口一'};self.assertEqual(self.e['SelectRedArmyMap'](),1);self.assertFalse(self.f.taps)
 def test_unknown_map_timeout(self):
  self.assertEqual(self.e['SelectRedArmyMap'](),4)
 def test_enter_monster_then_confirm_sweep_dialog(self):
  self.f.visible={'084_第二怪二'};self.f.after=lambda *a:self.f.visible.add('084_扫荡界面二');self.assertEqual(self.e['EnterRedArmyMonster']('084_第二怪'),1);self.assertEqual(self.f.taps,[(600,900,500)]);self.assertEqual(self.f.now,1000)
 def test_original_sweep_thresholds_and_double_click_waits(self):
  for mode,pairs in [(0,6),(1,7),(2,8)]:
   self.setUp();self.f.visible={'084_扫荡界面一'};self.assertEqual(self.e['SweepRedArmyMonster'](mode),1);self.assertEqual(self.f.taps,[(600,900,20),(600,900,500)]*pairs);self.assertFalse(self.e['terminalConfirmed']);self.assertEqual(self.f.now,pairs*520+(50+50*pairs+500 if mode==1 else 0))
 def test_exact_zero_ocr_is_only_stage_end(self):
  self.f.visible={'084_扫荡界面二'};self.f.text='挑战次数：0';self.assertEqual(self.e['SweepRedArmyMonster'](0),1);self.assertFalse(self.f.taps);self.assertFalse(self.e['terminalConfirmed'])
 def test_nonexact_ocr_does_not_become_zero(self):
  for text in ['', '挑战次数:0','挑战次数： 0','挑战次数：1']:
   self.setUp();self.f.visible={'084_扫荡界面一'};self.f.text=text;self.assertEqual(self.e['SweepRedArmyMonster'](0),1);self.assertEqual(len(self.f.taps),12)
 def test_noon_sweep_event_order_and_waits(self):
  self.f.visible={'084_胜利','084_翻牌一','084_翻牌完成二'}
  self.f.after=lambda x,y,w:self.f.visible.clear() if w==0 else None
  self.e['SweepRedArmyMonster'](0);self.assertEqual(self.f.taps,[(600,900,500),(600,900,1000),(600,900,0)]);self.assertEqual(self.f.lookups[:5],['084_扫荡界面一','084_扫荡界面二','084_胜利','084_翻牌一','084_翻牌完成一'])
 def test_first_monster_victory_exits_before_flip(self):
  self.f.visible={'084_胜利','084_翻牌一'};self.assertEqual(self.e['SweepRedArmyMonster'](1),1);self.assertEqual(self.f.taps,[(600,900,500)]);self.assertNotIn('084_翻牌一',self.f.lookups);self.assertEqual(self.e['redActionAt'],50)
 def test_event_resets_counter_before_next_sweep(self):
  self.f.visible={'084_扫荡界面一'};count=[0]
  def after(x,y,w):
   if w==500:
    count[0]+=1
    if count[0]==1:self.f.visible.add('084_胜利')
    elif count[0]==2:self.f.visible.discard('084_胜利')
  self.f.after=after;self.assertEqual(self.e['SweepRedArmyMonster'](0),1);self.assertEqual(len(self.f.taps),15)
 def test_close_noon_priority_no_flip_pick(self):
  self.f.visible={'084_胜利','084_翻牌一','084_翻牌完成一','084_关闭一','084_主界面'};self.assertEqual(self.e['CloseRedArmyMonster'](0),1);self.assertEqual(self.f.taps,[(600,900,500),(600,900,0),(600,900,0)]);self.assertNotIn('084_翻牌一',self.f.lookups);self.assertEqual(self.f.now,1250)
 def test_close_first_includes_flip_with_original_waits(self):
  self.f.visible={'084_胜利','084_翻牌一','084_翻牌完成一','084_关闭一','084_主界面'};self.assertEqual(self.e['CloseRedArmyMonster'](1),1);self.assertEqual(self.f.taps,[(600,900,500),(600,900,1000),(600,900,0),(600,900,0)]);self.assertEqual(self.f.now,2250)
 def test_close_missing_board_never_success(self):
  self.f.visible={'084_关闭一'};self.f.after=lambda *a:self.f.visible.clear();self.assertEqual(self.e['CloseRedArmyMonster'](0),4);self.assertFalse(self.e['terminalConfirmed'])
 def test_antistuck_roundtrip_two_original_clicks(self):
  self.f.visible={'084_主界面'}
  def after(x,y,w):self.f.visible={'084_入口'} if w==2000 else {'084_主界面'}
  self.f.after=after;self.assertEqual(self.e['RefreshRedArmyPage'](),1);self.assertEqual(self.f.taps,[(600,900,2000),(600,900,1000)])
 def test_antistuck_unknown_no_blind_click(self):
  self.assertEqual(self.e['RefreshRedArmyPage'](),4);self.assertFalse(self.f.taps)
 def test_refresh_done_template_first_direction0(self):
  self.f.visible={'085_首怪打完','085_等待主界面'};self.f.text='挑战次数：1';self.assertEqual(self.e['WaitRedArmyRefresh'](),1);self.assertTrue(self.e['redFirstDone']);self.assertNotIn('085_等待主界面',self.f.lookups);self.assertEqual(self.f.now,1000)
 def test_refresh_ocr_one_or_two_and_countdown_carries(self):
  for text in ['挑战次数：1','挑战次数：2']:
   self.setUp();self.f.visible={'085_等待主界面'};self.f.text=text;self.assertEqual(self.e['WaitRedArmyRefresh'](),1);self.assertFalse(self.e['redFirstDone']);self.assertEqual(self.f.now,2000);self.assertEqual(self.e['redRefreshLeft'],5)
 def test_countdown_sixth_calls_antistuck_before_detection(self):
  calls=[];self.e.update(redRefreshLeft=1,RefreshRedArmyPage=lambda:calls.append('切页') or 1,SelectRedArmyMap=lambda:calls.append('选图') or 1);self.f.visible={'085_首怪打完'};self.assertEqual(self.e['WaitRedArmyRefresh'](),1);self.assertEqual(calls,['切页','选图']);self.assertFalse(self.e['redFirstDone']);self.assertEqual(self.e['redRefreshLeft'],6);self.assertFalse(self.f.lookups)
 def first_stubs(self,elapsed,refresh_clock=False,done=False):
  calls=[]
  self.e.update(EnterRedArmyMonster=lambda b:calls.append('首怪') or 1,SweepRedArmyMonster=lambda mode:calls.append('扫荡') or 1,CloseRedArmyMonster=lambda mode:calls.append('收尾') or 1,RefreshRedArmyPage=lambda:calls.append('切页') or 1,SelectRedArmyMap=lambda:calls.append('选图') or 1,BusinessExpired=lambda:False)
  def wait():
   calls.append('等待');self.f.now+=elapsed
   if refresh_clock:self.e['redActionAt']=self.f.now
   self.e['redFirstDone']=done;return 1
  self.e['WaitRedArmyRefresh']=wait;return calls
 def test_first_done_does_not_become_whole_business_terminal(self):
  calls=self.first_stubs(1000,done=True);self.assertEqual(self.e['RunRedArmyFirstMonster'](),1);self.assertEqual(calls,['首怪','扫荡','收尾','切页','选图','等待']);self.assertFalse(self.e['terminalConfirmed'])
 def test_original120sec_timeout_is_recovery_not_success(self):
  self.first_stubs(120001);self.assertEqual(self.e['RunRedArmyFirstMonster'](),4);self.assertFalse(self.e['terminalConfirmed']);self.assertTrue(any('120000' in x for x in self.f.logs))
 def test_original240sec_timeout_despite_progress(self):
  self.first_stubs(80001,refresh_clock=True);self.assertEqual(self.e['RunRedArmyFirstMonster'](),4);self.assertFalse(self.e['terminalConfirmed']);self.assertTrue(any('240000' in x for x in self.f.logs))
 def test_full_noon_real_mq_to_terminal_without_commit(self):
  self.e['EnterEnemyHall']=lambda:1;board={'084_主界面','084_图一已选一','084_第二怪一','084_第三怪一'};self.f.visible=set(board)
  self.f.after=lambda *a:setattr(self.f,'visible',{'084_扫荡界面一'})
  def ocr(*a):self.f.visible=set(board);return '挑战次数：0'
  self.e['Image'].OcrText=ocr;self.assertEqual(self.e['ExecuteRedArmy'](84),1);self.assertEqual(self.f.taps,[(600,900,500)]*2);self.assertTrue(self.e['red84Terminal']);self.assertFalse(self.e['red85Terminal']);self.assertEqual(self.e['red84Count'],0)
 def test_afternoon_first_then_second_third_and_two_refreshes(self):
  calls=[];self.e.update(currentTask=85,EnterEnemyHall=lambda:1,SelectRedArmyMap=lambda:calls.append('选图') or 1,RunRedArmyFirstMonster=lambda:calls.append('首怪流程') or 1,RefreshRedArmyPage=lambda:calls.append('切页') or 1,EnterRedArmyMonster=lambda b:calls.append(b) or 1,SweepRedArmyMonster=lambda mode:calls.append(mode) or 1,CloseRedArmyMonster=lambda mode:calls.append('收尾') or 1)
  self.f.visible={'084_主界面'};self.assertEqual(self.e['ExecuteRedArmy'](85),1);self.assertEqual(calls,['选图','首怪流程','切页','选图','084_第二怪',2,'收尾','切页','选图','084_第三怪',2,'收尾']);self.assertTrue(self.e['red85Terminal']);self.assertFalse(self.e['red84Terminal'])
 def test_first_timeout_prevents_later_monsters_and_terminal(self):
  self.e.update(currentTask=85,EnterEnemyHall=lambda:1,SelectRedArmyMap=lambda:1,RunRedArmyFirstMonster=lambda:4);self.f.visible={'084_主界面'};self.assertEqual(self.e['ExecuteRedArmy'](85),4);self.assertFalse(self.e['terminalConfirmed']);self.assertFalse(self.e['red85Terminal'])
 def test_public_commit_gated_and_other_tasks_unchanged(self):
  self.public();self.e.update(currentTask=84,terminalConfirmed=True,red84Reason='终态',red85Count=9);self.assertFalse(self.e['CommitTask'](False));self.assertEqual(self.e['red84Count'],0);self.assertTrue(self.e['CommitTask'](True));self.assertEqual((self.e['red84Count'],self.e['red85Count']),(1,9))
 def test_terminal_not_confirmed_cannot_commit(self):
  self.public();self.e.update(currentTask=85,terminalConfirmed=False);self.assertFalse(self.e['CommitTask'](True));self.assertEqual(self.e['red85Count'],0)
 def test_foreground_commit_rejection_cannot_commit(self):
  self.public();self.e.update(currentTask=85,terminalConfirmed=True,BeginForegroundCommit=lambda:False);self.assertFalse(self.e['CommitTask'](True));self.assertEqual(self.e['red85Count'],0)
 def test_resume_priority_outside_window_and_disabled(self):
  self.public();self.f.at(23);self.e.update(currentTask=85,redEnabled=False);self.e['SaveRecovery']();self.assertEqual(self.e['SelectDueTask'](),85);self.assertEqual(self.e['red85Recoveries'],1);self.assertEqual(self.e['red84Recoveries'],0)
 def test_hall_failure_restarts_same_task_without_commit(self):
  self.public();restarts=[];self.e.update(resumeTask=84,EnsureGameHall=lambda:1,ReturnToHall=lambda:4,RestartGame=lambda:restarts.append(self.e['resumeTask']))
  def dispatch(t):self.e['terminalConfirmed']=True;return 1
  self.e['DispatchTask']=dispatch;self.e['SchedulerStep']();self.assertEqual(restarts,[84]);self.assertEqual(self.e['red84Count'],0)
 def test_public_success_commit_true_and_next_time_log(self):
  self.public();self.e.update(resumeTask=85,EnsureGameHall=lambda:1,ReturnToHall=lambda:1)
  def dispatch(t):self.e['terminalConfirmed']=True;self.e['red85Reason']='终态';return 1
  self.e['DispatchTask']=dispatch;self.e['SchedulerStep']();self.assertEqual(self.e['red85Count'],1);self.assertTrue(any('CommitTask(True) 返回=true' in s for s in self.f.logs));self.assertTrue(any('下一次执行时间Unix=' in s for s in self.f.logs))
 def test_actual_foreground_monitor_recovers_each_id(self):
  from test_foreground import Foreground
  for task in [84,85]:
   fg=Foreground();fg.setUp();fg.e.update(Time=lambda:1760000000,Int=math.floor,Rnd=lambda:0,redMap=0,red84Hour=12,red84Minute=30,red85Hour=20,red85Minute=0)
   load(['common/红绸军状态.mq'],fg.e);fg.e['WorldDayStart']=lambda n:math.floor((n+28800)/86400)*86400-28800;fg.e['WorldLog']=fg.logs.append;fg.e['NewRedArmySession']();fg.e['SaveCurrentTask'](task);fg.request();self.assertTrue(fg.e['HandleForegroundRecovery']());self.assertEqual(fg.e['resumeTask'],task);self.assertEqual(fg.e['SelectDueTask'](),task);self.assertEqual((fg.e[f'red{task}Restarts'],fg.e[f'red{task}Recoveries'],fg.e[f'red{task}Count']),(1,1,0));self.assertEqual(fg.events,[('kill','game'),('run','game')])
 def test_interrupt_no_click_or_terminal(self):
  self.f.interrupt=True;self.f.visible={'084_未开启'};self.assertEqual(self.e['EnterRedArmy'](),4);self.assertFalse(self.f.taps)
 def test_append_only_exact_33_profiles_and123_calls(self):
  old=json.loads((E/'before/evidence/图色参数.txt').read_text('utf-8'));now=[x for x in json.loads((ROOT/'evidence/图色参数.json').read_text('utf-8')) if not x['name'].startswith(('016_','015_','014_','013_','012_','150_','155_','154_','153_','081_','080_','082_','078_','079_'))];conv=json.loads((E/'图色转换.json').read_text('utf-8'));raw=json.loads((E/'原始图色.json').read_text('utf-8'));self.assertEqual(now[:len(old)],old);self.assertEqual(len(conv),33);self.assertEqual(len(raw),123);self.assertEqual([x['definition'] for x in now[len(old):]],[x['definition'] for x in conv]);by={x['name']:x['definition'] for x in conv}
  for x in raw:self.assertEqual(by[x['name']],[0,0,719,1279,x['main'],x['offsets'],x['direction'],x['similarity']])
  self.assertEqual([x['name'] for x in conv if x['definition'][6]==0],['085_首怪打完','085_等待主界面'])
 def test_all_existing_business_files_and_states_unchanged(self):
  base=json.loads((E/'修改前基线.json').read_text('utf-8'))
  for rel,h in base.items():
   if rel.startswith('flows/') or rel in ['common/悟空冒险状态.mq','common/合作冒险状态.mq','common/定时体力状态.mq','common/跨服首领状态.mq','common/强敌入口.mq']:self.assertEqual(hashlib.sha256(__import__('historical_source').before_boss_native_exits_bytes(ROOT/rel)).hexdigest(),h,rel)
 def test_ui_hierarchy_default_values_and_isolation(self):
  ui=(ROOT/'ui/最小配置.uip').read_text('utf-8-sig');self.assertLess(ui.index('名称:"强敌一级分隔"'),ui.index('名称:"红绸军启用"'));self.assertLess(ui.index('名称:"跨服首领启用"'),ui.index('名称:"红绸军启用"'));self.assertIn('名称:"红绸军启用",提示内容:"    消灭红绸军（中午/下午）",选中:false',ui);self.assertIn('名称:"红绸军中午分",初始文本:"30"',ui);self.assertIn('名称:"红绸军下午时",初始文本:"20"',ui)

 def test_actual_mq_recognition_definitions_equal_evidence(self):
  source=(ROOT/'common/图色参数.mq').read_text('utf-8-sig')
  for x in json.loads((E/'图色转换.json').read_text('utf-8')):
   match=re.search(r'Case "'+re.escape(x['name'])+r'"\s*//[^\n]*\s*FindMultiColor (.*),foundX,foundY',source)
   self.assertIsNotNone(match,x['name']);self.assertEqual(json.loads('['+match[1]+']'),x['definition'])
 def test_business_public_timeout_before_gray_end_not_success(self):
  self.f.now=119000;self.f.visible={'084_未开启'};self.assertEqual(self.e['EnterRedArmy'](),4);self.assertEqual(self.e['redReason'],'');self.assertFalse(self.e['terminalConfirmed'])
 def test_unknown_sweep_and_close_cannot_set_terminal(self):
  for fn,args in [('SweepRedArmyMonster',(0,)),('CloseRedArmyMonster',(0,))]:
   self.setUp();self.assertEqual(self.e[fn](*args),4);self.assertFalse(self.e['terminalConfirmed']);self.assertFalse(self.e['red84Terminal'])
 def test_multiple_recoveries_no_limit_or_other_task_mutation(self):
  for n in range(8):self.e['RecoverRedArmyTask'](85);self.e['RestartRedArmyTask'](85)
  self.assertEqual((self.e['red85Recoveries'],self.e['red85Restarts']),(8,8));self.assertEqual((self.e['red84Recoveries'],self.e['red84Restarts']),(0,0))
