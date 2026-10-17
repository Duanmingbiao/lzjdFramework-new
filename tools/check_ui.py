"""Parse the complete UIP grammar, retaining repeated layout/control keys."""
import collections
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
TOKEN = re.compile(r'\s*("(?:[^"\\]|\\.)*"|-?\d+(?:\.\d+)?|[{}\[\]:,]|[^\s{}\[\]:,"]+)')


def parse(text):
    tokens = []
    pos = 0
    while text[pos:].strip():
        match = TOKEN.match(text, pos)
        if not match:
            raise ValueError(f'Invalid UIP token at character {pos}')
        tokens.append((match[1], match.start(1)))
        pos = match.end()
    index = 0

    def take(expected=None):
        nonlocal index
        if index >= len(tokens):
            raise ValueError(f'Unexpected end, expected {expected}')
        value, offset = tokens[index]
        if expected is not None and value != expected:
            line = text.count('\n', 0, offset) + 1
            raise ValueError(f'Line {line}: expected {expected}, got {value}')
        index += 1
        return value

    def value():
        token = tokens[index][0]
        if token == '{':
            take('{')
            result = []
            while tokens[index][0] != '}':
                key = take()
                take(':')
                result.append((key, value()))
                if tokens[index][0] != '}':
                    take(',')
            take('}')
            return result
        if token == '[':
            take('[')
            result = []
            while tokens[index][0] != ']':
                result.append(value())
                if tokens[index][0] != ']':
                    take(',')
            take(']')
            return result
        raw = take()
        if raw.startswith('"') or raw in ('true', 'false') or re.fullmatch(r'-?\d+(?:\.\d+)?', raw):
            return json.loads(raw)
        raise ValueError(f'Invalid UIP value {raw}')

    take('界面')
    take(':')
    tree = value()
    if index != len(tokens):
        raise ValueError('Unexpected content after UIP root')
    return tree


def inspect(text, source):
    tree = parse(text)
    controls = {}
    callbacks = []

    def walk(pairs):
        for kind, body in pairs:
            if not isinstance(body, list) or not body or not isinstance(body[0], tuple):
                continue
            props = dict(body)
            if '名称' in props:
                name = props['名称']
                if name in controls:
                    raise ValueError('Duplicate control name: ' + name)
                controls[name] = (kind, props)
                if kind == '多选框' and props.get('选中') is not False:
                    raise ValueError('Checkbox is not unchecked: ' + name)
                if kind == '下拉框' and not 0 <= props.get('初始选项', 0) < len(props['选项']):
                    raise ValueError('Dropdown index out of range: ' + name)
                for key, callback in body:
                    if key.endswith('响应') and callback:
                        callbacks.append((name, callback))
            walk(body)

    walk(tree)
    for name, callback in callbacks:
        if not re.search(r'(?mi)^(?:Sub|Function)\s+' + re.escape(callback) + r'\s*\(', source):
            raise ValueError(f'Undefined callback: {name} -> {callback}')
    reads = set(re.findall(r'(?:ReadUIConfig|WorldBoolean|WorldNumber|PositiveSetting|QFriendBooleanSetting)\(\s*"([^"]+)"', source))
    missing = reads - controls.keys()
    if missing:
        raise ValueError('Missing configuration controls: ' + repr(sorted(missing)))
    return controls


def check():
    project = json.loads((ROOT / 'project.json').read_text('utf-8-sig'))
    source = '\n'.join((ROOT / p).read_text('utf-8-sig') for p in [project['entry'], *project['modules']])
    ui = (ROOT / project['ui']).read_text('utf-8-sig')
    controls = inspect(ui, source)
    print(json.dumps({'pages': [key for key, _ in parse(ui)], 'controls': len(controls), 'types': dict(collections.Counter(kind for kind, _ in controls.values())), 'allUnchecked': True, 'syntaxAndBindings': 'pass'}, ensure_ascii=False))
    return controls


if __name__ == '__main__':
    check()
