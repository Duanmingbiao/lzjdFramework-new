from historical_source import before_stamina
from historical_source import before_friend
import unittest,json,hashlib,re
from pathlib import Path
from mq_subset import load,ROOT
import test_foreground
E=ROOT/'flows/166_领月卡龙石/evidence'
MODULE='flows/166_领月卡龙石/领月卡龙石.mq'
class MonthlyFlow(unittest.TestCase):
 def setUp(self):
  self.now=1000;self.events=[];self.lookups=[];self.visible=set();self.logs=[];self.after=lambda x,y,w:None;self.e={}
  load(['common/任务状态.mq','common/运行计时.mq',MODULE],self.e)
  self.e.update(TickCount=lambda:self.now,Delay=self.delay,MatchPattern=self.match,TouchPoint=self.touch,Note=self.logs.append,SetStage=lambda x:None,ReadActivityText=lambda *a:'活动',ReturnToHall=lambda:1,RESULT_OK=1,RESULT_TIMEOUT=4,businessLimit=120000,SwipeActivityPage=lambda reverse:self.events.append(('swipe',reverse,self.now)))
  self.e['NewSession']();self.e['businessStarted']=self.now
 def delay(self,n):self.now+=n
 def match(self,n):self.lookups.append(n);self.e.update(foundX=100,foundY=1100);return n in self.visible
 def touch(self,x,y,w):self.events.append((x,y,w));self.delay(w);self.after(x,y,w)
 def test_four_card_types_and_order(self):
  for n,kind in [('类型左卡',1),('类型右卡',3),('类型双卡',2),('类型未购买',0)]:
   self.visible={'166_'+n};self.now=1000;self.assertEqual(self.e['DetectMonthlyCard'](),1);self.assertEqual(self.e['monthCardType'],kind);self.assertEqual(self.now,2000)
  self.visible={'166_类型左卡','166_类型双卡'};self.assertEqual(self.e['DetectMonthlyCard'](),1);self.assertEqual(self.e['monthCardType'],1)
 def test_left_pair_uses_same_anchor_then_gray(self):
  self.e['monthCardType']=1;self.visible={'166_左卡可领','166_左卡灰色'};self.assertEqual(self.e['ClaimMonthlyStones'](),1);self.assertEqual(self.events,[(163,916,500),(163,916,500)])
 def test_right_pair_uses_exact_offset(self):
  self.e['monthCardType']=3;self.visible={'166_右卡可领','166_右卡灰色'};self.assertEqual(self.e['ClaimMonthlyStones'](),1);self.assertEqual(self.events,[(510,916,500),(510,916,500)])
 def test_dual_popup_left_right_gray_order(self):
  self.e['monthCardType']=2;self.visible={'166_奖励弹窗','166_左卡可领','166_右卡可领','166_双卡灰色'};self.assertEqual(self.e['ClaimMonthlyStones'](),1);self.assertEqual(self.events,[(100,1100,0),(163,916,500),(163,916,500),(510,916,500),(510,916,500)]);self.assertEqual(self.lookups,['166_奖励弹窗','166_左卡可领','166_右卡可领','166_双卡灰色'])
 def test_dual_requires_both_gray_not_one(self):
  self.e.update(monthCardType=2,businessLimit=100);self.visible={'166_左卡灰色','166_右卡灰色'};self.assertEqual(self.e['ClaimMonthlyStones'](),4);self.assertFalse(self.e['terminalConfirmed'])
 def test_unpurchased_is_explicit_no_reward_and_no_tap(self):
  self.e.update(EnterMonthlyActivities=lambda:1,FindMonthlyPage=lambda:1);self.visible={'166_类型未购买'};self.assertEqual(self.e['ExecuteMonthlyStones'](),1);self.assertTrue(self.e['terminalConfirmed']);self.assertEqual(self.events,[])
 def test_unknown_type_never_success(self):
  self.e['businessLimit']=100;self.assertEqual(self.e['DetectMonthlyCard'](),4);self.assertFalse(self.e['terminalConfirmed'])
 def test_expired_gray_never_success(self):
  self.e.update(monthCardType=1,businessLimit=100);self.now=1100;self.visible={'166_左卡灰色'};self.assertEqual(self.e['ClaimMonthlyStones'](),4)
 def test_interruption_after_pair_blocks_terminal(self):
  self.e['monthCardType']=1;self.visible={'166_左卡可领','166_左卡灰色'};self.after=lambda *a:self.e.update(ForegroundInterrupted=lambda:True);self.assertEqual(self.e['ClaimMonthlyStones'](),4);self.assertFalse(self.e['terminalConfirmed'])
 def test_page_confirm_has_priority_and_direction_starts_one(self):
  self.visible={'166_月卡页面','166_活动框一','166_月卡图标'};self.assertEqual(self.e['FindMonthlyPage'](),1);self.assertEqual(self.lookups,['166_月卡页面']);self.assertEqual(self.events,[]);self.assertEqual(self.e['monthlySearchDirection'],1)
 def test_icon_click_waits_1500_then_confirms(self):
  self.visible={'166_活动框一','166_月卡图标'};self.after=lambda *a:self.visible.add('166_月卡页面');self.assertEqual(self.e['FindMonthlyPage'](),1);self.assertEqual(self.events,[(100,1100,1500)])
 def test_paging_waits_initial_three_seconds_and_reverses_after_seven(self):
  self.visible={'166_活动框一'};self.assertEqual(self.e['FindMonthlyPage'](),4);swipes=[x for x in self.events if x[0]=='swipe'];self.assertGreater(swipes[0][2]-1000,3000);self.assertEqual([x[1] for x in swipes[:14]],[False]*7+[True]*7);self.assertGreater(self.now-1000,37000);self.assertFalse(self.e['terminalConfirmed'])
 def test_dynamic_direction_cycles_one_two_three_four_zero(self):
  directions=[];old=self.e['MatchPattern']
  def match(n):
   if n=='166_月卡页面':directions.append(self.e['monthlySearchDirection'])
   return old(n)
  self.e.update(MatchPattern=match,businessLimit=101);self.e['FindMonthlyPage']();self.assertEqual(directions[:5],[1,2,3,4,0])
 def test_download_prompts_use_exact_text_and_preserve_anchor(self):
  self.visible={'166_资源下载提示'};areas=[]
  def ocr(*a):areas.append(a);self.e.update(foundX=-1,foundY=-1);return '下载新功能' if a[0]==100 else '请在稳定网络下进行'
  self.e['ReadActivityText']=ocr;self.e['MonthResourcePrompt']();self.assertEqual(self.events,[(100,1100,0),(100,1100,0)]);self.assertEqual(areas,[(100,395,317,448),(230,615,479,654)])
  self.events.clear();self.e['monthKeepDownload']=True;self.e['MonthResourcePrompt']();self.assertEqual(self.events,[])
 def test_download_unrecognized_text_does_not_click(self):
  self.visible={'166_资源下载提示'};self.e['ReadActivityText']=lambda *a:'其他文字';self.e['MonthResourcePrompt']();self.assertEqual(self.events,[])
 def test_existing_activity_frame_skips_ocr_entry(self):
  self.visible={'166_活动框二'};self.e['ReadActivityText']=lambda *a:self.fail('unexpected OCR');self.assertEqual(self.e['EnterMonthlyActivities'](),1)
 def test_hall_to_activity_uses_ocr_title(self):
  self.visible={'166_大厅识别一','166_大厅活动入口二'};self.e['ReadActivityText']=lambda *a:'活动' if self.events else '';self.assertEqual(self.e['EnterMonthlyActivities'](),1);self.assertEqual(self.events,[(100,1100,1500)])
 def test_entry_timeout_is_not_success(self):
  self.e.update(ReadActivityText=lambda *a:'');self.assertEqual(self.e['EnterMonthlyActivities'](),4);self.assertGreater(self.now-1000,64000);self.assertFalse(self.e['terminalConfirmed'])
