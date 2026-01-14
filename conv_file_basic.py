import subprocess
import sys
import re
import os
import lib

class ConvFileBasic:

	path = ""
	dir = ""
	fname = ""
	ext = ""
	datadir = ""
	duration_s = 0
	bitrate = 0
	consistency_errors = 0
	consistency_error_threshold = 10
	ffmpeg_log_path = ""

	line_log = None

	def __init__(self,path):
		self.path = lib.resolve(path)
		self.dir = os.path.dirname(self.path)
		self.datadir = self.path+"/_conv"
		bname = os.path.basename(self.path)
		name_ext = os.path.splitext(bname)
		self.fname = name_ext[0]
		self.ext = name_ext[1].lower()
		self.line_log = []

		

	def exists(self):
		return os.path.exists(self.path)
	
	def rex(self,rex,s,flags=0):
		mm = re.findall(rex,s,flags=flags)
		if mm and len(mm):
			# print(mm)
			return mm[0] if type(mm[0]) == tuple else [mm[0]]
		return None
	
	def get_sec(self,time_str):
		res = self.rex(r"(\d+)\:(\d+)\:(\d+)",time_str)
		if not res:
			return None
		time = [int(x) for x in res]
		return time[0]*3600 + time[1]*60 + time[2]

	def parse_duration_bitrate(self, s):
		res = self.rex(r"Duration\: (\d+\:\d+\:\d+).+?bitrate\:\s*(\d+)",s)
		if not res:
			return
		# print(f"Duration: {res[0]}")
		self.duration_s = self.get_sec(res[0])
		self.bitrate = int(res[1])

	def process_line(self, s):
		if not self.duration_s:
			self.parse_duration_bitrate(s)
		
		self.parse_consistency_error(s)
		pass

	
	def log_line(self,s):
		s = s.strip()
		if self.ffmpeg_log_path:
			with open(self.ffmpeg_log_path, "a") as f:
				f.write(s+"\n")
		if s:
			self.line_log.append(s)

	def remove_file(self, path):
		try:
			os.remove(path)
			return 1
		except Exception:
			print(f"!!! Cannot remove file {path}.\nThe file converted will be saved as *.done.mp4.\nRun `convcleanup` afterwards.\n")
			return 0
		
	def parse_consistency_error(self, s):
		mm = re.findall(r"^(\[.+? @ .+?\] (Error .+)|(Error .+))",s)
		if len(mm):
			self.consistency_errors += 1
			if self.consistency_errors >= self.consistency_error_threshold:
				raise Exception(f"File consistency error: {mm[0][1] or mm[0][2]}")

	def check_consistency(self):
		self.runCmd(f'ffmpeg -i "{self.path}" -f null -')
		self.consistency_errors = 0

	def runCmd(self, cmd):

		if self.ffmpeg_log_path:
			open(self.ffmpeg_log_path, "w").close()
			
		try:
			process = subprocess.Popen(
				cmd,
				shell=True,
				stdout=subprocess.PIPE,
				stderr=subprocess.STDOUT, # Redirect stderr to stdout for combined output
				text=True, # Decode output as text (Python 3.7+)
				bufsize=1 # Line buffer the output
			)

		
			# Read and print the output line by line as it becomes available
			for s in process.stdout:
				self.log_line(s)
				self.process_line(s)

				
			# Wait for the process to complete and get the return code
			process.wait()

			if process.returncode != 0:
				raise Exception(f"Command failed with return code {process.returncode}: {self.line_log[-1:][0] if len(self.line_log) else '[unknown]'}")
			
			return 1

		except KeyboardInterrupt as e:
			# This block is executed when the user presses Ctrl+C
			print("\nMain script interrupted (KeyboardInterrupt). Terminating subprocess...")
			self.killProcess(process)
			raise e

		except FileNotFoundError:
			raise Exception(f"File not found")
		except Exception as e:
			self.killProcess(process)
			raise Exception(f"{e}")
		
	def killProcess(self, process):
		print("\nTerminating FFMPEG on error...")
		cmd = f"TASKKILL /F /T /PID {process.pid}"
		os.system(cmd)
		process.kill()