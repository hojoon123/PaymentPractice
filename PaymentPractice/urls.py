from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("", TemplateView.as_view(template_name="root.html"), name="root"),
    path("mall_test/", include("mall_test.urls")),
    path("mall/", include("mall.urls")),
]

if settings.DEBUG:
    urlpatterns += [path("__debug__", include("debug_toolbar.urls"))]
    # debug가 거짓이면 빈리스트를 반환
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
