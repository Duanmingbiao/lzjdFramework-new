import json,re,unittest
from mq_subset import ROOT,load

class GatherTests(unittest.TestCase):
 def setUp(self):
  from test_worldboss import WorldBossTests
  self.f=WorldBossTests();self.f.setUp();self.f.at(12);self.e=self.f.e
  def match(n):self.f.now+=10;return self.f.match(n)
  self.e['MatchPattern']=match
  self.e.update(currentTask=78,gatherEnabled=True,gatherDouble=False,gatherSweep=False)
  load(['common/战士集结状态.mq','flows/078_战士集结/战士集结.mq'],self.e)
  self.e['NewGatherSession']()
 def test_immediate_and_disabled(self):
  self.assertEqual(self.e['SelectGather'](),78)
  self.e['gatherEnabled']=False;self.assertEqual(self.e['SelectGather'](),0)
 def test_daytime_normal_and_timeout_schedules(self):
  day=self.e['WorldDayStart'](self.e['Time']())
  self.e['CommitGatherTask']();self.assertEqual(self.e['gatherDue'],day+72000)
  self.e['gatherEntryTimeout']=True;self.e['CommitGatherTask']();self.assertEqual(self.e['gatherDue'],day+72300)
 def test_ended_and_evening_nextday(self):
  day=self.e['WorldDayStart'](self.e['Time']())
  self.e['gatherPeriodEnded']=True;self.e['CommitGatherTask']();self.assertEqual(self.e['gatherDue'],day+86400)
  self.f.at(20);self.e['gatherPeriodEnded']=False;self.e['CommitGatherTask']();self.assertEqual(self.e['gatherDue'],day+86400)
 def test_entry_explicit_period_end(self):
  self.f.visible={'078_本期结束'}
  self.assertEqual(self.e['EnterGather'](),1);self.assertTrue(self.e['gatherPeriodEnded']);self.assertTrue(self.e['terminalConfirmed']);self.assertEqual(self.e['gatherCount'],0)
 def test_native_entry20sec_exit_not_attempt_exhaustion(self):
  self.assertEqual(self.e['EnterGather'](),1);self.assertTrue(self.e['gatherEntryTimeout']);self.assertGreater(self.f.now,20000)
 def test_public_interruption_never_marks_terminal(self):
  self.f.interrupt=True;self.f.visible={'078_本期结束'}
  self.assertEqual(self.e['EnterGather'](),4);self.assertFalse(self.e['terminalConfirmed'])
 def test_start_collect_exact_offset_and_delay(self):
  self.f.visible={'078_开始收集'}
  self.f.after=lambda *a:self.f.visible.clear() or self.f.visible.add('078_收集界面')
  self.assertEqual(self.e['EnterGather'](),1);self.assertEqual(self.f.taps,[(851,637,300)]);self.assertFalse(self.e['terminalConfirmed'])
 def test_new_challenge_double_order(self):
  self.e['gatherDouble']=True;self.f.visible={'078_新关卡','078_关卡详情'}
  def after(x,y,w):
   if len(self.f.taps)==4:self.f.interrupt=True
  self.f.after=after
  self.assertEqual(self.e['RunGather'](),4)
  self.assertEqual(self.f.taps,[(600,900,300),(314,1526,0),(479,1458,200),(600,900,1000)])
 def test_target6_fixed_start_order(self):
  self.f.visible={'152_开战图标6'}
  self.f.after=lambda *a:setattr(self.f,'interrupt',len(self.f.taps)>=2)
  self.assertEqual(self.e['RunGather'](),4);self.assertEqual(self.f.taps,[(587,982,500),(398,982,500)])
 def test_skip_offset(self):
  self.f.visible={'078_跳过战斗'};self.f.after=lambda *a:setattr(self.f,'interrupt',True)
  self.assertEqual(self.e['RunGather'](),4);self.assertEqual(self.f.taps,[(290,993,50)])
 def test_no_progress_needs_collect_page(self):
  self.assertEqual(self.e['RunGather'](),4);self.assertFalse(self.e['terminalConfirmed'])
 def test_collect_no_progress_only_phase_exit(self):
  self.f.visible={'078_收集界面'};self.assertEqual(self.e['RunGather'](),1);self.assertFalse(self.e['terminalConfirmed'])
 def test_seven_slot_cycle_and_confirm(self):
  self.f.visible={'078_收集界面'}
  self.assertEqual(self.e['FinishGather'](),1)
  self.assertEqual([x for x,y,w in self.f.taps[:8]],[702,770,846,916,963,1033,1113,702])
  self.assertTrue(self.e['terminalConfirmed']);self.assertEqual(self.e['gatherCount'],0)
 def test_finish_unknown_page_never_terminal(self):
  self.assertEqual(self.e['FinishGather'](),4);self.assertFalse(self.e['terminalConfirmed'])
 def test_recovery_preserves_schedule_and_count(self):
  due=self.e['gatherDue'];self.e['RecoverGatherTask']();self.e['RestartGatherTask']()
  self.assertEqual(self.e['gatherDue'],due);self.assertEqual(self.e['gatherCount'],0);self.assertEqual(self.e['gatherRecoveries'],1);self.assertEqual(self.e['gatherRestarts'],1)
 def test_no_new_ocr_or_fuzzy_recognition(self):
  source=(ROOT/'flows/078_战士集结/战士集结.mq').read_text('utf-8-sig')
  self.assertNotRegex(source,r'Ocr|OCR|InStr|KillApp|RunApp|CommitTask')
  data=json.loads((ROOT/'evidence/图色参数.json').read_text('utf8'))
  rows=[x for x in data if x['name'].startswith('078_')];self.assertEqual(len(rows),21)
  self.assertEqual(next(x['definition'][-1] for x in rows if x['name']=='078_关卡对话'),1)
  self.assertEqual(next(x['definition'][-2] for x in rows if x['name']=='078_老关卡'),0)
 def test_foreground_and_resume_wiring(self):
  self.assertIn('currentTask = 78 Or',(ROOT/'common/前台监控.mq').read_text('utf-8-sig'))
  self.assertIn('If resumeTask = 78 Then',(ROOT/'common/任务注册.mq').read_text('utf-8-sig'))
 def public(self):
  load(['common/任务状态.mq','common/任务注册.mq','common/任务调度.mq'],self.e)
  self.e['RegisterTasks']();self.e['NewSession']();self.e['SaveCurrentTask'](78)
 def test_public_commit_needs_terminal_and_hall(self):
  self.public();self.assertFalse(self.e['CommitTask'](True))
  self.e['ConfirmGatherTerminal']('七位置确认');self.assertFalse(self.e['CommitTask'](False))
  self.assertEqual(self.e['gatherCount'],0);self.assertTrue(self.e['CommitTask'](True));self.assertEqual(self.e['gatherCount'],1)
  self.assertFalse(self.e['CommitTask'](True));self.assertEqual(self.e['gatherCount'],1)
 def test_public_hall_fail_retains78(self):
  self.public();restarts=[]
  self.e.update(EnsureGameHall=lambda:1,ReturnToHall=lambda:4,RestartGame=lambda:restarts.append(self.e['resumeTask']))
  def dispatch(t):self.e['ConfirmGatherTerminal']('本轮出口');return 1
  self.e['DispatchTask']=dispatch;self.e['SchedulerStep']()
  self.assertEqual(restarts,[78]);self.assertEqual(self.e['resumeTask'],78);self.assertEqual(self.e['gatherCount'],0)
 def test_resume_ignores_disabled_and_future_due(self):
  self.public();self.e.update(gatherEnabled=False,gatherDue=self.e['Time']()+100000)
  self.assertEqual(self.e['SelectDueTask'](),78)
 def test_finish_time_frozen_across_hall20_boundary(self):
  self.f.at(19,59);self.e['ConfirmGatherTerminal']('正常结束');self.f.at(20,1)
  self.e['CommitGatherTask']();self.assertEqual(self.e['gatherDue'],self.e['WorldDayStart'](self.e['Time']())+72000)
 def test_all_three_menu_confirmation_variants(self):
  for variant in ['一','二','三']:
   self.f.visible={'078_异时空页面'+variant};self.assertEqual(self.e['EnterGatherHall'](),1)
 def test_old_sweep_requires_switch_and_y_less350(self):
  for enabled,y,expected in [(False,349,False),(True,350,False),(True,349,True)]:
   self.setUp();self.e['gatherSweep']=enabled;self.f.visible={'078_老关卡','078_关卡详情','078_收集界面'}
   def match(n):
    self.f.now+=10;v=self.f.match(n)
    if n=='078_老关卡':self.e['foundY']=y
    return v
   self.e['MatchPattern']=match
   def after(x,yy,w):
    if x==148:self.f.interrupt=True
   self.f.after=after
   self.e['RunGather']()
   self.assertEqual(any(x==148 for x,yy,w in self.f.taps),expected)
 def test_exact_root622_recognition_rows(self):
  s=(ROOT/'flows/078_战士集结/evidence/root622静态重建.txt').read_text('utf8')
  assign=r'L\d+_1 = (\d+)\n\s*'
  pattern=assign*4+r'L\d+_1 = "([0-9A-F]{6}(?:-[0-9A-F]{6})?)"\n\s+L\d+_1 = "([0-9|,A-Fa-f-]+)"\n\s+L\d+_1 = ([01])\n\s+L\d+_1 = ([^\n]+)'
  rows=[]
  for m in re.finditer(pattern,s):
   row=[int(m[i]) for i in range(1,5)]+[m[5],m[6],int(m[7]),1 if m[8]=='1' else .9]
   if row[:4]==[0,0,0,0]:row[:4]=[0,0,719,1279]
   if row not in rows:rows.append(row)
  records=[x for x in json.loads((ROOT/'evidence/图色参数.json').read_text('utf8')) if x.get('source')=='root.622 retained prototype']
  self.assertEqual(len(rows),15);self.assertEqual([x['definition'] for x in records],rows)
  mq=(ROOT/'common/图色参数.mq').read_text('utf-8-sig')
  for x in records:
   body=re.search(r'Case "'+x['name']+r'"(.*?)(?=\n    Case |\n    End Select)',mq,re.S)[1]
   self.assertIn('FindMultiColor '+', '.join(json.dumps(v) for v in x['definition'])+', foundX, foundY',body)

if __name__=='__main__':unittest.main()
