import unittest
from mq_subset import ROOT,load


class BeyondTests(unittest.TestCase):
 def setUp(self):
  from test_worldboss import WorldBossTests
  self.f=WorldBossTests();self.f.setUp();self.e=self.f.e
  self.e.update(currentTask=87,beyondEnabled=True)
  load(['common/极限状态.mq','flows/087_激战超越极限/激战超越极限.mq'],self.e)
  self.e['NewBeyondSession']();self.e['EnterEnemyHall']=lambda:1

 def test_first_run_then_24_hour_due(self):
  self.assertEqual(self.e['SelectBeyond'](),87);self.e['CommitBeyondTask']();self.assertEqual(self.e['SelectBeyond'](),0)

 def test_gray_unopened_is_professional_terminal(self):
  self.f.visible={'087_未开启一'};self.assertEqual(self.e['ExecuteBeyond'](),1);self.assertTrue(self.e['terminalConfirmed'])

 def test_completed_page_goes_directly_to_reward(self):
  self.f.visible={'087_已完成一'}
  def after(x,y,w):
   if (x,y)==(1075,-75):self.f.visible={'087_灰色领取'}
  self.f.after=after;self.assertEqual(self.e['ExecuteBeyond'](),1);self.assertIn('英雄奖励',self.e['beyondReason'])

 def test_static_integration(self):
  project=(ROOT/'project.json').read_text('utf-8-sig');ui=(ROOT/'ui/最小配置.uip').read_text('utf-8-sig')
  self.assertIn('flows/087_激战超越极限/激战超越极限.mq',project);self.assertIn('名称:"激战超越极限启用"',ui)


if __name__=='__main__':unittest.main()
