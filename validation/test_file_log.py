from historical_source import before_diagnostics
import unittest,json,hashlib
from pathlib import Path
from mq_subset import load,ROOT
class FileLogs(unittest.TestCase):
 def setUp(self):
  self.files={};self.dirs=set();self.trace=[];self.now=1000;self.fail=False
  class Dir:
   Exist=lambda _,p:p in self.files or p in self.dirs
   Create=lambda _,p:self.dirs.add(p) or True
  class File:
   Bytes=lambda _,p:len(self.files.get(p,'').encode('utf-8'))
   def Append(_,p,line):
    if not self.fail:self.files[p]=self.files.get(p,'')+line
  self.e={'Dir':Dir(),'File':File(),'TickCount':lambda:self.now,'Chr':chr,'TracePrint':self.trace.append,'stageName':'启动及QQ登录'}
  load(['common/日志.mq'],self.e)
 def test_stage_and_recovery_written_with_tick_and_crlf(self):
  self.e['Note']('公共调度器收到前台离开；前台=launcher')
  text=self.files['/sdcard/Pictures/dragonball-main.log']
  self.assertEqual(text,'[tick=1000] [龙珠激斗脚本][启动及QQ登录] 公共调度器收到前台离开；前台=launcher\r\n')
  self.assertEqual(self.trace,[text[:-2]])
 def test_foreground_goes_to_separate_file(self):
  load(['common/前台监控.mq'],self.e)
  self.e['ForegroundLog']('前台包名=com.tencent.mobileqq')
  self.assertNotIn('/sdcard/Pictures/dragonball-main.log',self.files)
  self.assertIn('[前台监控] 前台包名=com.tencent.mobileqq',self.files['/sdcard/Pictures/dragonball-foreground.log'])
 def test_append_keeps_previous_runs(self):
  p='/sdcard/Pictures/dragonball-main.log';self.files[p]='previous\r\n'
  self.e['Note']('新会话启动');self.now=2000;self.e['Note']('重启游戏')
  self.assertTrue(self.files[p].startswith('previous\r\n'));self.assertIn('[tick=2000]',self.files[p])
 def test_stage_change_logged_once(self):
  self.e['SetStage']('邮件');self.e['SetStage']('邮件')
  self.assertEqual(self.files['/sdcard/Pictures/dragonball-main.log'].count('进入阶段'),1)
 def test_write_failure_diagnostic_does_not_change_business(self):
  self.fail=True;self.e.update(currentTask=169,resumeTask=169,loginStarted=44)
  self.e['Note']('测试');self.assertTrue(any('写入失败' in x for x in self.trace))
  self.assertEqual((self.e['currentTask'],self.e['resumeTask'],self.e['loginStarted']),(169,169,44))
 def test_only_public_log_and_forwarder_changed(self):
  E=ROOT/'common/evidence/文件日志';base=json.loads((E/'修改前基线.json').read_text('utf-8'))
  for p,h in base.items():
   if p not in ['common/日志.mq','common/前台监控.mq','app/入口.mq','common/游戏控制.mq','common/点击操作.mq']:self.assertEqual(hashlib.sha256(before_diagnostics(ROOT/p).read_bytes()).hexdigest(),h,p)
  before=(E/'前台监控修改前.txt').read_text('utf-8-sig')
  after=(ROOT/'common/evidence/线程启动排查/前台监控修改前.txt').read_text('utf-8-sig')
  self.assertEqual(after,before.replace('    TracePrint "[龙珠激斗脚本][前台监控] " & message','    Call WriteForegroundLog("[龙珠激斗脚本][前台监控] " & message)'))
 def test_no_nested_thread_lock_or_business_operations(self):
  source=(ROOT/'common/日志.mq').read_text('utf-8-sig')
  for forbidden in ['Thread.Lock','KillApp','RunApp','Tap ','NewSession','SaveRecovery','CommitTask']:self.assertNotIn(forbidden,source)
if __name__=='__main__':unittest.main()
