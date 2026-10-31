# Tables from the quick reference card (transcribed by reading the card pages, 2026-10-31)

The card is a 6-page picture (`Imperialism - quick reference card.pdf`, extract with `tools/ocr_pdf.py images`); no OCR model read its tables and diagrams reliably (see `docs/manual_ocr.md`),
so these numbers were read off the page images by eye. Where the running game was also read, the two agree (noted). The parenthesised numbers are printed that way on the card; what they mean is
not stated on it (probably the entrenched or elevated value).

## Terrain, who develops it, what it makes (card pages 1-3)

| Terrain | Developed by | Produces | Undeveloped | Level I | Level II | Level III |
|---|---|---|---|---|---|---|
| Barren Hills* | Miner | coal | - | 2 | 4 | 6 |
| Barren Hills* | Miner | iron | - | 2 | 4 | 6 |
| Mountain* | Miner | coal / iron | - | 2 | 4 | 6 |
| Mountain* | Miner | gold / gems | - | 1 | 2 | 3 |
| Swamp*, Desert*, Tundra* | Driller | oil | - | 2 | 4 | 6 |
| Open Range | Rancher | livestock | 1 | 2 | 3 | 4 |
| Fertile Hills | Rancher | wool | 1 | 2 | 3 | 4 |
| Orchard | Farmer | fruit | 1 | 2 | 3 | 4 |
| Plantation | Farmer | cotton | 1 | 2 | 3 | 4 |
| Farm | Farmer | grain | 1 | 2 | 3 | 4 |
| Hardwood Forest | Forester | timber | 1 | 2 | 3 | 4 |
| Dry Plains | - | grain | always 1 | | | |
| Scrub Forest | - | timber | always 1 | | | |
| Horse Ranch | - | horses | always 1 | | | |

\* must be prospected first (a Prospector searches Barren Hills and Mountains for coal, iron, gold, gems; Desert, Swamp and Tundra for oil); they may hold nothing. Engineers build rail track, rail depots, ports and forts level 1-3;
a Developer buys land in Minor Nations so other civilians can work there (developer flags).

## Industrial development flow chart (card page 4) against what we verified

Matches `docs/recipes.md` and the play tests everywhere checked: Grain+Fruit and Fish or Livestock -> Canned Food (the Food order); Cotton or Wool -> Fabric -> Clothing; Timber -> Paper and Lumber; Lumber -> Furniture;
Coal+Iron -> Steel -> Hardware and Armaments; Oil -> Fuel -> Power; Horses -> Military Units (the Armory's cavalry take a Horse each, seen in play); Fabric, Lumber, Coal and Fuel feed Naval Units (the Shipyard); Paper
feeds trained/expert workers and civilian units (the Trade School and University cost Paper, seen); Steel and Lumber go to Transport Capacity / Factory Construction (the Refinery cost, seen); Untrained Worker -> Trained/Expert
Workers -> Civilian Units, Untrained Worker -> Military Units; Clothing, Furniture and Canned Food go to the workers; Gold -> $200 and Gems -> $500 (what a unit of each is worth in cash).

## Military units (card page 5): Era I, II, III

| | Firepower | Melee | Range | Defense | Movement |
|---|---|---|---|---|---|
| **Era I** | | | | | |
| Minutemen | 5 | 5 | 5 | 4(5) | 4 |
| Skirmishers | 5 | 5 | 5 | 7(8) | 6 |
| Regulars | 10 | 10 | 5 | 5(6) | 4 |
| Grenadiers | 12 | 12 | 5 | 5(6) | 4 |
| Hussars | 7 | 10 | 3 | 7 | 11 |
| Cuirassiers | 15 | 19 | 3 | 5 | 9 |
| Light Artillery | 10 | 3 | 9(10) | 3(4) | 5 |
| Artillery | 16 | 4 | 11(12) | 2(3) | 3 |
| Sappers | - | - | 5 | 3(4) | 4 |
| General | - | 1 | 1 | 5 | 7 |
| **Era II** | | | | | |
| Militia | 7 | 7 | 8 | 4(5) | 4 |
| Sharpshooters | 10 | 10 | 8 | 7(8) | 6 |
| Rifle Infantry | 15 | 15 | 8 | 7(8) | 4 |
| Guards | 17 | 17 | 8 | 7(8) | 4 |
| Scouts | 10 | 13 | 5 | 7 | 11 |
| Carbineers | 20 | 26 | 5 | 5 | 9 |
| Field Artillery | 17 | 5 | 12(13) | 3(4) | 6 |
| Siege Artillery | 30 | 8 | 14(15) | 3(4) | 3 |
| Engineers | - | - | 8 | 4(5) | 4 |
| General | - | 1 | 1 | 7 | 9 |
| **Era III** | | | | | |
| Conscripts | 10 | 10 | 10 | 10(12) | 5 |
| Rangers | 15 | 15 | 10 | 20(25) | 7 |
| Infantry | 22 | 22 | 10 | 20(25) | 5 |
| Machine Gunners | 25 | 25 | 10 | 20(25) | 4 |
| Mechanized | 22 | 28 | 10 | 10(12) | 11 |
| Armor | 45 | 60 | 12 | 20(25) | 9 |
| Mobile Artillery | 25 | 8 | 15(16) | 20(25) | 8 |
| Railroad Gun | 50 | 12 | 17(18) | 20(25) | 3 |
| Saboteurs | - | - | 10 | 10(12) | 5 |
| General | - | 1 | 1 | 20 | 11 |

Each column pairs one top label with one bottom label in the picture; the order here follows the pictures left to right. **Checked against the Armory dialog in play** (Era I): Firepower, Move (= Movement) and Range of Skirmishers, Hussars,
Regulars, Cuirassiers, Grenadiers, Light Artillery, Artillery and Sappers all match `docs/production_playtest.md`. Minutemen and General are not recruited at the Armory.

## Naval units (card page 6)

| | Frigate | Ship-of-the-Line | Raider | Ironclad | Advanced Ironclad | Armored Cruiser | Dreadnought | Battlecruiser |
|---|---|---|---|---|---|---|---|---|
| Firepower | 3 | 6 | 3 | 5 | 10 | 6 | 20 | 18 |
| Range | 5 | 6 | 7 | 8 | 10 | 9 | 13 | 13 |
| Armor | 10 | 20 | 20 | 55 | 60 | 50 | 70 | 55 |
| Hull | 35 | 65 | 30 | 50 | 70 | 40 | 115 | 90 |
| Speed | 4 | 3 | 7 | 5 | 6 | 8 | 7 | 9 |
| Sea Zone | 3 | 2 | 5 | 3 | 4 | 6 | 5 | 6 |

Frigate and Ship-of-the-Line match the Shipyard dialog in play (Firepower, Range, Armor, Hull, Speed).

## Diplomatic options (card page 6, flow chart)

Peace <-> War. **Trade Consulate ($500)** leads to: trades improve relations, boycotts, subsidies, and **Embassies ($5,000)**. An Embassy leads to: send civilians to Minor Nations (overseas profits), grants to MNs,
pacts with MNs, alliances with Great Powers, **Empire** (-> colony) and military intervention when an MN is threatened (-> colony). War allows attacks and an automatic boycott, and leads to conquering territory.
The two prices match what we saw in play (`docs/diplomacy.md`). The manual (chapter "Diplomacy") adds: the Empire overture costs nothing but is refused unless relations are friendly enough, and only Minor Nations
where you have an Embassy ever join voluntarily.
