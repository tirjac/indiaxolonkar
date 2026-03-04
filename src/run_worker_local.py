# -*- coding: utf-8 -*-
#
# @project indiaxolonkar
# @file src/run_worker_local.py
# @author  Shreos Roychowdhury <shreos@tirja.com>
# @version 1.0.0
# 
# @section DESCRIPTION
# 
#   run_worker_local.py : Local worker runner.
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

import argparse
import json
import uuid

from chalicelib.config import Config
from chalicelib.clients import Clients
from chalicelib.tasks import TaskStore
from chalicelib.worker import SqsWorker


class _Record:
	def __init__(self, body):
		self.body = body


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("image_path")
	parser.add_argument("--objective", default="sales")
	parser.add_argument("--category", default="Others")
	parser.add_argument("--comments", default="")
	parser.add_argument("--user-id", default="local")
	args = parser.parse_args()

	config = Config()
	clients = Clients(config)
	tasks = TaskStore(config, clients)
	worker = SqsWorker(config, clients, tasks)

	with open(args.image_path, "rb") as f:
		image_bytes = f.read()

	content_type = "image/png"
	original_key = f"original/{uuid.uuid4().hex}.png"

	s3 = clients.boto3_client("s3")
	s3.put_object(Bucket=config.S3_BUCKET, Key=original_key, Body=image_bytes, ContentType=content_type)
	original_url = f"https://{config.S3_BUCKET}.s3.{config.AWS_REGION}.amazonaws.com/{original_key}"

	task_id = str(uuid.uuid4())
	tasks.create_task(task_id, args.user_id, args.objective, args.comments, args.category, original_url, original_key, content_type, None, None)

	payload = {"task_id": task_id}

	worker.handle([_Record(json.dumps(payload))])
	result = tasks.get_task(task_id)
	print(json.dumps(result, indent=2))


if __name__ == "__main__":
	main()
