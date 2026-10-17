"""Check shared MQ names using case-insensitive identifier semantics."""
import re


def symbol_conflicts(sources):
    symbols = {}
    issues = []
    for path, text in sources:
        inside = False
        for number, raw in enumerate(text.splitlines(), 1):
            line = raw.split('//', 1)[0].strip()
            procedure = re.match(r'(?:Function|Sub)\s+(\w+)\s*\(', line, re.I)
            names = []
            if procedure:
                names = [procedure[1]]
                inside = True
            elif re.match(r'End\s+(?:Function|Sub)\b', line, re.I):
                inside = False
            elif not inside and re.match(r'Dim\s+', line, re.I):
                names = [part.strip() for part in re.sub(r'^Dim\s+', '', line, flags=re.I).split(',')]
            for name in names:
                key = name.casefold()
                location = f'{path}:{number}: {name}'
                if key in symbols:
                    issues.append('duplicate MQ name: ' + location + ' conflicts with ' + symbols[key])
                else:
                    symbols[key] = location
    return issues
