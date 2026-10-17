import unittest,json,re
from mq_subset import ROOT,load
import test_worldboss
E=ROOT/'flows/092_异时空试炼/evidence'
class YskTests(unittest.TestCase):
 def setUp(self):
  self.f=test_worldboss.WorldBossTests();self.f.setUp();self.e=self.f.e;self.swipes=[]
  def match(n):self.f.now+=10;return self.f.match(n)
  self.e.update(MatchPattern=match,currentTask=92,ReadUIConfig=lambda k,d:d,ForegroundInterrupted=lambda:self.f.interrupt,businessStarted=0,businessLimit=120000,Swipe=lambda *a:self.swipes.append(a),ReturnToHall=lambda:1,resumeTask=92)
  self.e['Sys'].IsRunning=lambda p:True
  load(['common/异时空试炼状态.mq','flows/092_异时空试炼/异时空试炼.mq','common/运行计时.mq'],self.e)
  self.e['LoadYskSettings']();self.e['NewYskSession']()
 def interrupt_after(self,n=1):
  def tap(*a):
   if len(self.f.taps)>=n:self.f.interrupt=True
  self.f.after=tap
 def test_config_original_defaults(self):
  self.assertFalse(self.e['yskEnabled']);self.assertEqual((self.e['yskMinutes'],self.e['yskInterval']),(2,30))
 def test_config_zero_and_numeric_floor(self):
  self.e['ReadUIConfig']=lambda k,d:{'SlYsk':True,'SlYsk挑战时长':'0','SlYsk间隔':'3.9'}.get(k,d);self.e['LoadYskSettings']();self.assertTrue(self.e['yskEnabled']);self.assertEqual((self.e['yskMinutes'],self.e['yskInterval']),(0,3))
 def test_invalid_numeric_uses_original_missing_fallback(self):
  self.e['ReadUIConfig']=lambda k,d:'bad';self.e['LoadYskSettings']();self.assertEqual((self.e['yskMinutes'],self.e['yskInterval']),(-1,-1))
 def test_selector_enabled_due_done_abandoned(self):
  self.assertEqual(self.e['SelectYsk'](),0);self.e['yskEnabled']=True;self.assertEqual(self.e['SelectYsk'](),92)
  for key in ['yskDone','yskAbandoned']:
   self.e[key]=True;self.assertEqual(self.e['SelectYsk'](),0);self.e[key]=False
  self.e['yskDue']=self.e['Time']()+1;self.assertEqual(self.e['SelectYsk'](),0)
 def test_public120_not_preempt_original_duration(self):
  self.f.now=120001;self.assertFalse(self.e['BusinessExpired']());self.f.interrupt=True;self.assertTrue(self.e['BusinessExpired']())
 def test_location_both_color_templates_no_click(self):
  for n in ['092_E33','092_E34']:
   self.setUp();self.f.visible={n};self.assertEqual(self.e['EnterYskTrial'](),1);self.assertFalse(self.f.taps)
 def test_hall_entry_original_anchor_wait(self):
  self.f.visible={'092_E30','092_E28'};self.f.after=lambda *a:setattr(self.f,'visible',{'092_E33'});self.assertEqual(self.e['EnterYskTrial'](),1);self.assertEqual(self.f.taps,[(600,900,1500)])
 def test_hall_missing_icon_left_slide(self):
  self.f.visible={'092_E30'}
  def swipe(*a):self.swipes.append(a);self.f.visible={'092_E33'}
  self.e['Swipe']=swipe;self.assertEqual(self.e['EnterYskTrial'](),1);self.assertEqual(self.swipes,[(150,545,500,545,300)])
 def test_entry_original_down_and500_200_waits(self):
  self.f.visible={'092_P00'};self.f.after=lambda *a:setattr(self.f,'visible',{'092_P01'});self.assertEqual(self.e['YskEnterMode'](),1);self.assertEqual(self.swipes,[(370,1000,370,300,300)]);self.assertEqual(self.f.taps,[(600,900,500)]);self.assertGreaterEqual(self.f.now,1700)
 def test_entry_unknown_native30_not_success(self):
  self.e['yskRestartOnTimeout']=True;self.assertEqual(self.e['YskEnterMode'](),4);self.assertTrue(self.e['yskNativeTimeout']);self.assertFalse(self.e['terminalConfirmed']);self.assertGreater(self.f.now,30000)
 def test_native_timeout_three_failures_not_success(self):
  self.e['yskRestartOnTimeout']=True
  for i in range(3):self.e['YskNativeRecovery']();self.e['RecoverYskTask']();self.assertEqual(self.e['yskFailures'],i+1)
  self.assertTrue(self.e['yskAbandoned']);self.assertEqual(self.e['resumeTask'],0);self.assertFalse(self.e['yskDone'])
 def test_no_restart_hall_boundary_and_unknown(self):
  self.e['yskRestartOnTimeout']=False;self.assertEqual(self.e['YskNativeRecovery'](),1);self.assertEqual(self.e['yskFailures'],1);self.assertFalse(self.e['yskNativeTimeout'])
  self.e['ReturnToHall']=lambda:4;self.assertEqual(self.e['YskNativeRecovery'](),4);self.assertTrue(self.e['yskNoRestartPending']);self.assertFalse(self.e['terminalConfirmed'])
 def test_absent_game_requests_public_recovery(self):
  self.e['Sys'].IsRunning=lambda p:False;self.e['ReturnToHall']=lambda:self.fail('must not click absent game');self.assertEqual(self.e['YskNativeRecovery'](),4);self.assertTrue(self.e['yskNativeTimeout'])
 def test_main_unknown300_not_done_or_coin_exhaustion(self):
  self.assertEqual(self.e['RunYskTrial'](),4);self.assertGreater(self.f.now,300000);self.assertFalse(self.e['terminalConfirmed']);self.assertFalse(self.e['yskDone']);self.assertEqual(self.e['yskExitKind'],0)
 def test_attack_time_preserved_through_start_recovery_restart(self):
  self.e.update(yskAttackAt=1234,yskAttackStarted=True);self.e['StartYskTask']();self.e['RecoverYskTask']();self.e['RestartYskTask']();self.assertEqual(self.e['yskAttackAt'],1234);self.assertTrue(self.e['yskAttackStarted'])
 def test_base_at_exact_duration_still_challenges(self):
  self.e.update(yskMinutes=0,yskAttackAt=-19990,yskAttackStarted=True);self.f.visible={'092_P01'};self.interrupt_after();self.e['RunYskTrial']();self.assertEqual(self.f.taps,[(370,500,250)]);self.assertFalse(self.e['terminalConfirmed'])
 def test_base_after_duration_pending_repeat_no_new_game(self):
  self.e.update(yskMinutes=0,yskAttackAt=-20000,yskAttackStarted=True);self.f.visible={'092_P01'};self.assertEqual(self.e['RunYskTrial'](),1);self.assertEqual(self.e['yskExitKind'],2);self.assertFalse(self.f.taps);self.assertFalse(self.e['yskDone'])
 def test_role_original_offset_and250_wait(self):
  self.f.visible={'092_P02'};self.interrupt_after();self.e['RunYskTrial']();self.assertEqual(self.f.taps,[(341,1525,250)])
 def test_start_original_anchor_and_timer_reset(self):
  self.f.visible={'092_P03'}
  def after(*a):self.f.visible=set();self.e['BusinessExpired']=lambda:self.f.now>400
  self.f.after=after;self.e['RunYskTrial']();self.assertEqual(self.f.taps,[(600,900,250)]);self.assertGreater(self.e['businessStarted'],250)
 def test_speed_first_two_taps_second_one_tap(self):
  for n,taps in [('092_P04',[(660,120,200),(660,120,500)]),('092_P05',[(660,120,500)])]:
   self.setUp();self.f.visible={n};self.interrupt_after(len(taps));self.e['RunYskTrial']();self.assertEqual(self.f.taps,taps)
 def result(self,coin=None,expired=False):
  self.f.visible={'092_P06'}|({coin} if coin else set());self.e['yskMinutes']=0 if expired else 2
  self.e.update(yskAttackAt=-21000 if expired else 0,yskAttackStarted=True)
  self.f.after=lambda *a:setattr(self.f,'visible',{'092_P01'})
  if coin and not expired:self.interrupt_after()
  return self.e['RunYskTrial']()
 def test_no_coin_only_after_five_samples_then_leave(self):
  self.assertEqual(self.result(),1);self.assertEqual(self.f.taps,[(250,1100,250)]);self.assertEqual(self.e['yskExitKind'],1);self.assertEqual(self.f.lookups.count('092_P07'),5);self.assertEqual(self.f.lookups.count('092_P08'),5)
 def test_coin_templates_repeat_before_duration(self):
  for n in ['092_P07','092_P08']:
   self.setUp();self.result(n);self.assertEqual(self.f.taps,[(470,1100,250)]);self.assertFalse(self.e['terminalConfirmed']);self.assertEqual(self.f.lookups.count('092_P07'),5)
 def test_coin_positive_latched_across_five_samples(self):
  original=self.e['MatchPattern'];seen=0
  def match(n):
   nonlocal seen
   if n=='092_P07':seen+=1;return seen==1
   return original(n)
  self.e['MatchPattern']=match;self.result('092_P07');self.assertEqual(self.f.taps,[(470,1100,250)])
 def test_expired_with_coin_leaves_and_reschedules(self):
  self.assertEqual(self.result('092_P08',True),1);self.assertEqual(self.f.taps,[(250,1100,250)]);self.assertEqual(self.e['yskExitKind'],2)
 def test_shop_exit_uses_anchor_not_purchase(self):
  self.f.visible={'092_P09'};self.interrupt_after();self.e['RunYskTrial']();self.assertEqual(self.f.taps,[(600,900,250)])
 def test_foreground_interruption_no_click_or_pending(self):
  self.f.interrupt=True;self.f.visible={'092_P06','092_P01'};self.assertEqual(self.e['RunYskTrial'](),4);self.assertFalse(self.f.taps);self.assertFalse(self.e['terminalConfirmed'])
 def test_hall_gate_repeat_interval_and_attack_reset(self):
  load(['common/任务状态.mq'],self.e);self.e['SaveCurrentTask'](92);self.e['YskFinish'](True);self.assertFalse(self.e['CommitTask'](False));self.assertEqual(self.e['yskExitKind'],2);self.assertTrue(self.e['CommitTask'](True));self.assertEqual(self.e['yskDue'],self.e['yskFinishedAt']+1800);self.assertFalse(self.e['yskDone']);self.assertFalse(self.e['yskAttackStarted'])
 def test_no_coin_commit_only_after_hall(self):
  load(['common/任务状态.mq'],self.e);self.e['SaveCurrentTask'](92);self.e['YskFinish'](False);self.assertFalse(self.e['yskDone']);self.assertFalse(self.e['CommitTask'](False));self.assertTrue(self.e['CommitTask'](True));self.assertTrue(self.e['yskDone'])
 def test_missing_interval_fallback300_and_zero_interval(self):
  for value,seconds in [(-1,300),(0,0),(30,1800)]:
   self.e.update(yskInterval=value,yskExitKind=2,yskFinishedAt=123);self.e['CommitYskTask']();self.assertEqual(self.e['yskDue'],123+seconds)
 def test_catalog_has_ten_business_seven_public_and_no_ocr(self):
  records=json.loads((E/'图色转换.json').read_text('utf8'));self.assertEqual(len(records),17);catalog=json.loads((ROOT/'evidence/图色参数.json').read_text('utf8'));self.assertEqual([r for r in catalog if r['name'].startswith('092_')],records)
  flow=(ROOT/'flows/092_异时空试炼/异时空试炼.mq').read_text('utf-8-sig');self.assertNotRegex(flow,r'OcrEx|OcrText|WorldText|KillApp|RunApp|CommitTask|SchedulerStep|012_|016_');self.assertTrue(set(re.findall(r'WorldMatch\("([^"]+)"\)',flow))<={r['name'] for r in records})
 def test_original_ui_keys_defaults_no_shop(self):
  ui=(ROOT/'ui/最小配置.uip').read_text('utf-8-sig');self.assertIn('名称:"SlYsk",提示内容:"异时空试炼[",选中:false',ui);self.assertIn('名称:"SlYsk挑战时长",提示内容:"888",初始文本:"2"',ui);self.assertIn('名称:"SlYsk间隔",提示内容:"888",初始文本:"30"',ui);self.assertNotIn('名称:"SlYskSc"',ui)
  for key in ['SlYskT1','SlYskT2','SlYskT3','SlYskT4']:self.assertEqual(ui.count('名称:"'+key+'"'),1)
  code=re.sub(r'"[^"]*"','""',ui);self.assertEqual(code.count('{'),code.count('}'))
 def test_no_coin_evidence_survives_foreground_recovery(self):
  self.f.visible={'092_P06'};self.interrupt_after();self.e['RunYskTrial']();self.assertFalse(self.e['yskHasCoin']);self.e['RecoverYskTask']();self.e['StartYskTask']();self.f.interrupt=False;self.f.visible={'092_P01'};self.assertEqual(self.e['RunYskTrial'](),1);self.assertEqual(self.e['yskExitKind'],1);self.assertEqual(len(self.f.taps),1)
 def test_interrupted_coin_sampling_not_saved_as_exhausted(self):
  self.f.visible={'092_P06'};old=self.e['Delay']
  def wait(n):old(n);self.f.interrupt=True
  self.e['Delay']=wait;self.assertEqual(self.e['RunYskTrial'](),4);self.assertTrue(self.e['yskHasCoin']);self.assertFalse(self.e['terminalConfirmed'])
 def test_registration_only92_after_partner(self):
  old=json.loads((ROOT/'reports/异时空试炼接入-20261017/before/project.json').read_text('utf8'));cfg=json.loads((ROOT/'project.json').read_text('utf8'));self.assertEqual(cfg['registeredTasks'],old['registeredTasks']+[92]);self.assertEqual(cfg['modules'],old['modules']+['common/异时空试炼状态.mq','flows/092_异时空试炼/异时空试炼.mq'])
if __name__=='__main__':unittest.main()
