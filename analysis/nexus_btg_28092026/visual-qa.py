"""Local browser QA: controls, links, responsive overflow and static fallback."""
import itertools
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'analysis/nexus_btg_28092026'
URL = 'http://127.0.0.1:4173/nexus_btg_28092026.html'
results=[]
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    for width in [1440,390]:
        page=browser.new_page(viewport={'width':width,'height':950})
        errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(URL,wait_until='networkidle')
        page.screenshot(path=str(OUT/f'qa-{width}-hero.png'))
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        page.locator('#transferencia figure').screenshot(path=str(OUT/f'qa-{width}-transfer.png'))
        page.locator('#sensibilidade').screenshot(path=str(OUT/f'qa-{width}-scenarios.png'))
        if width==1440:
            for turn,target,score,region,association in itertools.product(['1t','2t'],['hist','.75','.85'],['central','suave','estrito'],['2022','declarado'],['0','-1','1']):
                for key,value in zip(['turn','target','score','region','association'],[turn,target,score,region,association],strict=True):
                    page.locator('#lv-'+key).select_option(value)
                output=page.locator('#lv-result').inner_text()
                assert 'NaN' not in output and 'dos válidos' in output
            links=page.locator('a[href]').evaluate_all('(els)=>els.map(e=>e.getAttribute("href"))')
            for href in links:
                if href.startswith('#'):
                    assert page.locator(href).count(),href
                elif not href.startswith(('http','mailto:')):
                    file=href.split('#')[0]
                    assert (ROOT/'docs'/file).exists(),href
        assert not errors,errors
        results.append({'width':width,'overflow':False,'errors':errors,'sections':page.locator('main section').count()})
        page.close()
    page=browser.new_page(java_script_enabled=False)
    page.goto(URL,wait_until='networkidle')
    assert page.locator('#lv-result').is_visible()
    assert page.locator('#fontes').is_visible()
    browser.close()
(OUT/'visual-qa.json').write_text(json.dumps(results,indent=2)+'\n')
print(results)
