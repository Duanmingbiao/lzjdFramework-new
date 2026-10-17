import unittest,json,re
from mq_subset import ROOT,load
import test_worldboss
E=ROOT/'flows/014_龙魂试炼/evidence'
class SoulTests(unittest.TestCase):
 def setUp(self):
  self.f=test_worldboss.WorldBossTests();self.f.setUp();self.e=self.f.e;self.swipes=[];self.ocr=[]
  def match(n):self.f.now+=10;return self.f.match(n)
  def ocr(*a):self.ocr.append(a);return self.f.text
  self.e.update(MatchPattern=match,currentTask=14,businessStarted=0,businessLimit=120000,ForegroundInterrupted=lambda:self.f.interrupt,ReadUIConfig=lambda k,d:d,Replace=lambda s,a,b:s.replace(a,b),Chr=chr,InStr=lambda start,s,x:s.find(x,start-1)+1,Swipe=lambda *a:self.swipes.append(a))
  self.e['Image'].OcrText=ocr
  load(['common/龙魂试炼状态.mq','flows/014_龙魂试炼/龙魂试炼.mq','common/运行计时.mq'],self.e)
  self.e['LoadSoulSettings']();self.e['NewSoulSession']()
 def test_original_single_checkbox_default_disabled(self):
  keys=[];self.e['ReadUIConfig']=lambda k,d:keys.append(k) or d;self.e['LoadSoulSettings']();self.assertEqual(keys,['SlLh']);self.assertFalse(self.e['soulEnabled'])
 def test_enabled_immediate_due_and_five_limit(self):
  self.assertEqual(self.e['SelectSoul'](),0);self.e['soulEnabled']=True;self.assertEqual(self.e['SelectSoul'](),14)
  for key in ['soulDone','soulAbandoned']:
   self.e[key]=True;self.assertEqual(self.e['SelectSoul'](),0);self.e[key]=False
  self.e['soulDue']=self.e['Time']()+65;self.assertEqual(self.e['SelectSoul'](),0);self.f.stamp+=65;self.assertEqual(self.e['SelectSoul'](),14)
 def test_eight_exact_exhausted_tokens(self):
  for s in ['02','03','04','05','012','013','014','015']:self.assertTrue(self.e['SoulCountExhausted'](s))
  for s in ['',None,'0','00','06','错误02','02x','102','0/2']:self.assertFalse(self.e['SoulCountExhausted'](s))
 def test_old_ocr_conservative_separators_not_fuzzy_digits(self):
  for s,w in [(None,''),('0/2','02'),('0 | 12\r\n\t','012'),('错误0/2','错误02')]:self.assertEqual(self.e['SoulFilterText'](s),w)
 def test_exhausted_original_anchor_region_no_click_pending_only(self):
  self.f.visible={'014_P02'};self.f.text='0/2';self.assertEqual(self.e['RunSoulTrial'](),1)
  self.assertEqual(self.ocr,[(485,1008,538,1034,0,0)]);self.assertFalse(self.f.taps);self.assertTrue(self.e['terminalConfirmed']);self.assertFalse(self.e['soulDone']);self.assertEqual(self.e['soulCount'],0)
 def test_cooldown_contains00_not_counted(self):
  self.f.visible={'014_P02'};self.f.text='00:10';self.assertEqual(self.e['RunSoulTrial'](),1);self.assertEqual(self.e['soulExitKind'],2)
  self.e['CommitSoulTask']();self.assertEqual(self.e['soulDue'],self.e['soulFinishedAt']+65);self.assertEqual(self.e['soulCount'],0);self.assertFalse(self.e['soulDone'])
 def test_empty_unknown_count_never_exhausted_or_success(self):
  for s in ['',None,'错误02']:
   self.setUp();self.f.visible={'014_P02'};self.f.text=s;self.assertEqual(self.e['RunSoulTrial'](),4);self.assertFalse(self.e['terminalConfirmed']);self.assertFalse(self.e['soulDone']);self.assertFalse(self.e['soulNativeTimeout'])
 def test_no_count_anchor_public_timeout_no_native_failure(self):
  self.assertEqual(self.e['RunSoulTrial'](),4);self.assertFalse(self.e['soulNativeTimeout']);self.assertEqual(self.e['soulCount'],0);self.assertFalse(self.f.taps)
 def test_location_two_original_patterns_no_touch(self):
  for name in ['014_P33','014_P34']:
   self.setUp();self.f.visible={name};self.assertEqual(self.e['EnterSoulTrial'](),1);self.assertFalse(self.f.taps);self.assertFalse(self.swipes)
 def test_known_location_first_hit_preserves_anchor(self):
  self.f.visible={'014_P33'};self.assertTrue(self.e['SoulTrialKnown']());self.assertEqual(self.f.lookups,['014_P33'])
 def test_hall_icon_original_click1500(self):
  for icon in ['014_P28','014_P29']:
   self.setUp();self.e['ReturnToHall']=lambda:1;self.f.visible={'014_P30',icon};self.f.after=lambda *a:setattr(self.f,'visible',{'014_P33'})
   self.assertEqual(self.e['EnterSoulTrial'](),1);self.assertEqual(self.f.taps,[(600,900,1500)])
 def test_missing_trial_icon_original_slide_left(self):
  self.e['ReturnToHall']=lambda:1;self.f.visible={'014_P30'}
  def swipe(*a):self.swipes.append(a);self.f.visible={'014_P33'}
  self.e['Swipe']=swipe;self.assertEqual(self.e['EnterSoulTrial'](),1);self.assertEqual(self.swipes,[(150,545,500,545,300)])
 def test_entry_unknown60seconds_no_blind_click(self):
  self.e['ReturnToHall']=lambda:1;self.assertEqual(self.e['EnterSoulTrial'](),4);self.assertGreater(self.f.now,63000);self.assertFalse(self.f.taps);self.assertFalse(self.swipes);self.assertFalse(self.e['terminalConfirmed'])
 def test_return_hall_failure_stops_entry(self):
  self.e['ReturnToHall']=lambda:4;self.assertEqual(self.e['EnterSoulTrial'](),4);self.assertFalse(self.f.taps);self.assertFalse(self.swipes)
 def test_soul_initial_ocr_missing_does_not_click_or_scroll(self):
  self.f.visible={'014_P02','014_P14'};self.f.text='';self.assertEqual(self.e['RunSoulTrial'](),4);self.assertFalse(self.f.taps);self.assertFalse(self.swipes);self.assertFalse(self.e['terminalConfirmed'])
 def test_first_match_sweep_entry_result_short_circuit(self):
  for fn,name in [('SoulSweepReady','014_P12'),('SoulEntryIcon','014_P02'),('SoulSweepResult','014_P26')]:
   self.setUp();self.f.visible={name};self.assertTrue(self.e[fn]());self.assertEqual(self.f.lookups,[name])
 def test_autotriple_original_priorities_offsets(self):
  for n,tap in [('014_AutoReady',None),('014_AutoOff',(290,1070,50)),('014_TripleOff',(918,992,50)),('014_BattleBase',(918,916,50))]:
   self.setUp();self.f.visible={n};self.assertEqual(self.e['SoulAutoTriple'](),tap is None);self.assertEqual(self.f.taps,[] if tap is None else [tap])
 def battle(self,pattern,after=None):
  self.f.visible={'014_P02','014_P14'};self.f.text='1/2'
  def nextpage(x,y,w):
   if len(self.f.taps)==1:self.f.visible={'014_P14',pattern}
   elif (x,y)==(780,648):self.f.visible={pattern}
   elif after:after(x,y,w)
  self.f.after=nextpage
  return self.e['RunSoulTrial']()
 def test_challenge_original_offset_and_failure_countable_exit(self):
  self.assertEqual(self.battle('014_P25'),1);self.assertEqual(self.f.taps,[(600,900,50),(780,648,500),(600,900,0)]);self.assertEqual(self.e['soulReason'],'原战斗失败退出');self.assertEqual(self.e['soulCount'],0)
 def test_two_victory_original_clicks_require_exact_title(self):
  for name,point in [('014_P22',(502,539,0)),('014_P24',(484,585,500))]:
   self.setUp()
   def after(x,y,w):self.f.visible=set();self.f.text='试炼'
   self.assertEqual(self.battle(name,after),1);self.assertEqual(self.f.taps[-1],point);self.assertEqual(self.ocr[-1],(65,7,247,59,0,0));self.assertEqual(self.e['soulReason'],'原试炼标题返回')
 def test_blank_or_partial_return_title_not_success(self):
  for text in ['',None,'试 炼','试炼中']:
   self.setUp()
   def after(x,y,w,v=text):self.f.visible=set();self.f.text=v
   self.assertEqual(self.battle('014_P22',after),4);self.assertFalse(self.e['terminalConfirmed']);self.assertEqual(self.e['soulCount'],0)
 def test_sweep_original500_and_result1000_then_title(self):
  for sweep in ['014_P12','014_P13']:
   for result in ['014_P26','014_P27']:
    self.setUp();self.f.visible={'014_P02',sweep};self.f.text='1/2'
    def after(x,y,w):
     if w==50:self.f.visible={sweep}
     elif w==500:self.f.visible={result}
     else:self.f.visible=set();self.f.text='试炼'
    self.f.after=after;self.assertEqual(self.e['RunSoulTrial'](),1);self.assertEqual(self.f.taps,[(600,900,50),(600,900,500),(600,900,0)])
 def test_native20seconds_only_marks_continues_until_public_timeout(self):
  self.f.visible={'014_P02'};self.f.text='1/2';self.assertEqual(self.e['RunSoulTrial'](),4);self.assertGreater(self.f.now,120000);self.assertFalse(self.e['soulNativeTimeout']);self.assertFalse(self.e['terminalConfirmed']);self.assertEqual(self.e['soulCount'],0)
 def test_after20seconds_late_challenge_overwrites_marker(self):
  self.f.visible={'014_P02'};self.f.text='1/2'
  def after(x,y,w):
   if (x,y)==(780,648):self.f.visible={'014_P25'}
   elif self.f.now>21000:self.f.visible={'014_P14'}
  self.f.after=after;self.assertEqual(self.e['RunSoulTrial'](),1);self.assertGreater(self.f.now,21000);self.assertEqual(self.e['soulReason'],'原战斗失败退出');self.assertFalse(self.e['soulNativeTimeout'])
 def test_native35seconds_idle_boundary(self):
  def after(x,y,w):self.f.visible=set()
  self.assertEqual(self.battle('014_P22',after),4);self.assertGreater(self.f.now,35000);self.assertLess(self.f.now,38000);self.assertTrue(self.e['soulNativeTimeout'])
 def test_startbattle_original_double_click_and_extra500wait(self):
  starts=[]
  def after(x,y,w):
   if (x,y)==(587,982):starts.append(self.f.now);self.f.visible={'014_P25'}
  self.assertEqual(self.battle('152_开战图标6',after),1);self.assertIn((398,982,500),self.f.taps);self.assertIn((587,982,500),self.f.taps);self.assertGreaterEqual(self.f.now-starts[0],1500)
 def test_missing_fighters_click_anchor_then_continue(self):
  def after(x,y,w):self.f.visible={'014_P25'}
  self.assertEqual(self.battle('032_少人提示',after),1);self.assertEqual(self.f.taps[-2:],[(600,900,0),(600,900,0)])
 def test_return_button_original_fixed_point_and1000wait(self):
  def after(x,y,w):
   if (x,y)==(502,539):self.f.visible={'014_P23'};self.f.text=''
   elif (x,y)==(128,1228):self.f.visible=set();self.f.text='试炼'
  self.assertEqual(self.battle('014_P22',after),1);self.assertIn((128,1228,1000),self.f.taps)
 def test_initial_business_timer_reset_excludes_entry_elapsed(self):
  self.f.now=60000;self.f.visible={'014_P02'};self.f.text='0/2';self.assertEqual(self.e['RunSoulTrial'](),1);self.assertEqual(self.e['businessStarted'],60000)
 def test_soul_no_vertical_scroll_even_after1500(self):
  self.e['businessLimit']=2000;self.f.visible={'014_P02'};self.f.text='1/2';self.assertEqual(self.e['RunSoulTrial'](),4);self.assertGreater(self.f.now,1500);self.assertFalse(self.swipes)
 def test_native300seconds_even_with_battle_timer_refresh(self):
  self.assertEqual(self.battle('014_AutoReady'),4);self.assertGreater(self.f.now,300000);self.assertLess(self.f.now,302000);self.assertTrue(self.e['soulNativeTimeout']);self.assertFalse(self.e['terminalConfirmed'])
 def test_native_timeout_count65seconds_recovery_not_success(self):
  self.e.update(resumeTask=14);self.e['ConfirmSoulExit']('native',3);stamp=self.e['soulFinishedAt'];self.e['RecoverSoulTask']()
  self.assertEqual((self.e['soulCount'],self.e['soulDue'],self.e['resumeTask']),(1,stamp+65,0));self.assertFalse(self.e['soulDone']);self.assertFalse(self.e['terminalConfirmed'])
 def test_five_native_timeouts_abandoned_not_done(self):
  for i in range(5):self.e['ConfirmSoulExit']('native',3);self.e['RecoverSoulTask']()
  self.assertEqual(self.e['soulCount'],5);self.assertTrue(self.e['soulAbandoned']);self.assertFalse(self.e['soulDone'])
 def test_foreground_recovery_no_count_no_reschedule(self):
  self.e.update(resumeTask=14);due=self.e['soulDue'];self.e['RecoverSoulTask']();self.assertEqual((self.e['soulCount'],self.e['soulDue'],self.e['resumeTask']),(0,due,14))
 def test_commit_requires_terminal_and_continuous_hall(self):
  load(['common/任务状态.mq'],self.e);self.e['SaveCurrentTask'](14)
  self.assertFalse(self.e['CommitTask'](True));self.e['ConfirmSoulExit']('depleted',1);self.assertFalse(self.e['CommitTask'](False));self.assertFalse(self.e['soulDone'])
  self.assertTrue(self.e['CommitTask'](True));self.assertTrue(self.e['soulDone']);self.assertEqual(self.e['soulCount'],0);self.assertEqual(self.e['currentTask'],0)
 def test_five_business_exits_complete_only_after_commit(self):
  load(['common/任务状态.mq'],self.e)
  for i in range(5):
   self.e['SaveCurrentTask'](14);self.e['ConfirmSoulExit']('exit',4);self.assertEqual(self.e['soulCount'],i);self.assertTrue(self.e['CommitTask'](True));self.assertEqual(self.e['soulCount'],i+1)
  self.assertTrue(self.e['soulDone']);self.assertFalse(self.e['soulAbandoned'])
 def test_interruption_blocks_actions_and_terminal(self):
  self.f.interrupt=True
  for fn in ['EnterSoulTrial','RunSoulTrial','ExecuteSoulTrial']:self.assertEqual(self.e[fn](),4)
  self.assertEqual(self.e['ConfirmSoulExit']('late',1),4);self.assertFalse(self.e['ResetSoulTimer']());self.assertFalse(self.f.taps);self.assertFalse(self.swipes);self.assertFalse(self.e['terminalConfirmed'])
 def test_public_timeout_strict_greater_and_cannot_revive(self):
  self.f.now=120000;self.assertFalse(self.e['BusinessExpired']());self.f.now+=1;self.assertTrue(self.e['BusinessExpired']());self.assertFalse(self.e['ResetSoulTimer']());self.assertEqual(self.e['businessStarted'],0)
 def test_foreground_resumes12_preserves_attempts(self):
  import test_foreground
  fg=test_foreground.Foreground();fg.setUp();fg.e.update(Time=lambda:1760000000,WorldLog=fg.logs.append,WorldStage=lambda s:None)
  load(['common/龙魂试炼状态.mq'],fg.e);fg.e['NewSoulSession']();fg.e['SaveCurrentTask'](14);fg.request();self.assertTrue(fg.e['HandleForegroundRecovery']());self.assertEqual(fg.e['SelectDueTask'](),14);self.assertEqual((fg.e['soulCount'],fg.e['soulRecoveries'],fg.e['soulRestarts']),(0,1,1))
 def test_ui_only_original_checkbox_and_all_defaults_false(self):
  def controls(t):return {re.search('名称:"([^"]+)"',b)[1]:(k,b) for k,b in re.findall(r'(输入框|下拉框|多选框):\{([^{}]+)\}',t)}
  old=controls((ROOT/'reports/龙魂试炼接入-20261017/before/ui/最小配置.uip').read_text('utf-8-sig'));now=controls((ROOT/'ui/最小配置.uip').read_text('utf-8-sig'));original=controls((E/'原界面配置.uip.txt').read_text('utf8').replace('点击响应:"函数名1",',''))
  self.assertEqual({k:now[k] for k in old},old);self.assertEqual(set(now)-set(old),{'SlHb','SlJyin','SlLh'});self.assertEqual({k:now[k] for k in original},original);self.assertTrue(all('选中:false' in b for k,b in now.values() if k=='多选框'))
 def test_catalog_append_only22_and_exact_mq(self):
  before=json.loads((ROOT/'reports/龙魂试炼接入-20261017/before/evidence/图色参数.json').read_text('utf8'));now=json.loads((ROOT/'evidence/图色参数.json').read_text('utf8'));records=json.loads((E/'图色转换.json').read_text('utf8'));self.assertEqual([r for r in now if not r['name'].startswith(('016_','015_'))],before+records);self.assertEqual(len(records),22)
  mq=(ROOT/'common/图色参数.mq').read_text('utf-8-sig')
  for r in records:
   args=', '.join(json.dumps(x) if isinstance(x,str) else str(x) for x in r['definition']);self.assertIn('Case "'+r['name']+'"\n        FindMultiColor '+args+', foundX, foundY',mq)
 def test_raw_soul_patterns_not_other_trial_profiles(self):
  allraw={r['name']:r for r in json.loads((E/'图色全表.json').read_text('utf8'))};records=json.loads((E/'图色转换.json').read_text('utf8'))
  for r in records:
   if r['name'].startswith('014_P'):self.assertEqual(r,allraw[r['name']])
  self.assertNotIn('014_P01',{r['name'] for r in records});self.assertEqual({r['definition'][6] for r in records},{1})
 def test_raw_call_rectangles_colors_similarity(self):
  by={r['name']:r['definition'] for r in json.loads((E/'图色转换.json').read_text('utf8'))}
  for c in json.loads((E/'调用位置全表.json').read_text('utf8')):
   if c['name'] not in by:continue
   source='root637静态重建.txt' if c['source']=='root.637' else 'root783试炼位置.txt' if c['source']=='root.783试炼' else 'root787试炼入口.txt'
   lines=(E/source).read_text('utf8').splitlines();i=c['line']-1
   region=[int(re.search(r'= (\d+)$',line)[1]) for line in lines[i-4:i]]
   if region==[0,0,0,0]:region=[0,0,719,1279]
   else:region[2]=min(region[2],719);region[3]=min(region[3],1279)
   literal=lambda l:re.search(r'= "(.*)"$',l)[1]
   self.assertEqual(by[c['name']][:6],region+[literal(lines[i]),literal(lines[i+1])])
 def test_only_task14_no_new_engine_or_public_ownership(self):
  cfg=json.loads((ROOT/'project.json').read_text('utf8'));self.assertEqual(cfg['registeredTasks'].count(14),1)
  flow=(ROOT/'flows/014_龙魂试炼/龙魂试炼.mq').read_text('utf-8-sig');code='\n'.join(l for l in flow.splitlines() if not l.lstrip().startswith('//'));self.assertNotRegex(code,r'OcrEx|paddle|Image\.Ocr|KillApp|RunApp|CommitTask|SchedulerStep|businessStarted\s*=')
  names={r['name'] for r in json.loads((E/'图色转换.json').read_text('utf8'))}|{'152_开战图标6','032_少人提示'};self.assertTrue(set(re.findall('WorldMatch\\("([^"]+)"\\)',flow))<=names)
 def test_cooldown_requires_colon_not_bare00(self):
  for text in ['00','100','00-10']:
   self.setUp();self.e['businessLimit']=2000;self.f.visible={'014_P02'};self.f.text=text;self.assertEqual(self.e['RunSoulTrial'](),4);self.assertEqual(self.e['soulExitKind'],0);self.assertFalse(self.e['soulDone']);self.assertTrue(self.f.taps)
 def test_gray_ended_even_when_ocr_missing_no_click(self):
  self.f.visible={'014_P05'};self.assertEqual(self.e['RunSoulTrial'](),1);self.assertEqual(self.e['soulExitKind'],5);self.assertFalse(self.f.taps);self.assertFalse(self.swipes);self.assertFalse(self.e['soulDone']);self.assertEqual(self.e['soulCount'],0)
 def test_gray_end_only_commits_after_hall_no_count_no65seconds(self):
  load(['common/任务状态.mq'],self.e);self.e['SaveCurrentTask'](14);due=self.e['soulDue'];self.f.visible={'014_P05'};self.assertEqual(self.e['RunSoulTrial'](),1)
  self.assertFalse(self.e['CommitTask'](False));self.assertFalse(self.e['soulDone']);self.assertTrue(self.e['CommitTask'](True));self.assertTrue(self.e['soulDone']);self.assertEqual((self.e['soulCount'],self.e['soulDue']),(0,due))
 def test_empty_ocr_with_initial_and_gray_uses_only_gray_evidence(self):
  self.f.visible={'014_P02','014_P05','014_P14'};self.f.text='';self.assertEqual(self.e['RunSoulTrial'](),1);self.assertEqual(self.e['soulReason'],'原龙魂灰色入口结束');self.assertFalse(self.f.taps);self.assertEqual(self.e['soulCount'],0)
 def test_ocr_exhaustion_precedes_gray_when_both_match(self):
  self.f.visible={'014_P02','014_P05'};self.f.text='0/2';self.assertEqual(self.e['RunSoulTrial'](),1);self.assertEqual(self.e['soulExitKind'],1);self.assertNotIn('014_P05',self.f.lookups)
 def test_soul_original_duplicate_entry_reuses_single_template(self):
  by={r['name']:r['definition'] for r in json.loads((E/'图色转换.json').read_text('utf8'))};self.assertNotIn('014_P10',by);self.f.visible={'014_P02'};self.assertTrue(self.e['SoulEntryIcon']());self.assertEqual(self.f.lookups,['014_P02'])
 def test_soul_flow_has_no_gold_experience_region_or_internal_swipe(self):
  flow=(ROOT/'flows/014_龙魂试炼/龙魂试炼.mq').read_text('utf-8-sig');self.assertNotRegex(flow,r'012_|013_|SlJb|SlJyan|ax - 400|ax - 410|ax - 350')
  self.assertIn('WorldText(ax - 115, ay + 108, ax - 62, ay + 134)',flow);self.assertNotIn('Swipe',flow[flow.index('Function RunSoulTrial()'):]);self.assertIn('InStr(1, text, "00:")',flow)
 def test_soul_commit_cannot_modify_gold_experience(self):
  load(['common/金币试炼状态.mq','common/经验试炼状态.mq','common/任务状态.mq'],self.e);self.e['NewGoldSession']();self.e['NewExperienceSession']();self.e.update(goldCount=3,goldDue=99,experienceCount=4,experienceDue=88)
  self.e['SaveCurrentTask'](14);self.e['ConfirmSoulExit']('exit',4);self.assertTrue(self.e['CommitTask'](True));self.assertEqual((self.e['goldCount'],self.e['goldDue'],self.e['experienceCount'],self.e['experienceDue']),(3,99,4,88));self.assertEqual(self.e['soulCount'],1)
 def test_soul_native_recovery_cannot_modify_gold_experience(self):
  self.e.update(goldCount=3,experienceCount=4,goldDue=99,experienceDue=88,resumeTask=14);self.e['ConfirmSoulExit']('timeout',3);self.e['RecoverSoulTask']();self.assertEqual((self.e['goldCount'],self.e['experienceCount'],self.e['goldDue'],self.e['experienceDue']),(3,4,99,88));self.assertEqual(self.e['soulCount'],1)
 def test_gold12_experience13_soul14_selection_and_resume(self):
  import test_foreground
  fg=test_foreground.Foreground();fg.setUp();fg.e.update(Time=lambda:1760000000,WorldLog=fg.logs.append,WorldStage=lambda s:None)
  load(['common/金币试炼状态.mq','common/经验试炼状态.mq','common/龙魂试炼状态.mq'],fg.e)
  for name in ['NewGoldSession','NewExperienceSession','NewSoulSession','RegisterTasks']:fg.e[name]()
  fg.e.update(goldEnabled=True,experienceEnabled=True,soulEnabled=True,resumeTask=0);self.assertEqual(fg.e['SelectDueTask'](),12);fg.e['goldDone']=True;self.assertEqual(fg.e['SelectDueTask'](),13);fg.e['experienceDone']=True;self.assertEqual(fg.e['SelectDueTask'](),14);fg.e.update(resumeTask=14,goldDone=False);self.assertEqual(fg.e['SelectDueTask'](),14)
 def test_only_soul14_added_to_existing_registration(self):
  cfg=json.loads((ROOT/'project.json').read_text('utf8'));old=json.loads((ROOT/'reports/龙魂试炼接入-20261017/before/project.json').read_text('utf8'));self.assertEqual([v for v in cfg['registeredTasks'] if v not in (15,16)],old['registeredTasks']+[14]);self.assertEqual([v for v in cfg['modules'] if v not in ['common/伙伴试炼状态.mq','flows/016_伙伴试炼/伙伴试炼.mq','common/基因试炼状态.mq','flows/015_基因试炼/基因试炼.mq']],old['modules']+['common/龙魂试炼状态.mq','flows/014_龙魂试炼/龙魂试炼.mq'])
if __name__=='__main__':unittest.main()
