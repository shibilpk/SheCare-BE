from typing import List, Optional, Any, Generic
from ninja import Schema
from ninja_extra.pagination import PageNumberPaginationExtra
from ninja_extra.schemas.response import Url, T
from collections import OrderedDict
from django.core.paginator import Page
from ninja.types import DictStrAny


class BasePaginatedResponseSchema(Schema):
    page_obj: DictStrAny
    next: Optional[Url]
    previous: Optional[Url]
    results: List[Any]


class PaginatedResponseSchema(BasePaginatedResponseSchema, Generic[T]):
    results: List[T]


class CustomPagination(PageNumberPaginationExtra):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(
        self, *, base_url: str, page: Page
    ) -> DictStrAny:
        paginator = page.paginator

        page_obj = {
            "number": page.number,
            "start_index": page.start_index(),
            "has_other_pages": page.has_other_pages(),
            "has_previous": page.has_previous(),
            "has_next": page.has_next(),
            "paginator": {
                "num_pages": paginator.num_pages,
                "count": paginator.count,
            },
        }

        if page.has_previous():
            page_obj["previous_page_number"] = page.previous_page_number()

        if page.has_next():
            page_obj["next_page_number"] = page.next_page_number()

        return OrderedDict(
            [
                ("page_obj", page_obj),
                ("next", self.get_next_link(base_url, page=page)),
                ("previous", self.get_previous_link(base_url, page=page)),
                ("results", list(page)),
            ]
        )
