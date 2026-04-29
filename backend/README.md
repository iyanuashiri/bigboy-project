# bigboy-backend

## Setup

### virtual environment 
1. Clone the repository `git clone https://github.com/iyanuashiri/bigboy-project.git`
2. Create a virtual environment `python -m venv venv`
3. Activate the virtual environment `venv\Scripts\activate` on windows or `source venv/bin/activate` on linux
4. Install the requirements `pip install -r requirements.txt`
5. Run the migrations `python manage.py migrate`
6. Run the server `python manage.py runserver`

### uv
1. Clone the repository `git clone https://github.com/iyanuashiri/bigboy-project.git`
2. uv sync
3. uv run python manage.py migrate
4. uv run python manage.py runserver

### docker
1. Clone the repository `git clone https://github.com/iyanuashiri/bigboy-project.git`
2. docker build -t bigboy-backend .
3. docker run -p 8000:8000 bigboy-backend



## Cloud services 

1. Twilio
2. SendGrid
3. Render
4. NeonDB
5. Redis.io

## Environment variables

All keys are loaded in **`config/settings.py`** (see the module docstring at the top of that file for the full list). Bedrock call sites use **`config/bedrock_client.py`** → **`aws_boto_client_kwargs()`** so credentials stay consistent with **`AWS_ACCESS_KEY_ID`** / **`AWS_SECRET_ACCESS_KEY`** (omit both on AWS to use the instance role).

Highlights:

### Optional: S3 for user uploads (media)

When **`AWS_S3_MEDIA_BUCKET_NAME`** is set, **`DEFAULT`** file storage uses **S3** (`django-storages`). Otherwise uploads stay under **`MEDIA_ROOT`** on disk (fine for local dev).

**App Runner:** from **`infra/scripts/app-runner`**, run **`.\s3-media-only.ps1`** (or **`.\03a-s3-media-bucket.ps1`**, same script) after **`02-iam-roles.ps1`**. If Django is **already** deployed, **`s3-media-only.ps1`** updates **`state.json`** and calls **`update-service`** to set **`AWS_S3_MEDIA_BUCKET_NAME`** / **`AWS_S3_REGION_NAME`** when **`DjangoServiceArn`** is in **`state.json`**. For **new** services from scratch, **`06-apprunner-django.ps1`** injects those vars if **`MediaBucketName`** is already in state. See **`infra/scripts/app-runner/README.md`**.

| Variable | Purpose |
|----------|---------|
| **`AWS_S3_MEDIA_BUCKET_NAME`** | If non-empty, enables S3 media storage. |
| **`AWS_S3_REGION_NAME`** | S3 bucket region (defaults to **`AWS_REGION_NAME`** or **`us-east-2`**). |
| **`AWS_S3_MEDIA_LOCATION`** | Optional key prefix inside the bucket (no leading/trailing slashes). |
| **`AWS_S3_CUSTOM_DOMAIN`** | Optional CloudFront or vanity hostname for **`MEDIA_URL`** (e.g. `d111111abcdef8.cloudfront.net`). |
| **`AWS_S3_ENDPOINT_URL`** | Optional custom S3-compatible endpoint (e.g. LocalStack). |
| **`AWS_ACCESS_KEY_ID`** / **`AWS_SECRET_ACCESS_KEY`** | Optional; on **App Runner** omit these and grant **`s3:GetObject`**, **`s3:PutObject`**, **`s3:DeleteObject`** on `arn:aws:s3:::YOUR_BUCKET/*` to the **instance role**. |

`AWS_DEFAULT_ACL` is unset so buckets can use **Object Ownership** / private objects; the backend reads files via **`default_storage.open`** using IAM credentials.

Other variables (Twilio, Postgres, LangGraph, Bedrock, etc.) are documented in code and the repo **`.env.example`**.


## How to run ngrok
1. Download ngrok from https://ngrok.com/download
2. Unzip the downloaded file
3. Add the ngrok to your system path
4. Open Power Shell as administrator
5. Run ngrok `ngrok http --url=slightly-crisp-pheasant.ngrok-free.app 8000` or 
6. Forwarding https://slightly-crisp-pheasant.ngrok-free.app -> http://localhost:8000 (make sure the port is consistency. )
6. Copy the https url from ngrok
7. Add the https url to the webhook in twilio

## How to run celery
1. uv run celery -A config.celery worker --loglevel=info --pool=solo
2. Document upload indexing now runs asynchronously through Celery. Keep this worker running (plus Redis) for Explore → document uploads/RAG indexing.


## How to check the docs

http://127.0.0.1:8000/api/schema/swagger-ui/