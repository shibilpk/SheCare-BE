from datetime import timedelta
from pathlib import Path
from decouple import config, Csv
BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())


INSTALLED_APPS = [
    'ninja_extra',
    'ninja_jwt',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'accounts',
    'general',
    'customers',
    'periods',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'ninja.compatibility.files.fix_request_files_middleware',
    'core.middlewares.RequestMiddleware',

]

ROOT_URLCONF = 'shecare.urls'

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

WSGI_APPLICATION = 'shecare.wsgi.application'

if config('DB_ENGINE', default='postgresql') == 'postgresql':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME'),
            'USER': config('DB_USER'),
            'PASSWORD': config('DB_PASSWORD'),
            'HOST': config('DB_HOST'),
            'PORT': config('DB_PORT'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': ('django.contrib.auth.password_validation.UserAttributeSimilarityValidator'),
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


LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


STATIC_URL = 'static/'
AUTH_USER_MODEL = 'accounts.CustomUser'

NINJA_EXTRA = {
    'PAGINATION_CLASS': "ninja_extra.pagination.PageNumberPaginationExtra",
    'PAGINATION_PER_PAGE': 2,
    'ORDERING_CLASS': "ninja_extra.ordering.Ordering",
    'SEARCHING_CLASS': "ninja_extra.searching.Searching",
}


# JWT Settings for django-ninja-jwt
NINJA_JWT = {
    # Access token expires in 60 minutes
    'ACCESS_TOKEN_LIFETIME': timedelta(seconds=60),
    # Refresh token expires in 7 days
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True
}

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
FERNET_KEY = config('FERNET_KEY')
OTP_CONFIG = {
    'OTP_EXPIRY_MINUTES': config('OTP_EXPIRY_MINUTES', default=10, cast=int),
    'RESEND_OTP_INTERVAL_SECONDS': config(
        'RESEND_OTP_INTERVAL_SECONDS', default=60, cast=int),
    'MAX_OTP_ATTEMPTS': config('MAX_OTP_ATTEMPTS', default=5, cast=int),
    'OTP_LENGTH': config('OTP_LENGTH', default=6, cast=int),
    'MAX_FAILED_OTP_ATTEMPTS': config(
        'MAX_FAILED_OTP_ATTEMPTS', default=3, cast=int),
    'FAILED_RETRY_OTP_INTERVAL_MINUTES': config(
        'RETRY_OTP_INTERVAL_SECONDS', default=30, cast=int),
}
