# Inkle-to-Card Draft Converter — Research Step 1 (Domain Foundations)

Date: 2026-10-18 · Project: ~/projects/inkle-to-card/ · Program goal: inkle belt pattern -> correlated card (tablet) weaving settings (colors, positions, threading, turning, clear start position) -> PDF report.
Method: all sources fetched and saved this session (research/pages/); ids map to URLs via the session ledger (research/citations/ledger.json); key claims carry verbatim quotes (evidence render below). Derived/absence claims are flagged [unverified].

## 1. Headline
1. Inkle pattern = warp-only 2-row draft (top heddled / bottom unheddled), 1 square = 1 end, read L-to-R.[2][4]
2. Card settings = per-card hole colors A-D + S/Z threading + F/B turning per pick + deck start position.[7][8]
3. The bridge is standard practice: tablets woven ON inkle looms, 4 ends per card, the card stack replacing the heddles.[12][13][14]
4. Conventions exist for everything the PDF must state: A-D clockwise on front, cards numbered L-to-R facing right, home position A and D up, 8-pick 4F-4B default repeat.[8][11]
5. No tool found that converts inkle drafts -> card settings: InklePattern.com "needs a different draft and is not supported here"[18]; Seizenn edits both only as separate modules[16]; karetka converts tablet CSV only.[26] [unverified: this sweep]

## 2. Inkle side
Narrow warp-faced bands go by tape, band, inkle, strap, belt, trim; the inkle loom requires a continuous warp.[1] Inkle drafts apply only to the warp (weft barely visible): warp color order + which ends go on heddles; standard draft = 2-row grid, each square one end, top heddled / bottom unheddled, read left to right.[2] Schacht manual: a pattern draft is "a graphic description of the placement of the different colors of warp yarns used for the warp pattern"; top row through heddles, bottom row not.[4] Families: plain-weave color orders vs Baltic/speckled pick-up (pattern ends manipulated each pick).[12] Generators use a numbered H/U warp order with alternating sheds; pickup uses pick/drop charts; typical starter 17 threads, 9H/8U.[18]

## 3. Card side
Cards create the shed by turning: continually as a pack, individually for patterns, or n-forward/n-back.[5][12] Holes labeled A, B, C, D clockwise on the front face; tablets numbered left to right, facing right.[8] Cards are usually marked with colors or stripes so facings are noticed (teach this in the PDF).[5] S/Z threading: all four holes must be strung in the same direction or the card won't turn; Hendrickson's alternative is L/R notation.[6][8] A pick = quarter turn + weft pass; forward = bicycle-wheel direction from the weaver's view.[8] Structure is determined by threading direction, threading pattern, and turning direction; threads twist into a cord, the top-of-tablet thread shows on the band's face, and forward turning brings A,B,C,D successively to the near-top corner.[7] Home position: threaded-in patterns start with all tablets at the same home position, holes A and D above the warp; the term comes from Step by Step Tablet Weaving, but conventions differ - Groff's drafts begin with A and D closest to the fell, so the converter must state its convention.[8][11] Default 4F-4B: picks 1-4 look like the draft, 5-8 are its mirror; from standard position the surface shows D,C,B,A,A,B,C,D - the prediction model.[8] One-way turning builds twist; mitigations: push twist out, untie and comb, swivels/weights.[8]

## 4. Bridge
Mullarkey's laces: wind a warp of 40 ends on an inkle loom and thread onto 10 four-hole cards ("Inkle loom; belt shuttle; 10 four-hole weaving tablets"); the tablet stack goes where heddles would be, four warp ends per card.[12][13][14] "Tablet weaving is a little like loom-controlled complex patterning for inkle bands."[14] Threaded-in patterns: pattern from threading alone, all cards turned together.[8][14] A striped inkle band can be woven within a tablet deck; Twisted Threads supports warp-faced tabby (inkle-like plain weave) alongside warp-twined.[14][24] Translation gap: an inkle draft is a flat color sequence[2]; a tablet draft needs tablet count/order, per-hole colors, S/Z per tablet, and turning per pick.[8] Derived grain analysis (validate in Step 2): each card shows 1 thread per pick in an 8-pick cycle[8] while inkle alternates heddled/unheddled ends per pick[2] - so under the four-ends-per-card grouping, stripes of >=4 ends map cleanly to cards while narrower features degrade. (Corrected 2026-10-18: this analysis applies to Mapping B; the width-preserving Mapping A adopted in section 7 maps each end to a full card and preserves single-end stripes at fourfold thread cost.) Print the applicable caveat in the PDF.

