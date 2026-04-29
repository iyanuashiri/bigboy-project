# App Runner deploy (Bigboy) — **us-east-2**

Incremental PowerShell scripts. Each step **merges** `state.json` in this folder so you can stop and resume.

## S3 media only (Django already deployed)

If **Django and LangGraph are already running** and you only need **S3 + IAM + App Runner env** for uploads:

```powershell
cd infra\scripts\app-runner
$env:AWS_DEFAULT_REGION = "us-east-2"
.\s3-media-only.ps1
```

That creates **`bigboy-media-<AccountId>`** (or use **`-BucketName your-name`**), locks public access, attaches **`BigboyMediaS3`** to **`BigboyAppRunnerInstance`**, updates **`state.json`**, and — if **`DjangoServiceArn`** is in **`state.json`** — calls **`apprunner update-service`** to add **`AWS_S3_MEDIA_BUCKET_NAME`** and **`AWS_S3_REGION_NAME`**, then starts a new deployment.

- **`DjangoServiceArn` missing?** Paste the service ARN from the AWS console into **`state.json`** (or re-run **`06`** once with an empty conflict — easier: add `"DjangoServiceArn": "arn:aws:apprunner:..."` by hand), then run **`.\s3-media-only.ps1`** again. Or set the two env vars in the App Runner console and deploy.
- **Bucket/IAM only, no App Runner API call:** **`.\s3-media-only.ps1 -NoAppRunnerUpdate`**

## Prerequisites

- **AWS CLI v2**, **`aws login`** (or valid default credentials).
- **Region:** `us-east-2` (set `AWS_DEFAULT_REGION=us-east-2` or the scripts default to it in `_Common.ps1`).
- **ECR images** pushed:
  - `726101440593.dkr.ecr.us-east-2.amazonaws.com/bigboy-backend-repo:latest`
  - `726101440593.dkr.ecr.us-east-2.amazonaws.com/langgraph-service-repo:latest`
- Rebuild and push **Django** after the `ALLOWED_HOSTS` change in `backend/config/settings.py` if you have not already.

## Order (run one at a time)

From PowerShell:

```powershell
cd infra\scripts\app-runner
$env:AWS_DEFAULT_REGION = "us-east-2"

.\01-verify-aws.ps1
.\02-iam-roles.ps1
.\03a-s3-media-bucket.ps1    # optional: same as s3-media-only.ps1 (numbered flow)
.\03-rds-vpc-sg.ps1          # optional: -DbInstanceId bigboy-backend-db-instance-1
.\04-vpc-connector.ps1
.\05-apprunner-langgraph.ps1
.\06-apprunner-django.ps1    # needs DB password + Django SECRET_KEY — see below
# If the service already exists with an old health path, rebuild/push the Django image, then:
# .\07-update-django-healthcheck.ps1
```

### Step 6 — Where the secrets come from, and where they go

**`DatabasePassword`**

- **From:** The **master password** you chose when you created the **Aurora / RDS** instance (user is usually **`postgres`** for your cluster). If you forgot it, reset it in **RDS console** (modify instance / cluster) or retrieve it from **Secrets Manager** if RDS was set up to store credentials there.
- **Not** from Git or `README.md` — AWS never shows the old password in plain text in the console after creation.
- **To:** Passed only into this PowerShell command. The script puts it in **App Runner → your Django service → Configuration → Environment variables** as **`DATABASE_PASSWORD`** so the container can connect to Postgres. It does **not** write it into a repo file.

**`DjangoSecretKey`**

- **From:** Generate a new long random value for a real deploy (e.g. `python -c "import secrets; print(secrets.token_urlsafe(50))"` or any password manager). For a quick demo you might reuse the **`SECRET_KEY`** from your local **`.env`** if you already have one — **do not commit** that file.
- **To:** Same as above — ends up as **`SECRET_KEY`** on the **App Runner Django** service so Django can sign sessions/cookies.

**How you type them in (example)**

`Read-Host -AsSecureString` only hides input on screen; it fills variables you pass into step **06**:

```powershell
$db = Read-Host "RDS / Aurora master password (postgres user)" -AsSecureString
$sk = Read-Host "Django SECRET_KEY (long random string)" -AsSecureString
.\06-apprunner-django.ps1 -DatabasePassword $db -DjangoSecretKey $sk
```

