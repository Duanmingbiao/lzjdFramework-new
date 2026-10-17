import unittest
from mq_subset import ROOT,load


class LegendTests(unittest.TestCase):
 def setUp(self):
  from test_worldboss import WorldBossTests
  self.f=WorldBossTests();self.f.setUp();self.e=self.f.e
  self.e.update(currentTask=86,legendEnabled=True)
  load(['common/超战士状态.mq','flows/086_超战士传说/超战士传说.mq'],self.e)
  self.e['NewLegendSession']()
  self.e['EnterEnemyHall']=lambda:1

 def test_disabled_config_not_selected(self):
  self.e['legendEnabled']=False;self.assertEqual(self.e['SelectLegend'](),0)

 def test_first_run_then_24_hour_due(self):
  self.assertEqual(self.e['SelectLegend'](),86);self.e['CommitLegendTask']();self.assertEqual(self.e['SelectLegend'](),0);self.assertEqual(self.e['legendCount'],1)

 def test_gray_unopened_is_terminal_without_direct_commit(self):
  self.f.visible={'086_未开启一'};self.assertEqual(self.e['ExecuteLegend'](),1);self.assertTrue(self.e['legendTerminal']);self.assertTrue(self.e['terminalConfirmed']);self.assertEqual(self.e['legendCount'],0)

 def test_no_task_switches_difficulty_once_then_terminal(self):
  self.f.visible={'086_无任务一'};self.assertEqual(self.e['ExecuteLegend'](),1);self.assertEqual(self.f.taps,[(120,718,2000)]);self.assertIn('困难',self.e['legendReason'])

 def test_battle_failure_is_recovery_not_success(self):
  self.f.visible={'086_界面一'}
  def after(x,y,w):
   if w==500:self.f.visible={'086_战斗失败一'}
   elif w==1000:self.f.visible.clear()
  self.f.after=after;self.assertEqual(self.e['ExecuteLegend'](),4);self.assertFalse(self.e['terminalConfirmed']);self.assertEqual(self.e['legendCount'],0)

 def test_static_integration_and_ui(self):
  project=(ROOT/'project.json').read_text('utf-8-sig');ui=(ROOT/'ui/最小配置.uip').read_text('utf-8-sig');flow=(ROOT/'flows/086_超战士传说/超战士传说.mq').read_text('utf-8-sig')
  self.assertIn('"common/超战士状态.mq"',project);self.assertIn('"flows/086_超战士传说/超战士传说.mq"',project);self.assertIn('名称:"超战士传说启用"',ui);self.assertIn('项目不复制其完成标记',flow)


if __name__=='__main__':unittest.main()
