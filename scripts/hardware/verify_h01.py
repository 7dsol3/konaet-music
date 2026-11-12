"""Run real KiCad ERC/DRC and compare circuit, schematic netlist and PCB pads."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
import pcbnew as pcb

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'hardware/h01-audio'


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--cli',default='kicad-cli');args=ap.parse_args()
    def run(*cmd):
        subprocess.run([args.cli,*map(str,cmd)],check=True,timeout=180)
    run('sch','erc','--format','json','--exit-code-violations','-o',OUT/'erc.json',OUT/'konaet-h01.kicad_sch')
    run('pcb','drc','--format','json','--schematic-parity','--exit-code-violations','-o',OUT/'drc.json',OUT/'konaet-h01.kicad_pcb')
    run('sch','export','netlist','--format','kicadxml','-o',OUT/'netlist.xml',OUT/'konaet-h01.kicad_sch')
    erc=json.loads((OUT/'erc.json').read_text(encoding='utf-8'))
    drc=json.loads((OUT/'drc.json').read_text(encoding='utf-8'))
    assert not [v for s in erc['sheets'] for v in s['violations']]
    assert not drc['violations'] and not drc['unconnected_items']
    assert not drc['schematic_parity']
    parts=json.loads((OUT/'circuit.json').read_text())['parts']
    expected={(p['ref'],n):net for p in parts for n,net in p['pins'].items() if net}
    xml=ET.parse(OUT/'netlist.xml'); schematic={}
    for net in xml.findall('nets/net'):
        for n in net.findall('node'):
            key=(n.attrib['ref'],n.attrib['pin'])
            if key in expected: schematic[key]=net.attrib['name']
    assert schematic==expected,'Schematic nets differ from the circuit manifest'
    b=pcb.LoadBoard(str(OUT/'konaet-h01.kicad_pcb'));actual={}
    footprints=list(b.GetFootprints())
    assert {f.GetReference() for f in footprints}=={p['ref'] for p in parts}
    models=0
    for f in footprints:
        for pad in f.Pads():
            key=(f.GetReference(),pad.GetNumber())
            if key in expected: actual[key]=pad.GetNetname()
            elif pad.GetNetname() and not (key==('U1','4') and pad.GetNetname()=='unconnected-(U1-NC-Pad4)'):
                raise AssertionError(('Unexpected connected pad',key))
        for m in f.Models():
            assert m.m_Filename.startswith('${KIPRJMOD}/models/')
            assert (OUT/m.m_Filename.replace('${KIPRJMOD}/','')).is_file()
            models+=1
    assert actual==expected,'PCB pad connectivity differs from schematic'
    assert expected['U2','16']==expected['U2','12']==expected['U2','11']==expected['U2','10']=='GND'
    assert expected['R6','1']=='DAC_UNMUTE' and expected['R6','2']=='GND'
    assert expected['J2','1']=='MCLK' and expected['J2','9']=='ADC_SD'
    assert all(net not in ('+3V3','5V_IN','5V_PROTECTED') for (ref,n),net in expected.items() if ref=='J2')
    assert b.GetCopperLayerCount()==2
    tracks=list(b.GetTracks());assert tracks
    assert all(t.GetWidth()>=pcb.FromMM(.2) for t in tracks if type(t)==pcb.PCB_TRACK)
    bound=b.GetBoardEdgesBoundingBox()
    assert abs(pcb.ToMM(bound.GetWidth())-85)<.1 and abs(pcb.ToMM(bound.GetHeight())-65)<.1
    files=[OUT/'konaet-h01.kicad_pro',OUT/'konaet-h01.kicad_sch',OUT/'konaet-h01.kicad_pcb',OUT/'H01.kicad_sym',OUT/'fp-lib-table',OUT/'sym-lib-table',OUT/'circuit.json',OUT/'bom.csv',*sorted((OUT/'H01.pretty').glob('*')),*sorted((OUT/'models').glob('*'))]
    report={'status':'PASS','kicad':subprocess.check_output([args.cli,'version'],text=True).strip(),
      'components':len(parts),'connected_pads':len(expected),'nets':len(set(expected.values())),
      'models':models,'erc_violations':0,'drc_violations':0,'schematic_parity_issues':0,'unconnected_items':0,
      'copper_layers':2,'board_mm':[85,65,1.6], 'physical_tested':False,'fabrication_approved':False,
      'geometric_proxy':['Y1: 3225 crystal outline; not a manufacturer-verified oscillator model'],
      'hash_encoding':'UTF-8 source/STEP with LF newlines',
      'sha256':{str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest() for p in files}}
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='sha256'},indent=2))


if __name__=='__main__':main()
