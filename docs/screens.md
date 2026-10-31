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
| Technology screen | 5 | 2300 (0x8fc) | `TScreenBuilder_TechHistory`, `TTechHistoryView` | "Technologies / Cost / Benefits": what has been bought ("Purchased in 1815", e.g. Seed Drill, High Pressure Steam Engine). The manual's Technology Investment screen (buying) is reached with the microscope button; not looked at yet |
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
