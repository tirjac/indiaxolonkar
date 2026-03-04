# Documentation

## Quick Start


1. Create local venv for testing
   ```bash
   bash scripts/01_setup_python.sh
   ```

2. Create `.env.local`:
   ```bash
   bash scripts/21_generate_env_local.sh
   ```

3. Create aws resources (no deploy):
   ```bash
   bash scripts/19_recreate_all.sh
   ```

4. Local testing ( localhost:8000) :
   ```bash
   sh scripts/11_start_app_local.sh
   sh scripts/12_run_worker_local.sh
   ```

5. Deploy after local validation:
   ```bash
   sh scripts/17_deploy_dev.sh
   ```

## Required Environment Variables

- `SES_FROM_EMAIL`: Verified sender email address (SES email identity) used to send login/verification emails.
- `OPENAI_API_KEY`: API key used to call the OpenAI API for image + text generation.

## Other Docs

- [Architecture](./ARCHITECTURE.md)
- [Scripts](./SCRIPTS.md)
- [Setup](./SETUP.md)
- [Custom Domain](./CUSTOMDOMAIN.md)
