from django import template
from ..utils import get_permitted_actions

register = template.Library()

@register.simple_tag(takes_context=True)
def has_permission(context, permission_name):
    """Check if the current user has the specified permission."""
    user = context.get('user')
    if not user or not user.is_authenticated:
        return False
    
    permissions = get_permitted_actions(user)
    return permissions.get(permission_name, False)

@register.inclusion_tag('accounts/includes/permission_denied.html')
def require_permission(permission_name):
    """Render content only if the user has the specified permission."""
    return {'permission_name': permission_name}

@register.filter
def has_role(user, role_name):
    """Check if the user has the specified role."""
    if not user or not user.is_authenticated:
        return False
    return user.role == role_name.lower()

@register.filter
def has_any_role(user, roles):
    """Check if the user has any of the specified roles."""
    if not user or not user.is_authenticated:
        return False
    return user.role in [r.lower().strip() for r in roles.split(',')]
