import json
from django.http.response import HttpResponse
from django.shortcuts import render
from core.helpers import get_current_roles


def role_required(roles):
    def _method_wrapper(view_method):
        def _arguments_wrapper(request, *args, **kwargs):
            current_role = get_current_roles(request.user)
            matches = len(list(set(current_role).intersection(roles)))
            prev_page = request.META.get('HTTP_REFERER', None)
            if not matches and matches < 1:
                if request.is_ajax():
                    response_data = {
                        'status': 'false',
                        'title': 'Permission Denied',
                        'message': "You have no permission to do this action.",
                        'prev_page': prev_page,
                    }
                    return HttpResponse(json.dumps(response_data), content_type='application/javascript')
                else:
                    context = {
                        "title": "Permission Denied",
                        'message': "You have no permission to do this action.",
                        'prev_page': prev_page,
                        'error_code': 500

                    }
                    return render(request, 'errors/500.html', context)

            return view_method(request, *args, **kwargs)

        return _arguments_wrapper

    return _method_wrapper


def ajax_required(function):
    def wrap(request, *args, **kwargs):
        if request.headers.get('x-requested-with') != 'XMLHttpRequest':
            return render(request, 'error/400.html', {})
        return function(request, *args, **kwargs)
    wrap.__doc__ = function.__doc__
    return wrap
