import json
import os
import boto3


def _load_env_file(path):
	if not os.path.exists(path):
		return
	with open(path, "r", encoding="utf-8") as f:
		for line in f:
			line = line.strip()
			if not line or line.startswith("#") or "=" not in line:
				continue
			key, value = line.split("=", 1)
			if key not in os.environ:
				os.environ[key] = value


class Config:
	def __init__(self):
		_load_env_file(".env.local")
		self._load_ssm_params()
		self.APP_NAME = "indiaxolonkar"
		self.AWS_REGION = self._clean(os.getenv("AWS_REGION", "us-east-1"))
		self.S3_BUCKET = self._clean(os.getenv("S3_BUCKET", ""))
		self.SQS_QUEUE_URL = self._clean(os.getenv("SQS_QUEUE_URL", ""))
		self.SQS_QUEUE_NAME = self._clean(os.getenv("SQS_QUEUE_NAME", "image-jobs"))
		self.DDB_USERS_TABLE = self._clean(os.getenv("DDB_USERS_TABLE", "users"))
		self.DDB_TASKS_TABLE = self._clean(os.getenv("DDB_TASKS_TABLE", "tasks"))
		self.TASKS_BY_USER_INDEX = self._clean(os.getenv("TASKS_BY_USER_INDEX", "user_id-created_at-index"))
		self.SES_FROM_EMAIL = self._clean(os.getenv("SES_FROM_EMAIL", ""))
		self.OPENAI_API_KEY = self._clean(os.getenv("OPENAI_API_KEY", ""))
		self.REQUIRE_EMAIL_VERIFICATION = self._clean(os.getenv("REQUIRE_EMAIL_VERIFICATION", "true")).lower() == "true"
		self.DEBUG_MODE = self._clean(os.getenv("DEBUG_MODE", "false")).lower() == "true"
		self.CUSTOM_DOMAIN = self._clean(os.getenv("CUSTOM_DOMAIN", ""))

		self.CATEGORY_OPTIONS = [
			"Electronics",
			"Fashion",
			"Home & Kitchen",
			"Beauty & Personal Care",
			"Grocery",
			"Health & Wellness",
			"Sports & Outdoors",
			"Toys & Games",
			"Books & Stationery",
			"Automotive",
			"Others",
		]

		self.PAGE_SIZE = 5
		self.SESSION_COOKIE_NAME = "sid"
		self.SESSION_DAYS = 30

	def _load_ssm_params(self):
		param_name = os.getenv("SSM_PARAM_NAME", "").strip()
		if not param_name:
			raise ValueError("SSM_PARAM_NAME is required")
		region = os.getenv("AWS_REGION", "us-east-1").strip()
		client = boto3.client("ssm", region_name=region)
		try:
			resp = client.get_parameter(Name=param_name, WithDecryption=True)
		except Exception:
			return
		value = resp.get("Parameter", {}).get("Value") or "{}"
		try:
			data = json.loads(value)
		except json.JSONDecodeError:
			return
		if not isinstance(data, dict):
			return
		for key, val in data.items():
			if key not in os.environ or os.environ.get(key, "") == "":
				os.environ[key] = str(val)

	@staticmethod
	def _clean(value):
		if value is None:
			return ""
		value = value.strip()
		if len(value) >= 2 and ((value[0] == value[-1]) and value[0] in ("\"", "'")):
			return value[1:-1]
		return value
