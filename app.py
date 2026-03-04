from chalice import Chalice
from chalicelib.config import Config
from chalicelib.clients import Clients
from chalicelib.templates import TemplateRenderer
from chalicelib.auth import AuthService
from chalicelib.tasks import TaskStore
from chalicelib.handlers import Handlers
from chalicelib.worker import SqsWorker

config = Config()
clients = Clients(config)
templates = TemplateRenderer()
auth = AuthService(config, clients)
tasks = TaskStore(config, clients)
handlers = Handlers(config, clients, templates, auth, tasks)
worker = SqsWorker(config, clients, tasks)

app = Chalice(app_name=config.APP_NAME)
app.api.binary_types.append("multipart/form-data")
app.api.binary_types.append("application/octet-stream")


@app.route("/")
def home():
	return handlers.home(app.current_request)


@app.route("/terms")
def terms():
	return handlers.terms(app.current_request)


@app.route("/privacy")
def privacy():
	return handlers.privacy(app.current_request)


@app.route(
	"/login",
	methods=["GET", "POST"],
	content_types=["*/*"],
)
def login():
	return handlers.login(app.current_request)


@app.route("/logout")
def logout():
	return handlers.logout(app.current_request)


@app.route(
	"/upload",
	methods=["GET", "POST"],
	content_types=["*/*"],
)
def upload():
	return handlers.upload(app.current_request)


@app.route(
	"/update_task",
	methods=["POST"],
	content_types=["*/*"],
)
def update_task():
	return handlers.update_task(app.current_request)




@app.route("/history/{pageno}")
def history(pageno):
	return handlers.history(app.current_request, pageno)


@app.on_sqs_message(queue=config.SQS_QUEUE_NAME)
def handle_sqs(event):
	return worker.handle(event)
