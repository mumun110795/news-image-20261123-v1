#!/usr/bin/env python3
"""
THE MONDAY GLOBE — "Sum up 23 November's world news in one image"
make.fun bounty news-image-20261123. Original procedural artwork (PIL only).
All stories verified by live research on Mon 23 Nov 2026 (see SOURCES.md).

This generator renders the SQUARE hand-in edition: a dense 1024x1024
broadsheet front page written to entry.png (the sealed gate accepts at most
1024x1024 px and 1 MiB). The tall master render is kept separately as
news-image-20261123.png and is not touched by this script.

The page is drawn on a 2048x2048 canvas (S = 2 supersampling) and downscaled
with LANCZOS so the fine print stays crisp at 1024. All layout maths below is
in 1024-space "design units"; helpers scale coordinates and font sizes by S.
Illustrations are drawn once onto a reference canvas and cover-cropped into
their tiles, so the artwork keeps its proportions at any tile aspect.
"""
from PIL import Image, ImageDraw, ImageFont
import math, random, os

OUT = os.path.dirname(os.path.abspath(__file__))
S = 2                      # supersampling factor
W, H = 1024, 1024          # design size (final entry.png size)
PAPER   = (246, 240, 226)
PAPER_D = (238, 229, 208)
INK     = (22, 20, 16)
INK_SOFT= (58, 54, 46)
RED     = (164, 32, 28)
NAVY    = (30, 48, 84)
GOLD    = (176, 132, 44)
TEAL    = (28, 92, 96)
SKY     = (196, 214, 224)
SAND    = (224, 205, 168)

F_DIR = "/usr/share/fonts/truetype/noto/"
D_DIR = "/usr/share/fonts/truetype/dejavu/"
FONT_SCALE = S             # layout draws at S; illustration tiles draw at 1
def F(name, size): return ImageFont.truetype(name, int(round(size * FONT_SCALE)))
def mast(size):  return F(F_DIR + "NotoSerifDisplay-Black.ttf", size)
def serifB(size):return F(F_DIR + "NotoSerif-Bold.ttf", size)
def serif(size): return F(F_DIR + "NotoSerif-Regular.ttf", size)
def sansB(size): return F(F_DIR + "NotoSans-Bold.ttf", size)
def sans(size):  return F(F_DIR + "NotoSans-Regular.ttf", size)
def sansCB(size):return F(F_DIR + "NotoSans-CondensedBold.ttf", size)
def mono(size):  return F(D_DIR + "DejaVuSansMono.ttf", size)

img = Image.new("RGB", (W * S, H * S), PAPER)
dr = ImageDraw.Draw(img, "RGBA")

def tw(font, s):
    """Raw pixel width on the current canvas (used inside illustrations)."""
    b = dr.textbbox((0, 0), s, font=font); return b[2] - b[0]
def twd(font, s):
    """Width in design units (layout maths)."""
    return tw(font, s) / S
def th(font, s="Ag"):
    b = dr.textbbox((0, 0), s, font=font); return b[3] - b[1]

def wrap(text, font, maxw):
    """Greedy word wrap; maxw in design units."""
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if twd(font, t) <= maxw: cur = t
        else:
            if cur: lines.append(cur)
            cur = w_
    if cur: lines.append(cur)
    return lines

def text_block(x, y, text, font, maxw, leading, fill=INK, max_lines=None):
    """Draw wrapped text at design (x, y); leading is a multiple of font size.
    Returns the design y just below the block."""
    lines = wrap(text, font, maxw)
    if max_lines: lines = lines[:max_lines]
    lh = font.size / S * leading
    for i, ln in enumerate(lines):
        dr.text((x * S, (y + i * lh) * S), ln, font=font, fill=fill)
    return y + len(lines) * lh

def text_top(x, y, s, font, fill=INK, align="left"):
    """Draw a single line so its GLYPHS start exactly at design (x, y)
    (compensates for the font's internal bbox offset). Returns design width."""
    b = dr.textbbox((0, 0), s, font=font)
    wdt = (b[2] - b[0]) / S
    if align == "center": x = x - wdt / 2
    elif align == "right": x = x - wdt
    dr.text((x * S - b[0], y * S - b[1]), s, font=font, fill=fill)
    return wdt

def rule(x0, x1, y, wdt=2, fill=INK):
    dr.line([(x0 * S, y * S), (x1 * S, y * S)], fill=fill, width=max(1, int(wdt * S)))

def kicker(x, y, place, topic, color=RED, size=10):
    dr.text((x * S, y * S), place, font=sansB(size), fill=color)
    w1 = twd(sansB(size), place)
    dr.text(((x + w1 + 5) * S, y * S), "· " + topic, font=sansB(size), fill=INK_SOFT)
    return y + size * 1.45

def chip(x, y, label, fillc, txtc=(255, 255, 255), size=8.5, pad=8):
    fnt = sansB(size); wdt = twd(fnt, label) + pad * 2; hgt = size * 1.75
    dr.rounded_rectangle([x * S, y * S, (x + wdt) * S, (y + hgt) * S], radius=4 * S, fill=fillc)
    dr.text(((x + pad) * S, (y + hgt / 2 - size / 2 - 1) * S), label, font=fnt, fill=txtc)
    return x + wdt + 6

# Rich-text (mixed-font) wrapping, used for the compact briefs.
def rich_lines(segments, maxw):
    tokens = []
    for text, font, fill in segments:
        for w_ in text.split(" "):
            if w_: tokens.append((w_, font, fill))
    lines, cur, curw = [], [], 0.0
    for tok in tokens:
        w_ = twd(tok[1], tok[0])
        add = w_ if not cur else w_ + twd(tok[1], " ")
        if cur and curw + add > maxw:
            lines.append(cur); cur, curw = [tok], w_
        else:
            cur.append(tok); curw += add
    if cur: lines.append(cur)
    return lines

def draw_rich(x, y, segments, maxw, lh):
    lines = rich_lines(segments, maxw)
    for li, line in enumerate(lines):
        cx = x
        for w_, font, fill in line:
            if cx > x: cx += twd(font, " ")
            dr.text((cx * S, (y + li * lh) * S), w_, font=font, fill=fill)
            cx += twd(font, w_)
    return y + len(lines) * lh

# ---------------------------------------------------------------- stories
# heroes: (key, place, topic, region, headline, body)
HEROES = [
 ("cop31", "ANTALYA", "CLIMATE", "WORLD",
  "COP31 ENDS WITH NO DEAL — A CLIMATE SUMMIT COLLAPSES",
  "The Antalya Pact died on Sunday night, 44 hours into overtime, when the EU, Panama, the "
  "Marshall Islands, Norway and Vanuatu refused to endorse a text that never once mentioned "
  "fossil fuels. Some 130 countries had demanded transition language; petrostates, led by "
  "Saudi Arabia, held the line. The longest COP in history is the first to end without an "
  "overarching deal since Copenhagen in 2009. “We will not endorse a deal that does not even "
  "mention fossil fuels,” said Ireland's Darragh O'Brien for the EU. President Murat Kurum "
  "conceded: “There is no consensus on this document.” Australia's PM called the failure a "
  "sign of “difficult geopolitical times.”"),
 ("sparta", "GULF OF FINLAND", "WAR AT SEA", "EUROPE",
  "SPARTA II TOWED OUT OF FINNISH WATERS",
  "The drone-struck Russian cargo ship was towed out of Finland's waters on Sunday, its fire "
  "out and all 16 crew safe. Finnish, Estonian and Russian vessels fought the blaze together "
  "after two drones hit the Kaliningrad-bound ship on Saturday. President Stubb thanked the "
  "responders; Helsinki says Ukraine was likely behind the strike."),
 ("benghazi", "BENGHAZI", "MEDITERRANEAN", "AFRICA",
  "RUSSIAN CORVETTE SUNK IN LIBYAN PORT",
  "Suspected Ukrainian sea drones sank the Russian navy corvette Merkury at Benghazi on "
  "Sunday — satellite images show her capsized, bow above water. Ten people were hurt, none "
  "killed; a Malta-flagged merchantman was hit hours later. The UN demands an investigation "
  "and warns Libya “must not become a battleground” for foreign wars."),
]

