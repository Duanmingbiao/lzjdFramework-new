import unittest,json,re
from mq_subset import ROOT,load
import test_worldboss
E=ROOT/'flows/016_伙伴试炼/evidence'
class PartnerTests(unittest.TestCase):
 def setUp(self):
  self.f=test_worldboss.WorldBossTests();self.f.setUp();self.e=self.f.e;self.swipes=[];self.ocr=[]
  def match(n):self.f.now+=10;return self.f.match(n)
  def ocr(*a):self.ocr.append(a);return self.f.text
  self.e.update(MatchPattern=match,currentTask=16,businessStarted=0,businessLimit=120000,ForegroundInterrupted=lambda:self.f.interrupt,ReadUIConfig=lambda k,d:d,Replace=lambda s,a,b:s.replace(a,b),Chr=chr,InStr=lambda start,s,x:s.find(x,start-1)+1,Swipe=lambda *a:self.swipes.append(a))
  self.e['Image'].OcrText=ocr
  load(['common/伙伴试炼状态.mq','flows/016_伙伴试炼/伙伴试炼.mq','common/运行计时.mq'],self.e)
  self.e['LoadPartnerSettings']();self.e['NewPartnerSession']()
 def test_original_single_checkbox_default_disabled(self):
  keys=[];self.e['ReadUIConfig']=lambda k,d:keys.append(k) or d;self.e['LoadPartnerSettings']();self.assertEqual(keys,['SlHb']);self.assertFalse(self.e['partnerEnabled'])
 def test_enabled_immediate_due_and_five_limit(self):
  self.assertEqual(self.e['SelectPartner'](),0);self.e['partnerEnabled']=True;self.assertEqual(self.e['SelectPartner'](),16)
  for key in ['partnerDone','partnerAbandoned']:
   self.e[key]=True;self.assertEqual(self.e['SelectPartner'](),0);self.e[key]=False
  self.e['partnerDue']=self.e['Time']()+65;self.assertEqual(self.e['SelectPartner'](),0);self.f.stamp+=65;self.assertEqual(self.e['SelectPartner'](),16)
 def test_eight_exact_exhausted_tokens(self):
  for s in ['02','03','04','05','012','013','014','015']:self.assertTrue(self.e['PartnerCountExhausted'](s))
  for s in ['',None,'0','00','06','错误02','02x','102','0/2']:self.assertFalse(self.e['PartnerCountExhausted'](s))
 def test_old_ocr_conservative_separators_not_fuzzy_digits(self):
  for s,w in [(None,''),('0/2','02'),('0 | 12\r\n\t','012'),('错误0/2','错误02')]:self.assertEqual(self.e['PartnerFilterText'](s),w)
 def test_exhausted_original_anchor_region_no_click_pending_only(self):
  self.f.visible={'016_P04'};self.f.text='0/2';self.assertEqual(self.e['RunPartnerTrial'](),1)
  self.assertEqual(self.ocr,[(190,930,250,970,0,0)]);self.assertFalse(self.f.taps);self.assertTrue(self.e['terminalConfirmed']);self.assertFalse(self.e['partnerDone']);self.assertEqual(self.e['partnerCount'],0)
 def test_cooldown_contains00_not_counted(self):
  self.f.visible={'016_P04'};self.f.text='00:10';self.assertEqual(self.e['RunPartnerTrial'](),1);self.assertEqual(self.e['partnerExitKind'],2)
  self.e['CommitPartnerTask']();self.assertEqual(self.e['partnerDue'],self.e['partnerFinishedAt']+65);self.assertEqual(self.e['partnerCount'],0);self.assertFalse(self.e['partnerDone'])
 def test_empty_unknown_count_never_exhausted_or_success(self):
  for s in ['',None,'错误02']:
   self.setUp();self.f.visible={'016_P04'};self.f.text=s;self.assertEqual(self.e['RunPartnerTrial'](),4);self.assertFalse(self.e['terminalConfirmed']);self.assertFalse(self.e['partnerDone']);self.assertFalse(self.e['partnerNativeTimeout'])
 def test_no_count_anchor_public_timeout_no_native_failure(self):
  self.assertEqual(self.e['RunPartnerTrial'](),4);self.assertFalse(self.e['partnerNativeTimeout']);self.assertEqual(self.e['partnerCount'],0);self.assertFalse(self.f.taps)
 def test_location_two_original_patterns_no_touch(self):
  for name in ['016_P33','016_P34']:
   self.setUp();self.f.visible={name};self.assertEqual(self.e['EnterPartnerTrial'](),1);self.assertFalse(self.f.taps);self.assertFalse(self.swipes)
 def test_known_location_first_hit_preserves_anchor(self):
  self.f.visible={'016_P33'};self.assertTrue(self.e['PartnerTrialKnown']());self.assertEqual(self.f.lookups,['016_P33'])
 def test_hall_icon_original_click1500(self):
  for icon in ['016_P28','016_P29']:
   self.setUp();self.e['ReturnToHall']=lambda:1;self.f.visible={'016_P30',icon};self.f.after=lambda *a:setattr(self.f,'visible',{'016_P33'})
   self.assertEqual(self.e['EnterPartnerTrial'](),1);self.assertEqual(self.f.taps,[(600,900,1500)])
 def test_missing_trial_icon_original_slide_left(self):
  self.e['ReturnToHall']=lambda:1;self.f.visible={'016_P30'}
  def swipe(*a):self.swipes.append(a);self.f.visible={'016_P33'}
  self.e['Swipe']=swipe;self.assertEqual(self.e['EnterPartnerTrial'](),1);self.assertEqual(self.swipes,[(150,545,500,545,300)])
 def test_entry_unknown60seconds_no_blind_click(self):
  self.e['ReturnToHall']=lambda:1;self.assertEqual(self.e['EnterPartnerTrial'](),4);self.assertGreater(self.f.now,63000);self.assertFalse(self.f.taps);self.assertFalse(self.swipes);self.assertFalse(self.e['terminalConfirmed'])
 def test_return_hall_failure_stops_entry(self):
  self.e['ReturnToHall']=lambda:4;self.assertEqual(self.e['EnterPartnerTrial'](),4);self.assertFalse(self.f.taps);self.assertFalse(self.swipes)
 def test_scroll_original_vertical_direction_and_foreground_guard(self):
  self.assertTrue(self.e['PartnerTrialScrollDown']());self.assertEqual(self.swipes,[(370,1000,370,300,300)]);self.f.interrupt=True;self.assertFalse(self.e['PartnerTrialScrollDown']());self.assertEqual(len(self.swipes),1)
 def test_first_match_sweep_entry_result_short_circuit(self):
  for fn,name in [('PartnerSweepReady','016_P12'),('PartnerEntryIcon','016_P04'),('PartnerSweepResult','016_P26')]:
   self.setUp();self.f.visible={name};self.assertTrue(self.e[fn]());self.assertEqual(self.f.lookups,[name])
 def test_autotriple_original_priorities_offsets(self):
  for n,tap in [('016_AutoReady',None),('016_AutoOff',(290,1070,50)),('016_TripleOff',(918,992,50)),('016_BattleBase',(918,916,50))]:
   self.setUp();self.f.visible={n};self.assertEqual(self.e['PartnerAutoTriple'](),tap is None);self.assertEqual(self.f.taps,[] if tap is None else [tap])
 def battle(self,pattern,after=None):
  self.f.visible={'016_P04','016_P14'};self.f.text='1/2'
  def nextpage(x,y,w):
   if len(self.f.taps)==1:self.f.visible={'016_P14',pattern}
   elif (x,y)==(780,648):self.f.visible={pattern}
   elif after:after(x,y,w)
  self.f.after=nextpage
  return self.e['RunPartnerTrial']()
 def test_challenge_original_offset_and_failure_countable_exit(self):
  self.assertEqual(self.battle('016_P25'),1);self.assertEqual(self.f.taps,[(600,900,50),(780,648,500),(600,900,0)]);self.assertEqual(self.e['partnerReason'],'原战斗失败退出');self.assertEqual(self.e['partnerCount'],0)
 def test_two_victory_original_clicks_require_exact_title(self):
  for name,point in [('016_P22',(502,539,0)),('016_P24',(484,585,500))]:
   self.setUp()
   def after(x,y,w):self.f.visible=set();self.f.text='试炼'
   self.assertEqual(self.battle(name,after),1);self.assertEqual(self.f.taps[-1],point);self.assertEqual(self.ocr[-1],(65,7,247,59,0,0));self.assertEqual(self.e['partnerReason'],'原试炼标题返回')
 def test_blank_or_partial_return_title_not_success(self):
  for text in ['',None,'试 炼','试炼中']:
   self.setUp()
   def after(x,y,w,v=text):self.f.visible=set();self.f.text=v
   self.assertEqual(self.battle('016_P22',after),4);self.assertFalse(self.e['terminalConfirmed']);self.assertEqual(self.e['partnerCount'],0)
 def test_sweep_original500_and_result1000_then_title(self):
  for sweep in ['016_P12','016_P13']:
   for result in ['016_P26','016_P27']:
    self.setUp();self.f.visible={'016_P04',sweep};self.f.text='1/2'
    def after(x,y,w):
     if w==50:self.f.visible={sweep}
     elif w==500:self.f.visible={result}
     else:self.f.visible=set();self.f.text='试炼'
    self.f.after=after;self.assertEqual(self.e['RunPartnerTrial'](),1);self.assertEqual(self.f.taps,[(600,900,50),(600,900,500),(600,900,0)])
 def test_native20seconds_only_marks_continues_until_public_timeout(self):
  self.f.visible={'016_P04'};self.f.text='1/2';self.assertEqual(self.e['RunPartnerTrial'](),4);self.assertGreater(self.f.now,120000);self.assertFalse(self.e['partnerNativeTimeout']);self.assertFalse(self.e['terminalConfirmed']);self.assertEqual(self.e['partnerCount'],0)
 def test_after20seconds_late_challenge_overwrites_marker(self):
  self.f.visible={'016_P04'};self.f.text='1/2'
  def after(x,y,w):
   if (x,y)==(780,648):self.f.visible={'016_P25'}
   elif self.f.now>21000:self.f.visible={'016_P14'}
  self.f.after=after;self.assertEqual(self.e['RunPartnerTrial'](),1);self.assertGreater(self.f.now,21000);self.assertEqual(self.e['partnerReason'],'原战斗失败退出');self.assertFalse(self.e['partnerNativeTimeout'])
 def test_native35seconds_idle_boundary(self):
  def after(x,y,w):self.f.visible=set()
  self.assertEqual(self.battle('016_P22',after),4);self.assertGreater(self.f.now,35000);self.assertLess(self.f.now,38000);self.assertTrue(self.e['partnerNativeTimeout'])
 def test_startbattle_original_double_click_and_extra500wait(self):
  starts=[]
  def after(x,y,w):
   if (x,y)==(587,982):starts.append(self.f.now);self.f.visible={'016_P25'}
  self.assertEqual(self.battle('152_开战图标6',after),1);self.assertIn((398,982,500),self.f.taps);self.assertIn((587,982,500),self.f.taps);self.assertGreaterEqual(self.f.now-starts[0],1500)
 def test_missing_fighters_click_anchor_then_continue(self):
  def after(x,y,w):self.f.visible={'016_P25'}
  self.assertEqual(self.battle('032_少人提示',after),1);self.assertEqual(self.f.taps[-2:],[(600,900,0),(600,900,0)])
 def test_return_button_original_fixed_point_and1000wait(self):
  def after(x,y,w):
   if (x,y)==(502,539):self.f.visible={'016_P23'};self.f.text=''
   elif (x,y)==(128,1228):self.f.visible=set();self.f.text='试炼'
  self.assertEqual(self.battle('016_P22',after),1);self.assertIn((128,1228,1000),self.f.taps)
 def test_initial_business_timer_reset_excludes_entry_elapsed(self):
  self.f.now=60000;self.f.visible={'016_P04'};self.f.text='0/2';self.assertEqual(self.e['RunPartnerTrial'](),1);self.assertEqual(self.e['businessStarted'],60000)
 def test_scroll_only_strictly_after1500(self):
  times=[];self.e['Swipe']=lambda *a:times.append((self.f.now,a));self.e['businessLimit']=2000
  self.assertEqual(self.e['RunPartnerTrial'](),4);self.assertTrue(times);self.assertGreater(times[0][0],1500);self.assertEqual(times[0][1],(370,1000,370,300,300))
 def test_native300seconds_even_with_battle_timer_refresh(self):
  self.assertEqual(self.battle('016_AutoReady'),4);self.assertGreater(self.f.now,300000);self.assertLess(self.f.now,302000);self.assertTrue(self.e['partnerNativeTimeout']);self.assertFalse(self.e['terminalConfirmed'])
 def test_native_timeout_count65seconds_recovery_not_success(self):
  self.e.update(resumeTask=16);self.e['ConfirmPartnerExit']('native',3);stamp=self.e['partnerFinishedAt'];self.e['RecoverPartnerTask']()
  self.assertEqual((self.e['partnerCount'],self.e['partnerDue'],self.e['resumeTask']),(1,stamp+65,0));self.assertFalse(self.e['partnerDone']);self.assertFalse(self.e['terminalConfirmed'])
 def test_five_native_timeouts_abandoned_not_done(self):
  for i in range(5):self.e['ConfirmPartnerExit']('native',3);self.e['RecoverPartnerTask']()
  self.assertEqual(self.e['partnerCount'],5);self.assertTrue(self.e['partnerAbandoned']);self.assertFalse(self.e['partnerDone'])
 def test_foreground_recovery_no_count_no_reschedule(self):
  self.e.update(resumeTask=16);due=self.e['partnerDue'];self.e['RecoverPartnerTask']();self.assertEqual((self.e['partnerCount'],self.e['partnerDue'],self.e['resumeTask']),(0,due,16))
 def test_commit_requires_terminal_and_continuous_hall(self):
  load(['common/任务状态.mq'],self.e);self.e['SaveCurrentTask'](16)
  self.assertFalse(self.e['CommitTask'](True));self.e['ConfirmPartnerExit']('depleted',1);self.assertFalse(self.e['CommitTask'](False));self.assertFalse(self.e['partnerDone'])
  self.assertTrue(self.e['CommitTask'](True));self.assertTrue(self.e['partnerDone']);self.assertEqual(self.e['partnerCount'],0);self.assertEqual(self.e['currentTask'],0)
 def test_five_business_exits_complete_only_after_commit(self):
  load(['common/任务状态.mq'],self.e)
  for i in range(5):
   self.e['SaveCurrentTask'](16);self.e['ConfirmPartnerExit']('exit',4);self.assertEqual(self.e['partnerCount'],i);self.assertTrue(self.e['CommitTask'](True));self.assertEqual(self.e['partnerCount'],i+1)
  self.assertTrue(self.e['partnerDone']);self.assertFalse(self.e['partnerAbandoned'])
 def test_interruption_blocks_actions_and_terminal(self):
  self.f.interrupt=True
  for fn in ['EnterPartnerTrial','RunPartnerTrial','ExecutePartnerTrial']:self.assertEqual(self.e[fn](),4)
  self.assertEqual(self.e['ConfirmPartnerExit']('late',1),4);self.assertFalse(self.e['ResetPartnerTimer']());self.assertFalse(self.f.taps);self.assertFalse(self.swipes);self.assertFalse(self.e['terminalConfirmed'])
 def test_public_timeout_strict_greater_and_cannot_revive(self):
  self.f.now=120000;self.assertFalse(self.e['BusinessExpired']());self.f.now+=1;self.assertTrue(self.e['BusinessExpired']());self.assertFalse(self.e['ResetPartnerTimer']());self.assertEqual(self.e['businessStarted'],0)
 def test_foreground_resumes12_preserves_attempts(self):
  import test_foreground
  fg=test_foreground.Foreground();fg.setUp();fg.e.update(Time=lambda:1760000000,WorldLog=fg.logs.append,WorldStage=lambda s:None)
  load(['common/伙伴试炼状态.mq'],fg.e);fg.e['NewPartnerSession']();fg.e['SaveCurrentTask'](16);fg.request();self.assertTrue(fg.e['HandleForegroundRecovery']());self.assertEqual(fg.e['SelectDueTask'](),16);self.assertEqual((fg.e['partnerCount'],fg.e['partnerRecoveries'],fg.e['partnerRestarts']),(0,1,1))
 def test_ui_only_original_checkbox_and_all_defaults_false(self):
  def controls(t):return {re.search('名称:"([^"]+)"',b)[1]:(k,b) for k,b in re.findall(r'(输入框|下拉框|多选框):\{([^{}]+)\}',t)}
  old=controls((ROOT/'reports/伙伴试炼接入-20261017/before/ui/最小配置.uip').read_text('utf-8-sig'));now=controls((ROOT/'ui/最小配置.uip').read_text('utf-8-sig'));original=controls((E/'原界面配置.uip.txt').read_text('utf8').replace('点击响应:"函数名1",',''))
  self.assertEqual({k:now[k] for k in old},old);self.assertEqual(set(now)-set(old),{'SlHb'});self.assertEqual({k:now[k] for k in original},original);self.assertTrue(all('选中:false' in b for k,b in now.values() if k=='多选框'))
 def test_catalog_append_only23_and_exact_mq(self):
  before=json.loads((ROOT/'reports/伙伴试炼接入-20261017/before/evidence/图色参数.json').read_text('utf8'));now=json.loads((ROOT/'evidence/图色参数.json').read_text('utf8'));records=json.loads((E/'图色转换.json').read_text('utf8'));self.assertEqual(now,before+records);self.assertEqual(len(records),23)
  mq=(ROOT/'common/图色参数.mq').read_text('utf-8-sig')
  for r in records:
   args=', '.join(json.dumps(x) if isinstance(x,str) else str(x) for x in r['definition']);self.assertIn('Case "'+r['name']+'"\n        FindMultiColor '+args+', foundX, foundY',mq)
 def test_raw_partner_patterns_not_other_trial_profiles(self):
  allraw={r['name']:r for r in json.loads((E/'图色全表.json').read_text('utf8'))};records=json.loads((E/'图色转换.json').read_text('utf8'))
  for r in records:
   if r['name'].startswith('016_P'):self.assertEqual(r,allraw[r['name']])
  self.assertNotIn('016_P01',{r['name'] for r in records});self.assertEqual({r['definition'][6] for r in records},{1})
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
 def test_only_task16_no_new_engine_or_public_ownership(self):
  cfg=json.loads((ROOT/'project.json').read_text('utf8'));self.assertEqual(cfg['registeredTasks'].count(16),1)
  flow=(ROOT/'flows/016_伙伴试炼/伙伴试炼.mq').read_text('utf-8-sig');code='\n'.join(l for l in flow.splitlines() if not l.lstrip().startswith('//'));self.assertNotRegex(code,r'OcrEx|paddle|Image\.Ocr|KillApp|RunApp|CommitTask|SchedulerStep|businessStarted\s*=')
  names={r['name'] for r in json.loads((E/'图色转换.json').read_text('utf8'))}|{'152_开战图标6','032_少人提示'};self.assertTrue(set(re.findall('WorldMatch\\("([^"]+)"\\)',flow))<=names)
 def test_original_alternate_partner_entry_not_other_modes(self):
  self.f.visible={'016_P11'};self.assertTrue(self.e['PartnerEntryIcon']());self.assertEqual(self.f.lookups,['016_P04','016_P11'])
 def test_gray_end_independent_of_missing_ocr_no_click(self):
  self.f.visible={'016_P07'};self.assertEqual(self.e['RunPartnerTrial'](),1);self.assertEqual(self.e['partnerExitKind'],5);self.assertFalse(self.f.taps);self.assertFalse(self.e['partnerDone']);self.assertEqual(self.e['partnerCount'],0)
 def test_gray_end_hall_gate_no_count_no65seconds(self):
  load(['common/任务状态.mq'],self.e);self.e['SaveCurrentTask'](16);due=self.e['partnerDue'];self.f.visible={'016_P07'};self.assertEqual(self.e['RunPartnerTrial'](),1);self.assertFalse(self.e['CommitTask'](False));self.assertFalse(self.e['partnerDone']);self.assertTrue(self.e['CommitTask'](True));self.assertTrue(self.e['partnerDone']);self.assertEqual((self.e['partnerCount'],self.e['partnerDue']),(0,due))
 def test_empty_initial_ocr_does_not_open_challenge(self):
  self.f.visible={'016_P04','016_P14'};self.f.text='';self.assertEqual(self.e['RunPartnerTrial'](),4);self.assertFalse(self.f.taps);self.assertFalse(self.e['terminalConfirmed']);self.assertFalse(self.e['partnerNativeTimeout'])
 def test_valid_exhaustion_before_gray_branch(self):
  self.f.visible={'016_P04','016_P07'};self.f.text='0/2';self.assertEqual(self.e['RunPartnerTrial'](),1);self.assertEqual(self.e['partnerExitKind'],1);self.assertNotIn('016_P07',self.f.lookups)
 def test_partner_cooldown_accepts_bare00(self):
  self.f.visible={'016_P04'};self.f.text='00';self.assertEqual(self.e['RunPartnerTrial'](),1);self.assertEqual(self.e['partnerExitKind'],2);self.assertEqual(self.e['partnerCount'],0)
 def test_no_gene_special_branch_or_wrong_ocr_region(self):
  t=(ROOT/'flows/016_伙伴试炼/伙伴试炼.mq').read_text('utf-8-sig');self.assertNotRegex(t,r'012_|013_|014_|015_|SlJb|SlJyan|SlLh|SlJyin|Gene|Rapid|Pick|016_P(?:15|16|17|18|19|20|21)')
  self.assertIn('WorldText(ax - 410, ay + 30, ax - 350, ay + 70)',t);self.assertIn('InStr(1, text, "00")',t)
 def test_commit_and_recovery_isolate_previous_four_states(self):
  keys=['goldCount','experienceCount','soulCount','geneCount','goldDue','experienceDue','soulDue','geneDue'];values=[1,2,3,4,11,22,33,44];self.e.update(dict(zip(keys,values)));load(['common/任务状态.mq'],self.e);self.e['SaveCurrentTask'](16);self.e['ConfirmPartnerExit']('exit',4);self.assertTrue(self.e['CommitTask'](True));self.e['RecoverPartnerTask']();self.assertEqual([self.e[k] for k in keys],values)
 def test_all_five_trial_priority_and_partner_resume(self):
  import test_foreground
  fg=test_foreground.Foreground();fg.setUp();fg.e.update(Time=lambda:1760000000,WorldLog=fg.logs.append,WorldStage=lambda s:None)
  load(['common/金币试炼状态.mq','common/经验试炼状态.mq','common/龙魂试炼状态.mq','common/基因试炼状态.mq','common/伙伴试炼状态.mq'],fg.e)
  for name in ['NewGoldSession','NewExperienceSession','NewSoulSession','NewGeneSession','NewPartnerSession','RegisterTasks']:fg.e[name]()
  names=['gold','experience','soul','gene','partner'];fg.e.update({n+'Enabled':True for n in names});fg.e['resumeTask']=0
  for task,name in zip([12,13,14,15,16],names):self.assertEqual(fg.e['SelectDueTask'](),task);fg.e[name+'Done']=True
  fg.e.update(resumeTask=16,goldDone=False);self.assertEqual(fg.e['SelectDueTask'](),16)
 def test_only_partner16_added_no_future_trial(self):
  cfg=json.loads((ROOT/'project.json').read_text('utf8'));old=json.loads((ROOT/'reports/伙伴试炼接入-20261017/before/project.json').read_text('utf8'));self.assertEqual(cfg['registeredTasks'],old['registeredTasks']+[16]);self.assertEqual(cfg['modules'],old['modules']+['common/伙伴试炼状态.mq','flows/016_伙伴试炼/伙伴试炼.mq'])
 def test_recovery_restart_logs_keep_task16(self):
  self.e['RecoverPartnerTask']();self.e['RestartPartnerTask']();text='\n'.join(self.f.logs);self.assertIn('保留16',text);self.assertIn('公共重启恢复16',text);self.assertNotRegex(text,r'(?:保留|恢复)(?:14|15)')
if __name__=='__main__':unittest.main()


