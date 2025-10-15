from .models import UserProfile

def current_user(request):
    """
    Returns the currently logged-in user object (UserProfile) if session exists.
    """
    user_obj = None
    user_id = request.session.get('user_id')
    if user_id:
        try:
            user_obj = UserProfile.objects.get(pk=user_id)
        except UserProfile.DoesNotExist:
            request.session.flush()
    return {'user_obj': user_obj}
