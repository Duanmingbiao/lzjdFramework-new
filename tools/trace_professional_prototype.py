"""Read retained Lua prototype evidence; no target execution or file writes.

Linear register annotations are hints only: branches must be checked against
raw instruction PCs. This is not a decompiler or an execution emulator.
"""
import argparse
import json
import re
from pathlib import Path


def trace(path, index, start=0, end=None):
    proto = json.loads(Path(path).read_text('utf-8'))['children'][index]
    constants = proto['constants']
    registers = {i: f'R{i}' for i in range(256)}

    def constant(value):
        if isinstance(value, str) and re.fullmatch(r'id(?:[0-9a-f]{2})+', value):
            try:
                value = bytes.fromhex(value[2:]).decode('utf-8')
            except UnicodeError:
                pass
        return repr(value)

    def rk(value):
        return constant(constants[value-256]) if value >= 256 else registers[value]

    for pc, word in enumerate(proto['code']):
        op, a, b, c, bx = word & 63, word >> 6 & 255, word >> 23 & 511, word >> 14 & 511, word >> 14
        note = ''
        if op == 28:
            registers[a] = registers[b]
        elif op == 29:
            registers[a] = constant(constants[bx])
        elif op == 31:
            registers[a] = str(bool(b))
            note = f'R{a} = {registers[a]}'
        elif op == 34:
            registers[a] = rk(c)
        elif op == 35:
            registers[a] = registers[b] + '[' + rk(c) + ']'
        elif op == 39:
            registers[a] = f'table@{pc}'
        elif op == 38:
            note = f'{registers[a]}[{rk(b)}] = {rk(c)}'
        elif op == 43:
            note = f'CALL {registers[a]}(' + ', '.join(registers[i] for i in range(a+1, a+b)) + ')'
            if c > 1:
                note = f'R{a} = ' + note
                registers[a] = f'call@{pc}'
        elif op == 18:
            note = f'JMP {pc+1+bx-131071}'
        elif op in (19, 20, 21):
            note = f'COMPARE A={a} {rk(b)} ' + {19: '==', 20: '<', 21: '<='}[op] + ' ' + rk(c)
        elif op == 22:
            note = f'TEST R{a} C={c}'
        elif op == 45:
            note = f'RETURN R{a} B={b}'
        elif op in (8, 9):
            note = f'R{a} = {rk(b)} ' + ('+' if op == 8 else '-') + ' ' + rk(c)
            registers[a] = f'R{a}'
        if note and start <= pc < (end or len(proto['code'])):
            print(f'{pc}: {note}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('path')
    parser.add_argument('index', type=int)
    parser.add_argument('--start', type=int, default=0)
    parser.add_argument('--end', type=int)
    args = parser.parse_args()
    trace(args.path, args.index, args.start, args.end)
