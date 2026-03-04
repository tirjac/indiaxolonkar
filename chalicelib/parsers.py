# -*- coding: utf-8 -*-
#
# @project indiaxolonkar
# @file chalicelib/parsers.py
# @author  Shreos Roychowdhury <shreos@tirja.com>
# @version 1.0.0
# 
# @section DESCRIPTION
# 
#   parsers.py : Request parsing (multipart/urlencoded).
# 
# @section LICENSE
# 
# Copyright (c) 2026 Shreos Roychowdhury.
# Copyright (c) 2026 Tirja Consulting LLP.
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# 

from urllib.parse import parse_qs


class RequestParser:
	@staticmethod
	def parse_urlencoded(body_bytes):
		parsed = parse_qs(body_bytes.decode("utf-8"), keep_blank_values=True)
		return {k: v[0] for k, v in parsed.items()}

	@staticmethod
	def parse_multipart(body, content_type):
		boundary_token = "boundary="
		if boundary_token not in content_type:
			return {}, {}
		boundary = content_type.split(boundary_token, 1)[1]
		if boundary.startswith('"') and boundary.endswith('"'):
			boundary = boundary[1:-1]
		boundary_bytes = f"--{boundary}".encode("utf-8")
		parts = body.split(boundary_bytes)
		fields = {}
		files = {}
		for part in parts:
			if not part or part in (b"--\r\n", b"--"):
				continue
			if part.startswith(b"--"):
				continue
			part = part.lstrip(b"\r\n")
			headers_blob, _, content = part.partition(b"\r\n\r\n")
			content = content.rsplit(b"\r\n", 1)[0]
			headers_text = headers_blob.decode("utf-8", errors="ignore")
			headers = {}
			for line in headers_text.split("\r\n"):
				if ":" in line:
					k, v = line.split(":", 1)
					headers[k.strip().lower()] = v.strip()
			disp = headers.get("content-disposition", "")
			if "name=" not in disp:
				continue
			name = None
			filename = None
			for item in disp.split(";"):
				item = item.strip()
				if item.startswith("name="):
					name = item.split("=", 1)[1].strip('"')
				if item.startswith("filename="):
					filename = item.split("=", 1)[1].strip('"')
			if not name:
				continue
			if filename:
				files[name] = {
					"filename": filename,
					"content_type": headers.get("content-type", "application/octet-stream"),
					"content": content,
				}
			else:
				fields[name] = content.decode("utf-8", errors="ignore")
		return fields, files
