# Architecture

## Overview
The service accepts an image + objective + category, enqueues a job to SQS, and returns a task id. A worker processes the job, calls OpenAI image generation, stores results on S3, and updates DynamoDB.

## Components
- `app.py`: Chalice routes and SQS handler wiring only.
- `chalicelib/`: Modular application code.
  - `config.py`: Environment config loader.
  - `clients.py`: AWS/OpenAI client factories.
  - `templates.py`: Jinja2 rendering.
  - `auth.py`: Sessions and email verification.
  - `tasks.py`: DynamoDB task persistence.
  - `handlers.py`: HTTP route handlers.
  - `worker.py`: SQS job processor.
- `chalicelib/templates/`: Jinja2 templates.
- `src/`: Local-only utilities (not deployed by Chalice).

## Data Flow
1. `POST /upload` saves the original image to S3, writes a task to DynamoDB, and sends a message to SQS.
2. Worker receives the SQS message, loads the image, calls OpenAI, stores the transformed image to S3, and updates DynamoDB.
3. Client polls `GET /upload?task_id=...` for completion.

## Storage
- S3: original and transformed images (public read).
- DynamoDB:
  - Users table: user and session records.
  - Tasks table: task status and metadata.

## Auth
- Browser sessions via DynamoDB-backed session records.
- Optional email verification via SES (controlled by `REQUIRE_EMAIL_VERIFICATION`).
