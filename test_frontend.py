"""Chromium UI regression test, using set_content and a MOCK Steam adapter.
No real Steam availability assertion is made. Install Playwright only to run tests.
The app itself has no third-party dependency. Launchers do not run this script.
"""
import json
import os
from pathlib import Path
import tempfile
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parent
HTML=(ROOT/'steam_lens.html').read_text(encoding='utf-8')
TEST_LOCAL="const isLocal=()=>location.protocol==='http:'&&['127.0.0.1','localhost'].includes(location.hostname);"
# Supply a deterministic browser-storage shim because about:blank disallows localStorage.
STORAGE='<script>window._testStorage={};Object.defineProperty(window,"localStorage",{value:{getItem:k=>window._testStorage[k]??null,setItem:(k,v)=>window._testStorage[k]=v,removeItem:k=>delete window._testStorage[k]}});</script>'
DOC=HTML.replace('<head>','<head>'+STORAGE,1)
checks=[]
def check(condition,label):
    if not condition:raise AssertionError(label)
    checks.append(label)
    print('PASS',label)

with sync_playwright() as p:
    exe=os.environ.get('CHROMIUM_PATH')
    if not exe and Path('/usr/bin/chromium').exists():exe='/usr/bin/chromium'
    browser=p.chromium.launch(headless=True,**({'executable_path':exe} if exe else {}))
    context=browser.new_context(viewport={'width':1440,'height':1050},accept_downloads=True)
    context.set_default_timeout(5000)
    page=context.new_page();errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.route('https://**/*',lambda route:route.abort())
    page.set_content(DOC,wait_until='domcontentloaded')
    page.wait_for_timeout(100)
    check(page.locator('#metricCount').inner_text()=='36','initial synthetic sample count')
    check(page.locator('.game-card').count()==12,'12-card pagination')
    check('模拟数据' in page.locator('#sourceBanner').inner_text(),'persistent demo disclosure')
    check(page.evaluate('SteamLensTest.wilson(1,1)<SteamLensTest.wilson(950,1000)'),'Wilson penalizes tiny perfect sample')
    check(page.evaluate('SteamLensTest.wilson(0,0)===null'),'zero-review Wilson is unknown')
    check(page.evaluate('SteamLensTest.ratio({reviews:{positive:0,total:0}})===null'),'zero-review ratio is unknown')
    check(page.evaluate('SteamLensTest.recommendation({...SteamLensTest.DEMO[0],price:null}).value===null'),'missing price has no default composite score')
    check(page.evaluate('SteamLensTest.recommendation({...SteamLensTest.DEMO[0],reviews:null}).value===null'),'missing reviews have no default composite score')
    check(page.evaluate('Number.isFinite(SteamLensTest.recommendation(SteamLensTest.DEMO.find(g=>g.isFree&&g.reviews)).value)'),'free game score finite')
    check(page.evaluate("SteamLensTest.sortGames(SteamLensTest.DEMO,'priceAsc').at(-1).price===null"),'unknown price last in ascending sort')
    check(page.evaluate("SteamLensTest.sortGames(SteamLensTest.DEMO,'priceDesc').at(-1).price===null"),'unknown price last in descending sort')
    check(page.evaluate("JSON.stringify(SteamLensTest.parseIds('413150，105600 https://store.steampowered.com/app/413150/?cc=cn'))==='[413150,105600]'"),'ID / URL parsing and deduplication')
    check(page.evaluate("(()=>{try{SteamLensTest.parseIds('https://evil.test/123');return false}catch{return true}})()"),'reject non-Steam URLs')
    check(page.evaluate("SteamLensTest.csvCell('=1+2').includes(\"'=1+2\")"),'CSV formula injection protection')
    check(page.evaluate("(()=>{try{SteamLensTest.normalizeGame({...SteamLensTest.DEMO[0],currency:'USD'});return false}catch{return true}})()"),'reject currency / region mismatch')
    check(page.evaluate("(()=>{try{SteamLensTest.normalizeGame({...SteamLensTest.DEMO[0],reviews:{positive:1,negative:1,total:8}});return false}catch{return true}})()"),'reject inconsistent imported review counts')
    page.locator('#search').fill('戴森')
    check(page.locator('#metricCount').inner_text()=='1','search Chinese name')
    page.locator('#maxPrice').fill('1')
    check(page.locator('#metricCount').inner_text()=='0','filters combine with search')
    page.locator('#resetFilters').click()
    page.locator('[data-preset="value"]').click()
    check(page.evaluate("SteamLensTest.filterGames(SteamLensTest.dataset()).every(g=>g.price<=100&&g.languages.some(x=>['schinese','tchinese'].includes(x))&&g.reviews.total>=1000)"),'Chinese value preset constraints')
    page.locator('#resetFilters').click()
    page.locator('#chineseAudio').check()
    check(page.locator('#metricCount').inner_text()=='3','audio filter separate from text-language support')
    page.locator('#resetFilters').click()
    page.locator('[data-view="table"]').click()
    check(page.locator('tbody tr').count()==12,'table view')
    page.locator('[data-sort="priceAsc"]').click()
    check(page.locator('#sortBy').input_value()=='priceAsc','table price sort ascending')
    page.locator('[data-sort="priceAsc"]').click()
    check(page.locator('#sortBy').input_value()=='priceDesc','table price sort toggles descending')
    page.locator('#resetFilters').click()
    page.locator('[data-view="grid"]').click()
    page.locator('.game-card .favorite-btn').first.click()
    check(page.locator('#favoritesCount').inner_text()=='1','favorite action')
    page.locator('[data-nav="favorites"]').click()
    check(page.locator('#metricCount').inner_text()=='1','favorites view scoped')
    page.locator('[data-nav="discover"]').click()
    for i in range(4):page.locator('.game-card [data-compare]').nth(i).check()
    check(page.evaluate('SteamLensTest.state.compare.size===4'),'select four comparison games')
    page.locator('.game-card [data-compare]').nth(4).click()
    check(page.evaluate('SteamLensTest.state.compare.size===4'),'comparison cap enforced')
    page.locator('#compareBtn').click()
    check(page.locator('.compare-table th').count()==5,'four-game comparison table with labels')
    check('模拟记录' in page.locator('.compare-table').inner_text(),'comparison preserves source warning')
    page.locator('#closeDialog').click();page.locator('#clearCompare').click()
    page.locator('.game-title').first.click()
    page.get_by_role('tab',name='语言与配置').click()
    check('语言：支持语言与配音分开看' in page.locator('#dialogBody').inner_text(),'detail language / audio distinction')
    page.get_by_role('tab',name='评分依据').click()
    check('Wilson' in page.locator('#dialogBody').inner_text(),'detail scoring explanation')
    page.locator('#closeDialog').click()
    page.locator('#weightsBtn').click()
    page.evaluate("document.querySelectorAll('[data-weight]').forEach(x=>x.value=0)")
    page.locator('[data-action="applyWeights"]').click()
    check(page.locator('#dialog').evaluate('(e)=>e.open'),'zero total weights not accepted')
    page.locator('[data-action="resetWeights"]').click()
    page.locator('[data-action="applyWeights"]').click()
    check(not page.locator('#dialog').evaluate('(e)=>e.open'),'valid weights apply and close')
    page.locator('[data-nav="analytics"]').click()
    check(page.locator('#analytics .panel').count()==6,'six analytics panels')
    check(page.locator('svg.scatter circle').count()==34,'scatter excludes missing-price / review records')
    page.locator('[data-nav="discover"]').click()
    page.locator('#region').select_option('hk')
    check(page.locator('#metricCount').inner_text()=='0','region change never reuses CNY quotes')
    check(page.locator('#dataMode').input_value()=='live','non-CNY demo switches to empty region live catalog')
    page.locator('#dataMode').select_option('demo')
    check(page.locator('#region').input_value()=='cn','returning to demo explicitly selects its CNY region')
    with tempfile.TemporaryDirectory() as temp:
        page.locator('#exportBtn').click()
        with page.expect_download() as dl:page.locator('[data-action="exportCsv"]').click()
        path=Path(temp)/'export.csv';dl.value.save_as(path)
        text=path.read_text(encoding='utf-8-sig')
        check('数据来源' in text and '演示' in text and len(text.splitlines())==37,'CSV all filtered rows and source labels')
        with page.expect_download() as dl:page.locator('[data-action="exportJson"]').click()
        path=Path(temp)/'export.json';dl.value.save_as(path)
        exported=json.loads(path.read_text(encoding='utf-8'))
        check(exported['mode']=='demo' and len(exported['games'])==36,'JSON roundtrip structure and provenance')
        page.locator('#closeDialog').click()
        page.on('dialog',lambda dialog:dialog.accept())
        page.locator('#fileInput').set_input_files(str(path))
        page.wait_for_timeout(100)
        check(page.locator('#dataMode').input_value()=='import','JSON imports into isolated import catalog')
        check(page.evaluate("SteamLensTest.dataset().every(g=>g.source==='demo')"),'import never launders demo as real data')
        exported['mode']='import'
        exported['games']=exported['games'][:1]
        exported['games'][0]['source']='steam'
        exported['games'][0]['name']='<img src=x onerror="window.__xss=1">bad name'
        bad=Path(temp)/'xss.json';bad.write_text(json.dumps(exported),encoding='utf-8')
        page.locator('#fileInput').set_input_files(str(bad));page.wait_for_timeout(100)
        check(page.evaluate('window.__xss===undefined'),'imported title is escaped, no XSS')
        check(page.evaluate("SteamLensTest.dataset().find(g=>g.appid===413150).source==='imported'"),'imported claimed Steam record becomes unverified import')
    # Offline network button shows a setup guide, not fake refresh success.
    page.locator('#dataMode').select_option('demo');page.locator('#connectBtn').click()
    page.get_by_text('其他启动方式',exact=True).click()
    check('python server.py' in page.locator('#dialogBody').inner_text(),'standalone network setup explanation')
    check(page.locator('[data-action="fetchIds"]').is_disabled(),'standalone cannot pretend to fetch locally')
    page.locator('#closeDialog').click()
    page.evaluate("document.querySelector('#toast').hidden=true")
    page.evaluate('window.scrollTo(0,0)');page.wait_for_timeout(50)
    page.screenshot(path=str(ROOT/'preview-desktop.png'),full_page=True)
    check(not errors,'no JavaScript page errors in desktop UI tests')
    # A separate document replaces only the origin check and fetch function to exercise queue logic.
    mockpage=context.new_page();mockpage.route('https://**/*',lambda r:r.abort())
    mockdoc=DOC.replace(TEST_LOCAL,'const isLocal=()=>true;')
    assert mockdoc!=DOC,'Test-only local origin substitution must match exactly.'
    mockpage.set_content(mockdoc,wait_until='domcontentloaded')
    mockpage.evaluate('''() => {
      window._mockCalls=[];
      const good=structuredClone(SteamLensTest.DEMO[0]);
      good.name='Mock API fixture (not real Steam data)';good.source='steam';good.detailsAt='2026-09-29T08:00:00Z';good.reviewsAt=good.detailsAt;
      window.fetch=async(url,options)=>{
       window._mockCalls.push({url,options});
       if(url.startsWith('/api/health'))return new Response(JSON.stringify({service:'steam-lens'}));
       if(url.startsWith('/api/app')){const q=new URL(url,'http://localhost').searchParams;
        if(q.get('appid')==='413150')return new Response(JSON.stringify({game:good}));
        return new Response(JSON.stringify({error:'mock failure (no upstream request)'}),{status:502});
       }
       return new Response('{}',{status:500});
      };
    }''')
    mockpage.locator('#connectBtn').click()
    mockpage.locator('#networkAdvanced summary').click()
    mockpage.locator('#appIdsInput').fill('413150, 105600')
    mockpage.locator('[data-action="fetchIds"]').click()
    mockpage.wait_for_function('SteamLensTest.state.busy===false&&SteamLensTest.state.mode==="live"')
    check(mockpage.evaluate('SteamLensTest.dataset().length===1'),'partial success only stores fetched game')
    check(mockpage.evaluate('SteamLensTest.DEMO.length===36'),'network task leaves demo library unchanged')
    mockpage.locator('.network-log summary').click()
    check('失败 1' in mockpage.locator('#networkLog').inner_text(),'partial failure visible in acquisition log')
    check(mockpage.evaluate("window._mockCalls.filter(x=>x.url.startsWith('/api/app')).every(x=>x.options.headers['X-Steam-Lens']==='1')"),'adapter requests include same-origin app header')
    mockpage.locator('#appIdsInput').fill('105600')
    mockpage.locator('[data-action="fetchIds"]').click()
    mockpage.wait_for_function('SteamLensTest.state.busy===false')
    check(mockpage.evaluate('SteamLensTest.dataset().length===1'),'failed refresh retains previous real-catalog record')
    # Mobile rendering, with actual JS source and no origin substitution.
    mobile=context.new_page();mobile.set_viewport_size({'width':390,'height':844})
    mobile.route('https://**/*',lambda r:r.abort());mobile.set_content(DOC,wait_until='domcontentloaded')
    check(mobile.evaluate('document.documentElement.scrollWidth<=window.innerWidth'),'mobile viewport no horizontal overflow')
    check(not mobile.locator('#filtersPanel').evaluate('(e)=>e.open'),'mobile filters initially collapsed')
    mobile.screenshot(path=str(ROOT/'preview-mobile.png'),full_page=True)
    browser.close()
(ROOT/'frontend-test-results.json').write_text(json.dumps({'checks':len(checks),'passed':checks,'liveSteamVerified':False},ensure_ascii=False,indent=2),encoding='utf-8')
print(f'\n{len(checks)} frontend checks passed. Live Steam API was NOT used or verified.')
