from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib import messages
from users.models import Group, Membership
from .forms import GroupMemberForm, TaskForm
from .models import Task
from django.db import models
from datetime import date
from django.urls import reverse, reverse_lazy
from django.contrib.auth.mixins import UserPassesTestMixin

class TaskOwnerOrGroupAdminMixin(UserPassesTestMixin):
    def test_func(self):
        task = self.get_object()
        # Check if user is the task owner
        if task.owner == self.request.user:
            return True
        # Check if task belongs to a group and user is group admin
        if task.group and task.group.admin == self.request.user:
            return True
        # Check if task belongs to a group and user is a member (allowing deletion/edit for members is a choice)
        # For simplicity, keeping it owner/admin for modify/delete for now.
        return False
    
    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission to perform this action on this task.")
        return redirect(self.request.META.get('HTTP_REFERER', reverse_lazy('task_list')))


# Mixin to ensure only the group admin can access certain group management features
class GroupAdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        group = self.get_object()
        return self.request.user == group.admin

    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission to perform this action.")
        return redirect(reverse_lazy('group_list')) # Redirect to group list if not admin
from django.utils.timezone import localdate

class TaskListView(LoginRequiredMixin,ListView):
    model = Task
    template_name = 'tasks/task_list.html'
    context_object_name = 'tasks'
    paginate_by = 10

    def get_queryset(self):
        status_filter = self.request.GET.get('status')
    
        queryset = Task.objects.filter(
            models.Q(owner=self.request.user) | 
            models.Q(assignee=self.request.user) | 
            models.Q(group__members__user=self.request.user) | 
            models.Q(group__admin=self.request.user)
        ).distinct()

        Task.objects.filter(due_date__lt=date.today(), status='ongoing').update(status='overdue')

    
        if status_filter == 'ongoing':
            queryset = queryset.filter(status='ongoing').exclude(due_date__lt=date.today())
    
        elif status_filter == 'completed':
            queryset = queryset.filter(status='completed')
    
        elif status_filter == 'overdue':
            queryset = queryset.filter(due_date__lt=date.today(), status__in=['ongoing', 'overdue'])

        elif status_filter == 'all':
            pass  # Show all tasks (queryset already built)
    
        else:
            queryset = queryset.filter(status='ongoing').exclude(due_date__lt=date.today())
    
        queryset = queryset.order_by('due_date', '-created_at')
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_status_filter'] = self.request.GET.get('status', 'ongoing')
        return context

