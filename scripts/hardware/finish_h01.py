"""Import explicit router session, add ground planes, export review artifacts."""
from pathlib import Path
import argparse
import re
import pcbnew as pcb

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'hardware/h01-audio'
P=lambda x,y:pcb.VECTOR2I(pcb.FromMM(x),pcb.FromMM(y))


def relink_models():
    # SWIG's model iterator returns values. Rewrite serialized paths explicitly,
    # keeping the frozen library and placed models identical and portable.
    for path in [OUT/'konaet-h01.kicad_pcb',*(OUT/'H01.pretty').glob('*.kicad_mod')]:
        data=path.read_text(encoding='utf-8')
        def replacement(match):
            name=match[1].replace('Oscillator_SMD_Abracon_ASE-4Pin_3.2x2.5mm.step',
                                  'Crystal_SMD_3225-4Pin_3.2x2.5mm.step')
            if not (OUT/'models'/name).is_file(): raise FileNotFoundError(name)
            return '${KIPRJMOD}/models/'+name
        data=re.sub(r'\$\{KICAD\d+_3DMODEL_DIR\}/[^"/]+/([^"/]+)',replacement,data)
        path.write_text(data,encoding='utf-8')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--session',type=Path,required=True);args=ap.parse_args()
    path=OUT/'konaet-h01.kicad_pcb';b=pcb.LoadBoard(str(path))
    if not pcb.ImportSpecctraSES(b,str(args.session.resolve())): raise SystemExit('Router session import failed')
    for track in b.GetTracks():
        if type(track)==pcb.PCB_TRACK and track.GetWidth()<pcb.FromMM(.2):
            track.SetWidth(pcb.FromMM(.2))
    ground=b.FindNet('GND')
    for layer in (pcb.F_Cu,pcb.B_Cu):
        z=pcb.ZONE(b);z.SetNet(ground);z.SetLayer(layer);z.SetLocalClearance(pcb.FromMM(.25))
        z.SetThermalReliefGap(pcb.FromMM(.25));z.SetThermalReliefSpokeWidth(pcb.FromMM(.3))
        z.SetPadConnection(pcb.ZONE_CONNECTION_THERMAL)
        poly=z.Outline();poly.NewOutline()
        for xy in ((51,51),(134,51),(134,114),(51,114)):poly.Append(*P(*xy))
        b.Add(z)
    for x,y in ((60,53),(80,53),(105,53),(125,53),(53,70),(53,90),(132,70),(132,101),(65,112),(85,112),(110,112)):
        via=pcb.PCB_VIA(b);via.SetPosition(P(x,y));via.SetWidth(pcb.FromMM(.7));via.SetDrill(pcb.FromMM(.35));via.SetLayerPair(pcb.F_Cu,pcb.B_Cu);via.SetNet(ground);b.Add(via)
    pcb.ZONE_FILLER(b).Fill(b.Zones())
    pcb.SaveBoard(str(path),b)
    relink_models()
    print('Imported actual routed session and filled two ground planes.')


if __name__=='__main__':main()
