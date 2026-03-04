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
