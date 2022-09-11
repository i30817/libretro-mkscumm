#! /usr/bin/env python3


#project to create .scummvm files in the right directories for the Retroarch
#manual scanner to pick up and use for creation of a scummvm playlist.

#this is 'necessary' because the libretro core in retroarch has a very error
#prone and burdensome configuration:
# You first need to 'mass add' all of the games in the scummvm core by starting the core
# and using the inbuilt scanner mass add function, removing false positives you find
# (there are some, usually when the mass add adds them with a game entry that refers to the engine+number)
# Note that not all of those that have engine+number entry names will malfunction, only some on some engines. 
# The AGS engine for instance, rarely adds a 'unknown' game that doesn't work.
# Then after THAT, the core requires you to create files with the extension '.scummvm' with the scummvm.ini 
# game entry in the game directory for then to 'mass add' in the manual scanner to finally creat a playlist.
# the names will be the names for the scummvm files, which by necessity don't have 'illegal characters in windows'.

#this little program does the second for you and you don't need to use the manual scanner and the names will be
#'exactly equal' to the scummvm.ini names, illegal windows characters or not, by filling the label entry in the playlist.
#It has a option to set another name for the resulting playlist and filter with a accept prefix one or more base directories
#this allows you to filter games into different playlists like if you used the manual scanner twice, in case you don't
#want to overpopulate the scummvm playlist.


from pathlib import Path
from typing import Optional, List
import typer
import json
import os
import io
import re
import time
import sys

###########################################
########### SCRIPT SETTINGS ###############
###########################################

if sys.platform == 'win32': #this is for 64 bits too
    #this order is to make 'portable' installs have priority in windows, a concept that doesn't exist in linux or macosx
    #these are the default 32 and 64 bits installer paths, since there is no way to know what the user choses, check the defaults only.
    CONFIG = Path(r'C:/RetroArch-Win64/retroarch.cfg')
    if not CONFIG.exists():
        CONFIG = Path(r'C:/RetroArch/retroarch.cfg')
        if not CONFIG.exists():
            print('Portable install default location config not found, trying with APPDATA location')
            var = os.getenv('APPDATA')
            if var:
                CONFIG = Path(var, 'RetroArch', 'retroarch.cfg')
elif sys.platform == 'darwin':
    CONFIG = Path(Path.home(), 'Library', 'Application Support', 'RetroArch', 'config', 'retroarch.cfg')
else: #all the rest based on linux. If they arent based on linux, they'll try the else and fail harmlessly later
    var = os.getenv('XDG_CONFIG_HOME')
    if var:
        CONFIG = Path(var, 'retroarch', 'retroarch.cfg')
    else:
        CONFIG = Path(Path.home(), '.config', 'retroarch', 'retroarch.cfg')

#00-1f are ascii control codes, rest is 'normal' illegal windows filename chars according to powershell + &
forbidden    =  r'[\u0022\u003c\u003e\u007c\u0000\u0001\u0002\u0003\u0004\u0005\u0006\u0007\u0008' + \
                r'\u0009\u000a\u000b\u000c\u000d\u000e\u000f\u0010\u0011\u0012\u0013\u0014\u0015' + \
                r'\u0016\u0017\u0018\u0019\u001a\u001b\u001c\u001d\u001e\u001f\u003a\u002a\u003f\u005c\u002f\u0026]' 

def getPath(cfg: Path, setting):
    with open(cfg) as f:
        file_content = '[DUMMY]\n' + f.read()
    import configparser
    configParser = configparser.RawConfigParser()
    configParser.read_string(file_content)
    fdir = os.path.expanduser(configParser['DUMMY'][setting].strip('"'))
    if fdir == 'default':
        return None
    return Path(fdir)

def writeExtraPaths(ini: Path, extra: Path, theme: Path, saves: Path, soundfont: Path):
    with open(ini) as f:
        file_content = f.read()
    import configparser
    configParser = configparser.RawConfigParser()
    configParser.read_string(file_content)
    write = False
    if 'extrapath' not in configParser['scummvm']:
        configParser['scummvm']['extrapath'] = str(extra)
        write = True
    if 'themepath' not in configParser['scummvm']:
        configParser['scummvm']['themepath'] = str(theme)
        write = True
    if 'savepath' not in configParser['scummvm']:
        configParser['scummvm']['savepath'] = str(saves)
        write = True
    if 'soundfont' not in configParser['scummvm'] and soundfont.is_file():
        configParser['scummvm']['soundfont'] = str(soundfont)
        write = True
    if write:
        with open(ini, 'w') as f:
            configParser.write(f)

def error(error: str):
    typer.echo(typer.style(error, fg=typer.colors.RED, bold=True))

