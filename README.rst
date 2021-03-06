**Retroarch scummvm playlist creator**
======================================

Creating playlists for the scummvm core in retroarch is complicated.

1. Add the games, by loading, then starting the core from retroarch, then
'mass add' all the games (note this isn't the retroarch scanner - it's a
functionality of the core GUI - click the arrow next to 'Add Game...' in the
classic theme - the retroarch scan directory function should not be used for
scummvm games, and the manual scanner is unneeded with this program).

2. Download the required engine files and extract them to the right dir.
I recommend installing the scummvm required files with 'core system files
downloader' in retroarch if you're running the normal core [1]_.

3. Setup the paths to the required files in the scummvm core GUI options.
\

4. Create .scummvm files for each and every game entry in the created
scummvm.ini, in the game dir so the manual scanner can scan the .scummvm
files and assign it a playlist entry.

libretro-mkscumm removes the need for step 3 and 4 if you did step 1 and 2.

To update this program with pip installed, type:

``pip install --upgrade git+https://github.com/i30817/libretro-mkscumm.git``

If you'd like to try to download missing coverart until a PR with scummvm
names is added to the thumbnail server try to install and use libretrofuzz:

``pip install git+https://github.com/i30817/libretrofuzz.git``

.. [1] The diablodiab daily build core at http://build.bot.nu/nightly/ requires updated files from scummvm upstream, you can get them with:

  http://build.bot.nu/assets/system/ScummVM.zip

  Then extract the zip into the retroarch ``system`` directory.

libretro-mkscumm [OPTIONS] [CFG]
  :CFG:                 Path to the retroarch cfg file. If not default, asked from the user.
  
                        Linux default:   ``~/.config/retroarch/retroarch.cfg``
  
                        Windows default: ``%APPDATA%/RetroArch/retroarch.cfg``
  
                        MacOS default:   ``~/Library/Application Support/RetroArch/retroarch.cfg``
  
  --playlist TEXT       Playlist name to create. If not provided, ScummVM.lpl
                        is created or recreated if it exists.  [default:
                        ScummVM.lpl]
  --filter TEXT         Filter for game paths, you can add this option more
                        than once. If the option is used, only game entries in
                        scummvm.ini whose paths start with one of these create
                        a .scummvm file or get added to the playlist, use it
                        if you want multiple playlists.
  --install-completion  Install completion for the current shell.
  --show-completion     Show completion for the current shell, to copy it or
                        customize the installation.
  --help                Show this message and exit.


To install the program, type on the cmd line

+---------------------+-----------------------------------------------------------------------------------------------------------+
| Linux               | ``pip install --force-reinstall https://github.com/i30817/libretro-mkscumm/archive/master.zip``           |
+---------------------+-----------------------------------------------------------------------------------------------------------+
| Windows             | ``python -m pip install --force-reinstall https://github.com/i30817/libretro-mkscumm/archive/master.zip`` |
+---------------------+-----------------------------------------------------------------------------------------------------------+

In windows, you'll want to check the option to ???Add Python to PATH??? when installing python, to be able to execute the script from any path of the cmd line.
