"""Generate a Czech, two-page PDF knowledge-base fixture for classic pizzas."""

from __future__ import annotations

import math
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "sample-data" / "pizza-pdfs"
FONT_DIR = Path("C:/Windows/Fonts")
pdfmetrics.registerFont(TTFont("Arial", str(FONT_DIR / "arial.ttf")))
pdfmetrics.registerFont(TTFont("Arial-Bold", str(FONT_DIR / "arialbd.ttf")))

W, H = A4
INK = colors.HexColor("#193347")
MUTED = colors.HexColor("#536b78")
RED = colors.HexColor("#bd4b36")
CREAM = colors.HexColor("#f8f2e7")
GREEN = colors.HexColor("#397d64")
PALETTE = ["#bb5141", "#e6a349", "#428c71", "#54758e", "#9175a4", "#c7b26a"]
BODY = ParagraphStyle("body", fontName="Arial", fontSize=9.5, leading=14.1, textColor=INK)
SMALL = ParagraphStyle("small", parent=BODY, fontSize=7.7, leading=10.5)
CAPTION = ParagraphStyle("caption", parent=SMALL, textColor=MUTED)
CENTER = ParagraphStyle("center", parent=SMALL, alignment=TA_CENTER)

ITALIA = "https://www.italia.it/en/campania/naples/things-to-do/pizza"
NAPLES = "https://www.italia.it/en/campania/naples/things-to-do/naples-world-pizza-capital"
TYPES = "https://www.italia.it/en/italy/things-to-do/types-of-pizza-italy"
AVPN = "https://www.pizzanapoletana.org/it/ricetta_pizza_napoletana"
FRITTA = "https://www.visitnaples.eu/napoletanita/sapori-di-napoli/la-pizza-fritta-napoletana-storia-e-tradizione-di-una-ricetta-tutta-napoletana"
ROMA = "https://turismoroma.it/es/15042013-la-pizza"

