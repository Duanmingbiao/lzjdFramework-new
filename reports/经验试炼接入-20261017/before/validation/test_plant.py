import unittest,json,re
from mq_subset import ROOT,load
import test_worldboss

class PlantTests(unittest.TestCase):
 def setUp(self):
  self.f=test_worldboss.WorldBossTests();self.f.setUp();self.e=self.f.e
  def match(n):self.f.now+=10;return self.f.match(n)
  self.e.update(MatchPattern=match,currentTask=154,businessStarted=0,businessLimit=120000,ForegroundInterrupted=lambda:self.f.interrupt)
  load(['common/种仙豆状态.mq','flows/154_种仙豆/种仙豆.mq','common/运行计时.mq'],self.e)
  self.e['NewPlantSession']()
 def test_single_config_default_off_and_original_key(self):
  self.e['ReadUIConfig']=lambda k,d:d;self.e['LoadPlantSettings']();self.assertFalse(self.e['plantEnabled'])
  self.e['ReadUIConfig']=lambda k,d:'true' if k=='日常_种仙豆' else d;self.e['LoadPlantSettings']();self.assertTrue(self.e['plantEnabled'])
 def test_six_am_schedule_before_at_and_after(self):
  self.e['plantEnabled']=True
  for h,m,expected in [(5,59,0),(6,0,154),(12,0,154)]:
   self.f.at(h,m);self.e['NewPlantSession']();self.assertEqual(self.e['SelectPlant'](),expected)
 def test_entry_requires_actual_page(self):
  self.f.visible={'154_P00'};self.assertEqual(self.e['EnterPlant'](),1);self.assertFalse(self.f.taps)
 def test_entry_original_click1500_then_page(self):
  self.e['ReturnToHall']=lambda:1;self.f.visible={'153_大厅一','154_入口二'}
  self.f.after=lambda *a:setattr(self.f,'visible',{'154_P00'})
  self.assertEqual(self.e['EnterPlant'](),1);self.assertEqual(self.f.taps,[(600,900,1500)])
 def test_entry_unknown60sec_failure_not_complete(self):
  self.e['ReturnToHall']=lambda:1
  self.assertEqual(self.e['EnterPlant'](),4);self.assertGreater(self.f.now,62000);self.assertFalse(self.e['terminalConfirmed'])
 def test_confirmation_wait1000_no_click(self):
  self.f.visible={'154_P00'};self.assertEqual(self.e['ConfirmPlantPage'](),1);self.assertEqual(self.f.now,1010);self.assertFalse(self.f.taps)
 def test_six_collection_attempts_switch_upgrade_only(self):
  self.f.visible={'154_P00'};self.assertEqual(self.e['RunPlant'](),1)
  self.assertEqual(self.f.taps,[(577,830,1000)]*6)
  self.assertGreater(self.f.now,20000);self.assertFalse(self.e['terminalConfirmed'])
 def test_reward_switches_phase_and_resets_public_not_local_timer(self):
  self.f.visible={'154_P06'}
  def after(*a):self.f.visible={'154_P03'}
  self.f.after=after;self.assertEqual(self.e['RunPlant'](),1)
  self.assertEqual(self.f.taps,[(150,50,50)]);self.assertGreater(self.e['businessStarted'],0);self.assertFalse(self.e['terminalConfirmed'])
 def test_coin_page_and_coin_confirmation_order(self):
  self.f.visible={'154_P06'}
  def after(*a):
   if len(self.f.taps)==1:self.f.visible={'154_P01','154_P02','154_P03'}
  self.f.after=after;self.assertEqual(self.e['RunPlant'](),1)
  self.assertEqual(self.f.taps,[(150,50,50),(850,-40,1500),(600,900,1000)])
 def test_stone_or_max_does_not_click_after_phase_switch(self):
  for name in ['154_P03','154_P04','154_P05']:
   self.setUp();self.f.visible={'154_P06'};self.f.after=lambda *a:setattr(self.f,'visible',{name})
   self.assertEqual(self.e['RunPlant'](),1);self.assertEqual(self.f.taps,[(150,50,50)]);self.assertFalse(self.e['terminalConfirmed'])
 def test_20sec_unknown_is_only_phase_exit(self):
  self.assertEqual(self.e['RunPlant'](),1);self.assertGreater(self.f.now,20000);self.assertFalse(self.e['terminalConfirmed']);self.assertFalse(self.f.taps)
 def test_final_unknown10sec_requests_recovery_not_complete(self):
  self.assertEqual(self.e['FinishPlant'](),4);self.assertGreater(self.f.now,10000);self.assertFalse(self.e['terminalConfirmed'])
 def test_final_reward500_close_stone500_then_main500(self):
  self.f.visible={'154_P06','154_P04','154_P00'}
  self.assertEqual(self.e['FinishPlant'](),1);self.assertEqual(self.f.taps,[(150,50,500),(570,920,500)])
  self.assertGreaterEqual(self.f.now,1500);self.assertTrue(self.e['terminalConfirmed']);self.assertEqual(self.e['plantCount'],0)
 def test_final_max_confirmed_with500_wait(self):
  self.f.visible={'154_P05'};self.assertEqual(self.e['FinishPlant'](),1);self.assertGreaterEqual(self.f.now,500)
 def test_interruption_and_late_progress_do_not_commit(self):
  self.f.interrupt=True
  for fn in ['EnterPlant','ConfirmPlantPage','RunPlant','FinishPlant']:
   self.assertEqual(self.e[fn](),4)
  self.assertFalse(self.e['ResetPlantTimer']());self.assertFalse(self.e['terminalConfirmed']);self.assertFalse(self.f.taps)
  self.f.interrupt=False;self.f.now=120001;self.assertFalse(self.e['ResetPlantTimer']())
 def test_public_commit_gates_and_session_latch(self):
  load(['common/任务状态.mq','common/任务注册.mq'],self.e)
  self.e['SaveCurrentTask'](154);self.assertFalse(self.e['CommitTask'](True));self.e['ConfirmPlantExit']('confirmed')
  self.assertFalse(self.e['CommitTask'](False));self.assertTrue(self.e['CommitTask'](True));self.assertEqual(self.e['plantCount'],1)
  self.e['plantEnabled']=True;self.f.stamp+=86400;self.assertEqual(self.e['SelectPlant'](),0)
 def test_shared_foreground_recovery_keeps154(self):
  import test_foreground
  fg=test_foreground.Foreground();fg.setUp();fg.e.update(Time=lambda:1760000000,WorldDayStart=lambda n:n-3600,CStr=str,WorldLog=fg.logs.append,WorldStage=lambda s:None)
  load(['common/种仙豆状态.mq'],fg.e);fg.e['NewPlantSession']();fg.e['SaveCurrentTask'](154);fg.request()
  self.assertTrue(fg.e['HandleForegroundRecovery']());self.assertEqual(fg.e['SelectDueTask'](),154)
  self.assertEqual((fg.e['plantCount'],fg.e['plantRecoveries'],fg.e['plantRestarts']),(0,1,1))
 def test_raw_colors_append_only_and_coin_similarity095(self):
  records=json.loads((ROOT/'flows/154_种仙豆/evidence/图色转换.json').read_text('utf8'));self.assertEqual(len(records),9)
  old=json.loads((ROOT/'reports/种仙豆接入-20261017/before/图色参数.json').read_text('utf8'));now=[r for r in json.loads((ROOT/'evidence/图色参数.json').read_text('utf8')) if not r['name'].startswith(('012_','150_','155_'))];self.assertEqual(now,old+records)
  raw=(ROOT/'flows/154_种仙豆/evidence/root713静态重建.txt').read_text('utf8')
  colors=list(dict.fromkeys(re.findall(r'L\d+_1 = "([0-9A-F]{6}-[0-9A-F]{6})"\n\s*L\d+_1 = "([^"\n]+)"',raw)))
  self.assertEqual([(r['definition'][4],r['definition'][5]) for r in records[:7]],colors)
  self.assertEqual([r['definition'][7] for r in records[:7]],[0.9,0.95,0.9,0.9,0.9,0.9,0.9])
 def test_ui_only_original_checkbox_added_default_off(self):
  def controls(t):return {re.search('名称:"([^"]+)"',body)[1]:(kind,body) for kind,body in re.findall(r'(输入框|下拉框|多选框):\{([^{}]+)\}',t)}
  before=controls((ROOT/'reports/种仙豆接入-20261017/before/ui/最小配置.uip').read_text('utf-8-sig'));after=controls((ROOT/'ui/最小配置.uip').read_text('utf-8-sig'))
  self.assertEqual({k:after[k] for k in before},before);self.assertEqual(set(after)-set(before),{'SlJb','日常_种仙豆','Lzdmx','Lzdmx许愿'} | {'日常_蛇道_困难关卡', '日常_蛇道_跳过动画', '日常_蛇道_普通关卡', '日常_蛇道_补打', '日常_蛇道_特殊效果', '日常_蛇道', '日常_蛇道_雇佣战士_个', '日常_蛇道_时间', '日常_蛇道_分钟', '日常_蛇道_雇佣战士_位置', '日常_蛇道_模式', '日常_蛇道_失败次数', '日常_蛇道_雇佣战士_行'});self.assertIn('选中:false',after['日常_种仙豆'][1])
 def test_no_new_apis_or_public_mutation_and_unique_registration(self):
  flow=(ROOT/'flows/154_种仙豆/种仙豆.mq').read_text('utf-8-sig');self.assertNotRegex(flow,r'OcrEx|paddle|Image\.Ocr|CommitTask|KillApp|RunApp|businessStarted\s*=')
  cfg=json.loads((ROOT/'project.json').read_text('utf8'));self.assertEqual(cfg['registeredTasks'].count(154),1)
