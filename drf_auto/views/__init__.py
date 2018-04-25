"""
Вьюхи с автодокой.

"""
from django.http import Http404
from django.views.generic.base import TemplateView

from ..autodocs.docs import ApiDocumentation
from ..autodocs.settings import DocsSettings


class DRFDocsView(TemplateView):

    template_name = 'drf_auto/home.html'
    drf_router = None

    def get_context_data(self, **kwargs):
        if DocsSettings.HIDE_DOCS:
            raise Http404()

        context = super(DRFDocsView, self).get_context_data(**kwargs)
        docs = ApiDocumentation(drf_router=self.drf_router)
        endpoints = docs.get_endpoints()

        query = self.request.GET.get('query', '')
        if query and endpoints:
            endpoints = [endpoint for endpoint in endpoints if query in endpoint.path]

        context['query'] = query
        context['endpoints'] = endpoints
        context['all_methods'] = docs.all_methods
        return context
