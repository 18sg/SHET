from shet.client import ShetClient, shet_action, shet_property
from shet.sync import make_sync
from twisted.internet import threads
import sys
import subprocess
import mpd
import string

mpd_host = "localhost"
mpd_port = 6600

def compose(f, g):
    return lambda *args, **kws: f(g(*args, **kws))


def with_mpd(f):
	"""Connect to mpd before enterning the function, and disconnect afterwards"""
	def g(self, *args, **kwargs):
		self.mpd_client.connect(mpd_host, mpd_port)
		ret_val = None
		
		# Should be able to use a finally here; not sure why it won't work.
		try:
			ret_val = f(self, *args, **kwargs)
		except:
			self.mpd_client.disconnect()
			raise
		
		self.mpd_client.disconnect()
		return ret_val
	return g


class MpdClient(ShetClient):
	
	def __init__(self, dir):
		self.root = dir
		ShetClient.__init__(self)
		
		commands = """next prev pause play toggle stop clear seek move
		              volume repeat random single consume findadd update""".split()
		
		# Because closures in python are... a bit nutty.
		def make_command(name):
			def f(*args):
				return threads.deferToThread(subprocess.call,
				                             ["mpc", name] + map(str, args))
			return f
		
		for command in commands:
			self.add_action(command, make_command(command))
		
		self.mpd_client = mpd.MPDClient()
	
	
	# Get and Set the playlist.
	@shet_property
	@with_mpd
	def playlist(self):
		return [i["file"] for i in self.mpd_client.playlistinfo()]
	
	@playlist.set
	@with_mpd
	def playlist_set(self, new_pls):
		self.mpd_client.clear()
		for song in new_pls:
			self.mpd_client.add(song)
	
	
	# Get and Set the current song, and the position.
	@shet_property
	@with_mpd
	def current_pos(self):
		status = self.mpd_client.status()
		time = int(status["time"].split(':')[0]) if "time" in status else 0
		song = int(status["song"]) if "song" in status else 0
		return (song, time)
	
	@current_pos.set
	@with_mpd
	def current_pos_set(self, val):
		self.mpd_client.seek(val[0], val[1])
	
	@shet_property
	@with_mpd
	def playing(self):
		status = self.mpd_client.status()
		return status["state"] == "play"
	
	@playing.set
	@with_mpd
	def playing_set(self, playing):
		# If it's stopped, play. if it's paused/playing, pause/unpause.
		status = self.mpd_client.status()
		if status["state"] == "stop" and playing:
			self.mpd_client.play()
		elif status["state"] == "pause" and playing:
			self.mpd_client.pause(0)
		elif status["state"] == "play" and not playing:
			self.mpd_client.pause(1)
	
	def file_prefix(self, prefix, f_name):
		return f_name if '://' in f_name else (prefix + f_name)
	
	@shet_action
	@make_sync
	def get_playlist(self, dir, prefix=""):
		"""Get the playlist and current position from a similar client running in
		dir, prefixing all song locations with prefix.
		"""
		playlist = (yield self.get(dir + "/playlist"))
		current_pos = (yield self.get(dir + "/current_pos"))
		self.playlist_set([self.file_prefix(prefix, f_name) for f_name in playlist])
		self.current_pos_set(current_pos)
	
	@shet_action
	@with_mpd
	def current_song_length(self):
		"""Get the current song length."""
		status = self.mpd_client.status()
		return int(status["time"].split(':')[1]) if "time" in status else None
	
	@shet_action
	@with_mpd
	def current_song_pos(self):
		"""get the current sing position."""
		status = self.mpd_client.status()
		return int(status["time"].split(':')[0]) if "time" in status else None
	
	@shet_action
	def current(self, format=None):
		"""Get the current song details, possibly in an arbitrary format.
		See the mpc man page for details on the format string.
		"""
		if format is None:
			return threads.deferToThread(
				compose(string.strip, subprocess.check_output),
				["mpc", "current"])
		else:
			return threads.deferToThread(
				compose(string.strip, subprocess.check_output),
				["mpc", "-f", format, "current"])


if __name__ == "__main__":
	MpdClient(sys.argv[1]).run()