CARDS = [
 ("dymer", "DYMER", "UKRAINE", "EUROPE",
  "NINE DEAD IN DYMER RUBBLE; A CHILD PULLED ALIVE",
  "The toll from the Russian drone that levelled a five-storey block rose to nine on Monday. "
  "Rescuers freed a boy alive on Sunday evening; 11 neighbours are still sought. Across the "
  "Kyiv region 12 died overnight. Zelenskyy counts 2,700 drones fired at Ukraine in a week."),
 ("banten", "CIKANDE, BANTEN", "DISASTER", "ASIA",
  "FACTORY FIRE TOLL CONFIRMED AT 24, DOZENS MISSING",
  "Indonesia confirmed 24 dead on Monday after fire tore through the Milkita candy factory "
  "on Saturday night. About 30 workers are still missing; 24 body bags were recovered and "
  "DNA teams are identifying the remains. A short circuit is the suspected cause."),
 ("hormuz", "STRAIT OF HORMUZ", "CONFLICT", "MIDDLE EAST",
  "IRAN CLAIMS A FOURTH US DRONE DOWNED IN 24 HOURS",
  "The IRGC says it destroyed a US MQ-1 east of the strait on Sunday — the 20th of its type "
  "and the fourth in a day. Washington has not commented. Around 25 tankers have been hit in "
  "a week; traffic through the strait runs 65% below pre-war levels."),
 ("gaza", "GAZA", "CEASEFIRE", "MIDDLE EAST",
  "TWO KILLED IN KHAN YOUNIS AS THE TRUCE FRAYS",
  "An Israeli strike in the south killed two Palestinians on Sunday, a day after four died "
  "across the Strip. Gaza's Health Ministry puts deaths since the ceasefire at 1,675. Hamas "
  "seeks an urgent mediators' meeting after a strike killed three soup-kitchen workers."),
 ("sinaloa", "SINALOA", "CARTELS", "AMERICAS",
  "AFTER 'EL CHAPO ISIDRO', A SUCCESSION FIGHT LOOMS",
  "The capture of FBI most-wanted boss Fausto Isidro Meza Flores — seized Friday in a "
  "gunbattle that killed 11 — risks a bloody battle for his smuggling routes, analysts warn. "
  "His No. 2 was also taken; the US had offered $5m for the 44-year-old capo."),
 ("khartoum", "KHARTOUM", "SUDAN", "AFRICA",
  "DRONES HIT HOMES AND A UN BUILDING IN KHARTOUM",
  "Dawn drone strikes damaged homes and a UN premises in the capital on Sunday. The army "
  "says the drones were launched from Ethiopia's Bahir Dar airport; Addis Ababa denies it. "
  "Sudan's war has killed more than 200,000 and displaced millions since 2023."),
 ("washington", "WASHINGTON", "SECURITY", "AMERICAS",
  "AIRLINES ON ALERT FOR THANKSGIVING WEEK",
  "The FBI, DHS and TSA have warned carriers that al-Qaeda supporters are praising "
  "September's flydubai cockpit attack and urging copycats. Officials stress there is no "
  "specific, credible plot — but some six million Americans will fly between 24–30 Nov."),
 ("newdelhi", "NEW DELHI", "DIPLOMACY", "ASIA",
  "NEPAL'S BALEN SHAH MEETS MODI IN DELHI TODAY",
  "The rapper-turned-PM makes his first bilateral visit: energy deals, new air routes and "
  "flood reconstruction top the agenda after August floods killed 1,450 in Nepal. A package "
  "worth nearly $2bn is under discussion; a Janakpur–Ayodhya train may be launched."),
 ("markets", "MARKETS", "ECONOMY", "WORLD",
  "GOLD REBOUNDS AFTER ITS WORST WEEK IN EIGHT MONTHS",
  "Bullion jumped about 2% on Monday after a 9% plunge — its steepest weekly fall in eight "
  "months — as traders cut bets on Fed rate hikes. Wall Street's Friday rout (Nasdaq -5.3%) "
  "was driven by AI-spending fears. Brent slipped below $92; WTI held near $83."),
 ("turin", "TURIN", "SPORT", "EUROPE",
  "ALCARAZ BEATS No. 1 ZVEREV FOR FIRST ATP FINALS TITLE",
  "Carlos Alcaraz powered past world No. 1 Alexander Zverev 6-2 7-6(7) on Sunday to claim "
  "the one big title missing from his collection. The unbeaten champion banks a record "
  "$5.17m and a 14th straight win after four months out injured."),
]

BRIEFS = [
 ("BAHRAIN", "GULF", "MIDDLE EAST",
  "Iran strike wounds two on Sitra; the IRGC claims two US Patriot radars destroyed at "
  "al-Riffa and Awali. The GCC condemns the attacks; CENTCOM denies an F-16 was damaged."),
 ("HORMUZ", "DEFENCE", "MIDDLE EAST",
  "US orders its first Squire seaglider drones to patrol the strait — but their 185 km "
  "range is already questioned. The low-flying craft deploy to the Middle East in 2027."),
 ("MANILA", "SECURITY", "ASIA",
  "A Chinese H-6 bomber turned back about 170 km from Manila after appearing on public "
  "trackers over the South China Sea. A simulated missile launch is speculated, unconfirmed."),
 ("TALLINN", "SECURITY", "EUROPE",
  "Estonia shuts all Russia border crossings on 1 Dec; families rush to cross at Narva. "
  "Moscow calls the sabotage charge “unsubstantiated” and accuses Tallinn of building a wall."),
 ("BRASILIA", "HEALTH", "AMERICAS",
  "Bolsonaro is stable in intensive care for a third day with an acute bowel obstruction; "
  "no discharge is forecast. The Supreme Court rules on his sentence-reduction law on 4 Dec."),
 ("BRASILIA", "ECONOMY", "AMERICAS",
  "The lower house takes up Lula's R$50–60bn fiscal package, passed by the Senate on 18 Nov. "
  "Debt stands at 83% of GDP and the finance minister's chair is still empty."),
 ("BAYELSA", "NIGERIA", "AFRICA",
  "At least 24 dead after an overloaded boat carrying mourners to a funeral capsized on "
  "Friday. Few wore life jackets; the operator has been detained. (AP)"),
 ("JUBA", "SOUTH SUDAN", "AFRICA",
  "Twenty-four civilians killed in fresh violence, as the young state's fragile peace "
  "continues to unravel. (AFP)"),
 ("GENEVA", "HEALTH", "AFRICA",
  "The WHO chief pleads for peace in the Ebola-hit east of DR Congo, where fighting blocks "
  "the response. (AFP)"),
 ("SEOUL", "KOREA", "ASIA",
  "Kim Jong Un says North Korea seeks security, not supremacy, in a speech marking a "
  "military anniversary. (AFP)"),
 ("WARSAW", "EUROPE", "EUROPE",
  "Poland says three Russian cruise missiles struck its territory on Friday — the latest "
  "spillover of the Ukraine war onto NATO soil. (AFP)"),
 ("JERUSALEM", "POLITICS", "MIDDLE EAST",
  "Netanyahu's Likud and Eisenkot's party end unity talks without a deal. Eisenkot, the "
  "ex-army chief, condemns settler arson attacks in the West Bank as “Jewish terrorism”."),
 ("WASHINGTON", "POLITICS", "AMERICAS",
  "Democrats win their largest House majority since 1992 after flipping a North Carolina "
  "seat. (BBC)"),
 ("WASHINGTON", "HEALTH", "AMERICAS",
  "Trump reposts El-Sayed's “TrumpCare” pitch for universal health care, scrambling both "
  "parties' messaging. (Washington Post)"),
 ("IOWA", "UNITED STATES", "AMERICAS",
  "The Army plans to detonate tons of unstable explosives at a shuttered plant — despite a "
  "court order against it."),
 ("RED SEA", "YEMEN", "MIDDLE EAST",
  "The Saudi-led coalition says it intercepted a Houthi missile in the western region; the "
  "Houthis report four killed in a Saudi assault on a port city."),
 ("VANUATU", "PACIFIC", "OCEANIA",
  "A magnitude 6.5 earthquake struck deep beneath the Vanuatu region early Monday. No "
  "tsunami threat was reported. (USGS)"),
 ("LONDON", "FOOTBALL", "EUROPE",
  "FIFA is set to confirm the UK as host of the 2035 Women's World Cup — a first World Cup "
  "on British soil since 1966."),
 ("BASRA", "IRAQ", "MIDDLE EAST",
  "Four killed and 35 injured in Saturday's Hartha power-station fire; the PM orders an "
  "urgent investigation into the blaze. (Sat)"),
 ("DAMASCUS", "DRUGS", "MIDDLE EAST",
  "Syria destroys 400 million Captagon pills in one of the largest drug hauls on record."),
]