# Ingredient masses are an illustrative recipe for one pizza, not certified specifications.
# Dough is shown separately; the chart compares topping ingredients only.
PIZZAS = [
    dict(slug="01-margherita", name="Margherita", place="Neapol, Kampánie",
         story="Vyprávění o královně Markétě Savojské a pizzaři Raffaelu Espositovi zasadilo Margheritu do Neapole roku 1889. Podle známé legendy připomíná rajče, mozzarella a bazalka italskou trikolóru. Samotná kombinace však pravděpodobně existovala i dříve: příběh o jejím jediném vynálezci proto není jistý historický doklad.",
         character="Měkký střed, výrazná rajčatová kyselina a jemné mléčné tóny. AVPN vyhrazuje označení pravé neapolské pizzy jen Margheritě a Marinaře při dodržení dalších pravidel.",
         ingredients=[("Rajčata", 75), ("Mozzarella", 90), ("Tvrdý sýr", 6), ("Olivový olej", 7), ("Bazalka", 3)],
         allergens="1 (lepek), 7 (mléko)", wine="Lehké červené: mladé Gragnano nebo svěží Barbera; kyselina podpoří rajčata.",
         note="Párování je redakční doporučení, nikoli historicky doložená tradice.", sources=[NAPLES, AVPN]),
    dict(slug="02-marinara", name="Marinara", place="Neapol, Kampánie",
         story="Marinara patří k nejprostším neapolským pizzám. Jméno evokuje námořníky, ale samo o sobě neznamená mořské plody. Základ tvoří rajče, česnek, oregano a olivový olej; podle AVPN jde spolu s Margheritou o jeden ze dvou uznaných typů pravé neapolské pizzy.",
         character="Bez sýra v této ukázkové receptuře: vyniká rajče, sušené oregano a česnek. Přívlastek veganská platí jen při potvrzení všech použitých surovin a provozních postupů.",
         ingredients=[("Rajčata", 90), ("Česnek", 3), ("Oregano", 1), ("Olivový olej", 7)],
         allergens="1 (lepek)", wine="Suché bílé Falanghina: svěžest vyvažuje aromatický česnek.",
         note="Název pizzy není důkazem přítomnosti ryb ani mořských plodů.", sources=[AVPN, ITALIA]),
    dict(slug="03-napoli", name="Napoli (s ančovičkami)", place="Neapolský styl, Itálie",
         story="Pizza Napoli s ančovičkami je známá italská restaurační varianta rajčatového základu. Názvy a přesná skladba se mezi podniky mění; nejde o třetí druh schválený disciplinářem AVPN. Slanost ryb a kaparů vychází z kulinární tradice Středomoří, nikoli z doloženého jediného vynálezce.",
         character="Výrazná slaná chuť ančoviček; rajčata ji odlehčují. V této verzi je i mozzarella, ale jinde může chybět.",
         ingredients=[("Rajčata", 80), ("Mozzarella", 70), ("Ančovičky", 22), ("Kapary", 12), ("Olivový olej", 7)],
         allergens="1 (lepek), 4 (ryby), 7 (mléko)", wine="Suché Vermentino: citrusová svěžest zvládne sůl ančoviček.",
         note="Ryby a mléko se vážou k této konkrétní ukázkové variantě.", sources=[ITALIA, AVPN]),
    dict(slug="04-quattro-formaggi", name="Quattro Formaggi", place="Italská pizzeriová tradice",
         story="Čtyři sýry představují celou rodinu italských pizzeriových kombinací, nikoli recept s jednoznačným datem vzniku. Italia.it uvádí mozzarellu, fontinu, gorgonzolu a provolu; jiní pizzaři používají jiné čtyři sýry. Proto název popisuje princip, ne zaručené složení v každém podniku.",
         character="Krémová textura, výraznější plísňový sýr a téměř žádná rajčatová kyselina; zde jde o bílou variantu.",
         ingredients=[("Mozzarella", 65), ("Fontina", 35), ("Gorgonzola", 30), ("Provola", 30), ("Olivový olej", 5)],
         allergens="1 (lepek), 7 (mléko)", wine="Suché šumivé Franciacorta: perlení pročistí chuť po sýrech.",
         note="Konkrétní typy sýrů se musí v provozu ověřit z receptury.", sources=[ITALIA]),
    dict(slug="05-capricciosa", name="Capricciosa", place="Italská pizzeriová tradice",
         story="Capricciosa je bohatě obložená italská klasika. Italia.it ji popisuje vedle Quattro Stagioni: obě staví na rajčeti, mozzarelle, houbách, artyčocích, šunce a olivách; u Capricciosy uvádí i vařené vejce. Jednotný příběh o konkrétním autorovi se z těchto zdrojů nedá doložit.",
         character="Slanost šunky a oliv střídá zemité houby a nakládané artyčoky. Ukázková verze obsahuje také vejce.",
         ingredients=[("Rajčata", 75), ("Mozzarella", 75), ("Šunka", 40), ("Houby", 35), ("Artyčoky", 30), ("Olivy", 18), ("Vejce", 45)],
         allergens="1 (lepek), 3 (vejce), 7 (mléko)", wine="Suché rosé z Itálie: drží krok s pestrým obložením.",
         note="Alergeny v šunce a nálevu artyčoků závisí na dodavateli.", sources=[ITALIA]),
    dict(slug="06-quattro-stagioni", name="Quattro Stagioni", place="Italská pizzeriová tradice",
         story="Čtyři roční období jsou pizzou členěnou na výseče s různými přísadami. Běžné jsou houby, artyčoky, šunka a olivy na rajčatovém a sýrovém základu. Italia.it ji staví vedle Capricciosy; rozdíl je zejména v rozložení oblohy. Symbolika období je kulinární vyprávění, ne striktní norma.",
         character="Každý díl chutná jinak: od jemných hub k výrazným olivám. Graf surovin shrnuje celou pizzu, nikoli poměr jednotlivých výsečí.",
         ingredients=[("Rajčata", 75), ("Mozzarella", 75), ("Houby", 35), ("Artyčoky", 30), ("Šunka", 40), ("Olivy", 18)],
         allergens="1 (lepek), 7 (mléko)", wine="Mladé Chianti: šťavnatá kyselina se hodí k rajčatům a šunce.",
         note="Výseče se v různých pizzeriích obkládají různě.", sources=[ITALIA]),
    dict(slug="07-diavola", name="Diavola", place="Italská pizzeriová tradice",
         story="Diavola je zavedený italský název pro pikantní pizzu, obvykle s pálivým salámem. Nejde o jeden chráněný recept: ostrost i druh uzeniny se liší mezi pizzeriemi. Tento list zachycuje modelovou kombinaci rajčat, mozzarelly a pikantního salámu, nikoli historicky rekonstruovaný originál.",
         character="Tuk salámu nese chilli, rajče přidává kyselinu. Stupeň pálivosti je věcí použitého salámu.",
         ingredients=[("Rajčata", 75), ("Mozzarella", 80), ("Pikantní salám", 55), ("Olivový olej", 6)],
         allergens="1 (lepek), 7 (mléko); u salámu ověřit etiketu",
         wine="Ovocné červené Primitivo s mírným taninem: nezdůrazní tolik pálivost.",
         note="Není možné slíbit alergenní profil salámu bez obalu výrobku.", sources=[ITALIA]),
    dict(slug="08-prosciutto-funghi", name="Prosciutto e Funghi", place="Italská pizzeriová tradice",
         story="Šunka a houby tvoří snadno srozumitelnou klasiku italských pizzerií. Neodkazuje ke konkrétnímu autorovi či doloženému roku vzniku, spíš k osvědčenému spojení surovin. Pro tuto ukázku volíme vařenou šunku; prosciutto crudo by změnilo slanost i okamžik přidání.",
         character="Umami hub, jemná šunka a mléčná mozzarella. Houby je vhodné předem osušit, aby se střed pizzy nerozmočil.",
         ingredients=[("Rajčata", 75), ("Mozzarella", 85), ("Vařená šunka", 55), ("Žampiony", 55), ("Olivový olej", 6)],
         allergens="1 (lepek), 7 (mléko); u šunky ověřit etiketu",
         wine="Lehké červené Valpolicella: ovocnost doplní houby i šunku.",
         note="Vařená šunka zde není automaticky bez dalších alergenů.", sources=[ITALIA]),
    dict(slug="09-boscaiola", name="Boscaiola", place="Italská pizzeriová tradice",
         story="Boscaiola, tedy lesnický styl, spojuje houby a klobásu; tato dvojice je uvedena také v přehledu italských pizz na Italia.it. Varianta s mozzarellou a bez rajčat ukazuje, jak se bílé pizzy liší od neapolské dvojice chráněné pravidly AVPN.",
         character="Zemité houby a výrazná klobása vytvářejí sytý profil. Není vhodné tvrdit, že všechny Boscaioly používají shodnou klobásu.",
         ingredients=[("Mozzarella", 90), ("Houby", 75), ("Klobása", 65), ("Olivový olej", 6)],
         allergens="1 (lepek), 7 (mléko); u klobásy ověřit etiketu",
         wine="Svěží Sangiovese: kyselina vyvažuje tuk klobásy.",
         note="Složení klobásy může přidat další povinně deklarované alergeny.", sources=[ITALIA]),
    dict(slug="10-ortolana", name="Ortolana", place="Italská zeleninová tradice",
         story="Ortolana, pizza ve stylu zahradníka, ukazuje sezónní zeleninu jako hlavní oblohu. Jediná univerzální sestava zeleniny neexistuje: v tomto listu jsou cuketa, paprika a lilek. Podobné variace odpovídají pestrosti italských obloh, ne tvrzení o konkrétním historickém receptu.",
         character="Pečená zelenina dodává sladkost a trochu kouřovosti; mozzarella a rajče vše propojí.",
         ingredients=[("Rajčata", 70), ("Mozzarella", 75), ("Cuketa", 45), ("Paprika", 45), ("Lilek", 45), ("Olivový olej", 7)],
         allergens="1 (lepek), 7 (mléko)", wine="Suché Pinot Grigio: lehkost nepřekryje zeleninu.",
         note="Sezónní obměna zeleniny znamená i novou kontrolu receptury.", sources=[ITALIA]),
    dict(slug="11-pizza-bianca-romana", name="Pizza Bianca Romana", place="Řím, Lazio",
         story="Římská pizza bianca je jednoduchá bílá placka, kterou lze koupit v pekárně a jíst samotnou. Turismo Roma popisuje oblíbenou sezónní variantu plněnou šunkou a fíky. Zde zůstáváme u samotné bílé pizzy s rozmarýnem: není to tatáž receptura jako sladko-slaná pizza e fichi.",
         character="Křupavý povrch, olivový olej, rozmarýn a sůl bez rajčat a sýra. Technika a hydratace se liší podle římské pekárny.",
         ingredients=[("Olivový olej", 12), ("Rozmarýn", 3), ("Mořská sůl", 2)],
         allergens="1 (lepek)", wine="Suché Frascati: jemné bílé víno k bylinkám a oleji.",
         note="Přidání šunky nebo fíků z ní udělá jinou variantu.", sources=[ROMA, TYPES]),
    dict(slug="12-pizza-fritta", name="Pizza Fritta Napoletana", place="Neapol, Kampánie",
         story="Smažená pizza připomíná poválečné neapolské pouliční jídlo: když bylo pečení obtížné, těsto se plnilo a smažilo v oleji. Výplně nebyly vždy stejné; známá je ricotta a provola. Ve filmu Vittoria De Sicy Zlato Neapole (L'oro di Napoli) prodává smaženou pizzu postava hraná Sophií Loren. Jde o filmovou scénu, ne doklad osobních chutí herečky.",
         character="Uzavřená kapsa s krémovou náplní a smaženým povrchem. Na rozdíl od ostatních listů se nepeče v peci.",
         ingredients=[("Ricotta", 75), ("Provola", 55), ("Rajčata", 35), ("Salám", 35), ("Olej absorbovaný*", 18)],
         allergens="1 (lepek), 7 (mléko); u salámu ověřit etiketu",
         wine="Suché šumivé Asprinio d'Aversa: svěžest k smaženému těstu.",
         note="*Absorpce oleje je pouze demonstrativní odhad, nikoli nutriční údaj.", sources=[FRITTA]),
]


