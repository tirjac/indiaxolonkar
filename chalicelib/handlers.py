import json
import uuid
import base64
from chalice import Response
from .parsers import RequestParser
from .timeutil import now_iso
from chalicelib.seo_page import render_share_page


class Handlers:
	def __init__(self, config, clients, templates, auth, tasks):
		self._config = config
		self._clients = clients
		self._templates = templates
		self._auth = auth
		self._tasks = tasks

	def _html_response(self, body, set_cookie=None, status=200):
		headers = {"Content-Type": "text/html; charset=utf-8"}
		if set_cookie:
			headers["Set-Cookie"] = set_cookie
		return Response(body=body, status_code=status, headers=headers)


	def _json_response(self, payload, set_cookie=None, status=200):
		headers = {"Content-Type": "application/json"}
		if set_cookie:
			headers["Set-Cookie"] = set_cookie
		return Response(body=json.dumps(payload), status_code=status, headers=headers)

	def _redirect(self, location, set_cookie=None, status=302):
		headers = {"Location": location}
		if set_cookie:
			headers["Set-Cookie"] = set_cookie
		return Response(body="", status_code=status, headers=headers)

	def _base_path(self, request):
		if not request:
			return ""
		headers = request.headers or {}
		host = (headers.get("host") or "").split(":")[0].strip().lower()
		custom_domain = (getattr(self._config, "CUSTOM_DOMAIN", "") or "").strip().lower()
		if custom_domain and host == custom_domain:
			return ""
		prefix = headers.get("x-forwarded-prefix", "").strip()
		if prefix and prefix != "/":
			return prefix.rstrip("/")
		stage = ""
		if request.context:
			stage = request.context.get("stage") or ""
		if stage and stage != "$default":
			return f"/{stage}"
		return ""

	def _with_base_path(self, location, base_path):
		if not base_path:
			return location
		if location.startswith("http://") or location.startswith("https://"):
			return location
		if not location.startswith("/"):
			location = f"/{location}"
		return f"{base_path}{location}"

	def home(self, request):
		user_id, set_cookie = self._auth.ensure_session(request.headers)
		is_logged_in = user_id and not str(user_id).startswith("anon:")
		base_path = self._base_path(request)
		body = self._templates.render(
			"home.html",
			categories=self._config.CATEGORY_OPTIONS,
			is_logged_in=is_logged_in,
			debug_mode=self._config.DEBUG_MODE,
			base_path=base_path,
		)
		return self._html_response(body, set_cookie=set_cookie)

	def terms(self, request):
		return self._html_response(self._templates.render("terms.html", base_path=self._base_path(request)))

	def privacy(self, request):
		return self._html_response(self._templates.render("privacy.html", base_path=self._base_path(request)))

	def login(self, request):
		base_path = self._base_path(request)
		if request.method == "GET":
			return self._html_response(self._templates.render("login.html", message=None, require_code=False, email=None, base_path=base_path))

		content_type = request.headers.get("content-type", "")
		raw_body = request.raw_body or b""
		if "application/x-www-form-urlencoded" in content_type:
			data = RequestParser.parse_urlencoded(raw_body)
		else:
			data = request.json_body or {}

		email = (data.get("email") or "").strip().lower()
		password = data.get("password") or ""
		code = (data.get("code") or "").strip()
		if not email:
			return self._html_response(self._templates.render("login.html", message="Email required.", require_code=False, email=email, base_path=base_path), status=400)

		users_table = self._clients.dynamodb_table(self._config.DDB_USERS_TABLE)
		user = users_table.get_item(Key={"user_id": email}).get("Item")
		if not user:
			salt_b64, hash_b64 = self._auth.hash_password(password)
			verify_code = self._auth.generate_code()
			users_table.put_item(
				Item={
					"user_id": email,
					"item_type": "user",
					"email": email,
					"password_salt": salt_b64,
					"password_hash": hash_b64,
					"verified": False,
					"verify_code": verify_code,
					"created_at": now_iso(),
				}
			)
			if self._config.REQUIRE_EMAIL_VERIFICATION:
				try:
					self._auth.send_verification_email(email, verify_code)
					return self._html_response(self._templates.render("login.html", message="Verification code sent. Enter it to complete login.", require_code=True, email=email, base_path=base_path))
				except Exception as e:
					return self._html_response(self._templates.render("login.html", message=f"Email verification failed: {e}. Set REQUIRE_EMAIL_VERIFICATION=false or verify SES identity.", require_code=False, email=email, base_path=base_path), status=500)
			user = users_table.get_item(Key={"user_id": email}).get("Item")

		if self._config.REQUIRE_EMAIL_VERIFICATION and not user.get("verified", False):
			if not code:
				if password and not self._auth.verify_password(password, user.get("password_salt"), user.get("password_hash")):
					return self._html_response(self._templates.render("login.html", message="Invalid credentials.", require_code=False, email=email, base_path=base_path), status=401)
				return self._html_response(self._templates.render("login.html", message="Email not verified. Enter the code sent to your email.", require_code=True, email=email, base_path=base_path))
			if code != user.get("verify_code"):
				return self._html_response(self._templates.render("login.html", message="Invalid verification code.", require_code=True, email=email, base_path=base_path), status=400)
			users_table.update_item(
				Key={"user_id": email},
				UpdateExpression="SET verified = :v",
				ExpressionAttributeValues={":v": True},
			)

		if password and not self._auth.verify_password(password, user.get("password_salt"), user.get("password_hash")):
			return self._html_response(self._templates.render("login.html", message="Invalid credentials.", require_code=False, email=email, base_path=base_path), status=401)

		sid = self._auth.create_session(user_id_ref=email)
		set_cookie = self._auth.make_set_cookie(self._config.SESSION_COOKIE_NAME, sid, self._config.SESSION_DAYS)
		return self._redirect(self._with_base_path("/", base_path), set_cookie=set_cookie)

	def logout(self, request):
		set_cookie = f"{self._config.SESSION_COOKIE_NAME}=; Max-Age=0; Path=/; SameSite=Lax"
		return self._redirect(self._with_base_path("/", self._base_path(request)), set_cookie=set_cookie)

	def upload(self, request):
		if request.method == "GET":
			task_id = request.query_params.get("task_id") if request.query_params else None
			if not task_id:
				return self._json_response({"error": "task_id is required"}, status=400)

			user_id, set_cookie = self._auth.ensure_session(request.headers)
			item = self._tasks.get_task(task_id)
			if not item or item.get("user_id") != user_id:
				return self._json_response({"error": "Not found"}, set_cookie=set_cookie, status=404)

			payload = {
				"task_id": task_id,
				"status": item.get("status"),
				"photo_url": item.get("transformed_url"),
				"comments": item.get("explanation"),
				"original_url": item.get("original_url"),
				"caption": item.get("caption"),
				"description": item.get("description"),
				"share_url": item.get("share_url"),
				"error": item.get("error"),
			}
			return self._json_response(payload, set_cookie=set_cookie)

		user_id, set_cookie = self._auth.ensure_session(request.headers)
		content_type = request.headers.get("content-type", "")
		raw_body = request.raw_body or b""
		fields, files = RequestParser.parse_multipart(raw_body, content_type)
		image = files.get("image")
		if not image:
			return self._json_response({"error": "Image is required"}, set_cookie=set_cookie, status=400)

		objective = (fields.get("objective") or "sales").strip().lower()
		if objective not in ("sales", "engagement"):
			objective = "sales"
		comments = (fields.get("comments") or "").strip()
		category = fields.get("category") or "Others"
		if category not in self._config.CATEGORY_OPTIONS:
			category = "Others"
		contact_type = (fields.get("contact_type") or "product_url").strip()
		if contact_type not in ("product_url", "mobile_no"):
			contact_type = "product_url"
		contact_value = (fields.get("contact_value") or "").strip()

		image_bytes = image.get("content")
		file_content_type = image.get("content_type") or "image/png"

		if not self._config.S3_BUCKET or not self._config.SQS_QUEUE_URL:
			return self._json_response({"error": "S3_BUCKET and SQS_QUEUE_URL must be set"}, status=500)

		original_key = f"original/{uuid.uuid4().hex}.png"
		s3 = self._clients.boto3_client("s3")
		s3.put_object(Bucket=self._config.S3_BUCKET, Key=original_key, Body=image_bytes, ContentType=file_content_type)
		original_url = f"https://{self._config.S3_BUCKET}.s3.{self._config.AWS_REGION}.amazonaws.com/{original_key}"

		task_id = str(uuid.uuid4())
		self._tasks.create_task(task_id, user_id, objective, comments, category, original_url, original_key, file_content_type, contact_type, contact_value)

		payload = {"task_id": task_id}
		sqs = self._clients.boto3_client("sqs")
		sqs.send_message(QueueUrl=self._config.SQS_QUEUE_URL, MessageBody=json.dumps(payload))

		return self._json_response({"task_id": task_id, "status": "queued"}, set_cookie=set_cookie)

	def update_task(self, request):
		user_id, set_cookie = self._auth.ensure_session(request.headers)
		content_type = request.headers.get("content-type", "")
		raw_body = request.raw_body or b""
		if "application/x-www-form-urlencoded" in content_type:
			data = RequestParser.parse_urlencoded(raw_body)
		else:
			data = request.json_body or {}

		task_id = (data.get("task_id") or "").strip()
		caption = (data.get("caption") or "").strip()
		description = (data.get("description") or "").strip()
		retry = bool(data.get("retry"))
		if not task_id:
			return self._json_response({"error": "task_id is required"}, set_cookie=set_cookie, status=400)

		item = self._tasks.get_task(task_id)
		if not item or item.get("user_id") != user_id:
			return self._json_response({"error": "Not found"}, set_cookie=set_cookie, status=404)

		if retry:
			payload = {"task_id": task_id}
			self._tasks.update_task(task_id, {"status": "queued", "error": ""})
			sqs = self._clients.boto3_client("sqs")
			sqs.send_message(QueueUrl=self._config.SQS_QUEUE_URL, MessageBody=json.dumps(payload))
			return self._json_response({"task_id": task_id, "status": "queued"}, set_cookie=set_cookie)

		transformed_url = item.get("transformed_url") or ""
		thumbnail_url = item.get("thumbnail_url") or ""
		contact_type = item.get("contact_type")
		contact_value = item.get("contact_value")
		share_url = item.get("share_url") or ""
		if not share_url:
			share_key = f"share/{task_id}.html"
			share_url = f"https://{self._config.S3_BUCKET}.s3.{self._config.AWS_REGION}.amazonaws.com/{share_key}"
		else:
			share_key = share_url.split(".amazonaws.com/", 1)[-1]

		share_html = render_share_page(
			caption,
			description,
			transformed_url,
			thumbnail_url,
			contact_type,
			contact_value,
			share_url,
		)
		s3 = self._clients.boto3_client("s3")
		s3.put_object(
			Bucket=self._config.S3_BUCKET,
			Key=share_key,
			Body=share_html.encode("utf-8"),
			ContentType="text/html",
		)

		self._tasks.update_task(
			task_id,
			{
				"caption": caption,
				"description": description,
				"share_url": share_url,
			},
		)

		return self._json_response(
			{"task_id": task_id, "caption": caption, "description": description, "share_url": share_url},
			set_cookie=set_cookie,
		)

	def history(self, request, pageno):
		user_id, set_cookie = self._auth.ensure_session(request.headers)
		try:
			page = max(1, int(pageno))
		except ValueError:
			page = 1

		last_evaluated_key = None
		for _ in range(page - 1):
			result = self._tasks.query_tasks_by_user(user_id, last_evaluated_key)
			last_evaluated_key = result.get("LastEvaluatedKey")
			if not last_evaluated_key:
				break

		result = self._tasks.query_tasks_by_user(user_id, last_evaluated_key)
		items = result.get("Items", [])

		if "application/json" in (request.headers.get("accept") or ""):
			return self._json_response({"page": page, "items": items}, set_cookie=set_cookie)

		body = self._templates.render("history.html", items=items, page=page, base_path=self._base_path(request))
		return self._html_response(body, set_cookie=set_cookie)
