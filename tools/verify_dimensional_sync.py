"""Read-only verification of the explicitly authorized four-module file sync."""
import argparse
import hashlib
import json
from pathlib import Path
from check_ui import inspect

ROOT = Path(__file__).resolve().parents[1]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def verify(before_path):
    before = json.loads(Path(before_path).read_text('utf8'))
    cfg = json.loads((ROOT/'assistant-sync.json').read_text('utf8'))
    target = Path(cfg['target'])
    for key in ['name', 'id', 'target']:
        assert cfg[key] == before['identity'][key], ('identity changed', key)
    project = json.loads((ROOT/'project.json').read_text('utf-8-sig'))
    paths = [project['entry'], *project['modules']]
    actual = {p.relative_to(ROOT).as_posix()
              for folder in ['app', 'common', 'flows']
              for p in (ROOT/folder).rglob('*.mq')}
    assert set(paths) == actual and len(paths) == len(actual)
    for filename, digest in before['sourceHashes'].items():
        assert sha((ROOT/filename).read_bytes()) == digest, ('source changed', filename)
    mq = '\r\n\r\n'.join('// '+p+'\r\n'+(ROOT/p).read_text('utf-8-sig').replace('\n','\r\n') for p in paths)
    ui = (ROOT/project['ui']).read_text('utf-8-sig').replace('\n','\r\n')
    source_controls = inspect(ui, mq)
    assert len(source_controls) == 225
    for name, (kind, props) in before['controlsAfter'].items():
        assert source_controls[name] == (kind, props), ('source control changed', name)
    for name, (kind, props) in before['controlsBefore'].items():
        assert source_controls[name] == (kind, props), ('old control changed', name)
    boxes = [props for kind, props in source_controls.values() if kind == '多选框']
    assert len(boxes) == 55 and all(p['选中'] is False for p in boxes)
    functions = ['ExecuteNamelessBattle', 'ExecuteGalaxyBattle', 'ExecuteForest', 'ExecuteAllianceBattle']
    keys = ['日常_无名星之战', '日常_跨银河大赛', '日常_恐惧森林', '日常_联盟组队战']
    for function, key, task in zip(functions, keys, [20, 21, 22, 23]):
        assert 'Function '+function+'()' in mq, function
        assert key in source_controls and task in project['registeredTasks'], key
    hashes = {}
    for ext, content in [('.mq', mq), ('.uip', ui)]:
        data = content.encode('gbk', errors='strict')
        digest = sha(data)
        assert digest == before['expectedHashes'][ext], ('unexpected build', ext)
        assert target.with_suffix(ext).read_bytes() == data, ('target mismatch', ext)
        assert cfg['lastSynced'][ext] == digest
        for folder, encoding in [('手机助手3.8导入版','gbk'), ('UTF-8查看版','utf-8-sig')]:
            p = ROOT/'dist'/folder/('龙珠激斗脚本'+ext)
            assert p.read_bytes() == content.encode(encoding, errors='strict'), str(p)
        hashes[ext] = digest
    target_controls = inspect(target.with_suffix('.uip').read_bytes().decode('gbk'), target.read_bytes().decode('gbk'))
    assert target_controls == source_controls
    preserved = {}
    for filename, digest in before['assistantBefore'].items():
        p = Path(filename)
        if p.suffix not in ['.mq', '.uip']:
            assert sha(p.read_bytes()) == digest, ('metadata/cache changed', filename)
            preserved[filename] = digest
    assert {str(p) for p in target.parent.glob(target.stem+'.*')} == set(before['assistantBefore'])
    prop = json.loads(target.with_suffix('.prop').read_bytes().decode('gbk'))
    assert prop['Name'] == cfg['name'] and prop['id'] == cfg['id']
    return {'target':str(target), 'id':cfg['id'], 'sourceUnits':len(paths),
            'modules':keys, 'controls':len(source_controls), 'oldControlsPreserved':len(before['controlsBefore']),
            'checkboxes':len(boxes), 'allUnchecked':True, 'sourceHashesUnchanged':True,
            'sourceBuildTargetMQAndUIExact':True, 'hashes':hashes, 'preserved':preserved,
            'assistantOperated':False, 'deviceConnected':False, 'officialCompilationVerified':False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('before')
    print(json.dumps(verify(parser.parse_args().before), ensure_ascii=False, indent=2))
