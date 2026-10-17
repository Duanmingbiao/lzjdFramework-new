import unittest,json,re,math,hashlib
from mq_subset import ROOT,load
import test_worldboss
E=ROOT/'flows/155_蛇道/evidence'
KEYS=json.loads((E/'配置键.json').read_text('utf8'))

class SnakeTests(unittest.TestCase):
 def setUp(self):
  self.f=test_worldboss.WorldBossTests();self.f.setUp();self.e=self.f.e;self.swipes=[]
  def match(n):self.f.now+=10;return self.f.match(n)
  self.e.update(MatchPattern=match,currentTask=155,businessStarted=0,businessLimit=120000,ForegroundInterrupted=lambda:self.f.interrupt,ReadUIConfig=lambda k,d:d,Len=len,Mid=lambda s,p,n:s[p-1:p-1+n],InStr=lambda p,s,v:s.find(v,p-1)+1,Swipe=lambda *a:self.swipes.append(a))
  def numeric(v):
   if isinstance(v,bool) or v is None:return False
   try:float(v);return True
   except (ValueError,TypeError):return False
  self.e['IsNumeric']=numeric
  load(['common/蛇道状态.mq','flows/155_蛇道/蛇道.mq','common/运行计时.mq'],self.e)
  self.e['LoadSnakeSettings']();self.e['NewSnakeSession']()
 def test_all13_original_settings_defaults(self):
  seen=[];self.e['ReadUIConfig']=lambda k,d:seen.append(k) or d;self.e['LoadSnakeSettings']()
  self.assertEqual(set(seen),set(KEYS));self.assertFalse(self.e['snakeEnabled'])
  self.assertEqual([self.e[k] for k in ['snakeCatchup','snakeHour','snakeMinute','snakeMode','snakeAnimation','snakeHireRow','snakeHireColumn','snakeHireSlot','snakeEffect','snakeFailureLimit']],[1,9,10,0,1,0,0,5,0,3])
 def test_time_before_at_after(self):
  for h,m,want in [(9,9,0),(9,10,155),(22,0,155)]:
   self.f.at(h,m);self.e['NewSnakeSession']();self.e['snakeEnabled']=True;self.assertEqual(self.e['SelectSnake'](),want)
 def test_catchup_strict_window_and_once_even_unchecked(self):
  for seconds,want in [(1800,0),(1801,155),(17399,155),(17400,0)]:
   self.setUp();self.f.at(0);self.f.stamp+=seconds;self.e['NewSnakeSession']();self.e['snakeCatchup']=0
   self.assertEqual(self.e['SelectSnake'](),want)
   if want:
    self.assertEqual(self.e['snakeMode'],1);self.e['snakeDone']=True;self.assertEqual(self.e['SelectSnake'](),0)
 def test_default_difficulties15(self):
  self.assertEqual([self.e['SnakeDifficulty'](i) for i in range(1,16)],[2]*8+[1]*5+[0]*2)
 def test_csv_numeric_floor_overlap_ordinary_first(self):
  self.e.update(snakeOrdinary='2, 3.9,,bad',snakeHard='1,2,3,4')
  self.assertEqual([self.e['SnakeDifficulty'](i) for i in range(1,6)],[2,1,1,2,0]);self.assertFalse(self.e['SnakeListContains'](None,1))
 def test_ocr_original_rectangle_and_no_empty_hit(self):
  calls=[];self.e['WorldText']=lambda *a:calls.append(a) or None
  self.assertFalse(self.e['SnakeHireTextHit']());self.assertEqual(calls,[(82,545,648,637)])
  for raw,want in [('',False),('   ',False),('该战',False),('雇佣',True),('是否雇佣该战士',True),('该战士',True),('取消',False)]:
   self.e['WorldText']=lambda *a,v=raw:v;self.assertEqual(self.e['SnakeHireTextHit'](),want)
 def test_ocr_only_after_original_hire_confirmation_pattern(self):
  self.e['snakeHireRow']=1;self.f.visible={'155_P05'}
  self.f.text='';self.assertEqual(self.e['HireSnakeWarrior'](),1);self.assertFalse(self.f.taps)
 def test_hire_keyword_original_two_fixed_clicks(self):
  self.e['snakeHireRow']=1;self.f.visible={'155_P05'};self.f.text='雇佣该战士'
  self.assertEqual(self.e['HireSnakeWarrior'](),1);self.assertEqual(self.f.taps,[(517,758,200),(517,758,500)])
 def test_hire_disabled_no_recognition_or_click(self):
  self.assertEqual(self.e['HireSnakeWarrior'](),1);self.assertFalse(self.f.lookups);self.assertFalse(self.f.taps)
 def test_hire_already_hired_no_confirmation(self):
  self.e['snakeHireRow']=1;self.f.visible={'155_P04','155_P05'};self.f.text='雇佣'
  self.assertEqual(self.e['HireSnakeWarrior'](),1);self.assertFalse(self.f.taps)
 def test_hire90sec_unknown_only_phase_exit(self):
  self.e['snakeHireRow']=1;self.assertEqual(self.e['HireSnakeWarrior'](),1)
  self.assertGreaterEqual(self.f.now,90000);self.assertFalse(self.e['terminalConfirmed']);self.assertFalse(self.f.taps)
 def test_hire9rows3columns_original_offsets_and_pages(self):
  for row in range(1,10):
   for column,dx in enumerate([44,249,450]):
    self.setUp();self.e.update(snakeHireRow=row,snakeHireColumn=column);self.f.visible={'155_P02'}
    self.f.after=lambda *a:setattr(self.f,'visible',{'155_P04'})
    self.assertEqual(self.e['HireSnakeWarrior'](),1)
    dy={1:-791,2:-539,0:-285}[row%3];self.assertEqual(self.f.taps,[(600+dx,900+dy,200),(600+dx,900+dy,300)])
    self.assertEqual(len(self.swipes),4*((row-1)//3));self.assertTrue(all(s[-1] in [400,200] for s in self.swipes))
 def test_sweep_confirmation_exact_three_clicks(self):
  self.f.visible={'155_P50'};self.f.after=lambda *a:setattr(self.f,'visible',{'155_P00'})
  self.assertTrue(self.e['SweepSnake']());self.assertEqual(self.f.taps,[(626,1216,300),(423,1538,300),(426,1760,1000)])
 def test_sweep_timeout_false_not_done(self):
  self.assertFalse(self.e['SweepSnake']());self.assertGreater(self.f.now,30000);self.assertFalse(self.e['terminalConfirmed'])
 def test_sweep_result_applies_mode_only_after_main_confirmed(self):
  for mode,want in [(0,5),(1,1),(2,5)]:
   self.setUp();self.e['snakeMode']=mode;self.f.visible={'155_P07'};self.e['SweepSnake']=lambda:True
   self.assertEqual(self.e['SnakeMapStep'](),want)
  self.e['SweepSnake']=lambda:False;self.assertEqual(self.e['SnakeMapStep'](),1)
 def test_floor15_patterns_click_reset_not_terminal(self):
  for floor in range(1,16):
   self.setUp();self.f.visible={f'155_P{floor+7:02d}'}
   self.assertEqual(self.e['SnakeMapStep'](),1);self.assertEqual(self.e['snakeFloor'],floor)
   self.assertEqual(self.f.taps,[(600,900,0)]);self.assertGreater(self.e['businessStarted'],0);self.assertFalse(self.e['terminalConfirmed'])
 def test_alternate_floor_does_not_invent_floor_number(self):
  self.e['snakeFloor']=7;self.f.visible={'155_P23'};self.assertEqual(self.e['SnakeMapStep'](),1)
  self.assertEqual(self.e['snakeFloor'],7);self.assertEqual(self.f.taps,[(600,870,0)])
 def test_special_prompt_three_original_anchor_clicks(self):
  self.f.visible={'155_P26'};self.assertEqual(self.e['SnakeMapStep'](),1)
  self.assertEqual(self.f.taps,[(979,525,1000),(1081,91,1000),(600,900,0)])
 def test_difficulty_and_fallback_offsets(self):
  for floor,dy in [(1,-225),(9,-528),(14,-820)]:
   self.setUp();self.e['snakeFloor']=floor;self.f.visible={'155_P32'};self.assertTrue(self.e['SnakeChooseDifficulty']());self.assertEqual(self.f.taps,[(840,900+dy,0)])
  for name,dy in [('155_P33',-820),('155_P34',-528),('155_P35',-225)]:
   self.setUp();self.f.visible={name};self.assertTrue(self.e['SnakeChooseDifficulty']());self.assertEqual(self.f.taps,[(840,900+dy,0)])
 def test_ready_watch_and_skip_do_not_mix(self):
  self.f.visible={'155_P41'};self.assertFalse(self.e['SnakeReady']());self.e['snakeAnimation']=0;self.assertTrue(self.e['SnakeReady']())
 def test_all7_formation_slots_and_duration100(self):
  for slot in range(7):
   self.setUp();self.e['snakeHireSlot']=slot;self.f.visible={'155_P42'};self.assertTrue(self.e['SnakeFormation']())
   if slot==6:self.assertFalse(self.swipes);self.assertFalse(self.f.taps)
   else:
    sx=[70,250,430][slot%3];sy=-620 if slot<3 else -415;tx,ty=(450,-180) if slot==0 else (250,-120)
    self.assertEqual(self.swipes,[(600+sx,900+sy,600+tx,900+ty,100)]);self.assertEqual(self.f.taps,[(569,799,500)])
 def test_failed_ready_never_uses_negative_anchor(self):
  self.assertFalse(self.e['SnakeFormation']());self.assertFalse(self.swipes);self.assertFalse(self.f.taps)
 def test_auto_triple_priority_and_offsets(self):
  for name,xy,want in [('155_P55',None,True),('155_P56',(290,1070),False),('155_P57',(918,992),False),('155_P54',(918,916),False)]:
   self.setUp();self.f.visible={name};self.assertEqual(self.e['SnakeAutoTriple'](),want);self.assertEqual(self.f.taps,[] if xy is None else [(*xy,50)])
 def test_battle_visible_original_skip(self):
  self.f.visible={'155_P54'};self.assertTrue(self.e['SnakeBattleVisible']());self.assertEqual(self.f.taps,[(290,993,50)])
 def test_one_stage_win_loss_and_failure_limit(self):
  for name in ['155_P38','155_P39']:
   self.setUp();self.e['snakeMode']=2;self.f.visible={name};self.e['FinishSnake']=lambda retry:('finish',retry)
   self.assertEqual(self.e['RunSnake'](),('finish',False));self.assertEqual(self.e['snakeFailures'],int(name.endswith('39')))
  self.setUp();self.e['snakeFailureLimit']=3;self.f.visible={'155_P39'};self.e['FinishSnake']=lambda retry:('finish',retry)
  self.assertEqual(self.e['RunSnake'](),('finish',False));self.assertEqual(self.e['snakeFailures'],3)
 def test_fullclear_cleanup_and_timeout_retry_marker(self):
  self.f.visible={'155_P28'};self.e['FinishSnake']=lambda retry:('finish',retry);self.assertEqual(self.e['RunSnake'](),('finish',False))
  self.setUp();self.e['snakeStarts']=6;self.e['FinishSnake']=lambda retry:('finish',retry);self.assertEqual(self.e['RunSnake'](),('finish',True))
 def test_native_finish20sec_requires_later_hall_commit(self):
  self.assertEqual(self.e['FinishSnake'](True),1);self.assertGreater(self.f.now,20500)
  self.assertTrue(self.e['terminalConfirmed']);self.assertEqual(self.e['snakeCount'],0);self.assertFalse(self.e['snakeDone'])
 def test_native_finish_main11_attempts_and_detail_exit(self):
  self.f.visible={'155_P00'};self.assertEqual(self.e['FinishSnake'](False),1);self.assertEqual(self.f.taps,[(1065,-79,500)]*11)
  self.setUp();self.f.visible={'155_P48'};self.assertEqual(self.e['FinishSnake'](False),1);self.assertEqual(self.f.taps,[(850,729,500)])
 def test_unknown_initial_page_not_done(self):
  self.e['EnterSnake']=lambda:1;self.assertEqual(self.e['ExecuteSnake'](),4);self.assertFalse(self.e['terminalConfirmed'])
 def test_early_fullclear_does_not_hire_or_fight(self):
  self.e['EnterSnake']=lambda:1;self.f.visible={'155_P01'};self.assertEqual(self.e['ExecuteSnake'](),1);self.assertFalse(self.f.taps)
 def test_public_commit_no_hall_no_count_retry1hour(self):
  load(['common/任务状态.mq','common/任务注册.mq'],self.e);self.e['SaveCurrentTask'](155)
  self.assertFalse(self.e['CommitTask'](True));self.e['ConfirmSnakeExit']('native retry',True);finished=self.e['snakeFinishedAt']
  self.assertFalse(self.e['CommitTask'](False));self.assertTrue(self.e['CommitTask'](True));self.assertFalse(self.e['snakeDone']);self.assertEqual(self.e['snakeDue'],finished+3600)
 def test_public_commit_normal_done(self):
  load(['common/任务状态.mq'],self.e);self.e['SaveCurrentTask'](155);self.e['ConfirmSnakeExit']('done',False)
  self.assertTrue(self.e['CommitTask'](True));self.assertTrue(self.e['snakeDone']);self.assertEqual(self.e['snakeCount'],1)
 def test_interruption_blocks_all_side_effects_and_completion(self):
  self.f.interrupt=True
  for name in ['EnterSnake','SweepSnake','SnakeFormation','ResetSnakeTimer','SnakeHireTextHit']:
   self.e[name]()
  self.assertEqual(self.e['ConfirmSnakeExit']('late',False),4);self.assertFalse(self.f.taps);self.assertFalse(self.swipes);self.assertFalse(self.e['terminalConfirmed'])
 def test_foreground_recovers_same_task_without_commit(self):
  import test_foreground
  fg=test_foreground.Foreground();fg.setUp();fg.e.update(Time=lambda:1760000000,WorldDayStart=lambda n:n-3600,CStr=str,WorldLog=fg.logs.append,WorldStage=lambda s:None,snakeHour=9,snakeMinute=10,snakeMode=0,snakeAnimation=1)
  load(['common/蛇道状态.mq'],fg.e);fg.e['NewSnakeSession']();fg.e['SaveCurrentTask'](155);fg.request()
  self.assertTrue(fg.e['HandleForegroundRecovery']());self.assertEqual(fg.e['SelectDueTask'](),155);self.assertEqual((fg.e['snakeCount'],fg.e['snakeRecoveries'],fg.e['snakeRestarts']),(0,1,1))
 def test_catalog_append_only_and_all_actual_definitions(self):
  records=json.loads((E/'图色转换.json').read_text('utf8'));before=json.loads((ROOT/'reports/蛇道接入-20261017/before/图色参数-安装前恢复用.json').read_text('utf8'));now=[r for r in json.loads((ROOT/'evidence/图色参数.json').read_text('utf8')) if not r['name'].startswith(('012_','150_'))]
  self.assertEqual(now,before+records);self.assertEqual(len(records),64)
  mq=(ROOT/'common/图色参数.mq').read_text('utf-8-sig')
  for r in records:
   args=', '.join(json.dumps(x) if isinstance(x,str) else str(x) for x in r['definition'])
   self.assertIn('Case "'+r['name']+'"\n        FindMultiColor '+args+', foundX, foundY',mq)
 def test_original_regions_not_widened_and_no_color_tolerance_added(self):
  by={x['name']:x['definition'] for x in json.loads((E/'图色转换.json').read_text('utf8'))}
  self.assertEqual(by['155_P05'][:4],[0,0,719,1215]);self.assertEqual(by['155_P05'][4],'0D36FF')
  self.assertEqual(by['155_P01'][:4],[0,0,719,1248]);self.assertEqual(by['155_P38'][:4],[35,115,703,926]);self.assertEqual(by['155_P45'][:4],[5,115,703,926]);self.assertEqual(by['155_P54'][:4],[0,0,719,205])
 def test_all_named_patterns_exist_and_original15_floors(self):
  names={r['name'] for r in json.loads((E/'图色转换.json').read_text('utf8'))};flow=(ROOT/'flows/155_蛇道/蛇道.mq').read_text('utf-8-sig')
  self.assertTrue(set(re.findall('WorldMatch\\("([^"]+)"\\)',flow))<=names)
  self.assertEqual(sorted(map(int,re.findall(r'snakeFloor = (\d+)',flow))),[1]+list(range(1,16)))
 def test_original_ui13_no_changes_to_previous_controls(self):
  def controls(t):return {re.search('名称:"([^"]+)"',body)[1]:(kind,body) for kind,body in re.findall(r'(输入框|下拉框|多选框):\{([^{}]+)\}',t)}
  before=controls((ROOT/'reports/蛇道接入-20261017/before/ui/最小配置.uip').read_text('utf-8-sig'));after={k:v for k,v in controls((ROOT/'ui/最小配置.uip').read_text('utf-8-sig')).items() if k not in ['SlJb','Lzdmx','Lzdmx许愿']};original=controls((E/'原界面配置.uip.txt').read_text('utf8'))
  self.assertEqual({k:after[k] for k in before},before);self.assertEqual(set(after)-set(before),set(KEYS));self.assertEqual({k:after[k] for k in KEYS},original)
  self.assertTrue(all('选中:false' in body for kind,body in after.values() if kind=='多选框'))
 def test_only_registered_once_no_new_engine_or_external_actions(self):
  cfg=json.loads((ROOT/'project.json').read_text('utf8'));self.assertEqual(cfg['registeredTasks'].count(155),1)
  flow=(ROOT/'flows/155_蛇道/蛇道.mq').read_text('utf-8-sig');self.assertNotRegex(flow,r'OcrEx|paddle|KillApp|RunApp|CommitTask|SchedulerStep|businessStarted\s*=')
  self.assertNotRegex(flow,r'If snakeEffect|snakeEffect =')
 def test_raw_find2_call_rectangles_colors_direction_similarity(self):
  by={r['name']:r['definition'] for r in json.loads((E/'图色转换.json').read_text('utf8'))}
  calls=json.loads((E/'调用位置.json').read_text('utf8'));self.assertEqual(len(calls),98)
  for call in calls:
   source=call['source'];filename='root787蛇道分支.txt' if source=='root.787蛇道' else source.replace('.','')+'静态重建.txt'
   lines=(E/filename).read_text('utf8').splitlines();i=call['line']-1
   region=[int(re.search(r'= (\d+)$',x)[1]) for x in lines[i-4:i]]
   if region==[0,0,0,0]:region=[0,0,719,1279]
   else:region[2]=min(region[2],719);region[3]=min(region[3],1279)
   literal=lambda line:re.search(r'= "(.*)"$',line)[1]
   self.assertEqual(by[call['name']][:6],region+[literal(lines[i]),literal(lines[i+1])])
   self.assertEqual(by[call['name']][6:], [1,0.9])
 def test_native_10minute_no_progress_strict_boundary_if_public_limit_allows(self):
  self.e['businessLimit']=900000
  self.e['FinishSnake']=lambda retry:('finish',retry)
  self.assertEqual(self.e['RunSnake'](),('finish',True));self.assertGreater(self.f.now,600000);self.assertLess(self.f.now,601000)
 def test_unknown_entry60seconds_and_no_blind_taps(self):
  self.e['ReturnToHall']=lambda:1
  self.assertEqual(self.e['EnterSnake'](),4);self.assertFalse(self.e['terminalConfirmed']);self.assertFalse(self.f.taps);self.assertGreater(self.f.now,62000)
 def test_phase_restored_after_sweep_and_start(self):
  phases=[];self.e['WorldStage']=phases.append;self.f.visible={'155_P07','155_P28'};self.e['SweepSnake']=lambda:phases.append('蛇道扫荡') or False
  self.e['FinishSnake']=lambda retry:1;self.assertEqual(self.e['RunSnake'](),1)
  self.assertEqual(phases[-2:],['蛇道扫荡','蛇道逐关挑战'])
 def test_sweep_extra_chests_original_clicks(self):
  for name,dx,dy,wait in [('155_P49',252,-347,500),('155_P51',-174,860,50),('155_P52',-174,860,50),('155_P53',-35,531,50)]:
   self.setUp();self.f.visible={name};self.f.after=lambda *a:setattr(self.f,'visible',{'155_P00'})
   self.assertTrue(self.e['SweepSnake']());self.assertEqual(self.f.taps,[(600+dx,900+dy,wait)])
 def test_battle_confirm_formation_then_start_and_battle(self):
  self.f.visible={'155_P43','155_P42'};self.e['snakeHireSlot']=6
  def after(x,y,w):
   if (x,y)==(587,982):self.f.visible={'155_P54'}
  self.f.after=after;self.assertEqual(self.e['StartSnakeBattle'](),1)
  self.assertEqual(self.f.taps,[(398,982,0),(587,982,500),(290,993,50)]);self.assertEqual(self.e['snakeStarts'],0)
 def test_battle_unrecognized15sec_is_not_completion(self):
  self.assertEqual(self.e['StartSnakeBattle'](),1);self.assertGreater(self.f.now,17500);self.assertFalse(self.e['terminalConfirmed']);self.assertFalse(self.f.taps)
 def test_unknown_run_public_timeout_never_commits(self):
  self.assertEqual(self.e['RunSnake'](),4);self.assertFalse(self.e['terminalConfirmed']);self.assertFalse(self.f.taps)

if __name__=='__main__':unittest.main()
