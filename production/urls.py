from django.urls import path
from . import views

app_name = 'production'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('orders/', views.order_list, name='order_list'),
    path('orders/create/', views.create_order, name='create_order'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('orders/<int:order_id>/update/', views.update_order_status, name='update_order_status'),
    path('orders/<int:order_id>/bom/', views.manage_bom, name='manage_bom'),
    path('orders/<int:order_id>/issue-materials/', views.issue_materials, name='issue_materials'),
    path('quality-check/<int:order_id>/', views.quality_check, name='quality_check'),
    path('reports/', views.reports, name='reports'),
    
    # API endpoints
    path('api/orders/create/', views.create_order_api, name='create_order_api'),
    path('api/orders/list/', views.list_orders_api, name='list_orders_api'),
    path('api/orders/<int:order_id>/update/', views.update_order_api, name='update_order_api'),
    path('api/notifications/', views.get_notifications_api, name='get_notifications_api'),
]