def mainaux(cfg: Path = typer.Argument(CONFIG, help='Path to the retroarch cfg file.'),
        playlist: str = typer.Option('ScummVM.lpl', help='Playlist name to create. If not provided, ScummVM.lpl is created or recreated if it exists.'),
        filters: Optional[List[str]] = typer.Option(None, '--filter', help='Filter for game paths, you can add this option more than once. If the option is used, only game entries in scummvm.ini whose paths start with one of these create a .scummvm file or get added to the playlist, use it if you want multiple playlists.')
    ):
    """
    Retroarch scummvm playlist creator
    
    Creating playlists for the scummvm core in retroarch is complicated.

    1. Add the games, by loading, then starting the core from retroarch, then 'mass add' all the games (note this isn't the retroarch scanner - it's a functionality of the core GUI - click the arrow next to 'Add Game...' in the classic theme - the retroarch scan directory function should not be used for scummvm games, and the manual scanner is unneeded with this program).
    
    2. Download the required engine files and extract them to the right dir. I recommend installing the scummvm required files with 'core system files downloader' in retroarch if you're running the normal core¹.
    
    3. Setup the paths to the required files in the scummvm core GUI options.
    
    4. Create .scummvm files for each and every game entry in the created scummvm.ini, in the game dir so the manual scanner can scan the .scummvm files and assign it a playlist entry.

    libretro-scummvm-playlist removes the need for step 3 and 4 if you did step 1 and 2.

    To update this program to the latest release with pip installed, type:

    pip install --force-reinstall libretro_scummvm_playlist
    
    If you'd like to try to download missing coverart until a PR with scummvm names is added to the thumbnail server try to install and use libretrofuzz:
    
    pip install --force-reinstall libretrofuzz
    
    ¹ The diablodiab more updated core at http://build.bot.nu/nightly/ requires updated files from scummvm upstream, you can get them with:
    
    http://build.bot.nu/assets/system/ScummVM.zip
    
    Then extract the zip into the retroarch system directory.
    """
    if not cfg.is_file():
        error(f'Invalid Retroarch cfg file: {cfg}')
        raise typer.Exit(code=1)
    
    playlist_dir = getPath(cfg, 'playlist_directory')
    
    if not playlist_dir.is_dir() or not os.access(playlist_dir, os.W_OK):
        error(f'Invalid Retroarch playlist directory: {playlist_dir}')
        raise typer.Exit(code=1)

    system_dir = getPath(cfg, 'system_directory')    
    if not system_dir.is_dir():
        error(f'Invalid Retroarch system directory: {system_dir}')
        raise typer.Exit(code=1)

    system   = Path(system_dir, 'scummvm.ini')
    if not system.is_file():
        error(f'Invalid scummvm.ini file: {system}')
        raise typer.Exit(code=1)
    
    extra_dir = Path(system_dir, 'scummvm', 'extra' )
    if not extra_dir.is_dir() or len(list(extra_dir.glob("./*"))) == 0:
        error(f'Extra scummvm extra dir does not exist or is empty.\nPlease see the documentation to download it.')
        raise typer.Exit(code=1)
    
    theme_dir = Path(system_dir, 'scummvm', 'theme' )
    if not theme_dir.is_dir():
        error(f'Extra scummvm theme dir does not exist.\nPlease see the documentation to download it.')
        raise typer.Exit(code=1)
    
    saves_dir  = getPath(cfg, 'savefile_directory')
    if not saves_dir or not saves_dir.is_dir():
        error(f'Invalid Retroarch saves directory: {saves_dir}')
        raise typer.Exit(code=1)
        
    cores_dir  = getPath(cfg, 'libretro_directory')
    if not cores_dir.is_dir():
        error(f'Invalid Retroarch cores directory: {cores_dir}')
        raise typer.Exit(code=1)
    core = os.path.abspath( Path(cores_dir, 'scummvm_libretro' + ( '.dll' if os.name == 'nt' else '.so' ) ) )
    
    content_dir  = getPath(cfg, 'rgui_browser_directory')
    if not content_dir:
        content_dir = ''
    
    with open(system) as f:
        text = f.read()
    
    #if the MT32 and CM32L roms exist in the system dir (for instance for dosbox)
    mt32rom1 = Path(system_dir, 'MT32_CONTROL.ROM')
    mt32rom2 = Path(system_dir, 'MT32_PCM.ROM')
    cm32rom1 = Path(system_dir, 'CM32L_CONTROL.ROM')
    cm32rom2 = Path(system_dir, 'CM32L_PCM.ROM')
    if mt32rom1.is_file() and mt32rom2.is_file():
        target1 = Path(extra_dir, 'MT32_CONTROL.ROM')
        target2 = Path(extra_dir, 'MT32_PCM.ROM')
        if not target1.exists():
            os.link(mt32rom1, target1)
        if not target2.exists():
            os.link(mt32rom2, target2)
    if cm32rom1.is_file() and cm32rom2.is_file():
        target1 = Path(extra_dir, 'CM32L_CONTROL.ROM')
        target2 = Path(extra_dir, 'CM32L_PCM.ROM')
        if not target1.exists():
            os.link(cm32rom1, target1)
        if not target2.exists():
            os.link(cm32rom2, target2)
    
    #write scummvm core specific paths so the user doesn't have to
    soundfont = Path(extra_dir, 'Roland_SC-55.sf2')
    writeExtraPaths(system, extra_dir, theme_dir, saves_dir, soundfont)
    
    #all [] constructs except [scummvm.*], which includes [scummvm], followed by the first description and path
    pattern = re.compile(r'\[(?!scummvm)([^]]*)\](?:.*\n)*?description\s?=\s?(.*)(?:.*\n)*?path\s?=\s?(.*)')
    
    if playlist and not playlist.endswith('.lpl'):
        playlist = playlist + '.lpl'
        
    #in this constructor, if the last is a absolute path returns only that
    playlist = Path(playlist_dir, playlist)
    
    #the playlist to be, scan content dir is a placeholder that disables refresh playlist
    json_lpl = {
        'version': '1.5',
        'default_core_path': f'{core}',
        'default_core_name': 'ScummVM',
        'base_content_directory': f'{content_dir}',
        'label_display_mode': 0,
        'right_thumbnail_mode': 0,
        'left_thumbnail_mode': 0,
        'sort_mode': 0,
        'scan_content_dir': '',
        'scan_file_exts': 'scummvm',
        'scan_dat_file_path': '',
        'scan_search_recursively': True,
        'scan_search_archives': False,
        'scan_filter_dat_content': False,
        'items': []
    }
    invalid_paths = []
    all_paths = []
    #if you have a systemd mount that is 'automount' and has a timeout, and the drive is not mounted, 
    #on each and every call to a path that would be inside the mountpoint, systemd attempts to mount 
    #and waits the timeout. This obviously slows down checking for files. Don't do this.
    #I'll warn once if 'it's taking too long' by pointing to the mountpoint if the exists() call takes
    #more than 1 second 5 times.
    latch_counter = 5
    
    for m in re.finditer(pattern, text):
        label = m.group(2)
        
        filename = re.sub(forbidden, '_', label)
        
        filename = filename + '.scummvm' #final filename
        
        #create scummvm files; all scummvm.ini 'path' game entries are absolute directories.
        game_dir = os.path.abspath(m.group(3))
        
        shortcircuit = False
        if filters:
            for flt in filters:
                shortcircuit = not game_dir.startswith( os.path.abspath(flt) )
                if shortcircuit:
                    break
        
        if not shortcircuit:
            all_paths.append(game_dir)
            path = Path(game_dir, filename)
            json_lpl['items'].append(
            {
                'path': f'{path}',
                'label': label,
                'core_path': f'{core}',
                'core_name': 'ScummVM',
                'crc32': '00000000|crc',
                'db_name': 'ScummVM.lpl'
            })
            t = time.monotonic()
            if os.path.isdir(game_dir):
                elapsed_time = time.monotonic() - t
                with open(path, 'w') as f:
                    f.write(m.group(1))
            else:
                elapsed_time = time.monotonic() - t
                invalid_paths.append(game_dir)
            
            if elapsed_time > 1:
                latch_counter = latch_counter - 1
                if latch_counter == 0 or elapsed_time > 10:
                    latch_counter = 0
                    from textwrap import dedent
                    typer.echo(f'Warning: exists() call is taking too long.')
                    typer.echo(dedent('''\
                    It is likely you have a disconnected external drive and a /etc/fstab file
                    with nofail and/or automount and a too long timeout or no timeout.
                    Without a timeout, the default timeout for automount is 90 seconds!
                    The minimal timeout value, which i recommend in this situation for
                    fstab systemd external drives is x-systemd.device-timeout=1ms.
                    see: https://wiki.archlinux.org/title/fstab#External_devices'''))
    
    #'scan_content_dir' should be the common path, if possible or a empty string if there is no common
    #path or no games are in the playlist at all. That disables the option to 'refresh playlist'.
    if len(all_paths) > 0:
        json_lpl['scan_content_dir'] = os.path.commonpath( all_paths )
    
    #write or rewrite the playlist
    with open(playlist, 'w') as f:
        f.write(json.dumps(json_lpl, indent=4))
    
    if invalid_paths:
        error('Some paths in scummvm.ini are not available.\nWhen they are, please rerun this command to create the .scummvm files:')
        for invalid in invalid_paths:
            error(f'{invalid}')
def main():
    typer.run(mainaux)
    return 0

if __name__ == "__main__":
    error('Please run libretro-scummvm-playlist instead of running the script directly')
    raise typer.Exit(code=1)
