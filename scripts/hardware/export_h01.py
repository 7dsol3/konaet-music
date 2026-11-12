"""Export the validated PCB using KiCad, not illustrative replacement geometry."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'hardware/h01-audio'


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--cli',default='kicad-cli');args=ap.parse_args()
    report=json.loads((OUT/'validation.json').read_text())
    assert report['status']=='PASS'
    for rel,sha in report['sha256'].items():
        assert hashlib.sha256((ROOT/rel).read_bytes().replace(b'\r\n',b'\n')).hexdigest()==sha,rel
    def run(*cmd):
        completed=subprocess.run([args.cli,*map(str,cmd)],capture_output=True,timeout=180)
        text=(completed.stdout+completed.stderr).decode('utf-8',errors='replace')
        if completed.returncode or 'File not found' in text or 'Could not add 3D model' in text:
            raise RuntimeError(text)
        print('Exported: '+' '.join(map(str,cmd[:3])))
    board=OUT/'konaet-h01.kicad_pcb';sch=OUT/'konaet-h01.kicad_sch'
    run('sch','export','pdf','-o',OUT/'schematic.pdf',sch)
    run('pcb','export','step','--force','-o',OUT/'konaet-h01.step',board)
    run('pcb','export','glb','--force','-o',OUT/'konaet-h01.glb',board)
    run('pcb','export','gerbers','--layers','F.Cu,B.Cu,F.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts','-o',str(OUT/'fabrication')+'/',board)
    run('pcb','export','drill','--format','excellon','--generate-map','-o',str(OUT/'fabrication')+'/',board)
    run('pcb','export','pos','--format','csv','--units','mm','--side','front','-o',OUT/'placement.csv',board)
    run('pcb','export','pdf','--layers','F.Cu,B.Cu,F.SilkS,Edge.Cuts','-o',OUT/'layout.pdf',board)
    for name,side,rotate in [('board-3d','top','325,0,25'),('board-top','top','0,0,0'),('board-bottom','bottom','0,0,0')]:
        run('pcb','render','--quality','high','--width','1600','--height','1000','--background','opaque','--side',side,'--rotate',rotate,'-o',OUT/(name+'.png'),board)
    names=['schematic.pdf','layout.pdf','placement.csv','konaet-h01.step','konaet-h01.glb','board-3d.png','board-top.png','board-bottom.png']
    files=[OUT/n for n in names]+sorted((OUT/'fabrication').glob('*'))
    manifest={'source_pcb_sha256':report['sha256']['hardware/h01-audio/konaet-h01.kicad_pcb'],
              'source_schematic_sha256':report['sha256']['hardware/h01-audio/konaet-h01.kicad_sch'],
              'kicad':report['kicad'],'physical_tested':False,'fabrication_approved':False,
              'exports':{str(p.relative_to(OUT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
    (OUT/'exports.json').write_text(json.dumps(manifest,indent=2)+'\n')


if __name__=='__main__':main()
