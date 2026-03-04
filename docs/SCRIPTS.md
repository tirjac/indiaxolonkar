# Scripts

## Core
- `scripts/00_script_config.sh`: loads venv + .env.local and exports vars.
- `scripts/01_setup_python.sh`: create venv and install requirements; also creates `.chalice/config.json` if missing.
- `scripts/02_run_python.sh`: run python inside venv.
- `scripts/03_run_any.sh`: run any command with env/venv loaded.

## Local Test
- `scripts/11_start_app_local.sh`: run Chalice locally.
- `scripts/12_run_worker_local.sh`: poll SQS and process jobs locally.
- `scripts/14_send_job_local.sh`: enqueue a job (uploads image to S3 + sends SQS message).

## Deploy
- `scripts/17_deploy_dev.sh`: sync SSM param name, predeploy checks, and deploy to dev.
- `scripts/18_recreate_all.sh`: recreate core resources and deploy.
- `scripts/16_predeploy_check.sh`: predeploy checks.

## Resources Management
- `scripts/21_generate_env_local.sh`: generate `.env.local`.
- `scripts/22_set_required_env.sh`: set SES_FROM_EMAIL and OPENAI_API_KEY (env or prompt).
- `scripts/23_create_db.sh`: create DynamoDB tables.
- `scripts/24_create_s3_bucket.sh`: create S3 bucket and set public read policy.
- `scripts/25_create_sqs.sh`: create SQS queue and print URL.
- `scripts/26_push_env_to_ssm.sh`: push `.env.local` to SSM parameter.
- `scripts/27_update_sqs_visibility.sh`: update SQS visibility timeout.
- `scripts/28_attach_policy.sh`: attach app IAM policy (SSM, DDB, S3, SQS, SES) to the Lambda IAM role.
- `scripts/29_setup_custom_domain.sh`: create API Gateway custom domain + base path mapping and print CNAME target.
- `scripts/31_verify_only_ses_from_mail.sh`: check SES_FROM_EMAIL verification status.
- `scripts/31_verify_send_ses_from_mail.sh`: request SES verification email if needed.

## Debug Tools
- `scripts/51_debug_get_dynamo_entry.sh <task_id>`: fetch a task record.
- `scripts/52_get_task_entry.sh [max] [wait]`: receive SQS messages.
- `scripts/53_flush_tasks_table.sh`: delete all task records.
- `scripts/54_get_cloudwatch_log.sh`: fetch latest CloudWatch logs for a Lambda.
- `scripts/55_disable_sqs_trigger.sh`: disable the SQS Lambda event source mapping.
- `scripts/56_enable_sqs_trigger.sh`: enable the SQS Lambda event source mapping.

## Cleanup, USE WITH CAUTION
- `scripts/91_delete_app.sh <app_name> [stage]`: delete a specific Chalice app by name.
- `scripts/99_delete_all.sh`: delete all AWS resources for this project.
