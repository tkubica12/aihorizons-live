# Pizza PDF fixtures

`catalog.json` is a separate, versioned fictional structured catalog for the
relational database and MCP demo. Its prices, availability and allergen profiles
are not extracted from the PDFs or certified for food service. The PDF sheets
below remain editorial material; see `Docs/catalog-demo.md` for seeding and
verification.

`order-history.json` is a separate fictional milestone-2 fixture containing
three selectable demo profiles and six orders. It uses IDs from `catalog.json`
but is not derived from the PDFs or from real transactions. Seed the catalog
first; see `Docs/order-history-demo.md` for the read-only MCP example.

`pizza-pdfs/` contains 12 Czech, two-page PDF data sheets for a document-based
knowledge-base demo. Each sheet contains a short historical account, a model
ingredient table, EU allergen numbers, a suggested wine pairing, a labeled vector
illustration, a dough/assembly flowchart and a donut chart of topping masses.
The charts are computed from the adjacent model recipe, **not** from real sales,
nutrition or production measurements. Pizza variants vary by restaurant; these
documents must not replace a current business recipe or allergen declaration.

Regenerate in the managed Windows environment with
`python scripts\generate_pizza_pdfs.py` (requires ReportLab and Arial TTF).
The PDFs can be checked with PyMuPDF: expect exactly 12 files, two pages in each,
and selectable Czech text on both pages. The generator intentionally uses local
vector graphics; it does not call an image model or embed externally sourced
images.

## Sources and evidence scope

Public sources consulted on 2026-09-23 via Tavily search and page extraction:

| Source | What it supports |
| --- | --- |
| [Italia.it: traditional pizza](https://www.italia.it/en/campania/naples/things-to-do/pizza) | Common toppings and variant names |
| [Italia.it: Naples and pizza](https://www.italia.it/en/campania/naples/things-to-do/naples-world-pizza-capital) | Margherita legend and its uncertainty |
| [Italia.it: types of pizza](https://www.italia.it/en/italy/things-to-do/types-of-pizza-italy) | Neapolitan and Roman styles |
| [AVPN: Neapolitan standard](https://www.pizzanapoletana.org/it/ricetta_pizza_napoletana) | Marinara, Margherita and preparation |
| [Turismo Roma: pizza](https://turismoroma.it/es/15042013-la-pizza) | Roman pizza bianca and fig variant |
| [VisitNaples: pizza fritta](https://www.visitnaples.eu/napoletanita/sapori-di-napoli/la-pizza-fritta-napoletana-storia-e-tradizione-di-una-ricetta-tutta-napoletana) | Pizzas fried in postwar Naples and the film reference |

Evidence manifest: public official/culinary source class **searched** (six
relevant pages extracted); WebIQ public search **blocked** by connector
authentication, so Tavily was used. No internal workplace records or community
discussion were used. Each PDF lists only its relevant factual sources; recipe
weights, wine pairings, diagrams and allergen assessments are explicitly
editorial/demo material.

## Delivery

Target: private `pizza-pdfs` blob container in `aihorizons673af34ddocs`,
resource group `RG-AI-Horizons`. Upload with Microsoft Entra data-plane access,
`az storage blob upload --auth-mode login`, and list the container afterward to
confirm all 12 blob names and sizes. Never enable anonymous access or Shared Key
just to upload fixtures.
