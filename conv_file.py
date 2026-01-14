from conv_file_basic import ConvFileBasic	
import os
import shutil
import pathlib
import time
import json

class ConvFile(ConvFileBasic):

	duration_s = 0
	framerate = 0
	progress = None

	tmp_path = ""
	target_path = ""
	fail_target_path = ""

	speed_rnd_frame = None
	speed_rnd_frame_sz = 8
	speed_rnd_index = 0

	def __init__(self,path):
		super().__init__(path)

	
	def parse_progress(self,s):
		res = self.rex(r"frame\=\s*(\d+).+?\stime\=(\d+\:\d+\:\d+).+?\sspeed\=\s*([\d\.]+)",s)
		if not res:
			return None
		
		cur_sec = self.get_sec(res[1])
		progress = cur_sec / self.duration_s if self.duration_s else -1
		p = {
			"progress": progress,
			"frame": int(res[0]),
			"speed": float(res[2])
		}

		if not self.speed_rnd_frame:
			self.speed_rnd_frame = [p["speed"] for i in range(self.speed_rnd_frame_sz)]

		self.speed_rnd_frame[self.speed_rnd_index % self.speed_rnd_frame_sz] = p["speed"]
		rnd_speed = sum(self.speed_rnd_frame) / self.speed_rnd_frame_sz
		
		p["estimated_s"] = int((self.duration_s - cur_sec)/rnd_speed) if progress > 0 else -1
		p["estimated"] = f"{int(p['estimated_s']/60)}:"+f"{int(p['estimated_s']%60)}".rjust(2,"0") if p["estimated_s"] >= 0 else None
		p["errors"] = self.consistency_errors

		self.progress = p
		return self.progress	
	
	def print_progress(self,p):
		progr = p["progress"]
		pline = ("="*int(progr*50)).ljust(50) if progr >= 0 else "unknown"
		pline = f"[{pline}]"
		if progr >=0:
			pline = f"{pline} {int(progr*100)}%"
		
		est = f" est: {p['estimated']}" if p['estimated'] else ""
		print(f"{pline} {p['speed']}x{est} (errors: {p['errors']})    \r",end="")
	
	def process_line(self,s):
		if not self.duration_s and not self.progress:
			self.parse_duration_bitrate(s)
		
		self.parse_consistency_error(s)
		
		p = self.parse_progress(s)
		if p:
			self.print_progress(p)


	def convert(self, target_path, vb, ab, target_dim=None, dbg=False):
		
		if dbg:
			cmd = f'-c:v copy -c:a copy '
		else:
			cmd = f'-c:v libx264 -b:v {vb}k -b:a {ab}k -max_muxing_queue_size 1024 '

		if target_dim:
			cmd += f' -vf scale={target_dim[0]}:{target_dim[1]} '
		
		cmd = f'ffmpeg -i "{self.path}" -y {cmd} "{target_path}"'

		if dbg:
			print(f"RUN CMD: {cmd}")

			# return

		try:
			# print(f"RUN CMD: {cmd}")
			
			
			# return
			self.runCmd(cmd)
			print("")
			# return

			
			
		except Exception as e:
			print("")
			raise e


	
