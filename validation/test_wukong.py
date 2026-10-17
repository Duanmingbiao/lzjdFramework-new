import unittest,json,hashlib
from types import SimpleNamespace
from mq_subset import ROOT,load
E=ROOT/'flows/151_悟空的冒险/evidence';MODULE='flows/151_悟空的冒险/悟空的冒险.mq'
class WukongTests(unittest.TestCase):
 def setUp(self):
  self.now=0;self.logs=[];self.taps=[];self.swipes=[];self.matches=[];self.visible=set();self.text='';self.interrupt=False
  self.e=dict(RESULT_OK=1,RESULT_TIMEOUT=4,RESULT_FAIL=3,TickCount=lambda:self.now,Time=lambda:1760000000+self.now//1000,Delay=self.delay,Note=self.logs.append,SetStage=lambda s:None,MatchPattern=self.match,TouchPoint=self.tap,ReleaseCapture=lambda:None,Swipe=self.swipe,BusinessExpired=lambda:self.now>=120000 or self.interrupt,Sys=SimpleNamespace(AppIsFront=lambda p:True),GAME_PACKAGE='game',Image=SimpleNamespace(OcrText=lambda *a:self.text),IsNull=lambda x:x is None,InStr=lambda start,s,sub:s.find(sub)+1,Progress=lambda:None,wukongKeepDownload=True,wukongHidden=0,wukongSweep=0,wukongLastMatch='',wukongLastOcr='',wukongTerminalReason='',wukongPhase='test',currentTask=151,terminalConfirmed=False)
  load([MODULE],self.e)
 def delay(self,n):self.now+=n
 def tap(self,x,y,w):self.taps.append((x,y,w));self.delay(w)
 def swipe(self,*a):self.swipes.append(a);self.now+=a[-1]
 def match(self,n):self.matches.append(n);self.e['foundX']=100;self.e['foundY']=1000;return n in self.visible
 def state(self):load(['common/悟空冒险状态.mq'],self.e);self.e['NewWukongSession']()
 def test_entry_click_offset_wait(self):
  self.visible={'151_大厅条件一','151_大厅入口一'};old=self.tap
  def tap(x,y,w):old(x,y,w);self.visible={'151_入口已到一'}
  self.e['TouchPoint']=tap;self.assertEqual(self.e['EnterWukongAdventure'](),1);self.assertEqual(self.taps,[(260,940,1500)])
 def test_entry_60sec_timeout_does_not_complete(self):
  self.e['ReturnToHall']=lambda:1;self.assertEqual(self.e['EnterWukongAdventure'](),4);self.assertFalse(self.e['terminalConfirmed']);self.assertGreater(self.now,62000)
 def test_source_initial_priority_then_qualification(self):
  self.visible={'151_冒险主界面','151_可扫荡'};self.assertEqual(self.e['DetectWukongMode'](),1);self.assertEqual(self.now,2500)
 def test_latest_unsweepable_ocr_is_explicit_exit(self):
  self.visible={'151_冒险主界面'};self.text='通关';self.assertEqual(self.e['DetectWukongMode'](),3);self.assertEqual(self.taps,[]);self.assertEqual(self.now,4000)
 def test_old_level_retries_exact_tap_and_swipe_sequence(self):
  self.visible={'151_冒险主界面'};self.text='通关';self.e['wukongSweep']=1;self.assertEqual(self.e['DetectWukongMode'](),3);self.assertEqual(len(self.taps),4);self.assertEqual(self.swipes,[(70,150,342,152,2000)]*2)
 def test_empty_ocr_unknown_is_not_terminal(self):
  self.visible={'151_冒险主界面'};self.assertEqual(self.e['DetectWukongMode'](),0);self.assertFalse(self.e['terminalConfirmed'])
 def test_explicit_gray_qualification_after_two_seconds(self):
  self.visible={'151_冒险主界面','151_扫荡灰色'};self.assertEqual(self.e['DetectWukongMode'](),3);self.assertGreater(self.now,4500)
 def test_sweep_action_order_exact_waits(self):
  self.visible={'151_可扫荡','151_下一步','151_扫荡确认','151_隐藏界面'};self.assertEqual(self.e['SweepWukongAdventure'](),2);self.assertEqual(self.taps,[(567,800,500),(100,1000,500),(100,1000,1500)])
 def test_sweep_two_gray_hits_terminal(self):
  self.visible={'151_扫荡灰色'};self.assertEqual(self.e['SweepWukongAdventure'](),3);self.assertEqual(sum('扫荡灰色终态累计' in x for x in self.logs),2)
 def test_sweep_timeout_without_terminal_not_success(self):
  self.assertEqual(self.e['SweepWukongAdventure'](),0);self.assertGreater(self.now,30000);self.assertFalse(self.e['terminalConfirmed'])
 def test_hidden_user_approved_two_gray_terminal(self):
  self.visible={'151_扫荡灰色'};self.assertEqual(self.e['CollectWukongAdventure'](),1);self.assertEqual(sum('隐藏灰色终态累计' in x for x in self.logs),2);self.assertGreater(self.now,5000)
 def test_hidden_one_gray_then_unknown_cannot_succeed(self):
  old=self.match;hits=[0]
  def match(n):
   if n=='151_扫荡灰色' and self.now>4000:
    hits[0]+=1
    return hits[0]==1
   return old(n)
  self.e['MatchPattern']=match;self.assertEqual(self.e['CollectWukongAdventure'](),4)
 def test_hidden_item_priority_and_wait1700(self):
  self.visible={f'151_极品{i}' for i in range(1,6)}|{'151_扫荡灰色'};self.assertEqual(self.e['CollectWukongAdventure'](),1);self.assertEqual([x for x in self.matches[:5]],[f'151_极品{i}' for i in range(1,6)]);self.assertTrue(all(x[2]==1700 for x in self.taps));self.assertFalse(any('上品' in x for x in self.matches))
 def test_upper_grade_adds_four_after_five_premium(self):
  self.visible={'151_扫荡灰色'};self.e['wukongHidden']=1;self.assertEqual(self.e['CollectWukongAdventure'](),1);self.assertEqual(self.matches[:9],[f'151_极品{i}' for i in range(1,6)]+[f'151_上品{i}' for i in range(1,5)])
 def test_hidden_claim_uses_same_anchor_only_once_three_taps(self):
  self.visible={'151_隐藏领取','151_扫荡灰色'};self.assertEqual(self.e['CollectWukongAdventure'](),1);self.assertEqual(self.taps,[(100,1000,200)]*3)
 def test_return_popup_template_one_precedes_two(self):
  self.visible={'151_返回弹窗一','151_返回弹窗二','151_扫荡灰色'};self.assertEqual(self.e['CollectWukongAdventure'](),1);self.assertNotIn('151_返回弹窗二',self.matches)
 def test_full_terminal_does_not_commit_itself(self):
  self.visible={'151_扫荡灰色'};self.e['EnterWukongAdventure']=lambda:1;self.e['DetectWukongMode']=lambda:2;self.assertEqual(self.e['ExecuteWukongAdventure'](),1);self.assertTrue(self.e['terminalConfirmed']);self.assertFalse(any('是否提交完成=是' in x for x in self.logs))
 def test_foreground_interruption_prevents_terminal(self):
  self.interrupt=True;self.assertEqual(self.e['ExecuteWukongAdventure'](),4);self.assertFalse(self.e['terminalConfirmed'])
 def test_public_hall_gate_and_independent_count(self):
  self.state();load(['common/任务状态.mq'],self.e);self.e.update(currentTask=151,resumeTask=151,terminalConfirmed=True,wukongInterval=3600,BeginForegroundCommit=lambda:True,EndForegroundCommit=lambda:None,mailCount=9,qfriendCount=8)
  self.assertFalse(self.e['CommitTask'](False));self.assertEqual(self.e['wukongCount'],0);self.assertTrue(self.e['CommitTask'](True));self.assertEqual(self.e['wukongCount'],1);self.assertEqual(self.e['mailCount'],9);self.assertEqual(self.e['qfriendCount'],8)
 def test_recovery151_before_other_due_tasks(self):
  self.state();load(['common/任务状态.mq','common/任务注册.mq'],self.e);self.e['RegisterTasks']();self.e['SaveRecovery']();self.assertEqual(self.e['SelectDueTask'](),151);self.assertEqual(self.e['wukongRecoveries'],1)
 def test_existing_businesses_bytes_unchanged(self):
  for rel,h in json.loads((E/'修改前基线.json').read_text('utf-8')).items():
   if rel.startswith('flows/'):self.assertEqual(hashlib.sha256((ROOT/rel).read_bytes()).hexdigest(),h,rel)
 def test_append_only_exact_profiles(self):
  old=json.loads((E/'before/evidence/图色参数.txt').read_text('utf-8'));now=[x for x in json.loads((ROOT/'evidence/图色参数.json').read_text('utf-8')) if not x['name'].startswith(('152_','070_','032_','强敌_','083_','084_','085_'))];conv=json.loads((E/'图色转换.json').read_text('utf-8'));self.assertEqual(now[:len(old)],old);self.assertEqual([x['definition'] for x in now[len(old):]],[x['definition'] for x in conv])
 def test_ui_three_levels_no152_registration(self):
  text=(ROOT/'ui/最小配置.uip').read_text('utf-8-sig');self.assertIn('日常任务:{',text);self.assertIn('名称:"悟空冒险启用"',text);self.assertIn('名称:"悟空隐藏关卡"',text);self.assertIn('名称:"悟空扫荡关卡"',text);self.assertNotIn(152,json.loads((ROOT/'flows/152_合作大冒险/evidence/before/project.txt').read_text('utf-8'))['registeredTasks'])
