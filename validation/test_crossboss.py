import unittest,json,hashlib,math,re
from types import SimpleNamespace
from mq_subset import ROOT,load
E=ROOT/'flows/083_跨服世界首领/evidence'
class CrossBossTests(unittest.TestCase):
 def setUp(self):
  from test_worldboss import WorldBossTests
  self.f=WorldBossTests();self.f.setUp();self.e=self.f.e
  self.e.update(currentTask=83,crossEnabled=False,crossSundayStop=False,crossHour=9,crossMinute=10,crossBuyConfig=0,DateTime=SimpleNamespace(WeekDay=lambda:5))
  load(['common/跨服首领状态.mq','flows/083_跨服世界首领/跨服世界首领.mq'],self.e);self.e['NewCrossBossSession']()
 def test_config_minutes_really_take_effect(self):
  self.e['ReadUIConfig']=lambda k,d:{'跨服首领启用':'true','跨服首领周日停':'false','跨服首领执行时':'11','跨服首领执行分':'37','跨服首领买次数':'2'}.get(k,d);self.e['LoadCrossBossSettings']();self.e['NewCrossBossSession']();self.assertEqual(self.e['crossDue'],self.e['WorldDayStart'](self.f.stamp)+11*3600+37*60);self.assertTrue(self.e['crossEnabled']);self.assertFalse(self.e['crossSundayStop']);self.assertEqual(self.e['crossBuyRuntime'],2)
 def test_time_before_default_waits(self):
  self.f.at(9,9);self.e['NewCrossBossSession']();self.e['crossEnabled']=True;self.assertEqual(self.e['SelectCrossBoss'](),0)
 def test_native_weekday_raw_rules_from_prototype(self):
  self.f.at(10)
  for week in range(1,8):
   for stop in [False,True]:
    self.e['NewCrossBossSession']();self.e.update(crossEnabled=True,crossSundayStop=stop);self.e['DateTime'].WeekDay=lambda w=week:w;self.assertEqual(self.e['SelectCrossBoss'](),0 if week==1 or week==7 and stop else 83)
 def test23_window_and_midnight_do_not_commit(self):
  self.f.at(23);self.e['NewCrossBossSession']();self.e['crossEnabled']=True;self.assertEqual(self.e['SelectCrossBoss'](),0);self.assertEqual(self.e['crossCount'],0);self.f.stamp=self.e['WorldDayStart'](self.f.stamp)+86400+3600;self.assertEqual(self.e['SelectCrossBoss'](),0)
 def test_day_commit_nextday_and_independent_counts(self):
  self.e.update(worldCount=4,cellCount=7,crossHour=10,crossMinute=25);self.e['CommitCrossBossTask']();self.assertEqual(self.e['crossCount'],1);self.assertEqual(self.e['crossDue'],self.e['WorldDayStart'](self.f.stamp)+86400+37500);self.assertEqual((self.e['worldCount'],self.e['cellCount']),(4,7))
 def test_gray_entry_approved_terminal_without_tap(self):
  self.f.visible={'083_灰入口二','083_预备一'};self.assertEqual(self.e['EnterCrossBoss'](),1);self.assertEqual(self.e['crossMode'],-1);self.assertTrue(self.e['crossTerminalReason']);self.assertFalse(self.f.taps)
 def test_preparation_before_formal_priority(self):
  self.f.visible={'083_预备一','083_未上阵一','083_已上阵一'};self.assertEqual(self.e['EnterCrossBoss'](),1);self.assertEqual(self.e['crossMode'],0)
 def test_formal_unformed_and_formed(self):
  for name in ['083_未上阵二','083_已上阵二']:
   self.f.visible={name};self.assertEqual(self.e['EnterCrossBoss'](),1);self.assertEqual(self.e['crossMode'],1)
 def test_entry_click_original_anchor_300(self):
  self.f.visible={'083_入口二'};self.f.after=lambda *a:self.f.visible.add('083_已上阵二');self.assertEqual(self.e['EnterCrossBoss'](),1);self.assertEqual(self.f.taps,[(600,900,300)])
 def test_unknown_entry_not_terminal(self):
  self.assertEqual(self.e['EnterCrossBoss'](),4);self.assertFalse(self.e['crossTerminal'])
 def test_prepare_exact_no_attempts_ocr(self):
  self.f.visible={'083_预备一'};self.f.text='次数不够';self.assertEqual(self.e['RunCrossPreparation'](),1);self.assertFalse(self.f.taps);self.assertIn('次数不够',self.e['crossTerminalReason'])
 def prep_exit(self,n,kind):
  self.f.visible={kind};seen=[]
  def after(*args):
   seen.append(args)
   if len(seen)==n:self.f.visible={'083_预备退出二'}
  self.f.after=after
  return self.e['RunCrossPreparation']()
 def test_six_prepare_actions_then_explicit_exit(self):
  self.assertEqual(self.prep_exit(6,'083_预备一'),1);self.assertEqual(len(self.f.taps),7);self.assertEqual(self.f.taps[:6],[(600,900,500)]*6);self.assertEqual(self.f.taps[-1],(600,900,0));self.assertIn('达阈值',self.e['crossTerminalReason'])
 def test_ten_result_actions_then_explicit_exit(self):
  self.assertEqual(self.prep_exit(10,'083_预备结果一'),1);self.assertEqual(len(self.f.taps),11)
 def test_threshold_without_exit_uses_native_three_second_exit(self):
  self.f.visible={'083_预备一'};self.assertEqual(self.e['RunCrossPreparation'](),1);self.assertEqual(len(self.f.taps),6);self.assertIn('超过3000',self.e['crossTerminalReason']);self.assertLess(self.f.now,4000)
 def test_ocr_blank_does_not_mean_empty(self):
  self.f.visible={'083_预备一'};self.f.text='';self.e['RunCrossPreparation']();self.assertEqual(len(self.f.taps),6);self.assertNotIn('次数不够',self.e['crossTerminalReason'])
 def test_purchase_exact_cross_coordinate_and_prices(self):
  for mode,adds,price in [(1,2,60),(2,4,140),(3,6,320),(4,9,870)]:
   self.setUp();self.e['crossBuyRuntime']=mode;self.f.text=str(price);self.f.visible={'083_购买主界面'}
   def after(x,y,w):
    if (x,y)==(590,1150):self.f.visible={'083_购买弹窗'}
    if (x,y)==(294,1230):self.f.visible={'083_购买主界面'}
   self.f.after=after;self.assertEqual(self.e['BuyCrossBossAttempts'](),1);self.assertEqual(self.f.taps[0],(590,1150,1000));self.assertEqual(self.f.taps[1:1+adds],[(388,1052,300)]*adds);self.assertEqual(self.f.taps[-1],(294,1230,0));self.assertEqual(self.e['crossBuyRuntime'],0)
 def test_price_blank_closes_and_runtime_config_independent(self):
  self.e.update(crossBuyRuntime=1,crossBuyConfig=1,worldBuyRuntime=4);self.f.visible={'083_购买弹窗'};self.f.text=''
  def after(x,y,w):
   if (x,y)==(589,917):self.f.visible={'083_购买主界面'}
  self.f.after=after;self.assertEqual(self.e['BuyCrossBossAttempts'](),1);self.assertNotIn((294,1230,0),self.f.taps);self.assertEqual(self.e['crossBuyConfig'],1);self.assertEqual(self.e['worldBuyRuntime'],4)
 def test_purchase_off_no_click(self):
  self.assertEqual(self.e['BuyCrossBossAttempts'](),1);self.assertFalse(self.f.taps)
 def test_formal_six_actions_only_stage_exit(self):
  self.f.visible={'083_已上阵一'};self.assertEqual(self.e['SweepCrossBoss'](),1);self.assertEqual(self.f.taps,[(600,900,500)]*6);self.assertFalse(self.e['crossTerminal'])
 def test_formal_unknown15sec_is_native_stage_exit(self):
  self.assertEqual(self.e['SweepCrossBoss'](),1);self.assertGreater(self.f.now,15000);self.assertEqual(self.e['crossTerminalReason'],'');self.assertFalse(self.e['terminalConfirmed'])
 def test_purchase_time_is_part_of_original_sweep_timer(self):
  self.f.now=15000;self.e['crossActionAt']=0;self.assertEqual(self.e['SweepCrossBoss'](),1);self.assertLess(self.f.now,15200);self.assertFalse(self.e['terminalConfirmed'])
 def test_formal_event_order_and_original_waits(self):
  self.f.visible={'083_已上阵一','083_未上阵二','083_扫荡奖励一','083_次数弹窗二'};self.assertEqual(self.e['SweepCrossBoss'](),1);self.assertEqual(self.f.taps,[(600,900,500),(600,900,500),(600,900,300),(600,900,0)]);self.assertEqual(self.e['crossActionAt'],1350)
 def test_confirm_board_closes_popup_before_page(self):
  self.f.visible={'083_次数弹窗一','083_已上阵二'};self.assertEqual(self.e['ConfirmCrossBossBoard'](),1);self.assertEqual(self.f.taps,[(600,900,300)]);self.assertEqual(self.f.now,800)
 def test_rewards_all_priority_then_explicit_empty(self):
  self.f.visible={'083_领奖入口一','083_一键领取一','083_领取奖励一','083_领取关闭一','083_无奖励一'};self.assertEqual(self.e['FinishCrossBossRewards'](),1);self.assertEqual(self.f.taps,[(600,900,500)]*4);self.assertEqual(self.f.now,2500);self.assertFalse(self.e['crossTerminal'])
 def test_reward_missing_button_unknown_never_success(self):
  self.assertEqual(self.e['FinishCrossBossRewards'](),4);self.assertEqual(self.e['crossTerminalReason'],'')
 def test_close_alone_not_terminal(self):
  self.f.visible={'083_领取关闭一'};self.f.after=lambda *a:self.f.visible.clear();self.assertEqual(self.e['FinishCrossBossRewards'](),4);self.assertEqual(len(self.f.taps),1)
 def test_full_gray_cycle_terminal_not_committed_in_business(self):
  self.e['EnterEnemyHall']=lambda:1;self.f.visible={'083_灰入口一'};self.assertEqual(self.e['ExecuteCrossBoss'](),1);self.assertTrue(self.e['terminalConfirmed']);self.assertTrue(self.e['crossTerminal']);self.assertEqual(self.e['crossCount'],0)
 def test_full_preparation_ocr_cycle(self):
  self.e['EnterEnemyHall']=lambda:1;self.f.visible={'083_预备一'};self.f.text='次数不够';self.assertEqual(self.e['ExecuteCrossBoss'](),1);self.assertTrue(self.e['crossTerminal']);self.assertEqual(self.e['crossCount'],0)
 def test_full_formal_requires_last_empty(self):
  self.e['EnterEnemyHall']=lambda:1;self.f.visible={'083_已上阵一'};self.e['BuyCrossBossAttempts']=lambda:1;self.e['SweepCrossBoss']=lambda:1;self.e['ConfirmCrossBossBoard']=lambda:1
  def rewards():self.e['crossTerminalReason']='明确无奖励';return 1
  self.e['FinishCrossBossRewards']=rewards;self.assertEqual(self.e['ExecuteCrossBoss'](),1);self.assertTrue(self.e['crossTerminal'])
 def public(self):
  load(['common/任务状态.mq','common/任务注册.mq','common/任务调度.mq'],self.e);self.e['RegisterTasks']();self.e['NewSession']()
 def test_resume_priority_bypasses_weekday_time_and_disabled(self):
  self.public();self.e.update(currentTask=83,crossEnabled=False);self.e['SaveRecovery']();self.assertEqual(self.e['SelectDueTask'](),83);self.assertEqual(self.e['crossRecoveries'],1);self.assertEqual(self.e['worldRecoveries'],0)
 def test_hall_gate_and_public_commit(self):
  self.public();self.e.update(currentTask=83,terminalConfirmed=True,worldCount=8,cellCount=9);self.assertFalse(self.e['CommitTask'](False));self.assertEqual(self.e['crossCount'],0);self.assertTrue(self.e['CommitTask'](True));self.assertEqual(self.e['crossCount'],1);self.assertEqual((self.e['worldCount'],self.e['cellCount']),(8,9))
 def test_public_dispatch_and_commit_true_log(self):
  self.public();self.e.update(resumeTask=83,EnsureGameHall=lambda:1,ReturnToHall=lambda:1)
  def dispatch(t):self.assertEqual(t,83);self.e['terminalConfirmed']=True;return 1
  self.e['DispatchTask']=dispatch;self.e['SchedulerStep']();self.assertEqual(self.e['crossCount'],1);self.assertTrue(any('CommitTask(True) 返回=true' in s for s in self.f.logs))
 def test_hall_fail_retains_original_and_never_commits(self):
  self.public();restarts=[];self.e.update(resumeTask=83,EnsureGameHall=lambda:1,ReturnToHall=lambda:4,RestartGame=lambda:restarts.append(self.e['resumeTask']))
  def dispatch(t):self.e['terminalConfirmed']=True;return 1
  self.e['DispatchTask']=dispatch;self.e['SchedulerStep']();self.assertEqual(restarts,[83]);self.assertEqual(self.e['crossCount'],0)
 def test_foreground5sec_actual_shared_monitor(self):
  from test_foreground import Foreground
  fg=Foreground();fg.setUp();fg.e.update(Time=lambda:1760000000,Int=math.floor,crossHour=9,crossMinute=10,crossBuyConfig=0)
  load(['common/跨服首领状态.mq'],fg.e);fg.e['WorldDayStart']=lambda n:math.floor((n+28800)/86400)*86400-28800;fg.e['WorldLog']=fg.logs.append;fg.e['NewCrossBossSession']();fg.e['SaveCurrentTask'](83);fg.request();self.assertTrue(fg.e['HandleForegroundRecovery']());self.assertEqual(fg.e['resumeTask'],83);self.assertEqual(fg.e['SelectDueTask'](),83);self.assertEqual((fg.e['crossRestarts'],fg.e['crossRecoveries'],fg.e['crossCount']),(1,1,0));self.assertEqual(fg.events,[('kill','game'),('run','game')])
 def test_qq_or_interruption_no_click_success(self):
  self.f.interrupt=True;self.f.visible={'083_灰入口一'};self.assertEqual(self.e['EnterCrossBoss'](),4);self.assertFalse(self.f.taps)
 def test_all_raw_recognition_records_exact_and_append_only(self):
  old=json.loads((E/'before/evidence/图色参数.txt').read_text('utf-8'));now=[x for x in json.loads((ROOT/'evidence/图色参数.json').read_text('utf-8')) if not x['name'].startswith(('150_','155_','154_','153_','081_','080_','082_','079_','078_','084_','085_'))];conv=json.loads((E/'图色转换.json').read_text('utf-8'));self.assertEqual(now[:len(old)],old);self.assertEqual([x['definition'] for x in now[len(old):]],[x['definition'] for x in conv]);by={x['name']:x['definition'] for x in conv}
  for r in json.loads((E/'原始图色.json').read_text('utf-8')):self.assertEqual(by[r['name']],[0,0,719,1279,r['main'],r['offsets'],r['direction'],r['similarity']])
 def test_old_business_and_independent_state_unchanged(self):
  base=json.loads((E/'修改前基线.json').read_text('utf-8'))
  for rel,h in base.items():
   if rel.startswith('flows/') or rel in ['common/悟空冒险状态.mq','common/合作冒险状态.mq','common/定时体力状态.mq']:self.assertEqual(hashlib.sha256(__import__('historical_source').before_boss_native_exits_bytes(ROOT/rel)).hexdigest(),h,rel)
 def test_ui_hierarchy_defaults_and_existing_editable_controls(self):
  ui=(ROOT/'ui/最小配置.uip').read_text('utf-8-sig');self.assertLess(ui.index('日常功能:{'),ui.index('名称:"强敌一级分隔"'));self.assertLess(ui.index('名称:"首领功能分隔"'),ui.index('名称:"跨服首领分隔"'));self.assertIn('名称:"跨服首领执行时",初始文本:"09"',ui);self.assertIn('名称:"跨服首领执行分",初始文本:"10"',ui);self.assertIn('名称:"跨服首领启用",提示内容:"    跨服世界首领",选中:false',ui)
