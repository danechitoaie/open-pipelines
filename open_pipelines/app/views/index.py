# Django
from django.views.generic import View
from django.shortcuts     import render

# Open Pipelines
from ..decorators import login_required


class IndexView(View):
    @login_required
    def get(self, request):
        return render(request, "index.html")
