
from django.urls import path
from .views import GroupCreateView, GroupDeleteView, GroupDetailView, GroupMemberManageView, GroupUpdateView, TaskCreateView, TaskListView, TaskUpdateView, TaskMarkCompleteView, TaskDeleteView, GroupListView

urlpatterns = [
    path('', TaskListView.as_view(), name='task_list'),
    path('create/', TaskCreateView.as_view(), name='task_create'),
    path('create/for_group/<uuid:group_id>/', TaskCreateView.as_view(), name='task_create_for_group'),
    path('<uuid:pk>/update/', TaskUpdateView.as_view(), name='task_update'),
    path('<uuid:pk>/complete/', TaskMarkCompleteView.as_view(), name='task_complete'),
    path('<uuid:pk>/delete/', TaskDeleteView.as_view(), name='task_delete'),

    #groups urls
    path('groups/', GroupListView.as_view(), name='group_list'),

    path('groups/create/', GroupCreateView.as_view(), name='group_create'),
    path('groups/<uuid:pk>/', GroupDetailView.as_view(), name='group_detail'), # New detail view
    path('groups/<uuid:pk>/edit/', GroupUpdateView.as_view(), name='group_edit'), # New edit view
    path('groups/<uuid:pk>/delete/', GroupDeleteView.as_view(), name='group_delete'), # New delete view
    path('groups/<uuid:pk>/members/', GroupMemberManageView.as_view(), name='group_members_manage'), # New member management
]