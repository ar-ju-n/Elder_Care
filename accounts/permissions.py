from rest_framework import permissions
from django.contrib.auth import get_user_model

User = get_user_model()

class IsAdminUser(permissions.BasePermission):
    """
    Allows access only to admin users.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.role == User.ADMIN)

class IsCaregiverUser(permissions.BasePermission):
    """
    Allows access only to caregiver users.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.role == User.CAREGIVER)

class IsFamilyUser(permissions.BasePermission):
    """
    Allows access only to family users.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.role == User.FAMILY)

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Instance must have an attribute named 'owner'.
        return obj.owner == request.user

# Custom permissions for specific actions
class CanApproveCaregiver(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.role == User.ADMIN)

class CanCreateJob(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.role in [User.ADMIN, User.FAMILY])

class CanApplyForJob(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.role == User.CAREGIVER)

class CanManageContent(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.role == User.ADMIN)

class CanParticipateInForum(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.role in [User.ADMIN, User.CAREGIVER, User.FAMILY])

class CanManageForum(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.role in [User.ADMIN, User.FAMILY])
