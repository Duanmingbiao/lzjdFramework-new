from historical_source import before_stamina
import unittest
from mq_subset import ROOT,load
class QFriendConfig(unittest.TestCase):
 def parse(self,value):
  self.logs=[];self.keys=[]
  def read(key,default):self.keys.append((key,default));return value
  e=dict(ReadUIConfig=read,IsNull=lambda x:x is None,CStr=lambda x:('true' if x else 'false') if isinstance(x,bool) else str(x),LCase=lambda x:x.lower(),Trim=lambda x:x.strip(),IsNumeric=lambda x:isinstance(x,(int,float)) and not isinstance(x,bool),WriteMainLog=self.logs.append)
  load(['common/配置读取.mq'],e);return e['QFriendBooleanSetting']('Q友一键领取')
 def test_false_variants_do_not_enter_batch(self):
  for v in [False,'false','False',' FALSE ',0,'0','',None,'unexpected']:
   with self.subTest(value=v):self.assertIs(self.parse(v),False)
 def test_true_variants_enable_batch(self):
  for v in [True,'true','True',' TRUE ',1,'1']:
   with self.subTest(value=v):self.assertIs(self.parse(v),True)
 def test_reading_type_and_value_are_logged_without_boolean_concat(self):
  self.parse('false');self.assertIn('返回类型=string',self.logs[0]);self.assertIn('读取原值=[false]',self.logs[0]);self.assertIn('解析结果=关闭',self.logs[0]);self.assertEqual(self.keys,[('Q友一键领取',False)])
  self.parse(False);self.assertIn('返回类型=boolean',self.logs[0])
 def test_only56_config_processing_changed(self):
  import json,hashlib
  E=ROOT/'flows/056_Q友体力/evidence/配置类型修复'
  for rel,h in json.loads((E/'修改前基线.json').read_text('utf-8')).items():
   if rel!='common/配置读取.mq':self.assertEqual(hashlib.sha256(before_stamina(ROOT/rel).read_bytes()).hexdigest(),h,rel)
