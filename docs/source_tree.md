# The original source tree, recovered from the exe's assert strings

The game calls one assert hook, `Ambit_Assert` (0x49d620), about 360 times with its compile-time file name and a line number, so the exe contains the paths of its own source files:
`D:\Ambit\*.cpp` (the Windows shell, by the "Ambit" framework authors) and `D:\Ambit\Cross\U*.cpp` (the game proper, shared with the Mac version; "U" units in the style of Mac PowerPlant).
`tools/exe_strings.py` lists every string with its address; `tools/source_files.py` ties functions to files; `tools/source_groups_check.py` compares that with our groups.

## How the attribution works

* A function that calls the assert hook with a file string is **anchored** to that file (264 functions; 200 kept).
* Header files and inline shared code drop other files' strings into functions that live elsewhere. Both the string pool and the code follow link order, so we keep only the `.cpp` anchors that fit one
  increasing order (longest non-decreasing run of string address against function address) and ignore the other 64.
* The linker puts one translation unit's functions together. Functions between two anchors of the **same** file are *inferred* for it (5,599 of 5,991 non-library functions are covered); between anchors of
  **different** files they are *boundary* (either side). Output: `names/source_attribution.tsv` (address, name, file, assert | inferred | boundary, line numbers).
* `names/source_files.tsv` maps each file to one of our groups and is used by `tools/split_source.py` to file unsorted functions.

## The files and what they are (certain address range; the file extends into the boundary zones on either side)

| File | Certain range | What it is |
|---|---|---|
| `McAppUI.cpp`, `McAppStream.cpp`, `QuickDraw.cpp`, `CDib.cpp`, `WAssetMgr.cpp`, `WNetMgr.cpp`, `DirectPlay.cpp`, `IncludeView.cpp`, `DiplomacyDialogs.cpp` | 0x47aa00-0x5e3f30 (interleaved) | the Windows shell: windows, streams, drawing, bitmaps, assets, networking |
| `Cross/UCity.cpp` | 0x4b4180-0x4b4580 | the city and its production orders (the recipes we decoded) |
| `Cross/UCityMinister.cpp` | 0x4be8d0-0x4c3910 | the Interior Minister (advice, reports) |
| `Cross/UCityDialogs.cpp`, `UCityViews.cpp` | 0x4bc0b0-0x4bdc10, 0x4c8390-0x4d0810 | city screens and dialogs |
| `Cross/UCountry.cpp` | anchor 0x4db7d0; zone about 0x4d1760-0x4dbac0 | nations, Great Powers, the diplomacy manager, tech |
| `Cross/UCountryAuto.cpp` | anchor 0x4e8540; zone about 0x4dbac0-0x4e8680 | the computer-controlled powers (the AI) |
| `Cross/UDefenseMinister.cpp` | 0x4ec540-0x4ed050 | the Defense Minister |
| `Cross/UDiplomacyViews.cpp` | anchor 0x4f2d10 | diplomacy screens |
| `Cross/UArmyMgr.cpp`, `UArmyViews.cpp` | 0x4a1f80-0x4a7b20, 0x4a9990 | armies and their views |
| `Cross/UNavy.cpp` | 0x54f8e0-0x5573f0 | the navy (134 functions) |
| `Cross/UOcean.cpp`, `UOceanViews.cpp` | 0x562340-0x5635e0, 0x564dc0 | ocean zones, ports, sea movement |
| `Cross/UMissionSubs.cpp` | anchor 0x53c0a0; zone about 0x52e7b0-0x53c1b0 | AI missions (the largest boundary zone: about 500 functions across it and the multiplayer file) |
| `Cross/UTacPlayer.cpp`, `UTacViews.cpp` | anchors 0x59b830, 0x5a9d90 | tactical battles |
| `Cross/UUnit.cpp` | anchor 0x5c2530 | units |
| `Cross/UMap.cpp` | 0x50e8b0-0x5147d0 | the map manager (63 functions; was filed under display) |
| `Cross/UMapper.cpp` | 0x529960-0x52e350 | the map generator, class `TMapMaker` (33 functions; was filed under framework) |
| `Cross/UMapDlog.cpp`, `USuperMap.cpp` | 0x51b1c0-0x51bb90, 0x598e10-0x59a180 | map dialogs and the large map view |
| `Cross/UNewspaper.cpp` | anchor 0x55ba30 | the Imperial Times |
| `Cross/UMultiplayerMgr.cpp` | anchor 0x545940 | multiplayer |
| `Cross/UViewMgr.cpp`, `UViewMgr.more.cpp`, `UMacViewMgr.cpp`, `UDisplayMgr.cpp`, `UGameWindow.cpp`, `UIcon.cpp`, `UHelpMgr.cpp`, `USmallViews.cpp`, `USetupScreens.cpp`, `UTestDialogs.cpp`, `UTradeViews.cpp`, `UOptionViews.cpp`, `UBattleReportViews.cpp`, `UAmbit.cpp`, `UCheaters.cpp` | various | views, windows, setup, help, cheats |

