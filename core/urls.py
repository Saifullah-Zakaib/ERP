from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Auth
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Core Pages
    path('', views.home_view, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('profile/', views.profile, name='profile'),
    path('change-password/', views.change_password, name='change_password'),
    path('help/', views.help_page, name='help'),
    path('notifications/', views.notifications, name='notifications'),
    path('ai-insights/', views.ai_insights_view, name='ai_insights'),
    
    # AI Insights API
    path('api/ai-insights/', views.ai_insights_api, name='ai_insights_api'),
    
    # ========== PASSWORD RESET URLs ==========
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-requests/', views.reset_requests, name='reset_requests'),
    path('approve-reset/<int:request_id>/', views.approve_reset, name='approve_reset'),
    path('reset-password/<int:user_id>/', views.reset_password, name='reset_password'),
    path('reject-reset/<int:request_id>/', views.reject_reset, name='reject_reset'),
    
    # ========== USER MANAGEMENT URLs ==========
 path('api/users/add/', views.add_user, name='add_user'),
    path('api/users/<int:user_id>/update/', views.update_user, name='update_user'),
    path('api/users/<int:user_id>/delete/', views.delete_user, name='delete_user'),
    
    
    
   # Notice management (Admin only)
    path('api/notices/post/', views.post_notice_api, name='post_notice'),
]