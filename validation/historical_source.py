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
