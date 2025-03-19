from django.conf import settings
from django.urls import include, path
from django.contrib import admin

from wagtail.admin import urls as wagtailadmin_urls
from wagtail import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls

from search import views as search_views

from wagtail.api.v2.views import PagesAPIViewSet
from rest_framework.routers import DefaultRouter
from blog.api import BlogPageViewSet

# API Router Setup
api_router = DefaultRouter()
api_router.register(r'pages', PagesAPIViewSet, basename="wagtailapi_pages")
api_router.register(r'blog', BlogPageViewSet, basename="blog_api")

urlpatterns = [
    # Django and Wagtail Admin
    path("django-admin/", admin.site.urls),
    path("admin/", include(wagtailadmin_urls)),
    
    # Wagtail Documents
    path("documents/", include(wagtaildocs_urls)),
    
    # Search Route
    path("search/", search_views.search, name="search"),
    
    # API Endpoints
    path("api/v2/", include(api_router.urls)),
]

# Static and Media Files in Debug Mode
if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Wagtail Page Serving (Must be last!)
urlpatterns += [
    path("", include(wagtail_urls)),  
]