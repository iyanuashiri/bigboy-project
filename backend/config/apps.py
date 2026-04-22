from django.contrib.admin.apps import AdminConfig


class BigBoyAdminConfig(AdminConfig):
    default_site = 'config.admin.BigBoyAdminSite'
