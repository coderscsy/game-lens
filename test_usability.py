"""Offline interaction regressions for the reading / discovery update."""
import json
import os
from pathlib import Path
import unittest
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
HTML = (ROOT / 'steam_lens.html').read_text(encoding='utf-8')
LOCAL = "const isLocal=()=>location.protocol==='http:'&&['127.0.0.1','localhost'].includes(location.hostname);"

class UsabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pw = sync_playwright().start()
        exe = os.environ.get('CHROMIUM_PATH')
        cls.browser = cls.pw.chromium.launch(headless=True, **({'executable_path': exe} if exe else {}))

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()

    def setUp(self):
        self.page = self.browser.new_page(viewport={'width': 1440, 'height': 900})
        self.page.set_default_timeout(3000)
        self.errors = []
        self.page.on('pageerror', lambda e: self.errors.append(str(e)))
        self.page.route('https://**/*', lambda r: r.abort())
        self.mount()

    def mount(self, local=False, saved=None):
        self.page.goto('about:blank')
        saved = saved or {'covers': False, 'favorites': [413150]}
        storage = '<script>window._saved=' + json.dumps({'steam-lens.v1': json.dumps(saved)}) + ';Object.defineProperty(window,"localStorage",{value:{getItem:k=>window._saved[k]??null,setItem:(k,v)=>window._saved[k]=v}});</script>'
        doc = HTML.replace('<head>', '<head>' + storage, 1)
        if local:
            doc = doc.replace(LOCAL, 'const isLocal=()=>true;')
        self.page.set_content(doc, wait_until='domcontentloaded')

    def tearDown(self):
        self.page.close()
        self.assertEqual(self.errors, [])

    def test_shortcuts_preserve_unrelated_filters_and_toggle(self):
        p = self.page
        p.locator('#maxPrice').fill('88')
        p.locator('#search').fill('星露谷')
        p.locator('#language').select_option('schinese')
        p.locator('[data-preset="quality"]').click()
        self.assertEqual(p.locator('#maxPrice').input_value(), '88')
        self.assertEqual(p.locator('#search').input_value(), '星露谷')
        self.assertEqual(p.locator('#language').input_value(), 'schinese')
        p.locator('[data-preset="quality"]').click()
        self.assertEqual(p.locator('#minRating').input_value(), '0')
        self.assertEqual(p.locator('#maxPrice').input_value(), '88')
        p.locator('#platform').select_option('mac')
        self.assertEqual(p.locator('[data-preset="mac"]').get_attribute('aria-pressed'), 'true')
        p.locator('[data-clear-filter="platform"]').click()
        self.assertEqual(p.locator('#platform').input_value(), 'any')

    def test_detail_only_displays_supported_platforms(self):
        p = self.page
        p.evaluate("SteamLensTest.DEMO[0].platforms={windows:true,mac:false,linux:null};SteamLensTest.render()")
        p.locator('#search').fill('413150')
        p.locator('[data-action="detail"][data-id="413150"]').first.click()
        text = p.locator('#dialogBody').inner_text()
        self.assertNotIn('macOS', text)
        self.assertNotIn('Linux', text)
        self.assertIn('Windows', text)
        p.get_by_role('tab', name='语言与配置').click()
        self.assertEqual(p.locator('[data-platform-requirement]').count(), 1)
        self.assertIn('最低配置', p.locator('[role="tabpanel"]:visible').inner_text())

    def test_detail_fits_viewport_and_tabs_remain_accessible(self):
        p = self.page
        p.set_viewport_size({'width':1440,'height':1100})
        p.locator('.game-title').first.click()
        self.assertTrue(p.get_by_role('tab', name='概览', exact=True).is_visible())
        p.get_by_role('tab', name='评分依据').click()
        self.assertIn('Wilson', p.locator('[role="tabpanel"]:visible').inner_text())
        p.get_by_role('button', name='展开详情').click()
        box = p.locator('#dialog').bounding_box()
        self.assertGreater(box['width'], 1300)
        self.assertGreater(box['height'], 1050)
        self.assertLessEqual(box['y'] + box['height'], 1100)
        p.keyboard.press('Escape')
        self.assertFalse(p.locator('#dialog').evaluate('(el)=>el.open'))

    def test_themes_persist_without_losing_old_favorites(self):
        p = self.page
        colors = set()
        for theme in ('day', 'dusk', 'night'):
            p.locator('#themeSelect').select_option(theme)
            colors.add(p.evaluate('getComputedStyle(document.body).backgroundColor'))
            saved = p.evaluate("JSON.parse(localStorage.getItem('steam-lens.v1'))")
            self.assertEqual(saved['theme'], theme)
            self.assertEqual(saved['favorites'], [413150])
        self.assertEqual(len(colors), 3)
        self.mount(saved=saved)
        self.assertEqual(p.locator('#themeSelect').input_value(), 'night')

    def test_unified_network_input_and_retry_keeps_successes(self):
        self.mount(local=True)
        p = self.page
        p.evaluate('''() => {
          window._phase=0;
          window.fetch=async url=>{
            if(url.startsWith('/api/health')) return new Response('{"service":"steam-lens"}');
            if(url.startsWith('/api/discover')) return new Response('{"appids":[413150,105600],"hasMore":false,"nextStart":20}');
            const id=Number(new URL(url,'http://localhost').searchParams.get('appid'));
            if(id===105600 && !window._phase) return new Response('{"error":"mock unavailable"}',{status:502});
            const game=structuredClone(SteamLensTest.DEMO.find(g=>g.appid===id));game.source='steam';
            return new Response(JSON.stringify({game}));
          };
        }''')
        p.locator('#connectBtn').click()
        p.locator('#onlineTerm').fill('https://store.steampowered.com/app/413150/ 105600')
        p.locator('#onlineTerm').press('Enter')
        p.wait_for_function('!SteamLensTest.state.busy && SteamLensTest.state.mode==="live"')
        self.assertIn('成功 1', p.locator('#networkSummary').inner_text())
        self.assertIn('失败 1', p.locator('#networkSummary').inner_text())
        p.evaluate('window._phase=1')
        p.locator('[data-action="retryFailedTask"]').click()
        p.wait_for_function('!SteamLensTest.state.busy && SteamLensTest.dataset().length===2')
        self.assertEqual(p.evaluate('SteamLensTest.DEMO.length'), 36)

    def test_readable_layout_on_desktop_and_phone(self):
        p = self.page
        self.assertGreaterEqual(p.locator('.game-sub').first.evaluate('(e)=>parseFloat(getComputedStyle(e).fontSize)'), 13)
        self.assertLess(p.locator('.hero').bounding_box()['height'], 95)
        for width in (1440, 1280, 768, 390):
            p.set_viewport_size({'width': width, 'height': 900})
            self.assertTrue(p.evaluate('document.documentElement.scrollWidth<=innerWidth'), str(width))

    def test_numbered_game_name_is_searched_instead_of_parsed_as_ids(self):
        self.mount(local=True)
        p=self.page
        p.evaluate('''() => {window.fetch=async url=>url.startsWith('/api/health')?new Response('{"service":"steam-lens"}'):new Response('{"appids":[],"hasMore":false}');}''')
        p.locator('#connectBtn').click()
        p.locator('#onlineTerm').fill('7 Days to Die')
        p.locator('#onlineTerm').press('Enter')
        p.wait_for_function('SteamLensTest.state.taskResult!==null')
        self.assertIn('没有找到候选',p.locator('#networkSummary').inner_text())

    def test_discovery_can_be_stopped_before_any_game_arrives(self):
        self.mount(local=True)
        p=self.page
        p.evaluate('''() => {window.fetch=(url,options)=>url.startsWith('/api/health')?Promise.resolve(new Response('{"service":"steam-lens"}')):new Promise((resolve,reject)=>options.signal.addEventListener('abort',()=>reject(new DOMException('stopped','AbortError'))));}''')
        p.locator('#connectBtn').click()
        p.locator('[data-kind="topsellers"]').click()
        self.assertTrue(p.locator('[data-action="stopTask"]').is_visible())
        p.locator('[data-action="stopTask"]').click()
        p.wait_for_function('!SteamLensTest.state.busy')
        self.assertIn('已停止',p.locator('#networkSummary').inner_text())
        self.assertEqual(p.evaluate('SteamLensTest.state.mode'),'demo')

if __name__ == '__main__':
    unittest.main(verbosity=2)
