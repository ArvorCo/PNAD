"""Test forecast on file:// as used by the user; no fetch/server dependency."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'analysis/reponderacao/validos'
URL = (ROOT / 'docs/reponderacao_pnad.html').as_uri()
results = []
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    for width in [1440, 390]:
        page = browser.new_page(viewport={'width': width, 'height': 1000})
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto(URL, wait_until='networkidle')
        section = page.locator('#projecao-validos')
        section.scroll_into_view_if_needed()
        section.screenshot(path=str(OUT / f'forecast-{width}.png'))
        data = json.loads(page.locator('#vf-data').text_content())
        for mode in data['modes']:
            page.locator(f'[data-vf-mode="{mode}"]').click()
            assert page.locator(f'[data-vf-mode="{mode}"]').get_attribute('aria-pressed') == 'true'
            for scenario in (data['scenario_labels'] if mode == 'modelo' else ['central']):
                if mode == 'modelo':
                    page.locator('#vf-scenario').select_option(scenario)
                for ballot, block in data['ballots'].items():
                    card = section.locator(f'article[data-ballot="{ballot}"]')
                    for candidate, value in block['scenarios'][scenario]['aggregate'][mode].items():
                        row = card.locator(f'[data-candidate="{candidate}"]')
                        assert row.locator('b').inner_text() == f'{value:.1f}%'.replace('.', ',')
                        assert abs(float(row.locator('.vf-bar').evaluate('(e)=>e.style.width').replace('%','')) - value) < .0001
                    assert 'NaN' not in card.inner_text()
        page.locator('#vf-scenario').select_option('central')
        section.locator('details').evaluate_all('(els)=>els.forEach(e=>e.open=true)')
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), width
        assert not errors, errors
        results.append({'width': width, 'controls': 'passed', 'overflow_all_forecast_details_open': False, 'page_errors': errors})
        page.close()
    page = browser.new_page(java_script_enabled=False)
    page.goto(URL, wait_until='networkidle')
    assert page.locator('#projecao-validos .vf-card').count() == 2
    assert not page.locator('.vf-controls').is_visible()
    expected = json.loads((ROOT / 'docs/assets/reponderacao_validos.json').read_text())['ballots']['1t']['scenarios']['central']['aggregate']['modelo']['lula']
    assert f'{expected:.1f}%'.replace('.', ',') in page.locator('#projecao-validos').inner_text()
    browser.close()
(OUT / 'qa.json').write_text(json.dumps(results, indent=2) + '\n')
print(results)
