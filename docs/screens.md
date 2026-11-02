# Screens of Imperialism (1997): manual names, ids, how to reach them

The names come from the game's own manual (`Imperialism - manual.pdf` in the game folder; read it with `pdftotext -layout`) and the hot
text the game shows. Screen ids are read from the running game with `python -I tools/readview.py id` (the short at +4 of the view
manager, global 0x6a21bc). Coordinates are mirror units (1296x999), as used by `harness/prod_do.ps1`.

## Main menu: the "IMPERIALISM" office screen

Every object has hot text on the paper at the bottom of the screen (mirror x 380-900, y 905-960). `harness/menu_hover.ps1` captures it.

| Object | Where | Hot text | Leads to (manual, "Starting a Game") |
|---|---|---|---|
| Ship in the Bottle | (240,340) | Load Saved Game | Load Saved Game screen (below) |
| Globe | (170,580) | Start New Game on Random Map | Map Room: pick a Great Power, difficulty, name, Start Game |
| Book (orange, bottom left) | (160,890) | Load Scenario or Tutorial | Library: scenario and tutorial list ("More..." pages through it) |
| Telephone, tea service | (1090,690), (960,650) | Multiplayer | Conference Room (protocol, join, host) |
| Awards, lamp, statue (right shelf) | (1070,360), (925,380), (1210,380) | Show High Scores | High scores |
| Pen | (1150,925) | Preferences | the Preferences screen, so settings can be changed before any game |
| Doors | (650,400) | Quit | exits the game |

**Load Saved Game screen** (the manual calls the in-game version the "Chart Room"): eight slots in two columns, slot 0 at (370,627);
selecting one shows its map, power, difficulty and year; **Load Game** is at (1150,472). Slot labels are read when the screen opens, but
the file is read at load time. `harness/prod_boot.ps1` does the whole thing: write the registry settings, launch, copy a fixture into
`Save\slot0.imp`, click bottle, slot 0, Load Game, and wait for screen id 2013. About 11 s of script from a cold start, and the registry
volumes and briefings/warnings settings survive the load (a new game would reset briefings to On).
Not yet found: how to leave the Library or Load screens without choosing (the manual says "the Doorway"); Esc does nothing there.

## In-game screens

| Manual name | Hot key | Screen id | Decompile builder / view class | What is on it |
|---|---|---|---|---|
| Terrain Map | (back arrow from the others) | 2013 (0x7dd) | TGameWindow map views | the map; toolbar: Zoom, Invest in Technology (microscope), Game Controls (computer), Help; Mini-Map; unit panel; End Turn (bottom right) |
| Transport screen ("Transport" and "Ledger" book) | 1 | 2014 (0x7de) | `TScreenBuilder_LedgerTransport` | left page: commodities moved on the network with sliders (e.g. 4/4); right page: the ledger of resources; locomotive and ship capacity bar |
| Industry screen (the capital city) | 2 | 2011 (0x7db) | `TCityProductionView`, `TBuildingView`, `TBuildingConstructionView`, `TBuildingExpansionView` | the 14 named sites (Capitol, Trade School, University, Armory, Shipyard, Railyard, Warehouse, Textile Mill, Lumber Mill, Steel Mill, Metalworks, Clothing Factory, Furniture Factory, Food Processing) plus the Oil Refinery and Power Plant sites once Oil Drilling is known; left bar: labor; right bar: food. Dialogs: see `production_playtest.md` |
| Trade screen ("Board of Trade") | 3 | 2009 (0x7d9) | `TScreenBuilder_BoardOfTrade` (0x4601b0) | commodity rows with Orders (Bid/Offer buttons), Price, Available and Quantity to Offer; ship icon at the right edge for merchant marine |
| Diplomacy screen | 4 | 2008 (0x7d8) | `TDiplomacyMapView`, `TForeignMinisterView` | the world map; "Information: <power>" with Provinces, Military, Industry; Map Key; tabs on both sides for information, overtures, treaties and trade policy. Offers: Escape rejects, Return accepts (manual hot keys) |
| Technology screen | 5 | 2300 (0x8fc) | `TScreenBuilder_TechHistory`, `TTechHistoryView` | "Technologies / Cost / Benefits": what has been bought ("Purchased in 1815", e.g. Seed Drill, High Pressure Steam Engine). The microscope button (map toolbar, (1133,80)) opens this same screen: it is where techs are bought, see `docs/technology.md` |
| Game Controls (computer button) | (1190,80) on the map | a dialog | | Save, Load, Quit, New Game, and Set Preferences |
| Preferences | via Game Controls, or the pen on the main menu | | `TGamePreferencesPicture` | Minister Briefings and Warnings and the volume sliders; stored in `HKCU\Software\SSI\Imperialism\Settings` |
| Help and Information | F1 or the `?` button | | `THelpWindow` | |

