"""Synchronize field metadata without changing copper; no evaluated input."""
from pathlib import Path
import json
import re

OUT=Path(__file__).resolve().parents[2]/'hardware/h01-audio'


def parse(text):
    root=[];stack=[root]
    for token in re.findall(r'"(?:\\.|[^"\\])*"|\(|\)|[^\s()]+',text):
        if token=='(':
            node=[];stack[-1].append(node);stack.append(node)
        elif token==')':
            if len(stack)==1:raise ValueError('Unbalanced input')
            stack.pop()
        else:stack[-1].append(token)
    if len(stack)!=1 or len(root)!=1:raise ValueError('Unbalanced input')
    return root[0]


def dump(node):
    return '('+' '.join(dump(x) if isinstance(x,list) else x for x in node)+')'


def sync():
    data={p['ref']:p for p in json.loads((OUT/'circuit.json').read_text())['parts']}
    for path in [OUT/'konaet-h01.kicad_pcb',*sorted((OUT/'H01.pretty').glob('*.kicad_mod'))]:
        tree=parse(path.read_text(encoding='utf-8'))
        footprints=[tree] if tree[0]=='footprint' else [n for n in tree if isinstance(n,list) and n[0]=='footprint']
        for f in footprints:
            ref=next(json.loads(n[2]) for n in f if isinstance(n,list) and n[:2]==['property','"Reference"'])
            info=data[ref]
            f[:]=[n for n in f if not (isinstance(n,list) and n[0]=='property' and n[1] in ('"4"','"MPN"','"Datasheet"'))]
            for name,value in [('MPN',info['mpn']),('Datasheet',info['source'])]:
                f.append(['property',json.dumps(name),json.dumps(value),['at','0','0','0'],['layer','"F.Fab"'],['hide','yes'],['effects',['font',['size','1','1']]]])
            if ref.startswith('H'):
                for n in f:
                    if isinstance(n,list) and n[0]=='attr':n[:]=[a for a in n if a!='exclude_from_bom']
        path.write_text(dump(tree)+'\n',encoding='utf-8')


if __name__=='__main__':sync()
