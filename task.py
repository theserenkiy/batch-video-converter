import time
import lib
import os

class Task:

	fields = None
	postponed = 0
	last_error = ""
	info = None

	def __init__(self, tasker, relpath="", hash=None, data=None):
		self.hash = hash or lib.md5(relpath) 
		self.relpath = relpath
		self.tasker = tasker
		self.taskpath = self.tasker.taskdir+"/"+self.hash+".json"
		self.fields = {
			"relpath":relpath, 
			"created":time.time(), 
			"lastrun":0, 
			"completed":0, 
			"meta":{}, 
			"stage":"", 
			"error":"", 
			"fatal":"",
			"error_log": [],
			"info": ""
		}
		for i in self.fields:
			self.__setattr__(i, self.fields[i])

		if data:
			self.load(data)

	def read(self):
		if not os.path.exists(self.taskpath):
			raise Exception(f"Cannot read task for {self.relpath}")
		data = lib.readJSON(self.taskpath)
		self.load(data)

	def commit(self):
		data = self.dump()
		lib.writeJSON(self.taskpath, data)

	def load(self,data):
		for i in self.fields:
			if i in data:
				self.__setattr__(i, data[i])

	def dump(self):
		out = {}
		for i in self.fields:
			out[i] = self.__getattribute__(i)
		return out

	def is_runnable(self):
		return not self.postponed and not self.completed and not self.fatal
	

	def run(self, obj):
		if self.error:
			print(f"On previous run an error occured:\n{self.error}")
		self.last_error = self.error+""
		self.error = ""

		self.lastrun = time.time()

		stages = self.tasker.stages
		start_stnum = stages.index(self.stage) if self.stage else 0

		try:
			for stnum in range(start_stnum, len(stages)):
				self.stage = stages[stnum]
				print(f"\nStage {stnum+1}: {self.stage}")
				foo = "stage_"+self.stage
				if not hasattr(obj,foo):
					raise Exception(f"Cannot find method {foo}")
				
				getattr(obj, foo)(self)
				self.commit()
			
			self.complete()

		except KeyboardInterrupt as e:
			self.err("Keyboard interrupt")
			self.commit()
			raise e
		except Exception as e:
			self.err(e)
			self.commit()
			raise e

	def is_stage_passed(self, stage):
		st = self.tasker.stages
		if stage not in st or not self.stage:
			return 0
		return st.index(self.stage) >= st.index(stage)

	def err(self, e):
		self.error = str(e)
		self.error_log.append([self.stage, lib.now(), self.error+""])
		if self.error.startswith("FATAL"):
			self.fatal = self.error[6:]
	
	def complete(self):
		self.completed = time.time()
		self.commit()
		print(f"Task completed: {self.hash}")

	def postpone(self):
		self.postponed = 1
		self.commit()