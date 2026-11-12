"""Reject stale CAD records/exports before rerunning tool validation."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'hardware/h01-audio'
record=json.loads((OUT/'validation.json').read_text())
assert record['status']=='PASS' and record['physical_tested'] is False
assert record['fabrication_approved'] is False
for rel,sha in record['sha256'].items():
    path=(ROOT/rel).resolve()
    assert path.is_relative_to(OUT.resolve())
    assert hashlib.sha256(path.read_bytes().replace(b'\r\n',b'\n')).hexdigest()==sha,rel
exports=json.loads((OUT/'exports.json').read_text())
assert exports['source_pcb_sha256']==record['sha256']['hardware/h01-audio/konaet-h01.kicad_pcb']
assert exports['source_schematic_sha256']==record['sha256']['hardware/h01-audio/konaet-h01.kicad_sch']
for rel,sha in exports['exports'].items():
    path=(OUT/rel).resolve();assert path.is_relative_to(OUT.resolve())
    assert hashlib.sha256(path.read_bytes()).hexdigest()==sha,rel
print('Current CAD source and exported deliverables match recorded hashes.')