Do **not** run `.\06-apprunner-django.ps1` with no arguments: `-DatabasePassword` and `-DjangoSecretKey` are required (use the pattern above).

**PowerShell 7:** you must use **`Read-Host ... -AsSecureString`** for `$db` and `$sk` (plain `Read-Host` produces strings and step 06 will error). If **`aws`** used to throw **`NativeCommandError`** on the `_Common.ps1` line, pull the latest **`_Common.ps1`** (`Invoke-Aws` fix) and rerun step **06**.

**`aws failed (exit 254)` with no detail:** older scripts dropped **`aws`** stderr. Current **`Invoke-Aws`** prints it after the command line. **`--cli-input-json`** also failed when the temp path lived under a Windows username **with spaces**; temp files are now under **`%WINDIR%\Temp`**. On Windows, AWS CLI v2 rejects **`file:///C:/...`** (**.NET `AbsoluteUri`**); the script uses **`file://C:/...`** with encoded segments instead.

Optional: `-DatabaseName bigboy` if you created that database (default is `postgres`).

## After deploy

1. Note **Django** URL from the script output or `state.json` → `DjangoServiceUrl`.
2. **Amplify:** set `VITE_API_BASE_URL` to `https://<django-host>/api/v1` and **redeploy** the frontend.
3. **LangGraph** URL is in `state.json` → `LanggraphServiceUrl`; shared key → `ResearchServiceApiKey` (do not commit `state.json`).
4. **User uploads (RAG PDFs):** greenfield flow uses **`.\03a-s3-media-bucket.ps1`** (after **02**) so **06** picks up **`MediaBucketName`**. If Django **already exists**, use **`.\s3-media-only.ps1`** instead (see section at top of this README). Details: **`backend/README.md`**.

## Inventory

See **`AWS_INVENTORY-us-east-2.md`** for RDS host, VPC, subnets, and ECR URIs.

## Troubleshooting

- **`Invalid JSON received` on step 05/06 (`--cli-input-json`):** fixed — App Runner input files are written **UTF-8 without BOM** (same BOM issue as IAM). Re-run **`.\05-apprunner-langgraph.ps1`**; the script will **repair** `state.json` if a previous run left empty LangGraph URL/ARN.
- **`MalformedPolicyDocument` on step 02 `create-role`:** fixed — trust/policy JSON files are now written **UTF-8 without BOM** (PowerShell `Set-Content -Encoding UTF8` adds a BOM that IAM rejects). Re-run `.\02-iam-roles.ps1`.
- **Step 05 says “Run 02 first”** after you already ran 04: step **02** did not finish, so `state.json` has no `EcrAccessRoleArn`. Run **`.\02-iam-roles.ps1`** again (03/04 can stay as-is), then **`.\05-apprunner-langgraph.ps1`**.
- **Step 02 failed on `get-role` (PowerShell 7):** fixed in repo — `aws` stderr no longer aborts the script. Re-run `.\02-iam-roles.ps1`.
- **Step 04 `Failed to get subnets details`:** fixed — CLI now sends `--subnets` once per id. Re-run `.\04-vpc-connector.ps1` (skip `03` if RDS rules already exist).
- **CREATE_FAILED** on App Runner: open **CloudWatch Logs** for the service; common issues are wrong **port**, **health check path**, or **DB connection** (SG / VPC connector / wrong password).
- **Health check failed on `/api/schema/`:** that route builds the full OpenAPI schema and can time out or error while the app warms up. The backend exposes **`GET /healthz`** (plain **`ok`**, no DB). New **06** deploys use that path. For an **existing** service: rebuild and push **`bigboy-backend-repo:latest`**, then run **`.\07-update-django-healthcheck.ps1`**. LangGraph keeps **`/health`**.
- **`DisallowedHost` / `169.254.172.2:8000`:** App Runner health checks use a **link-local** `Host` header. The backend **`AppRunnerLinkLocalHostMiddleware`** rewrites that to **`localhost`** for the request (rebuild and push the image after pulling this change).
- If you **deleted** an App Runner service and re-run step 5/6, delete or edit **`state.json`** so ARNs match reality.