class MonthlyArchitecture(unittest.TestCase):
 def setUp(self):
  self.f=test_foreground.Foreground();self.f.setUp();self.e=self.f.e;self.e.update(signEnabled=True,monthEnabled=True,monthInterval=3600);self.e['RegisterTasks']()
 def test_four_task_serial_first_round_and_independent_state(self):
  for task in [168,169,167,166]:
   self.assertEqual(self.e['SelectDueTask'](),task);self.e['SaveCurrentTask'](task);self.e['terminalConfirmed']=True;self.assertTrue(self.e['CommitTask'](True))
  self.assertEqual([self.e[x] for x in ['mailCount','rewardCount','signCount','monthCount']],[1]*4);self.assertEqual(self.e['monthDue'],3600000);self.assertEqual(self.e['SelectDueTask'](),0)
 def test_only_month_selected_and_resume_has_priority(self):
  self.e.update(mailEnabled=False,rewardEnabled=False,signEnabled=False);self.assertEqual(self.e['SelectDueTask'](),166);self.e['SaveCurrentTask'](166);self.e['SaveRecovery']();self.e.update(mailEnabled=True);self.assertEqual(self.e['SelectDueTask'](),166)
 def test_hall_required_for_commit(self):
  self.e['SaveCurrentTask'](166);self.assertFalse(self.e['CommitTask'](True));self.e['terminalConfirmed']=True;self.assertFalse(self.e['CommitTask'](False));self.assertEqual(self.e['monthCount'],0)
 def test_front_recovery_preserves_month(self):
  self.e['SaveCurrentTask'](166);self.f.request();self.assertTrue(self.e['HandleForegroundRecovery']());self.assertEqual(self.e['resumeTask'],166);self.assertEqual(self.e['monthFailures'],1);self.assertEqual(self.e['SelectDueTask'](),166)
 def test_timeout_recovery_reruns_month(self):
  self.e.update(mailEnabled=False,rewardEnabled=False,signEnabled=False,DispatchTask=lambda t:4);self.e['SchedulerStep']();self.assertEqual(self.e['resumeTask'],166);self.assertEqual(self.e['monthCount'],0)
  seen=[]
  def dispatch(t):seen.append(t);self.e['terminalConfirmed']=True;return 1
  self.e.update(DispatchTask=dispatch,ReturnToHall=lambda:1);self.e['SchedulerStep']();self.assertEqual(seen,[166]);self.assertEqual(self.e['monthCount'],1)
 def test_new_script_session_resets_runtime_only(self):
  self.e.update(monthCount=9,monthFirst=False,monthDue=999);self.e['NewSession']();self.assertEqual(self.e['monthCount'],0);self.assertTrue(self.e['monthFirst']);self.assertEqual(self.e['monthDue'],0);self.assertTrue(self.e['monthEnabled'])
 def test_due_order_includes_sign_selected_due(self):
  self.e.update(mailFirst=False,rewardFirst=False,signFirst=False,monthFirst=False,mailDue=900,rewardDue=800,signDue=500,monthDue=700);self.f.now=1000;self.assertEqual(self.e['SelectDueTask'](),167)
 def test_dispatch_month(self):
  load(['common/任务分派.mq'],self.e);seen=[];self.e['ExecuteMonthlyStones']=lambda:seen.append(166) or 1;self.assertEqual(self.e['DispatchTask'](166),1);self.assertEqual(seen,[166])
