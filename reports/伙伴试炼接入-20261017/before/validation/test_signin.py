from historical_source import before_stamina
from historical_source import before_monthly
import unittest,json,hashlib,re
from pathlib import Path
from mq_subset import load,ROOT
import test_foreground
MODULE='flows/167_日常签到/日常签到.mq'
E=ROOT/'flows/167_日常签到/evidence'
class SignFlow(unittest.TestCase):
 def setUp(self):
  self.now=1000;self.events=[];self.lookups=[];self.visible=set();self.logs=[];self.after=lambda x,y,w:None
  self.e={};load(['common/任务状态.mq','common/运行计时.mq',MODULE],self.e)
  self.e.update(TickCount=lambda:self.now,Delay=self.delay,TouchPoint=self.touch,MatchPattern=self.match,Note=self.logs.append,SetStage=lambda x:None,RESULT_OK=1,RESULT_TIMEOUT=4,businessLimit=12000)
  self.e['NewSession']();self.e['businessStarted']=self.now
 def delay(self,n):self.now+=n
 def touch(self,x,y,w):self.events.append((x,y,w));self.delay(w);self.after(x,y,w)
 def match(self,n):self.lookups.append((self.now,n));self.e.update(foundX=400,foundY=600);return n in self.visible
 def test_entry_order_and_exact_positions(self):
  self.visible={'167_入口','167_中心页面'};self.assertEqual(self.e['EnterDailySign'](),1)
  self.assertEqual(self.events,[(400,600,100),(150,50,200)])
 def test_independent_claims_then_popups_order(self):
  self.visible={'167_领取一','167_领取二','167_领取三','167_领取四','167_奖励弹窗','167_充值提示'}
  self.e['BusinessExpired']=lambda:len(self.events)>=6
  self.assertEqual(self.e['ClaimDailySign'](),4)
  self.assertEqual(self.events,[(405,600,500),(450,580,500),(450,580,500),(450,580,500),(5,5,0),(400,600,0)])
 def test_five_second_gate_not_refreshed_by_claims(self):
  self.visible={'167_领取一','167_累计灰色'};self.assertEqual(self.e['ClaimDailySign'](),1)
  cumulative=[t for t,n in self.lookups if n.startswith('167_累计')]
  self.assertTrue(cumulative);self.assertGreater(min(cumulative)-1000,5000);self.assertLess(self.now-1000,6000);self.assertFalse(self.e['terminalConfirmed'])
 def test_no_reward_requires_gray_then_center(self):
  self.visible={'167_中心页面','167_累计灰色'};self.assertEqual(self.e['ExecuteDailySign'](),1);self.assertTrue(self.e['terminalConfirmed']);self.assertEqual(self.events,[(150,50,200)])
 def test_gray_without_final_page_does_not_succeed(self):
  self.visible={'167_累计灰色'};self.assertEqual(self.e['ClaimDailySign'](),1);self.assertEqual(self.e['FinishDailySign'](),4);self.assertFalse(self.e['terminalConfirmed'])
 def test_finish_popup_first_and_uses_anchor_not_five_five(self):
  self.visible={'167_奖励弹窗','167_中心页面'};self.assertEqual(self.e['FinishDailySign'](),1);self.assertEqual(self.events,[(400,600,0)]);self.assertEqual([n for t,n in self.lookups],['167_奖励弹窗'])
 def test_unknown_each_stage_times_out(self):
  for fn in ['EnterDailySign','ClaimDailySign','FinishDailySign','ExecuteDailySign']:
   self.now=1000;self.e['terminalConfirmed']=False;self.assertEqual(self.e[fn](),4);self.assertFalse(self.e['terminalConfirmed'])
 def test_expired_terminal_never_succeeds(self):
  self.now=13000;self.visible={'167_中心页面','167_累计灰色','167_奖励弹窗'};self.assertEqual(self.e['ExecuteDailySign'](),4);self.assertFalse(self.e['terminalConfirmed']);self.assertEqual(self.events,[])
 def test_interruption_after_final_click_is_not_success(self):
  self.visible={'167_奖励弹窗'};self.after=lambda x,y,w:self.e.update(ForegroundInterrupted=lambda:True)
  self.assertEqual(self.e['FinishDailySign'](),4);self.assertFalse(self.e['terminalConfirmed'])
 def test_cumulative_claim_precedes_gray(self):
  self.visible={'167_累计可领','167_累计灰色'};self.assertEqual(self.e['ClaimDailySign'](),1);self.assertEqual(self.events,[(400,600,0)]);self.assertEqual([n for t,n in self.lookups][-2:],['167_累计可领','167_累计灰色'])
