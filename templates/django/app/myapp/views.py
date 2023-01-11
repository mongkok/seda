from django.http import JsonResponse
from django.views.generic import View

from app.myapp.tasks import mytask


class MyView(View):
    def get(self, request):
        return JsonResponse({"task": mytask()})