`UTradeViews.cpp` has no trade logic anchor: the trade manager's code (`TTradeMgr`, 0x5b8080) is in the zone after `UTestDialogs.cpp`, so it lives in a file whose name does not appear (possibly a `UTrade.cpp` with no assert). The same
may hold for tech (`TTechMgr`, 0x5aef30) and diplomacy (`TDiplomacyMgr`): they sit in the 0x5a9d90-0x5ba7a0 range between `UTacViews` and `UTradeViews`.

## Narrowing the boundary zones (`tools/source_boundaries.py`)

Only about 1,230 of the 5,996 non-library functions carry or sit between assert anchors of the same file. The rest lie in 'boundary' zones between two anchored files. Inside a zone the files switch exactly
once (a translation unit is contiguous), so the question is where. The resolver is deliberately conservative: it labels only functions on the evidence side of every best cut and leaves the stretch in
between open. Labels in `names/source_attribution.tsv`, strongest first:

| Label | Meaning | Functions |
|---|---|---|
| `assert` | the function calls the assert hook with its file name | 198 |
| `inferred` | between two asserts of the same file | 1,031 |
| `cut` | placed by **hard evidence**: its class (the methods of a class already attributed are all in one file) or the position of its exception-handler stub | 243 |
| `prior` | placed by the **semantic prior** only: a view/dialog class belongs in the `*Views`/`*Dialogs` file, other classes in the logic file; weaker, circular with our own class naming, treat as likely | 1,503 |
| `boundary` | still open (one of the two files) | 2,631 |

Evidence that was tested and what it showed:
* **Exception-handler stubs**: about 19% of functions store a stub address in their frame (`puStack_8 = &UNK_0062a8f6`). The stubs lie in one region in link order, and for the certain functions the stub address
  of a file's functions forms an interval with **no file out of order** (29 files). It orders functions but only bounds the cut (a function past A's last known stub is not in A's known part), so it helps near the edges.
* **Runtime-class addresses** (`classes.tsv`, `classVA`): the `CRuntimeClass` objects are laid out in link order too (17 files, **no file out of order**, tight clusters). Same limit: a monotone order, not a cut.
* **Call-graph votes** were tried and removed: UI code calls into game logic, so callers of a logic function vote for the UI file and pull the cut the wrong way. This had put 133 city-production functions
  into `UCityDialogs.cpp` before the check against our groups caught it (`tools/source_groups_check.py`: `UCity.cpp` is now 170 production functions, as it should be).
* **Data strings**: file names sit in the string pool next to the strings of their own file (the class name `TMapMgr` right before `UMap.cpp`'s name), roughly within 0x150 bytes, but pool order is too fuzzy to cut on.

The biggest zones still open: `UOceanViews|USetupScreens` (342), `UMapper|UMissionSubs` (298), `UMissionSubs|UMultiplayerMgr` (204), `USetupScreens|USmallViews` (178), `IncludeView|McAppStream` (157),
`UDiplomacyViews|UDisplayMgr` (131), `UTestDialogs|UTradeViews` (130). The ones holding trade, tech and diplomacy logic (`UTacViews|UTestDialogs`, `UTestDialogs|UTradeViews`) probably contain a file with no assert at all.
The tracer from the plan (real call trees) is the next independent source of evidence.

## What this changes

* The reimplementation's modules can follow the original files (city, country, country-auto, army, navy, ocean, missions, tactical, unit, map, mapper) instead of our guessed groups. See `docs/PLAN_reimplementation.md`.
* Corrections made from this: `UMap.cpp` and `UMapper.cpp` functions moved from `display` / `framework` to `map_sim` (`map_sim` grew from 19 to over 120 functions); `Ambit_Assert` named (0x49d620).
* **Multiplayer is tabled**: `UMultiplayerMgr.cpp` resolves to 0x540840-0x54ecc0 (190 functions), `WNetMgr.cpp` to 0x5e2850-0x5e3f30; with the lounge/join/net-select screens and the Remote/Proxy/Host Great Power classes they form the
  parked group `multiplayer` (262 functions), next to the parked `directplay` group (149).
