"""Offline cover-loader regression tests. No live Steam traffic.
Run after build.py. Requires Playwright + Chromium for browser tests only.
PNG test fixtures are synthetic color blocks, not real game artwork.
"""
import copy
import json
import os
from pathlib import Path
import struct
import zlib
from playwright.sync_api import sync_playwright
import server
from test_server import APP, REV, STAMP

ROOT=Path(__file__).resolve().parent
HTML=(ROOT/'steam_lens.html').read_text(encoding='utf-8')
STORAGE='''<script>window._testStorage={'steam-lens.v1':'{"covers":false}'};Object.defineProperty(window,"localStorage",{value:{getItem:k=>window._testStorage[k]??null,setItem:(k,v)=>window._testStorage[k]=v,removeItem:k=>delete window._testStorage[k]}});</script>'''
DOC=HTML.replace('<head>','<head>'+STORAGE,1)
PRIMARY='https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/413150/deadbeef/header_schinese.jpg?t=10'
ALTERNATE=PRIMARY.replace('shared.fastly','shared.akamai')
checks=[]
def check(condition,label):
    if not condition:raise AssertionError(label)
    checks.append(label);print('PASS',label)

def png(width=460,height=215):
    def chunk(tag,data):return struct.pack('!I',len(data))+tag+data+struct.pack('!I',zlib.crc32(tag+data)&0xffffffff)
    raw=b''.join(b'\0'+bytes((40,95,130))*width for _ in range(height))
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',width,height,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b'')
IMAGE=png();TINY=png(1,1)

# Real upstream-shaped metadata is preserved, not replaced by an invented URL.
raw=copy.deepcopy(APP);raw['header_image']=PRIMARY;raw['capsule_image']=PRIMARY.replace('header_schinese','capsule_616x353');raw['capsule_imagev5']=PRIMARY.replace('header_schinese','capsule_184x69')
g=server.normalize_app(413150,'cn',raw,REV,STAMP,STAMP,[])
check(g['headerImage']==PRIMARY,'backend preserves header path/hash/query')
check(g['capsuleImage']==raw['capsule_image'] and g['capsuleImageV5']==raw['capsule_imagev5'],'backend preserves alternate capsule metadata')
check(server.safe_steam_image(PRIMARY,105600) is None,'backend rejects another game AppID')
check(server.safe_steam_image(PRIMARY.replace('shared.fastly.steamstatic.com','evil.example'),413150) is None,'backend rejects non-Steam hosts')
check(server.safe_steam_image(PRIMARY.replace('https:','http:'),413150)==PRIMARY,'backend upgrades allowed legacy HTTP asset to HTTPS')
check(server.safe_steam_image('javascript:alert(1)',413150) is None,'backend rejects script URL')
check(server.safe_steam_image(PRIMARY.replace('https://','https://evil@'),413150) is None,'backend rejects credentials in URL')