Top bar of the in-game screens: four icons at about (560,65), (617,65), (673,65), (732,65) = Transport, Industry, Trade, Diplomacy;
the back arrow is at (57,135) and `?` at (1235,135).

## Keys

The manual's hot keys (1-5 for screens, F1 help, Escape/Return for offers, `w` on the map) work, but only as **window messages**:
a global key press (`keybd_event`) stopped reaching the game partway through a session, while `PostMessage` of WM_KEYDOWN to the
game frame and the `AmbitGameWindow` worked every time. `prod_do.ps1 "go industry|transport|trade|diplomacy|tech|map"` uses that and
`readview.py id` to confirm: transport 2014, industry 2011, trade 2009, diplomacy 2008, tech 2300, map 2013.

## Clicking by window messages (`harness/msgclick.ps1`, spike 2026-11-01)

Mouse clicks can be sent straight to the game's own windows, in game pixels, with no focus, no mirror scaling, no cursor movement, and **with the game minimized** (checked: the Trade School plus/minus
charged and refunded $100 while both the game frame and the mirror were minimized). The Compat shim relays real clicks with `SendMessage` (WM_MOUSEMOVE, WM_LBUTTONDOWN with MK_LBUTTON, WM_LBUTTONUP) to the
deepest visible child window under the pointer, in that window's **client** coordinates (`compat/src/input.c`, `resolve_target`); `msgclick.ps1` does the same.
* **Map, toolbar, screens**: target the 640x480 `AmbitGameWindow` with game pixels (mirror = 10.4 + 1.993 x). Example: factory icon (563,131) opens the Industry screen, back arrow (23,50).
* **Dialogs** are `AmbitMcWindow` children of the frame. Their window rect includes a 3 px border and 26 px caption, so a control position measured from the window's top-left (the `$script:DLG` numbers in `fast.ps1`) must have **(3,26) subtracted** for the message. Wrong offsets simply do nothing.
* **Choose the dialog by size** (`Get-Dialog`): a second visible `AmbitMcWindow` (a side panel, 182x329) can come first when enumerating. Handles change every time a dialog opens, so look them up per click.
* **Closing a dialog**: post `WM_SYSCOMMAND` `SC_CLOSE` (0xF060) to it (what the shim does for the title-bar X) **for the production, Trade School, University and other non-modal windows only**.
* **MODAL POPUPS CRASH THE GAME if closed with SC_CLOSE** (2 of 2 tries, 2026-11-01): the empty/real "Construction Options" popup (328 x 70 or 328 x 238; opened by clicking the selected Engineer's own tile) runs in MFC `CWnd::RunModalLoop`.
  Destroying it with SC_CLOSE leaves the loop calling through a freed window: access violation at address 0, `eip=0`, return address 0x60a718 = `CWnd__RunModalLoop`+0x10e (dumps `dumps/Imperialism.exe.31068.dmp` and `.27904.dmp`, read with `tools/dumpinfo.py`).
  Close it with its **Cancel button** (`msgclick.ps1 dcancel`, posted click). Also: a `SendMessage` click that opens a modal popup does not return until the popup closes, so a script using it hangs; use the posted click `gp X Y` for any click that can open a popup (Engineer's own tile, a working unit's tile).
* Not needed: hovering the real cursor, `Ensure-Focus`, the mirror. Not yet tried: slider drags (WM_MOUSEMOVE with MK_LBUTTON between down and up), right-click, the construction popups, the Civilian Report/advice popups.

## Reading what is on screen

Screenshots are the slow way. The display shim can log every string the game draws (it hooks `TextOutA`, `ExtTextOutA`, `TabbedTextOutA`, `DrawTextA`)
to `imperialism_text.log` in the game folder when `imperialism_shim.ini` has `[text_log]` / `enabled=1` (`prod_boot.ps1` writes that). Each line is
`<tick> <T|X|B|D> <x>,<y> <text>`; the game draws every string twice (a shadow one pixel up-left), and the reader collapses those. `prod_do.ps1 "mark; go trade; txt"`
prints what a screen drew: the Board of Trade's prices and quantities, the diplomacy "Information:" panel (Provinces / Military / Industry), hot text, the load
screen's slot names. Positions are in the game's own 640x480 coordinates (or the off-screen bitmap's). Installed build: `shim/build20.dll` (build 17 plus the
text log; the previous shim is saved as `original/msvfw32_before_textlog.dll`, and the log does nothing unless the ini switches it on).