# --- Square-edition body texts: same facts, tighter wording (headlines,
# --- kickers and story selection are unchanged from the lists above).
SQ_HERO_BODY = {
 "cop31":
  "The Antalya Pact died on Sunday night, 44 hours into overtime, when the EU, Panama, the "
  "Marshall Islands, Norway and Vanuatu refused to endorse a text that never once mentioned "
  "fossil fuels. Some 130 countries had demanded transition language; petrostates, led by "
  "Saudi Arabia, held the line. The longest COP in history is the first to end without an "
  "overarching deal since Copenhagen in 2009. “We will not endorse a deal that does not even "
  "mention fossil fuels,” said Ireland's Darragh O'Brien for the EU. President Kurum "
  "conceded: “There is no consensus on this document.”",
 "sparta":
  "The drone-struck Russian cargo ship was towed out of Finland's waters on Sunday, its fire "
  "out and all 16 crew safe. Finnish, Estonian and Russian vessels fought the blaze together "
  "after two drones hit the Kaliningrad-bound ship on Saturday. President Stubb thanked the "
  "responders; Helsinki says Ukraine was likely behind the strike.",
 "benghazi":
  "Suspected Ukrainian sea drones sank the Russian navy corvette Merkury at Benghazi on "
  "Sunday — satellite images show her capsized, bow above water. Ten people were hurt, none "
  "killed; a Malta-flagged merchantman was hit hours later. The UN demands an investigation "
  "and warns Libya “must not become a battleground” for foreign wars.",
}

SQ_CARD_BODY = {
 "dymer":
  "The toll from the drone that levelled a five-storey block rose to nine on Monday. "
  "Rescuers freed a boy alive on Sunday evening; 11 neighbours are still sought.",
 "banten":
  "Indonesia confirmed 24 dead on Monday after fire tore through the Milkita candy factory "
  "on Saturday night. About 30 workers are still missing; DNA teams are at work.",
 "hormuz":
  "The IRGC says it destroyed a US MQ-1 east of the strait on Sunday — the fourth US drone "
  "downed in 24 hours. Traffic through the strait runs 65% below pre-war levels.",
 "gaza":
  "An Israeli strike in the south killed two Palestinians on Sunday, a day after four died "
  "across the Strip. Gaza's Health Ministry puts deaths since the ceasefire at 1,675.",
 "sinaloa":
  "The capture of FBI most-wanted boss Fausto Isidro Meza Flores — seized Friday in a "
  "gunbattle that killed 11 — risks a bloody battle for his smuggling routes, analysts warn.",
 "khartoum":
  "Dawn drone strikes damaged homes and a UN premises in the capital on Sunday. The army "
  "blames Ethiopia's Bahir Dar airport; Addis Ababa denies it.",
 "washington":
  "The FBI, DHS and TSA warn carriers that al-Qaeda supporters are urging copycats of "
  "September's flydubai cockpit attack. No specific plot is known; six million Americans "
  "fly this week.",
 "newdelhi":
  "The rapper-turned-PM makes his first bilateral visit: energy deals, new air routes and "
  "flood reconstruction top the agenda after August floods killed 1,450 in Nepal.",
 "markets":
  "Bullion jumped about 2% on Monday after a 9% plunge — its steepest weekly fall in eight "
  "months — as traders cut bets on Fed rate hikes. Brent slipped below $92.",
 "turin":
  "Carlos Alcaraz powered past world No. 1 Alexander Zverev 6-2 7-6(7) on Sunday to claim "
  "the one big title missing from his collection, banking a record $5.17m.",
}

SQ_BRIEF_BODY = {
 ("BAHRAIN", "GULF"):
  "Iran strike wounds two on Sitra; the IRGC claims two US Patriot radars destroyed. "
  "The GCC condemns the attacks.",
 ("HORMUZ", "DEFENCE"):
  "US orders its first Squire seaglider drones for strait patrols, though their 185 km "
  "range is questioned. Deployment: 2027.",
 ("MANILA", "SECURITY"):
  "A Chinese H-6 bomber turned back about 170 km from Manila after appearing on public "
  "trackers over the South China Sea.",
 ("TALLINN", "SECURITY"):
  "Estonia shuts all Russia border crossings on 1 Dec; families rush to cross at Narva. "
  "Moscow rejects the sabotage charge.",
 ("BRASILIA", "HEALTH"):
  "Bolsonaro is stable in intensive care for a third day with an acute bowel obstruction; "
  "no discharge is forecast.",
 ("BRASILIA", "ECONOMY"):
  "The lower house takes up Lula's R$50–60bn fiscal package, passed by the Senate on "
  "18 Nov. Debt stands at 83% of GDP.",
 ("BAYELSA", "NIGERIA"):
  "At least 24 dead after an overloaded boat carrying mourners to a funeral capsized on "
  "Friday. Few wore life jackets. (AP)",
 ("JUBA", "SOUTH SUDAN"):
  "Twenty-four civilians killed in fresh violence, as the young state's fragile peace "
  "continues to unravel. (AFP)",
 ("GENEVA", "HEALTH"):
  "The WHO chief pleads for peace in the Ebola-hit east of DR Congo, where fighting "
  "blocks the response. (AFP)",
 ("SEOUL", "KOREA"):
  "Kim Jong Un says North Korea seeks security, not supremacy, in a speech marking a "
  "military anniversary. (AFP)",
 ("WARSAW", "EUROPE"):
  "Poland says three Russian cruise missiles struck its territory on Friday — the latest "
  "spillover onto NATO soil. (AFP)",
 ("JERUSALEM", "POLITICS"):
  "Netanyahu's Likud and Eisenkot's party end unity talks without a deal. Eisenkot "
  "condemns settler arson as “Jewish terrorism”.",
 ("WASHINGTON", "POLITICS"):
  "Democrats win their largest House majority since 1992 after flipping a North "
  "Carolina seat. (BBC)",
 ("WASHINGTON", "HEALTH"):
  "Trump reposts El-Sayed's “TrumpCare” pitch for universal health care, scrambling "
  "both parties' messaging. (Washington Post)",
 ("IOWA", "UNITED STATES"):
  "The Army plans to detonate tons of unstable explosives at a shuttered plant — "
  "despite a court order against it.",
 ("RED SEA", "YEMEN"):
  "The Saudi-led coalition says it intercepted a Houthi missile; the Houthis report "
  "four killed in a Saudi assault on a port city.",
 ("VANUATU", "PACIFIC"):
  "A magnitude 6.5 earthquake struck deep beneath the Vanuatu region early Monday. "
  "No tsunami threat was reported. (USGS)",
 ("LONDON", "FOOTBALL"):
  "FIFA is set to confirm the UK as host of the 2035 Women's World Cup — a first "
  "World Cup on British soil since 1966.",
 ("BASRA", "IRAQ"):
  "Four killed and 35 injured in Saturday's Hartha power-station fire; the PM orders "
  "an urgent investigation. (Sat)",
 ("DAMASCUS", "DRUGS"):
  "Syria destroys 400 million Captagon pills in one of the largest drug hauls on record.",
}

STATS = [
 ("0", "deals adopted\nat COP31"),
 ("24", "dead confirmed in\nthe Banten blaze"),
 ("9", "dead in the rubble\nat Dymer"),
 ("65%", "drop in Hormuz\nshipping traffic"),
 ("$3,610", "gold, per ounce,\nMonday rebound"),
]

REGION_COLORS = {
 "EUROPE": NAVY, "MIDDLE EAST": RED, "ASIA": TEAL, "AMERICAS": GOLD,
 "AFRICA": (122, 74, 30), "OCEANIA": (70, 110, 60), "WORLD": INK_SOFT,
}

# ---------------------------------------------------------------- artwork
# The ill_* functions below are the edition's original artwork, unchanged.
# They draw in whatever box they are given; draw_ill() renders them once onto
# a reference canvas and cover-crops the result into each layout tile.
def art_box(x, y, w, h, sky=(205, 218, 228)):
    dr.rectangle([x, y, x + w, y + h], fill=sky)
    return (x, y, w, h)

