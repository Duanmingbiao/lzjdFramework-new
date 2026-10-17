from historical_source import before_foreground
"""Run actual MQ control flow under mocked recognition; not an official compiler/device test."""
from pathlib import Path
import unittest,json,hashlib,re
from mq_subset import load
R=Path(__file__).resolve().parents[1]
E=R/'flows/169_领任务奖励/evidence'
MODULE='flows/169_领任务奖励/领任务奖励.mq'

class RewardFlow(unittest.TestCase):
 def setUp(self):
  self.now=1000;self.events=[];self.lookups=[];self.visible=set();self.after=lambda x,y,w:None
  self.e={}
  load(['common/任务状态.mq','common/运行计时.mq',MODULE],self.e)
  self.e.update(TickCount=lambda:self.now,Delay=self.delay,TouchPoint=self.touch,MatchPattern=self.match,
   Note=lambda m:None,SetStage=lambda m:None,RESULT_OK=1,RESULT_WAIT=2,RESULT_FAIL=3,RESULT_TIMEOUT=4,
   businessLimit=60000,loginLimit=600000)
  self.e['NewSession']();self.e['businessStarted']=self.now
 def delay(self,n):self.now+=n
 def match(self,name):
  self.lookups.append(name);self.e['foundX']=400;self.e['foundY']=1100
  return name in self.visible
 def touch(self,x,y,w):self.events.append((x,y,w));self.delay(w);self.after(x,y,w)
 def only(self,name):self.visible={name}
 def test_candidate_two_is_fallback_and_anchor_is_preserved(self):
  for func,kind in [('RewardGrowthClaimable','成长有奖'),('RewardGrowthEmpty','成长无奖'),('RewardDailyClaimable','日常有奖'),('RewardDailyEmpty','日常无奖')]:
   self.lookups=[];self.only('169_'+kind+'二');self.assertTrue(self.e[func]())
   self.assertEqual(self.lookups,['169_'+kind+'一','169_'+kind+'二'])
 def test_first_pass_checks_are_independent_and_popup_is_last(self):
  self.visible={'169_成长有奖一','169_成长无奖一','169_日常有奖一','169_通行证','169_特殊有奖','169_特殊无奖','169_奖励弹窗一','169_奖励弹窗二'}
  self.e['BusinessExpired']=lambda:len(self.events)>=7
  self.assertEqual(self.e['RewardFirstPass'](),4)
  self.assertEqual(self.events,[(400,1100,50),(310,123,50),(400,1100,50),(579,55,50),(400,1100,50),(310,123,50),(400,1100,50)])
  self.assertNotIn('169_奖励弹窗二',self.lookups)
 def test_daily_claim_does_not_refresh_ten_second_progress(self):
  self.only('169_日常有奖一');self.assertEqual(self.e['RewardFirstPass'](),4)
  self.assertTrue(10000<self.now-1000<10200);self.assertEqual(self.e['businessStarted'],1000)
 def test_growth_claim_refreshes_progress_but_not_total_deadline(self):
  self.e['businessLimit']=12000;self.only('169_成长有奖一')
  self.assertEqual(self.e['RewardFirstPass'](),4);self.assertTrue(12000<=self.now-1000<12200)
 def test_second_pass_popup_one_then_two_then_four_positions(self):
  self.visible={'169_奖励弹窗一','169_奖励弹窗二','169_日常无奖二'}
  self.assertEqual(self.e['RewardFourPositions'](),1)
  self.assertEqual(len(self.events),12)
  for i,dx in enumerate([-159,-27,106,234]):self.assertEqual(self.events[i*3:i*3+3],[(400,1100,200),(400,1100,1000),(400+dx,225,1000)])
  self.assertFalse(self.e['terminalConfirmed'])
 def test_third_pass_popup_order_is_reversed(self):
  self.visible={'169_奖励弹窗一','169_奖励弹窗二','169_成长无奖一'}
  self.assertEqual(self.e['RewardFinalPass'](),1);self.assertEqual(self.events,[(400,1100,1000),(400,1100,200)])
  self.assertTrue(self.e['terminalConfirmed'])
 def test_third_pass_special_claim_does_not_refresh_four_second_progress(self):
  self.only('169_特殊有奖');self.assertEqual(self.e['RewardFinalPass'](),4)
  self.assertTrue(4000<self.now-1000<4200);self.assertFalse(self.e['terminalConfirmed'])
 def test_final_special_empty_is_terminal(self):
  self.only('169_特殊无奖');self.assertEqual(self.e['RewardFinalPass'](),1);self.assertTrue(self.e['terminalConfirmed'])
 def test_each_unknown_stage_times_out_without_success(self):
  for func,limit in [('EnterTaskRewards',60000),('RewardFirstPass',10000),('RewardFourPositions',10000),('RewardFinalPass',4000)]:
   self.now=1000;self.assertEqual(self.e[func](),4);self.assertTrue(limit<=self.now-1000<=limit+20);self.assertFalse(self.e['terminalConfirmed']);self.assertEqual(self.events,[])
 def test_total_timeout_wins_over_final_empty(self):
  self.only('169_成长无奖一');self.now=61000;self.assertEqual(self.e['RewardFinalPass'](),4);self.assertFalse(self.e['terminalConfirmed'])
 def test_entry_checks_hall_click_before_page_candidates(self):
  self.only('169_入口');self.after=lambda x,y,w:self.only('169_通行证')
  self.assertEqual(self.e['EnterTaskRewards'](),1);self.assertEqual(self.events,[(727,1100,200)])
  # Synthetic matcher anchors are not real pixels; offset semantics, not bounds, are tested.
 def run_closed_loop(self,layout,with_rewards):
  self.only('169_入口');state={'page':'hall','positions':0,'next':''}
  def page(kind):state['page']=kind;self.only('169_'+kind)
  def action(x,y,w):
   p=state['page']
   if p=='hall':page('成长有奖'+layout if with_rewards else '成长无奖'+layout)
   elif p=='成长有奖'+layout:state['next']='成长无奖'+layout;page('奖励弹窗一')
   elif p=='奖励弹窗一':page(state['next'])
   elif p=='成长无奖'+layout:page('日常有奖'+layout if with_rewards else '日常无奖'+layout)
   elif p=='日常有奖'+layout:state['next']='日常无奖'+layout;page('奖励弹窗一')
   elif p=='日常无奖'+layout:
    if y==225:
     state['positions']+=1
     if with_rewards:state['next']='日常无奖'+layout;page('奖励弹窗一')
    elif (x,y)==(487,123):page('成长无奖'+layout)
    else:raise AssertionError((p,x,y,w))
  self.after=action
  self.assertEqual(self.e['ExecuteTaskRewards'](),1);self.assertTrue(self.e['terminalConfirmed']);self.assertEqual(state['positions'],4)
  self.assertEqual(self.e['rewardCount'],0);self.assertEqual(self.e['businessStarted'],1000)
 def test_layout_one_rewards_full_loop(self):self.run_closed_loop('一',True)
 def test_layout_two_rewards_full_loop(self):self.run_closed_loop('二',True)
 def test_layout_one_empty_full_loop(self):self.run_closed_loop('一',False)
 def test_layout_two_empty_full_loop(self):self.run_closed_loop('二',False)

