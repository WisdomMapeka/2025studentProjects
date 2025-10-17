from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('reports/', views.ReportsView.as_view(), name='reports'),
    path('export/csv/', views.export_csv, name='export_csv'),
    path('export/xlsx/', views.export_xlsx, name='export_xlsx'),
]
