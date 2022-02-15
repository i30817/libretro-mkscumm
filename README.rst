**Retroarch scummvm playlist creator**
======================================

  Creating playlists for the scummvm core in retroarch is complicated.

  1. Add the game directories to the scummvm.ini file in the Retroarch system
  directory, by starting the core and 'mass add' all the games, filtering out
  any false positives.

  2. Create .scummvm files for each and every game entry in the created
  scummvm.ini, in the game dir so the manual scanner can scan the .scummvm
  files and assign it a playlist entry.

  No more. This creates the .scummvm files, then creates a playlist for it, if
  the scummvm.ini file exists in your Retroarch system dir. In short, you only
  need to mass add and invoke this program.

**Usage: __main__.py [OPTIONS] [CFG]**

  libretro-mkscumm creates .scummvm files and playlists from the scummvm.ini
  in the retroarch system folder, created when you add games using the scummvm
  core.
  
Arguments:
  [CFG]  Path to the retroarch cfg file.  [default:
         ~/.config/retroarch/retroarch.cfg]

Options:
  --playlist TEXT       Playlist name to create. If not provided, ScummVM.lpl
                        is created or recreated if it exists.  [default:
                        ScummVM.lpl]
  --filters TEXT        Filters for game paths, you can add this option more
                        than once. Game entries in scummvm.ini whose paths
                        start with one of these don't create a .scummvm file
                        or get added to the playlist, use it if you want
                        multiple playlists.
  --install-completion  Install completion for the current shell.
  --show-completion     Show completion for the current shell, to copy it or
                        customize the installation.
  --help                Show this message and exit.


To install the program, type on the cmd line
 ``pip3 install git+https://github.com/i30817/libretro-mkscumm.git``

To upgrade the program
 ``pip3 install --upgrade git+https://github.com/i30817/libretro-mkscumm.git``

To remove
 ``pip3 uninstall libretro-mkscumm``
 
To install a program that can download missing coverart by fuzzy matching
 ``pip3 install git+https://github.com/i30817/libretrofuzz.git``