## 5. Prior art (none take an inkle draft as input [unverified])
TDD (github.com/jamespbarrett/tabletweave): JS tablet draft designer; active repo (v1.8.2, 2026-01); live site timed out in this sweep.[25] Twisted Threads (shelaghlewins.com / twistedthreads.org): web app for designing/weaving/sharing; interactive chart highlights the current row; Applesies and Fox Noses notation; supports brocade and warp-faced tabby.[24] GTT (guntram.co.za): "easiest to use" in a 2026 roundup (paid placements disclosed; main page 404 in this sweep); catalog spans threaded-in and doubleface families.[17] Seizenn (raktres.net, Jeff Bigot): free band-weaving pattern editor; separate inkle/tablet/disk/takadai modules, no conversion between them.[16] WeaveIt, Tablet Weaver, TempoWeave Mobile: commercial chart-focused drafting per the same roundup.[17] karetka (github.com/MartinRybensky/karetka): tablet-weaving CSV -> per-card, per-row turning instructions (HTML/TXT).[26] cardweaver (github.com/audreyseo/cardweaver): DSL + program synthesis; "card weaving instructions are mind-bogglingly low-level"; translating patterns between band-weaving kinds is a listed application.[27] snaut/tabletweaving: JS editor, S/Z + F/B per cell, JSON save, planned twist counter.[28]

## 6. Books
Collingwood, The Techniques of Tablet Weaving - definitive treatise (proved the Rameses girdle not tablet-woven; covers double-face twill, plain/twined weaves, brocades, patterned velvet).[5][23] Crockett, Card Weaving (Interweave, 1991) - standard modern reference in the Little Looms projects.[13] Step by Step Tablet Weaving - origin of "home position".[11] Karisto & Pasanen, Applesies and Fox Noses - notation Twisted Threads follows.[24]

## 7. v1 mapping algorithm (derived from cited mechanics; validate in Step 2)
Parse ends (color + H/U) -> assign ends to cards (corrected 2026-10-18 design decision). Mapping A, default and width-preserving: one inkle end per card, all four holes threaded with that end's color, so the deck reproduces the inkle color sequence across the band at full width, one card per column. Mapping B, optional and material-efficient: four consecutive ends per card, compressing the pattern to one-quarter width - Mullarkey's 10-card laces are a Mapping-B draft.[8][13] Then: S/Z rule per card (S turned forward gives Z-twined cord) -> 4F-4B pack default -> start position: home position A/D up, printed side right, Tablet 1 left -> emit draft table + turning chart + start-position figure + materials.[7][8][11][13][14] Caveats: Mapping B degrades features narrower than 4 ends, Mapping A costs four times the thread; Baltic pick-up out of scope v1 (double-face, 2 light / 2 dark, is the later path).[7][14]

