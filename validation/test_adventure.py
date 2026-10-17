import unittest,json,re,hashlib
from mq_subset import ROOT,load
import test_worldboss
E=ROOT/'flows/150_龙珠大冒险/evidence'
class AdventureTests(unittest.TestCase):
 def setUp(self):
  self.f=test_worldboss.WorldBossTests();self.f.setUp();self.e=self.f.e
  def match(n):self.f.now+=10;return self.f.match(n)
  self.e.update(MatchPattern=match,currentTask=150,businessStarted=0,businessLimit=120000,ForegroundInterrupted=lambda:self.f.interrupt,ReadUIConfig=lambda k,d:d)
  load(['common/龙珠大冒险状态.mq','flows/150_龙珠大冒险/龙珠大冒险.mq','common/运行计时.mq'],self.e)
  self.e['LoadAdventureSettings']();self.e['NewAdventureSession']();self.e.update(advFailures=0,advDirection=0,advCloseTen=False)
 def test_two_original_controls_defaults(self):
  keys=[];self.e['ReadUIConfig']=lambda k,d:keys.append(k) or d;self.e['LoadAdventureSettings']()
  self.assertEqual(keys,['Lzdmx','Lzdmx许愿']);self.assertFalse(self.e['advEnabled']);self.assertEqual(self.e['advReward'],2)
 def test_reward_bounds_and_original_six_choices(self):
  for raw in [0,1,2,3,4,5]:
   self.e['ReadUIConfig']=lambda k,d,v=raw:v if k=='Lzdmx许愿' else False;self.e['LoadAdventureSettings']();self.assertEqual(self.e['advReward'],raw)
  for raw in [None,'bad',6,-1]:
   self.e['ReadUIConfig']=lambda k,d,v=raw:v if k=='Lzdmx许愿' else False;self.e['LoadAdventureSettings']();self.assertEqual(self.e['advReward'],2)
 def test_immediate_enabled_only(self):
  self.assertEqual(self.e['SelectAdventure'](),0);self.e['advEnabled']=True;self.assertEqual(self.e['SelectAdventure'](),150)
 def test_entry_actual_main_or_wish_page(self):
  for name in ['150_P00','150_P01']:
   self.setUp();self.f.visible={name};self.assertEqual(self.e['EnterAdventure'](),1);self.assertFalse(self.f.taps)
 def test_entry_original_icon_offset1500(self):
  self.f.visible={'150_P52','150_P50'};self.f.after=lambda *a:setattr(self.f,'visible',{'150_P00'})
  self.assertEqual(self.e['EnterAdventure'](),1);self.assertEqual(self.f.taps,[(471,792,1500)])
 def test_entry_unknown60seconds_not_complete(self):
  self.e['ReturnToHall']=lambda:1;self.assertEqual(self.e['EnterAdventure'](),4);self.assertGreater(self.f.now,62000);self.assertFalse(self.e['terminalConfirmed']);self.assertFalse(self.f.taps)
 def test_direction0to4_names(self):
  for direction in range(5):
   self.setUp();name='150_P12' if direction==0 else f'150_P12D{direction}';self.f.visible={name};self.assertTrue(self.e['AdventureFindEvent'](direction));self.assertEqual(self.f.lookups,[name])
 def test_random_answer_original_three_offsets(self):
  for rnd,dy in [(0,33),(.34,156),(.99,277)]:
   self.setUp();self.e['Rnd']=lambda v=rnd:v;self.e.update(foundX=50,foundY=100);self.assertEqual(self.e['AdventureAnswer'](),1);self.assertEqual(self.f.taps,[(50,100+dy,0)])
 def test_bricks24_original_points_double_vs_single(self):
  points=[(48,372),(167,292),(286,218),(417,303),(533,384),(407,460),(535,535),(416,610),(536,690),(410,760),(535,836),(416,905),(300,980),(170,910),(52,828),(167,758),(45,673),(175,600),(45,525),(180,450),(295,377),(300,535),(295,685),(290,830)]
  for ten in [True,False]:
   self.setUp();self.e.update(foundX=10,foundY=20);self.assertEqual(self.e['AdventureBricks'](ten),1)
   self.assertEqual(self.f.taps,[(10,20,4500)]+[(10+x,20+y,0) for x,y in points for _ in range(2 if ten else 1)])
   self.assertEqual(self.f.now,5460)
 def test_event_ten_single_different_clicks(self):
  cases=[('150_P15',(165,800,1000),(600,900,5000)),('150_P20',(600,900,0),(100,50,0)),('150_P22',(150,50,0),(100,50,0)),('150_P23',(150,50,0),(600,900,0)),('150_P24',(150,50,0),(600,900,0))]
  for name,tenTap,singleTap in cases:
   for ten,want in [(True,tenTap),(False,singleTap)]:
    self.setUp();self.f.visible={name};self.assertEqual(self.e['AdventureMiniEvents'](ten),1);self.assertEqual(self.f.taps,[want])
 def test_remaining_simple_event_offsets(self):
  for name,ten,tap in [('150_P13',True,(600,900,0)),('150_P14',True,(510,780,5000)),('150_P32',False,(600,900,0)),('150_P16',False,(100,50,0)),('150_P17',True,(600,900,0)),('150_P18',False,(600,900,0)),('150_P19',True,(332,1021,0)),('150_P21',True,(600,900,0)),('150_P33',False,(600,900,0))]:
   self.setUp();self.f.visible={name};self.e['advFailures']=4;self.assertEqual(self.e['AdventureMiniEvents'](ten),1);self.assertEqual(self.f.taps,[tap]);self.assertEqual(self.e['advFailures'],0)
 def test_upgrade_timer_difference_ten_single(self):
  for name in ['150_P27','150_P28','150_P29']:
   for ten in [True,False]:
    self.setUp();self.f.visible={name};self.e['advFailures']=4;self.e['AdventureMiniEvents'](ten)
    self.assertEqual(self.f.taps,[(600,900,0)]);self.assertEqual(self.e['advFailures'],0);self.assertEqual(self.e['businessStarted']>0,not ten)
 def test_ten_close_cycles_direction_and_failure_counter(self):
  self.f.visible={'150_P30'}
  for i in range(1,7):self.e['AdventureMiniEvents'](True);self.assertEqual(self.e['advDirection'],i%5);self.assertEqual(self.e['advFailures'],i)
 def test_single_close_does_not_increment_or_clear_counter(self):
  self.f.visible={'150_P34'};self.e['advFailures']=4;self.e['AdventureMiniEvents'](False);self.assertEqual(self.e['advFailures'],4);self.assertEqual(self.e['advDirection'],0)
 def test_ten5failures_is_close_flag_not_completion(self):
  self.f.visible={'150_P30'};self.assertEqual(self.e['AdventureTenEvents'](),1);self.assertTrue(self.e['advCloseTen']);self.assertFalse(self.e['terminalConfirmed']);self.assertEqual(self.e['advFailures'],5)
 def test_ten_event_selected_exact_region_template_anchor(self):
  self.f.visible={'150_P10','150_P12'}
  self.f.after=lambda *a:setattr(self.f,'visible',{'150_P06'})
  self.assertEqual(self.e['AdventureTenEvents'](),1);self.assertEqual(self.f.taps,[(600,750,0)])
 def test_ten_unknown_public_timeout_no_close_success(self):
  self.assertEqual(self.e['AdventureTenEvents'](),4);self.assertFalse(self.e['advCloseTen']);self.assertFalse(self.e['terminalConfirmed'])
 def test_first_cleanup_requires_claimed_before_main_exit(self):
  self.f.visible={'150_P00'}
  def after(x,y,w):self.f.visible={'150_P41'} if len(self.f.taps)==1 else {'150_P00'}
  self.f.after=after;self.assertEqual(self.e['AdventureClaimItems'](),1);self.assertEqual(self.f.taps,[(330,1120,500),(852,810,500)])
 def test_first_cleanup42_sets_claimed(self):
  self.f.visible={'150_P42'};self.f.after=lambda *a:setattr(self.f,'visible',{'150_P00'})
  self.assertEqual(self.e['AdventureClaimItems'](),1);self.assertEqual(self.f.taps,[(600,900,500)])
 def test_two_cleanup_unknowns_never_succeed(self):
  for fn in ['AdventureClaimItems','AdventureClaimMilestones']:
   self.setUp();self.assertEqual(self.e[fn](),4);self.assertFalse(self.e['terminalConfirmed']);self.assertFalse(self.f.taps)
 def test_second_cleanup_hall_only_no_click(self):
  for name in ['150_P45','150_P46']:
   self.setUp();self.f.visible={name};self.assertEqual(self.e['AdventureClaimMilestones'](),1);self.assertFalse(self.f.taps)
 def test_second_cleanup_original_claim_and_navigation(self):
  self.f.visible={'150_P43'}
  def after(x,y,w):self.f.visible={'150_P47'} if len(self.f.taps)==1 else {'150_P43'} if len(self.f.taps)==2 else {'150_P46'}
  self.f.after=after;self.assertEqual(self.e['AdventureClaimMilestones'](),1);self.assertEqual(self.f.taps,[(80,130,500),(636,760,500),(108,1211,500)])
 def test_native_purchase_page_exits_without_buying(self):
  self.f.visible={'150_P00','150_P40'};self.e['AdventureClaimItems']=lambda:1;self.e['AdventureClaimMilestones']=lambda:1
  self.assertEqual(self.e['RunAdventure'](),1);self.assertFalse(self.f.taps);self.assertFalse(self.e['terminalConfirmed'])
 def test_wish_requires_original_pending_gate_and6offsets(self):
  for reward,(dx,dy) in enumerate([(0,0),(192,0),(382,0),(0,300),(192,300),(382,300)]):
   self.setUp();self.e['advReward']=reward;self.f.visible={'150_P01'}
   self.e['AdventureClaimItems']=lambda:1;self.e['AdventureClaimMilestones']=lambda:1
   def after(x,y,w):self.f.visible={'150_P38'} if len(self.f.taps)==1 else {'150_P40'}
   self.f.after=after;self.assertEqual(self.e['RunAdventure'](),1);self.assertEqual(self.f.taps,[(600,900,0),(600+dx,900+dy,0)])
  self.setUp();self.f.visible={'150_P00','150_P38','150_P40'};self.e['AdventureClaimItems']=lambda:1;self.e['AdventureClaimMilestones']=lambda:1
  self.assertEqual(self.e['RunAdventure'](),1);self.assertFalse(self.f.taps)
 def test_ball_confirmation_gate(self):
  self.f.visible={'150_P00','150_P36','150_P37','150_P40'};self.e['AdventureClaimItems']=lambda:1;self.e['AdventureClaimMilestones']=lambda:1
  self.assertEqual(self.e['RunAdventure'](),1);self.assertFalse(self.f.taps)
 def test_full_chain_pending_then_public_hall_commit8hours(self):
  load(['common/任务状态.mq'],self.e);self.e['SaveCurrentTask'](150);self.f.visible={'150_P00','150_P40'}
  def after(x,y,w):
   if (x,y)==(330,1120):self.f.visible={'150_P41'}
   elif (x,y)==(852,810):self.f.visible={'150_P00','150_P46'}
  self.f.after=after;self.assertEqual(self.e['ExecuteAdventure'](),1);self.assertTrue(self.e['terminalConfirmed']);self.assertEqual(self.e['advCount'],0)
  self.assertFalse(self.e['CommitTask'](False));finished=self.e['advFinishedAt'];self.assertTrue(self.e['CommitTask'](True));self.assertEqual(self.e['advDue'],finished+28800);self.assertEqual(self.e['advCount'],1);self.assertFalse(self.e['advDone'])
 def test_no_arbitrary_permanent_done_after_multiple_runs(self):
  self.e.update(advEnabled=True,advFinishedAt=self.e['Time']())
  for i in range(4):self.e['CommitAdventureTask']()
  self.assertFalse(self.e['advDone']);self.assertEqual(self.e['advCount'],4);self.assertEqual(self.e['SelectAdventure'](),0);self.f.stamp+=28800;self.assertEqual(self.e['SelectAdventure'](),150)
 def test_interruption_no_click_no_commit_or_timer_revival(self):
  self.f.interrupt=True
  for fn in ['EnterAdventure','RunAdventure','AdventureTenEvents','AdventureClaimItems','AdventureClaimMilestones']:
   self.assertEqual(self.e[fn](),4)
  self.assertEqual(self.e['ConfirmAdventureExit']('late'),4);self.assertFalse(self.e['ResetAdventureTimer']());self.assertFalse(self.f.taps);self.assertFalse(self.e['terminalConfirmed'])
 def test_foreground_recovers_task150_not151(self):
  import test_foreground
  fg=test_foreground.Foreground();fg.setUp();fg.e.update(Time=lambda:1760000000,WorldLog=fg.logs.append,WorldStage=lambda s:None,advReward=2)
  load(['common/龙珠大冒险状态.mq'],fg.e);fg.e['NewAdventureSession']();fg.e['SaveCurrentTask'](150);fg.request()
  self.assertTrue(fg.e['HandleForegroundRecovery']());self.assertEqual(fg.e['SelectDueTask'](),150);self.assertEqual((fg.e['advCount'],fg.e['advRecoveries'],fg.e['advRestarts']),(0,1,1))
 def test_ui_original2controls_all_previous_unchanged(self):
  def controls(t):return {re.search('名称:"([^"]+)"',body)[1]:(kind,body) for kind,body in re.findall(r'(输入框|下拉框|多选框):\{([^{}]+)\}',t)}
  before=controls((ROOT/'reports/龙珠大冒险接入-20261017/before/ui/最小配置.uip').read_text('utf-8-sig'));now=controls((ROOT/'ui/最小配置.uip').read_text('utf-8-sig'));original=controls((E/'原界面配置.uip.txt').read_text('utf8'))
  self.assertEqual({k:now[k] for k in before},before);self.assertEqual(set(now)-set(before),{'SlYsk','SlYsk挑战时长','SlYsk间隔','SlHb','SlJyin','SlLh','SlJyan','SlJb','Lzdmx','Lzdmx许愿'});self.assertEqual({k:now[k] for k in original},original)
  self.assertTrue(all('选中:false' in body for kind,body in now.values() if kind=='多选框'))
 def test_catalog_append_only58_and_mqexact(self):
  before=json.loads((ROOT/'reports/龙珠大冒险接入-20261017/before/evidence/图色参数.json').read_text('utf8'));now=json.loads((ROOT/'evidence/图色参数.json').read_text('utf8'));records=json.loads((E/'图色转换.json').read_text('utf8'))
  self.assertEqual([r for r in now if not r['name'].startswith(('092_','016_','015_','014_','013_','012_'))],before+records);self.assertEqual(len(records),58);mq=(ROOT/'common/图色参数.mq').read_text('utf-8-sig')
  for r in records:
   args=', '.join(json.dumps(x) if isinstance(x,str) else str(x) for x in r['definition']);self.assertIn('Case "'+r['name']+'"\n        FindMultiColor '+args+', foundX, foundY',mq)
 def test_raw_every_call_region_color_similarity_and_dynamic_direction(self):
  by={r['name']:r['definition'] for r in json.loads((E/'图色转换.json').read_text('utf8'))}
  for c in json.loads((E/'调用位置.json').read_text('utf8')):
   name='root709静态重建.txt' if c['source']=='root.709' else 'root787入口分支.txt';lines=(E/name).read_text('utf8').splitlines();i=c['line']-1
   region=[int(re.search(r'= (\d+)$',line)[1]) for line in lines[i-4:i]]
   if region==[0,0,0,0]:region=[0,0,719,1279]
   else:region[2]=min(region[2],719);region[3]=min(region[3],1279)
   literal=lambda line:re.search(r'= "(.*)"$',line)[1]
   self.assertEqual(by[c['name']][:6],region+[literal(lines[i]),literal(lines[i+1])]);sim=re.search(r'= (0\.\d+)$',lines[i+3]);self.assertEqual(by[c['name']][7],float(sim[1]) if sim else .9)
  self.assertEqual([by['150_P12' if d==0 else f'150_P12D{d}'][6] for d in range(5)],list(range(5)))
 def test_unique150_registration_and_no_new_engine_or_public_ownership(self):
  cfg=json.loads((ROOT/'project.json').read_text('utf8'));self.assertEqual(cfg['registeredTasks'].count(150),1)
  flow=(ROOT/'flows/150_龙珠大冒险/龙珠大冒险.mq').read_text('utf-8-sig');self.assertNotRegex(flow,r'OcrEx|paddle|Image\.Ocr|KillApp|RunApp|CommitTask|SchedulerStep|businessStarted\s*=|600000')
  names={r['name'] for r in json.loads((E/'图色转换.json').read_text('utf8'))}
  self.assertTrue(set(re.findall('WorldMatch\\("([^"]+)"\\)',flow))<=names)

if __name__=='__main__':unittest.main()
