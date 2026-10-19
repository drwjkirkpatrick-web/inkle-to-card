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
  - `"ends": [{"color": "navy", "heddled": true}, ...]` — full control;
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
