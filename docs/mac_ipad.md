# Playing on a Mac and an iPad (private Wine wrapper)

**Status: written, not tested.** I had no Mac to try it on. The Windows side (the game, the shim, the music DLL) is what this project verified; every Mac step below is from how
these tools normally work, so expect to fix a command or two. Fix this file when you do (`AGENTS.md` says to keep docs current).

## What is and is not possible

* **Wine runs on a Mac, not on an iPad.** iPadOS does not let an ordinary app generate code at run time (the "JIT" Wine and emulators need), and there is no maintained Wine for iOS.
  So "a Wine-wrapped version for the iPad" really means: **build a wrapped copy on the Mac, then reach it from the iPad**. Two ways, below.
* **Private means private:** the wrapper holds the game's files, which are copyrighted. Build it from your own GOG install, keep it on your own machines, and never commit or share it.
  The script writes to `~/ImperialismMac`, outside this repository, and the repo's `.gitignore` already excludes game files.

## Part 1: build the wrapper on the Mac

### Tooling to install (once)

| Tool | What for | Install |
|---|---|---|
| Xcode command line tools | git, compilers (Homebrew needs them) | `xcode-select --install` |
| Homebrew | installs the rest | see <https://brew.sh> (one line in Terminal) |
| Rosetta 2 (Apple Silicon Macs only) | runs the 32-bit-capable Intel Wine build | `softwareupdate --install-rosetta --agree-to-license` |
| Wine (a macOS build) | runs `Imperialism.exe` | `brew tap gcenx/wine` then `brew install --cask --no-quarantine wine-stable` |
| winetricks (optional) | fixes if something is missing | `brew install winetricks` |
| Your game files | the GOG install folder from the Windows PC | copy `C:\GOG Games\Imperialism` to the Mac (USB stick, network share, or the GOG installer's offline backup) |

Notes:
* Wine for macOS is a moving target. The `gcenx/wine` Homebrew tap carries recent builds (it is the one the Whisky/Sikarugir wrappers use). If `wine-stable` will not run a 32-bit program on your
  macOS version, try `wine-devel`, or the paid **CrossOver** (<https://www.codeweavers.com>, 14-day trial), which handles 32-bit games reliably and is the fallback I would try first.
* If you prefer a double-clickable `.app`: **Sikarugir** (the maintained successor to Wineskin/Kegworks; Whisky is archived) builds one from the same engine. Install it from its GitHub page,
  create a wrapper, point it at `Imperialism.exe`, and add the same DLL overrides as below. The script here makes a plain folder with a launcher instead, which has fewer moving parts.
* Check `brew doctor` is clean before blaming Wine.

### Build it

1. Copy the game folder to the Mac, for example to `~/Games/Imperialism` (keep the `Data`, `MUSIC`, `MOVIES`, `Save` folders and every `.dll` in it).
2. Get this repository (`git clone` of your fork or the original), then in Terminal:

   ```sh
   cd imperialism-re            # the repo folder
   sh tools/mac/make_wrapper.sh ~/Games/Imperialism
   ```

3. It creates `~/ImperialismMac/` with a Wine prefix, a copy of the game, and **`~/ImperialismMac/play.sh`**. Run `~/ImperialismMac/play.sh` to start the game.

What the script does: makes a 32-bit Wine prefix in `~/ImperialismMac/prefix`, copies the game files (the original is untouched), sets the DLL overrides below, and writes `play.sh`.

### Things that matter when the game runs under Wine

* **Music needs the project's `winmm.dll`.** The game plays its music through a replaced `winmm.dll` (ogg-winmm, reading the files in `MUSIC`). Wine has its own `winmm`, so the override
  `winmm=n,b` (native first) is required, or there is no music. The `libogg`, `libvorbis`, `libvorbisfile` DLLs in the game folder must come along.
* **The display shim (`msvfw32.dll`)**: the project's shim scales the 640x480 picture into a resizable window. Under Wine it may or may not work, because it hooks Windows drawing calls. `play.sh`
  starts with the shim **on** (`msvfw32=n,b`). If the window is blank or wrongly sized, run `play.sh noshim` (it then uses Wine's own `msvfw32`, a fixed 640x480 window; turn on Retina mode
  with `winecfg` -> Graphics, or use macOS's own zoom).
* **Mouse:** the game's hot text and tool tips need the pointer to hover, so use a mouse or trackpad, not touch.
* **Saves** go in the wrapper's own copy of `Save/`. Copy `.imp` files from the Windows PC to carry games over; `saves/` in this repo has test saves.
* If the game crashes at start, run `WINEDEBUG=err+all ~/ImperialismMac/play.sh` and look at what is reported; a missing DLL is the usual cause (`winetricks vcrun6` has fixed old games).

## Part 2: getting it onto the iPad

### A. Stream from the Mac (recommended)

The game runs on the Mac; the iPad shows it and sends the keyboard, trackpad or mouse. Works on the iPad with your trackpad cover or a mouse (iPadOS has pointer support). The game is 640x480 and slow-paced, so latency does not matter.

* **Moonlight (iPad app, free) + Sunshine (on the Mac)**: free and low latency. Sunshine has macOS builds (<https://github.com/LizardByte/Sunshine>); you add `play.sh` as an application in its web page.
* **Parsec** or **Jump Desktop** (paid): simpler to set up, work over the internet, support a mouse on the iPad.
* **Steam Link**: add `play.sh` (or the Wine process) as a non-Steam game in Steam on the Mac, then use the Steam Link iPad app.

Tips: set the stream to "desktop mouse" (absolute pointer), not "touch" or "game controller", so hot text works; stream at 1280x960 or the iPad's native 4:3 so the picture fills the screen.

### B. Run it on the iPad itself (slower, more fiddly)

**UTM** (<https://mac.getutm.app>; the "UTM SE" build installs from the App Store without any special permission) emulates a PC on the iPad. Install Windows XP or 98 inside it and copy the game folder in (you do not need Wine in this case: the
game runs natively under Windows). A 1997 game at 640x480 is light enough, but without JIT the emulator is slow; the full UTM build on a sideloaded setup (AltStore / Developer Mode JIT) is faster. Mouse and trackpad work through UTM's pointer capture.
This path never uses the shim's Wine overrides: copy the same game folder as it is on your Windows PC, shim and music DLL included.

## Later: a real port

Moving off Windows altogether (SDL front end, rewritten game logic) is possible but long; see the discussion in the session notes and `docs/STATUS.md`. The wrappers above are the cheap route to playing on a tablet now.