class RewardScheduling(unittest.TestCase):
 def setUp(self):
  self.now=1000;self.restarts=[];self.calls=[];self.e={}
  load(['common/任务状态.mq','common/任务注册.mq','common/任务分派.mq','common/任务调度.mq','common/运行计时.mq'],self.e)
  self.e.update(TickCount=lambda:self.now,Delay=lambda n:None,Note=lambda m:None,
   mailEnabled=True,rewardEnabled=True,mailInterval=10,rewardInterval=30,
   RESULT_OK=1,RESULT_WAIT=2,RESULT_FAIL=3,RESULT_TIMEOUT=4,businessLimit=120000)
  self.e['NewSession']();self.e['RegisterTasks']()
  self.e.update(EnsureGameHall=lambda:1,ReturnToHall=lambda:1,RestartGame=lambda:self.restarts.append(self.e['resumeTask']),ExecuteMail=lambda:self.done(168),ExecuteTaskRewards=lambda:self.done(169))
 def done(self,task):self.calls.append(task);self.e['terminalConfirmed']=True;return 1
 def test_mail_then_reward_once_independent_intervals(self):
  self.e['SchedulerStep']();self.e['SchedulerStep']();self.e['SchedulerStep']()
  self.assertEqual(self.calls,[168,169]);self.assertEqual((self.e['mailCount'],self.e['rewardCount']),(1,1))
  self.assertEqual((self.e['mailDue'],self.e['rewardDue']),(11000,31000))
  self.now=11000;self.assertEqual(self.e['SelectDueTask'](),168)
 def test_first_round_reward_not_starved_by_short_mail_interval(self):
  self.e['SchedulerStep']();self.now=20000;self.assertEqual(self.e['SelectDueTask'](),169)
 def test_both_overdue_choose_earliest_then_mail_on_tie(self):
  self.e.update(mailFirst=False,rewardFirst=False,mailDue=500,rewardDue=400)
  self.assertEqual(self.e['SelectDueTask'](),169);self.e['rewardDue']=500;self.assertEqual(self.e['SelectDueTask'](),168)
 def test_disabled_tasks_and_single_task_selection(self):
  self.e['mailEnabled']=False;self.assertEqual(self.e['SelectDueTask'](),169)
  self.e['rewardEnabled']=False;self.assertEqual(self.e['SelectDueTask'](),0)
 def test_reward_recovery_prioritized_even_if_disabled(self):
  self.e.update(rewardEnabled=False,resumeTask=169);self.assertEqual(self.e['SelectDueTask'](),169)
 def test_reward_failure_only_changes_reward_state_and_retries_same_task(self):
  self.e.update(mailEnabled=False,ExecuteTaskRewards=lambda:4)
  self.e['SchedulerStep']();self.assertEqual(self.restarts,[169]);self.assertEqual(self.e['rewardCount'],0)
  self.assertEqual(self.e['mailFailures'],0);self.assertEqual(self.e['rewardFailures'],1)
  self.e['ExecuteTaskRewards']=lambda:self.done(169);self.e['SchedulerStep']();self.assertEqual(self.calls,[169]);self.assertEqual(self.e['rewardCount'],1)
 def test_reward_return_failure_cannot_commit(self):
  self.e.update(mailEnabled=False,ReturnToHall=lambda:4);self.e['SchedulerStep']()
  self.assertEqual(self.e['rewardCount'],0);self.assertEqual(self.e['rewardDue'],0);self.assertEqual(self.restarts,[169])
 def test_reward_login_failure_keeps_pending_task(self):
  self.e.update(mailEnabled=False,EnsureGameHall=lambda:4);self.e['SchedulerStep']()
  self.assertEqual(self.calls,[]);self.assertEqual(self.restarts,[169]);self.assertEqual(self.e['rewardCount'],0)
 def test_success_result_without_terminal_does_not_commit(self):
  self.e.update(mailEnabled=False,ExecuteTaskRewards=lambda:1);self.e['SchedulerStep']();self.assertEqual(self.e['rewardCount'],0);self.assertEqual(self.restarts,[169])
 def test_new_session_resets_both_runtime_states_not_configuration(self):
  self.e['SchedulerStep']();self.e['SchedulerStep']();self.e['NewSession']()
  self.assertEqual((self.e['mailCount'],self.e['rewardCount']),(0,0));self.assertEqual(self.e['rewardDue'],0)
  self.assertEqual(self.e['rewardInterval'],30);self.assertEqual(self.e['SelectDueTask'](),168)
 def test_reward_commit_does_not_copy_mail_count(self):
  self.e.update(mailCount=77);self.e['SaveCurrentTask'](169);self.e['terminalConfirmed']=True
  self.assertTrue(self.e['CommitTask'](True));self.assertEqual(self.e['rewardCount'],1);self.assertEqual(self.e['mailCount'],77)

