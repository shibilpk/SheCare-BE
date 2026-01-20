from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from collections import OrderedDict, namedtuple


class CustomPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


    def get_paginated_response(self, data):

        page_obj = {
            'paginator':{}
        }

        page_obj['has_other_pages'] = self.page.has_other_pages()
        page_obj['paginator']['num_pages'] = self.page.paginator.num_pages
        page_obj['paginator']['count'] = self.page.paginator.count
        page_obj['start_index'] = self.page.start_index()
        page_obj['paginator']['page_range'] = list(self.page.paginator.page_range)
        page_obj['number'] = self.page.number

        page_obj['has_previous'] = self.page.has_previous()
        if self.page.has_previous():
            page_obj['previous_page_number'] = self.page.previous_page_number()

        page_obj['has_next'] = self.page.has_next()
        if self.page.has_next():
            page_obj['next_page_number'] = self.page.next_page_number()

        return Response(OrderedDict([

            ('page_obj', page_obj),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ]))