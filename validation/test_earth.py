import json
import re
import unittest
from types import SimpleNamespace
from mq_subset import ROOT, load


class EarthTests(unittest.TestCase):
 def setUp(self):
  from test_worldboss import WorldBossTests
  self.f=WorldBossTests();self.f.setUp();self.e=self.f.e;self.f.at(12)
  self.weekday=2
  self.e.update(currentTask=71,earthEnabled=True,earthTimeMode=0,earthBuyConfig=0,
                DateTime=SimpleNamespace(WeekDay=lambda:self.weekday))
  # Let polling consume mocked wall-clock time just as the device does.
  def match(name):self.f.now+=10;return self.f.match(name)
  self.e['MatchPattern']=match
  load(['common/地球保卫状态.mq','flows/071_地球保卫战/地球保卫战.mq'],self.e)
  self.e['NewEarthSession']();self.e['EnterEnemyHall']=lambda:1

 def test_configured_times_and_immediate(self):
  day=self.e['WorldDayStart'](self.e['Time']())
  for mode,seconds in [(0,64800),(1,68400),(2,72000),(3,75000)]:
   self.e['earthTimeMode']=mode;self.e['NewEarthSession']();self.assertEqual(self.e['earthDue'],day+seconds)
   self.assertEqual(self.e['SelectEarth'](),0)
  self.e['earthTimeMode']=4;self.e['NewEarthSession']();self.assertEqual(self.e['SelectEarth'](),71)

 def test_disabled_or_raw_weekday_one_skips_without_completion(self):
  self.f.at(20);self.e['earthEnabled']=False;self.assertEqual(self.e['SelectEarth'](),0)
  self.e['earthEnabled']=True;self.weekday=1;self.assertEqual(self.e['SelectEarth'](),0)
  self.assertEqual(self.e['earthCount'],0)

 def test_normal_before18_repeats_at18_then_nextday(self):
  self.e['earthTimeMode']=4;self.e['NewEarthSession']();self.e['CommitEarthTask']()
  self.assertEqual(self.e['earthDue'],self.e['WorldDayStart'](self.e['Time']())+64800)
  self.assertEqual(self.e['SelectEarth'](),0)
  self.f.at(18);self.assertEqual(self.e['SelectEarth'](),71)
  self.e['CommitEarthTask']();self.assertEqual(self.e['SelectEarth'](),0)

 def test_prestart_terminal_does_not_schedule_evening_repeat(self):
  self.e['earthTimeMode']=4;self.e['NewEarthSession']();self.e['earthPrestart']=True
  self.e['CommitEarthTask']();self.assertEqual(self.e['earthDue'],self.e['WorldDayStart'](self.e['Time']())+86400)

 def test_buy_runtime_survives_recovery_and_resets_on_new_day(self):
  self.e.update(earthBuyConfig=3,earthBuyRuntime=0)
  self.e['RecoverEarthTask']();self.assertEqual(self.e['earthBuyRuntime'],0)
  self.f.stamp+=86400;self.e['SelectEarth']();self.assertEqual(self.e['earthBuyRuntime'],3)

 def test_entry_click_stops_scrolling_after_first_entry(self):
  swipes=[];self.e['Swipe']=lambda *a:swipes.append(a)
  self.f.visible={'071_入口'}
  self.f.after=lambda *a:self.f.visible.clear()
  self.assertEqual(self.e['EnterEarth'](),4)
  self.assertEqual(len(swipes),1);self.assertEqual(self.f.taps,[(600,900,500)])

 def test_entry_order_quick_join_chat_checkbox_then_confirm(self):
  self.f.visible={'071_快速加入','071_聊天','071_未勾扫荡','071_已勾扫荡'}
  self.assertEqual(self.e['EnterEarth'](),1)
  self.assertEqual(self.f.taps,[(360,1100,500),(25,1111,500),(600,1200,500)])
  self.assertFalse(self.e['terminalConfirmed']);self.assertEqual(self.e['earthMode'],1)

 def test_prestart_is_explicit_terminal_no_purchase(self):
  self.f.visible={'071_未开始'}
  self.e['BuyEarthAttempts']=lambda:self.fail('prestart must return')
  self.assertEqual(self.e['ExecuteEarth'](),1)
  self.assertTrue(self.e['terminalConfirmed']);self.assertFalse(self.f.taps)
  self.assertEqual(self.e['earthCount'],0)

 def test_unknown_entry20sec_is_recovery_not_success(self):
  self.assertEqual(self.e['EnterEarth'](),4);self.assertGreater(self.f.now,20000)
  self.assertFalse(self.e['terminalConfirmed'])

 def test_foreground_gate_blocks_swipe(self):
  swipes=[];self.e['Swipe']=lambda *a:swipes.append(a)
  self.e['Sys'].AppIsFront=lambda p:False
  self.e['BusinessExpired']=lambda:self.f.now>=1000
  self.assertEqual(self.e['EnterEarth'](),4);self.assertFalse(swipes)

 def purchase(self,mode,text):
  self.e['earthBuyRuntime']=mode;self.e['earthBuyConfig']=mode
  self.f.text=text;self.f.visible={'071_已勾扫荡'};self.reads=[]
  def ocr(*a):self.reads.append(a);return self.f.text
  self.e['Image'].OcrText=ocr
  def after(x,y,w):
   if (x,y)==(600,1150):self.f.visible={'071_购买弹窗'}
   if (x,y) in [(290,1224),(589,917)]:self.f.visible={'071_已勾扫荡'}
  self.f.after=after
  return self.e['BuyEarthAttempts']()

 def test_disabled_purchase_never_reads_or_clicks(self):
  self.assertEqual(self.e['BuyEarthAttempts'](),1);self.assertFalse(self.f.taps)

 def test_all_purchase_counts_prices_offsets_and_three_ocr_reads(self):
  for mode,adds,price in [(1,1,40),(2,3,100),(3,5,200),(4,7,360),(5,9,560)]:
   self.setUp();self.assertEqual(self.purchase(mode,str(price)),1)
   self.assertEqual(self.f.taps,[(600,1150,1000)]+[(315,1045,200)]*adds+[(290,1224,0)])
   self.assertEqual(len(self.reads),3);self.assertEqual(self.reads[0][:4],(364,774,422,800))
   self.assertEqual(self.e['earthBuyRuntime'],0);self.assertEqual(self.e['earthBuyConfig'],mode)

 def test_blank_non_numeric_or_mismatch_only_closes_purchase(self):
  for text in ['', 'unknown', '39', '560']:
   self.setUp();self.assertEqual(self.purchase(1,text),1)
   self.assertEqual(self.f.taps[-1],(589,917,0));self.assertNotIn((290,1224,0),self.f.taps)
   self.assertFalse(self.e['terminalConfirmed'])

 def test_native_floor_number_semantics(self):
  self.assertEqual(self.purchase(1,'40.9'),1);self.assertEqual(self.f.taps[-1],(290,1224,0))

 def test_repeated_purchase_popup_never_confirms_twice(self):
  self.e['earthBuyRuntime']=1;self.f.text='40';self.f.visible={'071_购买弹窗'}
  def after(x,y,w):
   if (x,y)==(589,917):self.f.visible={'071_已勾扫荡'}
  self.f.after=after
  self.assertEqual(self.e['BuyEarthAttempts'](),1)
  self.assertEqual(self.f.taps.count((290,1224,0)),1);self.assertEqual(self.f.taps[-1],(589,917,0))

 def test_unknown_purchase20sec_does_not_clear_unattempted_config(self):
  self.e['earthBuyRuntime']=2
  self.assertEqual(self.e['BuyEarthAttempts'](),4)
  self.assertEqual(self.e['earthBuyRuntime'],2);self.assertFalse(self.e['terminalConfirmed'])

 def test_sweep_then_gray_then_challenge_then_no_attempts(self):
  self.e['earthMode']=1;self.f.visible={'071_可扫荡'}
  def after(x,y,w):
   if (x,y)==(500,1100):self.f.visible={'071_扫荡灰色','071_可挑战'}
   if (x,y)==(200,1100):self.f.visible={'071_挑战灰色'}
  self.f.after=after
  self.assertEqual(self.e['RunEarth'](),1)
  self.assertEqual(self.f.taps,[(500,1100,3000),(200,1100,3000)])
  self.assertTrue(self.e['terminalConfirmed']);self.assertEqual(self.e['earthCount'],0)

 def test_gray_challenge_not_terminal_before_stage_two(self):
  self.e['earthMode']=1;self.f.visible={'071_挑战灰色'}
  self.assertEqual(self.e['RunEarth'](),4);self.assertFalse(self.e['terminalConfirmed'])

 def test_family106_second_variant_clicks_own_anchor(self):
  self.e['earthMode']=2;self.f.visible={'071_开战二'}
  self.f.after=lambda *a:self.f.visible.add('071_挑战灰色')
  self.assertEqual(self.e['RunEarth'](),1);self.assertEqual(self.f.taps,[(600,900,500)])

 def test_supporting_battle_order_and_result_are_not_terminal(self):
  self.e['earthMode']=2;self.f.visible={'071_少人','071_暂停','071_退出','071_战斗结束'}
  def after(x,y,w):
   if (x,y)==(145,58):self.f.visible.clear()
  self.f.after=after
  self.assertEqual(self.e['RunEarth'](),4)
  self.assertEqual(self.f.taps,[(600,900,2000),(289,910,200),(600,900,2000),(145,58,200)])
  self.assertFalse(self.e['terminalConfirmed'])

 def test_150second_inactivity_under_long_public_limit(self):
  self.e.update(earthMode=2,BusinessExpired=lambda:self.f.now>=500000)
  self.assertEqual(self.e['RunEarth'](),4);self.assertGreater(self.f.now,150000)
  self.assertLess(self.f.now,151000);self.assertFalse(self.e['terminalConfirmed'])

 def test_repeated_sweeps_do_not_reset_public_limit(self):
  self.e['earthMode']=1;self.f.visible={'071_可扫荡'}
  self.assertEqual(self.e['RunEarth'](),4)
  self.assertGreaterEqual(self.f.now,120000);self.assertLess(self.f.now,124000)
  self.assertFalse(self.e['terminalConfirmed'])

 def public(self):
  load(['common/任务状态.mq','common/任务注册.mq','common/任务调度.mq'],self.e)
  self.e['RegisterTasks']();self.e['NewSession']()

 def test_resume_overrides_weekday_and_disabled_switch(self):
  self.public();self.e.update(earthEnabled=False,resumeTask=71);self.weekday=1
  self.assertEqual(self.e['SelectDueTask'](),71)

 def test_terminal_and_hall_required_for_commit(self):
  self.public();self.e['SaveCurrentTask'](71)
  self.assertFalse(self.e['CommitTask'](True));self.e['terminalConfirmed']=True
  self.assertFalse(self.e['CommitTask'](False));self.assertEqual(self.e['earthCount'],0)
  self.assertTrue(self.e['CommitTask'](True));self.assertEqual(self.e['earthCount'],1)

 def test_scheduler_hall_failure_saves_original_without_count(self):
  self.public();self.e.update(resumeTask=71,EnsureGameHall=lambda:1,ReturnToHall=lambda:4,RestartGame=lambda:None)
  def dispatch(t):self.e['terminalConfirmed']=True;return 1
  self.e['DispatchTask']=dispatch;self.e['SchedulerStep']()
  self.assertEqual(self.e['resumeTask'],71);self.assertEqual(self.e['earthCount'],0)

 def test_stage_updates_only_earth_task(self):
  old=self.e['worldPhase'];self.e['WorldStage']('地球挑战')
  self.assertEqual(self.e['worldPhase'],old);self.assertEqual(self.e['earthPhase'],'地球挑战')
  self.assertIn('地球保卫战71',self.f.logs[-1])

 def test_recognition_evidence_and_result_rectangle(self):
  rows=json.loads((ROOT/'flows/071_地球保卫战/evidence/图色转换.json').read_text('utf-8-sig'))
  source=(ROOT/'common/图色参数.mq').read_text('utf-8-sig');self.assertEqual(len(rows),17)
  for item in rows:
   body=re.search(r'Case "'+item['name']+r'"(.*?)(?=\n    Case |\n    End Select)',source,re.S)[1]
   args=','.join('"'+x+'"' if isinstance(x,str) else str(x) for x in item['definition'])
   self.assertIn('FindMultiColor '+args+',foundX,foundY',body)
  result=next(x for x in rows if x['name']=='071_战斗结束')
  self.assertEqual(result['definition'][:4],[29,237,691,628])


if __name__=='__main__':unittest.main()
