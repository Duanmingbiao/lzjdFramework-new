import unittest
from mq_subset import load
class ControlFlow(unittest.TestCase):
 def setUp(self):
  self.now=1000;self.events=[]
  self.e={'TickCount':lambda:self.now,'Delay':self.delay,'SetStage':lambda x:None,'Note':lambda x:None,'Progress':lambda:None}
  load(['common/任务状态.mq','common/任务注册.mq','common/运行计时.mq','flows/168_领邮件奖励/领邮件奖励.mq'],self.e)
  self.e.update(RESULT_OK=1,RESULT_WAIT=2,RESULT_FAIL=3,RESULT_TIMEOUT=4,mailEnabled=True,mailInterval=21600,loginLimit=600000,businessLimit=120000,messageMode=0,registeredTask=168,rewardRegisteredTask=169,rewardEnabled=False,rewardInterval=21600)
  self.e['NewSession']();self.e['businessStarted']=self.now
  self.e['TouchPoint']=self.touch;self.e['MatchPattern']=self.match
  self.patterns=set();self.e['foundX']=100;self.e['foundY']=1100
 def delay(self,ms):self.now+=ms
 def touch(self,x,y,ms):self.events.append((x,y,ms));self.delay(ms)
 def match(self,name):self.now+=1;self.e['foundX']=100;self.e['foundY']=1100;return name in self.patterns
 def test_fresh_session_runs_selected(self):self.assertEqual(self.e['SelectDueTask'](),168)
 def test_disabled_task_skipped(self):self.e['mailEnabled']=False;self.assertEqual(self.e['SelectDueTask'](),0)
 def test_recovery_has_priority(self):self.e.update(mailEnabled=False,resumeTask=168);self.assertEqual(self.e['SelectDueTask'](),168)
 def test_unconfirmed_terminal_cannot_commit(self):self.e['SaveCurrentTask'](168);self.assertFalse(self.e['CommitTask'](True));self.assertEqual(self.e['mailCount'],0)
 def test_return_failure_cannot_commit(self):self.e['SaveCurrentTask'](168);self.e['terminalConfirmed']=True;self.assertFalse(self.e['CommitTask'](False));self.assertEqual(self.e['mailDue'],0)
 def test_commit_schedules_interval_and_cannot_repeat(self):
  # Diagnostic concatenation is mocked because Python numeric coercion differs.
  self.e['Note']=lambda x:None
  self.e['SaveCurrentTask'](168);self.e['terminalConfirmed']=True
  self.e['mailCount']=0;self.e['mailInterval']=10
  self.assertTrue(self.e['CommitTask'](True));self.assertEqual(self.e['SelectDueTask'](),0)
  self.assertFalse(self.e['CommitTask'](True));self.now+=10000;self.assertEqual(self.e['SelectDueTask'](),168)
 def test_new_script_resets_runtime_not_configuration(self):
  self.e.update(mailDue=99999999,mailCount=22,mailFirst=False,resumeTask=168,mailInterval=17)
  self.e['NewSession']();self.assertEqual(self.e['SelectDueTask'](),168);self.assertEqual(self.e['mailCount'],0);self.assertEqual(self.e['mailInterval'],17)
 def test_entry_empty_layout_one(self):self.patterns={'邮件空一'};self.assertEqual(self.e['ExecuteMail'](),1);self.assertTrue(self.e['terminalConfirmed']);self.assertEqual(self.events,[])
 def test_entry_empty_layout_two(self):self.patterns={'邮件空二'};self.assertEqual(self.e['ExecuteMail'](),1)
 def test_entry_empty_skips_auto_messages(self):
  self.e['messageMode']=1;self.patterns={'邮件空一'};self.e['ReadMessages']=lambda:(_ for _ in ()).throw(AssertionError('early exit must skip messages'));self.assertEqual(self.e['ExecuteMail'](),1)
 def test_unknown_never_succeeds(self):self.assertEqual(self.e['ExecuteMail'](),4);self.assertFalse(self.e['terminalConfirmed'])
 def test_claim_deadline_does_not_refresh_on_click(self):
  self.patterns={'邮件可领一'};self.assertEqual(self.e['ExecuteMail'](),4);self.assertLess(self.now,8000);self.assertFalse(self.e['terminalConfirmed'])
 def test_messages_unknown_times_out(self):self.assertEqual(self.e['ReadMessages'](),4);self.assertFalse(self.e['terminalConfirmed'])
 def test_message_terminal_waits_threshold(self):
  self.patterns={'邮件消息终态'};start=self.now;self.assertEqual(self.e['ReadMessages'](),1);self.assertGreater(self.now-start,2000);self.assertLessEqual(self.now-start,5000)
 def test_claim_popups_independent_order(self):
  count={'empty':0}
  def matcher(name):
   self.match(name)
   if name=='邮件空一':count['empty']+=1;return count['empty']>1
   return name in {'邮件可领一','获得奖励','邮件关闭弹窗'}
  self.e['MatchPattern']=matcher
  self.assertEqual(self.e['ExecuteMail'](),1);self.assertEqual(self.events,[(419,1010,200),(100,1100,200),(100,1100,200)])
 def test_scheduler_return_failure_preserves_original_task(self):
  load(['common/任务调度.mq'], self.e)
  self.e['EnsureGameHall']=lambda:1
  def dispatch(task):self.e['terminalConfirmed']=True;return 1
  self.e['DispatchTask']=dispatch;self.e['ReturnToHall']=lambda:4
  self.e['mailFailures']=0;self.restarts=0
  def restart():self.restarts+=1
  self.e['RestartGame']=restart;self.e['SchedulerStep']()
  self.assertEqual(self.e['mailCount'],0);self.assertEqual(self.e['resumeTask'],168);self.assertEqual(self.restarts,1)
 def test_scheduler_success_commits_after_return(self):
  load(['common/任务调度.mq'], self.e)
  self.e['EnsureGameHall']=lambda:1
  def dispatch(task):self.e['terminalConfirmed']=True;return 1
  def returned():self.assertEqual(self.e['mailCount'],0);return 1
  self.e['DispatchTask']=dispatch;self.e['ReturnToHall']=returned
  self.e['RestartGame']=lambda:(_ for _ in ()).throw(AssertionError('no restart'))
  self.e['mailCount']=0;self.e['mailInterval']=10
  self.e['SchedulerStep']();self.assertEqual(self.e['mailCount'],1);self.assertEqual(self.e['resumeTask'],0)
 def test_scheduler_timeout_never_calls_return_or_commit(self):
  load(['common/任务调度.mq'], self.e)
  self.e['EnsureGameHall']=lambda:1;self.e['DispatchTask']=lambda task:4
  self.e['ReturnToHall']=lambda:(_ for _ in ()).throw(AssertionError('not successful'))
  self.e['RestartGame']=lambda:None;self.e['mailFailures']=0
  self.e['SchedulerStep']();self.assertEqual(self.e['resumeTask'],168);self.assertEqual(self.e['mailCount'],0)
 def test_login_deadline_not_reset_on_qq_foreground(self):
  load(['flows/001_游戏重连/登录游戏.mq'], self.e)
  class SysMock:
   def AppIsFront(self,p):return False
  self.e.update(Sys=SysMock(),GAME_PACKAGE='game',QQ_PACKAGE='qq',StartGame=lambda:None,ResetHallCheck=lambda:None,ResetHallClearing=lambda:None,ConfirmHall=lambda:False,HandleQQ=lambda:False)
  started=self.now;self.e['loginLimit']=80
  self.assertEqual(self.e['EnsureGameHall'](),4);self.assertEqual(self.e['loginStarted'],started);self.assertEqual(self.now-started,80)
 def test_restart_launches_game_even_if_qq_remains_front(self):
  load(['common/游戏控制.mq'],self.e)
  class SysMock:
   def AppIsFront(self,p):return p=='qq'
   def IsRunning(self,p):return False
  launched=[];self.e.update(Sys=SysMock(),GAME_PACKAGE='game',QQ_PACKAGE='qq',RunApp=lambda p:launched.append(p))
  self.e['StartGame']();self.assertEqual(launched,['game'])
 def test_live_qq_authorization_does_not_relaunch_game(self):
  load(['common/游戏控制.mq'],self.e)
  class SysMock:
   def AppIsFront(self,p):return p=='qq'
   def IsRunning(self,p):return True
  launched=[];self.e.update(Sys=SysMock(),GAME_PACKAGE='game',QQ_PACKAGE='qq',RunApp=lambda p:launched.append(p))
  self.e['StartGame']();self.assertEqual(launched,[])
 def test_notice_background_cannot_confirm_hall(self):
  load(['common/大厅清障.mq','common/页面识别.mq'],self.e)
  class SysMock:
   def AppIsFront(self,p):return True
  self.e.update(Sys=SysMock(),GAME_PACKAGE='game')
  self.patterns={'大厅主体','我知道了'};self.assertFalse(self.e['HallCandidate']())
 def test_qq_one_click_branch_uses_local_handled_flag(self):
  load(['flows/001_游戏重连/QQ登录.mq'],self.e)
  class SysMock:
   def GetFront(self):return 'qq'
  self.e.update(Sys=SysMock(),GAME_PACKAGE='game',QQ_PACKAGE='qq',loginStarted=self.now,TouchPattern=lambda name,delay:False)
  self.patterns={'QQ一键登录'}
  self.assertTrue(self.e['HandleQQ']())
  self.assertEqual(self.events, [(-51,1186,1000),(163,1100,1000)])
 def test_unknown_qq_page_does_not_click(self):
  load(['flows/001_游戏重连/QQ登录.mq'],self.e)
  class SysMock:
   def GetFront(self):return 'qq'
  self.e.update(Sys=SysMock(),GAME_PACKAGE='game',QQ_PACKAGE='qq',loginStarted=self.now,TouchPattern=lambda name,delay:False)
  self.assertFalse(self.e['HandleQQ']());self.assertEqual(self.events,[])
if __name__=='__main__':unittest.main()
