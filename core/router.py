from django.urls import path

from core.helpers import transform_string


class SimpleRouter:
    def __init__(self):
        self.registry = []

    def register(self, prefix, viewset):
        self.registry.append(
            {
                "prefix": prefix,
                "viewset": viewset,
                "basename": transform_string(viewset.model.__name__),
            }
        )

    def get_urls(self):
        urlpatterns = []
        for entry in self.registry:
            prefix = entry["prefix"]
            viewset = entry["viewset"]
            basename = entry["basename"]

            urlpatterns += [
                path(
                    f"{prefix}/list/",
                    viewset.as_view(
                        {
                            "get": "list",
                        },

                    ),
                    name=f"list-{basename}",
                ),
                path(
                    f"{prefix}/create/",
                    viewset.as_view(
                        {"get": "get_for_create", "post": "create"},

                    ),
                    name=f"create-{basename}",
                ),
                path(
                    f"{prefix}/retrieve/<uuid:pk>/",
                    viewset.as_view({"get": "retrieve"},),
                    name=f"retrieve-{basename}",
                ),
                path(
                    f"{prefix}/update/<uuid:pk>/",
                    viewset.as_view(
                        {"get": "get_for_update", "post": "update"},

                    ),
                    name=f"update-{basename}",
                ),
                path(
                    f"{prefix}/destroy/<uuid:pk>/",
                    viewset.as_view({"delete": "destroy"},),
                    name=f"destroy-{basename}",
                ),
                path(
                    f"{prefix}/autocomplete/",
                    viewset.as_view(
                        {
                            "get": "get_for_autocomplete",
                            "post": "post_for_autocomplete"
                        },

                    ),
                    name=f"autocomplete-{basename}",
                ),
            ]
        return urlpatterns

    @property
    def urls(self):
        return self.get_urls()