with sync_playwright() as p:
    exe=os.environ.get('CHROMIUM_PATH') or ('/usr/bin/chromium' if Path('/usr/bin/chromium').exists() else None)
    browser=p.chromium.launch(headless=True,**({'executable_path':exe} if exe else {}))
    errors=[]
    def page_for(handler,viewport=None):
        page=browser.new_page(viewport=viewport or {'width':1440,'height':1000})
        page.set_default_timeout(5000)
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.route('https://**/*',handler)
        page.set_content(DOC,wait_until='domcontentloaded')
        return page
    def mount(page,appid=413150,header=PRIMARY,extra=''):
        page.evaluate('''({appid,header,extra})=>{
            SteamLensTest.state.covers=true;
            let host=document.getElementById('coverFixture');
            if(!host){host=document.createElement('div');host.id='coverFixture';host.style.cssText='width:460px;max-width:95vw;position:fixed;left:5px;top:110px;z-index:200;background:#121b29';document.body.append(host);}
            const game={...SteamLensTest.DEMO[0],appid,headerImage:header};
            host.innerHTML=SteamLensTest.coverMarkup(game,extra)+'</div>';
            SteamLensTest.CoverLoader.init(host);
        }''',{'appid':appid,'header':header,'extra':extra})
    def settle(page,status='loaded'):
        page.wait_for_function('(status)=>document.querySelector("#coverFixture .cover").dataset.coverState===status',arg=status)
    def current(page):return page.locator('#coverFixture .cover-image').get_attribute('src')

    calls=[]
    def fallback(route):
        calls.append(route.request.url)
        if route.request.url==PRIMARY:route.fulfill(status=404,body='missing')
        else:route.fulfill(status=200,content_type='image/png',body=IMAGE)
    page=page_for(fallback)
    check(len(calls)==0,'covers-off setting sends no initial image request')
    check(page.evaluate('(u)=>SteamLensTest.normalizeGame({...SteamLensTest.DEMO[0],headerImage:null,header_image:u}).headerImage',PRIMARY)==PRIMARY,'frontend preserves raw API header_image')
    check(page.evaluate('(u)=>SteamLensTest.normalizeGame({...SteamLensTest.DEMO[0],headerImage:u}).headerImage',PRIMARY)==PRIMARY,'frontend round-trip keeps normalized headerImage')
    check(page.evaluate('(u)=>SteamLensTest.coverCandidates({...SteamLensTest.DEMO[0],headerImage:u})[0]',PRIMARY)==PRIMARY,'exact official path is first candidate')
    check(page.evaluate('(u)=>SteamLensTest.safeSteamImage(u,105600)',PRIMARY) is None,'frontend rejects image for wrong game')
    check(page.evaluate("SteamLensTest.safeSteamImage('https://steamstatic.com.evil.example/steam/apps/413150/header.jpg',413150)") is None,'frontend rejects lookalike CDN suffix')
    check(page.evaluate("SteamLensTest.safeSteamImage('data:image/svg+xml,<svg/>',413150)") is None,'frontend rejects executable imported image schemes')
    mount(page);settle(page)
    check(calls[:2]==[PRIMARY,ALTERNATE],'404 automatically falls back to alternate CDN with same hash path')
    check(current(page)==ALTERNATE,'working fallback is the actual displayed image')
    check(page.locator('#coverFixture .cover-image').evaluate('(e)=>e.naturalWidth===460&&e.complete'),'successful image fully decoded before placement')
    check(page.locator('#coverFixture .cover-fallback').evaluate('(e)=>getComputedStyle(e).visibility')=='hidden','placeholder text removed behind successful image')
    check(page.locator('#coverFixture .cover-image').evaluate('(e)=>getComputedStyle(e).objectFit')=='contain','image never stretches or crops its logo')
    size=page.locator('#coverFixture .cover').bounding_box()
    check(abs(size['width']/size['height']-920/430)<0.01,'card image container keeps header aspect ratio')
    before=len(calls);mount(page);settle(page)
    check(all(u==ALTERNATE for u in calls[before:]) and current(page)==ALTERNATE,'rerender reuses working source without retrying known failing first URL')
    mount(page,extra='detail-visual');settle(page)
    size=page.locator('#coverFixture .cover').bounding_box()
    check(abs(size['width']/size['height']-920/430)<0.01,'detail cover no longer forced into short cropped banner')
    page.close()

    # Several official images on a stalled CDN must not starve the backup host.
    pending=[]
    def stalled_host(route):
        if 'shared.fastly.steamstatic.com' in route.request.url:pending.append(route)
        else:route.fulfill(status=200,content_type='image/png',body=IMAGE)
    page=page_for(stalled_host);page.clock.install()
    page.evaluate('''(u)=>{SteamLensTest.DEMO[0].capsuleImage=u.replace('header_schinese','capsule_231x87');SteamLensTest.DEMO[0].capsuleImageV5=u.replace('header_schinese','capsule_184x69');}''',PRIMARY)
    mount(page)
    for _ in range(20):
        if pending:break
        page.wait_for_timeout(30)
    page.clock.run_for(4700);settle(page)
    check(current(page)==ALTERNATE,'backup CDN reached after one stalled host timeout despite multiple official images')
    for route in pending:
        try:route.abort()
        except Exception:pass
    page.close()

    # Failure cooldown avoids repeated waterfalls on sorting; retry is explicit.
    calls=[];mode={'fail':True}
    def offline(route):
        calls.append(route.request.url)
        if mode['fail']:route.abort()
        else:route.fulfill(status=200,content_type='image/png',body=IMAGE)
    page=page_for(offline);mount(page);settle(page,'failed')
    check(0<len(calls)<=12,'all-source failure is bounded, with no infinite retry')
    check(page.locator('#coverFixture .cover-retry').is_visible(),'failure shows actionable per-game retry button')
    check(current(page) is None,'all-failed state does not expose a broken src')
    before=len(calls);mount(page);settle(page,'failed')
    check(len(calls)==before,'short failure cache suppresses repeated automatic retry storm')
    mode['fail']=False
    page.locator('#coverFixture .cover-retry').click();settle(page)
    check(len(calls)>before and current(page)==PRIMARY,'manual retry bypasses failure cooldown and recovers')
    check(not page.locator('#dialog').evaluate('(e)=>e.open'),'retry click does not also open game detail dialog')
    check(page.evaluate('SteamLensTest.DEMO.length===36&&SteamLensTest.state.favorites.size===0'),'retry preserves existing catalog and favorites')
    page.close()

    # Small HTTP-200 error pixels must not be accepted as a game cover.
    calls=[]
    def tiny(route):
        calls.append(route.request.url)
        route.fulfill(status=200,content_type='image/png',body=TINY if route.request.url==PRIMARY else IMAGE)
    page=page_for(tiny);mount(page);settle(page)
    check(len(calls)==2 and current(page)==ALTERNATE,'tiny error pixel rejected; next source loads')
    page.close()

    # Deterministic time travel over the actual production 4.5 second timeout.
    pending=[];calls=[]
    def hang(route):
        calls.append(route.request.url)
        if route.request.url==PRIMARY:pending.append(route)
        else:route.fulfill(status=200,content_type='image/png',body=IMAGE)
    page=page_for(hang);page.clock.install();mount(page)
    for _ in range(20):
        if pending:break
        page.wait_for_timeout(30)
    check(bool(pending),'hanging primary source test started')
    page.clock.run_for(4700);settle(page)
    check(current(page)==ALTERNATE,'timeout advances to backup without waiting indefinitely')
    for route in pending:
        try:route.fulfill(status=200,content_type='image/png',body=IMAGE)
        except Exception:pass
    page.wait_for_timeout(50)
    check(current(page)==ALTERNATE,'late timed-out request cannot overwrite chosen image')
    page.close()

    # Detached cards must not keep their waterfall alive or overwrite another game.
    pending=[];calls=[]
    page=page_for(hang);mount(page)
    for _ in range(20):
        if pending:break
        page.wait_for_timeout(30)
    other='https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/105600/otherhash/header.jpg'
    mount(page,105600,other);settle(page)
    for route in pending:
        try:route.fulfill(status=200,content_type='image/png',body=IMAGE)
        except Exception:pass
    page.wait_for_timeout(100)
    check(current(page)==other,'rapid game change cannot receive prior game image')
    check(not any('/413150/' in u and u!=PRIMARY for u in calls),'detached card does not continue trying alternative URLs')
    page.close()

    # Entire timeout budget prevents even a list of silent sources from looping.
    pending=[]
    def silent(route):pending.append(route)
    page=page_for(silent);page.clock.install();mount(page)
    for _ in range(20):
        if pending:break
        page.wait_for_timeout(30)
    page.clock.run_for(19000);settle(page,'failed')
    check(page.locator('#coverFixture .cover-retry').is_visible(),'total timeout budget ends with retryable placeholder')
    for route in pending:
        try:route.abort()
        except Exception:pass
    page.wait_for_timeout(40)
    page.close()

    page=page_for(lambda r:r.fulfill(status=200,content_type='image/png',body=IMAGE),{'width':390,'height':844})
    mount(page);settle(page)
    check(page.evaluate('document.documentElement.scrollWidth<=innerWidth'),'mobile image layout does not cause horizontal overflow')
    check(page.locator('.game-grid').evaluate('(e)=>getComputedStyle(e).gridTemplateColumns.split(" " ).length===1'),'small phone uses one readable card column')
    check(page.locator('#coverFixture .cover-image').evaluate('(e)=>getComputedStyle(e).objectFit')=='contain','mobile cover also keeps whole artwork')
    page.close()
    check(not errors,'no uncaught JavaScript errors across cover scenarios')
    browser.close()

(ROOT/'cover-test-results.json').write_text(json.dumps({'checks':len(checks),'passed':checks,'liveSteamImagesVerified':False,'imageFixtures':'synthetic solid-color PNG generated in test; not game artwork'},ensure_ascii=False,indent=2),encoding='utf-8')
print(f'\n{len(checks)} cover checks passed; live Steam images were NOT verified.')
