browser_playable_extensions = ('mp4','mpeg4','webm','ogg')

#presets for dimension-to-bitrate decision
presets = {
	"high": {
		#if LARGEST side > 1920px -> convert with video bitrate 3000kbps
		"1920": 3000,
		"1280": 2000,
		"800": 1300,
		"0": 1000
	},
	"mid": {
		"1920": 2800,
		"1280": 1800,
		"800": 1100,
		"0": 800
	},
	"low": {
		"1920": 2000,
		"1280": 1500,
		"800": 1000,
		"0": 800
	}
}

# default config
# You can override this by placing file _conv_conf.json to working folder (and/or subfolders).
# That will work for given folder and all subfolders recursively.
basic_conf = {
	"worst_rate": 0.7,		# max relation of file sizes converted to original
	"max_side_size": 1280,	# max not-resizable size of LARGEST side
	"audio_bitrate": 128,
	"preset": "mid",
	"result_basepath": ".",
	"tmpdir": "d:/var/convtmp",
	"skip_regex": "",
	"copy_source_to_temp": 1,
	"force_browser_playable": True,		# if file not playable in browser (i.e. MP4, WEBM, OGG) 
										# convert it despite given max_rate/max_side_size conditions
	"skip_nested_configs": False		# If _conv_conf found in subfolder - skip it
}