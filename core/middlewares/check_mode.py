import json
from django.http.response import HttpResponseRedirect, HttpResponse
from django.urls import reverse


class CheckModeMiddleware(object):

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        from core.models import Mode

        mode, created = Mode.objects.get_or_create(id=1, defaults={'readonly': False, 'maintenance': False, 'down': False, })
        readonly = mode.readonly
        maintenance = mode.maintenance
        down = mode.down
        if not request.user.is_superuser:
            if down:
                if request.is_ajax():
                    response_data = {}
                    response_data['status'] = 'false'
                    response_data['message'] = "Application currently down. Please try again later."
                    response_data['static_message'] = "true"
                    return HttpResponse(json.dumps(response_data), content_type='application/javascript')
                else:
                    return HttpResponseRedirect(reverse('down'))
            elif readonly:
                if request.is_ajax():
                    response_data = {}
                    response_data['status'] = 'false'
                    response_data['message'] = "Application now readonly mode. please try again later."
                    response_data['static_message'] = "true"
                    return HttpResponse(json.dumps(response_data), content_type='application/javascript')
                else:
                    return HttpResponseRedirect(reverse('read_only'))