import re
import unittest
from mq_subset import ROOT

class StrongEnemySelectionTests(unittest.TestCase):
 def test_only_strong_enemy_group_is_selected(self):
  ui=(ROOT/'ui/最小配置.uip').read_text('utf-8-sig')
  boxes=dict(re.findall(r'多选框:\{名称:"([^"]+)"[^}]*?选中:(true|false)',ui))
  enabled={'世界首领启用','打沙鲁启用','跨服首领启用','红绸军启用','超战士传说启用','激战超越极限启用','那美克星组队战启用','地球保卫战启用'}
  self.assertEqual({key for key,value in boxes.items() if value=='true'},enabled)
  self.assertTrue({'邮件启用','任务奖励启用','日常签到启用','月卡龙石启用','好友体力启用','Q友体力启用','定时体力启用','悟空冒险启用','合作冒险启用'}.issubset(boxes))
 def test_purchase_and_execution_times_are_preserved(self):
  ui=(ROOT/'ui/最小配置.uip').read_text('utf-8-sig')
  for key,value in [('首领执行时','10'),('首领执行分','00'),('跨服首领执行时','09'),('跨服首领执行分','10'),('红绸军中午时','12'),('红绸军中午分','30'),('红绸军下午时','20'),('红绸军下午分','00')]:
   self.assertIn('名称:"'+key+'",初始文本:"'+value+'"',ui)
  for key in ['首领买次数','跨服首领买次数','地球保卫买次数','地球保卫执行时间']:
   self.assertRegex(ui,'名称:"'+key+'"[^}]*初始选项:0')
if __name__=='__main__':unittest.main()
