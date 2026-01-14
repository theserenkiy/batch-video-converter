from pathlib import Path
import os 
import lib
import re
from subdir import Subdir
import conf
from conv_process import ConvProcess
import time


class Convlist(ConvProcess):
	all_files = []
	
	cache = {}
	files = []

	def __init__(self):
		super().__init__("convlist")
		self.resetLog()
		self.cache_path = self.data_path+"/cache.json"
		self.cache = lib.readJSON(self.cache_path,{})

		conf_file = self.data_path+"/conf.json"
		if not os.path.exists(conf_file):
			lib.writeJSON(conf_file,{})
		

	def save_cache(self):
		print("Saving cache...")
		lib.writeJSON(self.cache_path, self.cache)
		print("OK")

	def run(self):
		
		try:
			sd = Subdir(self)
			sd.collect()
		except Exception as e:
			self.save_cache()
			self.err(f"Subdir error: {e}")
		except KeyboardInterrupt:
			self.save_cache()
			self.err(f"Aborted by user")
			exit()
			
		lib.writeJSON(self.data_path+"/files.json", self.files)

		print("====================================")
		print(f"{len(self.files)} files found!")

		self.printErrorsWarning()

		total_size = 0
		freed_space = 0
		out = []
		for f in self.files:
			d = f["data"]
			c = f["conf"]
			total_size += d["size"] 
			if d.get("error"):
				continue
			
			skip_regex = c.get("skip_regex")
			if skip_regex and re.search(skip_regex,d["relpath"],flags=re.IGNORECASE):
				self.warn(f"rejected by regex: {d['relpath']}")
				continue

			dest = {
				"relpath": d["relpath"],
				"created": time.time()
			}
			dim = d["dim"]
			rsz = c["max_side_size"]/max(dim)
			if rsz < 1:
				dim = [round(x*rsz) for x in d["dim"]]
				dim = [x+1 if x%2 else x for x in dim]
				dest["resize"] = dim
			else:
				dest["resize"] = None
			
			preset = conf.presets.get(c["preset"]) or conf.presets["mid"]
			largest = max(dim)
			bitrate = 0
			for side in preset:
				bitrate = preset[side]
				if int(side) <= largest:
					break

			dest["vb"] = bitrate
			dest["ab"] = c["audio_bitrate"]

			full_bitrate = bitrate + c["audio_bitrate"]
			rate = full_bitrate/d["full_bitrate"]

			if rate > c["worst_rate"] \
				and (not c["force_browser_playable"] or d["ext"] in conf.browser_playable_extensions):
				continue

			dest["rate"] = round(rate,2)
			
			new_sz = int(d["size"]*rate)
			freed_space += d["size"]-new_sz

			dest["tmpdir"] = lib.resolve(c["tmpdir"]) if "tmpdir" in c else "./_conv/tmp"			
			hash = lib.md5(d["relpath"])
			# print(f"UNAME {uname}")
			dest["hash"] = hash
			dest["result_basepath"] = c["result_basepath"]
			dest["copy_source_to_temp"] = c["copy_source_to_temp"]
			dest["source"] = d
			

			out.append(dest)

		print(f"{len(out)} files will be converted:\n")

		# for d in out:
		# 	print(f'{d["relpath"][0:64].ljust(64)}: {d["source"]["full_bitrate"]} -> {d["vb"]+d["ab"]}')

		print("\n")
		print(f"Total size: {(total_size/(1 << 20)):10.2f} MB")
		print(f"Space will be freed: {(freed_space/(1 << 20)):10.2f} MB")

		lib.writeJSON(self.data_path+"/convlist.json", out)
			



	def cacheGet(self,relpath):
		return self.cache[relpath] if relpath in self.cache else None

	def cacheAdd(self,data,relpath=None):
		if not relpath:
			relpath = data["relpath"]
		else:
			data["relpath"] = relpath
		self.cache[relpath] = data

	def addFile(self,data,cfg):
		self.files.append({"data": data, "conf": cfg})
		self.cacheAdd(data)



cl = Convlist()
cl.run()
