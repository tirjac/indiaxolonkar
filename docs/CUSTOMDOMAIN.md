# Custom Domain Setup

This project supports API Gateway custom domains for clean URLs.

## Prerequisites
- `CUSTOM_DOMAIN` set in `.env.local`
- `ACM_CERT_ARN` set (or allow script to request/lookup)
- Deployed API (so `chalice url --stage dev` returns a URL)

## Steps

1. Deploy the API (if not already):
   ```bash
   sh scripts/17_deploy_dev.sh
   ```

2. Create the API Gateway custom domain + base path mapping:
   ```bash
   sh scripts/29_setup_custom_domain.sh
   ```
   If no certificate exists, the script requests one and prints the DNS
   validation CNAME. Add that CNAME, wait for validation, then re‑run
   the script.

3. Update DNS CNAME for your custom domain to the CloudFront target
   printed by the script:
   ```
   CNAME <CUSTOM_DOMAIN> -> <distributionDomainName>
   ```

4. Re‑deploy so the app uses the custom domain (no `/api` prefix needed):
   ```bash
   sh scripts/17_deploy_dev.sh
   ```

## Notes

- Do **not** CNAME to `*.execute-api.*`. Use the CloudFront domain
  returned by API Gateway for custom domains.
- If `scripts/16_predeploy_check.sh` says `CUSTOM_DOMAIN` is ignored,
  it means API Gateway custom domain/mapping is not detected yet.
