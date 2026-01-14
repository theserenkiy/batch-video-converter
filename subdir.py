import os
import re
import lib
import conf
from file_info import FileInfo

class Subdir:
	convlist = None
	parent = None
	relpath = ""
	basepath = ""
	datadir = ""
	conf = None
	level = 0

	def __init__(self,convlist,relpath="",parent=None):
		self.convlist = convlist
		self.parent = parent
		self.relpath = relpath
		self.path = self.convlist.basepath + ("/" + relpath if relpath else "")
		self.datadir = self.path+"/_conv"

		self.conf = {}
		# prepare config
		self.conf.update(conf.basic_conf.copy())

		if self.parent:
			self.conf.update(self.parent.conf.copy())
			self.level = self.parent.level + 1

		conf_file = self.datadir + "/conf.json"
		if not self.conf.get("skip_nested_configs"):
			self.conf.update(lib.readJSON(conf_file,{}))

		# .noconv file works even if skip_nested_configs set
		if os.path.exists(self.path+"/.noconv"):
			self.conf["noconv"] = 1

		# read cache
		cache = lib.readJSON(self.datadir + "/cache.json",{})
		for relpath in cache:
			item = cache[relpath]
			self.convlist.cacheAdd(item, self.mkrelpath(relpath))
	


	def mkrelpath(self,subpath):
		return self.relpath+"/"+subpath if self.relpath else subpath



	def collect(self):
		if self.conf.get("noconv"):
			self.convlist.warn(f"Noconv set for {self.relpath}")
			return
		ff = os.listdir(self.path)
		subdirs = []
		for f in ff:
			frel = self.relpath + "/" + f if self.relpath else f
			fabs = self.convlist.basepath + "/" + frel
			# print(f"FABS: {fabs}")
			if os.path.isfile(fabs):	
				ne = os.path.splitext(f)
				ext = ne[1][1:].lower()
				bname = ne[0]
				# print(f"NE {ne}")
				if not re.search(r"^(mpe?g|mp4|mkv|avi|flv|mov|wmv|ts)$",ext):
					continue

				print(f"{'	'*self.level}{f}")
				
				size = os.stat(fabs).st_size

				finfo = {"relpath": frel, "fname": f, "bname": bname, "ext": ext, "size": size}
				
				finfo_ = self.convlist.cacheGet(frel)
				if finfo_ and (finfo_["size"] != size or "error" in finfo_):
					finfo_ = None
				
				if not finfo_:
					try:
						fi = FileInfo(fabs)
						finfo_ = fi.getInfo()
					except Exception as e:
						finfo["error"] = str(e)
				
				if(finfo_):
					finfo.update(finfo_)
				elif "error" not in finfo:
					finfo["error"] = "unknown error"

				self.convlist.addFile(finfo, self.conf.copy())
				err = finfo.get("error")
				if err:
					self.convlist.err(f"{err} @ {frel}")

			
			# if isdir
			else:
				if f[0] != "_":
					subdirs.append((frel,f))

		for d in subdirs:
			print(f"{'	'*self.level}[ {d[1]} ]")
			sd = Subdir(self.convlist, d[0], self)
			sd.collect()