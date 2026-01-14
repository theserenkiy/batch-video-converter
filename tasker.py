import os
import lib
from task import Task
import time

class Tasker:

	proc = None
	cursor = 0
	stages = None
	taskdir = ""

	def __init__(self, proc, stages):
		self.proc = proc
		self.stages = stages
		
		taskdir_file = lib.resolve(self.proc.data_path+"/taskdir.json")
		self.taskdir = lib.readJSON(taskdir_file,"")

		if not self.taskdir:
			uname = str(int(time.time()*1000))
			self.taskdir = os.path.dirname(__file__)+"/tasks/"+uname
			lib.writeJSON(taskdir_file, self.taskdir)
		
		os.makedirs(self.taskdir,exist_ok=True)
		
		self.hashes = [x[0:-5] for x in os.listdir(self.taskdir)]

	def getTask(self, relpath):
		hash = lib.md5(relpath)
		if hash not in self.hashes:
			return None
		
		task = Task(self, relpath, hash)
		task.read()
		return task
	
	def reset(self):
		self.cursor = 0

	def getUncompletedTasks(self):
		out = []
		for hash in self.hashes:
			d = self.getTaskData(hash)
			if not d.get("completed"): # and not d.get("postponed") and not d.get("fatal"):
				out.append(Task(self, hash=hash, data=d))

		return sorted(out, key=lambda t: t.created)
	
	def getTaskData(self, hash):
		return lib.readJSON(self.taskdir+"/"+hash+".json")
	
	def removeTask(self, task):
		taskpath = self.taskdir+"/"+task.hash+".json"
		if os.path.exists(taskpath):
			os.remove(taskpath)
		self.hashes.remove(task.hash)

	def getStat(self):
		stat = {"total": len(self.hashes), "completed": 0, "active": 0, "error": 0, "fatal": 0}
		for hash in self.hashes:
			d = self.getTaskData(hash)
			if d["completed"]:
				stat["completed"] += 1
			elif d["fatal"]:
				stat["fatal"] += 1
			elif d["error"]:
				stat["error"] += 1
			else: stat["active"] += 1
		return stat
	
	def printStat(self,header=None):
		print(header or "Task statistics:")
		stat = self.getStat()
		for k,v in stat.items():
			print(f"{k}: {v}")


	def create(self, relpath):
		t = Task(self,relpath)
		self.hashes.append(t.hash)
		return t

	
	