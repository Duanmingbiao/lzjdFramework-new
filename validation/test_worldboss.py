import unittest,json,hashlib,math,re
from types import SimpleNamespace
from mq_subset import ROOT,load
class WorldBossTests(unittest.TestCase):
 def setUp(self):
  self.now=0; self.stamp=1760000000;self.logs=[];self.taps=[];self.visible=set();self.lookups=[];self.text='';self.after=lambda *a:None;self.interrupt=False
  self.e={'RESULT_OK':1,'RESULT_WAIT':2,'RESULT_FAIL':3,'RESULT_TIMEOUT':4,'TickCount':lambda:self.now,'Time':lambda:self.stamp+self.now//1000,'Delay':self.delay,'Note':self.logs.append,'WriteMainLog':self.logs.append,'SetStage':lambda s:None,'Progress':lambda:None,'MatchPattern':self.match,'TouchPoint':self.tap,'ReleaseCapture':lambda:None,'Swipe':lambda *a:None,'Sys':SimpleNamespace(AppIsFront=lambda p:True),'GAME_PACKAGE':'game','BusinessExpired':lambda:self.now>=120000 or self.interrupt,'Image':SimpleNamespace(OcrText=lambda *a:self.text),'IsNull':lambda x:x is None,'IsNumeric':lambda x:not isinstance(x,bool) and str(x).replace('.','',1).isdigit(),'CDbl':float,'Int':math.floor,'CStr':str,'LCase':lambda x:x.lower(),'Trim':lambda x:x.strip(),'Rnd':lambda:0.0,'worldKeepDownload':True,'worldEnabled':False,'cellEnabled':False,'worldBuyConfig':0,'worldHour':10,'worldMinute':0,'currentTask':70,'terminalConfirmed':False}
  load(['common/世界首领状态.mq','common/强敌入口.mq','flows/070_世界首领/世界首领.mq','flows/032_世界首领沙鲁/打沙鲁.mq'],self.e)
  self.e['NewWorldBossSession']()
 def delay(self,n):self.now+=n
 def match(self,n):
  self.lookups.append(n);self.e['foundX']=600;self.e['foundY']=900;return n in self.visible
 def tap(self,x,y,w):self.taps.append((x,y,w));self.delay(w);self.after(x,y,w)
 def at(self,h,m=0):self.stamp=self.e['WorldDayStart'](self.stamp)+h*3600+m*60;self.now=0
 def test_config_false_and_numeric_bounds(self):
  for raw in [False,'false',' FALSE ',0,'0',None,'']:
   self.e['ReadUIConfig']=lambda *a,v=raw:v;self.assertFalse(self.e['WorldBoolean']('world'))
  for raw in [True,'true',1,'1']:
   self.e['ReadUIConfig']=lambda *a,v=raw:v;self.assertTrue(self.e['WorldBoolean']('world'))
  for raw in [-1,'bad',24,None]:
   self.e['ReadUIConfig']=lambda *a,v=raw:v;self.assertEqual(self.e['WorldNumber']('h',10,23),10)
 def test_timed_not_immediate_before10(self):
  self.at(9);self.e['NewWorldBossSession']();self.e.update(worldEnabled=True,cellEnabled=True);self.assertEqual(self.e['SelectWorldBoss'](),0)
 def test70_at10_and32_only21(self):
  self.at(10);self.e['NewWorldBossSession']();self.e.update(worldEnabled=True,cellEnabled=True);self.assertEqual(self.e['SelectWorldBoss'](),70);self.e['worldEnabled']=False;self.assertEqual(self.e['SelectWorldBoss'](),0);self.at(21);self.assertEqual(self.e['SelectWorldBoss'](),32)
 def test23_window_rolls_without_completion(self):
  self.at(23);self.e['NewWorldBossSession']();self.e.update(worldEnabled=True,cellEnabled=True);self.assertEqual(self.e['SelectWorldBoss'](),0);self.assertFalse(self.e['worldDone']);self.assertFalse(self.e['cellDone']);self.assertEqual(self.e['worldCount'],0);self.assertGreater(self.e['worldDue'],self.stamp)
 def test_daytime_commit_random_range_endpoints(self):
  self.at(12);day=self.e['WorldDayStart'](self.stamp)
  for rnd,minute in [(0,1),(.99999,50)]:
   self.e['Rnd']=lambda v=rnd:v;self.e['CommitWorldBossTask'](70);self.assertEqual(self.e['worldDue'],day+75600+minute*60)
 def test_night_commit_nextday_config(self):
  self.at(21,30);self.e['worldHour']=11;self.e['worldMinute']=12;self.e['CommitWorldBossTask'](70);self.assertEqual(self.e['worldDue'],self.e['WorldDayStart'](self.stamp)+86400+40320)
 def test_cell_commit_independent(self):
  self.at(22);self.e.update(currentTask=32,worldCount=8);self.e['CommitWorldBossTask'](32);self.assertEqual(self.e['worldCount'],8);self.assertEqual(self.e['cellCount'],1);self.assertEqual(self.e['cellDue'],self.e['WorldDayStart'](self.stamp)+86400+75600)
 def test_recovery_preserves_buy_and_counts(self):
  self.e.update(worldBuyRuntime=3,worldCount=4);self.e['RecoverWorldBossTask'](70);self.assertEqual(self.e['worldBuyRuntime'],3);self.assertEqual(self.e['worldCount'],4);self.assertEqual(self.e['worldRecoveries'],1);self.assertFalse(self.e['worldTerminal'])
 def test_entry_click_and_page_confirmation(self):
  self.visible={'070_入口二'};self.after=lambda *a:self.visible.add('070_首领界面');self.assertEqual(self.e['EnterBossPage']('070_'),1);self.assertEqual(self.taps,[(600,900,300)]);self.assertEqual(self.now,1000)
 def test_unknown_entry_times_out(self):
  self.assertEqual(self.e['EnterBossPage']('070_'),4);self.assertFalse(self.e['terminalConfirmed'])
 def test_buy_off_no_tap(self):
  self.e['worldBuyRuntime']=0;self.assertEqual(self.e['BuyWorldBossAttempts'](),1);self.assertFalse(self.taps)
 def purchase(self,mode,text):
  self.e['worldBuyRuntime']=mode;self.text=text;self.visible={'070_首领界面'}
  def after(x,y,w):
   if (x,y)==(640,1050):self.visible={'070_购买弹窗'}
   if (x,y) in [(294,1230),(589,917)]:self.visible={'070_首领界面'}
  self.after=after;return self.e['BuyWorldBossAttempts']()
 def test_buy_exact_prices_and_clicks(self):
  for mode,adds,price in [(1,2,60),(2,4,140),(3,6,320),(4,9,870)]:
   self.setUp();self.assertEqual(self.purchase(mode,str(price)),1);self.assertEqual(self.taps[0],(640,1050,1000));self.assertEqual(self.taps[1:1+adds],[(388,1052,300)]*adds);self.assertEqual(self.taps[-1],(294,1230,0));self.assertEqual(self.e['worldBuyRuntime'],0)
 def test_bad_or_mismatched_price_closes_without_buy(self):
  for text in ['', 'OCR不可用','59','870']:
   self.setUp();self.assertEqual(self.purchase(1,text),1);self.assertNotIn((294,1230,0),self.taps);self.assertEqual(self.taps[-1],(589,917,0))
 def test_purchase15sec_clears_only_runtime(self):
  self.e.update(worldBuyRuntime=2,worldBuyConfig=2);self.assertEqual(self.e['BuyWorldBossAttempts'](),1);self.assertGreater(self.now,15000);self.assertEqual(self.e['worldBuyRuntime'],0);self.assertEqual(self.e['worldBuyConfig'],2);self.assertFalse(self.e['terminalConfirmed'])
 def test_no_attempts_ocr_enters_reward_not_success(self):
  self.visible={'070_扫荡一'}
  for text in ['挑战次数0','挑战次数|0']:
   self.text=text;self.assertEqual(self.e['SweepWorldBoss'](),1);self.assertFalse(self.e['terminalConfirmed'])
  self.assertFalse(self.taps)
 def test_blank_ocr_not_zero_and_triple16cycles(self):
  self.visible={'070_扫荡一'};self.text='';self.assertEqual(self.e['SweepWorldBoss'](),1);self.assertEqual(len(self.taps),48);self.assertEqual(self.taps[:3],[(600,900,50),(600,900,50),(600,900,100)]);self.assertFalse(self.e['terminalConfirmed'])
 def test30sec_native_stage_exit_not_business_terminal(self):
  self.assertEqual(self.e['SweepWorldBoss'](),1);self.assertGreater(self.now,30000);self.assertFalse(self.e['terminalConfirmed'])
 def test_wait_revive_does_not_reset30sec_timer(self):
  self.visible={'070_复活一'};self.assertEqual(self.e['SweepWorldBoss'](),1);self.assertGreater(self.now,30000);self.assertFalse(self.taps);self.assertFalse(self.e['terminalConfirmed'])
 def test_all_three_user_approved_terminals(self):
  for prefix in ['070_','032_']:
   for name,taps in [('无奖一',[]),('灰领二',[(600,900,300)]),('领奖弹窗一',[(100,50,500),(100,50,0)] if prefix=='070_' else [(600,900,500),(600,900,0)])]:
    self.setUp();self.visible={prefix+name};self.assertEqual(self.e['FinishBossRewards'](prefix),1);self.assertEqual(self.taps,taps);self.assertFalse(self.e['terminalConfirmed']);self.assertTrue(self.e['worldTerminalReason'])
 def test_reward_priority_no_reward_before_gray(self):
  self.visible={'070_无奖一','070_灰领一','070_蓝领一'};self.assertEqual(self.e['FinishBossRewards']('070_'),1);self.assertFalse(self.taps);self.assertNotIn('070_灰领一',self.lookups)
 def test_unknown_reward_not_terminal(self):
  self.assertEqual(self.e['FinishBossRewards']('070_'),4);self.assertFalse(self.e['terminalConfirmed'])
 def test_ended_cell_encounter_path(self):
  self.visible={'032_奇遇结束二'};self.assertEqual(self.e['EnterCellEncounter'](),1);self.assertTrue(self.e['cellEncounterEnded']);self.assertFalse(self.taps)
 def test_active_cell_encounter_path(self):
  self.visible={'032_奇遇界面一','032_奇遇结束一'};self.assertEqual(self.e['EnterCellEncounter'](),1);self.assertFalse(self.e['cellEncounterEnded'])
 def test_cell_sweep21_and4_bounded_six_clicks(self):
  for limit in [20,3]:
   self.setUp();self.visible={'032_扫荡二'};self.assertEqual(self.e['SweepCellEncounter'](limit),1);self.assertEqual(len(self.taps),6*(limit+1));self.assertEqual(self.taps[:6],[(600,900,50)]*5+[(600,900,0)]);self.assertFalse(self.e['terminalConfirmed'])
 def test_cell_close_priority_before_sweep(self):
  self.visible={'032_关闭一','032_扫荡一'};self.assertEqual(self.e['SweepCellEncounter'](20),1);self.assertEqual(self.taps,[(600,900,50)])
 def test_cell_battle_four_starts_only_stage_exit(self):
  self.visible={'032_开战一'};self.assertEqual(self.e['RunCellFirstBattle'](),1);self.assertEqual(self.taps,[(600,900,300)]*4);self.assertFalse(self.e['terminalConfirmed'])
 def test_cell_start_icon_lack_pause_exit_order(self):
  self.visible={'032_开战图标6','032_少人提示','032_暂停','032_退出'};self.assertEqual(self.e['RunCellFirstBattle'](),1);self.assertEqual(self.taps,[(587,982,2000),(600,900,2000),(289,910,200),(600,900,200)])
 def test_cell_result_wait_before_tap(self):
  self.visible={'032_结果一'};self.after=lambda *a:self.visible.add('032_奇遇界面一');self.assertEqual(self.e['ReturnCellEncounter'](),1);self.assertEqual(self.taps,[(600,900,0)]);self.assertEqual(self.now,2100)
 def test_cell_ended_close_is_not_business_terminal(self):
  self.e['cellEncounterEnded']=True;self.visible={'032_关闭二'};self.assertEqual(self.e['ReturnCellWorldBoss'](),1);self.assertFalse(self.e['terminalConfirmed'])
 def test_cell_active_close_waits_for_boss(self):
  self.e['cellEncounterEnded']=False;self.visible={'032_关闭其他一'};self.after=lambda *a:self.visible.add('032_首领界面二');self.assertEqual(self.e['ReturnCellWorldBoss'](),1);self.assertEqual(self.taps,[(600,900,50)])
 def test_foreground_interruption_never_clicks(self):
  self.interrupt=True;self.visible={'070_灰领一'};self.assertEqual(self.e['FinishBossRewards']('070_'),4);self.assertFalse(self.taps)
 def test_full70_terminal_only_after_rewards(self):
  for fn in ['EnterEnemyHall','EnterBossPage','BuyWorldBossAttempts','SweepWorldBoss']:self.e[fn]=lambda *a:1
  self.visible={'070_无奖一'};self.assertEqual(self.e['ExecuteWorldBoss'](),1);self.assertTrue(self.e['terminalConfirmed']);self.assertTrue(self.e['worldTerminal']);self.assertEqual(self.e['worldCount'],0)
 def test_full32_ended_path_does_not_start_battle(self):
  self.e['currentTask']=32;self.e['EnterEnemyHall']=lambda:1;self.e['EnterBossPage']=lambda *a:1;self.e['cellEncounterEnded']=True;self.e['EnterCellEncounter']=lambda:1;self.e['ReturnCellWorldBoss']=lambda:1;self.e['RunCellFirstBattle']=lambda:self.fail('must skip ended battle');self.visible={'032_无奖一'};self.assertEqual(self.e['ExecuteCellBoss'](),1);self.assertTrue(self.e['terminalConfirmed']);self.assertTrue(self.e['cellTerminal']);self.assertEqual(self.e['cellCount'],0)
 def public(self):
  load(['common/任务状态.mq','common/任务注册.mq','common/任务分派.mq','common/任务调度.mq'],self.e);self.e['RegisterTasks']();self.e['NewSession']()
 def test_commit_hall_false_blocks_both(self):
  self.public()
  for task in [70,32]:
   self.e.update(currentTask=task,terminalConfirmed=True);self.assertFalse(self.e['CommitTask'](False));self.assertEqual(self.e['worldCount'],0);self.assertEqual(self.e['cellCount'],0)
 def test_public_serial70_then32_after_hall_commit(self):
  self.at(21,30);self.public();self.e.update(worldEnabled=True,cellEnabled=True,EnsureGameHall=lambda:1,ReturnToHall=lambda:1,mailEnabled=False,rewardEnabled=False,signEnabled=False,monthEnabled=False,friendEnabled=False,qfriendEnabled=False,wukongEnabled=False,coopEnabled=False);seen=[]
  def dispatch(t):seen.append(t);self.e['terminalConfirmed']=True;return 1
  self.e['DispatchTask']=dispatch;self.e['SchedulerStep']();self.e['SchedulerStep']();self.assertEqual(seen,[70,32]);self.assertEqual(self.e['worldCount'],1);self.assertEqual(self.e['cellCount'],1);self.assertEqual(sum('CommitTask(True) 返回=true' in s for s in self.logs),2)
 def test_resume_both_before_time_gate_even_disabled(self):
  self.public()
  for task in [70,32]:
   self.e.update(currentTask=task,worldEnabled=False,cellEnabled=False);self.e['SaveRecovery']();self.assertEqual(self.e['SelectDueTask'](),task)
 def test_business_failure_or_hall_failure_saves_original(self):
  for task in [70,32]:
   for businessOK,hallOK in [(False,True),(True,False)]:
    self.setUp();self.public();self.e.update(resumeTask=task,EnsureGameHall=lambda:1,ReturnToHall=lambda:1 if hallOK else 4);restarts=[]
    def dispatch(t):self.e['terminalConfirmed']=businessOK;return 1 if businessOK else 4
    self.e.update(DispatchTask=dispatch,RestartGame=lambda:restarts.append(self.e['resumeTask']));self.e['SchedulerStep']();self.assertEqual(restarts,[task]);self.assertEqual(self.e['worldCount'],0);self.assertEqual(self.e['cellCount'],0)
 def test_existing_business_bytes_unchanged(self):
  base=json.loads((ROOT/'flows/070_世界首领/evidence/修改前基线.json').read_text('utf-8'))
  for rel,h in base.items():
   if rel.startswith('flows/') or rel in ['common/悟空冒险状态.mq','common/合作冒险状态.mq']:self.assertEqual(hashlib.sha256((ROOT/rel).read_bytes()).hexdigest(),h,rel)
 def test_append_only_catalog_and_ui_layout(self):
  e=ROOT/'flows/070_世界首领/evidence';old=json.loads((e/'before/evidence/图色参数.txt').read_text('utf-8'));cat=[x for x in json.loads((ROOT/'evidence/图色参数.json').read_text('utf-8')) if not x['name'].startswith(('092_','016_','015_','014_','013_','012_','150_','155_','154_','153_','081_','080_','082_','079_','078_','083_','084_','085_'))];self.assertEqual(cat[:len(old)],old);self.assertEqual(len(cat)-len(old),64);ui=(ROOT/'ui/最小配置.uip').read_text('utf-8-sig');self.assertLess(ui.index('日常功能:{'),ui.index('名称:"悟空冒险启用"'));self.assertLess(ui.index('名称:"合作冒险启用"'),ui.index('名称:"强敌一级分隔"'));self.assertIn('名称:"打沙鲁启用"',ui)

 def test_missed_night_after_midnight_waits_configured_time(self):
  self.at(22);self.e['worldDue']=self.stamp-3600;self.stamp=self.e['WorldDayStart'](self.stamp)+86400+3600;self.now=0;self.e['worldEnabled']=True;self.assertEqual(self.e['SelectWorldBoss'](),0);self.assertEqual(self.e['worldDue'],self.e['WorldDayStart'](self.stamp)+36000)
 def test_every_raw_profile_keeps_exact_color_offsets_direction(self):
  for folder in ['070_世界首领','032_世界首领沙鲁']:
   e=ROOT/'flows'/folder/'evidence';converted={x['name']:x['definition'] for x in json.loads((e/'图色转换.json').read_text('utf-8'))}
   for raw in json.loads((e/'原始图色.json').read_text('utf-8')):
    d=converted[raw['name']];self.assertEqual(d[:4],[0,0,719,1279]);self.assertEqual(d[4:],[raw['main'],raw['offsets'],raw['direction'],raw['similarity']])
 def test_public_contains_no_reward_claiming_logic(self):
  source=(ROOT/'common/强敌入口.mq').read_text('utf-8-sig');self.assertNotIn('Function FinishBossRewards',source);self.assertNotIn('Function EnterBossPage',source)

 def test_actual_foreground5sec_restores_both_new_ids(self):
  from test_foreground import Foreground
  for task in [70,32]:
   fg=Foreground();fg.setUp();fg.e.update(Time=lambda:1760000000,Int=math.floor,worldHour=10,worldMinute=0,worldBuyConfig=0)
   load(['common/世界首领状态.mq'],fg.e);fg.e['NewWorldBossSession']();fg.e['SaveCurrentTask'](task);fg.request();self.assertTrue(fg.e['HandleForegroundRecovery']());self.assertEqual(fg.e['resumeTask'],task);self.assertEqual(fg.e['SelectDueTask'](),task);pre='world' if task==70 else 'cell';self.assertEqual(fg.e[pre+'Restarts'],1);self.assertEqual(fg.e[pre+'Recoveries'],1);self.assertEqual(fg.e[pre+'Count'],0);self.assertEqual(fg.events,[('kill','game'),('run','game')])
 def test_interruption_during_rewards_blocks_terminal(self):
  self.visible={'070_领奖弹窗一'}
  def tap(x,y,w):self.taps.append((x,y,w));self.interrupt=True
  self.e['TouchPoint']=tap;self.assertEqual(self.e['FinishBossRewards']('070_'),4);self.assertEqual(len(self.taps),1);self.assertFalse(self.e['terminalConfirmed'])

 def test_terminal_before21_hall_after21_keeps_night_plan(self):
  self.at(21);self.e['worldFinishedAt']=self.stamp-1;self.e['CommitWorldBossTask'](70);self.assertEqual(self.e['worldDue'],self.e['WorldDayStart'](self.stamp)+75660)
