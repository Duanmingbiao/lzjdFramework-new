import unittest,json,hashlib
from types import SimpleNamespace
from mq_subset import ROOT,load
E=ROOT/'flows/152_合作大冒险/evidence';MODULE='flows/152_合作大冒险/合作大冒险.mq'
class CoopTests(unittest.TestCase):
 def setUp(self):
  self.now=0;self.logs=[];self.taps=[];self.visible=set();self.matches=[];self.interrupt=False
  self.e=dict(RESULT_OK=1,RESULT_FAIL=3,RESULT_TIMEOUT=4,TickCount=lambda:self.now,Time=lambda:1760000000+self.now//1000,Delay=self.delay,Note=self.logs.append,SetStage=lambda s:None,MatchPattern=self.match,TouchPoint=self.tap,ReleaseCapture=lambda:None,Swipe=lambda *a:None,BusinessExpired=lambda:self.now>=120000 or self.interrupt,Sys=SimpleNamespace(AppIsFront=lambda p:True),GAME_PACKAGE='game',Progress=lambda:None,coopKeepDownload=True,coopTeamMode=0,coopPhase='test',coopLastMatch='',coopLastOcr='',terminalConfirmed=False,coopTerminal=False,DateTime=SimpleNamespace(WeekDay=lambda:5,Hour=lambda:12))
  load([MODULE],self.e)
 def delay(self,n):self.now+=n
 def tap(self,x,y,w):self.taps.append((x,y,w));self.delay(w)
 def match(self,n):self.matches.append(n);self.e['foundX']=100;self.e['foundY']=1000;return n in self.visible
 def state(self):load(['common/合作冒险状态.mq'],self.e);self.e['NewCoopSession']()
 def test_hall_icon_offset_wait(self):
  self.visible={'152_大厅条件一','152_大厅入口一'};old=self.tap
  def tap(x,y,w):old(x,y,w);self.visible={'152_大厅入口二'}
  self.e['TouchPoint']=tap;self.assertEqual(self.e['EnterCoopAdventure'](),1);self.assertEqual(self.taps,[(260,940,1500)])
 def test_fast_join_offset_and_page_confirm(self):
  self.visible={'152_组队首页'};old=self.tap
  def tap(x,y,w):old(x,y,w);self.visible={'152_冒险主界面'}
  self.e['TouchPoint']=tap;self.assertEqual(self.e['EnterCoopTeam'](),1);self.assertEqual(self.taps,[(504,880,200)]);self.assertEqual(self.now,400)
 def test_solo_create_check_start_order(self):
  self.e['coopTeamMode']=1;self.visible={'152_组队首页','152_独玩勾选前','152_独玩开启','152_冒险主界面'};self.assertEqual(self.e['EnterCoopTeam'](),1);self.assertEqual(self.taps,[(200,880,200),(517,881,200),(351,876,200)])
 def test_solo_after_six_checks_uses_quick_leave_pattern(self):
  self.e['coopTeamMode']=1;self.visible={'152_组队首页','152_独玩勾选前','152_快速离开'};old=self.tap
  def tap(x,y,w):
   old(x,y,w)
   if (x,y)==(351,876):self.visible={'152_冒险主界面'}
  self.e['TouchPoint']=tap;self.assertEqual(self.e['EnterCoopTeam'](),1);self.assertEqual(self.matches.count('152_独玩开启'),5);self.assertEqual(self.matches.count('152_快速离开'),1)
 def test_unknown_team_10sec_timeout_never_success(self):
  self.assertEqual(self.e['EnterCoopTeam'](),4);self.assertFalse(self.e['terminalConfirmed']);self.assertGreater(self.now,11000)
 def test_event_order_offsets_and_waits(self):
  self.visible={'152_抽牌事件','152_抽牌完成','152_随机事件','152_转盘未抽','152_体力购买'};self.assertEqual(self.e['RunCoopAdventure'](),1);self.assertEqual(self.taps,[(510,773,50),(220,1012,50),(100,1000,1000),(350,430,2000)]);self.assertFalse(self.e['terminalConfirmed'])
 def test_challenge_doubleclick_same_anchor(self):
  self.visible={'152_挑战对话','152_体力购买'};self.assertEqual(self.e['RunCoopAdventure'](),1);self.assertEqual(self.taps,[(100,1000,200)]*2);self.assertEqual(self.now,450)
 def test_battle_start_fixed_coordinates(self):
  self.visible={'152_开战图标6','152_体力购买'};self.assertEqual(self.e['RunCoopAdventure'](),1);self.assertEqual(self.taps,[(398,982,500),(587,982,500)])
 def test_boss_click_cap_five_without_false_success(self):
  self.visible={'152_BOSS一','152_BOSS二'};self.assertEqual(self.e['RunCoopAdventure'](),4);self.assertEqual(len(self.taps),5);self.assertNotIn('152_BOSS二',self.matches)
 def test_dice_count_six_without_approved_terminal_fails(self):
  self.visible={'152_冒险主界面'};self.assertEqual(self.e['RunCoopAdventure'](),3);self.assertEqual(self.taps,[(616,913,50)]*6);self.assertFalse(self.e['terminalConfirmed'])
 def test_open_battle_failure_counter_requires_recovery(self):
  self.visible={'152_开战图标6'};self.assertEqual(self.e['RunCoopAdventure'](),3);self.assertEqual(len(self.taps),22)
 def test_local300sec_unknown_timeout(self):
  self.e['BusinessExpired']=lambda:self.now>=600000;self.assertEqual(self.e['RunCoopAdventure'](),4);self.assertGreater(self.now,301000)
 def test_cleanup_claimed_close_is_terminal(self):
  self.visible={'152_已领取关闭'};self.assertEqual(self.e['FinishCoopAdventure'](),1);self.assertEqual(self.taps,[(100,1000,50)])
 def test_cleanup_five_confirmed_board_actions_exact_alternation(self):
  self.visible={'152_冒险主界面'};self.assertEqual(self.e['FinishCoopAdventure'](),1);self.assertEqual(self.taps,[(110,207,1000),(630,-93,1000),(110,207,1000),(630,-93,1000),(110,207,1000)])
 def test_purchase_close_before_claimed_result(self):
  self.visible={'152_体力购买','152_已领取关闭'};self.assertEqual(self.e['FinishCoopAdventure'](),1);self.assertEqual(self.taps,[(398,694,50),(100,1000,50)])
 def test_unknown_cleanup_not_success(self):
  self.assertEqual(self.e['FinishCoopAdventure'](),4);self.assertFalse(self.e['terminalConfirmed'])
 def test_full_normal_cycle_not_committed_in_business(self):
  self.e['EnterCoopAdventure']=lambda:1;self.e['EnterCoopTeam']=lambda:1;self.e['RunCoopAdventure']=lambda:1;self.visible={'152_已领取关闭'};self.assertEqual(self.e['ExecuteCoopAdventure'](),1);self.assertTrue(self.e['terminalConfirmed']);self.assertTrue(self.e['coopTerminal']);self.assertFalse(any('是否提交完成=是' in x for x in self.logs))
 def test_full_main_failure_cannot_reach_cleanup_or_succeed(self):
  self.e['EnterCoopAdventure']=lambda:1;self.e['EnterCoopTeam']=lambda:1;self.e['RunCoopAdventure']=lambda:3;self.e['FinishCoopAdventure']=lambda:self.fail('cleanup reached');self.assertEqual(self.e['ExecuteCoopAdventure'](),3);self.assertFalse(self.e['terminalConfirmed'])
 def test_foreground_interruption_blocks_terminal(self):
  self.interrupt=True;self.assertEqual(self.e['ExecuteCoopAdventure'](),4);self.assertFalse(self.e['terminalConfirmed'])
 def test_commit_hall_gate_and12hour_due_only152(self):
  self.state();load(['common/任务状态.mq'],self.e);self.e.update(currentTask=152,resumeTask=152,terminalConfirmed=True,BeginForegroundCommit=lambda:True,EndForegroundCommit=lambda:None,wukongCount=7,mailCount=8)
  self.assertFalse(self.e['CommitTask'](False));self.assertEqual(self.e['coopCount'],0);self.assertTrue(self.e['CommitTask'](True));self.assertEqual(self.e['coopCount'],1);self.assertEqual(self.e['coopDue'],43200000);self.assertEqual(self.e['wukongCount'],7);self.assertEqual(self.e['mailCount'],8)
 def test_recovery152_priority_even_disabled_outside_time(self):
  self.state();load(['common/任务状态.mq','common/任务注册.mq'],self.e);self.e['RegisterTasks']();self.e['coopEnabled']=False;self.e['currentTask']=152;self.e['SaveRecovery']();self.assertEqual(self.e['SelectDueTask'](),152);self.assertEqual(self.e['coopRecoveries'],1)
 def test_exact_native_weekday_branch_values(self):
  self.state()
  for week in [0,1,2,3,4,5,6,7]:
   self.e['DateTime'].WeekDay=lambda w=week:w;self.assertEqual(self.e['CoopTimeEligible'](),week<=5 and week!=1)
 def test_all_existing_business_files_unchanged(self):
  for rel,h in json.loads((E/'修改前基线.json').read_text('utf-8')).items():
   if rel.startswith('flows/') or rel in ['common/悟空冒险状态.mq','common/定时体力状态.mq']:self.assertEqual(hashlib.sha256((ROOT/rel).read_bytes()).hexdigest(),h,rel)
 def test_append_only_exact_parameters(self):
  old=json.loads((E/'before/evidence/图色参数.txt').read_text('utf-8'));now=[x for x in json.loads((ROOT/'evidence/图色参数.json').read_text('utf-8')) if not x['name'].startswith(('015_','014_','013_','012_','150_','155_','154_','153_','081_','080_','082_','079_','078_','070_','032_','强敌_','083_','084_','085_'))];conv=json.loads((E/'图色转换.json').read_text('utf-8'));self.assertEqual(now[:len(old)],old);self.assertEqual([x['definition'] for x in now[len(old):]],[x['definition'] for x in conv])
 def test_same_page_independent_modes_default_zero_and_no_placeholder(self):
  ui=(ROOT/'ui/最小配置.uip').read_text('utf-8-sig');self.assertIn('日常功能:{',ui);self.assertIn('名称:"合作冒险启用"',ui);self.assertIn('名称:"合作队伍模式"',ui);self.assertNotIn('合作待开发',ui);self.assertEqual(json.loads((ROOT/'project.json').read_text('utf-8'))['registeredTasks'].count(152),1)