def para(c: canvas.Canvas, text: str, x: float, top: float, width: float, style=BODY) -> float:
    p = Paragraph(text, style)
    _, height = p.wrap(width, H)
    p.drawOn(c, x, top - height)
    return top - height


def label(c: canvas.Canvas, text: str, x: float, y: float, size: int = 10, color=INK) -> None:
    c.setFillColor(color)
    c.setFont("Arial-Bold", size)
    c.drawString(x, y, text)


def frame(c: canvas.Canvas, pizza: dict, page: int) -> None:
    c.setFillColor(CREAM)
    c.rect(0, H - 112, W, 112, stroke=0, fill=1)
    c.setFillColor(RED)
    c.rect(0, H - 112, 9, 112, stroke=0, fill=1)
    label(c, "PIZZA / REDAKČNÍ KARTA", 40, H - 35, 9, RED)
    label(c, pizza["name"], 40, H - 72, 23)
    c.setFont("Arial", 10)
    c.setFillColor(MUTED)
    c.drawString(41, H - 93, pizza["place"])
    c.setStrokeColor(colors.HexColor("#d9e1df"))
    c.line(40, 49, W - 40, 49)
    para(c, "Ukázková znalostní báze · recept a množství jsou modelová data · 2026",
         40, 43, W - 125, CAPTION)
    label(c, f"{page} / 2", W - 76, 32, 9, MUTED)


