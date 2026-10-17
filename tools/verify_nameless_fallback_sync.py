"""Snapshot/verify an authorized sync using the existing independent verifier."""
import argparse
import hashlib
import json
from pathlib import Path
from check_ui import inspect
from verify_dimensional_sync import verify

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT/'reports/无名星战斗图色兜底同步-20261017'


def snapshot():
    p = json.loads((ROOT/'project.json').read_text('utf-8-sig'))
    c = json.loads((ROOT/'assistant-sync.json').read_text('utf8'))
    target = Path(c['target'])
    paths = [p['entry'], *p['modules']]
    mq = '\r\n\r\n'.join('// '+f+'\r\n'+(ROOT/f).read_text('utf-8-sig').replace('\n','\r\n') for f in paths)
    ui = (ROOT/p['ui']).read_text('utf-8-sig').replace('\n','\r\n')
    old_mq = target.read_bytes().decode('gbk')
    changed = {'app/入口.mq','common/无名星状态.mq','flows/020_无名星之战/无名星之战.mq'}
    for f in paths:
        if f not in changed:
            assert '// '+f+'\r\n'+(ROOT/f).read_text('utf-8-sig').replace('\n','\r\n') in old_mq, f
    source_controls = inspect(ui, mq)
    old_controls = inspect(target.with_suffix('.uip').read_bytes().decode('gbk'), old_mq)
    assert old_controls == source_controls
    assert 'Function NamelessBattleColorFallback()' in mq
    assert 'namelessBattleOcrWaitAt < 30000' in mq
    sha = lambda b: hashlib.sha256(b).hexdigest()
    result = {
        'identity':{k:c[k] for k in ['name','id','target']},
        'sourceHashes':{f:sha((ROOT/f).read_bytes()) for f in [*paths,p['ui']]},
        'controlsBefore':old_controls,'controlsAfter':source_controls,
        'expectedHashes':{ext:sha(text.encode('gbk')) for ext,text in [('.mq',mq),('.uip',ui)]},
        'assistantBefore':{str(f):sha(f.read_bytes()) for f in target.parent.glob(target.stem+'.*')},
        'unrelatedMQUnitsUnchanged':89,
    }
    REPORT.mkdir(exist_ok=True)
    path = REPORT/'同步前快照.json'
    if path.exists():
        raise RuntimeError('Snapshot already exists; do not overwrite the pre-sync baseline')
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    print(str(path))


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--snapshot',action='store_true')
    args=parser.parse_args()
    if args.snapshot:
        snapshot()
    else:
        result=verify(REPORT/'同步前快照.json')
        (REPORT/'独立同步验证.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
        print(json.dumps(result,ensure_ascii=False,indent=2))