class MonthlyPublicApis(unittest.TestCase):
 def setUp(self):
  self.events=[];self.logs=[];self.now=0;self.text='活动';self.front='game';self.interrupted=False
  class Image:
   def OcrText(_, *a):self.events.append(('ocr',a));return self.text
  class Sys:
   def AppIsFront(_,p):return self.front==p
  self.e=dict(Image=Image(),Sys=Sys(),GAME_PACKAGE='game',IsNull=lambda x:x is None,ReleaseCapture=lambda:None,ForegroundInterrupted=lambda:self.interrupted,TickCount=lambda:self.now,Note=self.logs.append,Swipe=lambda *a:self.events.append(('swipe',a)),activityOcrLast='<none>',activityOcrLogAt=-5000)
  load(['common/活动入口.mq'],self.e)
 def test_ocr_exact_region_string_and_empty(self):
  self.assertEqual(self.e['ReadActivityText'](65,7,247,59),'活动');self.assertEqual(self.events,[('ocr',(65,7,247,59,0,0))]);self.text=None;self.assertEqual(self.e['ReadActivityText'](65,7,247,59),'')
 def test_ocr_logging_throttled_same_output(self):
  self.e['ReadActivityText'](65,7,247,59);self.e['ReadActivityText'](65,7,247,59);self.assertEqual(len(self.logs),1);self.now=5000;self.e['ReadActivityText'](65,7,247,59);self.assertEqual(len(self.logs),2)
 def test_swipe_coordinates_duration_and_secondary_swipe(self):
  self.e['SwipeActivityPage'](False);self.assertEqual(self.events,[('swipe',(609,137,159,137,300)),('swipe',(100,100,100,50,100))]);self.events.clear();self.e['SwipeActivityPage'](True);self.assertEqual(self.events[0],('swipe',(159,137,609,137,300)))
 def test_swipe_blocked_outside_game(self):
  self.front='other';self.e['SwipeActivityPage'](False);self.assertEqual(self.events,[])
