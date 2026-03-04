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
