"""Standard pagination (cursor-based)."""
from typing import Any

from rest_framework.pagination import BasePagination
from rest_framework.request import Request
from rest_framework.response import Response


class CursorPagination(BasePagination):
    """Cursor-based pagination for large datasets.

    Uses cursor-based pagination instead of offset-based for better performance
    with large datasets and consistent results during data changes.
    """

    page_size = 20
    cursor_query_param = 'cursor'
    page_size_query_param = 'page_size'

    def paginate_queryset(
        self,
        queryset: Any,
        request: Request,
        view: Any = None,
    ) -> Any:
        """Paginate queryset using cursor."""
        # Get page size from request
        page_size = self.get_page_size(request)

        # Get cursor from request
        cursor = request.query_params.get(self.cursor_query_param)

        if cursor:
            # Decode cursor and filter queryset
            # TODO: Implement cursor encoding/decoding
            pass

        # Limit queryset
        return queryset[:page_size]

    def get_paginated_response(self, data: list[Any]) -> Response:
        """Return paginated response with metadata."""
        return Response({
            'results': data,
            'metadata': {
                'next_cursor': None,  # TODO: Encode next cursor
                'page_size': self.page_size,
                'has_more': False,  # TODO: Check if more results exist
            },
        })

    def get_page_size(self, request: Request) -> int:
        """Get page size from request or default."""
        if self.page_size_query_param:
            try:
                page_size = int(request.query_params[self.page_size_query_param])
                if 0 < page_size <= 100:  # Max 100 per page
                    return page_size
            except (ValueError, TypeError):
                pass

        return self.page_size
