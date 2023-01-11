from django.urls import path

from app.myapp import views

app_name = "myapp"

urlpatterns = [
    path("", views.MyView.as_view(), name="myview"),
]
