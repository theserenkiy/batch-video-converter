import os
import re
import lib
from conv_process import ConvProcess
from tasker import Tasker
import time
from conv_file import ConvFile
import shutil

os.system("title CONV")

class Conv(ConvProcess):

	def __init__(self):
		super().__init__("conv")
		self.resetLog()

		self.ffmpeg_log_dir = self.data_path+"/ffmpeg_log"
		os.makedirs(self.ffmpeg_log_dir, exist_ok=True)

		clist = lib.readJSON(self.data_path+"/convlist.json",[])
		self.convlist = sorted(clist, key=lambda x: x["rate"])

		self.stages = ["convert", "move", "remove_source", "rename"]
		self.tasker = Tasker(self, self.stages)


	def run(self):
		try:
			self.processUncompletedTasks()
			
			listlen = len(self.convlist) 
			for i,item in enumerate(self.convlist):
				info = f"{i+1}/{listlen}"
				t = self.tasker.getTask(item["relpath"])
				if t:
					if t.info != info:
						t.info = info
						t.commit()
					continue
				t = self.tasker.create(item["relpath"])
				t.meta = item
				t.info = info
				t.commit()
				self.runTask(t)

				time.sleep(1)

			print("======================")
			print("Script done!")
			self.tasker.printStat()
		
		except Exception as e:
			print(f"ERROR: {e}")

	def processUncompletedTasks(self):
		print("Processing previously uncompleted tasks...")
		tasks = self.tasker.getUncompletedTasks()
		for task in tasks:
			if task.is_stage_passed("convert") or task.fatal:
				cl_item = next((item for item in self.convlist if item["relpath"]==task.relpath), None)
				if cl_item and cl_item["created"] > task.created:
					self.tasker.removeTask(task)
					continue
				
			if task.fatal:
				continue
			self.runTask(task)
		
		print("\nUncompleted tasks done!")

	def runTask(self, task):
		print("\n####################################################")
		print(f"Run task {task.hash} ({task.info})")
		print(f"File: {task.relpath}")
		
		try:
			task.run(self)
		except KeyboardInterrupt:
			raise Exception("User abort")
		except Exception as e:
			self.err(f"{e} @ {task.relpath}")
			if str(e).startswith("DISK "):
				raise Exception("Disk error")
		
	def mkTmpPath(self, tmpdir, tmpname):
		tmpdir = lib.resolve(tmpdir)
		# print(f"Make TMP dir {tmpdir}")
		os.makedirs(tmpdir,exist_ok=True)
		return tmpdir+"/"+tmpname 
	
	def checkDiskConnected(self):
		if not os.path.exists(lib.resolve(".")):
			raise("DISK NOT CONNECTED")

	def precopy(self, task):
		m = task.meta

		if not m.get("copy_source_to_temp"):
			print("No need precopy")
			return

		src = lib.resolve(m["relpath"])
		dst = self.mkTmpPath(m["tmpdir"],m["hash"]+".src."+m["source"]["ext"])
		m["tmp_source"] = dst

		if os.stat(src).st_size != m["source"]["size"]:
			raise Exception("FATAL source file size mismatch")

		lib.removeFile(dst,silent=1)

		print("Copying source file to temp dir:")
		print(f"{m['relpath']} -> {dst}")
		shutil.copy(src, dst)


	def stage_convert(self,task):
		m = task.meta
		self.checkDiskConnected()
		self.precopy(task)

		tmp_path = self.mkTmpPath(m["tmpdir"],m["hash"]+".mp4")
	
		srcpath = m.get("tmp_source") or lib.resolve(m["relpath"]) 

		if not os.path.exists(srcpath):
			raise Exception("FATAL source file not found")

		print(f'Source size: {m["source"]["size"]/(1 << 20):6.2f}MB')
		# print(f"Source path: {srcpath}")
		print(f"Dest path: {tmp_path}")

		try:
			cf = ConvFile(srcpath)

			cf.ffmpeg_log_path = self.ffmpeg_log_dir+"/"+task.hash+".log"

			if task.last_error.startswith("File consistency error"):
				print("Checking consistency...")
				cf.check_consistency()

			src = m["source"]
			info = f'Bitrate: {src["full_bitrate"]} -> {m["vb"]+m["ab"]}'
			if m["resize"]:
				sd = src["dim"]
				dd = m["resize"]
				info += f'; Resize: {sd[0]}x{sd[1]} -> {dd[0]}x{dd[1]}'
			print("Converting. "+info)
			cf.convert(tmp_path, m["vb"], m["ab"], m["resize"], dbg=0)

			m["result_size"] = os.stat(tmp_path).st_size
			
			lib.removeFile(m.get("tmp_source"), tries=3)
		except Exception as e:
			try:
				lib.removeFile(m.get("tmp_source"), tries=3)
				lib.removeFile(tmp_path, tries=3)
			except Exception as e2:
				print(f"On error cleanup failed: {e2}")
			raise e

		
	def stage_move(self,task):
		m = task.meta
		self.checkDiskConnected()
		tmp_path = self.mkTmpPath(m["tmpdir"],m["hash"]+".mp4")

		target_relpath_noext = re.sub(r"\.[^\.]+$","", m["relpath"])
		temp_relpath = target_relpath_noext + ".conv.mp4"
		target_path = lib.resolve(m["result_basepath"]+"/"+temp_relpath)
		print(f"SOURCE PATH: {tmp_path}")
		print(f"TARGET PATH: {target_path}")

		if os.path.exists(target_path) and os.stat(target_path).st_size == m.get("result_size"):
			print("File already moved!")
			return 
		
		if not os.path.exists(tmp_path):
			raise Exception(f'FATAL missing tmp_path {tmp_path}')
		

		try:
			shutil.move(tmp_path, target_path)
		except Exception as e:
			raise Exception(f"Cannot move {tmp_path} -> {target_path}: {e}")
 
	def stage_remove_source(self, task):
		# raise Exception("Cannot remove yet")
		m = task.meta
		self.checkDiskConnected()
		src_path = lib.resolve(task.relpath,0)
		lib.removeFile(src_path)

	def stage_rename(self, task):
		# raise Exception("Cannot remove yet")
		m = task.meta
		self.checkDiskConnected()
		relpath_noext = re.sub(r"\.[^\.]+$","", task.relpath)
		bpath = lib.resolve(relpath_noext,0)
		src_path = bpath+".conv.mp4"
		dst_path = bpath+".mp4"

		print(f"SOURCE PATH: {src_path}")
		print(f"TARGET PATH: {dst_path}")

		if not os.path.exists(src_path):
			if os.path.exists(dst_path) and os.stat(dst_path).st_size == m.get("result_size"):
				print("Already moved. Do nothing!")
				return
			raise Exception("FATAL missing source file")

		try:
			shutil.move(src_path, dst_path)
		except Exception as e:
			raise Exception(f"Cannot move {src_path} -> {dst_path}: {e}")

Conv().run()