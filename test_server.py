"""Offline unit and local HTTP contract tests. These DO NOT verify Steam live availability."""
import copy
import json
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import server

STAMP='2026-09-29T08:00:00+00:00'
APP={
 'type':'game','name':'Fixture game <b>title</b>', 'is_free':False,
 'price_overview':{'currency':'CNY','initial':10000,'final':5000,'discount_percent':50},
 'supported_languages':'英语<strong>*</strong>, 简体中文, 繁体中文<strong>*</strong><br><strong>*</strong>具有完全音频支持的语言',
 'genres':[{'id':'1','description':'动作'},{'id':'23','description':'独立'}],
 'categories':[{'id':2},{'id':9},{'id':38},{'id':28},{'id':23}],
 'platforms':{'windows':True,'mac':False,'linux':True},
 'release_date':{'coming_soon':False,'date':'2024 年 2 月 29 日'},
 'pc_requirements':{'minimum':'<b>CPU:</b> Fixture only<br>RAM: unknown'},
}
REV={'total_reviews':1000,'total_positive':950,'total_negative':50,'review_score_desc':'Positive'}

class NormalizeTests(unittest.TestCase):
 def normalize(self,app=None,rev=REV):return server.normalize_app(42,'cn',copy.deepcopy(APP if app is None else app),copy.deepcopy(rev),STAMP,STAMP,[])
 def test_price_units(self):
  g=self.normalize();self.assertEqual(g['price'],50);self.assertEqual(g['originalPrice'],100)
 def test_missing_price_is_not_free(self):
  a=copy.deepcopy(APP);a.pop('price_overview');g=self.normalize(a);self.assertIsNone(g['price']);self.assertFalse(g['isFree'])
 def test_free_is_explicit(self):
  a=copy.deepcopy(APP);a.pop('price_overview');a['is_free']=True;g=self.normalize(a);self.assertEqual(g['price'],0);self.assertTrue(g['isFree'])
 def test_currency_mismatch(self):
  a=copy.deepcopy(APP);a['price_overview']['currency']='USD';g=self.normalize(a);self.assertIsNone(g['price']);self.assertEqual(g['currency'],'CNY');self.assertTrue(g['warnings'])
 def test_language_audio_are_separate(self):
  g=self.normalize();self.assertIn('schinese',g['languages']);self.assertNotIn('schinese',g['audioLanguages']);self.assertIn('tchinese',g['audioLanguages'])
 def test_missing_language(self):
  a=copy.deepcopy(APP);a.pop('supported_languages');g=self.normalize(a);self.assertIsNone(g['languages']);self.assertIsNone(g['audioLanguages'])
 def test_english_language_parse(self):
  langs,audio,_=server.parse_languages('English<strong>*</strong>, Simplified Chinese<br>* full audio');self.assertEqual(langs,['english','schinese']);self.assertEqual(audio,['english'])
 def test_review_failure_stays_unknown(self):self.assertIsNone(self.normalize(rev=None)['reviews'])
 def test_invalid_review_counts(self):
  r=dict(REV,total_negative=100);g=self.normalize(rev=r);self.assertIsNone(g['reviews']);self.assertTrue(g['warnings'])
 def test_zero_reviews_valid_not_fabricated(self):
  r=dict(REV,total_reviews=0,total_positive=0,total_negative=0);self.assertEqual(self.normalize(rev=r)['reviews']['total'],0)
 def test_leap_date(self):self.assertEqual(self.normalize()['releaseDate'],'2024-02-29')
 def test_invalid_date_preserved_as_text(self):
  a=copy.deepcopy(APP);a['release_date']['date']='2023 年 2 月 29 日';self.assertIsNone(self.normalize(a)['releaseDate'])
 def test_html_is_plain_text(self):
  g=self.normalize();self.assertEqual(g['name'],'Fixture game title');self.assertNotIn('<b>',g['requirements']['windows']['minimum'])
 def test_non_game_rejected(self):
  a=dict(APP,type='dlc');self.assertRaises(ValueError,self.normalize,a)
 def test_unknown_features(self):
  a=copy.deepcopy(APP);a.pop('categories');a.pop('genres');g=self.normalize(a);self.assertIsNone(g['coop']);self.assertIsNone(g['earlyAccess'])
 def test_game_features(self):
  g=self.normalize();self.assertTrue(g['coop']);self.assertTrue(g['onlineCoop']);self.assertEqual(g['controller'],'full')
 def test_id_validation(self):
  for bad in (True,0,-1,'42&url=evil','https://example.org','1.1'):
   with self.assertRaises(ValueError):server.valid_appid(bad)
 def test_region_validation(self):
  self.assertEqual(server.valid_region('HK'),'hk');self.assertRaises(ValueError,server.valid_region,'x')
 def test_upstream_whitelist(self):self.assertRaises(ValueError,server._remote,'https://example.org/');self.assertRaises(ValueError,server._remote,'http://store.steampowered.com/')
 def test_search_parser(self):
  p=server.SearchParser();p.feed('<a data-ds-appid="42" href="https://store.steampowered.com/app/42/">X</a><a data-ds-appid="42" href="https://store.steampowered.com/app/42/">DUP</a><a data-ds-appid="43" href="https://store.steampowered.com/sub/43/">PACKAGE</a><a href="https://store.steampowered.com/app/44/">Y</a>');self.assertEqual(p.ids,[42,44])

class CacheTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.old=server.CACHE_FILE;server.CACHE_FILE=Path(self.temp.name)/'cache.db';server.init_cache()
 def tearDown(self):server.CACHE_FILE=self.old;self.temp.cleanup()
 def test_cache_preserves_time_and_avoids_second_call(self):
  with patch.object(server,'_remote',return_value=b'{"x":1}') as remote:
   a=server.cached('https://store.steampowered.com/test',3600);b=server.cached('https://store.steampowered.com/test',3600)
  self.assertEqual(a,b);self.assertEqual(remote.call_count,1)
 def test_stale_fallback_is_labelled_and_keeps_old_timestamp(self):
  url='https://store.steampowered.com/test'
  with server.database() as c:c.execute('INSERT INTO responses VALUES (?,?,?,?)',(url,b'{}',STAMP,1))
  with patch.object(server,'_remote',side_effect=RuntimeError('offline')):body,stamp,warning=server.cached(url,3600)
  self.assertEqual(stamp,STAMP);self.assertIn('旧缓存',warning)
 def test_force_refresh(self):
  url='https://store.steampowered.com/test'
  with patch.object(server,'_remote',side_effect=[b'old',b'new']) as remote:
   server.cached(url,3600);new=server.cached(url,3600,True)
  self.assertEqual(new[0],b'new');self.assertEqual(remote.call_count,2)
 def test_partial_failure_keeps_details_but_no_fake_reviews(self):
  with patch.object(server,'get_json',side_effect=[({'42':{'success':True,'data':APP}},STAMP,None),RuntimeError('offline')]):g=server.fetch_app(42,'cn')
  self.assertEqual(g['price'],50);self.assertIsNone(g['reviews']);self.assertTrue(g['warnings'])

class HTTPTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.srv=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler);cls.port=cls.srv.server_port;cls.thread=threading.Thread(target=cls.srv.serve_forever,daemon=True);cls.thread.start()
 @classmethod
 def tearDownClass(cls):cls.srv.shutdown();cls.srv.server_close()
 def request(self,path,headers=None):return urlopen(Request(f'http://127.0.0.1:{self.port}'+path,headers=headers or {}),timeout=5)
 def test_health_is_not_claiming_upstream_verified(self):
  with self.request('/api/health',{'X-Steam-Lens':'1'}) as r:d=json.load(r)
  self.assertFalse(d['upstreamVerified']);self.assertEqual(d['service'],'steam-lens')
 def test_requires_custom_header(self):
  with self.assertRaises(HTTPError) as cm:self.request('/api/health')
  self.assertEqual(cm.exception.code,403)
 def test_rejects_cross_origin(self):
  with self.assertRaises(HTTPError) as cm:self.request('/api/health',{'X-Steam-Lens':'1','Origin':'https://example.org'})
  self.assertEqual(cm.exception.code,403)
 def test_rejects_host_rebinding(self):
  with self.assertRaises(HTTPError) as cm:self.request('/api/health',{'X-Steam-Lens':'1','Host':'evil.invalid'})
  self.assertEqual(cm.exception.code,403)
 def test_no_arbitrary_static_files(self):
  for path in ('/server.py','/.steam_lens_cache.sqlite3','/../../etc/passwd'):
   with self.assertRaises(HTTPError) as cm:self.request(path)
   self.assertEqual(cm.exception.code,404)
 def test_html_is_served(self):
  with self.request('/') as r:self.assertIn('<title>游鉴 · GameLens</title>'.encode(),r.read())
 def test_app_contract_with_mock_upstream(self):
  g=server.normalize_app(42,'cn',APP,REV,STAMP,STAMP,[])
  with patch.object(server,'fetch_app',return_value=g):
   with self.request('/api/app?appid=42&cc=cn',{'X-Steam-Lens':'1'}) as r:d=json.load(r)
  self.assertEqual(d['game']['appid'],42);self.assertEqual(d['game']['price'],50)

if __name__=='__main__':unittest.main(verbosity=2)
