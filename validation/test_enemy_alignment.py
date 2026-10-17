import unittest
from mq_subset import load, ROOT
import test_beyond
import test_legend

class AlignmentTests(unittest.TestCase):
 def beyond(self):
  f=test_beyond.BeyondTests();f.setUp();return f.f,f.e
 def test_auto_triple_exact_offsets_and_ready_priority(self):
  for pattern,expected in [('086_开启自动',(290,1070,50)),('086_开启三倍',(918,992,50)),('086_战斗基准',(918,916,50))]:
   fixture=test_legend.LegendTests();fixture.setUp();fixture.f.visible={pattern}
   self.assertFalse(fixture.e['LegendAutoTriple']());self.assertEqual(fixture.f.taps,[expected])
  fixture=test_legend.LegendTests();fixture.setUp();fixture.f.visible={'086_三倍已就绪','086_开启自动'}
  self.assertTrue(fixture.e['LegendAutoTriple']());self.assertFalse(fixture.f.taps)
 def test_auto_triple_interrupt_never_taps(self):
  fixture=test_legend.LegendTests();fixture.setUp();fixture.f.interrupt=True;fixture.f.visible={'086_开启自动'}
  self.assertFalse(fixture.e['LegendAutoTriple']());self.assertFalse(fixture.f.taps)
 def test_entry_swipe_and_page_priority(self):
  f,e=self.beyond();swipes=[];e['Swipe']=lambda *a:swipes.append(a);f.visible={'087_任务页一','087_已完成一','087_未开启一'}
  self.assertEqual(e['EnterBeyond'](),1);self.assertEqual(swipes,[(370,1000,370,300,300)]);self.assertEqual(f.now,1300);self.assertFalse(e['beyondRewardsReady'])
 def test_support_unknown_does_not_advance_round(self):
  f,e=self.beyond();f.visible={'087_任务页一'};original=f.match
  def match(n):f.now+=100;return original(n)
  e['MatchPattern']=match
  self.assertEqual(e['ExecuteBeyond'](),4);self.assertFalse(e['terminalConfirmed']);self.assertNotIn('087_点击战斗',f.lookups)
 def test_support_no_resources_and_invitation_offsets(self):
  f,e=self.beyond();f.visible={'087_支援无资源一'}
  self.assertEqual(e['EnterBeyondSupport'](),1);self.assertEqual(f.taps,[(600,900,300)])
  f.taps.clear();f.visible={'087_可邀请一'};self.assertEqual(e['InviteBeyondWarriors'](),1)
  self.assertEqual(f.taps,[(440,130,500),(440,550,500),(664,929,500)])
 def test_return_wait_before_click_and_task_confirmation(self):
  f,e=self.beyond();f.visible={'087_返回按钮一'};times=[]
  def after(*a):times.append(f.now);f.visible={'087_任务页一'}
  f.after=after
  self.assertEqual(e['ReturnBeyondFromSupport'](),1);self.assertEqual(f.taps,[(600,900,500)]);self.assertEqual(times,[2000])
 def test_battle_success_delays_and_completed_wait(self):
  for pattern,delay in [('087_挑战成功一',2000),('087_挑战成功二',1000),('087_已完成一',None)]:
   f,e=self.beyond();f.visible={pattern};self.assertEqual(e['FightBeyondRound'](),1)
   self.assertEqual(f.taps,[] if delay is None else [(600,900,delay)]);self.assertEqual(f.now,2000 if delay is None else delay+50)
 def test_battle_five_offset_then_anchor(self):
  f,e=self.beyond();f.visible={'087_点击战斗'}
  def after(*a):
   if len(f.taps)==6:f.visible={'087_挑战成功二'}
  f.after=after;self.assertEqual(e['FightBeyondRound'](),1)
  self.assertEqual(f.taps[:5],[(790,912,0)]*5);self.assertEqual(f.taps[5],(600,900,0))
 def test_skip_professional_template_offset_and_delay(self):
  f,e=self.beyond();f.visible={'087_跳过'}
  f.after=lambda *a:f.visible.add('087_挑战成功二')
  self.assertEqual(e['FightBeyondRound'](),1);self.assertEqual(f.taps[0],(290,993,50));self.assertEqual(f.now,4100);self.assertNotIn('152_跳过',f.lookups)
 def test_failure_terminal_only_in_battle(self):
  f,e=self.beyond();f.visible={'087_战斗失败一'}
  self.assertEqual(e['FightBeyondRound'](),1);self.assertTrue(e['beyondTerminal'])
  f,e=self.beyond();f.visible={'087_战斗失败一'};f.after=lambda *a:f.visible.add('087_任务页一')
  self.assertEqual(e['ContinueBeyondRound'](),1);self.assertFalse(e['beyondTerminal'])
 def test_gray_reward_before_blue(self):
  f,e=self.beyond();f.visible={'087_灰色领取','087_蓝色领取'}
  self.assertEqual(e['FinishBeyondRewards'](),1);self.assertEqual(f.taps,[(600,900,50)]);self.assertNotIn('087_蓝色领取',f.lookups)
 def test_ten_whole_rounds_then_rewards_not_ten_support_probes(self):
  f,e=self.beyond();events=[]
  for name in ['EnterBeyond','EnterBeyondSupport','InviteBeyondWarriors','ReturnBeyondFromSupport','FightBeyondRound','ContinueBeyondRound','FinishBeyondRewards']:
   e[name]=lambda n=name:events.append(n) or 1
  self.assertEqual(e['ExecuteBeyond'](),1)
  self.assertEqual(events,['EnterBeyond']+['EnterBeyondSupport','InviteBeyondWarriors','ReturnBeyondFromSupport','FightBeyondRound','ContinueBeyondRound']*10+['FinishBeyondRewards'])
  self.assertEqual(f.now,10000)
 def test_completed_continuation_exits_outer_rounds(self):
  f,e=self.beyond();events=[]
  for name in ['EnterBeyond','EnterBeyondSupport','InviteBeyondWarriors','ReturnBeyondFromSupport','FightBeyondRound','FinishBeyondRewards']:
   e[name]=lambda n=name:events.append(n) or 1
  f.visible={'087_已完成一'}
  self.assertEqual(e['ExecuteBeyond'](),1);self.assertEqual(events.count('EnterBeyondSupport'),1);self.assertEqual(f.now,1050)
 def test_phase_and_log_ownership(self):
  f,e=self.beyond();e['worldPhase']='sentinel'
  for task,prefix,name in [(86,'legend','超战士传说86'),(87,'beyond','激战超越极限87'),(71,'earth','地球保卫战71'),(88,'namek','那美克星组队战88')]:
   e['currentTask']=task;e['WorldStage']('阶段验证')
   self.assertEqual(e[prefix+'Phase'],'阶段验证');self.assertEqual(e['worldPhase'],'sentinel');self.assertIn(name,f.logs[-1])
 def test_four_tasks_foreground_recovery_real_dispatch(self):
  from test_foreground import Foreground
  for task,prefix,state in [(86,'legend','超战士状态'),(87,'beyond','极限状态'),(71,'earth','地球保卫状态'),(88,'namek','那美克状态')]:
   fixture=Foreground();fixture.setUp();e=fixture.e
   e.update(Time=lambda:1760000000,Int=int,earthHour=18,earthMinute=0,earthSecond=0)
   load(['common/世界首领状态.mq','common/'+state+'.mq'],e)
   e[prefix+'Count']=7;e[prefix+'Due']=12345;e[prefix+'Failures']=2;e[prefix+'Recoveries']=3;e[prefix+'Restarts']=0;e[prefix+'Terminal']=True
   e.update(currentTask=task,terminalConfirmed=True);fixture.request()
   self.assertTrue(e['HandleForegroundRecovery']());self.assertEqual(e['resumeTask'],task)
   self.assertEqual(e[prefix+'Count'],7);self.assertEqual(e[prefix+'Due'],12345)
   self.assertEqual(e[prefix+'Failures'],3);self.assertEqual(e[prefix+'Recoveries'],4)
   self.assertEqual(e[prefix+'Phase'],'等待恢复');self.assertFalse(e[prefix+'Terminal']);self.assertFalse(e['terminalConfirmed'])
   self.assertIn(('kill','game'),fixture.events);self.assertIn(('run','game'),fixture.events)
if __name__=='__main__':unittest.main()
