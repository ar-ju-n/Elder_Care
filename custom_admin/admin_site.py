from django.contrib import admin
from django.utils.translation import gettext_lazy as _


class ElderCareAdminSite(admin.AdminSite):
    site_header = _('Elder Care Administration')
    site_title = _('Elder Care Admin')
    index_title = _('Dashboard')
    
    def get_app_list(self, request, app_label=None):
        """
        Return a sorted list of all the installed apps that have been
        registered in this site.
        """
        app_dict = self._build_app_dict(request)
        
        # Sort the apps alphabetically.
        app_list = sorted(app_dict.values(), key=lambda x: x['name'].lower())

        # Sort the models alphabetically within each app.
        for app in app_list:
            app['models'].sort(key=lambda x: x['name'].lower())

        return app_list


# Create an instance of the custom admin site
admin_site = ElderCareAdminSite()
