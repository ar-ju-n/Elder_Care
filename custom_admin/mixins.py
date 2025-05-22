"""
Mixins for Custom Admin Views
"""
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect

class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to ensure user is an admin."""
    def test_func(self):
        return self.request.user.is_authenticated and (self.request.user.is_superuser or self.request.user.is_staff)
    
    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            messages.error(self.request, 'Please log in to access this page.')
            return super().handle_no_permission()
        messages.error(self.request, 'You do not have permission to access this page.')
        return redirect('custom_admin:dashboard')

class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to ensure user is staff."""
    def test_func(self):
        return self.request.user.is_staff
    
    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            messages.error(self.request, 'Please log in to access this page.')
            return super().handle_no_permission()
        messages.error(self.request, 'You do not have permission to access this page.')
        return redirect('custom_admin:dashboard')

class SuperuserRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to ensure user is a superuser."""
    def test_func(self):
        return self.request.user.is_superuser
    
    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            messages.error(self.request, 'Please log in to access this page.')
            return super().handle_no_permission()
        messages.error(self.request, 'You do not have permission to access this page.')
        return redirect('custom_admin:dashboard')

class SuccessMessageMixin:
    """Add a success message on successful form submission."""
    success_message = ''

    def form_valid(self, form):
        response = super().form_valid(form)
        success_message = self.get_success_message(form.cleaned_data)
        if success_message:
            messages.success(self.request, success_message)
        return response

    def get_success_message(self, cleaned_data):
        return self.success_message % cleaned_data

class FormInvalidMessageMixin:
    """Add an error message on invalid form submission."""
    form_invalid_message = 'Please correct the errors below.'

    def form_invalid(self, form):
        response = super().form_invalid(form)
        messages.error(self.request, self.get_form_invalid_message())
        return response

    def get_form_invalid_message(self):
        return self.form_invalid_message


class NextUrlMixin:
    """Mixin to handle next URL redirection after form submission."""
    next_page = None
    
    def get_success_url(self):
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
        return super().get_success_url()


class ObjectOwnerMixin:
    """Mixin to ensure the user owns the object being accessed."""
    owner_field = 'user'
    
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(**{self.owner_field: self.request.user})


class PaginationMixin:
    """
    Mixin to add pagination to list views.
    """
    paginate_by = 20
    paginate_orphans = 2
    page_kwarg = 'page'
    
    def get_paginate_by(self, queryset):
        """
        Override to customize the number of items per page.
        """
        return self.request.GET.get('per_page', self.paginate_by)

class SearchMixin:
    """
    Mixin to add search functionality to list views.
    """
    search_fields = []
    search_param = 'q'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get(self.search_param)
        
        if query and self.search_fields:
            q = Q()
            for field in self.search_fields:
                q |= Q(**{f"{field}__icontains": query})
            queryset = queryset.filter(q)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get(self.search_param, '')
        return context

class ExportMixin:
    """
    Mixin to add export functionality to list views.
    """
    export_formats = ['csv', 'json', 'xlsx']
    export_fields = []
    export_filename = 'export'
    
    def get_export_filename(self, format):
        """
        Returns the filename for the exported file.
        """
        return f"{self.export_filename}.{format}"
    
    def get_export_queryset(self):
        """
        Returns the queryset to be exported.
        """
        return self.get_queryset()
    
    def get_export_data(self, format, queryset):
        """
        Returns the data to be exported in the specified format.
        """
        if format == 'csv':
            return self.export_to_csv(queryset)
        elif format == 'json':
            return self.export_to_json(queryset)
        elif format == 'xlsx':
            return self.export_to_xlsx(queryset)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def export_to_csv(self, queryset):
        """Export the queryset to CSV format."""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        filename = self.get_export_filename('csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        writer = csv.writer(response)
        writer.writerow(self.export_fields)
        
        for obj in queryset:
            row = [getattr(obj, field, '') for field in self.export_fields]
            writer.writerow(row)
        
        return response
    
    def export_to_json(self, queryset):
        """Export the queryset to JSON format."""
        from django.http import JsonResponse
        from django.core import serializers
        
        data = serializers.serialize('json', queryset, fields=self.export_fields)
        response = JsonResponse(data, safe=False)
        filename = self.get_export_filename('json')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    
    def export_to_xlsx(self, queryset):
        """Export the queryset to XLSX format."""
        from openpyxl import Workbook
        from django.http import HttpResponse
        
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        filename = self.get_export_filename('xlsx')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        wb = Workbook()
        ws = wb.active
        ws.title = 'Export'
        
        # Add headers
        ws.append(self.export_fields)
        
        # Add data
        for obj in queryset:
            row = [getattr(obj, field, '') for field in self.export_fields]
            ws.append(row)
        
        wb.save(response)
        return response
    
    def get(self, request, *args, **kwargs):
        """
        Handles GET requests and exports data if requested.
        """
        export_format = request.GET.get('export')
        
        if export_format in self.export_formats:
            queryset = self.get_export_queryset()
            return self.get_export_data(export_format, queryset)
        
        return super().get(request, *args, **kwargs)
