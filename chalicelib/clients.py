# -*- coding: utf-8 -*-
#
# @project indiaxolonkar
# @file chalicelib/clients.py
# @author  Shreos Roychowdhury <shreos@tirja.com>
# @version 1.0.0
# 
# @section DESCRIPTION
# 
#   clients.py : AWS/OpenAI client helpers.
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

import boto3
from openai import OpenAI


class Clients:
	def __init__(self, config):
		self._config = config
		self._openai_client = None

	def get_openai(self):
		if self._openai_client is None:
			self._openai_client = OpenAI(api_key=self._config.OPENAI_API_KEY)
		return self._openai_client

	def boto3_client(self, service):
		return boto3.client(service, region_name=self._config.AWS_REGION)

	def dynamodb_table(self, name):
		return boto3.resource("dynamodb", region_name=self._config.AWS_REGION).Table(name)
