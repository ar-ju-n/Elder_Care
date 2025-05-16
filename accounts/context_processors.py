def emergency_contacts(request):
    if request.user.is_authenticated:
        return {'emergency_contacts': request.user.emergency_contacts.all()}
    return {'emergency_contacts': []}
