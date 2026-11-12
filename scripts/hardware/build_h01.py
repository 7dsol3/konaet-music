"""Generate the H-01A review prototype in KiCad; run with KiCad's Python.

The circuit manifest is the single source for schematic pins and PCB pad nets.
Routing is a separate, explicit step; this never invents a passing DRC result.
"""
from pathlib import Path
import argparse
import csv
import json
import math
import re
import shutil
import uuid
import pcbnew as pcb

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'hardware/h01-audio'
NAME = 'konaet-h01'
UID = lambda s: str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://konaet/h01a/' + s))
Q = lambda s: json.dumps(str(s))
P = lambda x, y: pcb.VECTOR2I(pcb.FromMM(x), pcb.FromMM(y))
PARTS = []


def part(ref, value, fp, xy, pins, mpn='', source='', angle=0, names=None, types=None):
    PARTS.append(dict(ref=ref, value=value, footprint=fp, xy=xy, angle=angle,
                      pins={str(k): v for k, v in pins.items()}, mpn=mpn or value,
                      source=source, names=names or {}, types=types or {}))


def circuit():
    ti = 'https://www.ti.com/lit/ds/symlink/'
    rfp = 'Resistor_SMD:R_0805_2012Metric'
    cfp = 'Capacitor_SMD:C_0805_2012Metric'
    part('J1', '5V IN / 5.25V MAX', 'Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical', (60, 62),
         {1:'5V_IN', 2:'GND'}, 'B2B-XH-A(LF)(SN)', 'https://www.jst-mfg.com/product/pdf/eng/eXH.pdf')
    part('D1', 'SS14 / reverse polarity', 'Diode_SMD:D_SMA', (69, 62), {1:'5V_PROTECTED',2:'5V_IN'},
         'SS14', 'https://www.vishay.com/docs/88746/ss12.pdf')
    part('U1', 'TLV75533PDBVR', 'Package_TO_SOT_SMD:SOT-23-5', (79, 62),
         {1:'5V_PROTECTED',2:'GND',3:'5V_PROTECTED',4:None,5:'+3V3'}, source=ti+'tlv755p.pdf',
         names={'1':'IN','2':'GND','3':'EN','4':'NC','5':'OUT'},
         types={'1':'power_in','2':'power_in','3':'input','4':'no_connect','5':'power_out'})
    for ref, value, xy, a, b in [
        ('C1','2.2uF / 16V X7R',(74,65),'5V_PROTECTED','GND'),
        ('C2','2.2uF / 16V X7R',(83,65),'+3V3','GND'),
        ('C3','10uF / 16V X7R',(87,65),'+3V3','GND'),
        ('C4','100nF / 16V X7R',(74,76),'+3V3','GND'),
        ('C5','2.2uF / 16V X7R',(95,79),'CAPP','CAPM'),
        ('C6','2.2uF / 16V X7R',(95,84),'VNEG','GND'),
        ('C7','100nF / 16V X7R',(100,73),'+3V3','GND'),
        ('C8','10uF / 16V X7R',(96,73),'+3V3','GND'),
        ('C9','100nF / 16V X7R',(100,89),'+3V3','GND'),
        ('C10','10uF / 16V X7R',(96,89),'+3V3','GND'),
        ('C11','100nF / 16V X7R',(110,73),'+3V3','GND'),
        ('C12','10uF / 16V X7R',(114,73),'+3V3','GND'),
        ('C13','100nF / 16V X7R',(113,78),'LDOO','GND'),
        ('C14','2.2nF / 50V C0G',(120,85),'LINE_L','GND'),
        ('C15','2.2nF / 50V C0G',(120,91),'LINE_R','GND'),
        ('C16','100nF / 16V X7R',(74,97),'+3V3','GND')]:
        part(ref,value,cfp,xy,{1:a,2:b})
    part('Y1','12.288MHz / 3V3','Oscillator:Oscillator_SMD_Abracon_ASE-4Pin_3.2x2.5mm',(78,76),
         {1:'+3V3',2:'GND',3:'CLK_RAW',4:'+3V3'},'ASE-12.288MHZ-L-C-T',
         'https://abracon.com/Oscillators/ASEseries.pdf',
         names={'1':'EN','2':'GND','3':'OUT','4':'VDD'},
         types={'1':'input','2':'power_in','3':'output','4':'power_in'})
    part('U2','PCM5102APWR','Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm',(105,82),
         {1:'+3V3',2:'CAPP',3:'GND',4:'CAPM',5:'VNEG',6:'DAC_L',7:'DAC_R',8:'+3V3',9:'GND',10:'GND',
          11:'GND',12:'GND',13:'BCLK',14:'DAC_SD',15:'LRCLK',16:'GND',17:'DAC_UNMUTE',18:'LDOO',19:'GND',20:'+3V3'},
         source=ti+'pcm5102a.pdf',
         names=dict(zip(map(str,range(1,21)),['CPVDD','CAPP','CPGND','CAPM','VNEG','OUTL','OUTR','AVDD','AGND','DEMP','FLT','SCK','BCK','DIN','LRCK','FMT','XSMT','LDOO','DGND','DVDD'])),
         types={str(i):'power_in' if i in (1,3,8,9,19,20) else 'output' if i in (2,4,5,6,7,18) else 'input' for i in range(1,21)})
    part('J2','FPGA 3V3 IO / NOT PMOD','Connector_PinHeader_2.54mm:PinHeader_2x06_P2.54mm_Vertical',(62,75),
         {1:'MCLK',2:'GND',3:'HOST_BCLK',4:'GND',5:'HOST_LRCLK',6:'GND',7:'HOST_DAC_SD',8:'GND',9:'ADC_SD',10:'GND',11:'DAC_UNMUTE',12:'GND'},
         '2x6 2.54mm header', names={'1':'CLK to FPGA','3':'BCLK from FPGA','5':'WS from FPGA','7':'DATA from FPGA','9':'MIC to FPGA','11':'UNMUTE from FPGA'},
         types={'1':'input','3':'output','5':'output','7':'output','9':'input','11':'output'})
    part('J3','MIC I2S / LEFT / 3V3','Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical',(62,94),
         {1:'+3V3',2:'GND',3:'BCLK',4:'LRCLK',5:'ADC_SD',6:'GND'}, '1x6 2.54mm header',
         names={'1':'3V3 OUT','2':'GND','3':'SCK','4':'WS','5':'SD','6':'LR LOW'}, types={'5':'output'})
    part('J4','LINE OUT / NOT SPEAKER','Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical',(127,85),
         {1:'LINE_L',2:'GND',3:'LINE_R'}, '1x3 2.54mm header',names={'1':'LEFT','2':'GND','3':'RIGHT'})
    for ref, val, xy, a, b in [
        ('R1','33R',(74,80),'CLK_RAW','MCLK'),
        ('R2','33R',(71,83),'HOST_BCLK','BCLK'),
        ('R3','33R',(75,87),'HOST_LRCLK','LRCLK'),
        ('R4','33R',(71,91),'HOST_DAC_SD','DAC_SD'),
        ('R5','100k',(78,101),'ADC_SD','GND'),
        ('R6','100k',(112,97),'DAC_UNMUTE','GND'),
        ('R7','470R',(115,85),'DAC_L','LINE_L'),
        ('R8','470R',(115,91),'DAC_R','LINE_R'),
        ('R9','2.2k',(92,62),'+3V3','LED_A')]:
        part(ref,val,rfp,xy,{1:a,2:b})
    part('D2','GREEN / power','LED_SMD:LED_0805_2012Metric',(97,62),{1:'GND',2:'LED_A'}, '0805 green LED')
    for i, (x,y) in enumerate(((55,55),(130,55),(55,110),(130,110)),1):
        part('H'+str(i),'M3 / NPTH','MountingHole:MountingHole_3.2mm_M3',(x,y),{})


