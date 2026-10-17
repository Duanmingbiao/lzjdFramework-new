import unittest,re
from mq_subset import load,ROOT
import test_gold,test_foreground
STATE=['common/金币试炼状态.mq','common/经验试炼状态.mq','common/龙魂试炼状态.mq','common/基因试炼状态.mq','common/伙伴试炼状态.mq','common/异时空试炼状态.mq']
TASKS=[(12,'gold','Gold'),(13,'experience','Experience'),(14,'soul','Soul'),(15,'gene','Gene'),(16,'partner','Partner'),(92,'ysk','Ysk')]
class TrialPublicFix(unittest.TestCase):
 def setUp(self):
  self.g=test_gold.GoldTests();self.g.setUp();self.e=self.g.e;self.f=self.g.f
  load(STATE+['common/任务状态.mq'],self.e)
  self.e['NewTrialPublicSession']()
  for _,_,cap in TASKS:self.e['New'+cap+'Session']()
  self.smart=[];self.smartText='';self.e['SmartOcr']=lambda *a:self.smart.append(a) or self.smartText
 def test_smart_only_fills_empty_primary_original_roi_color(self):
  self.f.text='';self.smartText='03';self.assertEqual(self.e['GoldReadCount'](149,306,219,346),'03');self.assertEqual(self.smart,[(149,306,219,346,'0000E9-101010')]);self.assertTrue(self.e['GoldCountExhausted']('03'))
 def test_null_primary_can_use_old_numeric_ocr(self):
  self.f.text=None;self.smartText='013';self.assertEqual(self.e['GoldReadCount'](149,306,219,346),'013')
 def test_nonempty_primary_unchanged_no_smart_override(self):
  for s in ['1/3','0/3','00:10','错误03']:
   self.f.text=s;self.smart.clear();self.assertEqual(self.e['GoldReadCount'](149,306,219,346),s);self.assertFalse(self.smart)
 def test_empty_or_single_digit_never_exhausted(self):
  for s in ['',None,'0','3','06','03x','错误03']:
   self.f.text='';self.smartText=s;value=self.e['GoldFilterText'](self.e['GoldReadCount'](149,306,219,346));self.assertFalse(self.e['GoldCountExhausted'](value))
 def test_red03_ends_only_pending_hall_no_click(self):
  self.f.visible={'012_P00'};self.f.text='';self.smartText='03';self.assertEqual(self.e['RunGoldTrial'](),1);self.assertEqual(self.e['goldExitKind'],1);self.assertFalse(self.e['goldDone']);self.assertFalse(self.f.taps);self.assertEqual(self.smart,[(200,1005,270,1045,'0000E9-101010')])
 def test_both_ocr_empty_remains_unknown_then_common_failure_not_done(self):
  self.f.visible={'012_P00'};self.f.text='';self.smartText='';self.assertEqual(self.e['RunGoldTrial'](),4);self.assertFalse(self.e['terminalConfirmed']);self.assertFalse(self.e['goldDone']);self.assertEqual(self.e['trialPublicTimedOutTask'],12)
 def test_numeric_fallback_never_used_for_title(self):
  flow=(ROOT/'flows/012_金币试炼/金币试炼.mq').read_text('utf-8-sig');self.assertEqual(flow.count('raw = SmartOcr('),1);self.assertIn('text = WorldText(65, 7, 247, 59)',flow);self.assertIn('GoldReadCount(ax - 400, ay + 105, ax - 330, ay + 145)',flow)
 def test_no_numeric_call_after_foreground_report(self):
  self.f.text='';self.f.interrupt=True;self.assertEqual(self.e['GoldReadCount'](149,306,219,346),'');self.assertFalse(self.smart)
 def test_each_trial_strict_deadline_and_reset(self):
  for task,_,_ in TASKS:
   self.e.update(currentTask=task,businessStarted=0,trialPublicTimedOutTask=0);self.f.now=120000;self.assertFalse(self.e['BusinessExpired']());self.f.now=120001;self.assertTrue(self.e['BusinessExpired']());self.assertEqual(self.e['trialPublicTimedOutTask'],task);self.e['businessStarted']=self.f.now;self.assertFalse(self.e['BusinessExpired']())
 def test_three_common_failures_release_each_trial_not_success_or65(self):
  for task,prefix,cap in TASKS:
   self.setUp();self.e.update(currentTask=task,resumeTask=task);due=self.e[prefix+'Due'];count=self.e.get(prefix+'Count')
   for i in range(3):
    self.e['trialPublicTimedOutTask']=task;self.e['SaveRecovery']();self.assertEqual(self.e[prefix+'Failures'],i+1);self.assertEqual(self.e[prefix+'Abandoned'],i==2);self.assertEqual(self.e['resumeTask'],0 if i==2 else task);self.assertFalse(self.e[prefix+'Done']);self.assertEqual(self.e[prefix+'Due'],due);self.assertEqual(self.e.get(prefix+'Count'),count);self.assertFalse(self.e['terminalConfirmed'])
 def test_public_failure_handled_once_not_double_counted(self):
  self.e.update(currentTask=12,trialPublicTimedOutTask=12);self.e['SaveRecovery']();self.e['SaveRecovery']();self.assertEqual(self.e['goldFailures'],1)
 def test_front_wins_over_expired_timer_no_public_failure(self):
  for task,prefix,_ in TASKS:
   self.setUp();self.e.update(currentTask=task,resumeTask=task,trialPublicTimedOutTask=task);self.f.interrupt=True;self.f.now=999999;self.e['SaveRecovery']();self.assertEqual(self.e[prefix+'Failures'],0);self.assertEqual(self.e['resumeTask'],task);self.assertEqual(self.e['trialPublicRecoveryTask'],0)
 def test_native35_failure_stays_separate_count_and65(self):
  self.e['ConfirmGoldExit']('native',3);at=self.e['goldFinishedAt'];self.e['SaveRecovery']();self.assertEqual(self.e['goldCount'],1);self.assertEqual(self.e['goldFailures'],0);self.assertEqual(self.e['goldDue'],at+65)
 def test_nontrial_timeout_keeps_existing_boundary(self):
  self.e.update(currentTask=168,businessStarted=0,trialPublicTimedOutTask=0);self.f.now=120000;self.assertTrue(self.e['BusinessExpired']());self.assertEqual(self.e['trialPublicTimedOutTask'],0)
 def scheduler(self,task=12,restart=False,running=True,hall=1):
  f=test_foreground.Foreground();f.setUp();e=f.e;e.update(Time=lambda:1760000000+f.now//1000,WorldLog=f.logs.append,WorldStage=lambda s:None,ReadUIConfig=lambda k,d:d,WorldWait=f.delay)
  load(STATE,e)
  for _,_,cap in TASKS:e['New'+cap+'Session']()
  e.update(trialRestartOnTimeout=restart,mailEnabled=False,rewardEnabled=False);e['SelectDueTask']=lambda:task;e['Sys'].IsRunning=lambda p:running;self.halls=[];e['ReturnToHall']=lambda:self.halls.append('hall') or hall
  def dispatch(t):f.now=e['businessStarted']+120001;self.assertTrue(e['BusinessExpired']());return 4
  e['DispatchTask']=dispatch;e['SchedulerStep']();return f,e
 def test_no_restart_option_returns_hall_without_kill_all_six(self):
  for task,_,_ in TASKS:
   f,e=self.scheduler(task);self.assertEqual(self.halls,['hall']);self.assertFalse(any(x[0]=='kill' for x in f.events));self.assertEqual(e['trialPublicRecoveryTask'],0);self.assertEqual(e['resumeTask'],task);self.assertFalse(e['terminalConfirmed'])
 def test_no_restart_unknown_hall_still_does_not_kill(self):
  f,e=self.scheduler(hall=4);self.assertFalse(any(x[0]=='kill' for x in f.events));self.assertEqual(e['resumeTask'],12);self.assertFalse(e['goldDone'])
 def test_restart_enabled_and_absent_game_request_existing_restart(self):
  for restart,running in [(True,True),(False,False)]:
   f,e=self.scheduler(restart=restart,running=running);self.assertTrue(any(x[0]=='kill' for x in f.events));self.assertEqual(e['goldFailures'],1)
 def test_gold_three_failures_then_real_selector_can_choose_experience(self):
  f,e=self.scheduler();e.update(goldEnabled=True,experienceEnabled=True)
  for i in range(2):e.update(currentTask=12,trialPublicTimedOutTask=12);e['SaveRecovery']()
  self.assertTrue(e['goldAbandoned']);self.assertEqual(e['resumeTask'],0);load(['common/任务注册.mq'],e);e['RegisterTasks']();self.assertEqual(e['SelectDueTask'](),13);self.assertFalse(e['goldDone'])
 def test_shared_gene_and_ysk_native_public_failure_counter(self):
  for task,prefix in [(15,'gene'),(92,'ysk')]:
   self.setUp();self.e.update(currentTask=task,resumeTask=task,trialPublicTimedOutTask=task);self.e[prefix+'Failures']=2;self.e['SaveRecovery']();self.assertEqual(self.e[prefix+'Failures'],3);self.assertTrue(self.e[prefix+'Abandoned']);self.assertEqual(self.e['resumeTask'],0)
 def test_start_task_does_not_reset_failure_history(self):
  self.e.update(goldFailures=2,trialPublicTimedOutTask=12,trialPublicRecoveryTask=12);self.e['SaveCurrentTask'](12);self.assertEqual(self.e['goldFailures'],2);self.assertEqual(self.e['trialPublicTimedOutTask'],0);self.assertEqual(self.e['trialPublicRecoveryTask'],0)
if __name__=='__main__':unittest.main()
