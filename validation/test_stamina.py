import unittest,json,hashlib
from types import SimpleNamespace
from mq_subset import ROOT,load
E=ROOT/'flows/050_定时领取体力/evidence'
MODULE='flows/050_定时领取体力/定时领取体力.mq'
class StaminaTests(unittest.TestCase):
 def setUp(self):
  self.now=0;self.stamp=1760000000;self.logs=[];self.taps=[];self.visible=set();self.matches=[];self.text='';self.interrupt=False
  self.e=dict(RESULT_OK=1,RESULT_TIMEOUT=4,RESULT_FAIL=3,Time=lambda:self.stamp,Int=lambda n:int(n//1),TickCount=lambda:self.now,Delay=self.delay,Note=self.logs.append,WriteMainLog=self.logs.append,SetStage=lambda n:None,SetTimedStaminaPhase=lambda *a:None,GAME_PACKAGE='game',Sys=SimpleNamespace(AppIsFront=lambda p:True),BusinessExpired=lambda:self.now>=120000 or self.interrupt,MatchPattern=self.match,TouchPoint=self.tap,ReleaseCapture=lambda:None,Progress=lambda:None,Image=SimpleNamespace(OcrText=lambda *a:self.text),IsNull=lambda x:x is None,IsNumeric=lambda x:str(x).replace('.','',1).isdigit(),CDbl=float,InStr=lambda start,s,sub:s.find(sub)+1,staminaGem=False,staminaRecover=False,staminaExchange=False,staminaKeepDownload=False,staminaEnabled=True,currentTask=50,staminaPhase='test',terminalConfirmed=False)
  load(['common/定时体力状态.mq',MODULE],self.e)
 def delay(self,n):self.now+=n
 def match(self,n):self.matches.append(n);self.e['foundX']=100;self.e['foundY']=1000;return n in self.visible
 def tap(self,x,y,w):self.taps.append((x,y,w));self.delay(w)
 def state(self):load(['common/定时体力状态.mq'],self.e);self.e['NewTimedStaminaSession']()
 def at(self,seconds):self.stamp=self.e['StaminaDayStart'](1760000000)+seconds
 def test_single_free_click_then_confirm(self):
  self.visible={'050_上午可领'};old=self.tap
  def tap(x,y,w):old(x,y,w);self.visible={'050_上午已领'}
  self.e['TouchPoint']=tap;self.assertEqual(self.e['ClaimTimedStamina'](1),1);self.assertEqual(self.taps,[(100,1000,200)])
 def test_no_reward_already_claimed_is_explicit_terminal(self):
  self.visible={'050_上午已领'};self.assertEqual(self.e['ClaimTimedStamina'](1),1);self.assertFalse(self.taps)
 def test_unknown_page_times_out_without_success(self):
  self.assertEqual(self.e['ClaimTimedStamina'](1),4);self.assertFalse(self.e['terminalConfirmed'])
 def test_gem_claim_order_and_combined_terminal(self):
  self.e['staminaGem']=True;self.visible={'050_上午可领','050_上午可补','050_中午可领','050_中午可补','050_前两档已领'}
  self.assertEqual(self.e['ClaimTimedStamina'](2),1);self.assertEqual(self.matches,['050_上午可领','050_上午可补','050_中午可领','050_中午可补','050_前两档已领']);self.assertEqual([x[2] for x in self.taps],[200]*4)
 def test_without_gem_does_not_click_earlier_slots_or_makeup(self):
  self.visible={'050_中午已领'};self.assertEqual(self.e['ClaimTimedStamina'](2),1);self.assertEqual(self.matches,['050_中午可领','050_中午已领'])
 def test_initial_order_claimed_makeup_free(self):
  self.visible={'050_上午可领'};self.assertEqual(self.e['DetectStaminaSlot'](1),1);self.assertEqual(self.matches,['050_上午已领','050_上午可补','050_上午可领'])
 def test_full_free_flow_confirms_before_public_commit(self):
  self.e['EnterTimedStaminaPage']=lambda:1;self.visible={'050_上午已领'};self.assertEqual(self.e['ExecuteTimedStamina'](50),1);self.assertTrue(self.e['terminalConfirmed']);self.assertTrue(self.e['staminaTerminal']);self.assertFalse(any('是否提交完成=是' in x for x in self.logs))
 def test_bulk_slot5_scans_four_slots(self):
  self.e['EnterTimedStaminaPage']=lambda:1;self.visible={f'050_{x}已领' for x in ['上午','中午','下午','晚上']};self.assertEqual(self.e['ExecuteTimedStamina'](54),1);self.assertIn('050_晚上已领',self.matches)
 def test_extras_unknown_15second_protection_not_success(self):
  self.e['staminaRecover']=True;self.assertEqual(self.e['TimedStaminaExtras'](),4);self.assertGreater(self.now,15000)
 def test_recover_gray_without_exchange(self):
  self.e['staminaRecover']=True;self.visible={'050_追回灰色'};self.assertEqual(self.e['TimedStaminaExtras'](),1);self.assertFalse(self.taps)
 def test_recover_ocr_confirmation_coordinates(self):
  self.e['staminaRecover']=True;self.visible={'050_追回确认'};self.text='是否消耗';self.assertEqual(self.e['TimedStaminaExtras'](),1);self.assertEqual(self.taps,[(440,785,1000)])
 def test_exchange_special_three_click_sequence(self):
  self.e['staminaExchange']=True;self.visible={'050_兑换弹窗'};self.assertEqual(self.e['TimedStaminaExtras'](),1);self.assertEqual(self.taps,[(612,650,1000),(412,750,1000),(412,750,1000)])
 def test_exchange_balance_below40_exits_without_spending(self):
  self.e['staminaExchange']=True;self.visible={'050_兑换可用'};self.text='39';self.assertEqual(self.e['TimedStaminaExtras'](),1);self.assertFalse(self.taps)
 def test_exchange_40_spends_once_then_gray_confirms(self):
  self.e['staminaExchange']=True;self.visible={'050_兑换可用'};self.text='40';old=self.tap
  def tap(x,y,w):old(x,y,w);self.visible={'050_兑换灰色'}
  self.e['TouchPoint']=tap;self.assertEqual(self.e['TimedStaminaExtras'](),1);self.assertEqual(self.taps,[(570,777,1000)])
 def test_foreground_interrupt_never_terminal(self):
  self.interrupt=True;self.assertEqual(self.e['ExecuteTimedStamina'](50),4);self.assertFalse(self.e['terminalConfirmed'])
 def test_schedule_before_start_does_not_run_on_boot(self):
  self.state();self.at(6*3600);self.e['NewTimedStaminaSession']();self.assertEqual(self.e['SelectTimedStamina'](),0)
 def test_schedule_boundaries_each_window(self):
  self.state()
  for id,start,end in [(50,25205,43200),(51,43205,64800),(52,64805,75600),(53,75605,86310)]:
   self.at(start);self.e['NewTimedStaminaSession']();self.assertEqual(self.e['SelectTimedStamina'](),id)
   self.at(end);self.e['NewTimedStaminaSession']();self.assertEqual(self.e['SelectTimedStamina'](),id)
   self.at(end+1);self.e['NewTimedStaminaSession']();self.assertNotEqual(self.e['SelectTimedStamina'](),id)
 def test_midnight_requires_gem(self):
  self.state();self.at(60);self.e['NewTimedStaminaSession']();self.assertEqual(self.e['SelectTimedStamina'](),0);self.e['staminaGem']=True;self.assertEqual(self.e['SelectTimedStamina'](),54)
 def test_stale_due_before_later_slot_does_not_run_early(self):
  self.state();self.at(8*3600);self.e['stamina50Due']=self.stamp+86400;self.e['stamina51Due']=self.stamp-86400;self.assertEqual(self.e['SelectTimedStamina'](),0)
 def test_commit_moves_only_one_slot_to_next_day(self):
  self.state();self.at(25205);other=self.e['stamina51Due'];self.e['CommitTimedStamina'](50);self.assertEqual(self.e['stamina50Count'],1);self.assertEqual(self.e['stamina51Count'],0);self.assertEqual(self.e['stamina51Due'],other);self.assertEqual(self.e['stamina50Due'],self.stamp+86400)
 def test_recovery_counts_and_restart_counts_per_slot(self):
  self.state();self.e['StartTimedStamina'](50);self.e['RecoverTimedStamina'](50);self.e['RestartTimedStamina'](50);self.e['StartTimedStamina'](51);self.assertEqual(self.e['staminaRecoveryCount'],0);self.e['StartTimedStamina'](50);self.assertEqual(self.e['staminaRecoveryCount'],1);self.assertEqual(self.e['staminaRestartCount'],1)
 def test_resume_has_priority_outside_window(self):
  self.state();load(['common/任务注册.mq'],self.e);self.e.update(resumeTask=53,registeredTask=168,rewardRegisteredTask=169,signRegisteredTask=167,monthRegisteredTask=166,friendRegisteredTask=55,qfriendRegisteredTask=56);self.assertEqual(self.e['SelectDueTask'](),53)
 def test_commit_requires_hall_confirmation(self):
  self.state();load(['common/任务状态.mq'],self.e);self.e.update(currentTask=50,resumeTask=50,terminalConfirmed=True,BeginForegroundCommit=lambda:True,EndForegroundCommit=lambda:None);self.assertFalse(self.e['CommitTask'](False));self.assertEqual(self.e['stamina50Count'],0);self.assertTrue(self.e['CommitTask'](True));self.assertEqual(self.e['stamina50Count'],1)
 def test_existing_six_businesses_bytes_unchanged(self):
  for folder in ['168_领邮件奖励','169_领任务奖励','167_日常签到','166_领月卡龙石','055_好友体力','056_Q友体力']:
   for p in (ROOT/'flows'/folder).glob('*.mq'):self.assertEqual(p.read_bytes(),(E/'before'/p.relative_to(ROOT).with_suffix('.txt')).read_bytes())
 def test_exact_catalog_conversion_append_only(self):
  before=json.loads((E/'before/evidence/图色参数.txt').read_text('utf-8'));now=[x for x in json.loads((ROOT/'evidence/图色参数.json').read_text('utf-8')) if not x['name'].startswith(('151_','152_'))];conv=json.loads((E/'图色转换.json').read_text('utf-8'));self.assertEqual(now[:len(before)],before);self.assertEqual([x['definition'] for x in now[len(before):]],[x['definition'] for x in conv])

 def test_recovery_after_midnight_keeps_today_next_occurrence(self):
  self.state();self.at(4*3600);day=self.e['StaminaDayStart'](self.stamp);self.e['CommitTimedStamina'](53);self.assertEqual(self.e['stamina53Due'],day+75605)
 def test_activity_target_page_confirms_without_icon_click(self):
  self.e['EnterTimedActivities']=lambda:1;self.visible={'050_体力页面一'};self.assertEqual(self.e['EnterTimedStaminaPage'](),1);self.assertFalse(self.taps)
 def test_activity_icon_uses_source_wait_and_rechecks_page(self):
  self.e['EnterTimedActivities']=lambda:1;self.visible={'050_活动框一','050_体力图标'};old=self.tap
  def tap(x,y,w):old(x,y,w);self.visible={'050_体力页面二'}
  self.e['TouchPoint']=tap;self.assertEqual(self.e['EnterTimedStaminaPage'](),1);self.assertEqual(self.taps,[(100,1000,1500)])
 def test_page_entry_35second_timeout_not_success(self):
  self.e['EnterTimedActivities']=lambda:1;self.assertEqual(self.e['EnterTimedStaminaPage'](),4);self.assertGreater(self.now,37000)
 def test_boolean_config_false_string_is_disabled(self):
  self.e.update(ReadUIConfig=lambda key,default:'false',CStr=str,LCase=lambda s:s.lower(),Trim=lambda s:s.strip());self.assertFalse(self.e['StaminaBooleanSetting']('定时体力启用'))
 def test_only_expected_integration_sources_changed(self):
  allowed={'app/入口.mq','common/配置读取.mq','common/任务状态.mq','common/图色参数.mq','common/任务注册.mq','common/任务分派.mq','common/任务调度.mq','common/前台监控.mq','common/游戏控制.mq','ui/最小配置.uip','project.json','assistant-sync.json','evidence/图色参数.json'}
  for rel,h in json.loads((E/'修改前基线.json').read_text('utf-8')).items():
   if rel not in allowed:self.assertEqual(hashlib.sha256((ROOT/rel).read_bytes()).hexdigest(),h,rel)
