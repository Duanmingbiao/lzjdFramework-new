import unittest,json,re
from mq_subset import ROOT,load
import test_worldboss
E=ROOT/'flows/015_基因试炼/evidence'
class GeneTests(unittest.TestCase):
 def setUp(self):
  self.f=test_worldboss.WorldBossTests();self.f.setUp();self.e=self.f.e;self.swipes=[];self.ocr=[]
  def match(n):self.f.now+=10;return self.f.match(n)
  def ocr(*a):self.ocr.append(a);return self.f.text
  self.e.update(MatchPattern=match,currentTask=15,businessStarted=0,businessLimit=120000,ForegroundInterrupted=lambda:self.f.interrupt,ReadUIConfig=lambda k,d:d,Replace=lambda s,a,b:s.replace(a,b),Chr=chr,InStr=lambda start,s,x:s.find(x,start-1)+1,Swipe=lambda *a:self.swipes.append(a))
  self.e['Image'].OcrText=ocr;self.e['Sys'].IsRunning=lambda p:True
  load(['common/基因试炼状态.mq','flows/015_基因试炼/基因试炼.mq','common/运行计时.mq'],self.e)
  self.e['LoadGeneSettings']();self.e['NewGeneSession']()
 def test_original_single_checkbox_default_disabled(self):
  keys=[];self.e['ReadUIConfig']=lambda k,d:keys.append(k) or d;self.e['LoadGeneSettings']();self.assertEqual(keys,['SlJyin','设置_重要_闪退']);self.assertFalse(self.e['geneEnabled'])
 def test_enabled_immediate_due_and_five_limit(self):
  self.assertEqual(self.e['SelectGene'](),0);self.e['geneEnabled']=True;self.assertEqual(self.e['SelectGene'](),15)
  for key in ['geneDone','geneAbandoned']:
   self.e[key]=True;self.assertEqual(self.e['SelectGene'](),0);self.e[key]=False
  self.e['geneDue']=self.e['Time']()+65;self.assertEqual(self.e['SelectGene'](),0);self.f.stamp+=65;self.assertEqual(self.e['SelectGene'](),15)
 def test_eight_exact_exhausted_tokens(self):
  for s in ['02','03','04','05','012','013','014','015']:self.assertTrue(self.e['GeneCountExhausted'](s))
  for s in ['',None,'0','00','06','错误02','02x','102','0/2']:self.assertFalse(self.e['GeneCountExhausted'](s))
 def test_old_ocr_conservative_separators_not_fuzzy_digits(self):
  for s,w in [(None,''),('0/2','02'),('0 | 12\r\n\t','012'),('错误0/2','错误02')]:self.assertEqual(self.e['GeneFilterText'](s),w)
 def test_exhausted_original_anchor_region_no_click_pending_only(self):
  self.f.visible={'015_P03'};self.f.text='0/2';self.assertEqual(self.e['RunGeneTrial'](),1)
  self.assertEqual(self.ocr,[(190,1015,250,1055,0,0)]);self.assertFalse(self.f.taps);self.assertTrue(self.e['terminalConfirmed']);self.assertFalse(self.e['geneDone']);self.assertEqual(self.e['geneCount'],0)
 def test_cooldown_contains00_not_counted(self):
  self.f.visible={'015_P03'};self.f.text='00:10';self.assertEqual(self.e['RunGeneTrial'](),1);self.assertEqual(self.e['geneExitKind'],2)
  self.e['CommitGeneTask']();self.assertEqual(self.e['geneDue'],self.e['geneFinishedAt']+65);self.assertEqual(self.e['geneCount'],0);self.assertFalse(self.e['geneDone'])
 def test_empty_unknown_count_never_exhausted_or_success(self):
  for s in ['',None,'错误02']:
   self.setUp();self.f.visible={'015_P03'};self.f.text=s;self.assertEqual(self.e['RunGeneTrial'](),4);self.assertFalse(self.e['terminalConfirmed']);self.assertFalse(self.e['geneDone']);self.assertFalse(self.e['geneNativeTimeout'])
 def test_no_count_anchor_public_timeout_no_native_failure(self):
  self.assertEqual(self.e['RunGeneTrial'](),4);self.assertFalse(self.e['geneNativeTimeout']);self.assertEqual(self.e['geneCount'],0);self.assertFalse(self.f.taps)
 def test_location_two_original_patterns_no_touch(self):
  for name in ['015_P33','015_P34']:
   self.setUp();self.f.visible={name};self.assertEqual(self.e['EnterGeneTrial'](),1);self.assertFalse(self.f.taps);self.assertFalse(self.swipes)
 def test_known_location_first_hit_preserves_anchor(self):
  self.f.visible={'015_P33'};self.assertTrue(self.e['GeneTrialKnown']());self.assertEqual(self.f.lookups,['015_P33'])
 def test_hall_icon_original_click1500(self):
  for icon in ['015_P28','015_P29']:
   self.setUp();self.e['ReturnToHall']=lambda:1;self.f.visible={'015_P30',icon};self.f.after=lambda *a:setattr(self.f,'visible',{'015_P33'})
   self.assertEqual(self.e['EnterGeneTrial'](),1);self.assertEqual(self.f.taps,[(600,900,1500)])
 def test_missing_trial_icon_original_slide_left(self):
  self.e['ReturnToHall']=lambda:1;self.f.visible={'015_P30'}
  def swipe(*a):self.swipes.append(a);self.f.visible={'015_P33'}
  self.e['Swipe']=swipe;self.assertEqual(self.e['EnterGeneTrial'](),1);self.assertEqual(self.swipes,[(150,545,500,545,300)])
 def test_entry_unknown60seconds_no_blind_click(self):
  self.e['ReturnToHall']=lambda:1;self.assertEqual(self.e['EnterGeneTrial'](),4);self.assertGreater(self.f.now,63000);self.assertFalse(self.f.taps);self.assertFalse(self.swipes);self.assertFalse(self.e['terminalConfirmed'])
 def test_return_hall_failure_stops_entry(self):
  self.e['ReturnToHall']=lambda:4;self.assertEqual(self.e['EnterGeneTrial'](),4);self.assertFalse(self.f.taps);self.assertFalse(self.swipes)
 def test_scroll_original_vertical_direction_and_foreground_guard(self):
  self.assertTrue(self.e['GeneTrialScrollDown']());self.assertEqual(self.swipes,[(370,1000,370,300,300)]);self.f.interrupt=True;self.assertFalse(self.e['GeneTrialScrollDown']());self.assertEqual(len(self.swipes),1)
 def test_first_match_sweep_entry_result_short_circuit(self):
  for fn,name in [('GeneSweepReady','015_P12'),('GeneEntryIcon','015_P03'),('GeneSweepResult','015_P26')]:
   self.setUp();self.f.visible={name};self.assertTrue(self.e[fn]());self.assertEqual(self.f.lookups,[name])
 def test_autotriple_original_priorities_offsets(self):
  for n,tap in [('015_AutoReady',None),('015_AutoOff',(290,1070,50)),('015_TripleOff',(918,992,50)),('015_BattleBase',(918,916,50))]:
   self.setUp();self.f.visible={n};self.assertEqual(self.e['GeneAutoTriple'](),tap is None);self.assertEqual(self.f.taps,[] if tap is None else [tap])
 def battle(self,pattern,after=None):
  self.f.visible={'015_P03','015_P14'};self.f.text='1/2'
  def nextpage(x,y,w):
   if len(self.f.taps)==1:self.f.visible={'015_P14',pattern}
   elif (x,y)==(780,648):self.f.visible={pattern}
   elif after:after(x,y,w)
  self.f.after=nextpage
  return self.e['RunGeneTrial']()
 def test_challenge_original_offset_and_failure_countable_exit(self):
  self.assertEqual(self.battle('015_P25'),1);self.assertEqual(self.f.taps,[(600,900,50),(780,648,500),(600,900,0)]);self.assertEqual(self.e['geneReason'],'原战斗失败退出');self.assertEqual(self.e['geneCount'],0)
 def test_two_victory_original_clicks_require_exact_title(self):
  for name,point in [('015_P22',(150,50,0)),('015_P24',(484,585,500))]:
   self.setUp()
   def after(x,y,w):self.f.visible=set();self.f.text='试炼'
   self.assertEqual(self.battle(name,after),1);self.assertEqual(self.f.taps[-1],point);self.assertEqual(self.ocr[-1],(65,7,247,59,0,0));self.assertEqual(self.e['geneReason'],'原试炼标题返回')
 def test_blank_or_partial_return_title_not_success(self):
  for text in ['',None,'试 炼','试炼中']:
   self.setUp()
   def after(x,y,w,v=text):self.f.visible=set();self.f.text=v
   self.assertEqual(self.battle('015_P22',after),4);self.assertFalse(self.e['terminalConfirmed']);self.assertEqual(self.e['geneCount'],0)
 def test_sweep_original500_and_result1000_then_title(self):
  for sweep in ['015_P12','015_P13']:
   for result in ['015_P26','015_P27']:
    self.setUp();self.f.visible={'015_P03',sweep};self.f.text='1/2'
    def after(x,y,w):
     if w==50:self.f.visible={sweep}
     elif w==500:self.f.visible={result}
     else:self.f.visible=set();self.f.text='试炼'
    self.f.after=after;self.assertEqual(self.e['RunGeneTrial'](),1);self.assertEqual(self.f.taps,[(600,900,50),(600,900,500),(600,900,0)])
 def test_native20seconds_only_marks_continues_until_public_timeout(self):
  self.f.visible={'015_P03'};self.f.text='1/2';self.assertEqual(self.e['RunGeneTrial'](),4);self.assertGreater(self.f.now,120000);self.assertFalse(self.e['geneNativeTimeout']);self.assertFalse(self.e['terminalConfirmed']);self.assertEqual(self.e['geneCount'],0)
 def test_after20seconds_late_challenge_overwrites_marker(self):
  self.f.visible={'015_P03'};self.f.text='1/2'
  def after(x,y,w):
   if (x,y)==(780,648):self.f.visible={'015_P25'}
   elif self.f.now>21000:self.f.visible={'015_P14'}
  self.f.after=after;self.assertEqual(self.e['RunGeneTrial'](),1);self.assertGreater(self.f.now,21000);self.assertEqual(self.e['geneReason'],'原战斗失败退出');self.assertFalse(self.e['geneNativeTimeout'])
 def test_native35seconds_idle_boundary(self):
  def after(x,y,w):self.f.visible=set()
  self.assertEqual(self.battle('015_P22',after),4);self.assertGreater(self.f.now,35000);self.assertLess(self.f.now,38000);self.assertTrue(self.e['geneNativeTimeout'])
 def test_startbattle_original_double_click_and_extra500wait(self):
  starts=[]
  def after(x,y,w):
   if (x,y)==(587,982):starts.append(self.f.now);self.f.visible={'015_P25'}
  self.assertEqual(self.battle('152_开战图标6',after),1);self.assertIn((398,982,500),self.f.taps);self.assertIn((587,982,500),self.f.taps);self.assertGreaterEqual(self.f.now-starts[0],1500)
 def test_missing_fighters_click_anchor_then_continue(self):
  def after(x,y,w):self.f.visible={'015_P25'}
  self.assertEqual(self.battle('032_少人提示',after),1);self.assertEqual(self.f.taps[-2:],[(600,900,0),(600,900,0)])
 def test_return_button_original_fixed_point_and1000wait(self):
  def after(x,y,w):
   if (x,y)==(150,50):self.f.visible={'015_P23'};self.f.text=''
   elif (x,y)==(128,1228):self.f.visible=set();self.f.text='试炼'
  self.assertEqual(self.battle('015_P22',after),1);self.assertIn((128,1228,1000),self.f.taps)
 def test_initial_business_timer_reset_excludes_entry_elapsed(self):
  self.f.now=60000;self.f.visible={'015_P03'};self.f.text='0/2';self.assertEqual(self.e['RunGeneTrial'](),1);self.assertEqual(self.e['businessStarted'],60000)
 def test_scroll_only_strictly_after1500(self):
  times=[];self.e['Swipe']=lambda *a:times.append((self.f.now,a));self.e['businessLimit']=2000
  self.assertEqual(self.e['RunGeneTrial'](),4);self.assertTrue(times);self.assertGreater(times[0][0],1500);self.assertEqual(times[0][1],(370,1000,370,300,300))
 def test_native300seconds_even_with_battle_timer_refresh(self):
  self.assertEqual(self.battle('015_AutoReady'),4);self.assertGreater(self.f.now,300000);self.assertLess(self.f.now,302000);self.assertTrue(self.e['geneNativeTimeout']);self.assertFalse(self.e['terminalConfirmed'])
 def test_native_timeout_count65seconds_recovery_not_success(self):
  self.e.update(resumeTask=15);self.e['ConfirmGeneExit']('native',3);stamp=self.e['geneFinishedAt'];self.e['RecoverGeneTask']()
  self.assertEqual((self.e['geneCount'],self.e['geneDue'],self.e['resumeTask']),(1,stamp+65,0));self.assertFalse(self.e['geneDone']);self.assertFalse(self.e['terminalConfirmed'])
 def test_five_native_timeouts_abandoned_not_done(self):
  for i in range(5):self.e['ConfirmGeneExit']('native',3);self.e['RecoverGeneTask']()
  self.assertEqual(self.e['geneCount'],5);self.assertTrue(self.e['geneAbandoned']);self.assertFalse(self.e['geneDone'])
 def test_foreground_recovery_no_count_no_reschedule(self):
  self.e.update(resumeTask=15);due=self.e['geneDue'];self.e['RecoverGeneTask']();self.assertEqual((self.e['geneCount'],self.e['geneDue'],self.e['resumeTask']),(0,due,15))
 def test_commit_requires_terminal_and_continuous_hall(self):
  load(['common/任务状态.mq'],self.e);self.e['SaveCurrentTask'](15)
  self.assertFalse(self.e['CommitTask'](True));self.e['ConfirmGeneExit']('depleted',1);self.assertFalse(self.e['CommitTask'](False));self.assertFalse(self.e['geneDone'])
  self.assertTrue(self.e['CommitTask'](True));self.assertTrue(self.e['geneDone']);self.assertEqual(self.e['geneCount'],0);self.assertEqual(self.e['currentTask'],0)
 def test_five_business_exits_complete_only_after_commit(self):
  load(['common/任务状态.mq'],self.e)
  for i in range(5):
   self.e['SaveCurrentTask'](15);self.e['ConfirmGeneExit']('exit',4);self.assertEqual(self.e['geneCount'],i);self.assertTrue(self.e['CommitTask'](True));self.assertEqual(self.e['geneCount'],i+1)
  self.assertTrue(self.e['geneDone']);self.assertFalse(self.e['geneAbandoned'])
 def test_interruption_blocks_actions_and_terminal(self):
  self.f.interrupt=True
  for fn in ['EnterGeneTrial','RunGeneTrial','ExecuteGeneTrial']:self.assertEqual(self.e[fn](),4)
  self.assertEqual(self.e['ConfirmGeneExit']('late',1),4);self.assertFalse(self.e['ResetGeneTimer']());self.assertFalse(self.f.taps);self.assertFalse(self.swipes);self.assertFalse(self.e['terminalConfirmed'])
 def test_public_timeout_strict_greater_and_cannot_revive(self):
  self.f.now=120000;self.assertFalse(self.e['BusinessExpired']());self.f.now+=1;self.assertTrue(self.e['BusinessExpired']());self.assertFalse(self.e['ResetGeneTimer']());self.assertEqual(self.e['businessStarted'],0)
 def test_foreground_resumes12_preserves_attempts(self):
  import test_foreground
  fg=test_foreground.Foreground();fg.setUp();fg.e.update(Time=lambda:1760000000,WorldLog=fg.logs.append,WorldStage=lambda s:None)
  load(['common/基因试炼状态.mq'],fg.e);fg.e['NewGeneSession']();fg.e['SaveCurrentTask'](15);fg.request();self.assertTrue(fg.e['HandleForegroundRecovery']());self.assertEqual(fg.e['SelectDueTask'](),15);self.assertEqual((fg.e['geneCount'],fg.e['geneRecoveries'],fg.e['geneRestarts']),(0,1,1))
 def test_ui_only_original_checkbox_and_all_defaults_false(self):
  def controls(t):return {re.search('名称:"([^"]+)"',b)[1]:(k,b) for k,b in re.findall(r'(输入框|下拉框|多选框):\{([^{}]+)\}',t)}
  old=controls((ROOT/'reports/基因试炼接入-20261017/before/ui/最小配置.uip').read_text('utf-8-sig'));now=controls((ROOT/'ui/最小配置.uip').read_text('utf-8-sig'));original=controls((E/'原界面配置.uip.txt').read_text('utf8').replace('点击响应:"函数名1",',''))
  self.assertEqual({k:now[k] for k in old},old);self.assertEqual(set(now)-set(old),{'SlJyin'});self.assertEqual({k:now[k] for k in original},original);self.assertTrue(all('选中:false' in b for k,b in now.values() if k=='多选框'))
 def test_catalog_append_only30_and_exact_mq(self):
  before=json.loads((ROOT/'reports/基因试炼接入-20261017/before/evidence/图色参数.json').read_text('utf8'));now=json.loads((ROOT/'evidence/图色参数.json').read_text('utf8'));records=json.loads((E/'图色转换.json').read_text('utf8'));self.assertEqual(now,before+records);self.assertEqual(len(records),30)
  mq=(ROOT/'common/图色参数.mq').read_text('utf-8-sig')
  for r in records:
   args=', '.join(json.dumps(x) if isinstance(x,str) else str(x) for x in r['definition']);self.assertIn('Case "'+r['name']+'"\n        FindMultiColor '+args+', foundX, foundY',mq)
 def test_raw_gene_patterns_not_other_trial_profiles(self):
  allraw={r['name']:r for r in json.loads((E/'图色全表.json').read_text('utf8'))};records=json.loads((E/'图色转换.json').read_text('utf8'))
  for r in records:
   if r['name'].startswith('015_P'):self.assertEqual(r,allraw[r['name']])
  self.assertNotIn('015_P01',{r['name'] for r in records});self.assertEqual({r['definition'][6] for r in records},{1})
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
 def test_only_task15_no_new_engine_or_public_ownership(self):
  cfg=json.loads((ROOT/'project.json').read_text('utf8'));self.assertEqual(cfg['registeredTasks'].count(15),1)
  flow=(ROOT/'flows/015_基因试炼/基因试炼.mq').read_text('utf-8-sig');code='\n'.join(l for l in flow.splitlines() if not l.lstrip().startswith('//'));self.assertNotRegex(code,r'OcrEx|paddle|Image\.Ocr|KillApp|RunApp|CommitTask|SchedulerStep|businessStarted\s*=')
  names={r['name'] for r in json.loads((E/'图色转换.json').read_text('utf8'))}|{'152_开战图标6','032_少人提示'};self.assertTrue(set(re.findall('WorldMatch\\("([^"]+)"\\)',flow))<=names)
 def test_original_54_coordinate_pairs_exact(self):
  points=json.loads((E/'原三类坐标.json').read_text('utf8'))
  for kind,(name,rows) in enumerate([('龟仙流',[-460,-320,-180]),('鹤仙流',[-320,-460,-180]),('女战士',[-180,-460,-320])],1):
   expected=[[x,y] for y in rows for x in [45,145,240,330,430,515]];self.assertEqual(points[name],expected)
   self.assertEqual([[self.e['GenePointX'](kind,i),self.e['GenePointY'](kind,i)] for i in range(1,19)],expected)
 def test_pick18_original_points_each_mode_and19th_exit(self):
  points=json.loads((E/'原三类坐标.json').read_text('utf8'))
  for kind,name in enumerate(['龟仙流','鹤仙流','女战士'],1):
   self.setUp();self.e.update(foundX=600,foundY=900)
   for i in range(19):self.assertEqual(self.e['GenePick'](kind),1)
   self.assertEqual(self.f.taps,[(600+x,900+y,1000) for x,y in points[name]]+[(849,876,0)]);self.assertEqual(self.e['genePickIndex'],19)
 def test_shared_pick_index_across_modes(self):
  self.f.visible={'015_P15','015_P16','015_P17'};self.assertEqual(self.e['GeneSpecialEvents'](),1);self.assertEqual(self.e['genePickIndex'],3);self.assertEqual(self.f.taps,[(645,440,1000),(745,580,1000),(840,720,1000)])
 def test19th_pick_does_not_reset_public_timer(self):
  self.f.now=1000;self.e.update(foundX=600,foundY=900,genePickIndex=18,businessStarted=123);self.assertEqual(self.e['GenePick'](1),1);self.assertEqual(self.e['businessStarted'],123);self.assertEqual(self.f.taps,[(849,876,0)])
 def test_simple_gene_popup_original200_without_idle_refresh(self):
  self.f.visible={'015_P18'};self.e['geneActionAt']=7;self.assertEqual(self.e['GeneSpecialEvents'](),1);self.assertEqual(self.f.taps,[(600,900,200)]);self.assertEqual(self.e['geneActionAt'],7)
 def test_gene_victory_fixed_point_then_exact_return_title(self):
  self.e['EnterGeneTrial']=lambda:1
  def after(x,y,w):
   if (x,y)==(150,50):self.f.visible=set();self.f.text='试炼'
  self.assertEqual(self.battle('015_P22',after),1);self.assertEqual(self.f.taps[-1],(150,50,0));self.assertEqual(self.e['geneReason'],'原试炼标题返回')
 def test_first_rapid_phase_uses_preexisting_last_hit_timer(self):
  self.f.now=5000;self.e['geneClickAt']=0;self.assertEqual(self.e['GeneRapidClicks'](),1);self.assertEqual(self.f.lookups.count('015_P20'),1);self.assertFalse(self.f.taps);self.assertGreater(self.f.now,17000);self.assertLess(self.f.now,17100)
 def test_first_rapid_auto_anchor_wait10_then_quiet3500(self):
  self.f.visible={'015_P20'};self.f.after=lambda *a:setattr(self.f,'visible',set());self.assertEqual(self.e['GeneRapidClicks'](),1);self.assertEqual(self.f.taps,[(600,900,0)]);self.assertGreater(self.f.now,15500);self.assertLess(self.f.now,15600)
 def test_second_rapid_exact70clicks_offset24_wait70_each(self):
  self.f.now=4000;self.e['geneClickAt']=0;self.f.visible={'015_P21'};self.f.after=lambda *a:setattr(self.f,'visible',set())
  self.assertEqual(self.e['GeneRapidClicks'](),1);self.assertEqual(self.f.taps,[(600,876,0)]*70);self.assertGreater(self.f.now,20900);self.assertLess(self.f.now,21000);self.assertEqual(self.e['geneActionAt'],self.f.now)
 def test_rapid_unknown_quiet_exit_not_business_success(self):
  self.assertEqual(self.e['GeneRapidClicks'](),1);self.assertFalse(self.e['terminalConfirmed']);self.assertEqual(self.e['geneCount'],0);self.assertFalse(self.e['geneDone']);self.assertFalse(self.f.taps)
 def test_rapid_interrupted_mid70_does_not_continue_clicks(self):
  self.f.now=4000;self.f.visible={'015_P21'}
  def after(*a):
   if len(self.f.taps)==3:self.f.interrupt=True
  self.f.after=after;self.assertEqual(self.e['GeneRapidClicks'](),4);self.assertEqual(len(self.f.taps),3);self.assertFalse(self.e['terminalConfirmed'])
 def test_repeated_rapid_hits_are_not_total3500_deadline(self):
  self.e['businessLimit']=5000;self.f.visible={'015_P20'};self.assertEqual(self.e['GeneRapidClicks'](),4);self.assertGreater(self.f.now,5000);self.assertGreater(len(self.f.taps),100);self.assertNotIn('015_P21',self.f.lookups);self.assertFalse(self.e['terminalConfirmed'])
 def test_gray_gene_end_no_count_no65_after_hall(self):
  load(['common/任务状态.mq'],self.e);self.e['SaveCurrentTask'](15);due=self.e['geneDue'];self.f.visible={'015_P06'};self.assertEqual(self.e['RunGeneTrial'](),1);self.assertEqual(self.e['geneExitKind'],5);self.assertFalse(self.e['CommitTask'](False));self.assertTrue(self.e['CommitTask'](True));self.assertTrue(self.e['geneDone']);self.assertEqual((self.e['geneCount'],self.e['geneDue']),(0,due));self.assertFalse(self.f.taps)
 def test_missing_initial_ocr_cannot_enter_even_challenge_visible(self):
  self.f.visible={'015_P03','015_P14'};self.f.text='';self.assertEqual(self.e['RunGeneTrial'](),4);self.assertFalse(self.f.taps);self.assertFalse(self.e['terminalConfirmed']);self.assertFalse(self.e['geneNativeTimeout'])
 def test_bare00_is_original_gene_cooldown(self):
  self.f.visible={'015_P03'};self.f.text='00';self.assertEqual(self.e['RunGeneTrial'](),1);self.assertEqual(self.e['geneExitKind'],2);self.assertEqual(self.e['geneCount'],0)
 def test_forced_timeout_restarts_via_public_not_business_count(self):
  self.e['geneRestartOnTimeout']=True;due=self.e['geneDue'];self.f.visible={'015_P19'};self.assertEqual(self.e['GeneSpecialEvents'](),4);self.assertTrue(self.e['geneForcedRecovery']);self.assertFalse(self.e['geneNativeTimeout']);self.assertEqual(self.e['geneFailures'],1);self.e['resumeTask']=15;self.e['RecoverGeneTask']();self.assertEqual((self.e['geneCount'],self.e['geneDue'],self.e['resumeTask']),(0,due,15));self.assertFalse(self.e['geneDone'])
 def test_forced_timeout_three_failures_abandoned_not_success(self):
  self.e['geneRestartOnTimeout']=True
  for i in range(3):self.e['GeneForcedTimeout']();self.e['RecoverGeneTask']()
  self.assertEqual(self.e['geneFailures'],3);self.assertTrue(self.e['geneAbandoned']);self.assertFalse(self.e['geneDone']);self.assertEqual(self.e['geneCount'],0);self.assertEqual(self.e['resumeTask'],0)
 def test_forced_no_restart_returns_hall_then_continues_original_loop(self):
  calls=[];self.e.update(geneRestartOnTimeout=False,ReturnToHall=lambda:calls.append('hall') or 1);self.assertEqual(self.e['GeneForcedTimeout'](),1);self.assertEqual(calls,['hall']);self.assertFalse(self.e['geneForcedRecovery']);self.assertFalse(self.e['geneNoRestartPending']);self.assertEqual(self.e['geneCount'],0)
 def test_forced_no_restart_hall_unknown_keeps_pending_no_success(self):
  self.e.update(geneRestartOnTimeout=False,ReturnToHall=lambda:4,resumeTask=15);self.assertEqual(self.e['GeneForcedTimeout'](),4);self.assertTrue(self.e['geneNoRestartPending']);self.e['RecoverGeneTask']();self.assertEqual(self.e['resumeTask'],15);self.assertEqual(self.e['geneCount'],0);self.assertFalse(self.e['terminalConfirmed'])
 def test_forced_game_absent_requests_public_restart_even_switch_off(self):
  self.e['geneRestartOnTimeout']=False;self.e['Sys'].IsRunning=lambda p:False;self.e['ReturnToHall']=lambda:self.fail('absent game must not enter hall');self.assertEqual(self.e['GeneForcedTimeout'](),4);self.assertTrue(self.e['geneForcedRecovery']);self.assertFalse(self.e['geneNoRestartPending'])
 def test_forced_no_restart_scheduler_must_not_kill_or_launch(self):
  import test_foreground
  fg=test_foreground.Foreground();fg.setUp();fg.e.update(Time=lambda:1760000000,WorldLog=fg.logs.append,WorldStage=lambda s:None,ReadUIConfig=lambda k,d:d)
  load(['common/基因试炼状态.mq'],fg.e);fg.e['NewGeneSession']();fg.e.update(geneRestartOnTimeout=False,SelectDueTask=lambda:15,ReturnToHall=lambda:4,DispatchTask=lambda task:fg.e['GeneForcedTimeout']())
  fg.e['SchedulerStep']();self.assertEqual(fg.e['geneFailures'],1);self.assertFalse(fg.events);self.assertEqual(fg.e['resumeTask'],15);self.assertEqual(fg.e['geneCount'],0)
 def test_commit_and_recovery_cannot_modify_other_three_trials(self):
  self.e.update(goldCount=1,experienceCount=2,soulCount=3,goldDue=11,experienceDue=22,soulDue=33);load(['common/任务状态.mq'],self.e);self.e['SaveCurrentTask'](15);self.e['ConfirmGeneExit']('exit',4);self.assertTrue(self.e['CommitTask'](True));self.e['RecoverGeneTask']();self.assertEqual([self.e[k] for k in ['goldCount','experienceCount','soulCount','goldDue','experienceDue','soulDue']],[1,2,3,11,22,33])
 def test_only_gene15_added_to_existing_modules(self):
  cfg=json.loads((ROOT/'project.json').read_text('utf8'));old=json.loads((ROOT/'reports/基因试炼接入-20261017/before/project.json').read_text('utf8'));self.assertEqual(cfg['registeredTasks'],old['registeredTasks']+[15]);self.assertEqual(cfg['modules'],old['modules']+['common/基因试炼状态.mq','flows/015_基因试炼/基因试炼.mq'])
 def test_initial_entry_timer_does_not_seed_first_rapid_quiet_clock(self):
  self.f.now=4000;self.f.visible={'015_P03','015_P14'};self.f.text='1/2';self.e['GeneSpecialEvents']=lambda:4
  self.assertEqual(self.e['RunGeneTrial'](),4);self.assertGreater(self.e['geneClickAt'],4000)
 def test_gene_failure_count_persists_across_start_not_across_session(self):
  self.e['geneFailures']=2;self.e['StartGeneTask']();self.assertEqual(self.e['geneFailures'],2);self.e['NewGeneSession']();self.assertEqual(self.e['geneFailures'],0)
 def test_public_timeout_no_restart_continues_same_iteration_events(self):
  self.e.update(geneRestartOnTimeout=False,ReturnToHall=lambda:1);self.f.visible={'015_P19','015_P22'};self.assertEqual(self.e['GeneSpecialEvents'](),1);self.assertEqual(self.e['geneFailures'],1);self.assertTrue(self.e['geneSpecialExit']);self.assertEqual(self.f.taps,[(150,50,0)])
 def test_recovery_restart_logs_always_belong_to_task15_not14(self):
  self.e['RecoverGeneTask']();self.e['RestartGeneTask']();text='\n'.join(self.f.logs);self.assertIn('保留15',text);self.assertIn('公共重启恢复15',text);self.assertNotIn('保留14',text);self.assertNotIn('恢复14',text)
if __name__=='__main__':unittest.main()