class SignArchitecture(unittest.TestCase):
 def setUp(self):
  self.f=test_foreground.Foreground();self.f.setUp();self.e=self.f.e;self.e.update(signEnabled=True,signInterval=3600);self.e['RegisterTasks']()
 def test_serial_first_round_and_independent_commit(self):
  for task in [168,169,167]:
   self.assertEqual(self.e['SelectDueTask'](),task);self.e['SaveCurrentTask'](task);self.e['terminalConfirmed']=True;self.assertTrue(self.e['CommitTask'](True))
  self.assertEqual([self.e[x] for x in ['mailCount','rewardCount','signCount']],[1,1,1]);self.assertEqual(self.e['signDue'],3600000);self.assertEqual(self.e['SelectDueTask'](),0)
 def test_sign_due_compares_against_selected_reward(self):
  self.e.update(mailFirst=False,rewardFirst=False,signFirst=False,mailDue=900,rewardDue=500,signDue=700);self.f.now=1000;self.assertEqual(self.e['SelectDueTask'](),169)
 def test_commit_requires_hall_and_terminal(self):
  self.e['SaveCurrentTask'](167);self.assertFalse(self.e['CommitTask'](True));self.e['terminalConfirmed']=True;self.assertFalse(self.e['CommitTask'](False));self.assertEqual(self.e['signCount'],0)
 def test_foreground_recovery_keeps_sign_task(self):
  self.e['SaveCurrentTask'](167);self.f.request();self.assertTrue(self.e['HandleForegroundRecovery']());self.assertEqual(self.e['resumeTask'],167);self.assertEqual(self.e['SelectDueTask'](),167);self.assertEqual(self.e['signFailures'],1)
 def test_timeout_recovery_reexecutes_original(self):
  self.e.update(mailEnabled=False,rewardEnabled=False,DispatchTask=lambda t:4);self.e['SchedulerStep']();self.assertEqual(self.e['resumeTask'],167);self.assertEqual(self.e['signCount'],0)
  seen=[]
  def dispatch(t):seen.append(t);self.e['terminalConfirmed']=True;return 1
  self.e.update(DispatchTask=dispatch,ReturnToHall=lambda:1);self.e['SchedulerStep']();self.assertEqual(seen,[167]);self.assertEqual(self.e['signCount'],1)
 def test_new_session_resets_sign_state_not_configuration(self):
  self.e.update(signCount=4,signDue=99999,signFirst=False);self.e['NewSession']();self.assertEqual(self.e['signCount'],0);self.assertTrue(self.e['signFirst']);self.assertTrue(self.e['signEnabled']);self.assertEqual(self.e['signInterval'],3600)
 def test_disabled_sign_is_not_selected(self):
  self.e.update(signEnabled=False,mailEnabled=False,rewardEnabled=False);self.assertEqual(self.e['SelectDueTask'](),0)
 def test_dispatch_calls_new_business(self):
  load(['common/任务分派.mq'],self.e);seen=[];self.e['ExecuteDailySign']=lambda:seen.append(167) or 1;self.assertEqual(self.e['DispatchTask'](167),1);self.assertEqual(seen,[167])
class SignEvidence(unittest.TestCase):
 def test_existing_business_and_nonintegration_files_unchanged(self):
  allowed={'app/入口.mq','common/配置读取.mq','common/任务状态.mq','common/任务注册.mq','common/任务分派.mq','common/前台监控.mq','common/图色参数.mq','ui/最小配置.uip'}
  for rel,h in json.loads((E/'修改前基线.json').read_text('utf-8')).items():
   self.assertEqual(hashlib.sha256((E/'before'/Path(rel).with_suffix('.txt')).read_bytes()).hexdigest(),h)
   if rel not in allowed:self.assertEqual(hashlib.sha256(before_stamina(ROOT/rel).read_bytes()).hexdigest(),h,rel)
 def test_exact_raw_conversion_and_append_only_catalog(self):
  raw=json.loads((E/'原始图色.json').read_text('utf-8'));converted=json.loads((E/'图色转换.json').read_text('utf-8'));self.assertEqual(len(raw['patterns']),12);self.assertEqual(len(converted),10);self.assertEqual(hashlib.sha256(Path(raw['source']).read_bytes()).hexdigest(),raw['sha256'])
  source=(ROOT/'common/图色参数.mq').read_text('utf-8-sig')
  for item in converted:
   a=next(x for x in raw['patterns'] if x['name']==item['name']);d=item['definition'];self.assertEqual(d[4:],[a['main'],a['offsets'],1,0.9]);self.assertEqual(d[:4],[0,0,719,1279] if a['region']==[0,0,0,0] else a['region']);self.assertIn(','.join(json.dumps(x,ensure_ascii=False) for x in d)+',foundX,foundY',source)
  old=json.loads((E/'before/evidence/图色参数.json').read_text('utf-8'));new=json.loads((ROOT/'evidence/图色参数.json').read_text('utf-8'));self.assertEqual([x for x in new if not x['name'].startswith(('015_','014_','013_','012_','150_','155_','154_','153_','081_','080_','082_','079_','078_','166_','055_','056_','050_','151_','152_','070_','032_','强敌_','083_','084_','085_'))],old+converted)
 def test_recovery_monitor_only_accepts_additional_task(self):
  old=(E/'before/common/前台监控.txt').read_text('utf-8-sig');new=before_monthly(ROOT/'common/前台监控.mq').read_text('utf-8-sig');self.assertEqual(new,old.replace('currentTask = 168 Or currentTask = 169','currentTask = 168 Or currentTask = 169 Or currentTask = 167'))
 def test_ui_existing_controls_preserved_and_two_added(self):
  def controls(t):return {re.search(r'名称:"([^"]+)"',body)[1]:(kind,body) for kind,body in re.findall(r'(输入框|下拉框|多选框):\{([^{}]+)\}',t)}
  old=controls((E/'before/ui/最小配置.txt').read_text('utf-8-sig'));new=controls(before_monthly(ROOT/'ui/最小配置.uip').read_text('utf-8-sig'));self.assertEqual({k:new[k] for k in old},old);self.assertEqual(set(new)-set(old),{'日常签到启用','签到间隔秒'})
