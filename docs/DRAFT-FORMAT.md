# Draft formats

`inkletocard` reads two draft formats; `parse_draft()` sniffs which one you
mean (anything starting with `{` or ending in `.json` is JSON; anything with
an `ends:` directive or a non-`.json` file is the text format).

## JSON format

```json
{
  "name": "quiet-harbor-17",
  "palette": {
    "navy": "#1B2A4A",
    "cream": "#F5F0E6",
    "blue": "#3B6EA5",
    "gold": "#C9A227"
  },
  "order": "navy navy cream cream blue blue gold gold navy",
  "heddles": "H U H U H U H U H"
}
```

- `palette` maps color names to `#rrggbb` hex values. Names appear verbatim
  in the PDF, so name them the way you think about your yarn.
- The warp is either `"ends"` (a list) or `"order"` (a compact string):
  - `"ends": [{"color": "navy", "heddled": true}, ...]` — full control
    (the key `color_name` is accepted as an alias — that is what
    `import-grid --save-draft` writes);
  - `"order": "navy cream cream blue"` — color sequence only.
- With `order`, `"heddles"` is optional. Omitted, ends alternate starting
  with a heddled end (a 17-end draft becomes 9 H / 8 U). Provided, every
  token must be `H` (heddled) or `U` (open/unheddled) and the counts must
  match. A `U`-first warp is just as valid as an `H`-first one.

## Text format

```text
# whole-line comments start with #
name: my belt
palette: navy #1B2A4A, cream #F5F0E6
ends: navy H | cream U | cream H | navy U | navy H | cream U | cream H | navy U
```

- One directive per line: `name:`, `palette:`, `ends:` (each required, each
  once). Blank lines and `#` comments are welcome.
- `palette:` entries are `<color> <#hex>`, comma separated. No spaces inside
  a color name (yet).
- `ends:` entries are `<color> <H|U>`, pipe separated. Lowercase `h`/`u` work.

## Validation rules (enforced after parsing)

1. Palette hex values must look like `#rrggbb`.
2. Every end's color must exist in the palette; unknown colors are reported
   with the palette keys you do have.
3. Heddled and open ends must alternate — that alternation *is* the inkle
   structure.
4. A band needs at least 8 ends (two cards under Mapping B).

All problems are reported at once, each with its line number (text) or key
and position (JSON), so you can fix a draft in one pass.


## Importing from photos (v0.2)

Two CLI commands read photos (Pillow required):

### `inkletocard palette PHOTO [--colors N] [--match DRAFT] [-o palette.json]`

Extracts the dominant colors of a yarn or fabric photo by adaptive
quantization, names each after its nearest common color (deduplicated with
`-2`, `-3` suffixes), and prints a `palette:` line you can paste straight
into a text draft. With `--match DRAFT`, each photo color is snapped to the
nearest color of that draft's palette - "close" means within 90 RGB
distance (a tunable constant, `photo._CLOSE_MATCH`) - and palette colors the
photo never shows are listed at the end.

### `inkletocard import-grid PHOTO --cols N [--name NAME] [--save-draft FILE]`

Reads a photo of a 2-row draft chart:

- Top row = heddled ends, bottom row = open ends; warp order runs top then
  bottom per column (end 1 = top column 1, end 2 = bottom column 1) - the
  standard inkle draft reading order, so 2 x cols ends in total.
- Each cell is sampled over its central half, so grid lines are ignored;
  uniform photo borders peel automatically (up to 25% per side - crop close
  to the grid if its edge cells match the page background).
- Cells cluster into at most 12 distinct colors; each becomes a palette
  entry, named after its nearest common color.
- The imported draft runs through the same validation as any other draft
  before the conversion pipeline takes over.
