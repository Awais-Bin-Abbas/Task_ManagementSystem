# pagination.py

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardPagination(PageNumberPagination):
    page_size = 5                      # default items per page
    page_size_query_param = 'page_size' # user can override like ?page_size=5
    max_page_size = 100                 # maximum items per page allowed

    def get_paginated_response(self, data):
        return Response({
            'total': self.page.paginator.count,       # total items in database
            'page_size': self.get_page_size(self.request),  # items per page
            'current_page': self.page.number,         # current page number
            'total_pages': self.page.paginator.num_pages,   # total pages
            'next': self.get_next_link(),              # link to next page
            'previous': self.get_previous_link(),     # link to previous page
            'results': data                           # actual data
        })