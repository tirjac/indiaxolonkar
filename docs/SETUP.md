# Setup

## Prerequisites
- Python 3.12
- AWS CLI configured
- AWS resources: S3, SQS, DynamoDB, SES (optional)

## Environment

## Scripts

Scripts are grouped by number band and listed one-line each.

### Basic
- `scripts/00_script_config.sh`: load venv + env vars (used by all scripts).
- `scripts/01_setup_python.sh`: create venv and install requirements.
- `scripts/02_run_python.sh`: run python inside venv.
- `scripts/03_run_any.sh`: run any command with env/venv loaded.

### Local Testing 
- `scripts/11_start_app_local.sh`: run Chalice locally.
- `scripts/12_run_worker_local.sh`: poll SQS and process jobs locally.
- `scripts/14_send_job_local.sh`: enqueue a job (upload + SQS).

### Deploy 
- `scripts/16_predeploy_check.sh`: verify env/resources/SSM + compile.
- `scripts/17_deploy_dev.sh`: deploy to dev (includes policy attach when needed).
- `scripts/19_recreate_all.sh`: create resources and optionally deploy.

### AWS Setup 
- `scripts/21_generate_env_local.sh`: generate `.env.local`.
- `scripts/22_set_required_env.sh`: set SES_FROM_EMAIL + OPENAI_API_KEY (env or prompt).
- `scripts/23_create_db.sh`: create DynamoDB tables.
- `scripts/24_create_s3_bucket.sh`: create S3 bucket + public read policy.
- `scripts/25_create_sqs.sh`: create SQS queue + write URL.
- `scripts/26_push_env_to_ssm.sh`: push env to SSM parameter.
- `scripts/27_update_sqs_visibility.sh`: update SQS visibility timeout.
- `scripts/28_attach_policy.sh`: attach IAM policy to Lambda role.
- `scripts/29_setup_custom_domain.sh`: create custom domain + base path mapping.
- `scripts/31_verify_only_ses_from_mail.sh`: check SES_FROM_EMAIL verification status.
- `scripts/31_verify_send_ses_from_mail.sh`: request SES verification email if needed.

### Debug
- `scripts/51_debug_get_dynamo_entry.sh`: fetch a task record.
- `scripts/52_get_task_entry.sh`: receive SQS messages.
- `scripts/53_flush_tasks_table.sh`: delete all task records.
- `scripts/54_get_cloudwatch_log.sh`: fetch latest CloudWatch logs.
- `scripts/55_disable_sqs_trigger.sh`: disable the SQS Lambda event source mapping.
- `scripts/56_enable_sqs_trigger.sh`: enable the SQS Lambda event source mapping.

### Cleanup
- `scripts/91_delete_app.sh`: delete a specific Chalice app (API/Lambdas/IAM only).
- `scripts/99_delete_all.sh`: delete all AWS resources for this project.
