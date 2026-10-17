"""Native boss phase exits are not generic completion or OCR fallbacks."""
import unittest
import test_worldboss
import test_crossboss

class BossExitTests(unittest.TestCase):
 def world(self):
  f=test_worldboss.WorldBossTests();f.setUp();return f,f.e
 def cross(self):
  fixture=test_crossboss.CrossBossTests();fixture.setUp();return fixture,fixture.f,fixture.e
 def test_world_only_exact_zero_words_stop_without_click(self):
  for text in ['挑战次数0','挑战次数|0']:
   f,e=self.world();f.visible={'070_扫荡一','070_复活一'};f.text=text
   self.assertEqual(e['SweepWorldBoss'](),1);self.assertFalse(f.taps);self.assertFalse(e['terminalConfirmed'])
   self.assertNotIn('070_复活一',f.lookups)
 def test_world_blank_nonzero_and_similar_text_do_not_mean_zero(self):
  for text in ['',None,'挑战次数10','挑战次数1','0','次数不够','挑战次数 0','挑战次数|0/5']:
   f,e=self.world();f.visible={'070_扫荡一'};f.text=text
   self.assertEqual(e['SweepWorldBoss'](),1);self.assertEqual(len(f.taps),48)
   self.assertFalse(any('OCR命中=' in line for line in f.logs));self.assertFalse(e['terminalConfirmed'])
 def test_world_native_wait_exit_still_requires_reward_terminal(self):
  f,e=self.world()
  for name in ['EnterEnemyHall','EnterBossPage','BuyWorldBossAttempts']:e[name]=lambda *a:1
  f.visible={'070_无奖一'}
  self.assertEqual(e['ExecuteWorldBoss'](),1);self.assertGreater(f.now,30000)
  self.assertTrue(e['terminalConfirmed']);self.assertEqual(e['worldCount'],0)
 def test_world_native_wait_exit_unknown_rewards_never_complete(self):
  f,e=self.world()
  for name in ['EnterEnemyHall','EnterBossPage','BuyWorldBossAttempts']:e[name]=lambda *a:1
  self.assertEqual(e['ExecuteWorldBoss'](),4);self.assertFalse(e['terminalConfirmed']);self.assertEqual(e['worldCount'],0)
 def test_cross_unknown_preparation_before_threshold_is_not_three_second_exit(self):
  _,f,e=self.cross()
  self.assertEqual(e['RunCrossPreparation'](),4);self.assertGreaterEqual(f.now,120000)
  self.assertEqual(e['crossTerminalReason'],'');self.assertFalse(f.taps)
 def test_cross_ten_results_without_exit_uses_native_terminal(self):
  _,f,e=self.cross();f.visible={'083_预备结果一'}
  self.assertEqual(e['RunCrossPreparation'](),1);self.assertEqual(f.taps,[(600,900,500)]*10)
  self.assertIn('超过3000',e['crossTerminalReason']);self.assertEqual(e['crossCount'],0)
 def test_cross_native_preparation_exit_hall_failure_recovers_not_commits(self):
  fixture,f,e=self.cross();fixture.public();f.visible={'083_预备一'};restarts=[]
  e.update(resumeTask=83,EnterEnemyHall=lambda:1,EnsureGameHall=lambda:1,ReturnToHall=lambda:4,DispatchTask=lambda t:e['ExecuteCrossBoss'](),RestartGame=lambda:restarts.append(e['resumeTask']))
  e['SchedulerStep']();self.assertEqual(restarts,[83]);self.assertEqual(e['crossCount'],0);self.assertEqual(e['resumeTask'],83)
 def test_cross_native_preparation_exit_hall_success_commits_once_and_unblocks(self):
  fixture,f,e=self.cross();fixture.public();f.visible={'083_预备一'}
  e.update(resumeTask=83,EnterEnemyHall=lambda:1,EnsureGameHall=lambda:1,ReturnToHall=lambda:1,DispatchTask=lambda t:e['ExecuteCrossBoss']())
  e['SchedulerStep']();self.assertEqual(e['crossCount'],1);self.assertEqual(e['resumeTask'],0)
  e['SelectLegend']=lambda:86
  self.assertEqual(e['SelectDueTask'](),86);self.assertEqual(e['crossRecoveries'],0)
 def test_cross_formal_wait_exit_still_requires_board_and_rewards(self):
  _,f,e=self.cross();e.update(EnterEnemyHall=lambda:1,crossMode=1,EnterCrossBoss=lambda:1,BuyCrossBossAttempts=lambda:1)
  self.assertEqual(e['ExecuteCrossBoss'](),4);self.assertFalse(e['terminalConfirmed']);self.assertEqual(e['crossTerminalReason'],'')
 def test_public_deadline_and_foreground_interrupt_override_native_exits(self):
  for interrupted in [False,True]:
   f,e=self.world();f.now=120000 if not interrupted else 0;f.interrupt=interrupted
   self.assertEqual(e['SweepWorldBoss'](),4);self.assertFalse(e['terminalConfirmed'])
   _,f,e=self.cross();f.now=120000 if not interrupted else 0;f.interrupt=interrupted;f.visible={'083_预备一'}
   self.assertEqual(e['RunCrossPreparation'](),4);self.assertEqual(e['crossTerminalReason'],'');self.assertFalse(f.taps)
if __name__=='__main__':unittest.main()
