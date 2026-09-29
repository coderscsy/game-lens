'use strict';
/* 游鉴 · GameLens — dependency-free UI. Demo data is intentionally synthetic. */
const ICON_PATHS={
 radar:'<circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="4.5"/><path d="M12 3v9l6.3 6.3"/><circle cx="12" cy="12" r="1"/>',
 search:'<circle cx="10.5" cy="10.5" r="6.8"/><path d="m16 16 4.5 4.5"/>',
 sliders:'<path d="M4 6h5m4 0h7M4 12h9m4 0h3M4 18h3m4 0h9"/><circle cx="11" cy="6" r="2"/><circle cx="15" cy="12" r="2"/><circle cx="9" cy="18" r="2"/>',
 grid:'<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
 list:'<path d="M9 5h12M9 12h12M9 19h12"/><path d="M3 5h1M3 12h1M3 19h1"/>',
 wallet:'<path d="M20 8V5H5a2 2 0 0 0-2 2v12h17V8H5a2 2 0 0 1 0-4"/><path d="M20 11h-6v5h6"/>',
 thumb:'<path d="M8 21H4V10h4m0 11h9a2 2 0 0 0 2-1.6l2-8A2 2 0 0 0 19 9h-5l1-5-2-2-5 8z"/>',
 tag:'<path d="m3 3 8 .2L21 13l-8 8L3.2 11z"/><circle cx="7.5" cy="7.5" r="1"/>',
 star:'<path d="m12 3 2.8 5.7 6.2.9-4.5 4.4 1.1 6.2L12 17.3l-5.6 2.9 1.1-6.2L3 9.6l6.2-.9z"/>',
 link:'<path d="m10 7 3-3a5 5 0 0 1 7 7l-3 3M14 17l-3 3a5 5 0 0 1-7-7l3-3M8 16l8-8"/>',
 spark:'<path d="m12 3 2.6 6.4L21 12l-6.4 2.6L12 21l-2.6-6.4L3 12l6.4-2.6z"/>',
 refresh:'<path d="M20 11a8 8 0 0 0-13.7-5.6L3 9m0-6v6h6M4 13a8 8 0 0 0 13.7 5.6L21 15m0 6v-6h-6"/>',
 download:'<path d="M12 3v12m-5-5 5 5 5-5M4 16v5h16v-5"/>',
 upload:'<path d="M12 16V4m-5 5 5-5 5 5M4 16v5h16v-5"/>',
 close:'<path d="m6 6 12 12M18 6 6 18"/>',
 arrow:'<path d="M4 12h16m-6-6 6 6-6 6"/>',
 info:'<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7v.1"/>',
 game:'<path d="M7 7h10c3 0 4 4 4 9s-3 5-5 1H8c-2 4-5 4-5-1s1-9 4-9Z"/><path d="M7 10v5m-2.5-2.5h5M16 11h.1M18 14h.1"/>',
 check:'<path d="m5 12 4 4L19 6"/>',
};
const icon=n=>`<svg class="icon" viewBox="0 0 24 24" aria-hidden="true">${ICON_PATHS[n]||ICON_PATHS.info}</svg>`;
const $=id=>document.getElementById(id);
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function hydrate(root=document){root.querySelectorAll('[data-icon]').forEach(el=>{el.innerHTML=icon(el.dataset.icon);el.removeAttribute('data-icon');});}
const REGIONS={cn:{name:'国区',currency:'CNY',symbol:'¥',anchor:200,budget:100},hk:{name:'港区',currency:'HKD',symbol:'HK$',anchor:240,budget:120},us:{name:'美区',currency:'USD',symbol:'$',anchor:40,budget:20},jp:{name:'日区',currency:'JPY',symbol:'JP¥',anchor:5000,budget:2500}};
const LANGUAGE_NAMES={schinese:'简体中文',tchinese:'繁体中文',english:'英语',japanese:'日语',koreana:'韩语',french:'法语',german:'德语',spanish:'西班牙语',latam:'拉美西班牙语',russian:'俄语',portuguese:'葡萄牙语',brazilian:'巴西葡萄牙语',italian:'意大利语',polish:'波兰语',turkish:'土耳其语',thai:'泰语',ukrainian:'乌克兰语',arabic:'阿拉伯语',vietnamese:'越南语',indonesian:'印度尼西亚语'};
const DEFAULT_WEIGHTS={quality:65,price:20,discount:10,language:5};
const STORAGE_KEY='steam-lens.v1';
const PAGE_SIZE=12;
const DEMO=JSON.parse($('demoData').textContent);
let storageFailed=false,toastTimer=null;
function readSaved(){try{return JSON.parse(localStorage.getItem(STORAGE_KEY)||'{}')||{};}catch{return {};}}
const saved=readSaved();
const filters={q:'',minPrice:'',maxPrice:'',priceMode:'any',minRating:0,minReviews:'',maxReviews:'',genres:[],language:'any',chineseAudio:false,platform:'any',singleplayer:false,coop:false,multiplayer:false,controller:false,cloud:false,releaseAfter:'any',hideEarlyAccess:false,showUpcoming:false};
const DEFAULT_FILTERS=JSON.parse(JSON.stringify(filters));
function finiteNumber(value,min=0,max=1e12){return typeof value==='number'&&Number.isFinite(value)&&value>=min&&value<=max?value:null;}
function dateOnly(v){if(typeof v!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(v))return null;const d=new Date(v+'T00:00:00Z');return Number.isFinite(d.getTime())&&d.toISOString().slice(0,10)===v?v:null;}
function validStamp(v){return typeof v==='string'&&Number.isFinite(Date.parse(v))?v:null;}
function strList(v,limit=80){return Array.isArray(v)?[...new Set(v.filter(x=>typeof x==='string').map(x=>x.slice(0,300)))].slice(0,limit):[];}

