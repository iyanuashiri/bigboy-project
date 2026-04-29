# bigboy AWS infrastructure (CDK)

Deploys:

- **VPC** — public, private (with NAT), isolated subnets  
- **RDS PostgreSQL** — `db.t4g.micro`, encrypted, credentials in Secrets Manager  
- **ECS Fargate** — Django behind **internet-facing ALB** (:80)  
- **ECS Fargate** — LangGraph in **private** subnets, **Service Discovery** DNS `research.bigboy.internal:8765`  
- **CloudFront** — HTTPS in front of the ALB (use this URL from Amplify / the SPA as `VITE_API_BASE_URL`)  
- **Amplify** (`AWS::Amplify::App` + `main` branch) — connect your **GitHub** repo in the Amplify console; build uses repo-root **`amplify.yml`** and `AMPLIFY_MONOREPO_APP_ROOT=frontend-vue`  
- **Secrets Manager** — Django `SECRET_KEY`, shared **LangGraph** service key (`X-Research-Service-Key`), RDS master secret

## Prerequisites

- AWS CLI v2 and `aws login` / configured credentials  
- Docker Desktop (Windows) for `cdk deploy` **asset builds** (`fromAsset`)  
- Node.js ≥ 18  
- CDK must resolve account + region (set explicitly if needed):

```powershell
$env:CDK_DEFAULT_ACCOUNT = (aws sts get-caller-identity --query Account --output text)
$env:CDK_DEFAULT_REGION = "us-east-1"
```

- **CDK bootstrap** once per account/region:

```powershell
cd infra
npx cdk bootstrap aws://ACCOUNT-ID/REGION
```

## App Runner (manual deploy, **us-east-2**)

Use this path when you are **not** using CDK and want **Django + LangGraph on App Runner** with your existing **ECR** images and **Aurora/RDS**.

### What to do

1. **AWS CLI** + **`aws login`**. Set region for this stack:

   ```powershell
   $env:AWS_DEFAULT_REGION = "us-east-2"
   ```

2. Open the step-by-step doc and inventory (ECR URIs, RDS host, VPC):

   - **`scripts/app-runner/README.md`** — run scripts **`01`** through **`06`** in order (each step updates `state.json`).
   - **`scripts/app-runner/AWS_INVENTORY-us-east-2.md`** — quick reference for your account.

3. From **PowerShell**, go to the script folder (from repo root: `cd infra\scripts\app-runner`; if you are already in `infra\`: `cd .\scripts\app-runner`) and run the numbered scripts. For **step 06**, use secure strings for the DB password and Django `SECRET_KEY` — see **`scripts/app-runner/README.md`**.

   ```powershell
   cd infra\scripts\app-runner
   $env:AWS_DEFAULT_REGION = "us-east-2"
   .\01-verify-aws.ps1
   .\02-iam-roles.ps1
   .\s3-media-only.ps1        # optional: S3 + IAM; updates existing Django App Runner env if state has DjangoServiceArn
   .\03-rds-vpc-sg.ps1
   .\04-vpc-connector.ps1
   .\05-apprunner-langgraph.ps1
   .\06-apprunner-django.ps1 -DatabasePassword $db -DjangoSecretKey $sk
   ```

   If **03** already succeeded once (RDS security group rules in place), you can skip **`03`** and continue from **`02`** / **`04`** as described in **`scripts/app-runner/README.md`** (troubleshooting section).

4. **Frontend:** after Django has a URL, set Amplify **`VITE_API_BASE_URL`** to `https://<django-app-runner-host>/api/v1` and **redeploy** the Vue app.

### CDK vs App Runner

- **CDK** (sections below): full stack including VPC, ECS, ALB, CloudFront, Amplify L1 — run from **`infra/`** with `npx cdk deploy`. It does **not** currently provision an S3 media bucket; use the **App Runner** script **`03a-s3-media-bucket.ps1`**, or add a bucket + task role policy in CDK yourself if you move uploads to ECS.
- **App Runner** (this section): lighter, console/CLI-driven — scripts live under **`scripts/app-runner/`**.

## Synth & deploy

Always run commands from the **`infra/`** directory (paths use `process.cwd()/..`).

If you use **`aws login`**, CDK may still say “no credentials have been configured”. Export a session into the shell:

**PowerShell**

```powershell
cd infra
. .\scripts\set-cdk-aws-env.ps1
```

**Git Bash** (your `MINGW64` terminal)

```bash
cd infra
source ./scripts/set-cdk-aws-env.sh
```

**Docker Desktop must be running** before `cdk deploy` (CDK builds images with `fromAsset`). If you see `dockerDesktopLinuxEngine` / pipe errors, start Docker and retry.

If image builds fail with **DNS / PyPI** errors inside `uv sync`, set explicit DNS in Docker Desktop → **Settings → Docker Engine**, e.g. `"dns": ["8.8.8.8", "1.1.1.1"]`, then **Apply & restart**. Dockerfiles already retry `uv sync` and set `UV_HTTP_TIMEOUT=300`.

```powershell
cd infra
npm install
npx cdk synth
npx cdk deploy
```

For a fast template check without Docker builds:

```powershell
$env:CDK_DISABLE_DOCKER = "1"
npx cdk synth
Remove-Item Env:CDK_DISABLE_DOCKER
```

Real deploys **must not** set `CDK_DISABLE_DOCKER` so CDK can build and push images to the bootstrap asset ECR.

## After deploy

1. Copy **`CloudFrontApiUrl`** from stack outputs → use as **`VITE_API_BASE_URL`** locally or confirm it matches Amplify branch env (set automatically by CDK).  
2. **Amplify** — open the Amplify app in the console, **Connect branch** / GitHub, pick `main`, enable builds. Monorepo root is the repo root; `amplify.yml` selects `frontend-vue`.  
3. **Django / Bedrock** — Fargate tasks use an IAM policy allowing `bedrock:InvokeModel*`. Ensure the account can call Bedrock in the chosen region, or set keys via task env if your code uses explicit credentials.  
4. **Costs** — NAT gateway, RDS, Fargate, CloudFront, and Amplify traffic may incur charges. Destroy the stack when done: `npx cdk destroy`.

## Optional GitHub + CDK L2 Amplify

`aws-cdk-lib@2.170` only exposes Amplify **L1** here. For full GitHub-as-code, upgrade CDK and add `@aws-cdk/aws-amplify-alpha` or a newer `aws-cdk-lib` that includes `amplify.App`.
