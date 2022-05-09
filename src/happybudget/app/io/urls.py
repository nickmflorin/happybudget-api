from django.urls import path

from .views import TempUploadImageView, TempUploadFileView

app_name = "io"

urlpatterns = [
    path('temp-upload-image/', TempUploadImageView.as_view()),
    path('temp-upload-file/', TempUploadFileView.as_view()),
]
