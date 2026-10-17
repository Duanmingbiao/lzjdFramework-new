import json
import re
import unittest
from mq_subset import ROOT, load


class NamekTests(unittest.TestCase):
 def setUp(self):
  from test_worldboss import WorldBossTests
  self.f = WorldBossTests(); self.f.setUp(); self.e = self.f.e
  self.f.at(10)
  self.e.update(currentTask=88, namekEnabled=True)
  load(['common/那美克状态.mq', 'flows/088_那美克星组队战/那美克星组队战.mq'], self.e)
  self.e['NewNamekSession']()
  self.e['EnterEnemyHall'] = lambda: 1

 def test_timed_start_exactly_100005(self):
  self.assertEqual(self.e['SelectNamek'](), 0)
  self.f.now = 4999; self.assertEqual(self.e['SelectNamek'](), 0)
  self.f.now = 5000; self.assertEqual(self.e['SelectNamek'](), 88)

 def test_disabled_not_selected(self):
  self.f.at(12); self.e['namekEnabled'] = False
  self.assertEqual(self.e['SelectNamek'](), 0)

 def test_last_thirty_seconds_only_skips_new_dispatch(self):
  self.f.at(23, 59); self.f.now = 30000
  self.assertEqual(self.e['SelectNamek'](), 88)
  self.f.now += 1000
  self.assertEqual(self.e['SelectNamek'](), 0)
  self.assertFalse(self.e['namekDone']); self.assertEqual(self.e['namekCount'], 0)

 def test_next_day_resets_due_to_100005(self):
  self.f.at(12); self.e['CommitNamekTask']()
  expected = self.e['WorldDayStart'](self.e['Time']()) + 122405
  self.assertEqual(self.e['namekDue'], expected)
  self.assertEqual(self.e['SelectNamek'](), 0)
  self.f.stamp += 86400; self.assertEqual(self.e['SelectNamek'](), 88)

 def test_gray_entry_waits_then_terminal_without_commit(self):
  swipes=[]; self.e['Swipe']=lambda *a:swipes.append(a)
  self.f.visible={'088_未开放二'}
  self.assertEqual(self.e['ExecuteNamek'](), 1)
  self.assertEqual(swipes, [(370,1000,370,300,300)])
  self.assertEqual(self.f.now,2050)
  self.assertTrue(self.e['terminalConfirmed']); self.assertEqual(self.e['namekCount'],0)

 def test_entry_requires_recognized_task_page(self):
  self.f.visible={'088_入口一'}
  def after(x,y,w): self.f.visible={'088_未准备二'}
  self.f.after=after
  self.assertEqual(self.e['EnterNamek'](),1)
  self.assertEqual(self.f.taps,[(600,900,500)])
  self.assertFalse(self.e['terminalConfirmed'])

 def test_entry_25sec_unknown_delays_one_hour_without_success(self):
  self.assertEqual(self.e['EnterNamek'](),2)
  self.assertTrue(self.e['namekDeferred']); self.assertFalse(self.e['terminalConfirmed'])
  self.assertGreater(self.f.now,25000)
  self.assertEqual(self.e['namekRetryAt'],self.e['Time']()+3600)

 def test_public_timeout_precedes_entry_retry(self):
  self.e['BusinessExpired']=lambda:self.f.now>=1000
  self.assertEqual(self.e['EnterNamek'](),4)
  self.assertFalse(self.e['namekDeferred']);self.assertFalse(self.f.taps)

 def test_entry_swipe_obeys_game_foreground_gate(self):
  swipes=[]; self.e['Swipe']=lambda *a:swipes.append(a)
  self.e['Sys'].AppIsFront=lambda p:False
  self.e['BusinessExpired']=lambda:self.f.now>=1000
  self.assertEqual(self.e['EnterNamek'](),4)
  self.assertFalse(swipes);self.assertFalse(self.f.taps)

 def test_prepare_unready_then_ready_then_map(self):
  self.f.visible={'088_未准备一'}
  def after(x,y,w):self.f.visible={'088_准备二'} if w==50 else {'088_关卡一'}
  self.f.after=after
  self.assertEqual(self.e['PrepareNamek'](),1)
  self.assertEqual(self.f.taps,[(600,900,50),(600,900,5000)])
  self.assertFalse(self.e['terminalConfirmed'])

 def test_prepare_finished_wait_before_click_and_terminal(self):
  self.f.visible={'088_任务结束二'}
  self.assertEqual(self.e['PrepareNamek'](),1)
  self.assertEqual(self.f.taps,[(600,900,0)]);self.assertEqual(self.f.now,2150)
  self.assertTrue(self.e['terminalConfirmed'])

 def test_five_positions_after_four_quick_probes_then_six_rounds(self):
  self.f.visible={'088_关卡一'}
  self.assertEqual(self.e['RunNamek'](),1)
  positions=[(450,620,50),(580,410,50),(260,280,50),(390,110,50),(660,-50,50)]
  self.assertEqual(self.f.taps,positions*6)
  self.assertEqual(self.f.lookups.count('088_快速战斗'),24)
  self.assertFalse(self.e['terminalConfirmed'])

 def test_quick_fight_and_target_six_keep_order(self):
  self.f.visible={'088_快速战斗','152_开战图标6'}
  def after(x,y,w):
   if (x,y)==(587,982):self.f.visible={'088_蓝框一'}
  self.f.after=after
  self.assertEqual(self.e['RunNamek'](),1)
  self.assertEqual(self.f.taps,[(600,900,500),(398,982,500),(587,982,500),(600,900,500)])
  self.assertFalse(self.e['terminalConfirmed'])

 def test_skip_uses_root725_offset_and_wait(self):
  self.f.visible={'088_跳过'}
  self.f.after=lambda *a:self.f.visible.add('088_蓝框一')
  self.assertEqual(self.e['RunNamek'](),1)
  self.assertEqual(self.f.taps[0],(290,993,50));self.assertGreaterEqual(self.f.now,3550)

 def test_chest_double_click_uses_same_anchor(self):
  self.f.visible={'088_有宝箱'}
  def after(x,y,w):
   if w==500:self.f.visible={'088_蓝框二'}
  self.f.after=after
  self.assertEqual(self.e['RunNamek'](),1)
  self.assertEqual(self.f.taps[:2],[(454,363,50),(454,363,500)])

 def test_empty_chests_only_continue_then_blue_frame_exits_stage(self):
  for variant in ['一','二']:
   self.setUp();self.f.visible={'088_空宝箱'+variant}
   self.f.after=lambda *a:self.f.visible.add('088_蓝框一')
   self.assertEqual(self.e['RunNamek'](),1)
   self.assertEqual(self.f.taps,[(600,900,50),(600,900,500)])
   self.assertFalse(self.e['terminalConfirmed'])

 def test_six_defeats_yield_one_hour_retry_no_completion(self):
  self.f.visible={'088_战斗失败'}
  self.assertEqual(self.e['RunNamek'](),2)
  self.assertEqual(self.f.taps,[(600,900,500)]*6)
  self.assertTrue(self.e['namekDeferred']);self.assertFalse(self.e['terminalConfirmed'])

 def test_blue_frame_precedes_sixth_failure_retry(self):
  self.f.visible={'088_战斗失败'}
  def after(x,y,w):
   if len(self.f.taps)==6:self.f.visible={'088_蓝框一'}
  self.f.after=after
  self.assertEqual(self.e['RunNamek'](),1);self.assertFalse(self.e['namekDeferred'])

 def test_counter_exit_requires_final_page(self):
  self.f.visible={'088_关卡一'}
  self.assertEqual(self.e['RunNamek'](),1)
  self.f.visible.clear()
  self.assertEqual(self.e['FinishNamek'](),4);self.assertFalse(self.e['terminalConfirmed'])

 def test_finish_map_or_blue_are_explicit_terminal(self):
  for pattern in ['088_关卡一','088_关卡二','088_蓝框一','088_蓝框二']:
   self.setUp();self.f.visible={pattern}
   self.assertEqual(self.e['FinishNamek'](),1);self.assertTrue(self.e['terminalConfirmed'])
   self.assertEqual(self.e['namekCount'],0)

 def test_finish_ended_page_click_is_not_alone_success(self):
  self.f.visible={'088_任务结束一'}
  def after(x,y,w):self.f.visible={'088_关卡二'}
  self.f.after=after
  self.assertEqual(self.e['FinishNamek'](),1)
  self.assertEqual(self.f.taps,[(600,900,0)]);self.assertEqual(self.f.now,2050)

 def test_foreground_interrupt_blocks_click_and_terminal(self):
  self.f.interrupt=True;self.f.visible={'088_蓝框一'}
  self.assertEqual(self.e['FinishNamek'](),4);self.assertFalse(self.f.taps)
  self.assertFalse(self.e['terminalConfirmed'])

 def public(self):
  load(['common/任务状态.mq','common/任务注册.mq','common/任务调度.mq'],self.e)
  self.e['RegisterTasks']();self.e['NewSession']()
  self.e.update(mailEnabled=False,rewardEnabled=False,signEnabled=False,monthEnabled=False,
                friendEnabled=False,qfriendEnabled=False,EnsureGameHall=lambda:1,ReturnToHall=lambda:1)
  self.e['RestartGame']=lambda:None

 def test_recovery_prioritized_even_when_disabled_before_time(self):
  self.public();self.e.update(namekEnabled=False,resumeTask=88)
  self.assertEqual(self.e['SelectDueTask'](),88)

 def test_public_commit_requires_hall_and_terminal(self):
  self.public();self.e['SaveCurrentTask'](88)
  self.assertFalse(self.e['CommitTask'](True))
  self.e['terminalConfirmed']=True
  self.assertFalse(self.e['CommitTask'](False));self.assertEqual(self.e['namekCount'],0)
  self.assertTrue(self.e['CommitTask'](True));self.assertEqual(self.e['namekCount'],1)

 def test_retry_scheduling_requires_hall_and_foreground_gate(self):
  self.e.update(currentTask=88,resumeTask=88)
  self.e['NamekRetry']('test')
  self.assertFalse(self.e['ScheduleNamekRetry'](False));self.assertEqual(self.e['resumeTask'],88)
  self.e['BeginForegroundCommit']=lambda:False
  self.assertFalse(self.e['ScheduleNamekRetry'](True));self.assertEqual(self.e['namekCount'],0)

 def test_scheduler_yields_retry_then_runs_another_task(self):
  self.public();self.f.now=5000
  self.e.update(mailEnabled=True,mailFirst=True,mailDue=0,mailInterval=10,mailCount=0)
  seen=[]
  def dispatch(t):
   seen.append(t)
   if t==88:return self.e['NamekRetry']('入口失败')
   self.e['terminalConfirmed']=True;return 1
  self.e['DispatchTask']=dispatch
  self.e['SchedulerStep']()
  self.assertEqual(self.e['namekCount'],0);self.assertEqual(self.e['resumeTask'],0)
  self.assertEqual(self.e['namekDue'],self.e['Time']()+3600)
  self.e['SchedulerStep']();self.assertEqual(seen,[88,168])
  self.assertEqual(self.e['mailCount'],1)

 def test_retry_hall_failure_restores_original_task(self):
  self.public();self.f.now=5000
  self.e['ReturnToHall']=lambda:4
  self.e['DispatchTask']=lambda t:self.e['NamekRetry']('入口失败')
  self.e['SchedulerStep']()
  self.assertEqual(self.e['resumeTask'],88);self.assertEqual(self.e['namekCount'],0)
  self.assertEqual(self.e['namekRecoveries'],1);self.assertFalse(self.e['namekDeferred'])

 def test_business_stage_log_does_not_mutate_other_task_phase(self):
  old=self.e['worldPhase'];self.e['WorldStage']('那美克挑战')
  self.assertEqual(self.e['worldPhase'],old);self.assertEqual(self.e['namekPhase'],'那美克挑战')
  self.assertIn('那美克星组队战88',self.f.logs[-1])

 def test_registered_recognition_matches_saved_evidence(self):
  evidence=json.loads((ROOT/'flows/088_那美克星组队战/evidence/图色转换.json').read_text('utf-8-sig'))
  source=(ROOT/'common/图色参数.mq').read_text('utf-8-sig')
  self.assertEqual(len(evidence),21)
  for item in evidence:
   body=re.search(r'Case "'+item['name']+r'"(.*?)(?=\n    Case |\n    End Select)',source,re.S)[1]
   args=','.join('"'+x+'"' if isinstance(x,str) else str(x) for x in item['definition'])
   self.assertIn('FindMultiColor '+args+',foundX,foundY',body)
  self.assertEqual([x['name'] for x in evidence if x['definition'][6]==0],['088_小怪详情','088_有宝箱'])


if __name__=='__main__':unittest.main()
