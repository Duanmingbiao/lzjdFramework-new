import unittest,re
from mq_subset import ROOT,load
import test_worldboss

class EntrySwipeTests(unittest.TestCase):
 def fixture(self,task):
  f=test_worldboss.WorldBossTests();f.setUp();e=f.e;swipes=[];events=[]
  def match(name):f.now+=10;return f.match(name)
  e.update(MatchPattern=match,currentTask=task,businessStarted=0,businessLimit=120000,ForegroundInterrupted=lambda:f.interrupt)
  if task==155:
   load(['common/蛇道状态.mq','flows/155_蛇道/蛇道.mq','common/运行计时.mq'],e)
   run=e['EnterSnake'];hall='155_P62';icon='155_P58';page='155_P63';tap=(600,900,200)
  else:
   load(['common/龙珠大冒险状态.mq','flows/150_龙珠大冒险/龙珠大冒险.mq','common/运行计时.mq'],e)
   run=e['EnterAdventure'];hall='150_P46';icon='150_P50';page='150_P00';tap=(471,792,1500)
  e['ReturnToHall']=lambda:events.append('hall') or 1
  def swipe(*args):swipes.append(args);events.append('swipe');f.visible={hall,icon}
  e['Swipe']=swipe;f.after=lambda *a:setattr(f,'visible',{page})
  return f,e,swipes,events,run,hall,icon,page,tap
 def test_missing_icon_hall_swipe_then_recheck_and_enter_both_tasks(self):
  for task in [155,150]:
   with self.subTest(task=task):
    f,e,swipes,events,run,hall,icon,page,tap=self.fixture(task);f.visible={hall}
    self.assertEqual(run(),1);self.assertEqual(swipes,[(500,545,150,545,300)]);self.assertEqual(events,['hall','swipe']);self.assertEqual(f.taps,[tap]);self.assertFalse(e['terminalConfirmed'])
 def test_visible_icon_clicks_without_swipe(self):
  for task in [155,150]:
   with self.subTest(task=task):
    f,e,swipes,events,run,hall,icon,page,tap=self.fixture(task);f.visible={hall,icon}
    self.assertEqual(run(),1);self.assertFalse(swipes);self.assertFalse(events);self.assertEqual(f.taps,[tap])
 def test_already_inside_no_navigation(self):
  for task in [155,150]:
   with self.subTest(task=task):
    f,e,swipes,events,run,hall,icon,page,tap=self.fixture(task);f.visible={page}
    self.assertEqual(run(),1);self.assertFalse(swipes);self.assertFalse(f.taps);self.assertFalse(events)
 def test_unknown_page_does_not_blind_swipe_or_complete(self):
  for task in [155,150]:
   with self.subTest(task=task):
    f,e,swipes,events,run,hall,icon,page,tap=self.fixture(task)
    self.assertEqual(run(),4);self.assertFalse(swipes);self.assertFalse(f.taps);self.assertFalse(e['terminalConfirmed']);self.assertGreater(f.now,62000)
 def test_hall_return_failure_blocks_swipe(self):
  for task in [155,150]:
   with self.subTest(task=task):
    f,e,swipes,events,run,hall,icon,page,tap=self.fixture(task);f.visible={hall};e['ReturnToHall']=lambda:4
    self.assertEqual(run(),4);self.assertFalse(swipes);self.assertFalse(f.taps)
 def test_foreground_interrupt_between_hall_and_swipe_blocks_action(self):
  for task in [155,150]:
   with self.subTest(task=task):
    f,e,swipes,events,run,hall,icon,page,tap=self.fixture(task);f.visible={hall}
    def interrupted():f.interrupt=True;return 1
    e['ReturnToHall']=interrupted;self.assertEqual(run(),4);self.assertFalse(swipes);self.assertFalse(f.taps);self.assertFalse(e['terminalConfirmed'])
 def test_front_guard_blocks_swipe(self):
  for task in [155,150]:
   with self.subTest(task=task):
    f,e,swipes,events,run,hall,icon,page,tap=self.fixture(task);f.visible={hall};e['Sys'].AppIsFront=lambda package:False
    self.assertEqual(run(),4);self.assertFalse(swipes);self.assertFalse(f.taps)
 def test_expired_timer_cannot_be_revived_by_navigation(self):
  for task in [155,150]:
   with self.subTest(task=task):
    f,e,swipes,events,run,hall,icon,page,tap=self.fixture(task);f.visible={hall};f.now=120001
    self.assertEqual(run(),4);self.assertFalse(swipes);self.assertFalse(events);self.assertFalse(e['terminalConfirmed'])
 def test_retained_professional_right_direction_and_call_sites(self):
  helper=(ROOT/'flows/153_悟空送仙豆/evidence/root785静态重建.txt').read_text('utf8').split('elseif A1_1 == "滑右" then',1)[1].split('  end',1)[0]
  self.assertEqual([int(re.search(rf'L{n}_1 = (\d+)',helper)[1]) for n in range(6,11)],[500,545,150,545,300])
  for rel in ['flows/155_蛇道/evidence/root787蛇道分支.txt','flows/150_龙珠大冒险/evidence/root787入口分支.txt']:
   self.assertIn('= "滑右"',(ROOT/rel).read_text('utf8'))
 def test_left_direction_other_two_modules_unchanged(self):
  for rel in ['flows/153_悟空送仙豆/悟空送仙豆.mq','flows/154_种仙豆/种仙豆.mq']:
   self.assertIn('Swipe 150, 545, 500, 545, 300',(ROOT/rel).read_text('utf-8-sig'))
  for rel in ['flows/155_蛇道/蛇道.mq','flows/150_龙珠大冒险/龙珠大冒险.mq']:
   source=(ROOT/rel).read_text('utf-8-sig');self.assertNotIn('150, 545, 500, 545, 300',source);self.assertIn('500, 545, 150, 545, 300',source)

if __name__=='__main__':unittest.main()
