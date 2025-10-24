from django.urls import path
from . import views

urlpatterns = [
    path('', views.queue_list, name='queue_list'),
    path('<int:pk>/', views.queue_detail, name='queue_detail'),
    path('<int:pk>/done/', views.mark_as_done, name='mark_as_done'),
    path('<int:pk>/start/', views.start_serving, name='start_serving'),
]
