from django.urls import path
from . import views

app_name = 'excel_app'

urlpatterns = [
    path('', views.table_view, name='table'),
    path('upload/', views.upload_view, name='upload'),
    path('delete/<int:pk>/', views.delete_record, name='delete_record'),
    path('checklist/', views.checklist_view, name='checklist'),
    path('upload_excel/', views.upload_view, name='upload_excel'),
    path('table/', views.table_view, name='table_view'),
    path('view/<int:pk>/', views.view_excel_data, name='view_excel_data'),
    path('bulk-delete/', views.bulk_delete, name='bulk_delete'),
    path('api/broadcast/', views.broadcast_api, name='broadcast_api'),
    path('checklist/<int:excel_id>/', views.checklist_detail, name='checklist_detail'),
    path('download-sample/', views.download_sample_excel, name='download_sample'),
]