// Only Steam-owned HTTPS image locations for this exact AppID are accepted.
// Keep the full API path: it may include a content-hash subdirectory.
function safeSteamImage(value,appid){
 if(typeof value!=='string'||value.length>2048)return null;
 try{
  const u=new URL(value.trim().replace(/^\/\//,'https://'));
  const steamHost=u.hostname==='steamstatic.com'||u.hostname.endsWith('.steamstatic.com')||u.hostname==='steamcdn-a.akamaihd.net';
  if(!steamHost||!['http:','https:'].includes(u.protocol)||u.username||u.password||(u.port&&u.port!=='443'))return null;
  const path=u.pathname.match(/^\/(?:store_item_assets\/steam|steam)\/apps\/([1-9]\d{0,9})\/(?:[a-zA-Z0-9_-]+\/)*[a-zA-Z0-9_.-]+\.(?:jpe?g|png|webp|avif)$/i);
  if(!path||Number(path[1])!==Number(appid))return null;
  u.protocol='https:';u.hash='';return u.href;
 }catch{return null;}
}
function coverCandidates(g){
 const urls=[],add=v=>{const u=safeSteamImage(v,g.appid);if(u&&!urls.includes(u))urls.push(u);};
 const official=[g.headerImage,g.header_image,g.capsuleImage,g.capsule_image,g.capsuleImageV5,g.capsule_imagev5,...(Array.isArray(g.coverUrls)?g.coverUrls.slice(0,6):[])];
 // Try the alternate host immediately: several stalled images on one CDN
 // must not consume the entire request budget before a healthy host is tried.
 for(const v of official){const valid=safeSteamImage(v,g.appid);if(!valid)continue;add(valid);const u=new URL(valid);u.hostname=u.hostname==='shared.akamai.steamstatic.com'?'shared.fastly.steamstatic.com':'shared.akamai.steamstatic.com';add(u.href);}
 for(const base of ['https://shared.fastly.steamstatic.com/store_item_assets/steam/apps','https://shared.akamai.steamstatic.com/store_item_assets/steam/apps','https://cdn.akamai.steamstatic.com/steam/apps','https://cdn.cloudflare.steamstatic.com/steam/apps'])add(`${base}/${g.appid}/header.jpg`);
 for(const base of ['https://shared.fastly.steamstatic.com/store_item_assets/steam/apps','https://cdn.akamai.steamstatic.com/steam/apps'])add(`${base}/${g.appid}/capsule_616x353.jpg`);
 return urls.slice(0,12);
}

function normalizeGame(g,forcedSource=null){
 if(!g||typeof g!=='object'||!Number.isInteger(g.appid)||g.appid<=0||g.appid>9999999999)throw Error('每条记录都必须包含合法的数值 AppID。');
 if(typeof g.name!=='string'||!g.name.trim())throw Error(`AppID ${g.appid} 缺少名称。`);
 if(!REGIONS[g.region])throw Error(`AppID ${g.appid} 缺少合法地区 cn / hk / us / jp。`);
 if(g.currency!==REGIONS[g.region].currency)throw Error(`AppID ${g.appid} 的币种与地区不符，拒绝混算。`);
 const num=v=>finiteNumber(v),tri=v=>typeof v==='boolean'?v:null;
 let reviews=null;
 if(g.reviews!=null){const r=g.reviews,n=num(r.total),p=num(r.positive),neg=num(r.negative);
  if(![n,p,neg].every(Number.isInteger)||n!==p+neg)throw Error(`AppID ${g.appid} 评论数不一致：正面 + 负面必须等于总数。`);
  reviews={total:n,positive:p,negative:neg,description:String(r.description||'').slice(0,100),scope:String(r.scope||'imported_unknown_scope').slice(0,150)};
 }
 let source=forcedSource||(['demo','steam','imported'].includes(g.source)?g.source:'imported');
 const price=num(g.price),original=num(g.originalPrice),discount=finiteNumber(g.discount,0,100);
 if(g.isFree===true&&price!==0)throw Error(`AppID ${g.appid} 标记免费但价格不为零。`);
 const platforms={};for(const k of ['windows','mac','linux'])platforms[k]=tri(g.platforms?.[k]);
 const requirements={};for(const k of ['windows','mac','linux'])requirements[k]={minimum:String(g.requirements?.[k]?.minimum||'').slice(0,12000),recommended:String(g.requirements?.[k]?.recommended||'').slice(0,12000)};
 return {appid:g.appid,name:g.name.trim().slice(0,300),aliases:strList(g.aliases,10),headerImage:safeSteamImage(g.headerImage||g.header_image,g.appid),capsuleImage:safeSteamImage(g.capsuleImage||g.capsule_image,g.appid),capsuleImageV5:safeSteamImage(g.capsuleImageV5||g.capsule_imagev5,g.appid),coverUrls:(Array.isArray(g.coverUrls)?g.coverUrls:[]).map(u=>safeSteamImage(u,g.appid)).filter(Boolean).slice(0,6),region:g.region,currency:g.currency,price,originalPrice:original,discount:price===null?null:discount,isFree:g.isFree===true,
 genres:strList(g.genres,30),tags:strList(g.tags,30),languages:Array.isArray(g.languages)?strList(g.languages):null,audioLanguages:Array.isArray(g.audioLanguages)?strList(g.audioLanguages):null,languageText:String(g.languageText||'').slice(0,2500),
 reviews,metacritic:finiteNumber(g.metacritic,0,100),platforms,singleplayer:tri(g.singleplayer),coop:tri(g.coop),multiplayer:tri(g.multiplayer),onlineCoop:tri(g.onlineCoop),localCoop:tri(g.localCoop),
 controller:['full','partial'].includes(g.controller)?g.controller:null,cloud:tri(g.cloud),achievements:num(g.achievements),releaseDate:dateOnly(g.releaseDate),releaseText:String(g.releaseText||'').slice(0,120),comingSoon:g.comingSoon===true,earlyAccess:tri(g.earlyAccess),
 developers:strList(g.developers,20),publishers:strList(g.publishers,20),description:String(g.description||'').slice(0,3000),requiredAge:g.requiredAge??null,dlcCount:num(g.dlcCount),requirements,
 source,originalSource:String(g.originalSource||g.source||'').slice(0,30),detailsAt:validStamp(g.detailsAt),reviewsAt:validStamp(g.reviewsAt),warnings:strList(g.warnings,20)};
}
function restoreCatalog(value){const out={};if(!value||typeof value!=='object')return out;for(const cc of Object.keys(REGIONS)){if(!Array.isArray(value[cc]))continue;const map=new Map();for(const g of value[cc].slice(0,5000)){try{const n=normalizeGame(g);if(n.region===cc)map.set(n.appid,n);}catch{}}out[cc]=[...map.values()];}return out;}
const safeWeights={...DEFAULT_WEIGHTS};for(const k of Object.keys(safeWeights)){if(finiteNumber(saved.weights?.[k],0,100)!==null)safeWeights[k]=saved.weights[k];}
const state={region:REGIONS[saved.region]?saved.region:'cn',mode:['demo','live','import'].includes(saved.mode)?saved.mode:'demo',nav:'discover',view:saved.view==='table'?'table':'grid',sort:['recommend','wilson','rating','reviews','priceAsc','priceDesc','discount','release','metacritic'].includes(saved.sort)?saved.sort:'recommend',
 weights:safeWeights,favorites:new Set(Array.isArray(saved.favorites)?saved.favorites.filter(x=>Number.isInteger(x)&&x>0):[]),live:restoreCatalog(saved.live),imported:restoreCatalog(saved.imported),page:1,preset:'all',compare:new Set(),covers:saved.covers!==false,
 theme:['day','dusk','night'].includes(saved.theme)?saved.theme:'day',busy:false,abort:null,cancelled:false,logs:[],cursor:null,taskResult:null,retryIds:[],taskOptions:null};
if(state.mode==='demo'&&state.region!=='cn')state.mode='live';
let currentResults=[];
function persist(){try{localStorage.setItem(STORAGE_KEY,JSON.stringify({region:state.region,mode:state.mode,view:state.view,sort:state.sort,weights:state.weights,favorites:[...state.favorites],live:state.live,imported:state.imported,covers:state.covers,theme:state.theme}));}catch{if(!storageFailed){storageFailed=true;toast('浏览器存储空间不足或已禁用。当前会话仍可用，请导出 JSON 保存数据。',true);}}}
function applyTheme(){document.documentElement.dataset.theme=state.theme;$('themeSelect').value=state.theme;}
function toast(message,error=false){clearTimeout(toastTimer);$('toast').textContent=message;$('toast').className='toast'+(error?' error':'');$('toast').hidden=false;toastTimer=setTimeout(()=>$('toast').hidden=true,6500);}
function money(n,region=state.region){if(n===null||!Number.isFinite(n))return '—';const r=REGIONS[region];return r.symbol+new Intl.NumberFormat('zh-CN',{maximumFractionDigits:2,minimumFractionDigits:n%1?2:0}).format(n);}
const number=n=>new Intl.NumberFormat('zh-CN').format(n||0);
function compact(n){if(n==null)return '未知';if(n>=10000)return (n/10000).toFixed(n>=100000?0:1)+'万';return number(n);}
function percent(n,digits=1){return n===null||!Number.isFinite(n)?'—':n.toFixed(digits)+'%';}
function ratio(g){return g.reviews&&g.reviews.total>0?g.reviews.positive/g.reviews.total*100:null;}
function wilson(positive,total){if(!(total>0))return null;const z=1.96,p=positive/total;return (p+z*z/(2*total)-z*Math.sqrt((p*(1-p)+z*z/(4*total))/total))/(1+z*z/total)*100;}
function hasChinese(list){return Array.isArray(list)&&list.some(x=>x==='schinese'||x==='tchinese');}
function recommendation(g){
 const anchor=Number(filters.maxPrice)>0?Number(filters.maxPrice):REGIONS[state.region].anchor;
 const parts={quality:g.reviews?wilson(g.reviews.positive,g.reviews.total):null,price:g.price!==null?Math.max(0,Math.min(100,100*(1-Math.log1p(g.price)/Math.log1p(anchor)))):null,discount:g.discount,language:g.languages!==null?(hasChinese(g.languages)?100:0):null};
 const total=Object.values(state.weights).reduce((a,b)=>a+b,0);
 if(!total||Object.keys(parts).some(k=>state.weights[k]>0&&parts[k]===null))return {value:null,parts,anchor,weights:state.weights,total};
 const value=Object.keys(parts).reduce((s,k)=>s+(parts[k]??0)*state.weights[k]/total,0);
 return {value,parts,anchor,weights:state.weights,total};
}
function priceText(g){return g.isFree&&g.price===0?'免费':g.price===null?(g.comingSoon?'待发售':'暂无报价'):money(g.price,g.region);}
function sourceLabel(g){return g.source==='demo'?'演示':g.source==='imported'?'导入 · 未验证':'Steam 采集';}
function stamp(value,short=false){if(!value)return '未记录';return new Date(value).toLocaleString('zh-CN',short?{month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hour12:false}:{year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hour12:false});}
function sourceHint(g){if(g.source==='demo')return '演示数据 · 非实时';if(g.source==='imported')return '导入数据 · '+stamp(g.detailsAt,true);return (g.warnings.length?'旧缓存 / 部分缺失 · ':'采集于 ')+stamp(g.detailsAt,true);}
function dataset(){return state.mode==='demo'?(state.region==='cn'?DEMO:[]):state.mode==='live'?(state.live[state.region]||[]):(state.imported[state.region]||[]);}
function getGame(appid){return dataset().find(g=>g.appid===Number(appid));}
function filterGames(games){const q=filters.q.trim().toLocaleLowerCase();return games.filter(g=>{
 if(state.nav==='favorites'&&!state.favorites.has(g.appid))return false;
 if(q&&!([g.name,...g.aliases,String(g.appid),...g.genres,...g.tags,...g.developers,...g.publishers].join(' ').toLocaleLowerCase().includes(q)))return false;
 if(filters.minPrice!==''&&(g.price===null||g.price<Number(filters.minPrice)))return false;
 if(filters.maxPrice!==''&&(g.price===null||g.price>Number(filters.maxPrice)))return false;
 if(filters.priceMode==='free'&&!(g.isFree&&g.price===0))return false;
 if(filters.priceMode==='paid'&&!(g.price!==null&&g.price>0))return false;
 if(filters.priceMode==='discount'&&!(g.discount>0))return false;
 if(Number(filters.minRating)>0&&(ratio(g)===null||ratio(g)<Number(filters.minRating)))return false;
 if(filters.minReviews!==''&&(!g.reviews||g.reviews.total<Number(filters.minReviews)))return false;
 if(filters.maxReviews!==''&&(!g.reviews||g.reviews.total>Number(filters.maxReviews)))return false;
 if(filters.genres.length&&!filters.genres.some(t=>g.genres.includes(t)))return false;
 if(filters.language==='zh'&&!hasChinese(g.languages))return false;
 if(!['any','zh'].includes(filters.language)&&!g.languages?.includes(filters.language))return false;
 if(filters.chineseAudio&&!hasChinese(g.audioLanguages))return false;
 if(filters.platform!=='any'&&g.platforms[filters.platform]!==true)return false;
 for(const field of ['singleplayer','coop','multiplayer','cloud'])if(filters[field]&&g[field]!==true)return false;
 if(filters.controller&&g.controller!=='full')return false;
 if(filters.releaseAfter!=='any'&&(!g.releaseDate||Number(g.releaseDate.slice(0,4))<Number(filters.releaseAfter)))return false;
 if(filters.hideEarlyAccess&&g.earlyAccess!==false)return false;
 if(!filters.showUpcoming&&g.comingSoon)return false;
 return true;
});}
function sortValue(g,key){switch(key){case'recommend':return recommendation(g).value;case'wilson':return g.reviews?wilson(g.reviews.positive,g.reviews.total):null;case'rating':return ratio(g);case'reviews':return g.reviews?.total??null;case'priceAsc':case'priceDesc':return g.price;case'discount':return g.discount;case'release':return g.releaseDate?Date.parse(g.releaseDate):null;case'metacritic':return g.metacritic;default:return null;}}
function sortGames(games,key=state.sort){const asc=key==='priceAsc';return games.map(g=>({g,v:sortValue(g,key)})).sort((a,b)=>{if(a.v===null&&b.v!==null)return 1;if(b.v===null&&a.v!==null)return-1;if(a.v!==null&&b.v!==null&&a.v!==b.v)return asc?a.v-b.v:b.v-a.v;return (b.g.reviews?.total??0)-(a.g.reviews?.total??0)||a.g.appid-b.g.appid;}).map(x=>x.g);}
function controlsFromFilters(){for(const [key,value]of Object.entries(filters)){if(key==='genres')continue;const el=$(key==='q'?'search':key);if(!el)continue;if(el.type==='checkbox')el.checked=value;else el.value=value;}$('minRating').value=filters.minRating;$('ratingValue').textContent=Number(filters.minRating)>0?filters.minRating+'%':'不限';$('sortBy').value=state.sort;$('region').value=state.region;$('dataMode').value=state.mode;}
function renderGenres(){const counts=new Map();for(const g of dataset())for(const t of new Set(g.genres))counts.set(t,(counts.get(t)||0)+1);const genres=[...counts].sort((a,b)=>b[1]-a[1]);$('genreOptions').innerHTML=genres.length?genres.map(([t,n])=>`<button class="genre-chip ${filters.genres.includes(t)?'active':''}" data-genre="${esc(t)}" title="当前库 ${n} 款">${esc(t)}</button>`).join(''):'<span class="tiny muted">获取数据后显示类型</span>';}
function filterTokens(){
 const tokens=[],add=(key,label)=>tokens.push({key,label});
 if(filters.q)add('q','搜索：'+filters.q);
 if(filters.minPrice!==''||filters.maxPrice!=='')add('priceRange',`${filters.minPrice===''?'0':money(Number(filters.minPrice))} — ${filters.maxPrice===''?'不限':money(Number(filters.maxPrice))}`);
 if(filters.minRating>0)add('minRating',`好评 ≥ ${filters.minRating}%`);
 if(filters.language!=='any')add('language',filters.language==='zh'?'支持中文':LANGUAGE_NAMES[filters.language]);
 if(filters.minReviews!=='')add('minReviews',`评论 ≥ ${compact(Number(filters.minReviews))}`);
 if(filters.maxReviews!=='')add('maxReviews',`评论 ≤ ${compact(Number(filters.maxReviews))}`);
 for(const genre of filters.genres)add('genre:'+genre,genre);
 if(filters.platform!=='any')add('platform',PLATFORM_NAMES[filters.platform]);
 for(const k of ['singleplayer','coop','multiplayer','controller','cloud','chineseAudio'])if(filters[k])add(k,{singleplayer:'单人',coop:'合作',multiplayer:'多人',controller:'完整手柄',cloud:'云存档',chineseAudio:'中文配音'}[k]);
 if(filters.priceMode!=='any')add('priceMode',{free:'免费',paid:'付费',discount:'折扣'}[filters.priceMode]);
 if(filters.releaseAfter!=='any')add('releaseAfter',filters.releaseAfter+' 年以后');
 if(filters.hideEarlyAccess)add('hideEarlyAccess','无抢先体验');
 if(filters.showUpcoming)add('showUpcoming','含未发售');
 return tokens;
}
function clearFilter(key){
 if(key==='priceRange'){filters.minPrice='';filters.maxPrice='';}
 else if(key.startsWith('genre:'))filters.genres=filters.genres.filter(g=>g!==key.slice(6));
 else if(Object.hasOwn(DEFAULT_FILTERS,key))filters[key]=DEFAULT_FILTERS[key];
 state.page=1;render();
}
const PLATFORM_NAMES={windows:'Windows',mac:'macOS',linux:'Linux'};
function supportedPlatforms(g){return Object.keys(PLATFORM_NAMES).filter(k=>g.platforms?.[k]===true);}
function platformText(g){return supportedPlatforms(g).map(k=>PLATFORM_NAMES[k]).join(' / ')||(Object.values(g.platforms||{}).some(v=>v===null)?'平台待获取':'暂无支持平台信息');}
function renderBanner(){const data=dataset(),banner=$('sourceBanner');banner.classList.toggle('real',state.mode==='live');let html;
 if(state.mode==='demo')html=`${icon('info')}<div class="banner-main"><strong>演示模式 · ${data.length} 款样例</strong>　价格、评分、语言与标签等为模拟数据，仅展示筛选功能，不是当前报价或真实评测统计。</div><button data-action="network">获取真实数据 →</button>`;
 else if(state.mode==='import')html=`${icon('info')}<div class="banner-main"><strong>导入模式 · ${data.length} 款</strong>　内容来自本地 JSON，未独立验证${data.some(g=>g.source==='demo')?'；含演示记录':''}。不同地区不混算。</div><button data-action="network">从 Steam 复核 →</button>`;
 else{const dates=data.map(g=>g.detailsAt).filter(Boolean).sort((a,b)=>Date.parse(b)-Date.parse(a));const warnings=data.filter(g=>g.warnings.length).length;html=`${icon('info')}<div class="banner-main"><strong>${REGIONS[state.region].name}采集库 · ${data.length} 款</strong>　${dates.length?'最近一条采集于 '+esc(stamp(dates[0]))+'；各游戏时间可能不同。':'尚未获取数据。'}${warnings?' '+warnings+' 款有缓存或缺失提示。':''} 仅统计已加载游戏，不是 Steam 全库。</div><button data-action="network">继续获取 →</button>`;}
 banner.innerHTML=html;$('currencyHint').textContent=REGIONS[state.region].currency;
}
function renderStats(games){const priced=games.filter(g=>g.price!==null).map(g=>g.price).sort((a,b)=>a-b);const mid=priced.length?priced.length%2?priced[(priced.length-1)/2]:(priced[priced.length/2-1]+priced[priced.length/2])/2:null;const reviews=games.reduce((s,g)=>({positive:s.positive+(g.reviews?.positive||0),total:s.total+(g.reviews?.total||0)}),{positive:0,total:0});const discounted=games.filter(g=>g.discount>0);
 $('metricCount').textContent=number(games.length);$('metricScope').textContent=`当前库 ${number(dataset().length)} 款 · 非全库统计`;$('metricPrice').textContent=money(mid);$('metricPriced').textContent=`${priced.length} 款有报价 · 含免费项`;$('metricRating').textContent=percent(reviews.total?reviews.positive/reviews.total*100:null);$('metricReviews').textContent=`基于 ${compact(reviews.total)} 条评论${state.mode==='demo'?'（模拟）':''}`;$('metricDeals').textContent=number(discounted.length);$('metricDiscount').textContent=discounted.length?`最高减价 ${Math.max(...discounted.map(g=>g.discount))}% · 非史低标记`:'当前筛选结果中暂无已知折扣';
}

// Bounded sequential fallbacks. Probes stay off-DOM until fully decoded: no
// broken-image icon, stale request race, or changing-card image overwrite.
const COVER_TIMING=Object.freeze({perSource:4500,total:18000,failureTTL:45000,successTTL:1800000});
const CoverLoader=(()=>{
 const active=new Map(),cache=new Map();
 const observer=typeof IntersectionObserver==='function'?new IntersectionObserver(entries=>{
  for(const entry of entries)if(entry.isIntersecting){observer.unobserve(entry.target);const job=active.get(entry.target);if(job)start(job);}
 },{rootMargin:'350px'}):null;
 function remember(key,value){cache.delete(key);cache.set(key,value);while(cache.size>800)cache.delete(cache.keys().next().value);}
 function stopProbe(job){clearTimeout(job.timer);if(job.probe){job.probe.onload=null;job.probe.onerror=null;job.probe.removeAttribute('src');job.probe=null;}}
 function cleanup(job){stopProbe(job);observer?.unobserve(job.img);active.delete(job.img);}
 function status(job,kind,label){
  job.box.dataset.coverState=kind;
  const text=job.box.querySelector('.cover-status');if(text)text.textContent=label;
  const retry=job.box.querySelector('.cover-retry');if(retry)retry.hidden=kind!=='failed';
 }
 function fail(job){
  if(job.img.isConnected)status(job,'failed','封面暂不可用 · 可重试');
  remember(job.key,{url:null,until:Date.now()+COVER_TIMING.failureTTL});cleanup(job);
 }
 function next(job){
  stopProbe(job);
  if(!job.img.isConnected||!state.covers){cleanup(job);return;}
  const remaining=job.deadline-Date.now();
  if(!job.urls.length||remaining<=0){fail(job);return;}
  const url=job.urls.shift(),probe=new Image();job.probe=probe;job.attempt++;
  status(job,'loading',job.attempt===1?'正在加载封面…':'正在尝试备用封面…');
  probe.decoding='async';probe.referrerPolicy='no-referrer';
  probe.onload=()=>{
   if(job.probe!==probe)return;
   if(!job.img.isConnected||!state.covers){cleanup(job);return;}
   // Ignore tiny tracking / error pixels that may be returned with HTTP 200.
   if(probe.naturalWidth<160||probe.naturalHeight<60){next(job);return;}
   clearTimeout(job.timer);probe.onload=null;probe.onerror=null;job.probe=null;
   probe.className='cover-image';probe.alt=job.img.alt;probe.width=920;probe.height=430;
   probe.dataset.coverUrls=job.img.dataset.coverUrls;probe.dataset.appid=job.img.dataset.appid;probe.dataset.coverInit='1';
   observer?.unobserve(job.img);active.delete(job.img);
   job.img.replaceWith(probe);status(job,'loaded','');
   remember(job.key,{url,until:Date.now()+COVER_TIMING.successTTL});
  };
  probe.onerror=()=>{if(job.probe===probe)next(job);};
  job.timer=setTimeout(()=>{if(job.probe===probe)next(job);},Math.min(COVER_TIMING.perSource,remaining));
  probe.src=url;
 }
 function start(job){
  if(job.started)return;job.started=true;
  if(!job.img.isConnected||!state.covers){cleanup(job);return;}
  const hit=cache.get(job.key);
  if(hit&&hit.until>Date.now()){
   if(!hit.url){status(job,'failed','封面暂不可用 · 可重试');cleanup(job);return;}
   if(job.urls.includes(hit.url))job.urls=[hit.url,...job.urls.filter(u=>u!==hit.url)];
  }
  job.deadline=Date.now()+COVER_TIMING.total;next(job);
 }
 function init(root=document){
  for(const job of active.values())if(!job.img.isConnected||!state.covers)cleanup(job);
  root.querySelectorAll('img[data-cover-urls]:not([data-cover-init])').forEach(img=>{
   if(!state.covers)return;img.dataset.coverInit='1';
   let urls=[];try{urls=JSON.parse(img.dataset.coverUrls);}catch{}
   urls=Array.isArray(urls)?[...new Set(urls.map(u=>safeSteamImage(u,img.dataset.appid)).filter(Boolean))].slice(0,12):[];
   const job={img,box:img.closest('.cover'),urls,key:JSON.stringify(urls),timer:null,probe:null,attempt:0,started:false};
   if(!job.box)return;active.set(img,job);
   if(observer)observer.observe(img);else start(job);
  });
 }
 function retry(box){
  if(!box||!state.covers)return;
  const img=box.querySelector('img[data-cover-urls]');if(!img)return;
  const existing=active.get(img);if(existing)cleanup(existing);
  cache.delete(img.dataset.coverUrls);img.removeAttribute('data-cover-init');
  box.dataset.coverState='loading';const button=box.querySelector('.cover-retry');if(button)button.hidden=true;
  init(box);const job=active.get(img);if(job){observer?.unobserve(img);start(job);}
 }
 function retryFailed(){for(const box of document.querySelectorAll('.cover[data-cover-state="failed"]'))retry(box);}
 return {init,retry,retryFailed};
})();
function coverMarkup(g,extra=''){
 const palettes=[['#244458','#20303a'],['#4c343c','#272a40'],['#385048','#1b303b'],['#575037','#283c40'],['#3e3656','#263845'],['#1e484d','#232d4c']];const c=palettes[g.appid%palettes.length];const label=g.aliases?.find(x=>/^[a-zA-Z]/.test(x))||g.name;
 return `<div class="cover ${extra}" data-action="detail" data-id="${g.appid}" data-cover-state="${state.covers?'loading':'disabled'}" style="--art1:${c[0]};--art2:${c[1]}"><div class="cover-fallback"><span class="art-label">${esc(g.genres[0]||'GAME')}</span><span class="art-title">${esc(label)}</span><span class="cover-status">${state.covers?'封面等待加载':'封面已关闭'}</span></div>${state.covers?`<img class="cover-image" decoding="async" width="920" height="430" data-cover-urls="${esc(JSON.stringify(coverCandidates(g)))}" data-appid="${g.appid}" alt="${esc(g.name)} 商店封面" referrerpolicy="no-referrer"><button class="cover-retry" data-action="retryCover" data-id="${g.appid}" title="重试这款游戏的封面，不清除收藏或游戏数据" aria-label="重试 ${esc(g.name)} 的封面" hidden>重试封面 ↻</button>`:''}`;
}

function card(g,index){const rate=ratio(g),rec=recommendation(g),fav=state.favorites.has(g.appid),selected=state.compare.has(g.appid);const chinese=g.languages===null?'语言待获取':hasChinese(g.languages)?'中文支持':'未标注中文';const tags=g.genres.slice(0,2).concat(g.coop?['合作']:[]).slice(0,3);const platform=platformText(g);
 return `<article class="game-card ${selected?'selected':''}" data-game-id="${g.appid}">${coverMarkup(g)}<div class="cover-top"><span class="rank"># ${String(index+1).padStart(2,'0')}</span><button class="favorite-btn ${fav?'active':''}" data-action="favorite" data-id="${g.appid}" aria-label="${fav?'取消收藏':'收藏'} ${esc(g.name)}" aria-pressed="${fav}">${icon('star')}</button></div><div class="cover-bottom">${g.discount>0?`<span class="badge sale">−${g.discount}%</span>`:''}<span class="badge ${g.source==='demo'?'demo':''}">${esc(sourceLabel(g))}</span>${g.earlyAccess?'<span class="badge">抢先体验</span>':''}${g.comingSoon?'<span class="badge">未发售</span>':''}</div></div><div class="game-body"><h3 class="game-title" title="${esc(g.name)}" data-action="detail" data-id="${g.appid}" tabindex="0" role="button">${esc(g.name)}</h3><div class="game-sub">${esc(chinese)} · ${esc(platform)}</div><div class="tag-row">${tags.map(t=>`<span class="tag">${esc(t)}</span>`).join('')}</div><div class="card-review"><span class="review-value ${rate!==null&&rate>=80?'cyan':'amber'}">${percent(rate)}</span><span class="muted">好评</span><span class="muted float-right">${g.reviews?compact(g.reviews.total)+' 条评论':'评论待获取'}</span></div><div class="review-track"><span style="width:${rate??0}%"></span></div><div class="card-bottom"><div><span class="price">${esc(priceText(g))}</span>${g.discount>0&&g.originalPrice!==null?`<span class="old-price">${esc(money(g.originalPrice,g.region))}</span>`:''}</div><button class="score" data-action="detail" data-id="${g.appid}" title="本工具推荐分，不是 Steam 官方评分；点击查看计算依据"><div class="score-label">工具推荐分</div><b>${rec.value===null?'—':rec.value.toFixed(1)}</b><small> /100</small></button></div><div class="card-actions"><label><input type="checkbox" data-compare="${g.appid}" ${selected?'checked':''}>对比</label><button data-action="detail" data-id="${g.appid}" title="${esc(sourceHint(g))}" class="${g.warnings.length?'amber':''}">${g.warnings.length?'数据有提示':g.source==='demo'?'模拟 · 非实时':g.source==='imported'?'导入 · 未验证':stamp(g.detailsAt,true)}</button><a href="https://store.steampowered.com/app/${g.appid}/?cc=${g.region}&l=schinese" target="_blank" rel="noopener noreferrer">Steam ↗</a></div></div></article>`;
}
function renderTable(games,offset){const header=[['name','游戏'],['priceAsc','价格'],['discount','折扣'],['rating','好评率'],['reviews','评论数'],['recommend','推荐分']];return `<div class="table-wrap"><table><thead><tr><th>对比</th><th>#</th>${header.map(([k,t])=>`<th>${k==='name'?t:`<button data-sort="${k}">${t} ↕</button>`}</th>`).join('')}<th>中文 / 平台</th><th>收藏</th></tr></thead><tbody>${games.map((g,i)=>{const s=recommendation(g).value;return `<tr><td><input type="checkbox" data-compare="${g.appid}" ${state.compare.has(g.appid)?'checked':''} aria-label="对比 ${esc(g.name)}"></td><td class="mono muted">${offset+i+1}</td><td><button class="game-title" data-action="detail" data-id="${g.appid}">${esc(g.name)}</button><div class="table-source">${esc(sourceLabel(g))} · ${g.genres.slice(0,2).map(esc).join(' / ')}</div></td><td class="mono">${esc(priceText(g))}</td><td class="green mono">${g.discount>0?'−'+g.discount+'%':'—'}</td><td class="cyan mono">${percent(ratio(g))}</td><td class="mono">${g.reviews?number(g.reviews.total):'—'}</td><td class="cell-score">${s===null?'—':s.toFixed(1)}</td><td class="tiny muted">${g.languages===null?'未知':hasChinese(g.languages)?'支持中文':'未标注中文'}<br>${esc(platformText(g))}</td><td><button class="favorite-btn ${state.favorites.has(g.appid)?'active':''}" data-action="favorite" data-id="${g.appid}" aria-label="收藏 ${esc(g.name)}">${icon('star')}</button></td></tr>`;}).join('')}</tbody></table></div>`;}
function emptyMarkup(){const isEmpty=dataset().length===0;return `<div class="empty">${icon(isEmpty?'radar':'search')}<h3>${isEmpty?'先建立你的游戏数据集':'暂时没有匹配的游戏'}</h3><p>${isEmpty?'通过本机服务搜索 Steam、读取热销候选，或输入 AppID 获取详情。也可以导入已保存的 JSON；不会用演示数据填充真实库。':state.nav==='favorites'?'当前筛选范围没有已收藏游戏。收藏属于本地列表，不会同步 Steam 愿望单。':'试着放宽价格、语言或评论数量条件。缺失数据不会自动当作符合条件。'}</p><button class="btn primary" data-action="${isEmpty?'network':'reset'}">${isEmpty?'获取 Steam 数据':'重置筛选条件'}</button></div>`;}
function render(){
 currentResults=sortGames(filterGames(dataset()));const pages=Math.max(1,Math.ceil(currentResults.length/PAGE_SIZE));state.page=Math.max(1,Math.min(state.page,pages));
 controlsFromFilters();renderBanner();renderGenres();renderStats(currentResults);
 document.querySelectorAll('[data-nav]').forEach(el=>el.classList.toggle('active',el.dataset.nav===state.nav));$('favoritesCount').textContent=state.favorites.size;
 document.querySelectorAll('[data-preset]').forEach(el=>{const active=presetActive(el.dataset.preset);el.classList.toggle('active',active);el.setAttribute('aria-pressed',String(active));});document.querySelectorAll('[data-view]').forEach(el=>el.classList.toggle('active',el.dataset.view===state.view));
 $('resultsLabel').innerHTML=`${state.nav==='favorites'?'已收藏 · ':state.nav==='analytics'?'统计样本 · ':''}找到 <strong>${number(currentResults.length)}</strong> 款游戏`;
 $('filterTokens').innerHTML=filterTokens().map(t=>`<button class="filter-token" data-clear-filter="${esc(t.key)}" aria-label="移除${esc(t.label)}">${esc(t.label)} <span aria-hidden="true">×</span></button>`).join('');
 $('results').hidden=state.nav==='analytics';$('analytics').hidden=state.nav!=='analytics';$('viewSwitch').hidden=state.nav==='analytics';
 if(state.nav==='analytics'){renderAnalytics(currentResults);$('pagination').innerHTML='';}
 else{const offset=(state.page-1)*PAGE_SIZE,page=currentResults.slice(offset,offset+PAGE_SIZE);$('results').innerHTML=page.length?(state.view==='grid'?`<div class="game-grid">${page.map((g,i)=>card(g,offset+i)).join('')}</div>`:renderTable(page,offset)):emptyMarkup();$('pagination').innerHTML=currentResults.length?`<button class="btn small subtle" data-page="${state.page-1}" ${state.page===1?'disabled':''}>← 上一页</button><span>${state.page} / ${pages} · 每页 ${PAGE_SIZE} 款</span><button class="btn small subtle" data-page="${state.page+1}" ${state.page===pages?'disabled':''}>下一页 →</button>`:'';}
 $('resultsFootnote').textContent=(state.mode==='demo'?'当前所有统计、价格和推荐结果基于模拟样例，仅用于试用界面。 ':state.mode==='import'?'导入记录未经过本工具独立验证，请留意原始采集时间及评论口径。 ':'采集评论口径：所有语言、Steam 购买、过滤跑题评论；不等同于近期评价或特定语言商店评分。 ')+ '排序与统计仅覆盖当前筛选结果；价格以对应地区 Steam 结算页面为准。Mac 商店标记不保证新版 macOS / Apple Silicon 兼容。';
 renderCompareDock();hydrate();CoverLoader.init();
}
function bars(items){const max=Math.max(1,...items.map(x=>x[1]));return items.map(([label,n])=>`<div class="chart-row"><span class="chart-label" title="${esc(label)}">${esc(label)}</span><div class="chart-bar"><span style="width:${n/max*100}%"></span></div><span class="chart-number">${number(n)}</span></div>`).join('');}
function renderAnalytics(games){if(!games.length){$('analytics').innerHTML=emptyMarkup();return;}const r=REGIONS[state.region],bounds=state.region==='jp'?[1000,2500,5000]:state.region==='us'?[10,25,50]:[50,100,200];const priceItems=[['免费开玩',games.filter(g=>g.isFree&&g.price===0).length],[`0–${money(bounds[0])}`,games.filter(g=>g.price!==null&&!(g.isFree&&g.price===0)&&g.price<=bounds[0]).length],[`${money(bounds[0])}–${money(bounds[1])}`,games.filter(g=>g.price>bounds[0]&&g.price<=bounds[1]).length],[`${money(bounds[1])}–${money(bounds[2])}`,games.filter(g=>g.price>bounds[1]&&g.price<=bounds[2]).length],[`>${money(bounds[2])}`,games.filter(g=>g.price>bounds[2]).length],['价格未知',games.filter(g=>g.price===null).length]];
 const ratingItems=[['95%–100%',games.filter(g=>ratio(g)!==null&&ratio(g)>=95).length],['90%–<95%',games.filter(g=>ratio(g)!==null&&ratio(g)>=90&&ratio(g)<95).length],['80%–<90%',games.filter(g=>ratio(g)!==null&&ratio(g)>=80&&ratio(g)<90).length],['70%–<80%',games.filter(g=>ratio(g)!==null&&ratio(g)>=70&&ratio(g)<80).length],['<70%',games.filter(g=>ratio(g)!==null&&ratio(g)<70).length],['尚无评分',games.filter(g=>ratio(g)===null).length]];
 const genres=new Map();for(const g of games)for(const t of new Set(g.genres))genres.set(t,(genres.get(t)||0)+1);const knownLang=games.filter(g=>g.languages!==null).length;const reviewKnown=games.filter(g=>g.reviews!==null).length;const chinese=games.filter(g=>hasChinese(g.languages)).length;const points=games.filter(g=>g.price!==null&&ratio(g)!==null);const xmax=Math.max(1,...points.map(g=>g.price))*1.05;
 const svg=`<svg class="scatter" viewBox="0 0 500 260" role="img" aria-label="游戏价格与好评率散点图"><line x1="45" y1="15" x2="45" y2="222"/><line x1="45" y1="222" x2="480" y2="222"/>${[0,25,50,75,100].map(n=>`<line x1="45" y1="${222-n*2}" x2="480" y2="${222-n*2}" stroke-dasharray="3 5"/><text x="35" y="${226-n*2}" text-anchor="end">${n}%</text>`).join('')}${[0,.25,.5,.75,1].map(f=>`<text x="${45+f*425}" y="241" text-anchor="middle">${esc(money(xmax*f))}</text>`).join('')}${points.map(g=>`<circle cx="${45+g.price/xmax*425}" cy="${222-ratio(g)*2}" r="${Math.min(9,3+Math.log10(Math.max(1,g.reviews.total))*.6)}" data-action="detail" data-id="${g.appid}" tabindex="0"><title>${esc(g.name)} · ${esc(priceText(g))} · ${percent(ratio(g))}</title></circle>`).join('')}</svg>`;
 const note=state.mode==='demo'?'模拟数据 · ':'当前筛选样本 · ';
 $('analytics').innerHTML=`<section class="panel"><h3>预算分布</h3><p class="panel-sub">${note}${games.length} 款 · ${r.currency} · 边界左开右闭</p>${bars(priceItems)}</section><section class="panel"><h3>口碑分布</h3><p class="panel-sub">每款游戏计一次，不以评论量加权</p>${bars(ratingItems)}</section><section class="panel"><h3>类型构成</h3><p class="panel-sub">一款游戏可属于多种类型，合计可能超过游戏数</p>${bars([...genres].sort((a,b)=>b[1]-a[1]).slice(0,8))}</section><section class="panel"><h3>价格 × 口碑</h3><p class="panel-sub">左上方偏向低价高好评；圆点大小反映评论数量。点击查看。</p>${points.length?svg:'<div class="chart-empty">尚无同时包含价格与评分的记录</div>'}</section><section class="panel"><h3>语言与功能覆盖</h3><p class="panel-sub">未知字段不算作“支持”，也不算作“确认不支持”</p><div class="coverage-list"><div class="coverage-item"><span>中文支持 / 已知语言信息</span><b>${chinese} / ${knownLang}</b></div><div class="coverage-item"><span>合作游戏</span><b>${games.filter(g=>g.coop===true).length}</b></div><div class="coverage-item"><span>完整手柄支持</span><b>${games.filter(g=>g.controller==='full').length}</b></div><div class="coverage-item"><span>商店标注 macOS</span><b>${games.filter(g=>g.platforms.mac===true).length}</b></div><div class="coverage-item"><span>Steam 云存档</span><b>${games.filter(g=>g.cloud===true).length}</b></div></div></section><section class="panel"><h3>数据完整度</h3><p class="panel-sub">只报告已知信息，空缺不以零值填充</p>${bars([['价格可用',games.filter(g=>g.price!==null).length],['评论汇总',reviewKnown],['语言信息',knownLang],['发行日期',games.filter(g=>g.releaseDate).length],['媒体评分',games.filter(g=>g.metacritic!==null).length],['存在提示',games.filter(g=>g.warnings.length).length]])}<p class="tiny muted">史低价、真实近期评分、游玩时长、在线人数及 Deck 认证未接入，不参与推荐。</p></section>`;
}
function resetFilters(){Object.assign(filters,JSON.parse(JSON.stringify(DEFAULT_FILTERS)));state.preset='all';state.page=1;state.sort='recommend';render();persist();}
function presetPatch(name){return {
 value:{language:'zh',minPrice:'',maxPrice:String(REGIONS[state.region].budget),priceMode:'any',minRating:80,minReviews:'1000',maxReviews:''},
 quality:{minRating:90,minReviews:'1000',maxReviews:''},
 coop:{coop:true},hidden:{minRating:90,minReviews:'200',maxReviews:'10000'},mac:{platform:'mac'}
 }[name]||{};}
function presetActive(name){
 if(name==='all')return !filterTokens().length;
 return Object.entries(presetPatch(name)).every(([k,v])=>String(filters[k])===String(v));
}
function preset(name){
 if(name==='all'){resetFilters();return;}
 const patch=presetPatch(name),active=presetActive(name);
 for(const [key,value] of Object.entries(patch))filters[key]=active?DEFAULT_FILTERS[key]:value;
 state.page=1;render();persist();
}
function renderCompareDock(){const selected=[...state.compare].map(getGame).filter(Boolean);$('compareDock').hidden=!selected.length;$('compareCount').textContent=`已选 ${selected.length} / 4`;$('compareNames').textContent=selected.map(g=>g.name).join(' · ');$('compareBtn').disabled=selected.length<2;}
function toggleCompare(id,checked){if(checked&&state.compare.size>=4&&!state.compare.has(id)){toast('最多同时对比 4 款游戏。');render();return;}checked?state.compare.add(id):state.compare.delete(id);render();}
function openDialog(title,content,width='760px'){$('dialog').classList.remove('game-detail','expanded');$('dialog').scrollTop=0;$('dialogTitle').textContent=title;$('dialogBody').innerHTML=content;$('dialog').style.width=width;if(!$('dialog').open)$('dialog').showModal();hydrate($('dialog'));CoverLoader.init($('dialogBody'));}
function yesNo(v){return v===true?'支持':v===false?'未标注支持':'未知 / 未提供';}
function languagesText(list){return list===null?'未知 / 未获取':list.length?list.map(x=>LANGUAGE_NAMES[x]||x).join('、'):'未标注';}
function requirementsText(text){return String(text||'').replace(/\r\n?/g,'\n').replace(/\n[ \t]*\n+/g,'\n').trim();}
function detail(g){
 if(!g)return;
 const r=recommendation(g),val=x=>x===null?'—':x.toFixed(2),platforms=supportedPlatforms(g);
 const lines=pairs=>pairs.map(([k,v])=>`<div class="data-line"><span>${esc(k)}</span><span>${esc(v)}</span></div>`).join('');
 const warning=g.source==='demo'?'模拟记录 · 价格、评分、平台与配置等为演示属性，请联网获取真实资料。':g.source==='imported'?'用户导入记录 · 未独立验证，请在 Steam 复核。':'Steam 采集快照 · 价格以商店结算页面为准。';
 const overview=`<h3>关于这款游戏</h3><p>${esc(g.description||'未获取游戏简介。')}</p><div class="dialog-grid"><section><h3>价格与口碑</h3>${lines([['当前价格',priceText(g)],['原价',money(g.originalPrice,g.region)],['折扣',g.discount===null?'未知':g.discount+'%'],['好评率',percent(ratio(g),2)],['评论数',g.reviews?number(g.reviews.total):'未获取'],['Metacritic',g.metacritic===null?'未提供':g.metacritic+'/100']])}</section><section><h3>游戏信息</h3>${lines([['类型',g.genres.join('、')||'未知'],['发行日期',g.releaseDate||g.releaseText||'未知'],['开发商',g.developers.join('、')||'未知'],['发行商',g.publishers.join('、')||'未知'],['手柄',g.controller==='full'?'完整支持':g.controller==='partial'?'部分支持':'未提供'],['单人 / 合作',yesNo(g.singleplayer)+' / '+yesNo(g.coop)],['云存档 / 成就',yesNo(g.cloud)+' / '+(g.achievements===null?'未知':g.achievements+' 项')]])}</section></div>`;
 const requirements=`<h3>语言：支持语言与配音分开看</h3>${lines([['支持语言',languagesText(g.languages)],['完整音频',languagesText(g.audioLanguages)]])}<p class="hint">商店汇总未细分界面与字幕，请以商店语言表为准。</p><h3>硬件要求（商店原始文字）</h3>${platforms.length?platforms.map(k=>`<section class="detail-spec-wrap" data-platform-requirement="${k}"><h4>${PLATFORM_NAMES[k]}</h4><div class="requirements-grid"><div><b>最低配置</b><div class="detail-spec">${esc(requirementsText(g.requirements?.[k]?.minimum)||'尚未获取，请在 Steam 商店核对。')}</div></div>${g.requirements?.[k]?.recommended?`<div><b>推荐配置</b><div class="detail-spec">${esc(requirementsText(g.requirements[k].recommended))}</div></div>`:''}</div></section>`).join(''):'<p>平台资料待完善，暂不显示未经确认的系统配置。</p>'}${platforms.includes('mac')?'<p class="hint">macOS 商店标记不保证新版系统或 Apple Silicon 兼容。</p>':''}`;
 const scoring=`<h3>工具推荐分 <span class="green mono">${r.value===null?'待完善数据':r.value.toFixed(2)+' / 100'}</span></h3><p>按当前权重综合口碑、预算、折扣和中文支持；这是本工具的辅助指标。</p>${Object.keys(r.parts).map(k=>`<div class="breakdown"><span>${{quality:'置信口碑',price:'预算友好',discount:'折扣力度',language:'中文支持'}[k]}</span><div class="chart-bar"><span style="width:${r.parts[k]??0}%"></span></div><small>${val(r.parts[k])} × ${r.total?(r.weights[k]/r.total*100).toFixed(0):0}%</small></div>`).join('')}${lines([['95% Wilson 下界',g.reviews?percent(wilson(g.reviews.positive,g.reviews.total),2):'未知'],['正面 / 负面评论',g.reviews?`${number(g.reviews.positive)} / ${number(g.reviews.negative)}`:'未获取'],['预算参考上限',money(r.anchor)]])}<p class="hint">Wilson 下界用于平衡好评率与样本量。预算友好分 = max(0, 100 × [1 − ln(1+价格) / ln(1+参考上限)])。中文分代表商店是否标注中文。非零权重的字段缺失时综合分保持未知。</p><button class="btn subtle" data-action="weights">调整推荐权重</button>`;
 const source=`<h3>来源与数据质量</h3>${lines([['详情 / 价格采集',stamp(g.detailsAt)],['评论采集',stamp(g.reviewsAt)],['评论统计口径',g.reviews?.scope||'未提供'],['来源',sourceLabel(g)]])}${g.warnings.length?`<div class="log amber">${esc(g.warnings.join('\n'))}</div>`:''}<p>历史最低价、近期评价、在线人数、通关时长和 Deck 认证未接入。</p><button class="btn subtle" data-action="refreshDetail" data-id="${g.appid}">获取这款游戏的最新资料</button>`;
 const tabs=[['overview','概览',overview],['requirements','语言与配置',requirements],['scoring','评分依据',scoring],['source','数据来源',source]];
 openDialog(g.name,`<div class="detail-layout"><aside class="detail-aside">${coverMarkup(g,'detail-visual')}</div><h2>${esc(g.name)}</h2><p class="detail-meta">AppID ${g.appid} · ${esc(REGIONS[g.region].name)} / ${g.currency}</p><div class="detail-platforms">${platforms.length?platforms.map(k=>`<span class="tag">${PLATFORM_NAMES[k]}</span>`).join(''):`<span class="muted">${esc(platformText(g))}</span>`}</div><div class="detail-price">${esc(priceText(g))}<span>${percent(ratio(g))} 好评</span></div><div class="detail-actions"><a class="btn primary w100" href="https://store.steampowered.com/app/${g.appid}/?cc=${g.region}&l=schinese" target="_blank" rel="noopener noreferrer">在 Steam 查看 ↗</a><button class="btn subtle w100" data-action="expandDetail" aria-label="展开详情" aria-pressed="false">展开详情</button></div><div class="callout">${esc(warning)}</div></aside><div class="detail-content"><div class="detail-tabs" role="tablist" aria-label="游戏详情栏目">${tabs.map(([id,label],i)=>`<button id="detail-tab-${id}" role="tab" data-detail-tab="${id}" aria-controls="detail-panel-${id}" aria-selected="${i===0}" tabindex="${i===0?0:-1}">${label}</button>`).join('')}</div>${tabs.map(([id,label,body],i)=>`<section id="detail-panel-${id}" class="detail-panel" role="tabpanel" aria-labelledby="detail-tab-${id}" tabindex="0" ${i===0?'':'hidden'}>${body}</section>`).join('')}</div></div>`,'1180px');
 $('dialog').classList.add('game-detail');
}
function selectDetailTab(id){
 for(const tab of document.querySelectorAll('[data-detail-tab]')){const active=tab.dataset.detailTab===id;tab.setAttribute('aria-selected',String(active));tab.tabIndex=active?0:-1;}
 for(const panel of document.querySelectorAll('.detail-panel')){panel.hidden=panel.id!=='detail-panel-'+id;if(!panel.hidden)panel.scrollTop=0;}
 if(matchMedia('(max-width:800px)').matches){const layout=document.querySelector('.detail-layout'),content=document.querySelector('.detail-content');layout.scrollTop+=content.getBoundingClientRect().top-layout.getBoundingClientRect().top;}
}
function showCompare(){const games=[...state.compare].map(getGame).filter(Boolean);if(games.length<2){toast('请至少选择 2 款游戏。');return;}const rows=[['当前价格',g=>priceText(g)],['折扣',g=>g.discount===null?'未知':g.discount+'%'],['好评率',g=>percent(ratio(g),2)],['评论数量',g=>g.reviews?number(g.reviews.total):'未知'],['Wilson 下界',g=>g.reviews?percent(wilson(g.reviews.positive,g.reviews.total),2):'未知'],['工具推荐分',g=>recommendation(g).value?.toFixed(2)??'未知'],['类型',g=>g.genres.join('、')],['支持语言',g=>languagesText(g.languages)],['完整音频',g=>languagesText(g.audioLanguages)],['支持平台',platformText],['合作 / 多人',g=>yesNo(g.coop)+' / '+yesNo(g.multiplayer)],['手柄',g=>g.controller==='full'?'完整支持':g.controller==='partial'?'部分支持':'未提供'],['Metacritic',g=>g.metacritic??'未提供'],['发行时间',g=>g.releaseDate||g.releaseText||'未知'],['数据来源',sourceLabel],['价格采集时间',g=>stamp(g.detailsAt)],['数据提示',g=>g.source==='demo'?'模拟记录，非真实统计':g.warnings.join('；')||'请核对结算价']];openDialog('横向对比 · '+REGIONS[state.region].name,`<p class="tiny muted">同一地区、同一推荐权重。不会把国区价格换个符号后当作港区报价。</p><div class="table-wrap"><table class="compare-table"><thead><tr><th>维度</th>${games.map(g=>`<th><div class="game-title">${esc(g.name)}</div><a href="https://store.steampowered.com/app/${g.appid}/?cc=${g.region}&l=schinese" target="_blank" rel="noopener noreferrer">Steam ↗</a></th>`).join('')}</tr></thead><tbody>${rows.map(([k,fn])=>`<tr><td class="muted">${esc(k)}</td>${games.map(g=>`<td>${esc(fn(g))}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`,'1100px');}
function showWeights(){const labels={quality:'置信口碑',price:'预算友好',discount:'折扣力度',language:'中文支持'};openDialog('推荐权重 · 由你决定',`<p>先筛选符合硬性条件的游戏，再用这四项计算推荐分。滑块值自动按总和归一化，不必手动凑成 100。</p>${Object.keys(labels).map(k=>`<div class="weight-row"><label for="weight-${k}">${labels[k]}</label><input id="weight-${k}" type="range" min="0" max="100" step="1" value="${state.weights[k]}" data-weight="${k}"><output id="weight-out-${k}">${state.weights[k]}</output></div>`).join('')}<p id="weightsTotal" class="tiny muted">${weightSummary()}</p><div class="stack"><button class="btn primary" data-action="applyWeights">应用权重</button><button class="btn subtle" data-action="resetWeights">恢复默认</button></div><div class="divider"></div><h3>评分计算方式</h3><p>置信口碑 = 正面评价比例的 95% Wilson 下界 × 100。它在相同好评率下，降低小样本的排序优势；不代表游戏质量的置信区间。</p><pre><code>p = 正面评论数 / 总评论数；z = 1.96
下界 = [p + z²/(2n) − z√((p(1−p)+z²/(4n))/n)] / [1+z²/n]
综合分 = Σ(各项分数 × 权重) / Σ权重</code></pre><p>预算友好分按价格对数递减；设置最高预算后用该数值作为参考上限，否则使用对应地区的默认参考。折扣分使用当前减价百分比；中文支持为 100 或 0。免费游戏没有“每元评分除以零”的问题。</p><div class="callout">重要：缺失的价格、评论或语言字段不会凭空补全。某项有非零权重但缺失数据时，综合分显示“未知”并排在有分数的记录之后。</div>`);}
function weightSummary(){const total=Object.values(state.weights).reduce((a,b)=>a+b,0);return total?'当前比例：'+Object.entries(state.weights).map(([k,v])=>({quality:'口碑',price:'价格',discount:'折扣',language:'中文'}[k])+` ${(v/total*100).toFixed(1)}%`).join(' · '):'至少保留一个非零权重，否则无法计算推荐分。';}
function showAbout(){openDialog('数据来源、开源参考与边界',`<h3>这版工具能做什么</h3><p>单 HTML 提供筛选、推荐、对比、收藏、统计及 CSV / JSON 导出。真实采集通过同目录的 Python 本机服务完成；不要求 Steam 账号、Cookie 或 API Key。本工具不登录 Steam，不修改愿望单，不购买游戏。</p><div class="callout">内置 ${DEMO.length} 款是模拟数据，名称与 AppID 只用于示范导航。价格、评价、语言、类型与平台等样例字段未经当前核实。采集库与演示库完全分开。</div><h3>来源与实现参考</h3><div class="source-list"><div class="source-item"><strong><a href="https://partner.steamgames.com/doc/store/getreviews" target="_blank" rel="noopener noreferrer">Steamworks · User Reviews — Get List ↗</a></strong><p>评论使用官方文档接口；采用全部语言、Steam 购买、过滤跑题评论的 query_summary。day_range 不是“近 30 天评分”的开关。本工具没有假装提供近期评分。</p></div><div class="source-item"><strong><a href="https://github.com/IsThereAnyDeal/AugmentedSteam" target="_blank" rel="noopener noreferrer">Augmented Steam ↗</a></strong><p>功能方向参考：价格信息、细化搜索、评论数量与评分过滤。该项目采用 GPL-3.0-or-later。本页面为独立实现，没有复制其代码或以它为构建依赖。</p></div><div class="source-item"><strong><a href="https://github.com/mmuffins/SteamStorefrontAPI" target="_blank" rel="noopener noreferrer">SteamStorefrontAPI ↗</a></strong><p>参考商店详情、地区与精选条目的访问方式。其 README 明确说明 Storefront 接口并非正式公开文档接口；本工具同样不承诺长期稳定。</p></div><div class="source-item"><strong><a href="https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS" target="_blank" rel="noopener noreferrer">MDN · CORS ↗</a></strong><p>浏览器跨域读取依赖上游许可，因此没有使用来源不明的公共 CORS 代理，而是由本机服务读取白名单端点。</p></div></div><h3>边界</h3><p>统计只覆盖已加载并通过筛选的游戏，不是 Steam 全库，也不是个人账号的自动化推荐。默认排除未发售条目，后端仅接受游戏本体；DLC、试玩、软件会跳过。类型来自商店 genres，不冒充用户标签。</p><p>未接入历史最低价、跨商店比价、在线人数、真实近期评分、通关时长及 Deck 认证；这些字段不参与评分。地区切换只改变查询地区，不改变你的 Steam 账号地区，也不保证能够购买。</p><h3>隐私、缓存与验证状态</h3><p>本机服务只监听 127.0.0.1，采用同源校验、Steam 域名白名单、限速、超时与缓存。详情默认缓存 1 小时，评论缓存 6 小时；上游失败使用旧缓存时保留原时间并标出警告。启用封面会从 Steam CDN 加载图片。</p><p>Steam 可用性取决于当前网络与上游接口。采集成功后显示原始采集时间；接口变化或网络限制会显示具体错误。演示库不会自动变成真实数据，联网验证仅适用于当次成功采集的游戏。</p>`,'850px');}
function showSettings(){openDialog('显示与本地数据',`<h3>游戏封面</h3><label class="checkbox-label"><input type="checkbox" id="coversSetting" ${state.covers?'checked':''}>从 Steam CDN 加载真实封面</label><p class="tiny muted">优先读取接口提供的封面完整地址；失败或超时后自动尝试备用 Steam 图片源。图片等比完整显示，不裁切标题；全部失败时显示游戏名及“重试封面”按钮。关闭后不请求外部图片。页面逻辑不依赖外部字体或 JavaScript 库。</p><button class="btn small subtle" data-action="retryCovers">重试当前失败封面 ↻</button><p class="tiny muted">旧版已采集数据没有保存官方图片字段；在“联网获取”中刷新这些游戏后可补齐。纯 HTML 仍可使用备用路径，但无法保证每款游戏都有可用图片。</p><h3>本地保存</h3><p>收藏、显示设置和已采集数据保存在当前浏览器的 localStorage。换浏览器、切换文件打开与本机服务地址，或清除网站数据后，保存内容可能不同。建议导出 JSON 做备份；收藏不会修改你的 Steam 愿望单。</p><div class="stack"><button class="btn primary" data-action="saveSettings">保存显示设置</button><button class="btn subtle" data-action="export">导出备份</button></div><h3>数据量说明</h3><p>适用于个人选购与局部游戏池。每次最多采集 200 个 AppID，导入最多 5,000 条记录。大量全库采集应改用数据库、任务队列与官方授权数据源，不应通过高频访问或绕过限流实现。</p>`);}
const isLocal=()=>location.protocol==='http:'&&['127.0.0.1','localhost'].includes(location.hostname);
async function api(path,signal){if(!isLocal())throw Error('请使用完整包启动 server.py，并在本机服务打开页面；双击 HTML 不能直接请求此本机接口。');const ctrl=new AbortController();const timer=setTimeout(()=>ctrl.abort('timeout'),50000);const abort=()=>ctrl.abort('user');if(signal){if(signal.aborted)ctrl.abort('user');else signal.addEventListener('abort',abort,{once:true});}try{const response=await fetch(path,{headers:{'X-Steam-Lens':'1'},credentials:'omit',cache:'no-store',signal:ctrl.signal});const text=await response.text();let result;try{result=JSON.parse(text);}catch{throw Error('本机接口未返回 JSON。请使用配套 server.py，而不是普通静态 HTTP 服务。');}if(!response.ok)throw Error(result.error||`本机服务返回 HTTP ${response.status}`);return result;}catch(e){if(ctrl.signal.aborted)throw Error(signal?.aborted?'已停止采集':'请求超时；请检查网络后重试。');throw e;}finally{clearTimeout(timer);signal?.removeEventListener('abort',abort);}}
function showNetwork(){
 const local=isLocal(),disabled=local&&!state.busy?'':'disabled';
 openDialog('获取 Steam 游戏',`<div class="network-state"><span class="pill" id="networkStatus">${local?'正在检查本机服务…':'单文件模式'}</span><span class="muted">${REGIONS[state.region].name} · ${REGIONS[state.region].currency}</span></div>${!local?`<div class="callout"><b>先启动本机服务，即可一键采集。</b><br>Windows 双击同目录的 <b>start_windows.bat</b>，随后在自动打开的网页操作。</div><p><a class="btn primary" href="http://127.0.0.1:8765/">打开已启动的本机服务 ↗</a></p><details><summary>其他启动方式</summary><pre><code>python server.py
# macOS / Linux：python3 server.py</code></pre></details>`:''}
 <section class="network-quick"><h3>不知道从哪款开始？</h3><p>一键读取商店候选，自动获取详情并加入当前地区的游戏库。</p><div class="stack"><button class="btn primary" data-kind="topsellers" ${disabled}>一键获取热销游戏</button><button class="btn" data-kind="specials" ${disabled}>看看特价</button><button class="btn" data-kind="new" ${disabled}>最近发行</button></div><p class="hint">每批最多 20 款，通常需要几分钟，可随时停止；已成功获取的游戏会保留。</p></section>
 <h3>已有想找的游戏</h3><div class="network-search"><input id="onlineTerm" type="search" maxlength="4000" placeholder="输入游戏名、AppID 或粘贴 Steam 链接" aria-label="游戏名称、AppID 或 Steam 链接"><button class="btn primary" data-action="onlineSearch" ${disabled}>搜索 / 获取</button></div>
 <section class="network-progress" aria-live="polite"><p id="networkSummary"></p><progress id="networkProgress" max="1" value="0" ${state.busy?'':'hidden'}></progress><div class="stack"><button class="btn subtle small" data-action="stopTask" ${state.busy?'':'hidden'}>停止采集</button><button class="btn small" data-action="retryFailedTask" ${!state.busy&&state.retryIds.length&&state.taskOptions?.region===state.region?'':'hidden'}>重试失败 / 未完成</button><button class="btn primary small" data-action="viewCollected" ${state.live[state.region]?.length?'':'hidden'}>查看已获取游戏</button><button class="btn subtle small" id="nextOnlinePage" data-action="nextOnlinePage" ${local&&state.cursor?.hasMore&&state.cursor.region===state.region&&!state.busy?'':'disabled'}>再获取一批</button></div></section>
 <details class="network-advanced" id="networkAdvanced"><summary>批量 AppID 与更多选项</summary><textarea id="appIdsInput" placeholder="413150, 105600 或 Steam 商店链接" aria-label="AppID 或 Steam 商店链接"></textarea><div class="stack"><button class="btn primary" data-action="fetchIds" ${disabled}>获取这些游戏</button><button class="btn subtle" data-action="useDemoIds">填入样例的 AppID</button></div><p class="hint">每次最多 200 个，保留成功数据。只使用 ID，不复用演示属性。</p></details>
 <details class="network-log"><summary>采集日志与缓存说明</summary><div class="log" id="networkLog">${esc(state.logs.join('\n')||'尚未开始采集。')}</div><p class="hint">详情默认缓存 1 小时，评论 6 小时。刷新结果可请求更新；失败使用旧缓存时保留原采集时间。服务就绪不代表 Steam 已连通。</p></details>`,'820px');
 updateNetworkProgress();
 if(local)api('/api/health').then(r=>{if($('networkStatus'))$('networkStatus').textContent=r.service==='steam-lens'?'本机服务就绪':'服务标识不匹配';}).catch(e=>{if($('networkStatus'))$('networkStatus').textContent=e.message;});
}
function updateNetworkProgress(){
 if(!$('networkSummary'))return;
 const result=state.taskResult;
 $('networkSummary').textContent=state.busy?$('syncStatus').textContent:result?.region===state.region?result.message:'选择一个入口开始，成功后自动切换到已采集数据。';
 $('networkProgress').hidden=!state.busy;$('networkProgress').max=$('syncProgress').max;$('networkProgress').value=$('syncProgress').value;
 document.querySelectorAll('[data-action="stopTask"]').forEach(b=>b.hidden=!state.busy);
 document.querySelectorAll('[data-action="retryFailedTask"]').forEach(b=>b.hidden=state.busy||!state.retryIds.length||state.taskOptions?.region!==state.region);
 document.querySelectorAll('[data-action="viewCollected"]').forEach(b=>b.hidden=!state.live[state.region]?.length);
}
function submitOnline(){
 const term=$('onlineTerm').value.trim();
 if(!term){toast('输入游戏名称或链接，也可以一键获取热销游戏。');return;}
 try{if(/^[\d\s,，;；]+$/.test(term)||/https?:\/\//i.test(term))runTask({ids:parseIds(term)});else{if(term.length>100)throw Error('游戏名称请控制在 100 个字符以内。');runTask({kind:'search',term,start:0});}}catch(e){toast(e.message,true);}
}
function addLog(text){state.logs.push(text);if(state.logs.length>250)state.logs.shift();if($('networkLog')){$('networkLog').textContent=state.logs.join('\n');$('networkLog').scrollTop=$('networkLog').scrollHeight;}}
function busyUI(active){$('busyStrip').hidden=!active;for(const id of ['region','dataMode','refreshBtn'])$(id).disabled=active;$('dialogBody').querySelectorAll('[data-kind],[data-action="fetchIds"],[data-action="onlineSearch"],[data-action="nextOnlinePage"],[data-action="retryFailedTask"]').forEach(b=>b.disabled=active||!isLocal());}
function parseIds(text){const cleaned=text.replace(/https?:\/\/store\.steampowered\.com\/app\/(\d+)[^\s,，;；]*/gi,' $1 ');const tokens=cleaned.split(/[\s,，;；]+/).filter(Boolean);if(!tokens.length)throw Error('请先输入 AppID 或 Steam 商店链接。');if(tokens.some(x=>!/^[1-9]\d{0,9}$/.test(x)))throw Error('包含无法识别的内容。请只输入 AppID 或 store.steampowered.com/app/… 链接。');const ids=[...new Set(tokens.map(Number))];if(ids.length>200)throw Error('每次最多 200 个 AppID，请分批获取。');return ids;}
async function runTask(options){if(state.busy){toast('已有采集任务，请先完成或停止。');return;}if(!isLocal()){showNetwork();return;}const cc=state.region;state.retryIds=[];state.taskOptions={refresh:options.refresh===true,region:cc};state.taskResult=null;state.busy=true;state.cancelled=false;state.abort=new AbortController();state.logs=[];busyUI(true);let done=0,failed=0,queue=options.ids||[];let enteredLive=false;const pending=new Set();
 try{$('syncStatus').textContent='准备读取 Steam…';$('syncProgress').max=1;$('syncProgress').value=0;updateNetworkProgress();addLog(`地区 ${cc.toUpperCase()} / ${REGIONS[cc].currency}；开始采集。`);
 if(!options.ids){const found=await api('/api/discover?'+new URLSearchParams({cc,kind:options.kind||'search',term:options.term||'',start:String(options.start||0)}),state.abort.signal);if(!Array.isArray(found.appids))throw Error('搜索响应缺少 AppID 列表。');queue=found.appids.filter(id=>Number.isInteger(id)&&id>0);state.cursor={kind:options.kind||'search',term:options.term||'',start:found.nextStart,hasMore:found.hasMore===true,region:cc};addLog(`本页 ${queue.length} 个候选${found.total!==null&&found.total!==undefined?'；商店报告候选总数 '+found.total:''}。这不是完整采集数量。`);if(found.warning)addLog(found.warning);}
 queue=[...new Set(queue)].slice(0,200);if(!queue.length){state.taskResult={region:cc,message:'没有找到候选游戏，请尝试英文名或 Steam 链接。'};addLog('没有可用候选。可尝试英文名称或直接输入 AppID。');toast('本次没有获取到候选游戏。');return;}
 queue.forEach(id=>pending.add(id));$('syncProgress').max=queue.length;
 for(let i=0;i<queue.length;i++){if(state.cancelled)break;const id=queue[i];$('syncStatus').textContent=`正在读取 ${i+1} / ${queue.length} · AppID ${id} · 成功 ${done} / 失败 ${failed}`;updateNetworkProgress();try{const data=await api('/api/app?'+new URLSearchParams({appid:String(id),cc,refresh:options.refresh?'1':'0'}),state.abort.signal);if(state.cancelled)break;const game=normalizeGame(data.game,'steam');if(game.region!==cc||game.appid!==id)throw Error('响应的地区或 AppID 与请求不一致。');const existing=state.live[cc]||[];state.live[cc]=existing.filter(g=>g.appid!==id).concat(game);done++;pending.delete(id);addLog(`✓ ${game.name} · ${priceText(game)} · ${game.reviews?number(game.reviews.total)+' 条评论':'评论未获取'}${game.warnings.length?' [有提示]':''}`);for(const warning of game.warnings)addLog('  '+warning);
 if(!enteredLive){state.mode='live';state.compare.clear();state.page=1;enteredLive=true;}persist();render();
 }catch(e){if(state.cancelled)break;failed++;addLog(`✕ ${id}：${e.message}`);if(/HTTP 429|冷却中/.test(e.message)){addLog('检测到限流，停止当前队列。');break;}}
 $('syncProgress').value=i+1;updateNetworkProgress();
 }
 state.taskResult={region:cc,message:`${state.cancelled?'已停止':'采集完成'}：成功 ${done}，失败 ${failed}${pending.size>failed?'，未完成 '+(pending.size-failed):''}。${done?'已保存到当前地区游戏库。':''}`};
 addLog(`${state.cancelled?'已停止':'本次结束'}：成功 ${done}，失败 ${failed}。未处理条目没有被记作成功。`);toast(`${state.cancelled?'已停止采集':'采集结束'}：成功 ${done}，失败 ${failed}。${done?'已切换到真实采集库。':'未填入任何演示数据。'}`,done===0&&failed>0);
 }catch(e){state.taskResult={region:cc,message:e.message};addLog('错误：'+e.message);toast(e.message,true);}finally{state.retryIds=[...pending];state.busy=false;state.abort=null;busyUI(false);updateNetworkProgress();if($('nextOnlinePage'))$('nextOnlinePage').disabled=!(state.cursor?.hasMore&&state.cursor.region===cc);render();persist();}
}
function csvCell(value){let s=String(value??'');if(/^[\s]*[=+\-@]/.test(s))s="'"+s;return '"'+s.replace(/"/g,'""')+'"';}
function downloadFile(name,content,mime){const blob=new Blob([content],{type:mime});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);}
function exportCSV(){const rows=[['数据来源','地区','币种','AppID','游戏','现价','原价','减价百分比','好评率百分比','评论总数','正面评论','负面评论','Wilson下界百分比','工具推荐分','类型','商店标注语言','完整音频','Windows','macOS','Linux','单人','合作','多人','手柄','云存档','Metacritic','发行日期','开发商','发行商','价格采集时间','评论采集时间','评论统计口径','数据提示']];for(const g of currentResults)rows.push([sourceLabel(g),g.region,g.currency,g.appid,g.name,g.price,g.originalPrice,g.discount,ratio(g)?.toFixed(4),g.reviews?.total,g.reviews?.positive,g.reviews?.negative,g.reviews?wilson(g.reviews.positive,g.reviews.total)?.toFixed(4):'',recommendation(g).value?.toFixed(4),g.genres.join(';'),languagesText(g.languages),languagesText(g.audioLanguages),yesNo(g.platforms.windows),yesNo(g.platforms.mac),yesNo(g.platforms.linux),yesNo(g.singleplayer),yesNo(g.coop),yesNo(g.multiplayer),g.controller,yesNo(g.cloud),g.metacritic,g.releaseDate||g.releaseText,g.developers.join(';'),g.publishers.join(';'),g.detailsAt,g.reviewsAt,g.reviews?.scope,g.warnings.join(';')]);downloadFile(`steam-lens_${state.region}_${state.mode}_${new Date().toISOString().slice(0,10)}.csv`,'\uFEFF'+rows.map(r=>r.map(csvCell).join(',')).join('\r\n'),'text/csv;charset=utf-8');toast(`已导出当前筛选、排序结果 ${currentResults.length} 条，含来源和地区。`);}
function exportJSON(){const data={schemaVersion:1,kind:'steam-lens-export',exportedAt:new Date().toISOString(),mode:state.mode,region:state.region,currency:REGIONS[state.region].currency,scope:'current_region_entire_loaded_catalog',favorites:[...state.favorites],games:dataset()};downloadFile(`steam-lens_${state.region}_${state.mode}.json`,JSON.stringify(data,null,2),'application/json');toast('已导出当前地区的完整已加载数据与本地收藏 ID。');}
function showExport(){openDialog('导出数据',`<h3>CSV · 当前筛选与排序结果</h3><p>共 ${currentResults.length} 条，包含价格、类型、语言、评论数、推荐分、地区、来源与采集时间。不是只导出当前页；演示数据会明确标注。</p><button class="btn primary" data-action="exportCsv">导出 CSV</button><div class="divider"></div><h3>JSON · 当前地区的完整已加载库</h3><p>共 ${dataset().length} 条，保留全部字段与收藏 ID，方便再次导入。导入的数据默认标注为“未独立验证”，不会直接被当作新采集记录。</p><button class="btn" data-action="exportJson">导出 JSON 备份</button>`);}
async function importJSON(file){if(state.busy){toast('请先停止采集再导入。');return;}if(!file)return;if(file.size>20*1024*1024){toast('文件超过 20 MB，请拆分导入。',true);return;}try{const parsed=JSON.parse(await file.text());if(!parsed||parsed.schemaVersion!==1||!Array.isArray(parsed.games))throw Error('需要本工具 schemaVersion: 1 的 JSON，且包含 games 数组。');if(parsed.games.length>5000)throw Error('单次最多导入 5,000 条。');const byRegion={},ids=new Set();for(const raw of parsed.games){const source=parsed.mode==='demo'||raw.source==='demo'?'demo':'imported';const g=normalizeGame(raw,source),key=g.region+':'+g.appid;if(ids.has(key))throw Error(`文件内有重复地区/AppID：${key}。`);ids.add(key);(byRegion[g.region]??=[]).push(g);}if(!parsed.games.length)throw Error('文件没有游戏记录。');if(!confirm(`将向独立导入库合并 ${parsed.games.length} 条记录，同地区同 AppID 的旧导入记录会更新。真实采集库和演示库不会被改写。继续吗？`))return;for(const [cc,games]of Object.entries(byRegion)){const map=new Map((state.imported[cc]||[]).map(g=>[g.appid,g]));for(const g of games)map.set(g.appid,g);state.imported[cc]=[...map.values()];}if(Array.isArray(parsed.favorites))for(const id of parsed.favorites)if(Number.isInteger(id)&&id>0&&id<=9999999999)state.favorites.add(id);state.mode='import';state.region=Object.keys(byRegion).includes(state.region)?state.region:Object.keys(byRegion)[0];state.compare.clear();Object.assign(filters,JSON.parse(JSON.stringify(DEFAULT_FILTERS)));state.page=1;state.preset='all';persist();render();toast(`已导入 ${parsed.games.length} 条，保留来源提示并与采集库隔离。`);}catch(e){toast('导入失败：'+e.message,true);}}

// Events use escaped templates and delegates; no imported HTML, script or URL is executed.
// Image errors are handled per attempt by CoverLoader; never hide unrelated images.
document.addEventListener('keydown',e=>{if(e.target.id==='onlineTerm'&&e.key==='Enter'){e.preventDefault();submitOnline();return;}if(e.target.matches('[data-detail-tab]')&&['ArrowLeft','ArrowRight','Home','End'].includes(e.key)){e.preventDefault();const tabs=[...document.querySelectorAll('[data-detail-tab]')];let n=tabs.indexOf(e.target);n=e.key==='Home'?0:e.key==='End'?tabs.length-1:(n+(e.key==='ArrowRight'?1:-1)+tabs.length)%tabs.length;selectDetailTab(tabs[n].dataset.detailTab);tabs[n].focus();return;}if((e.key==='Enter'||e.key===' ')&&e.target.matches('[role="button"][data-action],circle[data-action]')){e.preventDefault();e.target.click();}});
$('closeDialog').onclick=()=>$('dialog').close();$('dialog').addEventListener('click',e=>{if(e.target===$('dialog')){const r=$('dialog').getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)$('dialog').close();}});
$('themeSelect').onchange=e=>{state.theme=e.target.value;applyTheme();persist();};
$('connectBtn').onclick=showNetwork;$('aboutBtn').onclick=showAbout;$('settingsBtn').onclick=showSettings;$('weightsBtn').onclick=showWeights;$('exportBtn').onclick=showExport;
$('importBtn').onclick=()=>{if(state.busy){toast('请先停止采集再导入。');return;}$('fileInput').click();};$('fileInput').onchange=async e=>{await importJSON(e.target.files?.[0]);e.target.value='';};
$('resetFilters').onclick=e=>{e.preventDefault();e.stopPropagation();resetFilters();};$('compareBtn').onclick=showCompare;$('clearCompare').onclick=()=>{state.compare.clear();render();};
$('stopSync').onclick=()=>{state.cancelled=true;state.abort?.abort();addLog('用户停止队列；服务器当前请求可能仍在结束。');};
$('refreshBtn').onclick=()=>{if(!currentResults.length){toast('没有可刷新的游戏。');return;}if(!isLocal()){showNetwork();return;}const ids=currentResults.map(g=>g.appid).slice(0,200);if(currentResults.length>200)toast('本次只刷新筛选排序后的前 200 款。');runTask({ids,refresh:true});};
$('region').onchange=e=>{state.region=e.target.value;if(state.mode==='demo'&&state.region!=='cn')state.mode='live';filters.minPrice='';filters.maxPrice='';state.compare.clear();state.page=1;state.preset=null;state.cursor=null;persist();render();toast('地区已切换，原地区价格不会混入新地区；预算范围已重置。');};
$('dataMode').onchange=e=>{state.mode=e.target.value;if(state.mode==='demo')state.region='cn';state.compare.clear();state.page=1;filters.genres=[];persist();render();};
$('sortBy').onchange=e=>{state.sort=e.target.value;state.page=1;render();persist();};
for(const key of Object.keys(filters)){if(key==='genres')continue;const el=$(key==='q'?'search':key);if(!el)continue;el.addEventListener(el.tagName==='SELECT'||el.type==='checkbox'?'change':'input',()=>{if(el.type==='checkbox')filters[key]=el.checked;else if(el.type==='number'){filters[key]=el.value===''?'':String(Math.max(0,Number(el.value)||0));}else filters[key]=el.value;state.page=1;state.preset=null;render();});}
document.addEventListener('change',e=>{if(e.target.matches('[data-compare]'))toggleCompare(Number(e.target.dataset.compare),e.target.checked);});
document.addEventListener('input',e=>{if(e.target.matches('[data-weight]')){const k=e.target.dataset.weight;$('weight-out-'+k).textContent=e.target.value;}});
document.addEventListener('click',e=>{const clear=e.target.closest('[data-clear-filter]');if(clear){clearFilter(clear.dataset.clearFilter);return;}const tab=e.target.closest('[data-detail-tab]');if(tab){selectDetailTab(tab.dataset.detailTab);return;}const nav=e.target.closest('[data-nav]');if(nav){state.nav=nav.dataset.nav;state.page=1;render();return;}const pre=e.target.closest('[data-preset]');if(pre){preset(pre.dataset.preset);return;}const genre=e.target.closest('[data-genre]');if(genre){const t=genre.dataset.genre;filters.genres=filters.genres.includes(t)?filters.genres.filter(x=>x!==t):filters.genres.concat(t);state.page=1;state.preset=null;render();return;}const view=e.target.closest('[data-view]');if(view){state.view=view.dataset.view;persist();render();return;}const sort=e.target.closest('[data-sort]');if(sort){state.sort=sort.dataset.sort==='priceAsc'&&state.sort==='priceAsc'?'priceDesc':sort.dataset.sort;state.page=1;persist();render();return;}const page=e.target.closest('[data-page]');if(page&&!page.disabled){state.page=Number(page.dataset.page);render();document.querySelector('.results-area').scrollIntoView({block:'start',behavior:'smooth'});return;}const kind=e.target.closest('[data-kind]');if(kind&&!kind.disabled){runTask({kind:kind.dataset.kind,start:0});return;}const action=e.target.closest('[data-action]');if(!action||action.disabled)return;const id=Number(action.dataset.id);
 switch(action.dataset.action){
 case'favorite':e.stopPropagation();state.favorites.has(id)?state.favorites.delete(id):state.favorites.add(id);persist();render();break;
 case'detail':if(!action.classList.contains('detail-visual'))detail(getGame(id));break;
 case'expandDetail':{const expanded=$('dialog').classList.toggle('expanded');action.textContent=expanded?'恢复窗口':'展开详情';action.setAttribute('aria-label',action.textContent);action.setAttribute('aria-pressed',String(expanded));break;}
 case'refreshDetail':if(!isLocal()){showNetwork();break;}showNetwork();runTask({ids:[id],refresh:true});break;
 case'stopTask':$('stopSync').click();break;
 case'viewCollected':state.mode='live';state.nav='discover';state.page=1;render();persist();$('dialog').close();break;
 case'retryFailedTask':if(state.taskOptions?.region===state.region)runTask({ids:[...state.retryIds],refresh:state.taskOptions.refresh});break;case'network':showNetwork();break;case'reset':resetFilters();break;case'weights':showWeights();break;
 case'applyWeights':{const weights={};for(const k of Object.keys(DEFAULT_WEIGHTS))weights[k]=Number($('weight-'+k).value);if(!Object.values(weights).some(v=>v>0)){toast('至少保留一个非零权重。',true);break;}state.weights=weights;persist();render();$('dialog').close();toast('推荐权重已应用。');break;}
 case'resetWeights':state.weights={...DEFAULT_WEIGHTS};persist();render();showWeights();break;
 case'retryCover':CoverLoader.retry(e.target.closest('.cover'));break;
 case'retryCovers':CoverLoader.retryFailed();$('dialog').close();toast('正在重试当前已显示的失败封面。');break;
 case'saveSettings':state.covers=$('coversSetting').checked;persist();render();$('dialog').close();break;
 case'export':showExport();break;case'exportCsv':exportCSV();break;case'exportJson':exportJSON();break;
 case'useDemoIds':if($('appIdsInput'))$('appIdsInput').value=DEMO.map(g=>g.appid).join(', ');break;
 case'fetchIds':try{runTask({ids:parseIds($('appIdsInput').value)});}catch(err){toast(err.message,true);}break;
 case'onlineSearch':submitOnline();break;
 case'nextOnlinePage':if(state.cursor?.hasMore&&state.cursor.region===state.region)runTask({...state.cursor});break;
 }
});
if(matchMedia('(max-width: 720px)').matches)$('filtersPanel').open=false;
applyTheme();
const headerObserver=new ResizeObserver(()=>document.documentElement.style.setProperty('--header-height',document.querySelector('header').offsetHeight+'px'));headerObserver.observe(document.querySelector('header'));
render();
// Minimal explicit surface for automated local regression tests, not a remote API.
window.SteamLensTest={wilson,ratio,recommendation,filterGames,sortGames,normalizeGame,parseIds,csvCell,dataset,filters,state,render,DEMO,safeSteamImage,coverCandidates,CoverLoader,COVER_TIMING,coverMarkup};
