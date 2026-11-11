# Icon packs in assets/library/icons

Written by tools/import_icon_packs.py. Only packs whose licence is on the allow-list are imported: MIT,
Apache-2.0, ISC, CC0, public domain; CC BY 4.0 only with ALLOW_CC_BY=1 in .env (credit line added to the
video description automatically). Skipped on purpose: OpenMoji (CC BY-SA 4.0), brand logos, anything
without a clear licence file. Emoji keywords for the search index: emojilib 4.0.3 (MIT) and
unicode-emoji-json 0.9.0 (MIT). Search model: sentence-transformers/all-MiniLM-L6-v2 (Apache-2.0).

Kinds: illustration = colour illustration / emoji (only role 'family' can be a video's main icon family),
flat = one-colour filled, line = one-colour stroke (small labels), flag, map. Brand / logo sets are never
imported and icon names with brand / logo in them are dropped (trademarks).

| Id | Pack | Kind | Role | Icons | Licence | Author | Upstream | Imported from | Credit in the video | Licence file |
|---|---|---|---|---|---|---|---|---|---|---|
| fluent_flat | Fluent Emoji Flat | illustration | family | 1,594 | MIT | Microsoft Corporation | https://github.com/microsoft/fluentui-emoji | @iconify-json/fluent-emoji-flat@1.2.6 | not required | icons/fluent_flat/LICENCE |
| fluent_color | Fluent Emoji Color | illustration | family | 1,590 | MIT | Microsoft Corporation | https://github.com/microsoft/fluentui-emoji | @iconify-json/fluent-emoji@1.2.7 | not required | icons/fluent_color/LICENCE |
| noto | Noto Emoji | illustration | family | 1,680 | Apache-2.0 | Google Inc | https://github.com/googlefonts/noto-emoji | @iconify-json/noto@1.2.7 | not required | icons/noto/LICENCE |
| phosphor | Phosphor Icons (fill + duotone) | flat | flat | 2,866 | MIT | Phosphor Icons | https://github.com/phosphor-icons/core | @iconify-json/ph@1.2.2 | not required | icons/phosphor/LICENCE |
| tabler | Tabler Icons | line | line | 5,874 | MIT | Paweł Kuna | https://github.com/tabler/tabler-icons | @iconify-json/tabler@1.2.44 | not required | icons/tabler/LICENCE |
| flags | Flag Icons | flag | flags | 271 | MIT | Panayiotis Lipiridis | https://github.com/lipis/flag-icons | @iconify-json/flag@1.2.15 | not required | icons/flags/LICENCE |
| natural_earth | Natural Earth country shapes (1:110m) | map | map | 176 | public-domain | Natural Earth | https://www.naturalearthdata.com | Natural Earth 1:110m admin 0 countries (tools/make_worldmap.py) | not required | icons/natural_earth/LICENCE |
| akar_icons | Akar Icons | line | line | 454 | MIT | Arturo Wibawa | https://github.com/artcoholic/akar-icons | @iconify-json/akar-icons@1.2.7 | not required | icons/akar_icons/LICENCE |
| andrsrxn | andrsrxn/icons | line | line | 2,772 | MIT | Andrés Raxón | https://github.com/andrsrxn/icons | @iconify-json/andrsrxn@1.2.4 | not required | icons/andrsrxn/LICENCE |
| ant_design | Ant Design Icons | flat | flat | 848 | MIT | HeskeyBaozi | https://github.com/ant-design/ant-design-icons | @iconify-json/ant-design@1.2.9 | not required | icons/ant_design/LICENCE |
| at_icons | @icons | flat | flat | 705 | MIT | Valentin Fossati | https://github.com/Voxybuns/at-icons | @iconify-json/at-icons@1.2.5 | not required | icons/at_icons/LICENCE |
| bi | Bootstrap Icons | flat | flat | 2,078 | MIT | The Bootstrap Authors | https://github.com/twbs/icons | @iconify-json/bi@1.2.7 | not required | icons/bi/LICENCE |
| bitcoin_icons | Bitcoin Icons | flat | flat | 330 | MIT | Bitcoin Design Community | https://github.com/BitcoinDesign/Bitcoin-Icons | @iconify-json/bitcoin-icons@1.2.5 | not required | icons/bitcoin_icons/LICENCE |
| boxicons | Boxicons | flat | flat | 3,768 | MIT | Boxicons | https://github.com/box-icons/boxicons-core | @iconify-json/boxicons@1.2.0 | not required | icons/boxicons/LICENCE |
| bx | BoxIcons v2 | flat | flat | 814 | MIT | Boxicons | https://github.com/box-icons/boxicons | @iconify-json/bx@1.2.3 | not required | icons/bx/LICENCE |
| bxs | BoxIcons v2 Solid | flat | flat | 665 | MIT | Boxicons | https://github.com/box-icons/boxicons | @iconify-json/bxs@1.2.3 | not required | icons/bxs/LICENCE |
| bytesize | Bytesize Icons | line | line | 101 | MIT | Dan Klammer | https://github.com/danklammer/bytesize-icons | @iconify-json/bytesize@1.2.2 | not required | icons/bytesize/LICENCE |
| carbon | Carbon | flat | flat | 2,595 | Apache-2.0 | IBM | https://github.com/carbon-design-system/carbon/tree/main/packages/icons | @iconify-json/carbon@1.2.30 | not required | icons/carbon/LICENCE |
| charm | Charm Icons | line | line | 261 | MIT | Jay Newey | https://github.com/jaynewey/charm-icons | @iconify-json/charm@1.2.3 | not required | icons/charm/LICENCE |
| cif | CoreUI Flags | flag | flags | 199 | CC0-1.0 | creativeLabs Łukasz Holeczek | https://github.com/coreui/coreui-icons | @iconify-json/cif@1.2.9 | not required | icons/cif/LICENCE |
| circle_flags | Circle Flags | flag | flags | 444 | MIT | HatScripts | https://github.com/HatScripts/circle-flags | @iconify-json/circle-flags@1.2.14 | not required | icons/circle_flags/LICENCE |
| clarity | Clarity | flat | flat | 1,103 | MIT | VMware | https://github.com/vmware/clarity | @iconify-json/clarity@1.2.4 | not required | icons/clarity/LICENCE |
| codex | CodeX Icons | line | line | 156 | MIT | CodeX | https://github.com/davidabou/icons | @iconify-json/codex@1.2.2 | not required | icons/codex/LICENCE |
| coolicons | coolicons | line | line | 19,830 | MIT | Kryston Schwarze | https://github.com/krystonschwarze/coolicons | @iconify-json/coolicons@1.2.3 | not required | icons/coolicons/LICENCE |
| cuida | Cuida Icons | flat | flat | 178 | Apache-2.0 | Sysvale | https://github.com/Sysvale/cuida-icons | @iconify-json/cuida@1.2.5 | not required | icons/cuida/LICENCE |
| dinkie_icons | Dinkie Icons | flat | flat | 1,194 | MIT | atelierAnchor | https://github.com/atelier-anchor/dinkie-icons | @iconify-json/dinkie-icons@1.2.0 | not required | icons/dinkie_icons/LICENCE |
| doodle_icons | Oreo Doodle Icons | line | line | 204 | MIT | Nicole Tang | https://github.com/oreo-design/doodle-icons | @iconify-json/doodle-icons@1.2.0 | not required | icons/doodle_icons/LICENCE |
| duo_icons | Duoicons | flat | flat | 91 | MIT | fernandcf | https://github.com/fazdiu/duo-icons | @iconify-json/duo-icons@1.2.2 | not required | icons/duo_icons/LICENCE |
| ei | Evil Icons | flat | flat | 70 | MIT | Alexander Madyankin and Roman Shamin | https://github.com/evil-icons/evil-icons | @iconify-json/ei@1.2.2 | not required | icons/ei/LICENCE |
| energy_icons | Energy Icons | flat | flat | 8,252 | MIT | Sam Passmore | https://github.com/Sam-r-passmore/energy-icons | @iconify-json/energy-icons@1.2.4 | not required | icons/energy_icons/LICENCE |
| eos_icons | EOS Icons | flat | flat | 253 | MIT | SUSE UX/UI team | https://gitlab.com/SUSE-UIUX/eos-icons | @iconify-json/eos-icons@1.2.4 | not required | icons/eos_icons/LICENCE |
| ep | Element Plus | flat | flat | 293 | MIT | Element Plus | https://github.com/element-plus/element-plus-icons | @iconify-json/ep@1.2.4 | not required | icons/ep/LICENCE |
| eva | Eva Icons | flat | flat | 490 | MIT | Akveo | https://github.com/akveo/eva-icons/ | @iconify-json/eva@1.2.3 | not required | icons/eva/LICENCE |
| f7 | Framework7 Icons | flat | flat | 1,236 | MIT | Vladimir Kharlampidi | https://github.com/framework7io/framework7-icons | @iconify-json/f7@1.2.2 | not required | icons/f7/LICENCE |
| famicons | Famicons | flat | flat | 1,248 | MIT | Family | https://github.com/familyjs/famicons | @iconify-json/famicons@1.2.2 | not required | icons/famicons/LICENCE |
| fe | Feather Icon | flat | flat | 255 | MIT | Megumi Hano | https://github.com/feathericon/feathericon | @iconify-json/fe@1.2.4 | not required | icons/fe/LICENCE |
| feather | Feather Icons | line | line | 286 | MIT | Cole Bemis | https://github.com/feathericons/feather | @iconify-json/feather@1.2.1 | not required | icons/feather/LICENCE |
| flagpack | Flagpack | flag | flags | 254 | MIT | Yummygum | https://github.com/Yummygum/flagpack-core | @iconify-json/flagpack@1.2.10 | not required | icons/flagpack/LICENCE |
| flat_color_icons | Flat Color Icons | illustration | illustration | 326 | MIT | Icons8 | https://github.com/icons8/flat-Color-icons | @iconify-json/flat-color-icons@1.2.3 | not required | icons/flat_color_icons/LICENCE |
| flat_ui | Flat UI Icons | illustration | illustration | 100 | MIT | Designmodo, Inc. | https://github.com/designmodo/Flat-UI | @iconify-json/flat-ui@1.2.3 | not required | icons/flat_ui/LICENCE |
| flowbite | Flowbite Icons | line | line | 751 | MIT | Themesberg | https://github.com/themesberg/flowbite-icons | @iconify-json/flowbite@1.2.7 | not required | icons/flowbite/LICENCE |
| fluent | Fluent UI System Icons | flat | flat | 19,945 | MIT | Microsoft Corporation | https://github.com/microsoft/fluentui-system-icons | @iconify-json/fluent@1.2.61 | not required | icons/fluent/LICENCE |
| fluent_ui_color | Fluent UI System Color Icons | illustration | illustration | 890 | MIT | Microsoft Corporation | https://github.com/microsoft/fluentui-system-icons | @iconify-json/fluent-color@1.2.21 | not required | icons/fluent_ui_color/LICENCE |
| fluent_emoji_high_contrast | Fluent Emoji High Contrast | flat | flat | 1,594 | MIT | Microsoft Corporation | https://github.com/microsoft/fluentui-emoji | @iconify-json/fluent-emoji-high-contrast@1.2.6 | not required | icons/fluent_emoji_high_contrast/LICENCE |
| fluent_mdl2 | Fluent UI MDL2 | flat | flat | 1,695 | MIT | Microsoft Corporation | https://github.com/microsoft/fluentui/tree/master/packages/react-icons-mdl2 | @iconify-json/fluent-mdl2@1.2.1 | not required | icons/fluent_mdl2/LICENCE |
| fontisto | Fontisto | flat | flat | 614 | MIT | Kenan Gündoğan | https://github.com/kenangundogan/fontisto | @iconify-json/fontisto@1.2.1 | not required | icons/fontisto/LICENCE |
| formkit | FormKit Icons | flat | flat | 144 | MIT | FormKit, Inc | https://github.com/formkit/formkit/tree/master/packages/icons | @iconify-json/formkit@1.2.2 | not required | icons/formkit/LICENCE |
| foundation | Foundation | flat | flat | 283 | MIT | Zurb | https://github.com/zurb/foundation-icon-fonts | @iconify-json/foundation@1.2.1 | not required | icons/foundation/LICENCE |
| fxemoji | Firefox OS Emoji | illustration | family | 1,034 | Apache-2.0 | Mozilla | https://github.com/mozilla/fxemoji | @iconify-json/fxemoji@1.2.2 | not required | icons/fxemoji/LICENCE |
| garden | Garden SVG Icons | flat | flat | 1,478 | Apache-2.0 | Zendesk | https://github.com/zendeskgarden/svg-icons | @iconify-json/garden@1.2.8 | not required | icons/garden/LICENCE |
| geo | GeoGlyphs | flat | flat | 30 | MIT | Sam Matthews | https://github.com/cugos/geoglyphs | @iconify-json/geo@1.2.3 | not required | icons/geo/LICENCE |
| gg | css.gg | flat | flat | 704 | MIT | Astrit | https://github.com/astrit/css.gg | @iconify-json/gg@1.2.2 | not required | icons/gg/LICENCE |
| ginetex | Ginetex Care Symbols | flat | flat | 50 | MIT | YESSIR Organization | https://github.com/yessir-web-tech/ginetex-icons | @iconify-json/ginetex@1.2.0 | not required | icons/ginetex/LICENCE |
| glyphs | Glyphs | flat | flat | 3,452 | MIT | Goran Spasojevic | https://github.com/gorango/glyphs | @iconify-json/glyphs@1.2.0 | not required | icons/glyphs/LICENCE |
| glyphs_poly | Glyphs Poly | illustration | illustration | 863 | MIT | Goran Spasojevic | https://github.com/gorango/glyphs | @iconify-json/glyphs-poly@1.2.0 | not required | icons/glyphs_poly/LICENCE |
| gravity_ui | Gravity UI Icons | flat | flat | 774 | MIT | YANDEX LLC | https://github.com/gravity-ui/icons/ | @iconify-json/gravity-ui@1.2.15 | not required | icons/gravity_ui/LICENCE |
| griddy_icons | Griddy Icons | flat | flat | 2,010 | MIT | Zuzana Benova | https://github.com/griddy-icons/griddy-icons | @iconify-json/griddy-icons@1.2.0 | not required | icons/griddy_icons/LICENCE |
| grommet_icons | Grommet Icons | line | line | 636 | Apache-2.0 | Grommet | https://github.com/grommet/grommet-icons | @iconify-json/grommet-icons@1.2.4 | not required | icons/grommet_icons/LICENCE |
| healthicons | Health Icons | flat | flat | 2,114 | MIT | Resolve to Save Lives | https://github.com/resolvetosavelives/healthicons | @iconify-json/healthicons@1.2.18 | not required | icons/healthicons/LICENCE |
| heroicons | HeroIcons | flat | flat | 1,288 | MIT | Refactoring UI Inc | https://github.com/tailwindlabs/heroicons | @iconify-json/heroicons@1.2.3 | not required | icons/heroicons/LICENCE |
| heroicons_outline | HeroIcons v1 Outline | line | line | 230 | MIT | Refactoring UI Inc | https://github.com/tailwindlabs/heroicons | @iconify-json/heroicons-outline@1.2.1 | not required | icons/heroicons_outline/LICENCE |
| heroicons_solid | HeroIcons v1 Solid | flat | flat | 230 | MIT | Refactoring UI Inc | https://github.com/tailwindlabs/heroicons | @iconify-json/heroicons-solid@1.2.1 | not required | icons/heroicons_solid/LICENCE |
| hugeicons | Huge Icons | line | line | 6,064 | MIT | Hugeicons | https://icon-sets.iconify.design/icon-sets/hugeicons/ | @iconify-json/hugeicons@1.2.35 | not required | icons/hugeicons/LICENCE |
| humbleicons | Humbleicons | line | line | 277 | MIT | Jiří Zralý | https://github.com/zraly/humbleicons | @iconify-json/humbleicons@1.2.20 | not required | icons/humbleicons/LICENCE |
| ic | Google Material Icons | flat | flat | 10,950 | Apache-2.0 | Material Design Authors | https://github.com/material-icons/material-icons | @iconify-json/ic@1.2.4 | not required | icons/ic/LICENCE |
| icon_park | IconPark | illustration | family | 2,657 | Apache-2.0 | ByteDance | https://github.com/bytedance/IconPark | @iconify-json/icon-park@1.2.4 | not required | icons/icon_park/LICENCE |
| icon_park_outline | IconPark Outline | line | line | 2,657 | Apache-2.0 | ByteDance | https://github.com/bytedance/IconPark | @iconify-json/icon-park-outline@1.2.4 | not required | icons/icon_park_outline/LICENCE |
| icon_park_solid | IconPark Solid | line | line | 1,946 | Apache-2.0 | ByteDance | https://github.com/bytedance/IconPark | @iconify-json/icon-park-solid@1.2.4 | not required | icons/icon_park_solid/LICENCE |
| icon_park_twotone | IconPark TwoTone | line | line | 1,943 | Apache-2.0 | ByteDance | https://github.com/bytedance/IconPark | @iconify-json/icon-park-twotone@1.2.4 | not required | icons/icon_park_twotone/LICENCE |
| iconito | Iconito Food | illustration | illustration | 120 | MIT | Iconito | https://github.com/iconi-to/free-food | @iconify-json/iconito@1.2.0 | not required | icons/iconito/LICENCE |
| iconmind | IconMind | line | line | 31,722 | MIT | IconMind | https://github.com/Iconmind/iconmind | @iconify-json/iconmind@1.2.2 | not required | icons/iconmind/LICENCE |
| iconoir | Iconoir | line | line | 1,671 | MIT | Luca Burgio | https://github.com/iconoir-icons/iconoir | @iconify-json/iconoir@1.2.12 | not required | icons/iconoir/LICENCE |
| iconoven | IconOven | line | line | 18,232 | MIT | Appic Marketing | https://iconoven.com/icons | @iconify-json/iconoven@1.2.1 | not required | icons/iconoven/LICENCE |
| icons8 | Icons8 Windows 10 Icons | flat | flat | 234 | MIT | Icons8 | https://github.com/icons8/windows-10-icons | @iconify-json/icons8@1.2.1 | not required | icons/icons8/LICENCE |
| il | Icalicons | flat | flat | 84 | MIT | Icalia Labs |  | @iconify-json/il@1.2.2 | not required | icons/il/LICENCE |
| ion | IonIcons | flat | flat | 1,263 | MIT | Ben Sperry | https://github.com/ionic-team/ionicons | @iconify-json/ion@1.2.7 | not required | icons/ion/LICENCE |
| iwwa | Innowatio Font | flat | flat | 104 | Apache-2.0 | Innowatio | https://github.com/innowatio/iwwa-icons | @iconify-json/iwwa@1.2.1 | not required | icons/iwwa/LICENCE |
| ix | Siemens Industrial Experience Icons | flat | flat | 1,475 | MIT | Siemens AG | https://github.com/siemens/ix-icons | @iconify-json/ix@1.2.14 | not required | icons/ix/LICENCE |
| jam | Jam Icons | flat | flat | 940 | MIT | Michael Amprimo | https://github.com/michaelampr | @iconify-json/jam@1.2.3 | not required | icons/jam/LICENCE |
| keyline_icons | Keyline Icons | line | line | 14,664 | MIT | Keyline Icons | https://github.com/keyline-icons/keyline-icons | @iconify-json/keyline-icons@1.2.21 | not required | icons/keyline_icons/LICENCE |
| la | Line Awesome | flat | flat | 1,544 | Apache-2.0 | Icons8 | https://github.com/icons8/line-awesome | @iconify-json/la@1.2.1 | not required | icons/la/LICENCE |
| line_md | Material Line Icons | line | line | 1,218 | MIT | Vjacheslav Trushkin | https://github.com/cyberalien/line-md | @iconify-json/line-md@1.2.16 | not required | icons/line_md/LICENCE |
| lineicons | Lineicons | flat | flat | 600 | MIT | Lineicons | https://github.com/LineiconsHQ/Lineicons | @iconify-json/lineicons@1.2.6 | not required | icons/lineicons/LICENCE |
| lsicon | Lsicon | flat | flat | 716 | MIT | Wis Design | https://www.lsicon.com/ | @iconify-json/lsicon@1.2.5 | not required | icons/lsicon/LICENCE |
| lucide | Lucide | line | line | 2,046 | ISC | Lucide Contributors | https://github.com/lucide-icons/lucide | @iconify-json/lucide@1.2.153 | not required | icons/lucide/LICENCE |
| lucide_extended | Lucide Extended | line | line | 2,900 | ISC | Applifted | https://github.com/applifted/lucide-extended | @iconify-json/lucide-extended@1.2.4 | not required | icons/lucide_extended/LICENCE |
| lucide_lab | Lucide Lab | line | line | 373 | ISC | Lucide Contributors | https://github.com/lucide-icons/lucide-lab | @iconify-json/lucide-lab@1.2.3 | not required | icons/lucide_lab/LICENCE |
| mage | Mage Icons | line | line | 1,042 | Apache-2.0 | MageIcons | https://github.com/Mage-Icons/mage-icons | @iconify-json/mage@1.2.4 | not required | icons/mage/LICENCE |
| majesticons | Majesticons | line | line | 760 | MIT | Gerrit Halfmann | https://github.com/halfmage/majesticons | @iconify-json/majesticons@1.2.5 | not required | icons/majesticons/LICENCE |
| maki | Maki | flat | flat | 215 | CC0-1.0 | Mapbox | https://github.com/mapbox/maki | @iconify-json/maki@1.2.6 | not required | icons/maki/LICENCE |
| marketeq | Marketeq | illustration | illustration | 590 | MIT | Marketeq |  | @iconify-json/marketeq@1.2.2 | not required | icons/marketeq/LICENCE |
| material_symbols | Material Symbols | flat | flat | 15,764 | Apache-2.0 | Google | https://github.com/google/material-design-icons | @iconify-json/material-symbols@1.2.98 | not required | icons/material_symbols/LICENCE |
| material_symbols_light | Material Symbols Light | flat | flat | 15,829 | Apache-2.0 | Google | https://github.com/google/material-design-icons | @iconify-json/material-symbols-light@1.2.100 | not required | icons/material_symbols_light/LICENCE |
| matita | Matita | line | line | 383 | MIT | matita.dev | https://github.com/matita-dev/icons | @iconify-json/matita@1.2.4 | not required | icons/matita/LICENCE |
| mdi | Material Design Icons | flat | flat | 7,447 | Apache-2.0 | Pictogrammers | https://github.com/Templarian/MaterialDesign | @iconify-json/mdi@1.2.3 | not required | icons/mdi/LICENCE |
| medical_icon | Medical Icons | flat | flat | 144 | MIT | Samuel Frémondière | https://github.com/samcome/webfont-medical-icons | @iconify-json/medical-icon@1.2.0 | not required | icons/medical_icon/LICENCE |
| memory | Memory Icons | flat | flat | 651 | Apache-2.0 | Pictogrammers | https://github.com/Pictogrammers/Memory | @iconify-json/memory@1.2.2 | not required | icons/memory/LICENCE |
| meteocons | Meteocons | illustration | illustration | 447 | MIT | Bas Milius | https://github.com/basmilius/weather-icons | @iconify-json/meteocons@1.2.5 | not required | icons/meteocons/LICENCE |
| meteor_icons | Meteor Icons | line | line | 409 | MIT | zkreations | https://github.com/zkreations/icons | @iconify-json/meteor-icons@1.2.10 | not required | icons/meteor_icons/LICENCE |
| mi | Mono Icons | flat | flat | 180 | MIT | Mono | https://github.com/mono-company/mono-icons | @iconify-json/mi@1.2.2 | not required | icons/mi/LICENCE |
| mingcute | MingCute Icon | flat | flat | 4,526 | Apache-2.0 | MingCute Design | https://github.com/Richard9394/MingCute | @iconify-json/mingcute@1.2.10 | not required | icons/mingcute/LICENCE |
| mono_icons | Mono Icons | flat | flat | 180 | MIT | Mono | https://github.com/mono-company/mono-icons | @iconify-json/mono-icons@1.2.0 | not required | icons/mono_icons/LICENCE |
| mynaui | Myna UI Icons | line | line | 2,620 | MIT | Praveen Juge | https://github.com/praveenjuge/mynaui-icons | @iconify-json/mynaui@1.2.19 | not required | icons/mynaui/LICENCE |
| nimbus | Nimbus | flat | flat | 140 | MIT | Linkedstore S.A. | https://github.com/cyberalien/nimbus-icons | @iconify-json/nimbus@1.2.1 | not required | icons/nimbus/LICENCE |
| noto_v1 | Noto Emoji (v1) | illustration | family | 2,162 | Apache-2.0 | Google Inc | https://github.com/googlefonts/noto-emoji | @iconify-json/noto-v1@1.2.5 | not required | icons/noto_v1/LICENCE |
| octicon | Octicons | flat | flat | 776 | MIT | GitHub | https://github.com/primer/octicons/ | @iconify-json/octicon@1.2.40 | not required | icons/octicon/LICENCE |
| oi | Open Iconic | flat | flat | 223 | MIT | Iconic | https://github.com/iconic/open-iconic | @iconify-json/oi@1.2.1 | not required | icons/oi/LICENCE |
| ooui | OOUI | flat | flat | 403 | MIT | OOUI Team | https://github.com/wikimedia/oojs-ui | @iconify-json/ooui@1.2.25 | not required | icons/ooui/LICENCE |
| osmic | OSM Icons | flat | flat | 169 | CC0-1.0 | GMGeo | https://github.com/gmgeo/osmic | @iconify-json/osmic@1.2.1 | not required | icons/osmic/LICENCE |
| oui | OpenSearch UI | flat | flat | 437 | Apache-2.0 | OpenSearch Contributors | https://github.com/opensearch-project/oui | @iconify-json/oui@1.2.6 | not required | icons/oui/LICENCE |
| pajamas | Gitlab SVGs | flat | flat | 409 | MIT | GitLab B.V. | https://gitlab.com/gitlab-org/gitlab-svgs/-/tree/main | @iconify-json/pajamas@1.2.15 | not required | icons/pajamas/LICENCE |
| pinhead | Pinhead Map Icons | flat | flat | 2,845 | CC0-1.0 | Quincy Morgan | https://github.com/waysidemapping/pinhead | @iconify-json/pinhead@1.2.41 | not required | icons/pinhead/LICENCE |
| pixelarticons | Pixelarticons | flat | flat | 1,036 | MIT | Gerrit Halfmann | https://github.com/halfmage/pixelarticons | @iconify-json/pixelarticons@1.2.10 | not required | icons/pixelarticons/LICENCE |
| prime | Prime Icons | flat | flat | 313 | MIT | PrimeTek | https://github.com/primefaces/primeicons | @iconify-json/prime@1.2.5 | not required | icons/prime/LICENCE |
| proicons | ProIcons | line | line | 544 | MIT | ProCode | https://github.com/ProCode-Software/proicons | @iconify-json/proicons@1.2.21 | not required | icons/proicons/LICENCE |
| qlementine_icons | Qlementine Icons | flat | flat | 905 | MIT | Olivier Cléro | https://github.com/oclero/qlementine-icons | @iconify-json/qlementine-icons@1.2.16 | not required | icons/qlementine_icons/LICENCE |
| quill | Quill Icons | line | line | 140 | MIT | Casper Lourens | https://www.figma.com/community/file/1034432054377533052/Quill-Iconset | @iconify-json/quill@1.2.4 | not required | icons/quill/LICENCE |
| radix_icons | Radix Icons | flat | flat | 318 | MIT | WorkOS | https://github.com/radix-ui/icons | @iconify-json/radix-icons@1.2.6 | not required | icons/radix_icons/LICENCE |
| raphael | Raphael | flat | flat | 266 | MIT | Dmitry Baranovskiy | https://github.com/dmitrybaranovskiy/raphael | @iconify-json/raphael@1.2.1 | not required | icons/raphael/LICENCE |
| reicon | Reicon | flat | flat | 6,590 | MIT | REICON | https://github.com/dqev/reicon | @iconify-json/reicon@1.2.6 | not required | icons/reicon/LICENCE |
| ri | Remix Icon | flat | flat | 3,188 | Apache-2.0 | Remix Design | https://github.com/cyberalien/RemixIcon | @iconify-json/ri@1.2.10 | not required | icons/ri/LICENCE |
| si | Sargam Icons | line | line | 1,299 | MIT | Abhimanyu Rana | https://github.com/planetabhi/sargam-icons | @iconify-json/si@1.2.17 | not required | icons/si/LICENCE |
| sidekickicons | SidekickIcons | flat | flat | 644 | MIT | Andri Soone | https://github.com/ndri/sidekickicons | @iconify-json/sidekickicons@1.2.7 | not required | icons/sidekickicons/LICENCE |
| simple_line_icons | Simple line icons | flat | flat | 189 | MIT | Sabbir Ahmed | https://github.com/thesabbir/simple-line-icons | @iconify-json/simple-line-icons@1.2.1 | not required | icons/simple_line_icons/LICENCE |
| stash | Stash Icons | flat | flat | 982 | MIT | Pingback LLC | https://github.com/stash-ui/icons | @iconify-json/stash@1.2.4 | not required | icons/stash/LICENCE |
| struq | Struq Icons | line | line | 300 | MIT | Struq | https://struq.nl/iconen | @iconify-json/struq@1.2.0 | not required | icons/struq/LICENCE |
| svg_spinners | SVG Spinners | flat | flat | 46 | MIT | Utkarsh Verma | https://github.com/n3r4zzurr0/svg-spinners | @iconify-json/svg-spinners@1.2.4 | not required | icons/svg_spinners/LICENCE |
| tabler_flags | Tabler Flags | flag | flags | 297 | MIT | Paweł Kuna | https://github.com/tabler/tabler-flags | @iconify-json/tabler-flags@1.2.2 | not required | icons/tabler_flags/LICENCE |
| tdesign | TDesign Icons | line | line | 2,282 | MIT | TDesign | https://github.com/Tencent/tdesign-icons | @iconify-json/tdesign@1.2.20 | not required | icons/tdesign/LICENCE |
| teenyicons | Teenyicons | flat | flat | 1,200 | MIT | smhmd | https://github.com/teenyicons/teenyicons | @iconify-json/teenyicons@1.2.2 | not required | icons/teenyicons/LICENCE |
| temaki | Temaki | flat | flat | 557 | CC0-1.0 | Bryan Housel | https://github.com/rapideditor/temaki | @iconify-json/temaki@1.2.7 | not required | icons/temaki/LICENCE |
| topcoat | TopCoat Icons | flat | flat | 89 | Apache-2.0 | TopCoat | https://github.com/topcoat/icons | @iconify-json/topcoat@1.2.0 | not required | icons/topcoat/LICENCE |
| uil | Unicons | flat | flat | 1,215 | Apache-2.0 | Iconscout | https://github.com/Iconscout/unicons | @iconify-json/uil@1.2.3 | not required | icons/uil/LICENCE |
| uim | Unicons Monochrome | flat | flat | 298 | Apache-2.0 | Iconscout | https://github.com/Iconscout/unicons | @iconify-json/uim@1.2.3 | not required | icons/uim/LICENCE |
| uis | Unicons Solid | flat | flat | 190 | Apache-2.0 | Iconscout | https://github.com/Iconscout/unicons | @iconify-json/uis@1.2.3 | not required | icons/uis/LICENCE |
| uit | Unicons Thin Line | flat | flat | 215 | Apache-2.0 | Iconscout | https://github.com/Iconscout/unicons | @iconify-json/uit@1.2.3 | not required | icons/uit/LICENCE |
| uiw | uiw icons | flat | flat | 214 | MIT | liwen0526 | https://github.com/uiwjs/icons | @iconify-json/uiw@1.2.4 | not required | icons/uiw/LICENCE |
| vaadin | Vaadin Icons | flat | flat | 636 | Apache-2.0 | Vaadin | https://github.com/vaadin/web-components | @iconify-json/vaadin@1.2.1 | not required | icons/vaadin/LICENCE |
| vadivam | Vadivam | line | line | 2,020 | MIT | Praveen Juge | https://github.com/praveenjuge/vadivam | @iconify-json/vadivam@1.2.8 | not required | icons/vadivam/LICENCE |
| weui | WeUI Icon | flat | flat | 162 | MIT | WeUI | https://github.com/weui/weui-icon | @iconify-json/weui@1.2.4 | not required | icons/weui/LICENCE |
| withicons | with icons | line | line | 7,000 | MIT | Evergrow | https://github.com/withevergrow/withicons | @iconify-json/withicons@1.2.3 | not required | icons/withicons/LICENCE |
| withicons_anime | with icons Anime | illustration | family | 1,000 | MIT | Evergrow | https://github.com/withevergrow/withicons | @iconify-json/withicons-anime@1.2.1 | not required | icons/withicons_anime/LICENCE |
| withicons_bauhaus | with icons Bauhaus | illustration | family | 1,000 | MIT | Evergrow | https://github.com/withevergrow/withicons | @iconify-json/withicons-bauhaus@1.2.0 | not required | icons/withicons_bauhaus/LICENCE |
| withicons_bento | with icons Bento | illustration | family | 1,000 | MIT | Evergrow | https://github.com/withevergrow/withicons | @iconify-json/withicons-bento@1.2.0 | not required | icons/withicons_bento/LICENCE |
| withicons_brutal | with icons Brutal | illustration | family | 1,000 | MIT | Evergrow | https://github.com/withevergrow/withicons | @iconify-json/withicons-brutal@1.2.0 | not required | icons/withicons_brutal/LICENCE |
| withicons_christmas | with icons Christmas | illustration | illustration | 1,000 | MIT | Evergrow | https://github.com/withevergrow/withicons | @iconify-json/withicons-christmas@1.2.1 | not required | icons/withicons_christmas/LICENCE |
| withicons_chrome | with icons Chrome | illustration | family | 1,000 | MIT | Evergrow | https://github.com/withevergrow/withicons | @iconify-json/withicons-chrome@1.2.0 | not required | icons/withicons_chrome/LICENCE |
| withicons_clay | with icons Clay | illustration | family | 1,000 | MIT | Evergrow | https://github.com/withevergrow/withicons | @iconify-json/withicons-clay@1.2.0 | not required | icons/withicons_clay/LICENCE |
| withicons_coquette | with icons Coquette | illustration | family | 1,000 | MIT | Evergrow | https://github.com/withevergrow/withicons | @iconify-json/withicons-coquette@1.2.0 | not required | icons/withicons_coquette/LICENCE |
| withicons_dock | with icons Dock | illustration | family | 1,000 | MIT | Evergrow | https://github.com/withevergrow/withicons | @iconify-json/withicons-dock@1.2.0 | not required | icons/withicons_dock/LICENCE |
| withicons_glass | with icons Glass | illustration | family | 1,000 | MIT | Evergrow | https://github.com/withevergrow/withicons | @iconify-json/withicons-glass@1.2.0 | not required | icons/withicons_glass/LICENCE |
| withicons_gothic | with icons Gothic | illustration | family | 1,000 | MIT | Evergrow | https://github.com/withevergrow/withicons | @iconify-json/withicons-gothic@1.2.1 | not required | icons/withicons_gothic/LICENCE |
| withicons_halloween | with icons Halloween | illustration | illustration | 1,000 | MIT | Evergrow | https://github.com/withevergrow/withicons | @iconify-json/withicons-halloween@1.2.1 | not required | icons/withicons_halloween/LICENCE |
| withicons_kawaii | with icons Kawaii | illustration | family | 1,000 | MIT | Evergrow | https://github.com/withevergrow/withicons | @iconify-json/withicons-kawaii@1.2.0 | not required | icons/withicons_kawaii/LICENCE |
| withicons_liquid | with icons Liquid | illustration | family | 1,000 | MIT | Evergrow | https://github.com/withevergrow/withicons | @iconify-json/withicons-liquid@1.2.0 | not required | icons/withicons_liquid/LICENCE |
| withicons_lunar | with icons Cunar | illustration | illustration | 1,000 | MIT | Evergrow | https://github.com/withevergrow/withicons | @iconify-json/withicons-lunar@1.2.0 | not required | icons/withicons_lunar/LICENCE |
| withicons_luxe | with icons Luxe | illustration | family | 1,000 | MIT | Evergrow | https://github.com/withevergrow/withicons | @iconify-json/withicons-luxe@1.2.0 | not required | icons/withicons_luxe/LICENCE |
| withicons_pastel | with icons Pastel | illustration | family | 1,000 | MIT | Evergrow | https://github.com/withevergrow/withicons | @iconify-json/withicons-pastel@1.2.0 | not required | icons/withicons_pastel/LICENCE |
| withicons_plush | with icons Plush | illustration | family | 1,000 | MIT | Evergrow | https://github.com/withevergrow/withicons | @iconify-json/withicons-plush@1.2.0 | not required | icons/withicons_plush/LICENCE |
| withicons_rangoli | with icons Rangoli | illustration | illustration | 1,000 | MIT | Evergrow | https://github.com/withevergrow/withicons | @iconify-json/withicons-rangoli@1.2.0 | not required | icons/withicons_rangoli/LICENCE |
| withicons_retro | with icons Retro | illustration | family | 1,000 | MIT | Evergrow | https://github.com/withevergrow/withicons | @iconify-json/withicons-retro@1.2.0 | not required | icons/withicons_retro/LICENCE |
| withicons_skeuo | with icons Skeuo | illustration | family | 1,000 | MIT | Evergrow | https://github.com/withevergrow/withicons | @iconify-json/withicons-skeuo@1.2.0 | not required | icons/withicons_skeuo/LICENCE |
| withicons_soft3d | with icons Soft 3D | illustration | family | 1,000 | MIT | Evergrow | https://github.com/withevergrow/withicons | @iconify-json/withicons-soft3d@1.2.0 | not required | icons/withicons_soft3d/LICENCE |
| withicons_sticker | with icons Sticker | illustration | family | 1,000 | MIT | Evergrow | https://github.com/withevergrow/withicons | @iconify-json/withicons-sticker@1.2.0 | not required | icons/withicons_sticker/LICENCE |
| withicons_suite | with icons Suite | illustration | family | 1,000 | MIT | Evergrow | https://github.com/withevergrow/withicons | @iconify-json/withicons-suite@1.2.0 | not required | icons/withicons_suite/LICENCE |
| withicons_utsav | with icons Utsav | illustration | illustration | 1,000 | MIT | Evergrow | https://github.com/withevergrow/withicons | @iconify-json/withicons-utsav@1.2.0 | not required | icons/withicons_utsav/LICENCE |
| withicons_valentine | with icons Valentine | illustration | illustration | 1,000 | MIT | Evergrow | https://github.com/withevergrow/withicons | @iconify-json/withicons-valentine@1.2.0 | not required | icons/withicons_valentine/LICENCE |
| wpf | Icons8 Windows 8 Icons | flat | flat | 200 | MIT | Icons8 | https://github.com/icons8/WPF-UI-Framework | @iconify-json/wpf@1.2.0 | not required | icons/wpf/LICENCE |
| zondicons | Zondicons | flat | flat | 297 | MIT | Steve Schoger | https://github.com/dukestreetstudio/zondicons | @iconify-json/zondicons@1.2.2 | not required | icons/zondicons/LICENCE |

## Refused Iconify sets (@iconify/json@2.2.555, tools/import_icon_packs.py --discover)

| Iconify set | Name | Icons | Licence | Why |
|---|---|---|---|---|
| basil | Basil | 493 | CC-BY-4.0 | CC BY 4.0: only with ALLOW_CC_BY=1 in .env (credit line then automatic) |
| ci | coolicons v4 | 442 | CC-BY-4.0 | CC BY 4.0: only with ALLOW_CC_BY=1 in .env (credit line then automatic) |
| cil | CoreUI Free | 554 | CC-BY-4.0 | CC BY 4.0: only with ALLOW_CC_BY=1 in .env (credit line then automatic) |
| covid | Covid Icons | 142 | CC-BY-4.0 | CC BY 4.0: only with ALLOW_CC_BY=1 in .env (credit line then automatic) |
| emojione | Emoji One (Colored) | 1,834 | CC-BY-4.0 | CC BY 4.0: only with ALLOW_CC_BY=1 in .env (credit line then automatic) |
| emojione-monotone | Emoji One (Monotone) | 1,403 | CC-BY-4.0 | CC BY 4.0: only with ALLOW_CC_BY=1 in .env (credit line then automatic) |
| fa6-regular | Font Awesome 6 Regular | 163 | CC-BY-4.0 | CC BY 4.0: only with ALLOW_CC_BY=1 in .env (credit line then automatic) |
| fa6-solid | Font Awesome 6 Solid | 1,402 | CC-BY-4.0 | CC BY 4.0: only with ALLOW_CC_BY=1 in .env (credit line then automatic) |
| fa7-regular | Font Awesome Regular | 272 | CC-BY-4.0 | CC BY 4.0: only with ALLOW_CC_BY=1 in .env (credit line then automatic) |
| fa7-solid | Font Awesome Solid | 2,000 | CC-BY-4.0 | CC BY 4.0: only with ALLOW_CC_BY=1 in .env (credit line then automatic) |
| fa-regular | Font Awesome 5 Regular | 151 | CC-BY-4.0 | CC BY 4.0: only with ALLOW_CC_BY=1 in .env (credit line then automatic) |
| fa-solid | Font Awesome 5 Solid | 1,001 | CC-BY-4.0 | CC BY 4.0: only with ALLOW_CC_BY=1 in .env (credit line then automatic) |
| fad | FontAudio | 155 | CC-BY-4.0 | CC BY 4.0: only with ALLOW_CC_BY=1 in .env (credit line then automatic) |
| gis | Font-GIS | 367 | CC-BY-4.0 | CC BY 4.0: only with ALLOW_CC_BY=1 in .env (credit line then automatic) |
| guidance | Guidance | 360 | CC-BY-4.0 | CC BY 4.0: only with ALLOW_CC_BY=1 in .env (credit line then automatic) |
| iconamoon | IconaMoon | 1,781 | CC-BY-4.0 | CC BY 4.0: only with ALLOW_CC_BY=1 in .env (credit line then automatic) |
| lets-icons | Lets Icons | 1,528 | CC-BY-4.0 | CC BY 4.0: only with ALLOW_CC_BY=1 in .env (credit line then automatic) |
| nrk | NRK Core Icons | 637 | CC-BY-4.0 | CC BY 4.0: only with ALLOW_CC_BY=1 in .env (credit line then automatic) |
| pepicons | Pepicons | 428 | CC-BY-4.0 | CC BY 4.0: only with ALLOW_CC_BY=1 in .env (credit line then automatic) |
| pepicons-pencil | Pepicons Pencil | 1,275 | CC-BY-4.0 | CC BY 4.0: only with ALLOW_CC_BY=1 in .env (credit line then automatic) |
| pepicons-pop | Pepicons Pop! | 1,275 | CC-BY-4.0 | CC BY 4.0: only with ALLOW_CC_BY=1 in .env (credit line then automatic) |
| pepicons-print | Pepicons Print | 1,275 | CC-BY-4.0 | CC BY 4.0: only with ALLOW_CC_BY=1 in .env (credit line then automatic) |
| pixel | Pixel Icon | 578 | CC-BY-4.0 | CC BY 4.0: only with ALLOW_CC_BY=1 in .env (credit line then automatic) |
| roentgen | Röntgen | 574 | CC-BY-4.0 | CC BY 4.0: only with ALLOW_CC_BY=1 in .env (credit line then automatic) |
| solar | Solar | 8,706 | CC-BY-4.0 | CC BY 4.0: only with ALLOW_CC_BY=1 in .env (credit line then automatic) |
| streamline | Streamline | 3,000 | CC-BY-4.0 | CC BY 4.0: only with ALLOW_CC_BY=1 in .env (credit line then automatic) |
| streamline-block | Streamline Block | 300 | CC-BY-4.0 | CC BY 4.0: only with ALLOW_CC_BY=1 in .env (credit line then automatic) |
| streamline-color | Streamline color | 2,000 | CC-BY-4.0 | CC BY 4.0: only with ALLOW_CC_BY=1 in .env (credit line then automatic) |
| streamline-cyber | Cyber free icons | 500 | CC-BY-4.0 | CC BY 4.0: only with ALLOW_CC_BY=1 in .env (credit line then automatic) |
| streamline-cyber-color | Cyber color icons | 500 | CC-BY-4.0 | CC BY 4.0: only with ALLOW_CC_BY=1 in .env (credit line then automatic) |
| streamline-emojis | Streamline Emojis | 787 | CC-BY-4.0 | CC BY 4.0: only with ALLOW_CC_BY=1 in .env (credit line then automatic) |
| streamline-flex | Flex free icons | 1,500 | CC-BY-4.0 | CC BY 4.0: only with ALLOW_CC_BY=1 in .env (credit line then automatic) |
| streamline-flex-color | Flex color icons | 1,000 | CC-BY-4.0 | CC BY 4.0: only with ALLOW_CC_BY=1 in .env (credit line then automatic) |
| streamline-freehand | Freehand free icons | 1,000 | CC-BY-4.0 | CC BY 4.0: only with ALLOW_CC_BY=1 in .env (credit line then automatic) |
| streamline-freehand-color | Freehand color icons | 1,000 | CC-BY-4.0 | CC BY 4.0: only with ALLOW_CC_BY=1 in .env (credit line then automatic) |
| streamline-kameleon-color | Kameleon color icons | 600 | CC-BY-4.0 | CC BY 4.0: only with ALLOW_CC_BY=1 in .env (credit line then automatic) |
| streamline-memes | Memes | 84 | CC-BY-4.0 | CC BY 4.0: only with ALLOW_CC_BY=1 in .env (credit line then automatic) |
| streamline-pixel | Pixel free icons | 662 | CC-BY-4.0 | CC BY 4.0: only with ALLOW_CC_BY=1 in .env (credit line then automatic) |
| streamline-plump | Plump free icons | 1,499 | CC-BY-4.0 | CC BY 4.0: only with ALLOW_CC_BY=1 in .env (credit line then automatic) |
| streamline-plump-color | Plump color icons | 1,000 | CC-BY-4.0 | CC BY 4.0: only with ALLOW_CC_BY=1 in .env (credit line then automatic) |
| streamline-sharp | Sharp free icons | 1,500 | CC-BY-4.0 | CC BY 4.0: only with ALLOW_CC_BY=1 in .env (credit line then automatic) |
| streamline-sharp-color | Sharp color icons | 1,000 | CC-BY-4.0 | CC BY 4.0: only with ALLOW_CC_BY=1 in .env (credit line then automatic) |
| streamline-stickies-color | Stickies color icons | 200 | CC-BY-4.0 | CC BY 4.0: only with ALLOW_CC_BY=1 in .env (credit line then automatic) |
| streamline-ultimate | Ultimate free icons | 1,999 | CC-BY-4.0 | CC BY 4.0: only with ALLOW_CC_BY=1 in .env (credit line then automatic) |
| streamline-ultimate-color | Ultimate color icons | 998 | CC-BY-4.0 | CC BY 4.0: only with ALLOW_CC_BY=1 in .env (credit line then automatic) |
| subway | Subway Icon Set | 306 | CC-BY-4.0 | CC BY 4.0: only with ALLOW_CC_BY=1 in .env (credit line then automatic) |
| twemoji | Twitter Emoji | 3,988 | CC-BY-4.0 | CC BY 4.0: only with ALLOW_CC_BY=1 in .env (credit line then automatic) |
| fa6-brands | Font Awesome 6 Brands | 495 | CC-BY-4.0 | brand / logo set (Archive / Unmaintained): trademarks |
| fa-brands | Font Awesome 5 Brands | 457 | CC-BY-4.0 | brand / logo set (Archive / Unmaintained): trademarks |
| brandico | Brandico | 45 | CC-BY-SA-3.0 | brand / logo set (Logos): trademarks |
| bxl | Boxicons Brands | 295 | MIT | brand / logo set (Logos): trademarks |
| cbi | Custom Brand Icons | 1,792 | CC-BY-NC-SA-4.0 | brand / logo set (Logos): trademarks |
| cib | CoreUI Brands | 830 | CC0-1.0 | brand / logo set (Logos): trademarks |
| cryptocurrency | Cryptocurrency Icons | 483 | CC0-1.0 | brand / logo set (Logos): trademarks |
| cryptocurrency-color | Cryptocurrency Color Icons | 483 | CC0-1.0 | brand / logo set (Logos): trademarks |
| entypo-social | Entypo+ Social | 76 | CC-BY-SA-4.0 | brand / logo set (Logos): trademarks |
| fa7-brands | Font Awesome Brands | 608 | CC-BY-4.0 | brand / logo set (Logos): trademarks |
| logos | SVG Logos | 2,064 | CC0-1.0 | brand / logo set (Logos): trademarks |
| nonicons | Nonicons | 69 | MIT | brand / logo set (Logos): trademarks |
| selfhst | selfh.st/icons | 7,332 | CC-BY-4.0 | brand / logo set (Logos): trademarks |
| simple-icons | Simple Icons | 3,470 | CC0-1.0 | brand / logo set (Logos): trademarks |
| streamline-logos | Logos free icons | 1,362 | CC-BY-4.0 | brand / logo set (Logos): trademarks |
| thesvg | theSVG | 3,805 | MIT | brand / logo set (Logos): trademarks |
| thesvg-color | theSVG Color | 5,204 | MIT | brand / logo set (Logos): trademarks |
| token | Web3 Icons | 1,788 | MIT | brand / logo set (Logos): trademarks |
| token-branded | Web3 Icons Branded | 4,085 | MIT | brand / logo set (Logos): trademarks |
| catppuccin | Catppuccin Icons | 656 | MIT | brand / logo set (Programming): trademarks |
| codicon | Codicons | 657 | CC-BY-4.0 | brand / logo set (Programming): trademarks |
| devicon | Devicon | 1,121 | MIT | brand / logo set (Programming): trademarks |
| devicon-plain | Devicon Plain | 809 | MIT | brand / logo set (Programming): trademarks |
| file-icons | File Icons | 930 | ISC | brand / logo set (Programming): trademarks |
| gcp | Google Cloud Icons | 214 | Apache-2.0 | brand / logo set (Programming): trademarks |
| k8s | Kubernetes Icons | 38 | Apache-2.0 | brand / logo set (Programming): trademarks |
| material-icon-theme | Material Icon Theme | 910 | MIT | brand / logo set (Programming): trademarks |
| skill-icons | Skill Icons | 400 | MIT | brand / logo set (Programming): trademarks |
| unjs | UnJS Logos | 63 | Apache-2.0 | brand / logo set (Programming): trademarks |
| vscode-icons | VSCode Icons | 1,720 | MIT | brand / logo set (Programming): trademarks |
| rivet-icons | Rivet Icons | 210 | BSD-3-Clause | licence BSD-3-Clause is not on the allow-list |
| game-icons | Game Icons | 4,133 | CC-BY-3.0 | licence CC-BY-3.0 is not on the allow-list |
| ps | PrestaShop Icons | 479 | CC-BY-NC-4.0 | licence CC-BY-NC-4.0 is not on the allow-list |
| fontelico | Fontelico | 34 | CC-BY-SA-3.0 | licence CC-BY-SA-3.0 is not on the allow-list |
| arcticons | Arcticons | 15,474 | CC-BY-SA-4.0 | licence CC-BY-SA-4.0 is not on the allow-list |
| emojione-v1 | Emoji One (v1) | 1,262 | CC-BY-SA-4.0 | licence CC-BY-SA-4.0 is not on the allow-list |
| entypo | Entypo+ | 321 | CC-BY-SA-4.0 | licence CC-BY-SA-4.0 is not on the allow-list |
| openmoji | OpenMoji | 4,546 | CC-BY-SA-4.0 | licence CC-BY-SA-4.0 is not on the allow-list |
| si-glyph | SmartIcons Glyph | 799 | CC-BY-SA-4.0 | licence CC-BY-SA-4.0 is not on the allow-list |
| typcn | Typicons | 336 | CC-BY-SA-4.0 | licence CC-BY-SA-4.0 is not on the allow-list |
| gridicons | Gridicons | 207 | GPL-2.0-only | licence GPL-2.0-only is not on the allow-list |
| dashicons | Dashicons | 342 | GPL-2.0-or-later | licence GPL-2.0-or-later is not on the allow-list |
| wordpress | WordPress Icons | 344 | GPL-2.0-or-later | licence GPL-2.0-or-later is not on the allow-list |
| gala | Gala Icons | 51 | GPL-3.0 | licence GPL-3.0 is not on the allow-list |
| et | Elegant | 100 | GPL-3.0-or-later | licence GPL-3.0-or-later is not on the allow-list |
| icomoon-free | IcoMoon Free | 491 | GPL-3.0-or-later | licence GPL-3.0-or-later is not on the allow-list |
| circum | Circum Icons | 288 | MPL-2.0 | licence MPL-2.0 is not on the allow-list |
| academicons | Academicons | 158 | OFL-1.1 | licence OFL-1.1 is not on the allow-list |
| bpmn | BPMN | 112 | OFL-1.1 | licence OFL-1.1 is not on the allow-list |
| el | Elusive Icons | 304 | OFL-1.1 | licence OFL-1.1 is not on the allow-list |
| fa | Font Awesome 4 | 678 | OFL-1.1 | licence OFL-1.1 is not on the allow-list |
| ls | Ligature Symbols | 348 | OFL-1.1 | licence OFL-1.1 is not on the allow-list |
| map | Map Icons | 167 | OFL-1.1 | licence OFL-1.1 is not on the allow-list |
| mdi-light | Material Design Light | 284 | OFL-1.1 | licence OFL-1.1 is not on the allow-list |
| picon | Pico-icon | 824 | OFL-1.1 | licence OFL-1.1 is not on the allow-list |
| vs | Vesper Icons | 159 | OFL-1.1 | licence OFL-1.1 is not on the allow-list |
| websymbol | Web Symbols Liga | 85 | OFL-1.1 | licence OFL-1.1 is not on the allow-list |
| whh | WebHostingHub Glyphs | 2,125 | OFL-1.1 | licence OFL-1.1 is not on the allow-list |
| wi | Weather Icons | 219 | OFL-1.1 | licence OFL-1.1 is not on the allow-list |
| zmdi | Material Design Iconic Font | 777 | OFL-1.1 | licence OFL-1.1 is not on the allow-list |
| system-uicons | System UIcons | 430 | Unlicense | licence Unlicense is not on the allow-list |