class TaskCreateView(LoginRequiredMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'
    success_url = reverse_lazy('task_list') # Default redirect

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request_user'] = self.request.user
        
        group_id = self.kwargs.get('group_id') 
        if group_id:
            try:
                group = Group.objects.get(pk=group_id)
                if not (self.request.user == group.admin or Membership.objects.filter(group=group, user=self.request.user).exists()):
                    messages.error(self.request, "You do not have permission to add tasks to this group.")
                    return redirect(reverse_lazy('group_list'))
                kwargs['specific_group'] = group
            except Group.DoesNotExist:
                messages.error(self.request, "Invalid group specified.")
                return redirect(reverse_lazy('task_list'))
        return kwargs

    def form_valid(self, form):
        task = form.save(commit=False)
        task.owner = self.request.user

        group_id = self.kwargs.get('group_id')
        if group_id:
            try:
                task.group = Group.objects.get(pk=group_id)
            except Group.DoesNotExist:
                messages.error(self.request, "Invalid group specified during task creation.")
                return redirect(reverse_lazy('task_list'))
        
        if not task.assignee:
            if not task.group:
                task.assignee = self.request.user
            elif self.request.user == task.group.admin or Membership.objects.filter(group=task.group, user=self.request.user).exists():
                 task.assignee = self.request.user
            else:
                messages.warning(self.request, "Task created for group but no assignee selected, and you are not a member to self-assign. It is unassigned.")

        task.save()

        messages.success(self.request, 'Task created successfully!')
        if task.group:
            return redirect(reverse('group_detail', kwargs={'pk': str(group_id)})) 
        return redirect('task_list')
        

# View for updating an existing task
class TaskUpdateView(LoginRequiredMixin, TaskOwnerOrGroupAdminMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'
    context_object_name = 'task'

    def get_success_url(self):
        if self.object.group:
            # FIX: Ensure self.object.group.pk is a string for reverse_lazy
            return reverse_lazy('group_detail', kwargs={'pk': str(self.object.group.pk)})
        return reverse_lazy('task_list')

    def form_valid(self, form):
        task = form.save(commit=False)

        if 'due_date' in form.changed_data and task.status == 'overdue' and self.request.user != task.owner:
            messages.error(self.request, "Only the task owner can change the due date of an overdue task.")
            return self.form_invalid(form) 

        task.save()

        messages.success(self.request, 'Task updated successfully!')
        if task.group:
            # FIX: Ensure task.group.pk is a string for redirect
            return redirect(reverse_lazy('group_detail', kwargs={'pk': str(task.group.pk)}))
        return redirect(self.get_success_url())
    
class TaskMarkCompleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
            task = get_object_or_404(Task, pk=pk)
            is_owner = task.owner == request.user
            is_assignee = task.assignee == request.user and task.assignee is not None
            is_group_admin = task.group and task.group.admin == request.user
            is_group_member = task.group and Membership.objects.filter(group=task.group, user=request.user).exists()

            if not (is_owner or is_assignee or is_group_admin or is_group_member):
                messages.error(request, "You do not have permission to complete this task.")
                return redirect('task_list')
           
            if task.status != 'completed':
                task.status = 'completed'
                task.save()
                messages.success(request, "Task marked as completed.")
            else:
                messages.info(request, "Task is already completed.")
            return redirect('task_list')
    
class TaskDeleteView(LoginRequiredMixin, DeleteView):
    model = Task
    template_name = 'tasks/task_confirm_delete.html'
    context_object_name = 'task'

    def get_success_url(self):
        if self.object.group:
            return reverse_lazy('group_detail', kwargs={'pk': self.object.group.pk})
        return reverse_lazy('task_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Task deleted successfully.")
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Delete Task'
        context['group_id'] = self.object.group.id if self.object.group else None
        return context
    
class TaskOwnerOrGroupAdminMixin(UserPassesTestMixin):
    def test_func(self):
        task = self.get_object()

        if task.owner == self.request.user:
            return True
        
        if task.group and task.group.admin == self.request.user:
            return True
        
        return False
        
    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission to perform this action.")
        return redirect('task_list')
    
class GroupAdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        group = self.get_object()
        return self.request.user == group.admin
    
    def handle_no_permission(self):
        messages.error(self.request, "You must be the group admin to perform this action.")
        return redirect('group_list')

# Group Management Views
class GroupListView(LoginRequiredMixin, ListView):
    model = Group
    template_name = 'groups/group_list.html'
    context_object_name = 'groups'

    def get_queryset(self):
        return Group.objects.filter(
            models.Q(admin=self.request.user) |
            models.Q(members__user=self.request.user)
        ).distinct().order_by('name')


class GroupCreateView(LoginRequiredMixin, CreateView):
    model = Group
    fields = ['name']
    template_name = 'groups/group_form.html'
    success_url = reverse_lazy('group_list')

    def form_valid(self, form):
        form.instance.admin = self.request.user
        group = form.save()
        Membership.objects.create(user=self.request.user, group=group)
        messages.success(self.request, f'Group "{group.name}" created successfully!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Create New Group'
        return context


class GroupDetailView(LoginRequiredMixin, DetailView):
    model = Group
    template_name = 'groups/group_detail.html'
    context_object_name = 'group'

    def get_queryset(self):
        return Group.objects.filter(
            models.Q(admin=self.request.user) |
            models.Q(members__user=self.request.user)
        ).distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = self.get_object()
        context['members'] = group.members.all().order_by('user__username')
        context['tasks'] = group.tasks.all().order_by('due_date', '-created_at')
        context['is_admin'] = (self.request.user == group.admin)
        return context


class GroupUpdateView(GroupAdminRequiredMixin, UpdateView):
    model = Group
    fields = ['name']
    template_name = 'groups/group_form.html'
    context_object_name = 'group'

    def get_success_url(self):
        return reverse_lazy('group_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, f'Group "{form.instance.name}" updated successfully.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Edit Group'
        return context


class GroupDeleteView(GroupAdminRequiredMixin, DeleteView):
    model = Group
    template_name = 'groups/group_confirm_delete.html'
    context_object_name = 'group'
    success_url = reverse_lazy('group_list')

    def form_valid(self, form):
        messages.success(self.request, f'Group "{self.object.name}" deleted successfully.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Delete Group'
        return context


class GroupMemberManageView(GroupAdminRequiredMixin, UpdateView):
    model = Group
    form_class = GroupMemberForm
    template_name = 'groups/group_member_manage.html'
    context_object_name = 'group'

    def get_success_url(self):
        return reverse_lazy('group_detail', kwargs={'pk': self.object.pk})

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(
            data=self.request.POST if self.request.method == 'POST' else None,
            files=self.request.FILES if self.request.method == 'POST' else None,
            group=self.get_object()
        )

    def form_valid(self, form):
        group = self.get_object()
        selected_members = form.cleaned_data['members']

        if group.admin not in selected_members:
            selected_members = list(selected_members) + [group.admin]

        current_members = [m.user for m in group.members.exclude(user=group.admin)]

        members_to_add = set(selected_members) - set(current_members)
        for user_to_add in members_to_add:
            if user_to_add != group.admin:
                Membership.objects.get_or_create(group=group, user=user_to_add)

        members_to_remove = set(current_members) - set(selected_members)
        for user_to_remove in members_to_remove:
            Membership.objects.filter(group=group, user=user_to_remove).delete()

        messages.success(self.request, f'Members for group "{group.name}" updated successfully.')
        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Manage Members for "{self.object.name}"'
        return context