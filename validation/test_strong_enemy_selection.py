import re
import unittest
from mq_subset import ROOT

class StrongEnemySelectionTests(unittest.TestCase):
 def test_all_checkboxes_default_unchecked(self):
  ui=(ROOT/'ui/最小配置.uip').read_text('utf-8-sig')
  boxes=dict(re.findall(r'多选框:\{名称:"([^"]+)"[^}]*?选中:(true|false)',ui))
  self.assertTrue(boxes)
  self.assertEqual(set(boxes.values()),{'false'})
  self.assertTrue({'邮件启用','任务奖励启用','日常签到启用','月卡龙石启用','好友体力启用','Q友体力启用','定时体力启用','悟空冒险启用','合作冒险启用'}.issubset(boxes))
 def test_all_features_share_daily_page(self):
  ui=(ROOT/'ui/最小配置.uip').read_text('utf-8-sig')
  daily=ui.split('日常功能:{',1)[1].split('公共设置:{',1)[0]
  self.assertNotIn('异时空冒险:{',ui)
  for key in ['世界首领启用','战士集结启用','日常_超宇宙战士','日常_弗利萨军团','日常_强者对决','日常_战士记忆']:
   self.assertIn('名称:"'+key+'"',daily)
 def test_purchase_and_execution_times_are_preserved(self):
  ui=(ROOT/'ui/最小配置.uip').read_text('utf-8-sig')
  for key,value in [('首领执行时','10'),('首领执行分','00'),('跨服首领执行时','09'),('跨服首领执行分','10'),('红绸军中午时','12'),('红绸军中午分','30'),('红绸军下午时','20'),('红绸军下午分','00')]:
   self.assertIn('名称:"'+key+'",初始文本:"'+value+'"',ui)
  for key in ['首领买次数','跨服首领买次数','地球保卫买次数','地球保卫执行时间']:
   self.assertRegex(ui,'名称:"'+key+'"[^}]*初始选项:0')
if __name__=='__main__':unittest.main()
