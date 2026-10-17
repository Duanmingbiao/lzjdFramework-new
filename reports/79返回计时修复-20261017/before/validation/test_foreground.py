from historical_source import before_diagnostics
import unittest,json,hashlib,re
from pathlib import Path
from mq_subset import load,ROOT
class Shared:
 def __init__(self):self.data={};self.locked=False
 def Lock(self):
  assert not self.locked,'nested/unreleased lock';self.locked=True
 def Release(self):
  assert self.locked,'unbalanced release';self.locked=False
 def SetShareVar(self,k,v):self.data[k]=v
 def GetShareVar(self,k):return self.data[k]
class Foreground(unittest.TestCase):
 def setUp(self):
  self.now=0;self.front='game';self.logs=[];self.events=[];self.thread=Shared();self.sample_during_delay=False
  class Sys:
   GetFront=lambda _:self.front
   AppIsFront=lambda _,p:self.front==p
   IsRunning=lambda _,p:True
  self.e={'Thread':self.thread,'Sys':Sys(),'TickCount':lambda:self.now,'TracePrint':self.logs.append,'WriteForegroundLog':self.logs.append,'Note':self.logs.append,'SetStage':lambda x:None,'Delay':self.delay,'KillApp':self.kill,'RunApp':self.launch,'GAME_PACKAGE':'game','QQ_PACKAGE':'qq','RESULT_OK':1,'RESULT_WAIT':2,'RESULT_FAIL':3,'RESULT_TIMEOUT':4,'mailEnabled':True,'rewardEnabled':True,'mailInterval':21600,'rewardInterval':21600,'registeredTask':168,'rewardRegisteredTask':169,'loginLimit':600000,'businessLimit':120000,'ReleaseCapture':lambda:None,'Tap':lambda x,y:self.events.append(('tap',x,y))}
  load(['common/前台监控.mq','common/任务状态.mq','common/任务注册.mq','common/运行计时.mq','common/游戏控制.mq','common/任务调度.mq','common/点击操作.mq'],self.e)
  self.e['NewSession']();self.e['InitForegroundMonitor']()
  self.e['EnsureGameHall']=lambda:1
 def delay(self,ms):
  self.now+=ms
  if self.sample_during_delay:self.sample(self.front,self.now)
 def kill(self,p):
  self.assertTrue(self.thread.data['fg.recovering']);self.events.append(('kill',p));self.front='launcher';self.sample(self.front,self.now)
 def launch(self,p):
  self.assertTrue(self.thread.data['fg.recovering']);self.events.append(('run',p));self.front=p;self.sample(p,self.now)
 def sample(self,p,t):self.front=p;self.now=t;self.e['SampleForeground']('game','qq');self.assertFalse(self.thread.locked)
 def request(self):self.sample('other',self.now);self.sample('other',self.now+5000)
 def test_game_and_qq_allow_without_timer_reset(self):
  self.e['loginStarted']=123
  for p,t in [('game',0),('qq',100),('qq',10000),('game',11000)]:self.sample(p,t)
  self.assertFalse(self.e['ForegroundInterrupted']());self.assertEqual(self.e['loginStarted'],123)
 def test_exact_five_seconds_latches_once(self):
  self.sample('other',0);self.sample('other',4999);self.assertFalse(self.e['ForegroundInterrupted']())
  self.sample('other',5000);self.sample('other',20000)
  self.assertTrue(self.e['ForegroundInterrupted']());self.assertEqual(sum('上报' in x for x in self.logs),1)
 def test_return_to_game_or_qq_cancels(self):
  for allowed in ['game','qq']:
   self.e['InitForegroundMonitor']();self.sample('other',0);self.sample(allowed,4999);self.sample('other',6000);self.sample('other',10999)
   self.assertFalse(self.e['ForegroundInterrupted']());self.sample('other',11000);self.assertTrue(self.e['ForegroundInterrupted']())
 def test_other_apps_switch_does_not_restart_countdown(self):
  self.sample('other1',0);self.sample('other2',4000);self.sample('other3',5000);self.assertTrue(self.e['ForegroundInterrupted']())
 def test_settings_overlay_empty_not_whitelisted(self):
  for p in ['assistant','script.settings','']:
   self.e['InitForegroundMonitor']();self.sample(p,0);self.sample(p,5000);self.assertTrue(self.e['ForegroundInterrupted']())
 def test_report_not_cancelled_after_threshold(self):
  self.request();self.sample('qq',5100);self.assertTrue(self.e['ForegroundInterrupted']())
 def test_recovery_suppresses_and_resets_countdown(self):
  self.sample('other',0);self.e['BeginForegroundRecovery']();self.sample('launcher',20000)
  self.assertFalse(self.e['ForegroundInterrupted']());self.e['EndForegroundRecovery']();self.sample('launcher',21000);self.sample('launcher',25999)
  self.assertFalse(self.e['ForegroundInterrupted']())
 def test_login_deadline_continues_on_qq(self):
  self.e.update(loginStarted=0,loginLimit=10000)
  self.sample('qq',9999);self.assertFalse(self.e['LoginExpired']());self.sample('qq',10000);self.assertTrue(self.e['LoginExpired']())
 def test_report_interrupts_timers_without_reset(self):
  self.e.update(loginStarted=100,businessStarted=200);self.request()
  self.assertTrue(self.e['LoginExpired']());self.assertTrue(self.e['BusinessExpired']());self.assertEqual((self.e['loginStarted'],self.e['businessStarted']),(100,200))
 def test_pending_report_blocks_commit(self):
  self.e['SaveCurrentTask'](169);self.e['terminalConfirmed']=True;self.request()
  self.assertFalse(self.e['CommitTask'](True));self.assertEqual(self.e['rewardCount'],0);self.assertFalse(self.thread.locked)
 def test_normal_commit_releases_lock(self):
  self.e['SaveCurrentTask'](169);self.e['terminalConfirmed']=True;self.assertTrue(self.e['CommitTask'](True));self.assertFalse(self.thread.locked)
 def test_no_click_on_other_app_or_pending_request(self):
  self.front='other';self.e['TouchPoint'](1,2,1000);self.assertEqual(self.events,[])
  self.request();self.front='game';self.e['TouchPoint'](1,2,1000);self.assertEqual(self.events,[])
 def test_click_wait_unchanged_without_request(self):
  self.e['TouchPoint'](1,2,1050);self.assertEqual(self.now,1050);self.assertEqual(self.events,[('tap',1,2)])
 def test_monitor_never_performs_game_or_task_actions(self):
  self.request();self.assertEqual(self.events,[]);self.assertEqual(self.e['currentTask'],0)
 def test_scheduler_recovers_original_169_before_mail(self):
  self.e['SaveCurrentTask'](169);self.request();seen=[]
  self.e['EnsureGameHall']=lambda:seen.append('hall') or 1
  self.e['DispatchTask']=lambda t:seen.append(t) or 4
  self.e['SchedulerStep']()
  self.assertEqual(seen,['hall',169]);self.assertEqual(self.e['resumeTask'],169);self.assertEqual(self.e['mailCount'],0);self.assertEqual(self.e['rewardCount'],0)
  self.assertEqual(self.events[:2],[('kill','game'),('run','game')])
 def test_report_during_business_skips_return_and_commit(self):
  self.e['SaveCurrentTask'](169)
  def business(t):self.e['terminalConfirmed']=True;self.request();return 1
  self.e['DispatchTask']=business;self.e['ReturnToHall']=lambda:(_ for _ in ()).throw(AssertionError('return must not run'))
  self.e['SchedulerStep']();self.assertEqual(self.e['resumeTask'],169);self.assertEqual(self.e['rewardCount'],0);self.assertEqual(self.e['rewardFailures'],1)
 def test_report_during_return_never_commits(self):
  self.e['SaveCurrentTask'](168)
  def business(t):self.e['terminalConfirmed']=True;return 1
  def hall():self.request();return 1
  self.e['DispatchTask']=business;self.e['ReturnToHall']=hall;self.e['SchedulerStep']();self.assertEqual(self.e['mailCount'],0);self.assertEqual(self.e['resumeTask'],168)
 def test_report_during_login_is_not_login_timeout(self):
  self.e['EnsureGameHall']=lambda:self.request() or 4
  self.e['SchedulerStep']();self.assertEqual(self.e['loginFailures'],0);self.assertEqual(self.e['resumeTask'],168)
 def test_idle_recovery_logs_in_without_selecting_fake_task(self):
  self.e.update(mailEnabled=False,rewardEnabled=False);self.request();seen=[];self.e['EnsureGameHall']=lambda:seen.append('hall') or 1
  self.e['SchedulerStep']();self.assertEqual(seen,['hall']);self.assertEqual(self.e['resumeTask'],0);self.assertFalse(self.e['foregroundLoginPending'])
 def test_idle_login_failure_retries_without_new_session(self):
  self.e.update(mailEnabled=False,rewardEnabled=False);self.request();self.e['EnsureGameHall']=lambda:4
  self.e['SchedulerStep']();self.assertTrue(self.e['foregroundLoginPending']);self.assertEqual(self.e['currentTask'],0)
 def test_relaunch_is_immediate_and_monitor_suppressed_during_kill(self):
  self.e['SaveCurrentTask'](169);self.request();self.sample_during_delay=True
  self.assertTrue(self.e['HandleForegroundRecovery']());self.assertEqual(self.events,[('kill','game'),('run','game')]);self.assertFalse(self.e['ForegroundInterrupted']());self.assertFalse(self.thread.data['fg.recovering']);self.assertEqual(self.e['resumeTask'],169)
 def test_only_authorized_public_modules_changed(self):
  base=json.loads((ROOT/'common/evidence/前台监控/修改前基线.json').read_text('utf-8'))
  from historical_source import AUTHORIZED
  for p,h in base.items():
   if p not in AUTHORIZED and p != 'common/日志.mq':self.assertEqual(hashlib.sha256(before_diagnostics(ROOT/p).read_bytes()).hexdigest(),h,p)
  source=(ROOT/'app/入口.mq').read_text('utf-8-sig');self.assertEqual(source.count('Thread.Start('),1)
 def test_recovery_login_timer_includes_relaunch_and_is_not_reset(self):
  self.e['RestartGame']();started=self.e['loginStarted'];self.now+=200
  self.e.update(ResetHallCheck=lambda:None,ResetHallClearing=lambda:None,ConfirmHall=lambda:True)
  load(['flows/001_游戏重连/登录游戏.mq'],self.e)
  self.assertEqual(self.e['EnsureGameHall'](),1);self.assertEqual(self.e['loginStarted'],started)
 def test_return_loop_interrupts_on_report(self):
  self.request();self.e.update(ResetHallCheck=lambda:None,ResetHallClearing=lambda:None)
  load(['common/返回大厅.mq'],self.e);self.assertEqual(self.e['ReturnToHall'](),4)
 def test_click_wait_interrupts_without_more_taps(self):
  def interrupted_delay(ms):self.now+=ms;self.thread.SetShareVar('fg.request',True)
  self.e['Delay']=interrupted_delay;self.e['TouchPoint'](1,2,1000)
  self.assertEqual(self.now,100);self.assertEqual(self.events,[('tap',1,2)])
if __name__=='__main__':unittest.main()