def schematic():
    # Clear functional panels; global net labels make every connection searchable.
    libs, instances = [], []
    positions = {'J1':(45,48),'D1':(110,48),'U1':(175,48),'Y1':(45,100),'J2':(175,106),'U2':(312,48),'J3':(380,106),'J4':(380,48)}
    positions.update({f'H{i+1}':(175+i*65,238) for i in range(4)})
    passives = [p for p in PARTS if p['ref'] not in positions and p['pins']]
    for i,p in enumerate(passives):
        positions[p['ref']] = (45+(i%6)*65, 154+(i//6)*21)
    for p in PARTS:
        ref=p['ref']; x,y=(round(v/1.27)*1.27 for v in positions[ref]); size=len(p['pins']); h=max(0,size-1)*2.54
        # Inputs on the left, outputs on the right for ICs and clock; passives horizontal.
        if size == 2:
            coords={n:(-7.62 if n=='1' else 7.62,0,0 if n=='1' else 180) for n in p['pins']}
            shape='(rectangle (start -2.54 1.016) (end 2.54 -1.016) (stroke (width 0.254) (type default)) (fill (type none)))'
            if ref.startswith('C'):
                shape=''.join(f'(polyline (pts (xy {xx} -1.524) (xy {xx} 1.524)) (stroke (width 0.254) (type default)) (fill (type none)))' for xx in (-0.762,0.762))
                shape+=''.join(f'(polyline (pts (xy {s*2.54} 0) (xy {s*.762} 0)) (stroke (width 0.254) (type default)) (fill (type none)))' for s in (-1,1))
            elif ref.startswith('D'):
                shape='(polyline (pts (xy -1.27 -1.524) (xy -1.27 1.524)) (stroke (width 0.254) (type default)) (fill (type none))) (polyline (pts (xy -1.27 0) (xy 1.27 1.524) (xy 1.27 -1.524) (xy -1.27 0)) (stroke (width 0.254) (type default)) (fill (type none))) (polyline (pts (xy -2.54 0) (xy 2.54 0)) (stroke (width 0.254) (type default)) (fill (type none)))'
            elif ref.startswith('J'):
                shape='(rectangle (start -2.54 1.524) (end 2.54 -1.524) (stroke (width 0.254) (type default)) (fill (type background)))'
        else:
            coords={n:(-15.24,-i*2.54,0) for i,n in enumerate(p['pins'])}
            shape=f'(rectangle (start -12.7 1.27) (end 12.7 {-h-1.27}) (stroke (width 0.254) (type default)) (fill (type background)))'
        pins=[]
        for n,(px,py,a) in coords.items():
            kind=p['types'].get(n,'passive'); name=p['names'].get(n,n)
            pins.append(f'(pin {kind} line (at {px} {py} {a}) (length {5.08 if size==2 else 2.54}) (name {Q(name)} (effects (font (size 0.85 0.85)))) (number {Q(n)} (effects (font (size 0.85 0.85)))))')
        lib=f'(symbol "H01:{ref}" (pin_names (offset 0.5)) (in_bom yes) (on_board yes) (property "Reference" {Q(ref)} (at 0 4 0) (effects (font (size 1 1)))) (property "Value" {Q(p["value"])} (at 0 -4 0) (effects (font (size 0.8 0.8)))) (symbol "{ref}_0_1" {shape}) (symbol "{ref}_1_1" {"".join(pins)}))'
        libs.append(lib)
        iid=UID(ref)
        instances.append(f'(symbol (lib_id "H01:{ref}") (at {x} {y} 0) (unit 1) (in_bom yes) (on_board yes) (dnp no) (uuid "{iid}") (property "Reference" {Q(ref)} (at {x} {y-6} 0) (effects (font (size 1 1)))) (property "Value" {Q(p["value"])} (at {x} {y-3} 0) (effects (font (size 0.85 0.85)))) (property "Footprint" "H01:{ref}" (at {x} {y} 0) (effects (font (size 1 1)) hide)) (property "Datasheet" {Q(p["source"])} (at {x} {y} 0) (effects (font (size 1 1)) hide)) (property "MPN" {Q(p["mpn"])} (at {x} {y} 0) (effects (font (size 1 1)) hide)) '+''.join(f'(pin "{n}" (uuid "{UID(ref+n)}"))' for n in coords)+f'(instances (project "{NAME}" (path "/{UID(NAME)}" (reference "{ref}") (unit 1)))))')
        for n,net in p['pins'].items():
            px,py,a=coords[n]; ax,ay=x+px,y-py
            if net is None:
                instances.append(f'(no_connect (at {ax} {ay}) (uuid "{UID(ref+n+"nc")}"))'); continue
            bx=ax-3.81 if a==0 else ax+3.81
            instances.append(f'(wire (pts (xy {ax} {ay}) (xy {bx} {ay})) (stroke (width 0) (type default)) (uuid "{UID(ref+n+"w")}"))')
            instances.append(f'(global_label {Q(net)} (shape bidirectional) (at {bx} {ay} {0 if a==0 else 180}) (effects (font (size 0.8 0.8)) (justify {"left" if a==0 else "right"})) (uuid "{UID(ref+n+"l")}"))')
    # Connector-fed rails must have a real external-source declaration for ERC.
    for i,net in enumerate(('5V_IN','5V_PROTECTED','GND')):
        x=round((45+i*65)/1.27)*1.27; y=round(251/1.27)*1.27
        libs.append(f'(symbol "H01:PWR{i}" (power) (pin_names (offset 0)) (in_bom no) (on_board no) (property "Reference" "#FLG" (at 0 0 0) (effects (font (size 1 1)) hide)) (property "Value" "PWR_FLAG" (at 0 0 0) (effects (font (size 1 1)) hide)) (symbol "PWR{i}_1_1" (pin power_out line (at 0 0 0) (length 0) (name "pwr" (effects (font (size 1 1)))) (number "1" (effects (font (size 1 1)))))))')
        instances.append(f'(symbol (lib_id "H01:PWR{i}") (at {x} {y} 0) (unit 1) (in_bom no) (on_board no) (dnp no) (uuid "{UID(net+"flag")}") (property "Reference" "#FLG0{i+1}" (at {x} {y} 0) (effects (font (size 1 1)) hide)) (property "Value" "EXTERNAL SUPPLY" (at {x} {y-3} 0) (effects (font (size 1 1)))) (instances (project "{NAME}" (path "/{UID(NAME)}" (reference "#FLG0{i+1}") (unit 1)))))')
        instances.append(f'(global_label {Q(net)} (shape bidirectional) (at {x} {y} 0) (effects (font (size 1 1)) (justify left)) (uuid "{UID(net+"flaglabel")}"))')
    headings=[(25,20,'KONAET / H-01A AUDIO CARRIER / REV A'),(25,27,'REVIEW PROTOTYPE - External 3.3V FPGA required - Not an AI computer'),(25,35,'01 / PROTECTED 5V INPUT + REGULATOR'),(285,35,'02 / PCM5102A LINE DAC'),(25,87,'03 / CLOCK + HOST INTERFACE'),(25,141,'04 / DECOUPLING, TERMINATION + OUTPUT FILTERS'),(25,261,'48 kHz / 32-bit I2S slots / 16 significant bits / 12.288 MHz host clock'),(25,267,'DAC defaults MUTED. Host must sequence XSMT. J4: line level, >=10 kohm; never a speaker.'),(25,273,'J2 is NOT PMOD. No 5V-tolerant IO. FPGA power is separate.'),(25,279,'External left-channel 3.3V I2S microphone. No inference CPU on carrier.')]
    for x,y,t in headings:
        instances.append(f'(text {Q(t)} (at {x} {y} 0) (effects (font (size {1.5 if y==20 else 1.1} {1.5 if y==20 else 1.1})) (justify left)) (uuid "{UID(t)}"))')
    data=f'(kicad_sch (version 20250114) (generator "konaet_h01") (uuid "{UID(NAME)}") (paper "A3") (title_block (title "KONAET H-01A audio carrier") (date "2026-11-11") (rev "A") (company "KONAET") (comment 1 "External 3.3V FPGA required; physical tests pending")) (lib_symbols {"".join(libs)}) {"".join(instances)} (sheet_instances (path "/" (page "1"))))'
    (OUT/(NAME+'.kicad_sch')).write_text(data,encoding='utf-8')
    (OUT/'H01.kicad_sym').write_text('(kicad_symbol_lib (version 20241209) (generator "konaet_h01") '+''.join(libs).replace('"H01:', '"')+')',encoding='utf-8')


def board(library):
    b=pcb.BOARD(); b.SetCopperLayerCount(2)
    b.GetDesignSettings().SetCopperLayerCount(2)
    b.GetDesignSettings().m_TrackMinWidth=pcb.FromMM(.2)
    b.GetDesignSettings().m_MinClearance=pcb.FromMM(.2)
    nets={n:pcb.NETINFO_ITEM(b,n) for p in PARTS for n in p['pins'].values() if n}
    for n in nets.values(): b.Add(n)
    b.GetDesignSettings().m_CurrentViaSize=pcb.FromMM(.7)
    b.GetDesignSettings().m_CurrentViaDrill=pcb.FromMM(.35)
    for p in PARTS:
        category,foot=p['footprint'].split(':')
        f=pcb.FootprintLoad(str(library/'footprints'/(category+'.pretty')),foot)
        if not f: raise RuntimeError(p['footprint'])
        f.SetReference(p['ref']); f.SetValue(p['value']); f.SetPosition(P(*p['xy'])); f.SetOrientationDegrees(p['angle'])
        f.SetPath(pcb.KIID_PATH('/'+UID(NAME)+'/'+UID(p['ref'])))
        f.SetFPID(pcb.LIB_ID('H01',p['ref']))
        if p['ref'].startswith('H'):f.SetAttributes(f.GetAttributes() & ~pcb.FP_EXCLUDE_FROM_BOM)
        f.Reference().SetTextSize(P(.8,.8)); f.Reference().SetTextThickness(pcb.FromMM(.12))
        f.Reference().SetPosition(P(p['xy'][0],p['xy'][1]-2.8))
        if p['ref']=='R1': f.Reference().SetPosition(P(74,82))
        if p['ref']=='J1': f.Reference().SetPosition(P(56,62))
        if p['ref']=='J3': f.Reference().SetPosition(P(59,94))
        f.Value().SetVisible(False)
        for pad in f.Pads():
            n=p['pins'].get(pad.GetNumber())
            if n: pad.SetNet(nets[n])
            elif p['ref']=='U1' and pad.GetNumber()=='4':
                nc=pcb.NETINFO_ITEM(b,'unconnected-(U1-NC-Pad4)');b.Add(nc);pad.SetNet(nc)
        frozen_models=[]
        for model in f.Models():
            original=re.sub(r'\$\{KICAD\d+_3DMODEL_DIR\}',str(library/'3dmodels').replace('\\','/'),model.m_Filename)
            src=Path(original)
            if not src.exists() and p['ref']=='Y1':
                # Explicit geometric proxy; not an Abracon-verified mechanical model.
                src=library/'3dmodels/Crystal.3dshapes/Crystal_SMD_3225-4Pin_3.2x2.5mm.step'
            if src.exists():
                target=OUT/'models'/src.name; target.parent.mkdir(exist_ok=True)
                shutil.copyfile(src,target)
                model.m_Filename='${KIPRJMOD}/models/'+src.name
                frozen_models.append(model)
            else: raise FileNotFoundError(src)
        f.Models().clear()
        for model in frozen_models: f.Add3DModel(model)
        b.Add(f)
        pcb.PCB_IO_KICAD_SEXPR().FootprintSave(str(OUT/'H01.pretty'),f)
    # Rounded outline, 85 x 65 mm, with four isolated M3 NPTH mounts.
    for (x1,y1,x2,y2) in ((54,50,131,50),(135,54,135,111),(131,115,54,115),(50,111,50,54)):
        edge=pcb.PCB_SHAPE(); edge.SetShape(pcb.SHAPE_T_SEGMENT);edge.SetStart(P(x1,y1));edge.SetEnd(P(x2,y2));edge.SetLayer(pcb.Edge_Cuts);edge.SetWidth(pcb.FromMM(.05));b.Add(edge)
    for start,mid,end in [((131,50),(133.828427,51.171573),(135,54)),((135,111),(133.828427,113.828427),(131,115)),((54,115),(51.171573,113.828427),(50,111)),((50,54),(51.171573,51.171573),(54,50))]:
        edge=pcb.PCB_SHAPE();edge.SetShape(pcb.SHAPE_T_ARC);edge.SetArcGeometry(P(*start),P(*mid),P(*end));edge.SetLayer(pcb.Edge_Cuts);edge.SetWidth(pcb.FromMM(.05));b.Add(edge)
    for t,x,y,s in [('KONAET',92.5,55,2.5),('H-01A / AUDIO CARRIER',108,103,1.15),('REV A / REVIEW PROTOTYPE',108,106,1),('I2S / 48 kHz / 3V3 IO',108,109,1),('5V IN',61,57.5,1),('1:5V  2:GND',65,68.5,.8),('FPGA / NOT PMOD',67,71,1),('MIC I2S',63,92,.8),('L G R / LINE',126,95,.8)]:
        text=pcb.PCB_TEXT(b);text.SetText(t);text.SetPosition(P(x,y));text.SetTextSize(P(s,s));text.SetTextThickness(pcb.FromMM(.15));text.SetLayer(pcb.F_SilkS);b.Add(text)
    b.SetFileName(str(OUT/(NAME+'.kicad_pcb')))
    pcb.SaveBoard(b.GetFileName(),b)
    pcb.ExportSpecctraDSN(b,str(OUT/(NAME+'.dsn')))


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--library',type=Path,required=True);args=ap.parse_args()
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'H01.pretty').mkdir(exist_ok=True)
    circuit(); schematic()
    project={'meta':{'filename':NAME+'.kicad_pro','version':1},
      'net_settings':{'version':3,'classes':[{'name':'Default','clearance':.2,'track_width':.25,'via_diameter':.7,'via_drill':.35,'diff_pair_width':.25,'diff_pair_gap':.25}]},
      'board':{'design_settings':{'rules':{'min_clearance':.2,'min_track_width':.2,'min_via_diameter':.6,'min_through_hole_diameter':.3,'min_hole_clearance':.25,'min_copper_edge_clearance':.5}}}}
    (OUT/(NAME+'.kicad_pro')).write_text(json.dumps(project,indent=2)+'\n')
    (OUT/'fp-lib-table').write_text('(fp_lib_table (version 7) (lib (name "H01")(type "KiCad")(uri "${KIPRJMOD}/H01.pretty")(options "")(descr "Frozen KiCad footprints for H01A")))\n')
    (OUT/'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "H01")(type "KiCad")(uri "${KIPRJMOD}/H01.kicad_sym")(options "")(descr "H01A circuit symbols")))\n')
    (OUT/'circuit.json').write_text(json.dumps({'revision':'A','board_mm':[85,65,1.6],'parts':PARTS},indent=2)+'\n')
    with (OUT/'bom.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['Reference','Value','MPN_or_specification','KiCad_footprint','Datasheet'])
        for p in PARTS: w.writerow([p['ref'],p['value'],p['mpn'],p['footprint'],p['source']])
    board(args.library)
    from sync_h01_fields import sync
    sync()
    print(f'Generated {len(PARTS)} placed components. Routing and validation still required.')


if __name__=='__main__': main()
