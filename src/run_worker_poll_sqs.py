import argparse
import json
import time

from chalicelib.config import Config
from chalicelib.clients import Clients
from chalicelib.tasks import TaskStore
from chalicelib.worker import SqsWorker


class _Record:
	def __init__(self, body):
		self.body = body


def _receive_messages(sqs, queue_url, max_messages, wait_seconds):
	resp = sqs.receive_message(
		QueueUrl=queue_url,
		MaxNumberOfMessages=max_messages,
		WaitTimeSeconds=wait_seconds,
	)
	return resp.get("Messages", [])


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("--max", type=int, default=1)
	parser.add_argument("--wait", type=int, default=10)
	parser.add_argument("--loop", action="store_true")
	parser.add_argument("--verbose", action="store_true")
	args = parser.parse_args()

	config = Config()
	clients = Clients(config)
	tasks = TaskStore(config, clients)
	worker = SqsWorker(config, clients, tasks)
	sqs = clients.boto3_client("sqs")

	if not config.SQS_QUEUE_URL:
		raise SystemExit("SQS_QUEUE_URL is not set")

	if args.verbose:
		print(f"Polling SQS: {config.SQS_QUEUE_URL} region={config.AWS_REGION} max={args.max} wait={args.wait}", flush=True)

	while True:
		try:
			messages = _receive_messages(sqs, config.SQS_QUEUE_URL, args.max, args.wait)
		except KeyboardInterrupt:
			print("Interrupted", flush=True)
			break
		if not messages:
			if args.loop:
				print("No messages", flush=True)
				time.sleep(1)
				continue
			print("No messages", flush=True)
			break

		for msg in messages:
			body = msg.get("Body", "")
			receipt = msg.get("ReceiptHandle")
			try:
				payload = json.loads(body)
				worker.handle([_Record(json.dumps(payload))])
				if receipt:
					sqs.delete_message(QueueUrl=config.SQS_QUEUE_URL, ReceiptHandle=receipt)
					print(f"Processed and deleted message: {payload.get('task_id')}", flush=True)
			except KeyboardInterrupt:
				print("Interrupted", flush=True)
				return
			except Exception as e:
				print(f"Failed to process message: {e}", flush=True)

		if not args.loop:
			break


if __name__ == "__main__":
	main()
