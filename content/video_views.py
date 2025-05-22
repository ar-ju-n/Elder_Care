from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from accounts.mixins import AdminRequiredMixin
from .models import Video, Tag
from .forms import VideoForm

class VideoListView(LoginRequiredMixin, ListView):
    model = Video
    template_name = 'content/video/list.html'
    context_object_name = 'videos'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = super().get_queryset().order_by('-published_at')
        search_query = self.request.GET.get('q')
        tag_slug = self.request.GET.get('tag')
        
        if search_query:
            queryset = queryset.filter(title__icontains=search_query)
        if tag_slug:
            queryset = queryset.filter(tags__name__iexact=tag_slug)
            
        return queryset.distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['all_tags'] = Tag.objects.all()
        context['search_query'] = self.request.GET.get('q', '')
        context['selected_tag'] = self.request.GET.get('tag', '')
        return context

class VideoDetailView(LoginRequiredMixin, DetailView):
    model = Video
    template_name = 'content/video/detail.html'
    context_object_name = 'video'

class VideoCreateView(AdminRequiredMixin, SuccessMessageMixin, CreateView):
    model = Video
    form_class = VideoForm
    template_name = 'content/video/form.html'
    success_url = reverse_lazy('video_list')
    success_message = "Video was created successfully!"
    
    def form_valid(self, form):
        form.instance.published_by = self.request.user
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add New Video'
        context['submit_text'] = 'Create Video'
        return context

class VideoUpdateView(AdminRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Video
    form_class = VideoForm
    template_name = 'content/video/form.html'
    success_url = reverse_lazy('video_list')
    success_message = "Video was updated successfully!"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit Video: {self.object.title}'
        context['submit_text'] = 'Update Video'
        return context

class VideoDeleteView(AdminRequiredMixin, DeleteView):
    model = Video
    template_name = 'content/video/confirm_delete.html'
    success_url = reverse_lazy('video_list')
    success_message = "Video was deleted successfully!"
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)

def toggle_video_status(request, pk):
    """Toggle video status between active/inactive"""
    if not request.user.is_authenticated or not request.user.is_admin:
        messages.error(request, 'You do not have permission to perform this action.')
        return redirect('video_list')
        
    video = get_object_or_404(Video, pk=pk)
    video.is_active = not video.is_active
    video.save()
    
    status = 'activated' if video.is_active else 'deactivated'
    messages.success(request, f'Video "{video.title}" has been {status}.')
    return redirect('video_list')
