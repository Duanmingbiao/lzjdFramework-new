from historical_source import before_stamina
import unittest,json
from types import SimpleNamespace
from mq_subset import ROOT,load
E=ROOT/'flows/056_Q友体力/evidence'
class QFriendFlow(unittest.TestCase):
 def setUp(self):
  self.now=0;self.taps=[];self.swipes=[];self.logs=[];self.matches=[];self.visible={'056_游戏好友页','056_Q友页面'};self.text='60/60';self.interrupted=False
  self.e=dict(RESULT_OK=1,RESULT_TIMEOUT=4,GAME_PACKAGE='game',Sys=SimpleNamespace(AppIsFront=lambda p:True),TickCount=lambda:self.now,Delay=self.delay,Note=self.logs.append,SetStage=lambda x:None,BusinessExpired=lambda:self.now>=240000 or self.interrupted,MatchPattern=self.match,TouchPoint=self.tap,ReleaseCapture=lambda:None,Swipe=lambda *a:self.swipes.append(a),Progress=lambda:None,Image=SimpleNamespace(OcrText=lambda *a:self.ocr(a)),IsNull=lambda x:x is None,qfriendOneClick=False)
  load(['flows/056_Q友体力/Q友体力.mq'],self.e)
 def delay(self,n):self.now+=n
 def tap(self,x,y,w):self.taps.append((x,y,w));self.delay(w)
 def match(self,n):self.matches.append(n);self.e['foundX']=127;self.e['foundY']=1226;return n in self.visible
 def ocr(self,a):self.assertEqual(a,(555,215,623,248,0,0));return self.text
 def test_single_ocr_terminal_after_first_pair(self):
  self.assertEqual(self.e['ExecuteQQFriendStamina'](),1);self.assertTrue(self.e['qfriendTerminal']);self.assertEqual(self.taps,[(137,180,0),(377,1116,500),(377,1116,1000)]);self.assertEqual(self.now,7500)
 def test_alternative_6060_is_terminal(self):
  self.text='6060';self.assertEqual(self.e['ExecuteQQFriendStamina'](),1)
 def test_batch_exact_two_pairs_without_ocr(self):
  self.e['qfriendOneClick']=True;self.e['Image'].OcrText=lambda *a:self.fail('batch must not OCR')
  self.assertEqual(self.e['ExecuteQQFriendStamina'](),1);self.assertEqual(self.taps[-4:],[(377,1116,500),(377,1116,1000),(587,1116,500),(587,1116,0)])
 def test_hall_entry_offset_and_wait(self):
  self.visible.add('056_大厅入口');self.assertEqual(self.e['ExecuteQQFriendStamina'](),1);self.assertEqual(self.taps[0],(665,1198,1000))
 def test_unknown_entry_not_success(self):
  self.visible.clear();self.assertEqual(self.e['ExecuteQQFriendStamina'](),4);self.assertFalse(self.e['terminalConfirmed']);self.assertGreater(self.now,20000)
 def test_missing_page_after_entry_cannot_complete(self):
  old=self.delay
  def delay(n):
   old(n)
   if n==6000:self.visible.clear()
  self.e['Delay']=delay;self.assertEqual(self.e['ExecuteQQFriendStamina'](),4);self.assertFalse(self.e['terminalConfirmed'])
 def test_unmatched_ocr_is_timeout_with_scroll(self):
  self.text='0/60';self.assertEqual(self.e['ExecuteQQFriendStamina'](),4);self.assertFalse(self.e['terminalConfirmed']);self.assertGreater(len(self.swipes),0);self.assertEqual(self.swipes[0],(377,1026,377,646,200))
 def test_empty_ocr_is_not_no_reward_success(self):
  self.text='';self.assertEqual(self.e['ExecuteQQFriendStamina'](),4);self.assertFalse(self.e['qfriendTerminal'])
 def test_claim_click_precedes_ocr(self):
  self.visible.add('056_单项领取');self.assertEqual(self.e['ExecuteQQFriendStamina'](),1);self.assertEqual(self.taps[-1],(127,1226,500))
 def test_foreground_interrupt_after_pair_blocks_success(self):
  old=self.tap
  def tap(x,y,w):
   old(x,y,w)
   if len(self.taps)==3:self.interrupted=True
  self.e['TouchPoint']=tap;self.assertEqual(self.e['ExecuteQQFriendStamina'](),4);self.assertFalse(self.e['terminalConfirmed'])
 def test_batch_missing_page_cannot_succeed(self):
  self.e['qfriendOneClick']=True;old=self.tap
  def tap(x,y,w):
   old(x,y,w)
   if len(self.taps)==3:self.visible.clear()
  self.e['TouchPoint']=tap;self.assertEqual(self.e['ExecuteQQFriendStamina'](),4);self.assertFalse(self.e['terminalConfirmed'])
 def test_public_commit_hall_gate_and_independent_counts(self):
  e=self.e;e.update(currentTask=56,resumeTask=56,qfriendCount=0,qfriendInterval=14400,terminalConfirmed=True,BeginForegroundCommit=lambda:True,EndForegroundCommit=lambda:None,friendCount=6,mailCount=7,rewardCount=8,signCount=9,monthCount=10)
  load(['common/任务状态.mq'],e);self.assertFalse(e['CommitTask'](False));self.assertEqual(e['qfriendCount'],0);self.assertTrue(e['CommitTask'](True));self.assertEqual(e['qfriendCount'],1);self.assertEqual([e[x] for x in ['friendCount','mailCount','rewardCount','signCount','monthCount']],[6,7,8,9,10])
 def test_recovery_preserves56_priority(self):
  e=self.e;e.update(currentTask=56,qfriendFailures=0,registeredTask=168,rewardRegisteredTask=169,signRegisteredTask=167,monthRegisteredTask=166,friendRegisteredTask=55,qfriendRegisteredTask=56)
  load(['common/任务状态.mq','common/任务注册.mq'],e);e['SaveRecovery']();self.assertTrue(e['qfriendRecovery']);self.assertEqual(e['SelectDueTask'](),56)
 def test_all_tasks_first_run_serial_order(self):
  e=self.e;load(['common/任务状态.mq','common/任务注册.mq'],e);e['NewSession']();e['RegisterTasks']()
  for prefix in ['mail','reward','sign','month','friend','qfriend']:e[prefix+'Enabled']=True
  for task,prefix in [(168,'mail'),(169,'reward'),(167,'sign'),(166,'month'),(55,'friend'),(56,'qfriend')]:
   self.assertEqual(e['SelectDueTask'](),task);e[prefix+'First']=False;e[prefix+'Due']=10000
 def test_original_five_businesses_unchanged(self):
  for folder in ['168_领邮件奖励','169_领任务奖励','167_日常签到','166_领月卡龙石','055_好友体力']:
   for p in (ROOT/'flows'/folder).glob('*.mq'):self.assertEqual(p.read_bytes(),(E/'before'/p.relative_to(ROOT).with_suffix('.txt')).read_bytes())
 def test_monitor_only_adds56_eligibility(self):
  old=(E/'before/common/前台监控.txt').read_text('utf-8-sig');now=before_stamina(ROOT/'common/前台监控.mq').read_text('utf-8-sig');self.assertEqual(now,old.replace('Or currentTask = 55 Then','Or currentTask = 55 Or currentTask = 56 Then'))
 def test_catalog_append_and_exact_parameters(self):
  old=json.loads((E/'before/evidence/图色参数.json').read_text('utf-8'));now=[x for x in json.loads((ROOT/'evidence/图色参数.json').read_text('utf-8')) if not x['name'].startswith(('050_','151_','152_','070_','032_','强敌_','083_','084_','085_'))];self.assertEqual(now[:-4],old);converted=json.loads((E/'图色转换.json').read_text('utf-8'));self.assertEqual([x['definition'] for x in now[-4:]],[x['definition'] for x in converted])