def pizza_illustration(c: canvas.Canvas, x: float, y: float, pizza: dict) -> None:
    """Schematic vector diagram; ingredient pictograms are decorative."""
    cx, cy, r = x + 90, y + 91, 73
    c.setFillColor(colors.HexColor("#d99a5b"))
    c.circle(cx, cy, r, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#f6dcaa"))
    c.circle(cx, cy, r - 9, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#c55342") if any("Rajč" in a for a, _ in pizza["ingredients"])
                   else colors.HexColor("#ead4a3"))
    c.circle(cx, cy, r - 18, fill=1, stroke=0)
    for i, (item, _) in enumerate(pizza["ingredients"][:6]):
        theta = 2 * math.pi * i / min(6, len(pizza["ingredients"])) + 0.2
        px, py = cx + 36 * math.cos(theta), cy + 36 * math.sin(theta)
        c.setFillColor(colors.HexColor(PALETTE[i]))
        c.circle(px, py, 9 + i % 3, fill=1, stroke=0)
    c.setStrokeColor(MUTED)
    c.line(cx + 66, cy + 30, x + 194, y + 151)
    c.line(cx + 12, cy - 8, x + 194, y + 112)
    c.line(cx - 63, cy - 47, x + 194, y + 72)
    para(c, "okraj / těsto", x + 198, y + 158, 148, SMALL)
    para(c, "střed / obloha", x + 198, y + 119, 148, SMALL)
    para(c, "barevné značky = přísady", x + 198, y + 79, 148, SMALL)
    para(c, "Schéma, nikoli fotografie ani údaj o původu surovin.", x + 7, y + 20, 374, CAPTION)


def ingredients_table(c: canvas.Canvas, pizza: dict, top: float) -> float:
    x, width = 40, W - 80
    rows = [("Těsto (mouka 00, voda, droždí, sůl)", "250 g")]
    rows += [(name, f"{grams} g") for name, grams in pizza["ingredients"]]
    row_h = 23
    c.setFillColor(INK)
    c.roundRect(x, top - 27, width, 27, 5, stroke=0, fill=1)
    label(c, "Surovina / modelová porce", x + 12, top - 18, 9, colors.white)
    label(c, "Množství", x + width - 82, top - 18, 9, colors.white)
    y = top - 27
    for i, (name, amount) in enumerate(rows):
        if i % 2 == 0:
            c.setFillColor(CREAM)
            c.rect(x, y - row_h, width, row_h, fill=1, stroke=0)
        para(c, name, x + 12, y - 6, width - 106, SMALL)
        para(c, amount, x + width - 80, y - 6, 68, SMALL)
        y -= row_h
    return y


def donut(c: canvas.Canvas, pizza: dict, x: float, y: float) -> None:
    total = sum(mass for _, mass in pizza["ingredients"])
    start = 90
    cx, cy, r = x + 83, y + 86, 70
    for i, (name, mass) in enumerate(pizza["ingredients"]):
        extent = mass * 360 / total
        c.setFillColor(colors.HexColor(PALETTE[i % len(PALETTE)]))
        c.wedge(cx - r, cy - r, cx + r, cy + r, start, extent, fill=1, stroke=0)
        start += extent
    c.setFillColor(colors.white)
    c.circle(cx, cy, 35, fill=1, stroke=0)
    label(c, f"{total} g", cx - 22, cy - 3, 12)
    para(c, "obloha", cx - 26, cy - 8, 53, CENTER)
    for i, (name, mass) in enumerate(pizza["ingredients"]):
        column = i // 4
        row = i % 4
        lx, ly = x + 181 + column * 145, y + 141 - row * 35
        c.setFillColor(colors.HexColor(PALETTE[i % len(PALETTE)]))
        c.circle(lx + 5, ly - 2, 5, fill=1, stroke=0)
        para(c, f"{name}<br/>{mass / total:.0%} oblohy", lx + 17, ly + 5, 123, SMALL)


def process(c: canvas.Canvas, pizza: dict, y: float) -> None:
    names = ["Zamíchat", "Nechat zrát", "Vytvarovat", "Naplnit", "Smažit" if "fritta" in pizza["slug"] else "Péct"]
    w, gap = 89, 17
    for i, name in enumerate(names):
        x = 40 + i * (w + gap)
        c.setFillColor(CREAM if i % 2 == 0 else colors.HexColor("#e5eee9"))
        c.roundRect(x, y, w, 47, 7, fill=1, stroke=0)
        label(c, str(i + 1).zfill(2), x + 7, y + 28, 8, RED)
        para(c, name, x + 5, y + 23, w - 10, CENTER)
        if i < 4:
            label(c, ">", x + w + 4, y + 19, 12, GREEN)


def make_pdf(pizza: dict) -> Path:
    path = OUT / f"{pizza['slug']}.pdf"
    c = canvas.Canvas(str(path), pagesize=A4, pageCompression=1)
    c.setTitle(f"Pizza {pizza['name']} | ukázková znalostní báze")
    c.setAuthor("AI Horizons · ukázková data")

    frame(c, pizza, 1)
    y = H - 139
    label(c, "Původ a příběh", 40, y, 13)
    y = para(c, pizza["story"], 40, y - 13, W - 80) - 23
    label(c, "Jak chutná", 40, y, 13)
    y = para(c, pizza["character"], 40, y - 13, W - 80) - 23
    label(c, "Modelová receptura · jedna pizza", 40, y, 13)
    table_bottom = ingredients_table(c, pizza, y - 14)
    label(c, "Anotovaná stavba pizzy", 40, table_bottom - 24, 13)
    pizza_illustration(c, 45, table_bottom - 219, pizza)
    if table_bottom - 219 < 50:
        raise ValueError(f"Page 1 overflow for {pizza['slug']}")
    c.showPage()

    frame(c, pizza, 2)
    label(c, "Vizualizace modelové porce", 40, H - 142, 13)
    para(c, "Podíl hmotnosti přísad v obloze; těsto se do kruhu nezapočítává.",
         40, H - 153, W - 80, CAPTION)
    donut(c, pizza, 42, H - 350)
    label(c, "Alergeny a provozní upozornění", 40, H - 380, 13)
    y = para(c, f"<b>Deklarované složky receptu:</b> {pizza['allergens']}. "
             "EU číslování: 1 obiloviny obsahující lepek, 3 vejce, 4 ryby, 7 mléko. "
             "Nejde o prohlášení o nepřítomnosti jiných alergenů ani o posouzení křížového kontaktu.",
             40, H - 393, W - 80)
    y -= 26
    label(c, "Doporučené párování", 40, y, 13)
    y = para(c, pizza["wine"], 40, y - 13, W - 80)
    y = para(c, pizza["note"], 40, y - 6, W - 80, CAPTION) - 27
    label(c, "Postup · orientační schéma", 40, y, 13)
    process(c, pizza, y - 65)
    y -= 100
    label(c, "Zdroje a interpretace", 40, y, 12)
    y -= 9
    for source in pizza["sources"]:
        y = para(c, source, 40, y - 5, W - 80, SMALL)
        c.linkURL(source, (40, y, W - 40, y + 11), relative=0)
    y = para(c, "Historické a typologické údaje vycházejí ze zdrojů výše. Gramáže, "
             "podíly, konkrétní recept, doporučení vína a diagram jsou ukázkové "
             "redakční údaje určené k testování extrakce z PDF.",
             40, y - 14, W - 80, CAPTION)
    if y < 62:
        raise ValueError(f"Page 2 overflow for {pizza['slug']}")
    c.save()
    return path


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for pizza in PIZZAS:
        print(make_pdf(pizza))


if __name__ == "__main__":
    main()
