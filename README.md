# ENTSO-E Scraper

A Lambda that downloads data from the ENTSO-E Transparency Platform API on a schedule and saves it as CSV in S3.
The Lambda runs in a private subnet and reaches the internet through fck-nat. All infrastructure is Terraform.

```
Scheduler ──► Lambda (private subnet) ──► fck-nat ──► ENTSO-E API
                 │
                 ├── SSM: dataset config + API token
                 └── S3:  <dataset>/area=<area>/date=<day>/<run>.csv
```

## Datasets

Defined in [`config/datasets.yaml`](config/datasets.yaml):

| Dataset | What | Runs |
|---|---|---|
| `generation_forecast_day_ahead` | Generation forecast, Slovakia | daily 19:00, for tomorrow |
| `generation_actual_per_unit` | Actual generation per unit, Slovakia | daily 08:00, for yesterday |

**Add a dataset:** add a block to `datasets.yaml` and run `terraform apply`. No code changes.

## Deploy

```bash
export AWS_PROFILE=<profile>
export TF_VAR_entsoe_token=<token>

# once: Terraform state bucket
terraform -chdir=infra/bootstrap init
terraform -chdir=infra/bootstrap apply

# infrastructure
./scripts/build.sh
terraform -chdir=infra init -backend-config="bucket=$(terraform -chdir=infra/bootstrap output -raw state_bucket)"
terraform -chdir=infra apply
```

## Run manually

```bash
aws lambda invoke --function-name entsoe-scraper --cli-binary-format raw-in-base64-out \
  --payload '{"dataset":"generation_actual_per_unit","start":"2026-01-01","end":"2026-01-07"}' /dev/stdout
```

`start` and `end` are optional. Without them the dataset's normal window is used.

## Good to know

- **Generic parsing:** every value in the XML becomes a CSV column, so new fields in the API response just appear as new columns.
- **Times** are UTC. Days are counted in Slovak time.
- **No data** from the API is logged as a warning; no file is written.
- **Secrets:** the API token is stored in SSM (encrypted) and never in Terraform state or git.
- **Cost:** about $11/month (the NAT instance). Run `terraform -chdir=infra destroy` when not needed.

## Next steps
