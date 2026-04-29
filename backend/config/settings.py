"""
Django settings for config project.

Environment variables are loaded below with ``python-decouple``. Use ``django.conf.settings`` elsewhere;
for Bedrock clients use ``config.bedrock_client.aws_boto_client_kwargs``.

**Core:** ``SECRET_KEY``, ``DEBUG``, ``ALLOWED_HOSTS``

**Database:** ``DATABASE_NAME``, ``DATABASE_USER``, ``DATABASE_PASSWORD``, ``DATABASE_HOST``, ``DATABASE_PORT``

**AWS:** ``AWS_ACCESS_KEY_ID``, ``AWS_SECRET_ACCESS_KEY``, ``AWS_REGION_NAME``, ``BEDROCK_MODEL_ID``,
``BEDROCK_EMBEDDING_MODEL_ID``

**S3 media (optional):** ``AWS_S3_MEDIA_BUCKET_NAME``, ``AWS_S3_REGION_NAME``, ``AWS_S3_MEDIA_LOCATION``,
``AWS_S3_CUSTOM_DOMAIN``, ``AWS_S3_ENDPOINT_URL``

**Celery / Redis:** ``CELERY_BROKER_URL``, ``CELERY_RESULT_BACKEND``, ``REDIS_HOST``, ``REDIS_PORT``,
``REDIS_USERNAME``, ``REDIS_PASSWORD``

**Twilio / SendGrid:** ``TWILIO_ACCOUNT_SID``, ``TWILIO_AUTH_TOKEN``, ``TWILIO_PHONE_NUMBER``,
``TWILIO_SERVICE_SID``, ``TO_NUMBER``, ``SENDGRID_API_KEY``

**Meta:** ``META_ACCESS_TOKEN``, ``META_PHONE_NUMBER_ID``, ``META_VERIFY_TOKEN``, ``META_API_VERSION``

**LangGraph:** ``LANGGRAPH_SERVICE_URL``, ``LANGGRAPH_SERVICE_API_KEY``, ``LANGGRAPH_SERVICE_TIMEOUT``
"""
import sys
from pathlib import Path
from urllib.parse import quote

from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

# --- Core ---
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = [
    h.strip()
    for h in config(
        'ALLOWED_HOSTS',
        default='localhost,127.0.0.1,.awsapprunner.com,.elb.amazonaws.com,.amazonaws.com',
    ).split(',')
    if h.strip()
]

# --- AWS (Bedrock, S3 credential chain; omit keys on App Runner to use instance role) ---
AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID', default='').strip() or None
AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY', default='').strip() or None
AWS_REGION_NAME = config('AWS_REGION_NAME', default='us-east-2').strip() or 'us-east-2'
BEDROCK_MODEL_ID = config('BEDROCK_MODEL_ID', default='global.amazon.nova-2-lite-v1:0').strip()
BEDROCK_EMBEDDING_MODEL_ID = config(
    'BEDROCK_EMBEDDING_MODEL_ID', default='amazon.titan-embed-text-v2:0'
).strip()

# Application definition

INSTALLED_APPS = [
    # 'django.contrib.admin',
    'config.apps.BigBoyAdminConfig',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'storages',

    'rest_framework',
    'rest_framework.authtoken',
    'drf_spectacular',
    "corsheaders",
    "phonenumber_field",

    'bigboy.accounts.apps.AccountsConfig',
    'bigboy.subjects.apps.SubjectsConfig',
    'bigboy.sources.apps.SourcesConfig',
    'bigboy.chats.apps.ChatsConfig',
    'bigboy.quizzes.apps.QuizzesConfig',
    'bigboy.reviews.apps.ReviewsConfig',
]

MIDDLEWARE = [
    # Before CommonMiddleware: App Runner probes use Host 169.254.x.x (link-local).
    'config.middleware.AppRunnerLinkLocalHostMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    "corsheaders.middleware.CorsMiddleware",
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

AUTH_USER_MODEL = 'accounts.Account'


# --- Database ---
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASE_NAME = config('DATABASE_NAME', default='')
DATABASE_USER = config('DATABASE_USER', default='')
DATABASE_PASSWORD = config('DATABASE_PASSWORD', default='')
DATABASE_HOST = config('DATABASE_HOST', default='')
DATABASE_PORT = int(config('DATABASE_PORT', default=5432, cast=int))

if DATABASE_NAME != '':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': DATABASE_NAME,
            'USER': DATABASE_USER,
            'PASSWORD': DATABASE_PASSWORD,
            'HOST': DATABASE_HOST,
            'PORT': DATABASE_PORT,
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }



# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# --- Static & user media (RAG uploads) ---
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = 'static/'

# Set ``AWS_S3_MEDIA_BUCKET_NAME`` for S3 (recommended on App Runner).
AWS_S3_MEDIA_BUCKET_NAME = config('AWS_S3_MEDIA_BUCKET_NAME', default='').strip()
USE_S3_MEDIA = bool(AWS_S3_MEDIA_BUCKET_NAME)

