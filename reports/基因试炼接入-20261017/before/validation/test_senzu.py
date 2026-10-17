import unittest,json,re
from mq_subset import ROOT,load
import test_worldboss

class SenzuTests(unittest.TestCase):
 def setUp(self):
  self.f=test_worldboss.WorldBossTests();self.f.setUp();self.e=self.f.e
  def match(n):self.f.now+=10;return self.f.match(n)
  self.e.update(MatchPattern=match,currentTask=153,businessStarted=0,businessLimit=120000,ForegroundInterrupted=lambda:self.f.interrupt)
  load(['common/悟空送仙豆状态.mq','flows/153_悟空送仙豆/悟空送仙豆.mq','common/运行计时.mq'],self.e)
  self.e['NewSenzuSession']()
 def test_config_exact_single_default_off(self):
  self.e['ReadUIConfig']=lambda k,d:d;self.e['LoadSenzuSettings']();self.assertFalse(self.e['senzuEnabled'])
  self.e['ReadUIConfig']=lambda k,d:'true' if k=='日常_悟空送仙豆' else d
  self.e['LoadSenzuSettings']();self.assertEqual(self.e['SelectSenzu'](),153)
 def test_assist_five_refreshes_then_persistent_off(self):
  self.f.visible={'153_P00'};self.assertEqual(self.e['AssistSenzu'](),1)
  self.assertEqual(self.f.taps,[(1037,798,0)]*5);self.assertFalse(self.e['senzuAssist'])
  self.e['RecoverSenzuTask']();self.e['StartSenzuTask']();self.assertFalse(self.e['senzuAssist']);self.assertEqual(self.e['senzuCount'],0)
 def test_assist_list_fifth_then_exit(self):
  self.f.visible={'153_协助列表二'};self.assertEqual(self.e['AssistSenzu'](),1)
  self.assertEqual(self.f.taps,[(600,900,0)]*5)
 def test_super_requires_armed_and_exact80_anchor(self):
  self.f.visible={'153_P05','153_P06'}
  self.f.after=lambda *a:setattr(self.f,'interrupt',len(self.f.taps)>=81)
  self.assertEqual(self.e['AssistSenzu'](),4)
  self.assertEqual(self.f.taps,[(312,1613,1000)]+[(312,1613,20)]*80)
 def test_unarmed_super_not_clicked(self):
  self.f.visible={'153_P06'};self.e['AssistSenzu']();self.assertFalse(self.f.taps)
 def test_assist_unknown_never_completed(self):
  self.assertEqual(self.e['AssistSenzu'](),4);self.assertFalse(self.e['terminalConfirmed'])
 def test_transport_five_refreshes_original_stop_count_only_after_commit(self):
  self.f.visible={'153_P13'};self.assertEqual(self.e['TransportSenzu'](),1)
  self.assertEqual(self.f.taps,[(584,582,0)]*5);self.assertTrue(self.e['terminalConfirmed']);self.assertEqual(self.e['senzuCount'],0)
  self.e['CommitSenzuTask']();self.assertEqual(self.e['senzuCount'],3);self.assertTrue(self.e['senzuDone'])
 def test_unchecked_and_checked_not_confused(self):
  self.f.visible={'153_P12'};self.f.after=lambda *a:setattr(self.f,'interrupt',True)
  self.e['TransportSenzu']();self.assertEqual(self.f.taps,[(80,600,250)]);self.assertFalse(self.e['terminalConfirmed'])
 def test_one_key_formation_order(self):
  self.f.visible={'153_P17'};self.f.after=lambda *a:setattr(self.f,'interrupt',len(self.f.taps)>=2)
  self.e['TransportSenzu']();self.assertEqual(self.f.taps,[(140,1100,500),(360,1100,250)])
 def test_transport_consumption_is_phase_exit_not_complete(self):
  self.f.visible={'153_消费石头二'};self.assertEqual(self.e['TransportSenzu'](),1)
  self.assertFalse(self.e['terminalConfirmed']);self.assertFalse(self.f.taps)
 def test_finish_consumption_close_then_exact_page(self):
  self.f.visible={'153_消费石头一','153_P00'};self.assertEqual(self.e['FinishSenzu'](),1)
  self.assertEqual(self.f.taps,[(600,900,50)]);self.assertTrue(self.e['terminalConfirmed'])
 def test_normal_one_hour_due_and_strict_count(self):
  self.e['senzuEnabled']=True
  for n in range(1,5):
   self.e['senzuFinishedAt']=self.e['Time']();self.e['CommitSenzuTask']()
   self.assertEqual(self.e['senzuCount'],n);self.assertEqual(self.e['senzuDone'],n>3)
   self.assertEqual(self.e['SelectSenzu'](),0)
   self.f.stamp+=3600
   self.assertEqual(self.e['SelectSenzu'](),0 if n>3 else 153)
 def test_finish_fourth_waits1000_before_exit(self):
  self.e['senzuCount']=3;self.f.visible={'153_P00'};self.assertEqual(self.e['FinishSenzu'](),1);self.assertGreaterEqual(self.f.now,1000)
 def test_unknown_final_does_not_complete_or_click(self):
  self.assertEqual(self.e['FinishSenzu'](),4);self.assertFalse(self.e['terminalConfirmed']);self.assertFalse(self.f.taps)
 def test_entry_page_direct_no_blind_click(self):
  self.f.visible={'153_P00'};self.assertEqual(self.e['EnterSenzu'](),1);self.assertFalse(self.f.taps)
 def test_entry_gated_by_hall_and_two_seconds(self):
  self.f.visible={'153_大厅一','153_入口'}
  def after(*a):self.f.visible={'153_P00'}
  self.f.after=after;self.assertEqual(self.e['EnterSenzu'](),1);self.assertGreater(self.f.now,2000);self.assertEqual(self.f.taps,[(600,900,0)])
 def test_entry_unknown60sec_not_false_completion(self):
  self.assertEqual(self.e['EnterSenzu'](),4);self.assertGreater(self.f.now,62000);self.assertFalse(self.e['terminalConfirmed'])
 def test_shared_commit_hall_and_foreground_gates(self):
  load(['common/任务状态.mq','common/任务注册.mq'],self.e)
  self.e['SaveCurrentTask'](153);self.assertEqual(self.e['SelectDueTask'](),153)
  self.assertFalse(self.e['CommitTask'](True));self.e['ConfirmSenzuExit']('test',False)
  self.assertFalse(self.e['CommitTask'](False));self.assertTrue(self.e['CommitTask'](True));self.assertEqual(self.e['senzuCount'],1)
 def test_foreground_recovery_routes153(self):
  import test_foreground
  fg=test_foreground.Foreground();fg.setUp();fg.e.update(Time=lambda:1760000000,CStr=str,WorldLog=fg.logs.append,WorldStage=lambda s:None)
  load(['common/悟空送仙豆状态.mq'],fg.e)
  fg.e['NewSenzuSession']();fg.e['SaveCurrentTask'](153);fg.request()
  self.assertTrue(fg.e['HandleForegroundRecovery']());self.assertEqual(fg.e['SelectDueTask'](),153)
  self.assertEqual((fg.e['senzuCount'],fg.e['senzuRestarts'],fg.e['senzuRecoveries']),(0,1,1))
 def test_26_records_exact_and_no_new_apis(self):
  records=json.loads((ROOT/'flows/153_悟空送仙豆/evidence/图色转换.json').read_text('utf8'));self.assertEqual(len(records),26)
  catalog=json.loads((ROOT/'evidence/图色参数.json').read_text('utf8'));self.assertEqual([r for r in catalog if r['name'].startswith('153_')],records)
  flow=(ROOT/'flows/153_悟空送仙豆/悟空送仙豆.mq').read_text('utf-8-sig');self.assertNotRegex(flow,r'OcrEx|paddle|Image\.Ocr|CommitTask|KillApp|RunApp')
 def test_daily_single_checkbox_off_and_other_controls_preserved(self):
  ui=(ROOT/'ui/最小配置.uip').read_text('utf-8-sig');self.assertEqual(ui.count('名称:"日常_悟空送仙豆"'),1)
  self.assertIn('名称:"日常_悟空送仙豆",提示内容:"悟空送仙豆",选中:false',ui)
  self.assertLess(ui.index('日常功能:{'),ui.index('名称:"日常_悟空送仙豆"'))
 def test_catalog_append_only_and_original_raw_colors(self):
  before=json.loads((ROOT/'reports/悟空送仙豆接入-20261017/before/图色参数.json').read_text('utf8'))
  now=[r for r in json.loads((ROOT/'evidence/图色参数.json').read_text('utf8')) if not r['name'].startswith(('014_','013_','012_','150_','155_','154_'))]
  self.assertEqual(now[:-26],before)
  raw=(ROOT/'flows/153_悟空送仙豆/evidence/root711静态重建.txt').read_text('utf8')
  colors=re.findall(r'L\d+_1 = "([0-9A-F]{6}-[0-9A-F]{6})"\n\s*L\d+_1 = "([^"\n]+)"',raw)
  unique=list(dict.fromkeys(colors))
  self.assertEqual([(r['definition'][4],r['definition'][5]) for r in now[-26:-4]],unique)
 def test_business_integration_and_built_artifacts_unchanged(self):
  backup=ROOT/'reports/悟空送仙豆接入-20261017/before'
  cfg=json.loads((ROOT/'project.json').read_text('utf8'));old=json.loads((backup/'project.json').read_text('utf8'))
  self.assertEqual([t for t in cfg['registeredTasks'] if t not in (14,13,12,150,154,155)],old['registeredTasks']+[153])
  self.assertEqual([p for p in cfg['modules'] if p not in ['common/龙魂试炼状态.mq','flows/014_龙魂试炼/龙魂试炼.mq','common/经验试炼状态.mq','flows/013_经验试炼/经验试炼.mq','common/金币试炼状态.mq','flows/012_金币试炼/金币试炼.mq','common/龙珠大冒险状态.mq','flows/150_龙珠大冒险/龙珠大冒险.mq','common/种仙豆状态.mq','flows/154_种仙豆/种仙豆.mq','common/蛇道状态.mq','flows/155_蛇道/蛇道.mq']],old['modules']+['common/悟空送仙豆状态.mq','flows/153_悟空送仙豆/悟空送仙豆.mq'])
 def test_consumption_exit_wins_over_fifth_refresh(self):
  self.f.visible={'153_P13'}
  def after(*a):
   if len(self.f.taps)==5:self.f.visible.add('153_消费石头一')
  self.f.after=after;self.assertEqual(self.e['TransportSenzu'](),1)
  self.assertFalse(self.e['terminalConfirmed']);self.assertFalse(self.e['senzuStop'])
 def test_config_keys_options_and_all_previous_controls_unchanged(self):
  def controls(t):return {re.search('名称:"([^"]+)"',body)[1]:(kind,body) for kind,body in re.findall(r'(输入框|下拉框|多选框):\{([^{}]+)\}',t)}
  before=controls((ROOT/'reports/悟空送仙豆接入-20261017/before/ui/最小配置.uip').read_text('utf-8-sig'))
  after=controls((ROOT/'ui/最小配置.uip').read_text('utf-8-sig'))
  self.assertEqual({k:after[k] for k in before},before)
  self.assertEqual(set(after)-set(before),{'SlLh','SlJyan','SlJb','日常_悟空送仙豆','日常_种仙豆','Lzdmx','Lzdmx许愿'} | {'日常_蛇道_困难关卡', '日常_蛇道_跳过动画', '日常_蛇道_普通关卡', '日常_蛇道_补打', '日常_蛇道_特殊效果', '日常_蛇道', '日常_蛇道_雇佣战士_个', '日常_蛇道_时间', '日常_蛇道_分钟', '日常_蛇道_雇佣战士_位置', '日常_蛇道_模式', '日常_蛇道_失败次数', '日常_蛇道_雇佣战士_行'})
 def test_all_named_matches_exist_and_preserve_mq_definitions(self):
  records=json.loads((ROOT/'flows/153_悟空送仙豆/evidence/图色转换.json').read_text('utf8'));names={r['name'] for r in records}
  flow=(ROOT/'flows/153_悟空送仙豆/悟空送仙豆.mq').read_text('utf-8-sig')
  for name in re.findall(r'WorldMatch\("([^"]+)"\)',flow):self.assertIn(name,names)
  for name in re.findall(r'WorldPair\("([^"]+)"\)',flow):self.assertTrue({name+'一',name+'二'}.issubset(names))
  mq=(ROOT/'common/图色参数.mq').read_text('utf-8-sig')
  for r in records:
   case=re.search('Case "'+r['name']+'"(.*?)(?=\n    Case |\n    End Select)',mq,re.S)[1]
   self.assertIn('FindMultiColor '+', '.join(json.dumps(v) for v in r['definition'])+', foundX, foundY',case)
 def test_no_late_reset_after_expiry_or_foreground_interrupt(self):
  self.f.now=120001;self.assertFalse(self.e['ResetSenzuTimer']());self.assertEqual(self.e['businessStarted'],0)
  self.f.now=0;self.f.interrupt=True;self.assertFalse(self.e['ResetSenzuTimer']())
