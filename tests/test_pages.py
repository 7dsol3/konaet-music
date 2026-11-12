import hashlib
import importlib.util
import json
from html.parser import HTMLParser
from pathlib import Path
from uuid import uuid4
import pytest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('build_pages',ROOT/'scripts/build_pages.py')
builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)


def test_bundled_public_catalog_matches_current_source():
    assert json.loads((ROOT/'deploy/browser/catalog.json').read_text(encoding='utf-8'))==builder.export_catalog()


def test_standalone_build_routes_assets_and_contains_no_customer_data():
    out=builder.build(ROOT/'dist'/('pages-test-'+uuid4().hex))
    class Links(HTMLParser):
        def handle_starttag(self,tag,attrs):
            for key,value in attrs:
                if key in {'href','src'} and value.startswith('/'):
                    assert value.startswith('/konaet-music/'),value
                    path=out/value.removeprefix('/konaet-music/').split('#')[0]
                    assert path.exists(),value
    for name in ['index.html','sound-lab/index.html','docs/index.html']:
        text=(out/name).read_text(encoding='utf-8');assert 'trycloudflare.com' not in text;Links().feed(text)
    report=json.loads((out/'pages-build.json').read_text())
    for path,sha in report['files'].items():assert hashlib.sha256((out/path).read_bytes()).hexdigest()==sha
    assert not list(out.rglob('*customers*')) and not list(out.rglob('*orders*'))
    with pytest.raises(ValueError):builder.build(ROOT,base='/')
    with pytest.raises(ValueError):builder.build(ROOT/'dist/pages-test',base='//example.org/')


def test_browser_qr_dependency_is_frozen_and_attributed():
    vendor=ROOT/'deploy/browser/vendor'
    provenance=json.loads((vendor/'provenance.json').read_text())
    assert hashlib.sha256((vendor/'qrcode.js').read_bytes()).hexdigest()==provenance['sha256']
    assert 'Kazuhiko Arase' in (vendor/'QRCODE-LICENSE.txt').read_text()