class RewardEvidence(unittest.TestCase):
 def test_original_color_values_and_order_preserved(self):
  original=json.loads((E/'原始图色.json').read_text('utf-8'));converted=json.loads((E/'图色转换.json').read_text('utf-8'))
  self.assertEqual(len(converted),14);self.assertEqual(hashlib.sha256(Path(original['source']).read_bytes()).hexdigest(),original['sha256'])
  source=(R/'common/图色参数.mq').read_text('utf-8-sig')
  for a,b in zip(original['records'],converted):
   self.assertEqual(a['definition'][4:],b['definition'][4:]);self.assertEqual(b['definition'][:4],[0,0,719,1279])
   self.assertIn('FindMultiColor '+','.join(json.dumps(x,ensure_ascii=False) for x in b['definition'])+',foundX,foundY',source)
 def test_existing_profiles_unchanged(self):
  before=json.loads((E/'接入前图色.json').read_text('utf-8'));now=json.loads((R/'evidence/图色参数.json').read_text('utf-8'))
  self.assertEqual([r for r in now if r['name'] != '首次启动协议' and not r['name'].startswith(('167_','166_','055_','056_','050_','151_','152_','070_','032_','强敌_','083_','084_','085_'))][:-14],before)
 def test_mail_login_hall_timers_and_scheduler_source_unchanged(self):
  allowed={Path(p) for p in ['app/入口.mq','common/配置读取.mq','common/任务状态.mq','common/任务注册.mq','common/任务分派.mq','common/图色参数.mq']}
  baseline=json.loads((E/'修改前基线.json').read_text('utf-8'))
  for p,digest in baseline.items():
   if Path(p) not in allowed:self.assertEqual(hashlib.sha256((R/'flows/001_游戏重连/evidence/首次启动协议/修改前登录游戏.txt' if Path(p)==Path('flows/001_游戏重连/登录游戏.mq') else before_foreground(R/p)).read_bytes()).hexdigest(),digest,p)
 def test_existing_editable_ui_contracts_preserved(self):
  def contract(source):
   result={}
   for kind,body in re.findall(r'(输入框|下拉框|多选框):\{([^{}]+)\}',source):
    name=re.search(r'名称:"([^"]+)"',body)[1]
    fields=re.findall(r'(选中|初始文本|选项|初始选项|仅输入数字|最大输入长度):("[^"]*"|\[[^\]]*\]|[^,}]+)',body)
    result[name]=(kind,dict(fields))
   return result
  before=contract((E/'接入前配置.uip').read_text('utf-8-sig'))
  after=contract((R/'ui/最小配置.uip').read_text('utf-8-sig'))
  # 2026-10-17 user-selected strong-enemy-only profile disables mail by default.
  before['邮件启用'][1]['选中']='false'
  for key,value in before.items():self.assertEqual(after[key],value)
  self.assertEqual(set(after)-set(before),{'任务奖励启用','任务奖励间隔秒','日常签到启用','签到间隔秒','月卡龙石启用','月卡间隔秒','保留下载提示','好友体力启用','好友体力间隔秒','Q友体力启用','Q友一键领取','Q友体力间隔秒','定时体力启用','体力龙石补领','体力追回','体力兑换','悟空冒险启用','悟空隐藏关卡','悟空扫荡关卡','悟空间隔秒','合作冒险启用','合作队伍模式','世界首领启用','首领买次数','首领执行时','首领执行分','打沙鲁启用','跨服首领启用','跨服首领周日停','跨服首领买次数','跨服首领执行时','跨服首领执行分','红绸军启用','红绸军地图','红绸军中午时','红绸军中午分','红绸军下午时','红绸军下午分','超战士传说启用','激战超越极限启用','那美克星组队战启用','地球保卫战启用','地球保卫买次数','地球保卫执行时间'})
if __name__=='__main__':unittest.main()
