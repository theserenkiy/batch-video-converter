import lib
import sys
import os
from datetime import datetime

class ConvProcess:
	
	name = ""
	basepath = ""
	data_path = ""
	log_empty = 0
	curlog = None

	def __init__(self,name):
		self.name = name
		self.basepath = lib.resolve(".")
		self.data_path = self.basepath +"/_conv"
		os.makedirs(self.data_path, exist_ok=True)
		self.dir_path_len = len(self.basepath)
		self.log_file = self.data_path + f"/{self.name}_log.txt"
		if not os.path.exists(self.log_file):
			open(self.log_file,"w").close()
			self.log_empty = 1
		
		self.curlog = {"error":[], "warn":[], "info":[]}

	def resetLog(self):
		if self.log_empty:
			return
		with open(self.log_file,"w") as f:
			f.write("")

	def log(self,lvl,s):
		self.log_empty = 0
		self.curlog[lvl].append(s)
		msg = f"{lvl.upper().ljust(5)}: {s}"
		print(" >> "+msg) #, file=sys.stderr) 
		f = open(self.log_file,"a",encoding="utf-8")
		f.write(f"{lib.now()} {msg}\n")
		f.close()

	def err(self,s):
		self.log("error",s)

	def warn(self,s):
		self.log("warn",s)

	def info(self,s):
		self.log("info",s)
	
	def printErrorsWarning(self):
		errlen = len(self.curlog["error"])
		if errlen:
			print(f"WARNING: {errlen} errors occured! See _conv/{self.name}_log.txt")