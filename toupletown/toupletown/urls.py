from django.contrib import admin
from django.urls import path
from weather import views as weatherviews
from quote import views as quoteviews

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", weatherviews.main, name="main"),
    path("quote/", quoteviews.get_quote, name="quote")
]
