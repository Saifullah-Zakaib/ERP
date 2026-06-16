from django.urls import path
from . import views

app_name = 'suppliers'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/add/', views.add_supplier, name='add_supplier'),
    path('suppliers/<int:supplier_id>/', views.supplier_detail, name='supplier_detail'),
    path('purchase-orders/', views.purchase_order_list, name='purchase_order_list'),
    path('purchase-orders/create/', views.create_purchase_order, name='create_purchase_order'),
    path('purchase-orders/<int:po_id>/', views.po_detail, name='po_detail'),
    path('material-requests/', views.material_requests, name='material_requests'),
    
    # Reports and Tracking
    path('reports/performance/', views.supplier_performance_report, name='performance_report'),
    path('reports/purchase/', views.purchase_report, name='purchase_report'),
    path('tracking/', views.order_tracking, name='order_tracking'),
    
    # API endpoints
    path('api/suppliers/add/', views.add_supplier_api, name='add_supplier_api'),
    path('api/suppliers/<int:supplier_id>/delete/', views.delete_supplier_api, name='delete_supplier_api'),
    path('api/suppliers/<int:supplier_id>/update-rating/', views.update_supplier_rating_api, name='update_supplier_rating_api'),
    path('api/purchase-orders/create/', views.create_purchase_order_api, name='create_purchase_order_api'),
    path('api/purchase-orders/<int:po_id>/update-status/', views.update_purchase_order_status, name='update_purchase_order_status'),
    path('api/purchase-orders/status-updates/', views.get_purchase_orders_status, name='get_purchase_orders_status'),
    path('api/notifications/', views.notifications_api, name='notifications_api'),
]
