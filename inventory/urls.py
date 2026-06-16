from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('items/', views.item_list, name='item_list'),
    path('items/<int:item_id>/', views.item_detail, name='item_detail'),
    path('items/add/', views.add_item, name='add_item'),
    path('items/<int:item_id>/update/', views.update_item, name='update_item'),
    path('movement/', views.record_movement, name='record_movement'),
    path('check-order-status/', views.check_order_status, name='check_order_status'),
    path('alerts/', views.alerts, name='alerts'),
    path('reports/', views.reports, name='reports'),
    
    # API endpoints
    path('api/items/add/', views.add_item_api, name='add_item_api'),
    path('api/items/<int:item_id>/update/', views.update_item_api, name='update_item_api'),
    path('api/orders/add/', views.add_order_api, name='add_order_api'),
    path('api/orders/check-status/', views.check_order_status_api, name='check_order_status_api'),
    path('api/check-production-status/', views.check_production_status_api, name='check_production_status_api'),
    path('api/orders/<int:order_id>/approve/', views.approve_order_api, name='approve_order_api'),
    path('api/orders/<int:order_id>/send-to-production/', views.send_to_production_api, name='send_to_production_api'),
    path('api/orders/<int:order_id>/request-materials/', views.request_materials_api, name='request_materials_api'),
]
