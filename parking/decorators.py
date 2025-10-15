# parking/decorators.py

from functools import wraps
from django.shortcuts import redirect

def login_required_phone(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user_id = request.session.get('user_id')
        if not user_id:
            return redirect('login_with_phone')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
