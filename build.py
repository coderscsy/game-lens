"""Development helper: embed JS and deliberately synthetic sample data in one HTML."""
import json
from pathlib import Path
import random

ROOT=Path(__file__).resolve().parent
# All non-identifier fields below are illustrative values, not current market data.
rows=[
(413150,'星露谷物语','Stardew Valley',['模拟','角色扮演','独立'],48,0,98,True,True),
(105600,'泰拉瑞亚','Terraria',['动作','冒险','独立'],36,50,97,True,True),
(1145360,'哈迪斯','Hades',['动作','角色扮演','独立'],80,50,98,True,False),
(367520,'空洞骑士','Hollow Knight',['动作','冒险','独立'],48,50,97,True,False),
(588650,'死亡细胞','Dead Cells',['动作','冒险','独立'],80,50,96,True,False),
(646570,'杀戮尖塔','Slay the Spire',['策略','角色扮演','独立'],100,75,97,True,False),
(427520,'异星工厂','Factorio',['策略','模拟','独立'],100,0,97,True,True),
(975370,'矮人要塞','Dwarf Fortress',['策略','模拟','独立'],122,20,95,False,False),
(1366540,'戴森球计划','Dyson Sphere Program',['策略','模拟','独立'],70,30,96,True,False),
(294100,'环世界','RimWorld',['策略','模拟','独立'],100,20,97,True,False),
(784150,'工人与资源：苏维埃共和国','Workers & Resources',['策略','模拟'],120,30,90,False,False),
(526870,'幸福工厂','Satisfactory',['模拟','冒险','独立'],160,50,96,False,True),
(1245620,'艾尔登法环','Elden Ring',['动作','角色扮演'],300,40,92,False,True),
(1086940,'博德之门 3','Baldur’s Gate 3',['角色扮演','策略','冒险'],298,20,96,True,True),
(1091500,'赛博朋克 2077','Cyberpunk 2077',['角色扮演','动作'],298,50,89,True,False),
(292030,'巫师 3：狂猎','The Witcher 3',['角色扮演','冒险'],190,80,95,False,False),
(1174180,'荒野大镖客：救赎 2','Red Dead Redemption 2',['动作','冒险'],279,70,92,False,False),
(2358720,'黑神话：悟空','Black Myth: Wukong',['动作','角色扮演'],268,0,95,False,False),
(1426210,'双人成行','It Takes Two',['冒险','动作'],198,60,95,False,True),
(632360,'雨中冒险 2','Risk of Rain 2',['动作','独立'],80,50,91,False,True),
(548430,'深岩银河','Deep Rock Galactic',['动作','冒险','独立'],90,50,97,False,True),
(322330,'饥荒联机版','Don’t Starve Together',['冒险','模拟','独立'],48,75,95,True,True),
(381210,'黎明杀机','Dead by Daylight',['动作','冒险'],82,60,83,False,True),
(730,'Counter-Strike 2','Counter-Strike 2',['动作','免费开玩'],0,0,85,False,False),
(570,'Dota 2','Dota 2',['策略','动作','免费开玩'],0,0,82,True,False),
(108600,'僵尸毁灭工程','Project Zomboid',['角色扮演','模拟','独立'],65,30,94,True,True),
(594650,'猎杀：对决','Hunt: Showdown',['动作'],198,75,82,False,True),
(1248130,'模拟农场 22','Farming Simulator 22',['模拟'],130,50,88,True,True),
(1817190,'漫威蜘蛛侠：迈尔斯·莫拉莱斯','Spider-Man: Miles Morales',['动作','冒险'],199,50,93,False,False),
(620,'传送门 2','Portal 2',['冒险','动作'],50,80,98,True,True),
(250900,'以撒的结合：重生','The Binding of Isaac',['动作','角色扮演','独立'],48,35,97,True,False),
(1942280,'土豆兄弟','Brotato',['动作','休闲','独立'],20,40,96,True,True),
(1966720,'致命公司','Lethal Company',['冒险','独立'],58,0,95,False,True),
(648800,'木筏求生','Raft',['冒险','模拟','独立'],68,50,93,False,True),
(588430,'辐射：避难所','Fallout Shelter',['模拟','免费开玩'],0,0,84,False,False),
(252950,'火箭联盟','Rocket League',['竞速','体育','动作'],88,0,91,False,True),
]
rng=random.Random(260929)
cover_metadata=json.loads((ROOT/'demo_cover_metadata.json').read_text(encoding='utf-8'))['games']
games=[]
for i,(appid,name,en,genres,original,discount,rate,mac,coop) in enumerate(rows):
    n=rng.randint(1500,210000)
    if i in (7,10,27,32): n=rng.randint(700,8000)
    p=round(n*rate/100)
    langs=['english','schinese'] if i not in (7,10,32) else ['english']
    if i%3==0: langs+=['tchinese','japanese']
    audio=['english']
    if i in (14,17,28): audio+=['schinese']
    requirements={k:{'minimum':'演示说明：真实硬件要求尚未获取，请到 Steam 商店核实。','recommended':''} for k in ['windows','mac','linux']}
    g=dict(appid=appid,name=name,aliases=[en],region='cn',currency='CNY',price=round(original*(1-discount/100),2),originalPrice=original,discount=discount,isFree=original==0,
      genres=genres,tags=[],languages=langs,audioLanguages=audio,languageText='',reviews={'total':n,'positive':p,'negative':n-p,'description':'模拟评论汇总','scope':'demo_simulated'},
      metacritic=80+i%16 if i%3==0 else None,platforms={'windows':True,'mac':mac,'linux':mac and i%2==0},
      singleplayer=i not in (18,22,23,24,32),coop=coop,multiplayer=coop or i in (23,24),onlineCoop=coop,localCoop=coop and i%3==0,controller='full' if i%5 else None,cloud=i%6!=0,achievements=20+i*3,
      releaseDate=f'{2013+i%12}-{i%12+1:02d}-{i%25+1:02d}',releaseText='演示发行日期',comingSoon=False,earlyAccess=i in (8,25,32),
      developers=['演示开发商'],publishers=['演示发行商'],description=f'这条 {name} 记录用于展示价格、{genres[0]}分类、语言与评分的联合筛选。所有示例属性为模拟值；请联网获取真实商店资料后再决定是否购买。',
      requiredAge=None,dlcCount=None,requirements=requirements,source='demo',detailsAt=None,reviewsAt=None,warnings=[])
    if i==34:
      g['reviews']=None;g['warnings']=['演示“评论缺失”场景：不应生成 0% 或虚构好评率。']
    if i==35:
      g['price']=None;g['originalPrice']=None;g['discount']=None;g['warnings']=['演示“价格缺失”场景：不应当作免费或混用其他地区价格。']
    # Only visual metadata is real here; prices, platforms and other demo
    # attributes stay explicitly synthetic. Building never contacts Steam.
    g.update({k:v for k,v in cover_metadata.get(str(appid),{}).items()
              if k in ('headerImage','capsuleImage','capsuleImageV5')})
    games.append(g)
text=(ROOT/'ui.template.html').read_text(encoding='utf-8')
text=text.replace('__DEMO__',json.dumps(games,ensure_ascii=False,separators=(',',':')).replace('</','<\\/'))
text=text.replace('__SCRIPT__',(ROOT/'app.js').read_text(encoding='utf-8'))
(ROOT/'steam_lens.html').write_text(text, encoding='utf-8')
(ROOT/'demo_data.json').write_text(json.dumps({'schemaVersion':1,'kind':'steam-lens-export','mode':'demo','region':'cn','currency':'CNY','games':games,'favorites':[]},ensure_ascii=False,indent=2), encoding='utf-8')
print(f'Built {ROOT/"steam_lens.html"}: {len(games)} synthetic samples, {len(text.encode()):,} bytes')
