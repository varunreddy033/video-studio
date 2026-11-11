# Icon packs in assets/library/icons

Written by tools/import_icon_packs.py. Only packs whose licence is on the allow-list are imported: MIT,
Apache-2.0, ISC, CC0, public domain; CC BY 4.0 only with ALLOW_CC_BY=1 in .env (credit line added to the
video description automatically). Skipped on purpose: OpenMoji (CC BY-SA 4.0), brand logos, anything
without a clear licence file. Emoji keywords for the search index: emojilib 4.0.3 (MIT) and
unicode-emoji-json 0.9.0 (MIT). Search model: sentence-transformers/all-MiniLM-L6-v2 (Apache-2.0).

| Id | Pack | Icons | Licence | Author | Upstream | Imported from | Credit in the video | Licence file |
|---|---|---|---|---|---|---|---|---|
| fluent_flat | Fluent Emoji Flat | 1,594 | MIT | Microsoft Corporation | https://github.com/microsoft/fluentui-emoji | @iconify-json/fluent-emoji-flat@1.2.6 | not required | icons/fluent_flat/LICENCE |
| fluent_color | Fluent Emoji Color | 1,590 | MIT | Microsoft Corporation | https://github.com/microsoft/fluentui-emoji | @iconify-json/fluent-emoji@1.2.7 | not required | icons/fluent_color/LICENCE |
| noto | Noto Emoji | 1,680 | Apache-2.0 | Google Inc | https://github.com/googlefonts/noto-emoji | @iconify-json/noto@1.2.7 | not required | icons/noto/LICENCE |
| phosphor | Phosphor Icons (fill + duotone) | 3,024 | MIT | Phosphor Icons | https://github.com/phosphor-icons/core | @iconify-json/ph@1.2.2 | not required | icons/phosphor/LICENCE |
| tabler | Tabler Icons | 6,287 | MIT | Paweł Kuna | https://github.com/tabler/tabler-icons | @iconify-json/tabler@1.2.44 | not required | icons/tabler/LICENCE |
| flags | Flag Icons | 271 | MIT | Panayiotis Lipiridis | https://github.com/lipis/flag-icons | @iconify-json/flag@1.2.15 | not required | icons/flags/LICENCE |
| natural_earth | Natural Earth country shapes (1:110m) | 176 | public-domain | Natural Earth | https://www.naturalearthdata.com | Natural Earth 1:110m admin 0 countries (tools/make_worldmap.py) | not required | icons/natural_earth/LICENCE |
