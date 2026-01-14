from pathlib import Path
import json
import os
import hashlib
from datetime import datetime
import time

def readJSON(path,default=None):
	if not os.path.exists(path):
		return default
	with open(path,"r",encoding="utf-8") as f:
		try:
			return json.loads(f.read().replace("\x00",""))
		except Exception as e:
			raise Exception(f"Read JSON {path}: {e}")

def writeJSON(path, data):
	f = open(path, "w", encoding="utf-8")
	f.write(json.dumps(data, indent="\t", ensure_ascii=False))
	f.close()

def resolve(path, slashes=1):
	path = os.path.abspath(str(Path(path).resolve()))
	return path.replace("\\","/") if slashes else path

def md5(s):
	md5 = hashlib.md5()
	md5.update(s.encode("utf-8"))
	return str(md5.hexdigest())

def now(format='%Y-%m-%d %H:%M:%S'):
	return datetime.now().strftime(format)

def removeFile(path, tries=1, delay=1, silent=0):
	if not path:
		return
	if not os.path.exists(path):
		if not silent:
			print(f"Cannot remove {path}: not exists")
		return
	
	lasterr = None
	for i in range(tries):
		try:
			trymsg = f". Try {i+1}/{tries}" if i else ""
			print(f"Deleting file {path}{trymsg}")
			os.chmod(path, 0o777)
			os.remove(path)
			return
		except Exception as e:
			lasterr = e
			if tries > 1:
				print(f"Fail. One more try in {delay} sec...")
				time.sleep(delay)

	raise Exception(f"Cannot delete {path}: {lasterr}")