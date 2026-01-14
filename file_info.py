from conv_file_basic import ConvFileBasic
import os
import re

class FileInfo(ConvFileBasic):

	def __init__(self, path):
		super().__init__(path)

	def getInfo(self):
		try:
			self.runCmd(f'ffprobe "{self.path}"')
		except Exception as e:
			raise Exception(f"Cannot get ffmpeg info: {e}")

		return self.parseResult("\n".join(self.line_log))


	def parseResult(self,s):
		out = {
			"duration_s": self.duration_s
		}

		for stream in ["video", "audio"]:
			res = self.rex(rf"Stream #\d\:\d.*?\: ({stream})(.+?)(?=Stream #|$)",s,re.IGNORECASE | re.DOTALL)
			if not res:
				raise Exception(f"Missing {stream} stream data")
			txt = res[1]

			if stream=="video":
				res = self.rex(r"\s(\d{3,4})x(\d{3,4})",txt)
				out["dim"] = [int(x) for x in res] if res else [0,0]
				# out["largest_side"] = max(out["dim"])

				mm = self.rex(r" ([\d\.]+)\s*fps\,",s)
				out["framerate"] = round(float(mm[0])) if mm else 0

			# res = self.rex(r"\s([\d\.]+)\s*kb\/s",txt)
			# if res:
			# 	out[stream+"_bitrate"] = round(float(res[0]))
			# 	continue

			# res = self.rex(r"\sBPS\s+\:\s(\d+)",txt)
			# if res:
			# 	out[stream+"_bitrate"] = round(int(res[0])/1024)
			# 	continue
			
		if not self.bitrate:
			raise Exception("missing bitrate")
		out["full_bitrate"] = self.bitrate
		# out["video_bitrate"] + out["audio_bitrate"]
		return out


	