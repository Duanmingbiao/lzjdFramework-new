from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
AUTHORIZED={'flows/001_游戏重连/登录游戏.mq','app/入口.mq','common/运行计时.mq','common/返回大厅.mq','common/任务状态.mq','common/游戏控制.mq','common/点击操作.mq','common/任务调度.mq'}
def before_foreground(path):
 path=Path(path)
 if path == ROOT/'common/日志.mq':return ROOT/'common/evidence/文件日志/日志修改前.txt'
 if path == ROOT/'common/前台监控.mq':return ROOT/'common/evidence/文件日志/前台监控修改前.txt'

 try:rel=path.relative_to(ROOT)
 except ValueError:return path
 if rel.as_posix() in AUTHORIZED:
  return ROOT/'common/evidence/前台监控/before'/rel.with_suffix('.txt')
 return before_diagnostics(path)


def before_diagnostics(path):
 path=Path(path)
 try: rel=path.relative_to(ROOT)
 except ValueError:return path
 backup=ROOT/"common/evidence/流程日志/before"/rel.with_suffix(".txt")
 return backup if path.suffix==".mq" and backup.exists() else before_signin(path)


def before_signin(path):
 path=Path(path)
 try:rel=path.relative_to(ROOT)
 except ValueError:return path
 backup=ROOT/'flows/167_日常签到/evidence/before'/rel.with_suffix('.txt')
 return backup if path.suffix in ('.mq','.uip') and backup.exists() else path


def before_monthly(path):
 path=Path(path)
 try:rel=path.relative_to(ROOT)
 except ValueError:return path
 backup=ROOT/'flows/166_领月卡龙石/evidence/before'/rel.with_suffix('.txt')
 return backup if path.suffix in ('.mq','.uip') and backup.exists() else path

def before_friend(path):
 path=Path(path)
 rel=path.relative_to(ROOT)
 backup=ROOT/'flows/055_好友体力/evidence/before'/rel.with_suffix('.txt')
 return backup if backup.exists() else path

def before_stamina(path):
 path=Path(path)
 rel=path.relative_to(ROOT)
 backup=ROOT/'flows/050_定时领取体力/evidence/before'/rel.with_suffix('.txt')
 return backup if backup.exists() else path

def before_boss_native_exits_bytes(path):
 """Undo only the three user-authorized 2026-10-17 native-exit patches for historical hashes.
 Any additional source change still fails the original hash assertion.
 """
 data=Path(path).read_bytes()
 if Path(path)==ROOT/'common/强敌入口.mq':
  addition='\n// 3.8 compatible numeric fallback, original trial ROI and original red color only.\n// Keep general OCR first: numeric OCR must not replace cooldown/title text OCR.\nFunction TrialCountText(x1, y1, x2, y2)\n    Dim text, raw\n    TrialCountText = ""\n    If BusinessExpired() Or Not Sys.AppIsFront(GAME_PACKAGE) Then\n        Exit Function\n    End If\n    text = WorldText(x1, y1, x2, y2)\n    If BusinessExpired() Or Not Sys.AppIsFront(GAME_PACKAGE) Then\n        Exit Function\n    End If\n    TrialCountText = text\n    If Not IsNull(text) Then\n        If text <> "" Then\n            Exit Function\n        End If\n    End If\n    If BusinessExpired() Then\n        Exit Function\n    End If\n    If Not Sys.AppIsFront(GAME_PACKAGE) Then\n        Exit Function\n    End If\n    ReleaseCapture\n    raw = SmartOcr(x1, y1, x2, y2, "0000E9-101010")\n    TrialCountText = ""\n    If BusinessExpired() Or Not Sys.AppIsFront(GAME_PACKAGE) Then\n        Exit Function\n    End If\n    If Not IsNull(raw) Then\n        TrialCountText = CStr(raw)\n    End If\n    text = ""\n    If Not IsNull(raw) Then\n        text = CStr(raw)\n    End If\n    Call WorldLog("3.8数字OCR补识别 区域=" & x1 & "," & y1 & "," & x2 & "," & y2 & " BGR=0000E9-101010 文本=[" & text & "]；空值不是耗尽")\nEnd Function\n'.replace('\n','\r\n').encode('utf8')
  assert data.count(addition)==1,'Unexpected trial OCR helper drift'
  data=data.replace(addition,b'')
 changes=[
  ('            Call WorldLog("专业版阶段出口=扫荡30秒无进展，停止扫荡并进入领奖；不是业务完成")\n            Call Progress()\n            SweepWorldBoss = RESULT_OK',
   '            Call WorldLog("超时原因=扫荡30秒无进展；不沿用原版超时后继续成功路径")'),
  ('                crossTerminalReason = "专业版预备操作达阈值，退出模板未命中且阶段累计超过3000毫秒，本轮结束"\n                Call WorldLog("专业版预备阶段出口=" & crossTerminalReason & "；等待公共返回大厅确认，不直接提交")\n                RunCrossPreparation = RESULT_OK',
   '                Call WorldLog("超时原因=预备阈值后退出模板未命中；阶段起点累计超过3000毫秒；不沿用原版盲结束")'),
  ('            Call WorldLog("专业版阶段出口=正式扫荡15秒未获奖励，进入主界面确认与领奖；不是业务完成")\n            SweepCrossBoss = RESULT_OK',
   '            Call WorldLog("超时原因=正式扫荡15秒未获奖励；计时起点包括购买阶段，扫荡点击不刷新")'),
 ]
 for after,before in changes:
  data=data.replace(after.replace('\n','\r\n').encode('utf-8'),before.encode('utf-8'))
 return data
