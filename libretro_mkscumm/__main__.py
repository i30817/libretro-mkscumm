#! /usr/bin/env python3



#dependency install for testing: pip3 install typer[all]

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
#It has a option to set another name for the resulting playlist and to 'ignore' one or more base directories
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

###########################################
########### SCRIPT SETTINGS ###############
###########################################


CONFIG = Path(Path.home(), '.config', 'retroarch', 'retroarch.cfg')

#00-1f are ascii control codes, rest is 'normal' illegal windows filename chars according to powershell + &
forbidden	=	r'[\u0022\u003c\u003e\u007c\u0000\u0001\u0002\u0003\u0004\u0005\u0006\u0007\u0008' + \
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

def mainaux(cfg: Path = typer.Argument(CONFIG, help='Path to the retroarch cfg file.'),
		playlist: str = typer.Option('ScummVM.lpl', help='Playlist name to create. If not provided, ScummVM.lpl is created or recreated if it exists.'),
		filters: Optional[List[str]] = typer.Option(None, help='Filters for game paths, you can add this option more than once. If the option is used, only game entries in scummvm.ini whose paths start with one of these create a .scummvm file or get added to the playlist, use it if you want multiple playlists.')
	):
	"""
	Creating playlists for the scummvm core in retroarch is complicated.

	1. Add the game directories to the scummvm.ini file in the Retroarch system directory, by starting the core and 'mass add' all the games, filtering out any false positives.
	
	2. Create .scummvm files for each and every game entry in the created scummvm.ini, in the game dir so the manual scanner can scan the .scummvm files and assign it a playlist entry.

	No more. This creates the .scummvm files, then creates a playlist for it, if the scummvm.ini file exists in your Retroarch system dir. In short, you only need to mass add and invoke this program.

	To update this program with pip installed, type:

	pip3 install --upgrade git+https://github.com/i30817/libretro-mkscumm.git
	
	If you'd like to try to download missing coverart until a PR with scummvm names is added to the thumbnail server try to install and use libretrofuzz:
	
	pip3 install git+https://github.com/i30817/libretrofuzz.git
	"""
	if not cfg.exists() or not cfg.is_file():
		typer.echo(f'Invalid Retroarch cfg file: {cfg}')
		raise typer.Abort()
	
	playlist_dir = getPath(cfg, 'playlist_directory')
	
	if not playlist_dir.exists() or not playlist_dir.is_dir() or not os.access(playlist_dir, os.W_OK):
		typer.echo(f'Invalid Retroarch playlist directory: {playlist_dir}')
		raise typer.Abort()

	system_dir = getPath(cfg, 'system_directory')	
	if not system_dir.exists() or not system_dir.is_dir():
		typer.echo(f'Invalid Retroarch system directory: {system_dir}')
		raise typer.Abort()

	system   = Path(system_dir, 'scummvm.ini')
	if not system.exists() or not system.is_file():
		typer.echo(f'Invalid scummvm.ini file: {system}')
		raise typer.Abort()
		
	cores_dir  = getPath(cfg, 'libretro_directory')
	if not cores_dir.exists() or not cores_dir.is_dir():
		typer.echo(f'Invalid Retroarch cores directory: {cores_dir}')
		raise typer.Abort()
	core = os.path.abspath( Path(cores_dir, 'scummvm_libretro' + ( '.dll' if os.name == 'nt' else '.so' ) ) )
	
	content_dir  = getPath(cfg, 'rgui_browser_directory')
	if not content_dir:
		content_dir = ''
	
	with open(system) as f:
		text = f.read()
	
	#all [] constructs except [scummvm.*], which includes [scummvm], followed by the first description and path
	pattern = re.compile(r'\[(?!scummvm)(.*)\](?:.*\n)*?description=(.*)(?:.*\n)*?path=(.*)')
	
	if playlist and not playlist.endswith('.lpl'):
		playlist = playlist + '.lpl'
		
	#in this constructor, if the last is a absolute path returns only that
	playlist = Path(playlist_dir, playlist)
	
	#the playlist to be
	json_lpl = {
		'version': '1.5',
		'default_core_path': f'{core}',
		'default_core_name': 'ScummVM',
		'base_content_directory': f'{content_dir}',
		'label_display_mode': 0,
		'right_thumbnail_mode': 0,
		'left_thumbnail_mode': 0,
		'sort_mode': 0,
		'scan_content_dir': f'{content_dir}',
		'scan_file_exts': 'scummvm',
		'scan_dat_file_path': '',
		'scan_search_recursively': False,
		'scan_search_archives': False,
		'scan_filter_dat_content': False,
		'items': []
	}
	invalid_paths = []
	
	#if you have a systemd mount that is 'automount' and has a timeout, and the drive is not mounted, 
	#on each and every call to a path that would be inside the mountpoint, systemd attempts to mount 
	#and waits the timeout. This obviously slows down checking for files. Don't do this.
	#I'll warn if 'it's taking too long' by pointing to the mountpoint.
	
	for m in re.finditer(pattern, text):
		label = m.group(2)
		
		filename = re.sub(forbidden, '_', label)
		
		filename = filename + '.scummvm' #final filename
		
		#create scummvm files; all scummvm.ini 'path' game entries are absolute directories.
		game_dir = os.path.abspath(m.group(3))+os.sep
		
		shortcircuit = False
		if filters:
			for flt in filters:
				shortcircuit = not game_dir.startswith( os.path.abspath(flt)+os.sep )
				if shortcircuit:
					break
		
		if not shortcircuit:
			t = time.monotonic()
			if os.path.exists(game_dir):
				path = Path(game_dir, filename)
				with open(path, 'w') as f:
					f.write(m.group(1))
				
				json_lpl['items'].append(
				{
					'path': f'{path}',
					'label': label,
					'core_path': f'{core}',
					'core_name': 'ScummVM',
					'crc32': '00000000|crc',
					'db_name': 'ScummVM.lpl'
				})
			else:
				invalid_paths.append(game_dir)
			elapsed_time = time.monotonic() - t
			if elapsed_time > 10:
				typer.echo(f'Warning: check for file existance took too long {elapsed_time}')
				typer.echo(
'''It is likely you have a disconnected external drive and a /etc/fstab file
with nofail and/or automount and a too long timeout or no timeout.
Without a timeout, the default timeout for automount is 90 seconds!
The minmal timeout value, which i recommend in this situation for
fstab systemd external drives is x-systemd.device-timeout=1ms.
see: https://wiki.archlinux.org/title/fstab#External_devices
'''
				)
	#write or rewrite the playlist
	with open(playlist, 'w') as f:
		f.write(json.dumps(json_lpl, indent=4))
	
	if invalid_paths:
		typer.echo('Paths in scummvm.ini that are not accessible and therefore didn\'t have .scummvm files created or were added to the playlist:')
		for invalid in invalid_paths:
			typer.echo(f'{invalid}')
def main():
	typer.run(mainaux)
	return 0

if __name__ == "__main__":
	typer.run(mainaux)
