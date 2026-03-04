# -*- coding: utf-8 -*-
#
# @project indiaxolonkar
# @file chalicelib/auth.py
# @author  Shreos Roychowdhury <shreos@tirja.com>
# @version 1.0.0
# 
# @section DESCRIPTION
# 
#   auth.py : Auth, sessions, password hashing, SES verification.
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

import os
import uuid
import base64
import hashlib
import hmac
from datetime import datetime, timezone, timedelta
from .timeutil import now_iso


class AuthService:
	def __init__(self, config, clients):
		self._config = config
		self._clients = clients

	def hash_password(self, password, salt=None):
		if salt is None:
			salt = os.urandom(16)
		pw_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
		return base64.b64encode(salt).decode("utf-8"), base64.b64encode(pw_hash).decode("utf-8")

	def verify_password(self, password, salt_b64, hash_b64):
		salt = base64.b64decode(salt_b64)
		pw_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
		return hmac.compare_digest(base64.b64encode(pw_hash).decode("utf-8"), hash_b64)

	@staticmethod
	def generate_code():
		return str(uuid.uuid4()).split("-")[0]

	@staticmethod
	def get_cookie(headers, name):
		cookie = headers.get("cookie") or headers.get("Cookie")
		if not cookie:
			return None
		parts = cookie.split(";")
		for part in parts:
			key_value = part.strip().split("=", 1)
			if len(key_value) == 2 and key_value[0] == name:
				return key_value[1]
		return None

	@staticmethod
	def make_set_cookie(name, value, max_age_days):
		max_age = max_age_days * 24 * 60 * 60
		expires = datetime.now(timezone.utc) + timedelta(seconds=max_age)
		expires_str = expires.strftime("%a, %d %b %Y %H:%M:%S GMT")
		return f"{name}={value}; Max-Age={max_age}; Expires={expires_str}; Path=/; SameSite=Lax; HttpOnly"

	def create_session(self, user_id_ref, sid=None):
		if sid is None:
			sid = f"sess_{uuid.uuid4().hex}"
		users_table = self._clients.dynamodb_table(self._config.DDB_USERS_TABLE)
		users_table.put_item(
			Item={
				"user_id": sid,
				"item_type": "session",
				"user_id_ref": user_id_ref,
			"created_at": now_iso(),
			}
		)
		return sid

	def get_user_id_from_session(self, headers):
		sid = self.get_cookie(headers, self._config.SESSION_COOKIE_NAME)
		if not sid:
			return None, None
		users_table = self._clients.dynamodb_table(self._config.DDB_USERS_TABLE)
		item = users_table.get_item(Key={"user_id": sid}).get("Item")
		if not item or item.get("item_type") != "session":
			return None, None
		return sid, item.get("user_id_ref")

	def ensure_session(self, headers):
		sid, user_id = self.get_user_id_from_session(headers)
		if sid and user_id:
			return user_id, None
		new_sid = f"sess_{uuid.uuid4().hex}"
		anon_user_id = f"anon:{new_sid}"
		self.create_session(user_id_ref=anon_user_id, sid=new_sid)
		return anon_user_id, self.make_set_cookie(self._config.SESSION_COOKIE_NAME, new_sid, self._config.SESSION_DAYS)

	def send_verification_email(self, email, code):
		if not self._config.SES_FROM_EMAIL:
			raise ValueError("SES_FROM_EMAIL is not set")
		ses = self._clients.boto3_client("ses")
		ses.send_email(
			Source=self._config.SES_FROM_EMAIL,
			Destination={"ToAddresses": [email]},
			Message={
				"Subject": {"Data": "Your verification code"},
				"Body": {"Text": {"Data": f"Your code is: {code}"}},
			},
		)
