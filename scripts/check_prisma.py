"""Render the standalone Prisma UI in PT/EN and exercise its actual controls.

Serve a Pages build first. Requires Playwright plus Chrome on Windows, or an
installed Playwright Chromium on other platforms. No microphone is auto-started.
Screenshots and the report go to artifacts/prisma-review (not the public site).
"""
from __future__ import annotations

import argparse
import io
import json
import math
import platform
import re
import struct
import wave
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
WIDTHS = (320, 390, 768, 1024, 1280, 1440, 1920)


def run(url: str, flows_only: bool = False):
    url = url.rstrip('/') + '/'
    output = ROOT / 'artifacts' / 'prisma-review'
    output.mkdir(parents=True, exist_ok=True)
    report = {'status': 'RUNNING', 'browser': '', 'layouts': [], 'flows': []}
    with sync_playwright() as p:
        options = {'channel': 'chrome'} if platform.system() == 'Windows' else {}
        browser = p.chromium.launch(headless=True, **options)
        report['browser'] = browser.version
        for locale in (() if flows_only else ('pt-BR', 'en-US')):
            for width in WIDTHS:
                context = browser.new_context(locale=locale, viewport={'width': width, 'height': 900}, service_workers='block')
                page = context.new_page()
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.goto(url)
                page.locator('.product-card').first.wait_for()
                page.evaluate('document.fonts.ready')

                def capture(name, dialog=None):
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (locale, width, name, 'page overflow')
                    if dialog:
                        box = page.locator(dialog).bounding_box()
                        assert box and box['x'] >= 0 and box['x'] + box['width'] <= width + 1, (locale, width, name, box)
                        assert box['height'] <= 901, (locale, width, name, box)
                    page.screenshot(path=str(output / f'{locale}-{width}-{name}.png'))

                assert page.locator('html').get_attribute('lang') == ('pt-BR' if locale == 'pt-BR' else 'en')
                assert page.locator('body').get_attribute('data-room-style') == 'prisma'
                overlaps = page.locator('.site-header').evaluate('''header => {
                    const boxes=[...header.children].filter(e=>getComputedStyle(e).display!=='none').map(e=>e.getBoundingClientRect());
                    return boxes.some((a,i)=>boxes.slice(i+1).some(b=>Math.min(a.right,b.right)-Math.max(a.left,b.left)>2 && Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top)>2));
                }''')
                assert not overlaps, (locale, width, 'header overlap')
                capture('home')
                page.locator('[data-glass-open]').click()
                capture('appearance', '#glass-settings-dialog')
                page.locator('.glass-settings-close').click()
                page.locator('[data-desk-view-button="research"]').first.click()
                if locale == 'pt-BR':
                    expect(page.locator('#workspace-query')).to_have_attribute('placeholder', 'O que você quer pesquisar?')
                capture('research')
                page.locator('[data-desk-view-button="guide"]').first.click()
                capture('guide')
                page.locator('[data-desk-view-button="discover"]').first.click()
                page.locator('.compare-check').nth(0).click()
                page.locator('.compare-check').nth(1).click()
                page.locator('#compare-open').click()
                capture('comparison', '#compare-dialog')
                page.locator('[data-close="compare-dialog"]').click()
                page.locator('.add-small:not([disabled])').first.click()
                page.locator('#bag-button').click()
                capture('bag', '#cart-dialog')
                page.locator('#checkout-button').click()
                page.locator('#checkout-dialog[open]').wait_for()
                capture('checkout', '#checkout-dialog')
                page.goto(url + 'sound-lab/')
                page.locator('#piano button').first.wait_for()
                page.evaluate('document.fonts.ready')
                capture('sound')
                assert not errors, (locale, width, errors)
                report['layouts'].append({'locale': locale, 'width': width, 'height': 900, 'views': 8, 'overflow': 0, 'status': 'PASS'})
                context.close()

        context = browser.new_context(locale='pt-BR', viewport={'width': 1280, 'height': 900}, service_workers='block')
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(url)
        page.locator('.product-card').first.wait_for()
        page.locator('#catalog-query').fill('no-such-instrument-prisma-check')
        page.locator('#catalog-form').evaluate('e=>e.requestSubmit()')
        expect(page.locator('#catalog-grid .empty-state')).to_contain_text('Nenhum instrumento encontrado')
        page.locator('#catalog-grid .empty-state button').click()
        expect(page.locator('.product-card')).to_have_count(12)
        page.locator('#studio-query').fill('GD20')
        page.locator('#studio-search').evaluate('e=>e.requestSubmit()')
        expect(page.locator('.product-card')).to_have_count(1)
        expect(page.locator('.product-name')).to_contain_text('GD20')
        page.locator('#catalog-query').fill('')
        page.locator('#catalog-form').evaluate('e=>e.requestSubmit()')
        expect(page.locator('.product-card')).to_have_count(12)
        report['flows'].extend(['empty_results_and_reset', 'header_catalog_search'])

        page.locator('.compare-check').nth(0).click()
        page.locator('.compare-check').nth(1).click()
        page.locator('[data-desk-view-button="research"]').first.click()
        expect(page.locator('#compare-tray')).not_to_be_visible()
        page.locator('[data-desk-view-button="discover"]').first.click()
        expect(page.locator('#compare-tray')).to_be_visible()
        page.locator('#compare-clear').click()
        expect(page.locator('#compare-tray')).not_to_be_visible()
        report['flows'].append('comparison_preserved_across_views')

        page.locator('.add-small:not([disabled])').first.click()
        page.locator('#bag-button').click()
        page.locator('.cart-quantity button').nth(1).click()
        expect(page.locator('.cart-quantity>span')).to_have_text('2')
        page.locator('.cart-quantity button').nth(0).click()
        expect(page.locator('.cart-quantity>span')).to_have_text('1')
        before = page.evaluate("KonaetRuntime.request('/api/sandbox/wallet').then(w=>w.balance_cents)")
        page.locator('#checkout-button').click()
        page.locator('#checkout-dialog[open]').wait_for()
        expect(page.locator('.checkout-info .pill')).to_contain_text('SEM COBRANÇA')
        page.locator('.code-style-picker select').select_option('orbit')
        with page.expect_download() as downloaded:
            page.locator('.code-actions a').click()
        assert downloaded.value.suggested_filename.endswith('.svg')
        downloaded.value.save_as(str(output / 'checkout.svg'))
        page.locator('.sandbox-actions .primary').click()
        expect(page.locator('.sandbox-receipt')).to_contain_text('TESTE APROVADO')
        after = page.evaluate("KonaetRuntime.request('/api/sandbox/wallet').then(w=>w.balance_cents)")
        assert after < before
        page.screenshot(path=str(output / 'test-approved.png'))
        page.locator('[data-close="checkout-dialog"]').click()
        page.locator('[data-studio-target="wallet-open"]').click()
        expect(page.locator('#wallet-transactions')).to_contain_text('Teste aprovado')
        page.locator('#wallet-topup').click()
        expect(page.locator('#wallet-topup')).to_be_enabled()
        assert page.evaluate("KonaetRuntime.request('/api/sandbox/wallet').then(w=>w.balance_cents)") > after
        page.locator('[data-workspace-close="wallet-dialog"]').click()
        page.locator('.add-small:not([disabled])').first.click()
        page.locator('#bag-button').click()
        page.locator('[name="checkout-method"][value="card"]').check()
        page.locator('#checkout-button').click()
        before_decline = page.evaluate("KonaetRuntime.request('/api/sandbox/wallet').then(w=>w.balance_cents)")
        page.locator('.sandbox-actions .secondary').click()
        expect(page.locator('.sandbox-receipt')).to_contain_text('TESTE RECUSADO')
        assert page.evaluate("KonaetRuntime.request('/api/sandbox/wallet').then(w=>w.balance_cents)") == before_decline
        page.locator('[data-close="checkout-dialog"]').click()
        report['flows'].extend(['bag_quantity', 'checkout_art_download', 'sandbox_approve', 'wallet_topup', 'sandbox_decline'])

        page.locator('[data-studio-target="hardware-open"]').click()
        expect(page.locator('#hardware-chart svg')).to_have_count(1)
        page.locator('#hardware-capacity').fill('2')
        page.locator('#hardware-run').click()
        expect(page.locator('#hardware-run')).to_be_enabled()
        expect(page.locator('#hardware-stats')).to_contain_text('recusados')
        page.screenshot(path=str(output / 'logic.png'))
        page.locator('[data-workspace-close="hardware-dialog"]').click()
        page.locator('.studio-more>summary').click()
        page.locator('[data-studio-target="connections-open"]').click()
        connection_count = page.evaluate("KonaetRuntime.request('/api/capabilities').then(c=>6+c.research.length)")
        expect(page.locator('.connection-card')).to_have_count(connection_count)
        page.screenshot(path=str(output / 'connections.png'))
        page.locator('[data-workspace-close="connections-dialog"]').click()
        report['flows'].extend(['logic_trace_with_changed_capacity', 'connection_states'])

        page.locator('#hero-ask').click()
        expect(page.locator('#message-input')).to_have_attribute('placeholder', 'Pergunte sobre um instrumento…')
        page.locator('#message-input').fill('Quero um violão até R$ 1.000,00')
        page.locator('#chat-form').evaluate('e=>e.requestSubmit()')
        expect(page.locator('.message.assistant').last).to_contain_text('R$')
        page.locator('#message-input').fill('Quanto custa o Takamine GD20?')
        page.locator('#chat-form').evaluate('e=>e.requestSubmit()')
        expect(page.locator('.message.assistant').last).to_contain_text('Takamine GD20')
        page.screenshot(path=str(output / 'assistant-pt.png'))
        page.locator('[data-close="assistant-dialog"]').click()
        report['flows'].append('portuguese_assistant_budget_and_exact_model')

        page.locator('[data-desk-view-button="research"]').first.click()
        external = re.compile(r'^https://')
        page.route(external, lambda route: route.abort())
        page.locator('#workspace-query').fill('audio synthesis')
        page.locator('#workspace-scope').select_option('knowledge')
        page.locator('#workspace-run').click()
        expect(page.locator('#workspace-run')).to_be_enabled(timeout=15000)
        assert page.locator('#research-sources .source-card').count() == 0
        expect(page.locator('#research-export')).to_be_disabled()
        assert page.locator('#research-answer').inner_text()
        page.unroute(external)
        report['flows'].append('unavailable_research_has_no_invented_sources')

        page.locator('.studio-more>summary').click()
        page.locator('[data-site-language]').select_option('en')
        expect(page.locator('html')).to_have_attribute('lang', 'en')
        expect(page.locator('#workspace-query')).to_have_attribute('placeholder', 'What would you like to discover?')
        page.reload()
        expect(page.locator('html')).to_have_attribute('lang', 'en')
        page.locator('[data-glass-open]').click()
        page.locator('[data-room-style-option="classic"]').click()
        expect(page.locator('body')).to_have_attribute('data-room-style', 'classic')
        page.locator('[data-room-style-option="prisma"]').click()
        page.locator('[data-prisma-light="follow"]').click()
        page.locator('#glass-accent').evaluate("e=>{e.value='#75c7ff';e.dispatchEvent(new Event('input',{bubbles:true}))}")
        page.locator('#glass-edge').evaluate("e=>{e.value='4';e.dispatchEvent(new Event('input',{bubbles:true}))}")
        with page.expect_download() as downloaded:
            page.locator('#glass-export').click()
        saved = output / 'look.json'
        downloaded.value.save_as(str(saved))
        assert json.loads(saved.read_text())['edge'] == 4
        page.locator('#glass-reset').click()
        page.locator('#glass-file').set_input_files(str(saved))
        expect(page.locator('#glass-edge')).to_have_value('4')
        page.locator('#glass-file').set_input_files({'name': 'invalid.json', 'mimeType': 'application/json', 'buffer': b'{"schema":"wrong"}'})
        expect(page.locator('#glass-status')).to_contain_text('not a KONAET')
        expect(page.locator('#glass-edge')).to_have_value('4')
        page.locator('#glass-motion').check()
        expect(page.locator('body')).to_have_attribute('data-prisma-light', 'fixed')
        page.locator('.glass-settings-close').click()
        page.goto(url + 'sound-lab/')
        expect(page.locator('body')).to_have_attribute('data-prisma-light', 'fixed')
        assert page.locator('body').evaluate("e=>e.style.getPropertyValue('--prisma-edge')") == '4px'
        assert page.locator('#play-chord').evaluate("e=>getComputedStyle(e).backgroundImage").find('117, 199, 255') >= 0
        report['flows'].extend(['language_switch_and_persistence', 'original_glass_available', 'look_export_import_and_invalid_file', 'reduced_motion', 'look_shared_with_sound_lab'])

        page.locator('#play-chord').click()
        expect(page.locator('#audio-state')).to_contain_text('Generated chord')
        page.wait_for_function("!document.querySelector('#explain-sound').disabled")
        page.locator('#explain-sound').click()
        expect(page.locator('#coach-facts p')).not_to_have_count(0)
        page.locator('#stop-audio').click()
        expect(page.locator('#signal-source')).to_have_text('OFF')
        page.locator('#metronome').click()
        expect(page.locator('#metronome')).to_have_attribute('aria-pressed', 'true')
        page.locator('#stop-audio').click()
        expect(page.locator('#metronome')).to_have_attribute('aria-pressed', 'false')
        page.locator('#build-program').click()
        expect(page.locator('#play-hardware')).to_be_enabled()
        expect(page.locator('#program-code')).to_contain_text('localparam')
        page.locator('#play-hardware').click()
        expect(page.locator('#audio-state')).to_contain_text('Digital-core reference')
        page.locator('#stop-audio').click()
        with page.expect_download() as downloaded:
            page.locator('#download-program').click()
        assert downloaded.value.suggested_filename.endswith('.svh')
        with page.expect_download() as downloaded:
            page.locator('#download-study').click()
        assert downloaded.value.suggested_filename.endswith('.wav')
        report['flows'].extend(['chord_play_and_stop', 'checked_music_explanation', 'metronome_start_stop', 'digital_core_generation_and_play', 'parameters_and_wav_download'])

        samples = io.BytesIO()
        with wave.open(samples, 'wb') as wav:
            wav.setparams((1, 2, 22050, 22050, 'NONE', 'not compressed'))
            wav.writeframes(b''.join(struct.pack('<h', round(4000 * math.sin(2 * math.pi * 440 * n / 22050))) for n in range(22050)))
        page.locator('#audio-file').set_input_files({'name': 'a440.wav', 'mimeType': 'audio/wav', 'buffer': samples.getvalue()})
        expect(page.locator('#play-file')).to_be_enabled()
        page.locator('#play-file').click()
        expect(page.locator('#audio-state')).to_contain_text('Local file')
        page.locator('#clear-file').click()
        expect(page.locator('#play-file')).to_be_disabled()
        expect(page.locator('#signal-source')).to_have_text('OFF')
        assert not errors, errors
        report['flows'].append('local_wav_load_play_and_clear')
        context.close()
        browser.close()
    report['status'] = 'PASS'
    (output / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='http://127.0.0.1:8765/')
    parser.add_argument('--flows-only', action='store_true', help='Debug flows without repeating the layout captures')
    args = parser.parse_args()
    run(args.url, args.flows_only)
