from .timeutil import now_iso
from boto3.dynamodb.conditions import Key


class TaskStore:
	def __init__(self, config, clients):
		self._config = config
		self._clients = clients

	def create_task(self, task_id, user_id, objective, comments, category, original_url, original_key, content_type, contact_type=None, contact_value=None):
		tasks_table = self._clients.dynamodb_table(self._config.DDB_TASKS_TABLE)
		tasks_table.put_item(
			Item={
				"task_id": task_id,
				"user_id": user_id,
				"created_at": now_iso(),
				"status": "queued",
				"objective": objective,
				"comments": comments,
				"category": category,
				"original_url": original_url,
				"original_key": original_key,
				"content_type": content_type,
				"contact_type": contact_type,
				"contact_value": contact_value,
			}
		)

	def update_task(self, task_id, updates):
		if not task_id:
			return
		tasks_table = self._clients.dynamodb_table(self._config.DDB_TASKS_TABLE)
		expr = []
		values = {}
		names = {}
		for key, value in updates.items():
			name_key = f"#{key}"
			names[name_key] = key
			expr.append(f"{name_key} = :{key}")
			values[f":{key}"] = value
		tasks_table.update_item(
			Key={"task_id": task_id},
			UpdateExpression="SET " + ", ".join(expr),
			ExpressionAttributeNames=names,
			ExpressionAttributeValues=values,
		)

	def get_task(self, task_id):
		tasks_table = self._clients.dynamodb_table(self._config.DDB_TASKS_TABLE)
		return tasks_table.get_item(Key={"task_id": task_id}).get("Item")

	def query_tasks_by_user(self, user_id, last_evaluated_key=None):
		tasks_table = self._clients.dynamodb_table(self._config.DDB_TASKS_TABLE)
		kwargs = {
			"IndexName": self._config.TASKS_BY_USER_INDEX,
			"KeyConditionExpression": Key("user_id").eq(user_id),
			"Limit": self._config.PAGE_SIZE,
			"ScanIndexForward": False,
		}
		if last_evaluated_key:
			kwargs["ExclusiveStartKey"] = last_evaluated_key
		return tasks_table.query(**kwargs)
