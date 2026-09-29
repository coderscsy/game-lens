#!/usr/bin/env python3
"""GameLens local read-only adapter. Python 3.10+, standard library only.
Official review API: https://partner.steamgames.com/doc/store/getreviews
Store appdetails/search are undocumented storefront endpoints and may change.
No Steam account, API key, cookie, login or third-party open proxy is required.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import datetime as dt
import html
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import sqlite3
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse, parse_qs
from urllib.request import Request, build_opener, HTTPRedirectHandler
import webbrowser

ROOT = Path(__file__).resolve().parent
CACHE_FILE = ROOT / '.steam_lens_cache.sqlite3'
CURRENCIES = {'cn': 'CNY', 'hk': 'HKD', 'us': 'USD', 'jp': 'JPY'}
LOCK = threading.Lock()
LAST_REQUEST = 0.0
COOLDOWN_UNTIL = 0.0
MAX_BYTES = 5 * 1024 * 1024
LANG_NAMES = {
    'schinese': ('简体中文', 'Simplified Chinese'),
    'tchinese': ('繁体中文', 'Traditional Chinese'),
    'english': ('英语', 'English'), 'japanese': ('日语', 'Japanese'),
    'koreana': ('韩语', 'Korean'), 'french': ('法语', 'French'),
    'german': ('德语', 'German'), 'spanish': ('西班牙语 - 西班牙', 'Spanish - Spain'),
    'latam': ('西班牙语 - 拉丁美洲', 'Spanish - Latin America'),
    'russian': ('俄语', 'Russian'), 'portuguese': ('葡萄牙语 - 葡萄牙', 'Portuguese - Portugal'),
    'brazilian': ('葡萄牙语 - 巴西', 'Portuguese - Brazil'),
    'italian': ('意大利语', 'Italian'), 'polish': ('波兰语', 'Polish'),
    'turkish': ('土耳其语', 'Turkish'), 'thai': ('泰语', 'Thai'),
    'ukrainian': ('乌克兰语', 'Ukrainian'), 'arabic': ('阿拉伯语', 'Arabic'),
    'vietnamese': ('越南语', 'Vietnamese'), 'indonesian': ('印度尼西亚语', 'Indonesian'),
}
GENRES = {'1': '动作', '2': '策略', '3': '角色扮演', '4': '休闲', '9': '竞速',
          '18': '体育', '23': '独立', '25': '冒险', '28': '模拟',
          '29': '大型多人在线', '37': '免费开玩', '70': '抢先体验'}


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')


def plain(value: object) -> str:
    text = re.sub(r'<(?:br\s*/?|/p|/li|/div)>', '\n', str(value or ''), flags=re.I)
    return html.unescape(re.sub(r'<[^>]*>', '', text)).strip()


def parse_languages(value: str | None) -> tuple[list[str] | None, list[str] | None, str]:
    if not value:
        return None, None, ''
    raw = re.split(r'<br\s*/?>', value, maxsplit=1, flags=re.I)[0]
    supported, audio = [], []
    for token in plain(raw).split(','):
        token = token.strip()
        name = token.replace('*', '').strip()
        code = next((k for k, labels in LANG_NAMES.items() if name in labels), name)
        if code:
            supported.append(code)
            if '*' in token:
                audio.append(code)
    return list(dict.fromkeys(supported)), list(dict.fromkeys(audio)), plain(value)


def valid_region(value: str) -> str:
    region = value.lower()
    if region not in CURRENCIES:
        raise ValueError('地区仅支持 cn / hk / us / jp。')
    return region


def valid_appid(value: object) -> int:
    if isinstance(value, bool) or not re.fullmatch(r'[1-9]\d{0,9}', str(value)):
        raise ValueError('AppID 必须为正整数（最多 10 位）。')
    return int(value)



def safe_steam_image(value: object, appid: int) -> str | None:
    """Validate a Steam-owned image URL for this AppID; preserve hash paths."""
    if not isinstance(value, str) or len(value) > 2048:
        return None
    try:
        value = value.strip()
        if value.startswith('//'):
            value = 'https:' + value
        url = urlparse(value)
        host = url.hostname or ''
        allowed = host == 'steamstatic.com' or host.endswith('.steamstatic.com') or host == 'steamcdn-a.akamaihd.net'
        if not allowed or url.scheme not in ('https', 'http') or url.username or url.password or url.port not in (None, 443):
            return None
        match = re.fullmatch(r'/(?:store_item_assets/steam|steam)/apps/([1-9]\d{0,9})/(?:[A-Za-z0-9_-]+/)*[A-Za-z0-9_.-]+\.(?:jpe?g|png|webp|avif)', url.path, re.I)
        if not match or int(match.group(1)) != appid:
            return None
        return url._replace(scheme='https', fragment='').geturl()
    except (TypeError, ValueError):
        return None

class SafeRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urlparse(newurl)
        if parsed.scheme != 'https' or parsed.hostname != 'store.steampowered.com' or parsed.port not in (None, 443):
            raise ValueError('拒绝转发到 Steam 商店以外的地址。')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


OPENER = build_opener(SafeRedirect())


def _remote(url: str) -> bytes:
    """Serial global rate limit, one retry for 5xx, no bypass of HTTP 429."""
    global LAST_REQUEST, COOLDOWN_UNTIL
    if urlparse(url).scheme != 'https' or urlparse(url).hostname != 'store.steampowered.com' or urlparse(url).port not in (None, 443):
        raise ValueError('上游域名不在白名单内。')
    with LOCK:
        if time.monotonic() < COOLDOWN_UNTIL:
            raise RuntimeError('Steam 请求受限，冷却中；请稍后再试。')
        for attempt in range(2):
            pause = 1.6 - (time.monotonic() - LAST_REQUEST)
            if pause > 0:
                time.sleep(pause)
            LAST_REQUEST = time.monotonic()
            req = Request(url, headers={
                'User-Agent': 'SteamLensLocal/1.0 (personal catalog browser)',
                'Accept': 'application/json,text/html;q=0.9',
                'Accept-Encoding': 'identity',
            })
            try:
                with OPENER.open(req, timeout=18) as response:
                    body = response.read(MAX_BYTES + 1)
                    if len(body) > MAX_BYTES:
                        raise RuntimeError('Steam 响应超过安全大小限制。')
                    return body
            except HTTPError as exc:
                if exc.code == 429:
                    retry = exc.headers.get('Retry-After', '60')
                    try:
                        wait = max(30, int(retry))
                    except ValueError:
                        try:
                            when = parsedate_to_datetime(retry)
                            if when.tzinfo is None:
                                when = when.replace(tzinfo=dt.timezone.utc)
                            wait = max(30, int((when - dt.datetime.now(dt.timezone.utc)).total_seconds()))
                        except (ValueError, TypeError, OverflowError):
                            wait = 60
                    COOLDOWN_UNTIL = time.monotonic() + wait
                    raise RuntimeError(f'Steam 限流（HTTP 429），请至少 {wait} 秒后再试。') from exc
                if 500 <= exc.code < 600 and attempt == 0:
                    time.sleep(2)
                    continue
                raise RuntimeError(f'Steam 返回 HTTP {exc.code}，未绕过访问限制。') from exc
            except (URLError, TimeoutError, OSError) as exc:
                raise RuntimeError(f'无法连接 Steam，请检查本机网络或系统代理：{exc}') from exc
    raise RuntimeError('Steam 请求未完成。')


@contextmanager
def database():
    """Commit/rollback AND close; sqlite Connection.__exit__ alone does not close."""
    conn = sqlite3.connect(CACHE_FILE, timeout=10)
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def init_cache() -> None:
    with database() as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS responses (key TEXT PRIMARY KEY, body BLOB NOT NULL, fetched TEXT NOT NULL, expires REAL NOT NULL)')


def cached(url: str, ttl: int, force: bool = False) -> tuple[bytes, str, str | None]:
    with database() as conn:
        row = conn.execute('SELECT body, fetched, expires FROM responses WHERE key=?', (url,)).fetchone()
    if row and not force and row[2] > time.time():
        return bytes(row[0]), row[1], None
    try:
        body = _remote(url)
        stamp = utc_now()
        with database() as conn:
            conn.execute('INSERT OR REPLACE INTO responses VALUES (?, ?, ?, ?)',
                         (url, body, stamp, time.time() + ttl))
        return body, stamp, None
    except Exception as exc:
        if row:
            # Preserve the ORIGINAL fetch timestamp. Never relabel stale prices as fresh.
            return bytes(row[0]), row[1], f'上游更新失败，使用旧缓存：{exc}'
        raise


def get_json(url: str, ttl: int, force: bool = False):
    body, stamp, warning = cached(url, ttl, force)
    try:
        data = json.loads(body)
    except (ValueError, UnicodeError) as exc:
        raise RuntimeError('Steam 未返回有效 JSON；接口可能已改变或受网络限制。') from exc
    return data, stamp, warning


def normalize_app(appid: int, region: str, data: dict, summary: dict | None,
                  details_at: str, reviews_at: str | None, warnings: list[str]) -> dict:
    if data.get('type') != 'game':
        raise ValueError('当前条目不是游戏本体（可能是 DLC、试玩或软件），已跳过。')
    price = data.get('price_overview') or {}
    free = data.get('is_free') is True
    currency = price.get('currency') or CURRENCIES[region]
    available = free or (isinstance(price.get('final'), (int, float)) and price['final'] >= 0)
    if currency != CURRENCIES[region]:
        warnings.append(f'接口返回币种 {currency} 与请求地区不匹配，已隐藏价格。')
        available = False
        currency = CURRENCIES[region]
    languages, audio, language_text = parse_languages(data.get('supported_languages'))
    categories = data.get('categories')
    category_ids = {int(x['id']) for x in (categories or []) if str(x.get('id', '')).isdigit()}
    feature = lambda ids: bool(category_ids & set(ids)) if categories is not None else None
    reviews = None
    if summary is not None:
        n, p, neg = (summary.get(x) for x in ('total_reviews', 'total_positive', 'total_negative'))
        if all(isinstance(v, int) and not isinstance(v, bool) and v >= 0 for v in (n, p, neg)) and p + neg == n:
            reviews = {'total': n, 'positive': p, 'negative': neg,
                       'description': plain(summary.get('review_score_desc')),
                       'scope': 'all_languages_steam_purchase_offtopic_filtered'}
        else:
            warnings.append('评论汇总字段缺失或不一致，评分已保留为未知。')
    release = data.get('release_date') or {}
    release_text = plain(release.get('date'))
    match = re.search(r'(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})', release_text)
    release_iso = None
    if match:
        try:
            release_iso = dt.date(*map(int, match.groups())).isoformat()
        except ValueError:
            pass
    elif re.fullmatch(r'\d{4}-\d{2}-\d{2}', release_text):
        try:
            release_iso = dt.date.fromisoformat(release_text).isoformat()
        except ValueError:
            pass
    elif release_text:
        for fmt in ('%d %b, %Y', '%b %d, %Y', '%d %B, %Y'):
            try:
                release_iso = dt.datetime.strptime(release_text, fmt).date().isoformat()
                break
            except ValueError:
                pass
    def specs(key):
        requirements = data.get(key)
        if not isinstance(requirements, dict):
            return {'minimum': '', 'recommended': ''}
        return {k: plain(requirements.get(k))[:12000] for k in ('minimum', 'recommended')}
    meta = data.get('metacritic') or {}
    return {
        'appid': appid, 'name': plain(data.get('name')) or str(appid),
        'aliases': [], 'region': region, 'currency': currency,
        'headerImage': safe_steam_image(data.get('header_image'), appid),
        'capsuleImage': safe_steam_image(data.get('capsule_image'), appid),
        'capsuleImageV5': safe_steam_image(data.get('capsule_imagev5'), appid),
        'price': (0 if free else price['final'] / 100) if available else None,
        'originalPrice': (0 if free else price.get('initial', price['final']) / 100) if available else None,
        'discount': price.get('discount_percent', 0) if available else None,
        'isFree': free, 'genres': [GENRES.get(str(x.get('id')), plain(x.get('description'))) for x in data.get('genres', [])],
        'tags': [], 'languages': languages, 'audioLanguages': audio, 'languageText': language_text,
        'reviews': reviews, 'metacritic': meta.get('score'),
        'platforms': data.get('platforms') or {},
        'singleplayer': feature([2]), 'multiplayer': feature([1, 9, 24, 27, 36, 37, 38, 39, 47]),
        'coop': feature([9, 38, 39, 47]), 'onlineCoop': feature([38]), 'localCoop': feature([39]),
        'controller': 'full' if data.get('controller_support') == 'full' or 28 in category_ids else ('partial' if 18 in category_ids else None),
        'cloud': feature([23]), 'achievements': (data.get('achievements') or {}).get('total'),
        'releaseDate': release_iso, 'releaseText': release_text,
        'comingSoon': release.get('coming_soon') is True,
        'earlyAccess': any(str(x.get('id')) == '70' for x in data.get('genres', [])) if 'genres' in data else None,
        'developers': data.get('developers') or [], 'publishers': data.get('publishers') or [],
        'description': plain(data.get('short_description'))[:2500],
        'requiredAge': data.get('required_age'), 'dlcCount': len(data['dlc']) if isinstance(data.get('dlc'), list) else None,
        'requirements': {'windows': specs('pc_requirements'), 'mac': specs('mac_requirements'), 'linux': specs('linux_requirements')},
        'source': 'steam', 'detailsAt': details_at, 'reviewsAt': reviews_at,
        'warnings': warnings,
    }


def fetch_app(appid: int, region: str, force: bool = False) -> dict:
    details_url = 'https://store.steampowered.com/api/appdetails?' + urlencode({'appids': appid, 'cc': region, 'l': 'schinese'})
    payload, details_at, warn = get_json(details_url, 3600, force)
    item = payload.get(str(appid)) if isinstance(payload, dict) else None
    if not isinstance(item, dict) or item.get('success') is not True or not isinstance(item.get('data'), dict):
        raise ValueError('此 AppID 无可用详情；可能不存在、地区不可用或接口暂不可用。')
    if item['data'].get('type') != 'game':
        raise ValueError('不是游戏本体，已跳过 DLC / 试玩 / 软件。')
    warnings = [warn] if warn else []
    # Review endpoint is documented. day_range is NOT a recent-rating window.
    review_url = f'https://store.steampowered.com/appreviews/{appid}?' + urlencode({
        'json': 1, 'language': 'all', 'purchase_type': 'steam', 'filter': 'all',
        'day_range': 365, 'cursor': '*', 'num_per_page': 1, 'review_type': 'all', 'filter_offtopic_activity': 1,
    })
    summary, reviews_at = None, None
    try:
        result, stamp, review_warning = get_json(review_url, 21600, force)
        if result.get('success') != 1 or not isinstance(result.get('query_summary'), dict):
            raise RuntimeError('缺少 query_summary。')
        summary, reviews_at = result['query_summary'], stamp
        if review_warning:
            warnings.append(review_warning)
    except Exception as exc:
        warnings.append(f'评论数据未获取，未生成虚假评分：{exc}')
    return normalize_app(appid, region, item['data'], summary, details_at, reviews_at, warnings)


class SearchParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids: list[int] = []

    def handle_starttag(self, tag, attrs):
        if tag != 'a':
            return
        attrs = dict(attrs)
        raw = attrs.get('data-ds-appid', '')
        href = attrs.get('href', '')
        match = re.search(r'https://store\.steampowered\.com/app/(\d+)(?:/|\?|$)', href)
        candidate = raw if re.fullmatch(r'[1-9]\d{0,9}', raw) else (match.group(1) if match else '')
        if candidate and '/sub/' not in href and '/bundle/' not in href:
            appid = int(candidate)
            if appid not in self.ids:
                self.ids.append(appid)


def discover(region: str, term: str = '', kind: str = 'topsellers', start: int = 0) -> dict:
    if kind not in ('topsellers', 'specials', 'new', 'search'):
        raise ValueError('未知的发现分类。')
    if len(term) > 100 or not 0 <= start <= 10000:
        raise ValueError('搜索词过长或翻页范围无效。')
    params = {'cc': region, 'l': 'schinese', 'infinite': 1, 'start': start, 'count': 20, 'category1': 998}
    if term:
        params['term'] = term
    if kind == 'topsellers':
        params['filter'] = 'topsellers'
    elif kind == 'specials':
        params['specials'] = 1
    elif kind == 'new':
        params['sort_by'] = 'Released_DESC'
    body, stamp, warning = cached('https://store.steampowered.com/search/results/?' + urlencode(params), 900)
    try:
        result = json.loads(body)
    except (ValueError, UnicodeError) as exc:
        raise RuntimeError('Steam 搜索未返回 JSON。可尝试直接输入 AppID；不要将登录页当作搜索结果。') from exc
    fragment = result.get('results_html')
    if not isinstance(fragment, str):
        raise RuntimeError('Steam 搜索结构已改变，缺少 results_html；请使用 AppID 获取。')
    parser = SearchParser()
    parser.feed(fragment)
    total = result.get('total_count')
    total = int(total) if str(total).isdigit() else None
    if not parser.ids and fragment.strip() and re.search(r'captcha|access denied|sign in', fragment, re.I):
        raise RuntimeError('Steam 返回验证/访问限制页面；未尝试绕过。')
    return {'appids': parser.ids[:20], 'start': start, 'nextStart': start + 20,
            'total': total, 'hasMore': (start + 20 < total) if total is not None else len(parser.ids) >= 20,
            'fetchedAt': stamp, 'warning': warning,
            'note': '商店搜索候选集，不代表已完整同步 Steam 全库。'}


class Handler(BaseHTTPRequestHandler):
    server_version = 'SteamLensLocal/1.0'

    def json_response(self, status: int, obj: dict):
        body = json.dumps(obj, ensure_ascii=False, allow_nan=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(body)

    def allowed(self) -> bool:
        port = self.server.server_port
        hosts = {f'127.0.0.1:{port}', f'localhost:{port}'}
        if self.headers.get('Host', '') not in hosts:
            return False
        origin = self.headers.get('Origin')
        if origin and origin not in {f'http://{h}' for h in hosts}:
            return False
        if self.headers.get('Sec-Fetch-Site') == 'cross-site':
            return False
        return True

    def do_GET(self):
        try:
            if not self.allowed():
                self.json_response(403, {'error': '仅允许本机同源访问。'})
                return
            parsed = urlparse(self.path)
            if parsed.path in ('/', '/index.html', '/steam_lens.html'):
                body = (ROOT / 'steam_lens.html').read_bytes()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(body)))
                self.send_header('X-Content-Type-Options', 'nosniff')
                self.send_header('X-Frame-Options', 'DENY')
                self.send_header('Referrer-Policy', 'no-referrer')
                self.end_headers()
                self.wfile.write(body)
                return
            if parsed.path.startswith('/api/') and self.headers.get('X-Steam-Lens') != '1':
                self.json_response(403, {'error': '缺少本机页面请求标识。请从本机首页操作。'})
                return
            if parsed.path == '/api/health':
                self.json_response(200, {'ok': True, 'service': 'steam-lens', 'version': 1,
                                         'upstreamVerified': False, 'note': '本机服务已启动；不代表 Steam 已连通。'})
                return
            args = parse_qs(parsed.query)
            one = lambda key, default='': args.get(key, [default])[0]
            if parsed.path == '/api/app':
                region = valid_region(one('cc', 'cn'))
                result = fetch_app(valid_appid(one('appid')), region, one('refresh') == '1')
                self.json_response(200, {'game': result})
            elif parsed.path == '/api/discover':
                result = discover(valid_region(one('cc', 'cn')), one('term'), one('kind', 'topsellers'), int(one('start', '0')))
                self.json_response(200, result)
            else:
                self.json_response(404, {'error': '地址不存在。'})
        except ValueError as exc:
            self.json_response(400, {'error': str(exc)})
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception as exc:
            try:
                self.json_response(502, {'error': str(exc)})
            except (BrokenPipeError, ConnectionResetError):
                pass

    def log_message(self, format, *args):
        print('[GameLens] ' + format % args)


def main():
    parser = argparse.ArgumentParser(description='游鉴 · GameLens 本机数据服务（无需第三方 Python 包）')
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--no-browser', action='store_true')
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error('端口必须在 1024–65535 之间。')
    if not (ROOT / 'steam_lens.html').exists():
        parser.error('请把 server.py 与 steam_lens.html 放在同一目录。')
    init_cache()
    try:
        server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    except OSError as exc:
        parser.exit(1, f'本机端口无法使用：{exc}\n可使用 --port 8766 更换端口。\n')
    server.daemon_threads = True
    address = f'http://127.0.0.1:{args.port}'
    print(f'\n游鉴 · GameLens 已启动：{address}\n仅本机访问。按 Ctrl+C 停止。价格以 Steam 结算页面为准。\n')
    if not args.no_browser:
        threading.Timer(0.5, lambda: webbrowser.open(address)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
