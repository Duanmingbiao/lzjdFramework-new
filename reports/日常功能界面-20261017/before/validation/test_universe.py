import json,re,unittest
from mq_subset import ROOT,load

class UniverseTests(unittest.TestCase):
 def setUp(self):
  from test_worldboss import WorldBossTests
  self.f=WorldBossTests();self.f.setUp();self.f.at(12);self.e=self.f.e
  def match(n):
   self.f.now+=10;v=self.f.match(n)
   if n=='079_胶囊快速挑战':self.e['foundY']=100
   return v
  self.e['MatchPattern']=match
  self.e.update(currentTask=79,universeEnabled=True,universeCapsule=False,universeFailureMode=1)
  load(['common/超宇宙状态.mq','flows/079_超宇宙战士/超宇宙战士.mq'],self.e)
  self.e['NewUniverseSession']()
 def test_immediate_and_disabled(self):
  self.assertEqual(self.e['SelectUniverse'](),79);self.e.update(universeEnabled=False,universeCapsule=True)
  self.assertEqual(self.e['SelectUniverse'](),0)
 def test_config_reads_exact_professional_keys(self):
  settings={'日常_超宇宙战士':'true','日常_超宇宙战士_胶囊任务':'1','设置_重要_开战失败':0}
  self.e['ReadUIConfig']=lambda k,d:settings.get(k,d);self.e['LoadUniverseSettings']()
  self.assertTrue(self.e['universeEnabled']);self.assertTrue(self.e['universeCapsule']);self.assertEqual(self.e['universeFailureMode'],0)
 def test_missing_config_defaults_off_and_restart(self):
  self.e['ReadUIConfig']=lambda k,d:d;self.e['LoadUniverseSettings']()
  self.assertFalse(self.e['universeEnabled']);self.assertFalse(self.e['universeCapsule']);self.assertEqual(self.e['universeFailureMode'],1)
 def test_unopened_wait200_no_click_terminal(self):
  self.f.visible={'079_未开启'};self.assertEqual(self.e['EnterUniverse'](),1)
  self.assertEqual(self.f.now,210);self.assertFalse(self.f.taps);self.assertTrue(self.e['terminalConfirmed']);self.assertEqual(self.e['universeCount'],0)
 def test_entry_click1000_and_three_map_variants(self):
  for name in ['079_地图一','079_地图二','079_地图三']:
   self.setUp();self.f.visible={'079_入口一',name}
   self.assertEqual(self.e['EnterUniverse'](),1);self.assertEqual(self.f.taps,[(600,900,1000)])
   self.assertFalse(self.e['terminalConfirmed'])
 def test_full_clear_wait_back_and_still_needs_map(self):
  self.f.visible={'079_全通关入口'}
  self.f.after=lambda *a:self.f.visible.clear() or self.f.visible.add('079_地图一')
  self.assertEqual(self.e['EnterUniverse'](),1);self.assertTrue(self.e['universeFullClear']);self.assertFalse(self.e['terminalConfirmed'])
  self.assertEqual(self.f.taps,[(150,50,300)])
 def test_unknown_entry_does_not_invent20sec_exit(self):
  self.assertEqual(self.e['EnterUniverse'](),4);self.assertGreaterEqual(self.f.now,120000);self.assertFalse(self.e['terminalConfirmed'])
 def test_three_exact_coordinate_tables(self):
  tables=[[(393,1070),(190,843),(383,779),(620,622),(441,491),(191,372)],[(506,967),(183,882),(374,741),(665,637),(454,598),(253,370)],[(388,1085),(180,869),(432,734),(639,645),(304,350)]]
  for layout,table in enumerate(tables,1):
   self.f.taps.clear()
   for index,point in enumerate(table,1):self.assertTrue(self.e['UniverseMapPoint'](layout,index))
   self.assertFalse(self.e['UniverseMapPoint'](layout,len(table)+1))
   self.assertEqual(self.f.taps,[(x,y,300) for x,y in table])
 def test_main15sec_only_phase_exit(self):
  self.assertEqual(self.e['RunUniverse'](),1);self.assertGreater(self.f.now,15000);self.assertFalse(self.e['terminalConfirmed'])
 def test_third_attempt_changes_button_order_and_sixth_exits(self):
  self.f.visible={'079_关卡详情一','079_挑战按钮一'}
  self.assertEqual(self.e['RunUniverse'](),1)
  self.assertEqual(self.f.taps,[(507,862,250)]*2+[(210,858,250),(507,862,250)]*4)
  self.assertFalse(self.e['terminalConfirmed'])
 def test_first_battle_six_missing_confirmations_then_back(self):
  self.f.visible={'152_开战图标6'}
  self.f.after=lambda x,y,w:setattr(self.f,'interrupt',True) if (x,y)==(128,1228) else None
  self.assertEqual(self.e['RunUniverse'](),4);self.assertEqual(self.f.taps,[(398,982,1000),(128,1228,1500)])
 def test_map_shared_point_counter_not_reset_on_layout_change(self):
  self.f.visible={'079_巡图一','079_巡图二','079_巡图三'}
  self.f.after=lambda *a:setattr(self.f,'interrupt',len(self.f.taps)>=3)
  self.e['RunUniverse']();self.assertEqual(self.f.taps,[(393,1070,300),(183,882,300),(432,734,300)])
 def test_postchallenge_return_requires_exact_page(self):
  self.f.visible={'079_返回界面二'};self.assertEqual(self.e['ReturnUniversePage'](False),1);self.assertFalse(self.e['terminalConfirmed'])
 def test_postchallenge_clear_and_close_order(self):
  self.f.visible={'079_获得一','079_全通关返回','079_关闭窗口','079_返回界面一'}
  self.assertEqual(self.e['ReturnUniversePage'](False),1);self.assertEqual(self.f.taps,[(600,900,50),(150,50,1000),(600,900,200)])
 def test_final_failure_click_before_page_no_terminal_alone(self):
  self.f.visible={'079_胶囊失败','079_返回界面一'}
  self.assertEqual(self.e['ReturnUniversePage'](True),1);self.assertEqual(self.f.taps,[(600,900,0)]);self.assertFalse(self.e['terminalConfirmed'])
 def test_capsule_initial_idle5000_not_completion(self):
  self.assertEqual(self.e['RunUniverseCapsule'](),1);self.assertGreater(self.f.now,5000);self.assertLess(self.f.now,5600);self.assertFalse(self.e['terminalConfirmed'])
 def test_capsule_fifth_quick_attempt_uses_fallback(self):
  self.f.visible={'079_胶囊快速挑战'};self.f.after=lambda *a:setattr(self.f,'interrupt',len(self.f.taps)>=5)
  self.e['RunUniverseCapsule']();self.assertEqual(self.f.taps,[(450,950,0)]*4+[(160,950,0)])
 def test_capsule_repeated_open_is_preserved(self):
  self.f.visible={'079_打开胶囊'};self.f.after=lambda *a:setattr(self.f,'interrupt',len(self.f.taps)>=2)
  self.e['RunUniverseCapsule']();self.assertEqual(self.f.taps,[(600,900,200)]*2)
 def test_capsule_target6_start_order_and_failure_mode(self):
  for mode,result in [(0,1),(1,4)]:
   self.setUp();self.e['universeFailureMode']=mode;self.f.visible={'079_胶囊快速挑战'}
   def after(*a):self.f.visible.clear();self.f.visible.add('152_开战图标6')
   self.f.after=after
   self.assertEqual(self.e['RunUniverseCapsule'](),result)
   self.assertEqual(self.f.taps,[(450,950,0)]+[(398,982,500),(587,982,500)]*11);self.assertFalse(self.e['terminalConfirmed'])
 def test_capsule_lack_exact_anchor_no_added_wait(self):
  self.f.visible={'079_阵容不足'};self.f.after=lambda *a:setattr(self.f,'interrupt',True)
  self.e['RunUniverseCapsule']();self.assertEqual(self.f.taps,[(600,900,0)])
 def test_capsule_failure_does_not_claim_win_or_commit(self):
  self.f.visible={'079_胶囊失败'};self.assertEqual(self.e['RunUniverseCapsule'](),1)
  self.assertIn('不是挑战成功',self.e['universeReason']);self.assertFalse(self.e['terminalConfirmed']);self.assertEqual(self.e['universeCount'],0)
 def test_skip_has50ms_without_gather3000ms_wait(self):
  self.f.visible={'078_跳过战斗'}
  def after(*a):self.f.visible.clear()
  self.f.after=after;self.e['RunUniverseCapsule']()
  self.assertEqual(self.f.taps,[(290,993,50)]);self.assertGreater(self.f.now,15000);self.assertLess(self.f.now,16000)
 def test_capsule_total180sec_with_long_public_limit(self):
  self.e['BusinessExpired']=lambda:self.f.now>=300000;self.f.visible={'079_胶囊入口'}
  self.assertEqual(self.e['RunUniverseCapsule'](),1);self.assertGreater(self.f.now,180000);self.assertFalse(self.e['terminalConfirmed'])
 def test_capsule_disabled_never_invoked_and_final_confirmation_required(self):
  self.e['EnterGatherHall']=lambda:1;self.e['EnterUniverse']=lambda:1;self.e['universeFullClear']=True
  self.e['RunUniverseCapsule']=lambda:self.fail('capsule is off')
  self.f.visible={'079_返回界面一'};self.assertEqual(self.e['ExecuteUniverse'](),1);self.assertTrue(self.e['terminalConfirmed'])
 def test_final_unknown_page_never_commits(self):
  self.e.update(EnterGatherHall=lambda:1,EnterUniverse=lambda:1,universeFullClear=True)
  self.assertEqual(self.e['ExecuteUniverse'](),4);self.assertFalse(self.e['terminalConfirmed'])
 def public(self):
  load(['common/任务状态.mq','common/任务注册.mq','common/任务调度.mq'],self.e)
  self.e['RegisterTasks']();self.e['NewSession']();self.e['SaveCurrentTask'](79)
 def test_public_terminal_and_hall_gates(self):
  self.public();self.assertFalse(self.e['CommitTask'](True));self.e['ConfirmUniverseTerminal']('本轮结束')
  self.assertFalse(self.e['CommitTask'](False));self.assertEqual(self.e['universeCount'],0)
  self.assertTrue(self.e['CommitTask'](True));self.assertEqual(self.e['universeCount'],1);self.assertTrue(self.e['universeDone']);self.assertEqual(self.e['SelectUniverse'](),0)
 def test_completed_latch_not_released_by_midnight_or_five_am(self):
  self.e['ConfirmUniverseTerminal']('本轮结束');self.e['CommitUniverseTask']()
  self.f.stamp+=86400;self.f.at(0,1);self.assertEqual(self.e['SelectUniverse'](),0)
  self.f.at(5,1);self.assertEqual(self.e['SelectUniverse'](),0)
  self.e['NewUniverseSession']();self.assertEqual(self.e['SelectUniverse'](),79)
 def test_resume_survives_disabled_and_schedule(self):
  self.public();self.e.update(universeEnabled=False,universeDue=self.e['Time']()+100000)
  self.assertEqual(self.e['SelectDueTask'](),79)
 def test_public_hall_failure_recovers79(self):
  self.public();restarts=[];self.e.update(EnsureGameHall=lambda:1,ReturnToHall=lambda:4,RestartGame=lambda:restarts.append(self.e['resumeTask']))
  def dispatch(t):self.e['ConfirmUniverseTerminal']('结束');return 1
  self.e['DispatchTask']=dispatch;self.e['SchedulerStep']()
  self.assertEqual(restarts,[79]);self.assertEqual(self.e['universeCount'],0)
 def test_interruption_not_terminal(self):
  self.f.interrupt=True;self.f.visible={'079_未开启'};self.assertEqual(self.e['EnterUniverse'](),4);self.assertFalse(self.e['terminalConfirmed'])
 def test_actual_shared_foreground_recovery_routes79(self):
  import math
  from test_foreground import Foreground
  fg=Foreground();fg.setUp();fg.e.update(Time=lambda:1760000000,CStr=str,universeCapsule=False,universeFailureMode=1)
  load(['common/超宇宙状态.mq'],fg.e)
  fg.e['WorldDayStart']=lambda n:math.floor((n+28800)/86400)*86400-28800
  fg.e['WorldLog']=fg.logs.append;fg.e['NewUniverseSession']();fg.e['SaveCurrentTask'](79);fg.request()
  self.assertTrue(fg.e['HandleForegroundRecovery']());self.assertEqual(fg.e['resumeTask'],79);self.assertEqual(fg.e['SelectDueTask'](),79)
  self.assertEqual((fg.e['universeRestarts'],fg.e['universeRecoveries'],fg.e['universeCount']),(1,1,0))
  self.assertEqual(fg.events,[('kill','game'),('run','game')])
 def test_no_new_version_specific_or_cross_boundary_apis(self):
  text=(ROOT/'flows/079_超宇宙战士/超宇宙战士.mq').read_text('utf-8-sig')
  self.assertNotRegex(text,r'OcrEx|paddle|Image\.Ocr|KillApp|RunApp|CommitTask|SchedulerStep|InStr')
 def test_log_stage_attributed_only79(self):
  before=self.e['worldPhase'];self.e['WorldStage']('胶囊阶段')
  self.assertEqual(self.e['worldPhase'],before);self.assertEqual(self.e['universePhase'],'胶囊阶段');self.assertIn('超宇宙战士79',self.f.logs[-1])
 def test_professional_ui_choices_and_order(self):
  t=(ROOT/'ui/最小配置.uip').read_text('utf-8-sig')
  self.assertIn('名称:"日常_超宇宙战士",提示内容:"超宇宙战士[",选中:false',t)
  self.assertIn('名称:"日常_超宇宙战士_胶囊任务",提示内容:"胶囊任务]",选中:false',t)
  self.assertIn('名称:"设置_重要_开战失败",选项:["结束任务","重启任务",],初始选项:1',t)
  self.assertLess(t.index('异时空冒险:{'),t.index('名称:"日常_超宇宙战士"'))
 def test_exact_professional_recognition_rows(self):
  ev=ROOT/'flows/079_超宇宙战士/evidence'
  rows=json.loads((ev/'图色唯一参数.json').read_text('utf8'));records=json.loads((ev/'图色转换.json').read_text('utf8'))
  self.assertEqual(len(rows),28);self.assertEqual([x['definition'] for x in records[:28]],rows)
  catalog=json.loads((ROOT/'evidence/图色参数.json').read_text('utf8'));self.assertEqual([x for x in catalog if x['name'].startswith('079_')],records)
  source=(ROOT/'common/图色参数.mq').read_text('utf-8-sig')
  for x in records:
   body=re.search(r'Case "'+x['name']+r'"(.*?)(?=\n    Case |\n    End Select)',source,re.S)[1]
   self.assertIn('FindMultiColor '+', '.join(json.dumps(v) for v in x['definition'])+', foundX, foundY',body)
  self.assertEqual(rows[0][-1],.95);self.assertEqual(rows[16][:4],[0,0,719,1215]);self.assertEqual(rows[7][-2],0)

if __name__=='__main__':unittest.main()