if USE_S3_MEDIA:
    AWS_STORAGE_BUCKET_NAME = AWS_S3_MEDIA_BUCKET_NAME
    AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME', default='').strip() or AWS_REGION_NAME
    AWS_S3_FILE_OVERWRITE = False
    AWS_DEFAULT_ACL = None
    AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}
    _media_loc = config('AWS_S3_MEDIA_LOCATION', default='').strip().strip('/')
    if _media_loc:
        AWS_LOCATION = _media_loc
    _s3_endpoint = config('AWS_S3_ENDPOINT_URL', default='').strip()
    if _s3_endpoint:
        AWS_S3_ENDPOINT_URL = _s3_endpoint
    _s3_domain = config('AWS_S3_CUSTOM_DOMAIN', default='').strip()
    if _s3_domain:
        AWS_S3_CUSTOM_DOMAIN = _s3_domain
        MEDIA_URL = f'https://{_s3_domain}/'
    else:
        MEDIA_URL = (
            f'https://{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com/'
        )
    MEDIA_ROOT = BASE_DIR / 'media'
    STORAGES = {
        'default': {'BACKEND': 'storages.backends.s3boto3.S3Boto3Storage'},
        'staticfiles': {
            'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
        },
    }
else:
    MEDIA_ROOT = BASE_DIR / 'media'
    MEDIA_URL = '/media/'
    STORAGES = {
        'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
        'staticfiles': {
            'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
        },
    }

# --- Django REST / CORS ---
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    # 'EXCEPTION_HANDLER': 'config.exceptions.custom_exception_handler',
}

# CORS settings
# https://pypi.org/project/django-cors-headers/
CORS_ALLOW_ALL_ORIGINS = True

REDIS_PASSWORD = config('REDIS_PASSWORD', default='')
REDIS_PORT = config('REDIS_PORT', default='6379')
REDIS_HOST = config('REDIS_HOST', default='')
REDIS_USERNAME = config('REDIS_USERNAME', default='')


def _build_redis_url(db: int = 0) -> str:
    host = (REDIS_HOST or '').strip()
    if not host:
        return ''
    username = (REDIS_USERNAME or '').strip()
    password = (REDIS_PASSWORD or '').strip()
    if username and password:
        auth = f'{quote(username)}:{quote(password)}@'
    elif password:
        auth = f':{quote(password)}@'
    elif username:
        auth = f'{quote(username)}@'
    else:
        auth = ''
    return f'redis://{auth}{host}:{REDIS_PORT}/{db}'


# --- Celery & Redis ---
_CELERY_REDIS_URL = _build_redis_url(db=0)
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default=_CELERY_REDIS_URL or 'memory://')
CELERY_RESULT_BACKEND = config(
    'CELERY_RESULT_BACKEND',
    default=_CELERY_REDIS_URL or 'cache+memory://',
)
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'

##############################
# DRF SPECTACULAR
#################################
SPECTACULAR_SETTINGS = {
    'TITLE': 'BigBoy API Documentation',
    'DESCRIPTION': 'BigBoy API Documentation',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'CONTACT': {
        'email': 'developers@bigboy.com'
    },
    'SCHEMA_PATH_PREFIX': '/api/v1',
    # OTHER SETTINGS
}


################################################################# 
# Twilio settings 
##################################################################
            
TWILIO_ACCOUNT_SID = config('TWILIO_ACCOUNT_SID', default='')
TWILIO_AUTH_TOKEN = config('TWILIO_AUTH_TOKEN', default='')
TWILIO_PHONE_NUMBER = config('TWILIO_PHONE_NUMBER', default='')
TO_NUMBER = config('TO_NUMBER', default='')
TWILIO_SERVICE_SID = config('TWILIO_SERVICE_SID', default='')


################################################################# 
# SendGrid settings 
##################################################################

SENDGRID_API_KEY = config('SENDGRID_API_KEY', default='')


###################################################################
# Meta (WhatsApp Cloud API, etc.)
###################################################################

META_ACCESS_TOKEN = config('META_ACCESS_TOKEN', default='')
META_PHONE_NUMBER_ID = config('META_PHONE_NUMBER_ID', default='')
META_VERIFY_TOKEN = config('META_VERIFY_TOKEN', default='')
META_API_VERSION = config('META_API_VERSION', default='')

# Standalone LangGraph research service (langgraph-service/)
LANGGRAPH_SERVICE_URL = config('LANGGRAPH_SERVICE_URL', default='')
LANGGRAPH_SERVICE_API_KEY = config('LANGGRAPH_SERVICE_API_KEY', default='')
LANGGRAPH_SERVICE_TIMEOUT = config('LANGGRAPH_SERVICE_TIMEOUT', default=120, cast=int)



################ Logging #####################
_LOG_HANDLERS = ['console', 'file'] if DEBUG else ['console']
LOGGING = {
    "version": 1,  # the dictConfig format version
    "disable_existing_loggers": False,  # retain the default loggers
    "handlers": {
        "file": {
            "class": "logging.FileHandler",
            "filename": str(BASE_DIR / "general.log"),
            "formatter": "verbose",
            "level": "DEBUG",
        },
        'console': {  # This is the STDOUT handler
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
            "formatter": "verbose",
            "level": "DEBUG",
            
        },
    },
    "loggers": {
        "": {
            "level": "DEBUG",
            "handlers": _LOG_HANDLERS,
        },
    },
    "formatters": {
        "verbose": {
            "format": "{name} {levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "root": {
        'handlers': ['console'],
        'level': 'DEBUG',  
    },
}