class MonthlyEvidence(unittest.TestCase):
 def test_original_business_and_nonintegration_sources_unchanged(self):
  allowed={'app/入口.mq','common/配置读取.mq','common/任务状态.mq','common/任务注册.mq','common/任务分派.mq','common/前台监控.mq','common/图色参数.mq','ui/最小配置.uip'}
  for rel,h in json.loads((E/'修改前基线.json').read_text('utf-8')).items():
   self.assertEqual(hashlib.sha256((E/'before'/Path(rel).with_suffix('.txt')).read_bytes()).hexdigest(),h)
   if rel not in allowed:self.assertEqual(hashlib.sha256(before_stamina(ROOT/rel).read_bytes()).hexdigest(),h,rel)
 def test_twenty_patterns_preserve_colors_regions_and_direction(self):
  raw=json.loads((E/'原始图色.json').read_text('utf-8'));converted=json.loads((E/'图色转换.json').read_text('utf-8'));self.assertEqual(len(converted),20)
  for src in raw['sources']:self.assertEqual(hashlib.sha256(Path(src['file']).read_bytes()).hexdigest(),src['sha256'])
  for c in converted:
   r=next(x for x in raw['patterns'] if x['name']==c['name']);d=c['definition'];self.assertEqual(d[4:6],[r['main'],r['offsets']]);self.assertEqual(d[:4],[0,0,719,1279] if r['region']==[0,0,0,0] else r['region']);self.assertEqual(d[7],0.9)
  old=json.loads((E/'before/evidence/图色参数.json').read_text('utf-8'));now=json.loads((ROOT/'evidence/图色参数.json').read_text('utf-8'));self.assertEqual([x for x in now if not x['name'].startswith(('013_','012_','150_','155_','154_','153_','081_','080_','082_','079_','078_','055_','056_','050_','151_','152_','070_','032_','强敌_','083_','084_','085_'))],old+converted)
 def test_monitor_change_only_recognizes_new_task(self):
  old=(E/'before/common/前台监控.txt').read_text('utf-8-sig');now=before_friend(ROOT/'common/前台监控.mq').read_text('utf-8-sig');self.assertEqual(now,old.replace('Or currentTask = 167 Then','Or currentTask = 167 Or currentTask = 166 Then'))
 def test_existing_ui_preserved_three_settings_added(self):
  def controls(t):return {re.search(r'名称:"([^"]+)"',b)[1]:(k,b) for k,b in re.findall(r'(输入框|下拉框|多选框):\{([^{}]+)\}',t)}
  old=controls((E/'before/ui/最小配置.txt').read_text('utf-8-sig'));now=controls(before_friend(ROOT/'ui/最小配置.uip').read_text('utf-8-sig'));self.assertEqual({k:now[k] for k in old},old);self.assertEqual(set(now)-set(old),{'月卡龙石启用','月卡间隔秒','保留下载提示'})