def smoke(cx, cy, s, n=7, col=(70, 66, 60)):
    rnd = random.Random(int(cx + cy))
    for i in range(n):
        r = max(16, s * (0.35 + 0.16 * i))
        j = min(10, int(r // 3))
        ox = i * s * 0.28; oy = -i * s * 0.30
        dr.ellipse([cx - r + ox + rnd.randint(-j, j), cy - r + oy,
                    cx + r + ox + rnd.randint(-j, j), cy + r + oy], fill=col + (150,))

def waves(x, y, w, n=5, col=NAVY):
    for i in range(n):
        yy = y + i * 16
        for xx in range(x, x + w - 46, 92):
            dr.arc([xx, yy, xx + 46, yy + 16], 0, 180, fill=col, width=4)

def sun_disc(cx, cy, r, col=(232, 178, 60)):
    dr.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)

def drone_sil(cx, cy, s, col=INK):
    dr.polygon([(cx - s, cy), (cx + s, cy), (cx + s * 0.3, cy + s * 0.28), (cx - s * 0.3, cy + s * 0.28)], fill=col)
    dr.line([(cx - s * 1.5, cy - s * 0.1), (cx - s * 0.4, cy + s * 0.1)], fill=col, width=max(3, s // 6))
    dr.line([(cx + s * 1.5, cy - s * 0.1), (cx + s * 0.4, cy + s * 0.1)], fill=col, width=max(3, s // 6))
    dr.line([(cx, cy + s * 0.2), (cx, cy + s * 0.75)], fill=col, width=max(3, s // 6))

def ill_cop31(x, y, w, h):
    art_box(x, y, w, h, (198, 210, 220))
    # cracked globe
    cx, cy, r = x + w // 2, y + h // 2 - 10, min(w, h) // 3
    dr.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(120, 165, 190), outline=INK, width=5)
    for gx, gy, gw, gh in [(-.55, -.3, .5, .34), (-.2, .25, .62, .3), (.3, -.55, .4, .3), (.42, .3, .34, .26)]:
        dr.ellipse([cx + r * gx, cy + r * gy, cx + r * (gx + gw), cy + r * (gy + gh)], fill=(96, 140, 96))
    pts = [(cx - r * .1, cy - r), (cx + r * .12, cy - r * .45), (cx - r * .08, cy - r * .05),
           (cx + r * .2, cy + r * .4), (cx + r * .02, cy + r)]
    dr.line(pts, fill=INK, width=6)
    # conference table arc + delegates
    dr.arc([x + 40, y + h - 190, x + w - 40, y + h + 60], 180, 360, fill=INK, width=8)
    for i in range(9):
        px = x + 90 + i * (w - 180) // 8
        dr.ellipse([px - 13, y + h - 128, px + 13, y + h - 102], fill=INK)
        dr.rectangle([px - 16, y + h - 102, px + 16, y + h - 66], fill=INK)
    # NO DEAL stamp
    bw, bh = 430, 118
    bx, by = x + w - bw - 36, y + 34
    dr.rectangle([bx, by, bx + bw, by + bh], outline=RED, width=10)
    t = "NO DEAL"; fnt = sansB(74)
    dr.text((bx + bw // 2 - tw(fnt, t) // 2, by + bh // 2 - 40), t, font=fnt, fill=RED)

def ill_sparta(x, y, w, h):
    art_box(x, y, w, h, (190, 206, 220))
    sea = y + int(h * 0.62)
    dr.rectangle([x, sea, x + w, y + h], fill=(86, 128, 160))
    waves(x + 16, sea + 14, w - 32, 3, (220, 232, 240))
    # cargo ship, listing
    sx, sy, sw = x + int(w * 0.16), sea - int(h * 0.30), int(w * 0.6)
    dr.polygon([(sx, sy + 90), (sx + sw, sy + 74), (sx + sw - 50, sy + 150), (sx + 40, sy + 158)], fill=(60, 60, 66))
    for i, c in enumerate([(164, 60, 44), (44, 90, 140), (176, 132, 44), (70, 120, 84)]):
        dr.rectangle([sx + 60 + i * 92, sy + 18, sx + 140 + i * 92, sy + 88], fill=c, outline=INK, width=3)
    dr.rectangle([sx + sw - 130, sy - 44, sx + sw - 40, sy + 20], fill=(90, 90, 96), outline=INK, width=3)
    # flames + smoke
    for fx in (sx + 120, sx + 220):
        dr.polygon([(fx, sy + 20), (fx + 26, sy - 52), (fx + 52, sy + 20)], fill=(226, 110, 40))
        dr.polygon([(fx + 12, sy + 20), (fx + 26, sy - 24), (fx + 40, sy + 20)], fill=(240, 180, 60))
    smoke(sx + 200, sy - 60, 46)
    # tug with water arcs
    tx = x + int(w * 0.8)
    dr.polygon([(tx, sea - 16), (tx + 130, sea - 16), (tx + 104, sea + 26), (tx + 22, sea + 26)], fill=INK)
    dr.rectangle([tx + 44, sea - 52, tx + 84, sea - 16], fill=INK)
    for k in range(3):
        dr.arc([tx - 320 + k * 26, sea - 250 - k * 8, tx + 60, sea + 30], 300, 360, fill=(235, 244, 250), width=6)
    drone_sil(x + int(w * 0.3), y + 52, 30)

def ill_benghazi(x, y, w, h):
    art_box(x, y, w, h, (186, 200, 214))
    sea = y + int(h * 0.58)
    dr.rectangle([x, sea, x + w, y + h], fill=(74, 112, 148))
    waves(x + 16, sea + 16, w - 32, 3, (215, 228, 238))
    dr.rectangle([x, sea - 8, x + w, sea + 8], fill=(120, 104, 84))  # quay
    # capsized corvette: hull up, bow out of water
    hx, hy = x + int(w * 0.2), sea - 6
    dr.polygon([(hx, hy), (hx + int(w * 0.52), hy - 14), (hx + int(w * 0.52), hy - 96), (hx + 60, hy - 78)], fill=(52, 56, 64))
    dr.polygon([(hx + int(w * 0.52), hy - 14), (hx + int(w * 0.66), hy - 120), (hx + int(w * 0.52), hy - 96)], fill=(70, 74, 82))
    dr.rectangle([hx + 90, hy - 128, hx + 210, hy - 92], fill=(44, 48, 56))
    for fx in (hx + 120, hx + 185):
        dr.polygon([(fx, hy - 92), (fx + 26, hy - 168), (fx + 54, hy - 92)], fill=(226, 110, 40))
        dr.polygon([(fx + 14, hy - 92), (fx + 27, hy - 132), (fx + 40, hy - 92)], fill=(244, 178, 60))
    smoke(hx + 200, hy - 168, 48, n=7)
    drone_sil(x + int(w * 0.72), y + 56, 30)
    drone_sil(x + int(w * 0.84), y + 92, 22)

def ill_dymer(x, y, w, h):
    art_box(x, y, w, h, (206, 204, 196))
    gy = y + h - 60
    dr.rectangle([x, gy, x + w, y + h], fill=(140, 128, 108))
    bx, bw_, bh_ = x + int(w * 0.18), int(w * 0.52), int(h * 0.66)
    by = gy - bh_
    dr.rectangle([bx, by, bx + bw_, gy], fill=(168, 158, 142), outline=INK, width=4)
    for r_ in range(5):
        for c_ in range(6):
            wx = bx + 22 + c_ * (bw_ - 44) // 6; wy = by + 20 + r_ * (bh_ - 40) // 5
            dr.rectangle([wx, wy, wx + 30, wy + 34], fill=(240, 214, 130) if (r_ + c_) % 3 else (90, 96, 104))
    # collapsed bite
    dr.polygon([(bx + bw_ - 190, by), (bx + bw_, by + 90), (bx + bw_, gy), (bx + bw_ - 120, gy),
                (bx + bw_ - 150, by + int(bh_ * 0.55)), (bx + bw_ - 120, by + int(bh_ * 0.3))], fill=PAPER)
    dr.polygon([(bx + bw_ - 190, by), (bx + bw_, by + 90), (bx + bw_, gy), (bx + bw_ - 120, gy),
                (bx + bw_ - 150, by + int(bh_ * 0.55)), (bx + bw_ - 120, by + int(bh_ * 0.3))], outline=INK, width=4)
    for i in range(7):
        rx = bx + bw_ - 170 + (i * 53) % 150; ry = gy - 18 - (i * 37) % 90
        dr.rectangle([rx, ry, rx + 34, ry + 20], fill=(120, 112, 98), outline=INK, width=2)
    smoke(bx + bw_ - 90, by + 40, 30, n=5)
    # rescue crane + light
    cxp = x + int(w * 0.82)
    dr.line([(cxp, gy), (cxp, by - 30)], fill=INK, width=8)
    dr.line([(cxp, by - 30), (bx + bw_ - 90, by + 6)], fill=INK, width=4)
    sun_disc(cxp + 6, by - 44, 16, (250, 226, 130))

def ill_banten(x, y, w, h):
    art_box(x, y, w, h, (214, 196, 178))
    gy = y + h - int(h * 0.16)
    dr.rectangle([x, gy, x + w, y + h], fill=(120, 104, 88))
    fx, fw, fh = x + int(w * 0.08), int(w * 0.58), int(h * 0.4)
    fy = gy - fh
    roof = fy - int(h * 0.13)
    dr.rectangle([fx, fy, fx + fw, gy], fill=(150, 138, 122), outline=INK, width=4)
    dr.polygon([(fx - 10, fy), (fx + fw // 2, roof), (fx + fw + 10, fy)], fill=(96, 88, 80))
    for i in range(6):
        wx = fx + 18 + i * (fw - 36) // 6
        dr.rectangle([wx, fy + int(fh * 0.3), wx + 22, fy + int(fh * 0.72)], fill=(96, 100, 108))
    # flames along the roofline (kept inside the tile)
    for i, fx2 in enumerate(range(fx + 16, fx + fw - 30, max(30, fw // 6))):
        base = fy - int(h * 0.05) - (i % 2) * int(h * 0.06)
        hh = int(h * (0.16 + 0.05 * (i % 3)))
        dr.polygon([(fx2, base), (fx2 + 13, base - hh), (fx2 + 26, base)], fill=(222, 96, 32))
        dr.polygon([(fx2 + 7, base), (fx2 + 13, base - hh // 2), (fx2 + 19, base)], fill=(244, 178, 60))
    smoke(fx + fw // 2, roof - int(h * 0.1), max(18, int(h * 0.11)), n=5, col=(58, 54, 50))
    # fire truck
    tx = x + int(w * 0.7); tw_ = int(w * 0.27)
    dr.rectangle([tx, gy - int(h * 0.24), tx + tw_, gy - int(h * 0.05)], fill=(178, 44, 36))
    dr.rectangle([tx + int(tw_ * 0.68), gy - int(h * 0.34), tx + tw_, gy - int(h * 0.24)], fill=(150, 36, 30))
    for wx in (tx + int(tw_ * 0.22), tx + int(tw_ * 0.78)):
        r_ = max(6, int(h * 0.055))
        dr.ellipse([wx - r_, gy - int(h * 0.1), wx + r_, gy - int(h * 0.1) + 2 * r_], fill=INK)
    dr.line([(tx + 6, gy - int(h * 0.34)), (fx + fw - 24, roof + 4)], fill=(235, 240, 244), width=5)

def ill_hormuz(x, y, w, h):
    art_box(x, y, w, h, (172, 196, 208))
    # stylised strait: two land masses, channel between
    dr.polygon([(x, y), (x + int(w * 0.52), y), (x + int(w * 0.34), y + int(h * 0.52)),
                (x + int(w * 0.4), y + h), (x, y + h)], fill=SAND, outline=INK, width=3)
    dr.polygon([(x + w, y + int(h * 0.3)), (x + w, y + h), (x + int(w * 0.62), y + h),
                (x + int(w * 0.56), y + int(h * 0.55))], fill=SAND, outline=INK, width=3)
    t = "STRAIT OF HORMUZ"; fnt = sansCB(26)
    dr.text((x + w // 2 - tw(fnt, t) // 2, y + h - 44), t, font=fnt, fill=NAVY)
    # tanker in channel
    tx, ty = x + int(w * 0.42), y + int(h * 0.6)
    dr.polygon([(tx, ty), (tx + 150, ty), (tx + 128, ty + 30), (tx + 20, ty + 30)], fill=(52, 56, 62))
    dr.rectangle([tx + 26, ty - 20, tx + 118, ty], fill=(164, 60, 44))
    # radar arcs + drone
    drone_sil(x + int(w * 0.66), y + 66, 34)
    for r_ in (44, 74, 104):
        dr.arc([x + int(w * 0.66) - r_, y + 66 - r_ // 2, x + int(w * 0.66) + r_, y + 66 + r_ // 2], 200, 330, fill=RED, width=4)
    dr.polygon([(x + int(w * 0.66), y + 66), (x + int(w * 0.86), y + int(h * 0.42)),
                (x + int(w * 0.6), y + int(h * 0.42))], fill=(164, 32, 28, 60))

def ill_gaza(x, y, w, h):
    art_box(x, y, w, h, (216, 200, 176))
    sun_disc(x + int(w * 0.8), y + 62, 34)
    gy = y + h - 50
    dr.rectangle([x, gy, x + w, y + h], fill=(150, 134, 108))
    rnd = random.Random(7)
    bx = x + 20
    while bx < x + w - 90:
        bw_ = rnd.randint(56, 104); bh_ = rnd.randint(90, 200)
        col = (168, 156, 138) if rnd.random() > 0.3 else (128, 118, 102)
        dr.rectangle([bx, gy - bh_, bx + bw_, gy], fill=col, outline=INK, width=3)
        for wy in range(gy - bh_ + 14, gy - 24, 34):
            for wx in range(bx + 10, bx + bw_ - 18, 26):
                if rnd.random() > 0.45:
                    dr.rectangle([wx, wy, wx + 13, wy + 16], fill=(84, 88, 94))
        bx += bw_ + 10
    smoke(x + int(w * 0.3), y + int(h * 0.34), 40, n=6)
    smoke(x + int(w * 0.62), y + int(h * 0.42), 30, n=5)
    # tents foreground
    for i, tx in enumerate(range(x + 40, x + w - 120, 170)):
        ty = gy - 6
        dr.polygon([(tx, ty), (tx + 62, ty - 62), (tx + 124, ty)], fill=(232, 226, 210), outline=INK, width=3)
        dr.polygon([(tx + 62, ty - 62), (tx + 62, ty), (tx + 40, ty)], fill=(206, 198, 178))

def ill_sinaloa(x, y, w, h):
    art_box(x, y, w, h, (222, 204, 168))
    sun_disc(x + int(w * 0.16), y + 56, 30)
    # mountains
    dr.polygon([(x, y + int(h * 0.62)), (x + int(w * 0.3), y + int(h * 0.3)), (x + int(w * 0.52), y + int(h * 0.62))], fill=(168, 138, 100))
    dr.polygon([(x + int(w * 0.4), y + int(h * 0.62)), (x + int(w * 0.68), y + int(h * 0.26)), (x + w, y + int(h * 0.62))], fill=(150, 122, 88))
    gy = y + int(h * 0.62)
    dr.rectangle([x, gy, x + w, y + h], fill=(196, 168, 120))
    # road
    dr.polygon([(x + int(w * 0.34), y + h), (x + int(w * 0.52), gy), (x + int(w * 0.6), gy), (x + int(w * 0.86), y + h)], fill=(96, 92, 86))
    # helicopter
    hx, hy = x + int(w * 0.68), y + 66
    dr.ellipse([hx - 62, hy - 20, hx + 62, hy + 22], fill=INK)
    dr.polygon([(hx + 56, hy - 4), (hx + 138, hy - 18), (hx + 138, hy + 2), (hx + 56, hy + 8)], fill=INK)
    dr.line([(hx - 84, hy - 30), (hx + 84, hy - 30)], fill=INK, width=7)
    dr.line([(hx + 138, hy - 26), (hx + 138, hy - 2)], fill=INK, width=6)
    # burning truck on road
    tx, ty = x + int(w * 0.47), y + int(h * 0.74)
    dr.rectangle([tx, ty, tx + 120, ty + 44], fill=(70, 70, 74))
    dr.rectangle([tx + 120, ty + 12, tx + 156, ty + 44], fill=(58, 58, 62))
    dr.polygon([(tx + 30, ty), (tx + 52, ty - 52), (tx + 74, ty)], fill=(222, 96, 32))
    smoke(tx + 60, ty - 56, 26, n=5)

def ill_khartoum(x, y, w, h):
    art_box(x, y, w, h, (214, 198, 172))
    gy = y + h - 52
    dr.rectangle([x, gy, x + w, y + h], fill=(158, 138, 104))
    rnd = random.Random(11)
    bx = x + 16
    while bx < x + w - 80:
        bw_ = rnd.randint(60, 110); bh_ = rnd.randint(80, 190)
        dr.rectangle([bx, gy - bh_, bx + bw_, gy], fill=(178, 160, 128), outline=INK, width=3)
        bx += bw_ + 12
    # UN building with flag (kept inside the box)
    ux, uw, uh = x + int(w * 0.38), int(w * 0.3), int(h * 0.52)
    pole = int(h * 0.14)
    dr.rectangle([ux, gy - uh, ux + uw, gy], fill=(226, 222, 210), outline=INK, width=4)
    for wy in range(gy - uh + 12, gy - 16, max(16, int(h * 0.11))):
        dr.rectangle([ux + 12, wy, ux + uw - 12, wy + 9], fill=(110, 140, 170))
    dr.line([(ux + uw // 2, gy - uh), (ux + uw // 2, gy - uh - pole)], fill=INK, width=4)
    dr.rectangle([ux + uw // 2, gy - uh - pole, ux + uw // 2 + int(uw * 0.42), gy - uh - pole + int(h * 0.1)], fill=(110, 168, 214))
    t = "UN"; fnt = sansB(max(13, int(h * 0.07)))
    dr.text((ux + uw // 2 + int(uw * 0.21) - tw(fnt, t) // 2, gy - uh - pole + 1), t, font=fnt, fill=(255, 255, 255))
    drone_sil(x + int(w * 0.2), y + 54, 30)
    drone_sil(x + int(w * 0.82), y + 84, 24)
    # explosion star
    ex, ey = x + int(w * 0.72), gy - 130
    for a in range(0, 360, 45):
        r1 = 34 if a % 90 == 0 else 20
        dr.line([(ex, ey), (ex + r1 * math.cos(math.radians(a)), ey + r1 * math.sin(math.radians(a)))], fill=RED, width=6)
    dr.ellipse([ex - 12, ey - 12, ex + 12, ey + 12], fill=(240, 170, 60))

def ill_washington(x, y, w, h):
    art_box(x, y, w, h, (196, 212, 226))
    gy = y + h - 64
    dr.rectangle([x, gy, x + w, y + h], fill=(120, 128, 138))
    for i in range(9):
        dr.line([(x + 30 + i * (w - 60) // 8, gy + 26), (x + 74 + i * (w - 60) // 8, gy + 26)], fill=(240, 240, 235), width=6)
    # terminal
    dr.rectangle([x + 30, gy - 108, x + int(w * 0.52), gy], fill=(150, 160, 172), outline=INK, width=3)
    for wx in range(x + 48, x + int(w * 0.52) - 30, 40):
        dr.rectangle([wx, gy - 88, wx + 24, gy - 30], fill=(110, 150, 190))
    dr.rectangle([x + int(w * 0.56), gy - 190, x + int(w * 0.62), gy], fill=(140, 148, 160), outline=INK, width=3)
    # plane taking off
    px, py = x + int(w * 0.6), y + max(86, int(h * 0.34))
    dr.polygon([(px, py), (px + 190, py - 26), (px + 226, py - 12), (px + 60, py + 22)], fill=(238, 240, 244), outline=INK, width=3)
    dr.polygon([(px + 168, py - 24), (px + 196, py - 74), (px + 224, py - 70), (px + 210, py - 14)], fill=RED)
    dr.polygon([(px + 40, py + 8), (px + 96, py + 52), (px + 122, py + 48), (px + 84, py + 4)], fill=(200, 208, 218), outline=INK, width=2)
    for i in range(6):
        dr.ellipse([px + 66 + i * 24, py - 6, px + 78 + i * 24, py + 4], fill=NAVY)
    # shield badge
    sx, sy = x + w - 120, y + 26
    dr.polygon([(sx, sy), (sx + 76, sy), (sx + 76, sy + 60), (sx + 38, sy + 96), (sx, sy + 60)], fill=GOLD, outline=INK, width=3)
    t = "!"; fnt = sansB(52)
    dr.text((sx + 38 - tw(fnt, t) // 2, sy + 14), t, font=fnt, fill=INK)

def ill_newdelhi(x, y, w, h):
    art_box(x, y, w, h, (208, 216, 208))
    gy = y + h - int(h * 0.14)
    dr.rectangle([x, gy, x + w, y + h], fill=(150, 146, 128))
    # parliament: dome + colonnade, all proportions relative to h
    cx = x + w // 2
    bw_ = int(w * 0.52); bh_ = int(h * 0.34); drad = int(h * 0.17)
    dr.rectangle([cx - bw_ // 2, gy - bh_, cx + bw_ // 2, gy], fill=(196, 178, 148), outline=INK, width=3)
    for i in range(7):
        px = cx - bw_ // 2 + 12 + i * (bw_ - 24) // 7
        dr.rectangle([px, gy - bh_ + 8, px + 9, gy - 8], fill=(226, 212, 182))
    dr.pieslice([cx - drad, gy - bh_ - 2 * drad + 6, cx + drad, gy - bh_ + 6], 180, 360, fill=(178, 96, 60), outline=INK, width=3)
    dr.rectangle([cx - 3, gy - bh_ - 2 * drad - 8, cx + 3, gy - bh_ - 2 * drad + 4], fill=INK)
    # two flags
    fh_ = int(h * 0.52); fw_ = max(34, int(w * 0.13))
    for fx, cols in [(x + int(w * 0.1), [(240, 140, 50), (240, 240, 240), (60, 140, 70)]),
                     (x + w - int(w * 0.1) - fw_, [(60, 90, 170), (240, 240, 240), (200, 40, 50)])]:
        dr.line([(fx, gy), (fx, gy - fh_)], fill=INK, width=4)
        for i, c in enumerate(cols):
            dr.rectangle([fx, gy - fh_ + i * 13, fx + fw_, gy - fh_ + (i + 1) * 13], fill=c)

def ill_markets(x, y, w, h):
    art_box(x, y, w, h, (232, 226, 206))
    # chart axes
    ax, ay = x + 50, y + h - 60
    dr.line([(ax, y + 30), (ax, ay)], fill=INK, width=4)
    dr.line([(ax, ay), (x + w - 30, ay)], fill=INK, width=4)
    hh = h - 100
    pts = [(ax + 10, ay - int(hh * 0.12)), (ax + 90, ay - int(hh * 0.3)), (ax + 170, ay - int(hh * 0.22)),
           (ax + 250, ay - int(hh * 0.48)), (ax + 330, ay - int(hh * 0.66)), (ax + 400, ay - int(hh * 0.92))]
    pts = [(px, max(py, y + 16)) for px, py in pts if px < x + w - 60]
    dr.line(pts, fill=RED, width=7)
    lx, ly = pts[-1]
    dr.polygon([(lx, ly), (lx - 26, ly + 4), (lx - 8, ly + 26)], fill=RED)
    # gold bars
    for i, (bx, by) in enumerate([(x + 60, y + h - 130), (x + 150, y + h - 130), (x + 105, y + h - 168)]):
        dr.polygon([(bx, by), (bx + 22, by - 16), (bx + 96, by - 16), (bx + 74, by)], fill=(226, 182, 74), outline=INK, width=3)
        dr.polygon([(bx + 22, by - 16), (bx + 96, by - 16), (bx + 84, by - 30), (bx + 34, by - 30)], fill=(240, 204, 96), outline=INK, width=3)
    t = "GOLD +2%"; fnt = sansB(40)
    dr.text((x + w - tw(fnt, t) - 36, y + 30), t, font=fnt, fill=(146, 106, 20))

def ill_turin(x, y, w, h):
    art_box(x, y, w, h, (120, 158, 108))
    # court lines
    dr.rectangle([x + 40, y + 40, x + w - 40, y + h - 40], outline=(240, 240, 235), width=5)
    dr.line([(x + w // 2, y + 40), (x + w // 2, y + h - 40)], fill=(240, 240, 235), width=5)
    dr.line([(x + 40, y + h // 2), (x + w - 40, y + h // 2)], fill=(240, 240, 235), width=4)
    # player silhouette (scaled to box height)
    s = h / 300.0
    cx, cy = x + int(w * 0.38), y + int(h * 0.62)
    def P(dx, dy): return (cx + int(dx * s), cy + int(dy * s))
    hx, hy2 = P(0, -108); hr = max(7, int(17 * s))
    dr.ellipse([hx - hr, hy2 - hr, hx + hr, hy2 + hr], fill=INK)                       # head
    dr.line([P(0, -88), P(-14, -8)], fill=INK, width=max(5, int(15 * s)))              # torso
    dr.line([P(-14, -8), P(-58, 82)], fill=INK, width=max(5, int(13 * s)))             # leg back
    dr.line([P(-14, -8), P(44, 70)], fill=INK, width=max(5, int(13 * s)))              # leg fwd
    dr.line([P(-6, -68), P(66, -104)], fill=INK, width=max(5, int(12 * s)))            # arm up
    dr.line([P(-6, -68), P(-66, -30)], fill=INK, width=max(5, int(12 * s)))            # arm back
    rx, ry = P(96, -136)
    rw_, rh_ = max(12, int(34 * s)), max(16, int(44 * s))
    dr.ellipse([rx - rw_, ry - rh_, rx + rw_, ry + rh_], outline=INK, width=max(3, int(7 * s)))  # racket
    dr.line([(rx - 6, ry + rh_ - 4), P(66, -104)], fill=INK, width=max(4, int(9 * s)))
    # ball + arc
    dr.ellipse([x + w - 130, y + 56, x + w - 102, y + 84], fill=(214, 232, 84), outline=INK, width=3)
    dr.arc([x + w - 330, y + 30, x + w - 60, y + 190], 90, 200, fill=(240, 240, 235), width=4)

ILL = {
 "cop31": ill_cop31, "sparta": ill_sparta, "benghazi": ill_benghazi, "dymer": ill_dymer,
 "banten": ill_banten, "hormuz": ill_hormuz, "gaza": ill_gaza, "sinaloa": ill_sinaloa,
 "khartoum": ill_khartoum, "washington": ill_washington, "newdelhi": ill_newdelhi,
 "markets": ill_markets, "turin": ill_turin,
}

REF_W, REF_H = 1100, 380          # illustration reference canvas
FOCAL = {"cop31": 0.25, "hormuz": 0.95}   # vertical crop focus (0 = top, 0.5 = centre)

def draw_ill(key, x, y, w, h):
    """Render an illustration into its tile: drawn once on the reference
    canvas, then scaled to COVER the tile and centre/focal-cropped, so the
    artwork is never distorted and can never escape its box."""
    global dr, FONT_SCALE
    tile = Image.new("RGB", (REF_W, REF_H), PAPER)
    old_dr, old_fs = dr, FONT_SCALE
    dr = ImageDraw.Draw(tile, "RGBA"); FONT_SCALE = 1
    ILL[key](0, 0, REF_W, REF_H)
    dr, FONT_SCALE = old_dr, old_fs
    tw_px, th_px = max(2, int(w * S)), max(2, int(h * S))
    scale = max(tw_px / REF_W, th_px / REF_H)
    nw, nh = max(tw_px, round(REF_W * scale)), max(th_px, round(REF_H * scale))
    tile = tile.resize((nw, nh), Image.LANCZOS)
    ox = (nw - tw_px) // 2
    oy = int((nh - th_px) * FOCAL.get(key, 0.5))
    tile = tile.crop((ox, oy, ox + tw_px, oy + th_px))
    img.paste(tile, (int(x * S), int(y * S)))

# ---------------------------------------------------------------- layout
MX = 22                      # margin (design units)
CW = W - 2 * MX              # content width = 980
y = 0

def rect(x0, y0, x1, y1, **kw):
    dr.rectangle([x0 * S, y0 * S, x1 * S, y1 * S], **kw)

# ---- top info line
rule(MX, W - MX, 7, 1.2); rule(MX, W - MX, 10.5, 2.5)
fnt = sansB(8.5)
text_top(MX, 14, "EST. 2017 · THE WORLD, ON ONE PAGE", fnt, INK_SOFT)
text_top(W // 2, 14, "ONE IMAGE · EVERY STORY CHECKED", fnt, INK_SOFT, align="center")
text_top(W - MX, 14, "No. 327 · LATE EDITION", fnt, INK_SOFT, align="right")

# ---- masthead
mf = mast(46)
mb = dr.textbbox((0, 0), "THE MONDAY GLOBE", font=mf)
mast_h = (mb[3] - mb[1]) / S
text_top(W // 2, 26, "THE MONDAY GLOBE", mf, INK, align="center")
y = 26 + mast_h + 4
rule(MX, W - MX, y, 1.5); y += 4

# ---- dateline row: one clean line, left / centre / right
dl_f = sansCB(10)
dl_left, dl_mid, dl_right = "MONDAY, 23 NOVEMBER 2026", "33 STORIES · 7 REGIONS · 13 ILLUSTRATED", "COMPILED 12:00 WIB"
wl, wm, wr = twd(dl_f, dl_left), twd(dl_f, dl_mid), twd(dl_f, dl_right)
assert MX + wl + 12 < W / 2 - wm / 2 and W / 2 + wm / 2 + 12 < W - MX - wr, "dateline overlap"
text_top(MX, y, dl_left, dl_f, INK)
text_top(W // 2, y, dl_mid, dl_f, RED, align="center")
text_top(W - MX, y, dl_right, dl_f, INK, align="right")
y += 13
rule(MX, W - MX, y, 3); y += 6

# ---- stat band: height COMPUTED from measured text so the captions always
# ---- sit fully inside the band with padding above and below.
num_f, cap_f, cap_lh = serifB(21), sansCB(8), 9.5
num_h = 0
for num, _lab in STATS:
    b = dr.textbbox((0, 0), num, font=num_f); num_h = max(num_h, (b[3] - b[1]) / S)
band_h = 4 + num_h + 2 + 2 * cap_lh + 4
band_y = y
rect(MX, band_y, W - MX, band_y + band_h, fill=PAPER_D)
rule(MX, W - MX, band_y, 1.2); rule(MX, W - MX, band_y + band_h, 1.2)
cell = CW / 5
for i, (num, lab) in enumerate(STATS):
    cx = MX + i * cell
    if i: dr.line([((cx) * S, (band_y + 7) * S), ((cx) * S, (band_y + band_h - 7) * S)], fill=INK_SOFT, width=1 * S)
    b = dr.textbbox((0, 0), num, font=num_f)
    dr.text(((cx + cell / 2) * S - (b[0] + b[2]) / 2, (band_y + 4) * S - b[1]), num,
            font=num_f, fill=RED if i in (0, 1, 2) else INK)
    cap_top = band_y + 4 + num_h + 2
    for j, ln in enumerate(lab.split("\n")):
        text_top(cx + cell / 2, cap_top + j * cap_lh, ln, cap_f, INK_SOFT, align="center")
y = band_y + band_h + 6

# ---- region chips
counts = {}
for it in HEROES + CARDS: counts[it[3]] = counts.get(it[3], 0) + 1
for it in BRIEFS: counts[it[2]] = counts.get(it[2], 0) + 1
chip_y = y
cx = MX
dr.text((cx * S, (chip_y + 1) * S), "IN THIS EDITION:", font=sansB(9), fill=INK)
cx += twd(sansB(9), "IN THIS EDITION:") + 10
for reg in ["EUROPE", "MIDDLE EAST", "AMERICAS", "ASIA", "AFRICA", "OCEANIA", "WORLD"]:
    cx = chip(cx, chip_y, f"{reg} {counts[reg]}", REGION_COLORS[reg], size=8.5)
text_top(W - MX, chip_y + 1, "STORY OF THE DAY: COP31", sansB(9), RED, align="right")
y = chip_y + 17
rule(MX, W - MX, y, 1.5); y += 7
print("after header: y =", round(y, 1))

# ---- heroes
SQ_HEROES = [(k, p, t, r, h, SQ_HERO_BODY[k]) for (k, p, t, r, h, _b) in HEROES]
LEFT_W = 540; RIGHT_X = MX + LEFT_W + 32; RIGHT_W = W - MX - RIGHT_X
hero_top = y

def hero_block(x, yy, w, item, art_h, kick_size, head_f, head_lead, body_f, body_lead, story_no):
    draw_ill(item[0], x, yy, w, art_h)
    rect(x, yy, x + w, yy + art_h, outline=INK, width=int(1.2 * S))
    y2 = kicker(x, yy + art_h + 5, item[1], item[2] + f"  ·  STORY {story_no}", size=kick_size)
    y2 = text_block(x, y2, item[4], head_f, w, head_lead)
    y2 += 2
    y2 = text_block(x, y2, item[5], body_f, w, body_lead)
    return y2

h0 = SQ_HEROES[0]
left_end = hero_block(MX, hero_top, LEFT_W, h0, 114, 9.5, serifB(17), 1.12, serif(9), 1.28, 1)
dr.text((MX * S, (left_end + 3) * S), "— Reporting by AP, Reuters, Le Monde and CNN",
        font=sans(8), fill=INK_SOFT)
left_end += 14

# map panel under the lead hero (left column)
MAP_H = 78
my = left_end + 4
rect(MX, my, MX + LEFT_W, my + MAP_H, fill=(214, 224, 222), outline=INK, width=int(1.2 * S))
text_top(MX + 10, my + 6, "WHERE IT HAPPENED", sansB(9.5), INK)
text_top(MX + LEFT_W - 10, my + 6, "STYLIZED MAP — NOT TO SCALE", sansCB(7), INK_SOFT, align="right")
map_y0, map_hh = my + 18, MAP_H - 22
def blob(pts, col=(168, 178, 158)):
    dr.polygon([( (MX + px * LEFT_W) * S, (map_y0 + py * map_hh) * S) for px, py in pts],
               fill=col, outline=INK, width=1 * S)
blob([(.06, .18), (.2, .08), (.3, .16), (.26, .34), (.17, .42), (.08, .32)])                    # N America
blob([(.2, .46), (.3, .44), (.33, .62), (.27, .82), (.21, .66)])                                # S America
blob([(.44, .14), (.56, .1), (.58, .24), (.5, .3), (.44, .24)])                                 # Europe
blob([(.46, .34), (.58, .32), (.62, .52), (.55, .78), (.47, .6)])                               # Africa
blob([(.58, .12), (.82, .08), (.92, .2), (.86, .34), (.68, .36), (.6, .26)])                    # Asia
blob([(.8, .52), (.92, .5), (.94, .66), (.83, .68)])                                            # Oceania
PINS = [("1", .49, .16), ("2", .56, .06), ("3", .56, .52), ("4", .535, .3), ("5", .79, .42),
        ("6", .645, .22), ("7", .615, .48), ("8", .13, .3), ("9", .575, .78), ("10", .1, .24),
        ("11", .76, .34), ("12", .5, .62), ("13", .455, .34)]
for n, px, py in PINS:
    cxp, cyp = MX + px * LEFT_W, map_y0 + py * map_hh
    r_ = 5.8
    dr.ellipse([(cxp - r_) * S, (cyp - r_) * S, (cxp + r_) * S, (cyp + r_) * S],
               fill=RED, outline=(255, 255, 255), width=1 * S)
    text_top(cxp, cyp - 3.2, n, sansB(6.5), (255, 255, 255), align="center")
left_end = my + MAP_H

right_end = hero_top
for k, hh_ in enumerate(SQ_HEROES[1:]):
    if k == 1: rule(RIGHT_X, W - MX, right_end + 3, 1, INK_SOFT); right_end += 8
    right_end = hero_block(RIGHT_X, right_end, RIGHT_W, hh_, 84, 9, serifB(13.5), 1.12,
                           serif(8.5), 1.24, k + 2)
y = max(left_end, right_end) + 6
print("after heroes: y =", round(y, 1), "(left", round(left_end, 1), "/ right", round(right_end, 1), ")")

# ---- DATE CHECK strip (2 x 2 paragraphs, height measured before drawing)
DC_PARAS = [
  "Every story verified against reporting dated 21–23 Nov 2026, opened and read before inclusion.",
  "IN: weekend stories still leading Monday — Sparta II (Sat), Benghazi & Banten (Sat–Mon), Dymer (Sun–Mon).",
  "CORRECTED: early claims of six dead at Benghazi. Reuters & Al Jazeera confirm no fatalities; 10 injured.",
  "OUT: Thu/Fri items with no Monday life, and one unverified $3.8bn game-sales claim, held for confirmation.",
]
dc_f, dc_lead = serif(8), 1.2
dc_colw = (CW - 32 - 18) / 2
dc_rows = []
for r_ in range(2):
    hts = [len(wrap(DC_PARAS[r_ * 2 + c], dc_f, dc_colw)) * dc_f.size / S * dc_lead for c in range(2)]
    dc_rows.append(max(hts))
dc_h = 6 + 14 + 3 + dc_rows[0] + 3 + dc_rows[1] + 6
rect(MX, y, W - MX, y + dc_h, fill=PAPER_D, outline=INK, width=int(1.2 * S))
text_top(MX + 16, y + 6, "DATE CHECK", sansB(10.5), INK)
yy = y + 6 + 14 + 3
for r_ in range(2):
    for c in range(2):
        text_block(MX + 16 + c * (dc_colw + 18), yy, DC_PARAS[r_ * 2 + c], dc_f, dc_colw, dc_lead)
    yy += dc_rows[r_] + 3
y += dc_h + 6
print("after date check: y =", round(y, 1))

# ---- pictures band + cards grid
def band(yy, title, right_note):
    rect(MX, yy, W - MX, yy + 15, fill=INK)
    text_top(W // 2, yy + 2.5, title, sansB(9.5), PAPER, align="center")
    text_top(W - MX - 8, yy + 3.5, right_note, sansCB(8), (200, 200, 200), align="right")
    return yy + 15

y = band(y, "AROUND THE WORLD — IN PICTURES", "STORIES 4–13") + 5
SQ_CARDS = [(k, p, t, r, h, SQ_CARD_BODY[k]) for (k, p, t, r, h, _b) in CARDS]
GAP = 9; CARD_W = (CW - 4 * GAP) / 5; CARD_ART = 32
card_head_f, card_body_f = serifB(10), serif(8)
def card_height(c):
    hh = len(wrap(c[4], card_head_f, CARD_W)) * card_head_f.size / S * 1.15
    bh = len(wrap(c[5], card_body_f, CARD_W)) * card_body_f.size / S * 1.25
    return CARD_ART + 3 + 10 + hh + 1 + bh
for r_ in range(2):
    row_cards = SQ_CARDS[r_ * 5:(r_ + 1) * 5]
    row_h = max(card_height(c) for c in row_cards)
    for col, c in enumerate(row_cards):
        x = MX + col * (CARD_W + GAP)
        if col: dr.line([((x - GAP / 2) * S, y * S), ((x - GAP / 2) * S, (y + row_h) * S)],
                        fill=(190, 182, 164), width=1 * S)
        draw_ill(c[0], x, y, CARD_W, CARD_ART)
        rect(x, y, x + CARD_W, y + CARD_ART, outline=INK, width=1 * S)
        y2 = kicker(x, y + CARD_ART + 3, c[1], c[2], size=8)
        y2 = text_block(x, y2, c[4], card_head_f, CARD_W, 1.15)
        y2 += 1
        text_block(x, y2, c[5], card_body_f, CARD_W, 1.25)
    y += row_h + 7
print("after cards: y =", round(y, 1))

# ---- briefs band + briefs (4 columns x 5 rows, rich inline text)
y = band(y, "ALSO ON MONDAY — THE WORLD IN BRIEF", "STORIES 14–33") + 5
SQ_BRIEFS = [(p, t, r, SQ_BRIEF_BODY[(p, t)]) for (p, t, r, _b) in BRIEFS]
B_GAP = 14; B_COLW = (CW - 3 * B_GAP) / 4; B_LH = 9.0; B_GAP_ROW = 3
def brief_segments(idx, b):
    return [(f"{idx + 14} ", serifB(11), RED),
            (f"{b[0]} · {b[1]} — ", sansB(7.5), INK),
            (b[3], serif(8), INK)]
brief_heights = [len(rich_lines(brief_segments(i, b), B_COLW)) * B_LH for i, b in enumerate(SQ_BRIEFS)]
for r_ in range(5):
    row_h = max(brief_heights[r_ * 4:(r_ + 1) * 4])
    for c in range(4):
        i = r_ * 4 + c
        draw_rich(MX + c * (B_COLW + B_GAP), y, brief_segments(i, SQ_BRIEFS[i]), B_COLW, B_LH)
    y += row_h + B_GAP_ROW
print("after briefs: y =", round(y, 1))

# ---- footer
rule(MX, W - MX, y + 2, 2.5); rule(MX, W - MX, y + 6, 1)
text_top(W // 2, y + 10, "THE MONDAY GLOBE · COMPILED FROM AP, REUTERS, THE GUARDIAN, AL JAZEERA, BBC, AFP AND AGENCY REPORTING",
         sansCB(8.5), INK, align="center")
text_top(W // 2, y + 21, "All artwork on this page was drawn procedurally for this edition. Full sources and verification notes: SOURCES.md · Story list: STORIES.md",
         sans(8), INK_SOFT, align="center")
print("final content bottom:", round(y + 32, 1), "of", H)

# ---- downscale to exactly 1024x1024 and save entry.png (<= 1 MiB)
small = img.resize((W, H), Image.LANCZOS)
entry_path = os.path.join(OUT, "entry.png")
small.save(entry_path, optimize=True)
size = os.path.getsize(entry_path)
if size > 1_048_576:
    small.quantize(colors=256, method=Image.Quantize.MEDIANCUT).save(entry_path, optimize=True)
    size = os.path.getsize(entry_path)
small.save(os.path.expanduser("~/workspace/makefun/news-image-20261123-v1-square.png"))
print("saved entry.png", small.size, size, "bytes")