## 8. PDF report spec
P1 title block. P2 threading draft table: column per card L-to-R, rows A-D colored per hole, fifth row = S/Z direction.[8] P3 deck summary: printed side toward the right, Tablet 1 at the left.[11] P4 starting position: explicit convention + figure (A corners top-far per Little Looms, or A/D up per Keith/Capriest); print which convention is used.[8][11][13] P5 turning chart: per pick, F/B per card, e.g. "4 turns forward (away from weaver) and 4 turns back (toward weaver)".[8][13] P6 woven preview from the surface-sequence model.[7][8] P7 materials: warp = 1.2 x length + 50 cm, or explicit allowances (40 ends 80", 8" take-up, 8" loom waste); card count; shuttle.[6][13] P8 notation legend: F/B, S/Z with slash symbols (community consensus "/" = Z, "\" = S), mark cards with colors/stripes.[5][8] P9 twist-build-up warnings and mitigations.[8]

## 9. Limitations
Home-position conventions conflict across books - the program must declare and print its convention, optionally both.[8][11] Six registered sources failed extraction and stay uncited: aspinnerweaver drafts page and the yarn-choices page (translate shells), TDD live site (timeout), GTT main page (404), and two JS-shell pages (a wooden-tables shop, a yarn-shop blog). The 2026 software roundup includes paid placements - rankings indicative only.[17] Community sentiment (Reddit/Ravelry/weaver YouTube) not yet swept. The absence claim in section 1 is limited to this sweep [unverified]. The section 7 algorithm is our derivation - validate against simulators and a hand-woven sample.

## 10. Next steps
Step 2: formal algorithm spec + hand-translate a 17-end starter (9H/8U), check against the D,C,B,A,A,B,C,D surface rule and a simulator (TDD/Seizenn).[8][16][18][25] Step 3: Python architecture (inkle parser -> card model -> reportlab PDF, P1-P9). Step 4: build + tests, then compile -> test -> commit -> README -> push main. Step 5: weave a sample band; correct the model where the cloth disagrees.

## 11. Commonly available tablet styles (equipment notes for the PDF)

The modern standard is the square four-hole card: the vast majority of weaving tablets are square with four holes, one per corner; triangular tablets have been found, there is evidence for six- and eight-holed tablets historically, and square tablets are universal among modern tablet weavers.[33]

A fiber-arts retailer currently offers five commercial styles, 25 cards per pack, with concrete specifications: Lacis laminated plastic cards (2-1/2" square, virtually indestructible) and Schacht cardboard cards (3.25" square, holes 1-5/8" apart on center, each side of the card a different color so misaligned cards are visible from the side view).[31] Hendrickson sells 4-hole and 8-hole cardboard cards, 3.5" on a side, with sides marked A, B, C and D to help keep order while weaving - the labeling convention this converter's drafts use.[31][8] Schacht's own page describes its cards as 3-1/2" square with colored bands and stripes along each edge to help you follow a pattern, made of sturdy yet flexible 24-point cardboard; the two stated Schacht sizes disagree between sources (3.25" at the retailer vs 3-1/2" from Schacht), so the PDF should not depend on card size.[30] The cards are used on their own - tied to a doorknob and tensioned around the waist - or on an inkle loom.[30]

DIY cards remain the classic starting point: cut a square about 5 cm on each side from cardboard or old playing cards, punch four holes in the corners, and round the corners off; historically tablets were made of bone or wood, and perhaps also of leather or horn.[39][6] A first band needs only 8 tablets, one shuttle, and two colors of yarn.[39] Six- and eight-hole cards are in modern use for advanced patterning.[14] Cards are usually marked with colors or stripes so their facings and orientations can be easily noticed - a habit the PDF legend should teach.[5]

Program implication: the converter targets the square four-hole card as its default hardware assumption (a 25-card pack covers bands up to 100 ends under Mapping A), states card count as one card per inkle end, and follows the A-D labeling embodied by Hendrickson's cards and the standard notation.[31][8]

## 12. Color selection guidance (palette module and PDF color notes)

The dominant factor in pattern visibility is value contrast - the light/dark difference - not hue: the eye perceives differences in value much more clearly than any other aspect of color, so yarns with strong light/dark contrast create bold patterns while equal-value colors blend into subtle designs.[34] "How bold your pattern looks depends almost entirely on how much black-and-white contrast there is within the pattern."[35] Hue contrast (how far apart colors are on the color wheel) does matter in making a pattern perceptible, but not nearly as much as value contrast: near-opposite hues with equal values weave blurry patterns, while a single hue with strong value contrast weaves a clear one.[37]

Visibility is bounded by the yarns: you can never get more contrast in the pattern than exists in the original yarns, so drafts should start from warp colors with strong light-dark contrast.[35] Because warm and bright colors appear lighter to the eye than they measure, weavers are advised to judge value by taking a black-and-white photo of the yarns before warping.[35] A second rule concerns mixing scale: two colors mixed in small dots blend their hues in the eye - bright green with magenta in plain weave gives brown - while larger patches contrast more strongly, which matters for one- and two-end features inside color sequences.[34]

Derived program behavior (our design, premises cited): implement the black-and-white-photo test digitally - compute each palette color's grayscale value, print a value ladder in the PDF palette section, and warn when adjacent stripe blocks in the source draft have low value contrast (threshold to calibrate in Step 2) - and carry a mixing caveat for sub-two-end features.[34][35]

## Sources

[1] https://en.wikipedia.org/wiki/Inkle_%28loom%29 — Wikipedia - Inkle (loom)
    > "One key element that differentiates inkle looms from other band looms is that a continuous warp is required."
    > "Band weaving** is the hand production of narrow woven fabric. This fabric may be called tape, band, [inkle](https://en.wikipedia.org/wiki/Inkle_(loom) "Inkle (loom)"), strap, belt, back strap, trim, and more."
[2] https://littlelooms.com/how-to-read-a-simple-inkle-draft — Little Looms - How to Read a Simple Inkle Draft
    > "The first important note about inkle drafts is that they apply only to the warp. Inkle weaving is a warp-faced weave, meaning you do not see the weft except at the selvedge, and even then just barely—so no weft color order is needed. Instead, you’ll get a warp color order and information about which warp ends need to be threaded on string heddles."
    > "Each colored square represents 1 warp thread, which we call an “end.”"
    > "The top layer of squares is typically labeled as “heddled” and the bottom as “unheddled.”"
[4] https://www.wollinchen.de/WebRoot/Store5/Shops/61105751/4A60/DE7C/7FE0/0F17/0336/C0A8/2935/6B37/inkle-manual.pdf — Schacht Inkle Weaving manual (PDF)
    > "The top row of the draft shows the warp threads that will be strung through heddles. The bottom row shows the warp threads which will not pass through heddles."
    > "Pattern Draft:* a graphic description of the placement of the different colors of warp yarns used for the warp pattern."
[5] https://en.wikipedia.org/wiki/Tablet_weaving — Wikipedia - Tablet weaving
    > "The fundamental principle is to turn the tablets to lift selected sets of threads in the warp. The tablets may be turned in one direction continually as a pack, turned individually to create patterns, or turned some number of times "forward" and the same number "back"."
    > "The tablets are usually marked with colors or stripes so that their facings and orientations can be easily noticed."
    > "appendix to his book _The Techniques of Tablet Weaving_, Peter Collingwood proved by structural analysis that the linen belt could not have been woven on tablets."
[6] https://www.stringpage.com/tw/basictw.html — Phiala's String Page - Basic Tablet Weaving
    > "warp length = 1.2 x final length + 50 cm"
    > "A card can be strung from left to right (Z-threaded) or right to left (S-threaded), but all four holes must be strung in the same direction or the card won't turn."
[7] https://www.stringpage.com/tw/twtheory.html — Phiala's String Page - Tablet Weaving Theory
    > "The thread which moved over the top of the tablet is the one which shows on the top face of the finished band."
    > "When the tablet is turned forward, holes A, B, C, D successively occupy the near top corner."
    > "threads in each tablet are twisted together to form a cord in the finished band."
    > "There are three important elements which determine the structure of tablet weaving: threading direction, threading pattern, and turning direction."
[8] https://www.keithweaves.com/tablet-weaving-standard-terms-and-notation — Keith Weaves - Tablet weaving standard terms and notation
    > "holes are labeled A, B, C, D, clockwise on the front face of the tablet."
    > "Tablets are numbered left to right and face to the right."
    > "Threaded-in patterns start with all tablets rotated to the same _home position_, with holes A and D above the warp."
    > "A pick consists of turning each tablets in the pack and then passing a weft."
    > "Warping involves determining the number and order of tablets, the colors to be threaded in each hole, and each tablet’s initial threading direction. Weaving involves determining how tablets are to be turned for each pick."
    > "The diagram is a table, one column for each tablet, numbered left to right, and one row for each hole, lettered A through D. Each table cell is colored to match the color of the thread passing through a hole of a tablet."
    > "Such drafts assume that the weaver will follow the 8-pick repeating sequence 4F-4B. When she does so, the first four rows look just like the draft, and the next four rows look like its mirror image (reflected along the top row)."
    > "turning 4F-4B will show rows D, C, B, A, A, B, C, D."
    > "All cards are rotated so that holes A and D are on the top."
[11] https://www.cs.vassar.edu/~capriest/3recipes.html — Capriest - Three Recipes for 14th-15th c. tablet weaving
    > "The term "home position," borrowed from the book Step by Step Tablet Weaving, refers to the basic starting point of a sequence of weaving."
    > "thread your tablets with the printed side toward the right, with Tablet 1 at the left side of the pack."
    > "Russell Groff's pattern drafts, for example, require beginning with holes A and D closest to the fell."
[12] https://handwovenmagazine.com/bandweaving-classes-for-beginners-and-beyond — Handwoven - Inkle vs. Tablet
    > "is done on an inkle loom and requires either string heddles or a rigid heddle to change sheds. It may or may not also involve pick-up."
    > "In the simplest designs, you turn all the cards together alternating going forward and backward the same number of times—i.e., forward, forward, backward, backward, repeat."
    > "Tablet weaving**, which can also be done on an inkle loom, uses a set of weaving tablets to change sheds. Each tablet has a set number of holes, usually at the corners. Warp ends are threaded in a certain order through these holes, and the shed is changed by turning the cards."
[13] https://www.datocms-assets.com/70931/1730831308-ll-tablet-projects-ebook_final.pdf — Little Looms tablet weaving projects ebook (PDF)
    > "Align the tablets so that the A 2corners of the tablets are at the top far corner as shown in Figure 2."
    > "Crockett, Candace. *Card Weaving.* Loveland, CO: Interweave, 1991."
    > "EQUIPMENT** Inkle loom; belt shuttle; 10 four-hole weaving tablets."
    > "4 turns forward (away from weaver) and 4 turns back (toward weaver)."
[14] https://littlelooms.com/patterning-portability-and-intrigue — Little Looms - Tablet weaving patterning and portability
    > "Instead of raising the unheddled ends above and below the heddled ones as you would with an inkle loom, he simply turned the deck of tablets according to the draft."
    > "Threaded-in patterns, he explained, are those where the pattern is achieved only by the way the cards are threaded. All cards are turned together, either forward or backward."
    > "where I would normally attach heddles, John had inserted a stack of tablets with four warp ends threaded through each one."
    > "Tablet weaving is a little like loom-controlled complex patterning for inkle bands."
    > "He even wove a simple striped inkle band in the center with unwoven warps above and below."
[16] https://www.raktres.net/seizenn — Seizenn inkle pattern editor
    > "SeiZenn - Band Weaving Pattern Editor"
[17] https://worldmetrics.org/best/tablet-weaving-software — WorldMetrics - Best Tablet Weaving Software 2026
    > "is the best pick when you need repeat-consistent tablet-weaving drafts for printing and community sharing, whereas **Tablet Weaver** fits when you’re doing loom work from repeat-based threading and want dependable, chart-focused outputs."
    > "Includes paid placements · ranking is editorial."
    > "Simulation preview tied to the draft build process to reduce errors before print and loom use."
[18] https://inklepattern.com/patterns — InklePattern.com - free inkle patterns
    > "Plain weave uses a numbered heddled/open (H/U) warp order and alternating sheds."
    > "Tablet weaving needs a different draft and is not supported here."
[23] https://schachtspindle.com/products/the-techniques-of-tablet-weaving — Schacht - The Techniques of Tablet Weaving (Collingwood)
    > "Peter Collingwood is well known to weavers as a thorough textile technique researcher. His ability to dive into a technique as he does here in _The Techniques of Tablet Weaving_ provides the weaving enthusiast with clear and accurate instruction, covering the topic in amazing detail."
[24] https://www.shelaghlewins.com/tablet_weaving/twt_patterns.php — Shelagh Lewins - Twisted Threads patterns page
    > "Twisted Threads is a web-based application for designing, weaving and sharing tablet weaving patterns."
    > "additionally supports brocade and warp-faced tabby structures."
[25] https://github.com/jamespbarrett/tabletweave — GitHub - jamespbarrett/tabletweave (TDD)
    > "This is a simple javascript based application intended to help practictioners of the ancient art of tablet weaving who wish to design their own drafts."
[26] https://github.com/MartinRybensky/karetka — GitHub - MartinRybensky/karetka (pattern to instructions)
    > "An application made for conversion of tablet weaving patterns in CSV format into instructions (which direction should be turned each tablet on each row and so on) in the HTML or TXT form."
[27] https://github.com/audreyseo/cardweaver — GitHub - audreyseo/cardweaver (DSL + synthesis)
    > "The original motivation for this project is the fact that card weaving instructions are mind-bogglingly low-level."
    > "translating patterns for other kinds of band weaving, using cross stitch patterns as the basis of card weaving patterns"
[28] https://github.com/snaut/tabletweaving — GitHub - snaut/tabletweaving (JS pattern editor)
    > "A tablet weaving pattern editor written entirely in javascript, html, css, svg."
    > "twist counter to help with creating twist neutral patterns"
[30] https://schachtspindle.com/products/tablet-weaving-cards — Schacht - Card Weaving Cards (pack of 25)
    > "Sold in a pack of 25 cards."
    > "Each card is 3-1/2" square, with colored bands and stripes along each edge to help you follow a pattern."
    > "You can use the cards on their own with a simple tensioning device, such as tying the yarn to a door knob and tensioning around your waist. Or use the cards on our Inkle Loom."
[31] https://www.mielkesfiberarts.com/product/card-weaving-cards — Mielke's Fiber Arts - four styles of card weaving cards
    > "All 4 types of cards we offer. 25 in each pack."
    > "LACIS: 25 laminated plastic card weaving cards, .019″ thick, 2-1/2″ square. For card and tablet weaving. Virtually indestructible, will not tear while providing a smooth surface for manipulation of threads. SCHACHT: 25 cardboard cards, 3.25″ square. Holes are 1-5/8th” apart on center."
    > "Choose from five styles of card weaving cards:_ LACIS: 25 laminated plastic card weaving cards, .019″ thick, 2-1/2″ square. For card and tablet weaving. Virtually indestructible, will not tear while providing a smooth surface for manipulation of threads. SCHACHT: 25 cardboard cards, 3.25″ square. Holes are 1-5/8th” apart on center."
    > "SCHACHT: 25 cardboard cards, 3.25″ square. Holes are 1-5/8th” apart on center."
    > "HENDRICKSON 4 hole: Pack of 25 cards These Tablet Weaving Cards are made of cardboard, and are 3.5″ on each side. Sides are marked A, B, C and D to help with keeping order while weaving."
[33] https://www.stringpage.com/assets/other/structures.pdf — Phiala - Tablet Weaving Structures: Theory and History (PDF)
    > "The vast majority of weaving tablets are square, with four holes, one per corner. Triangular tablets have been found, and there is evidence for the use of six and eightholed tablets as well."
    > "The structure of tablet weaving is determined by five main characteristics: • the shape or number of holes in the tablets. • which of the holes contain warp threads. • the threading direction of the warp. • the turning pattern. • whether adjacent tablets are set up the same way."
    > "work with square tablets in this article since they are universal among modern tablet weavers."
[34] https://handwovenmagazine.com/two-rules-color-theory-in-weaving — Handwoven - Two Rules About Color Theory in Weaving
    > "Rule 2. The eye perceives differences in value very clearly—much more clearly than it sees any other aspect of color. As a result, yarns with strong light/dark contrast will create a bold pattern in your handwoven cloth, while colors with equal values will blend into a subtle design. That makes it easy to figure out whether your woven pattern will show clearly in a given set of yarns."
[35] https://warpandweave.com/choose-yarn-colors-handwoven-designs — Warp & Weave - choose yarn colors for handwoven designs
    > "How bold your pattern looks depends almost entirely on how much black-and-white contrast there is within the pattern."
    > "The best way to figure out whether two yarns have enough light/dark contrast to make a pattern show up clearly is by taking a black and white photo of the yarns."
    > "You can never get more contrast in your pattern than you have in the original yarns. So if you want your pattern to show clearly, you need to start with yarns that have strong light-dark contrast."
[37] https://handweavingacademy.com/stripes-drafts-magic-post — Handweaving Academy - Stripes + Drafts = Magic (value contrast)
    > "Hue contrast – how far apart colors are on the color wheel – does matter in making a pattern perceptible, but not nearly as much as value contrast."
    > "The secret is the contrast in darkness (also known as _value contrast_) between the warp and the weft."
    > "The more value contrast (light/dark contrast) between warp and weft, the more clearly the draft pattern will show."
[39] https://www.shelaghlewins.com/tablet_weaving/TW01/TW01.htm — Shelagh Lewins - Getting Started (equipment and materials)
    > "cut out a square about 5 cm on each side, and punch four holes in the corners, drawing construction lines as shown in **Figure 1** to locate the holes. Round the corners off as shown."
    > "Historically, tablets were made of bone or wood, and perhaps also of leather or horn."
    > "you will need: - 8 tablets - 1 shuttle - 2 different colours of yarn"
