from rest_framework import viewsets, mixins


class CreateDestroyViewSet(mixins.CreateModelMixin,
                           mixins.DestroyModelMixin,
                           viewsets.GenericViewSet):
    pass


class ListRetrieveCreateDestroyBaseViewSet(mixins.ListModelMixin,
                                           mixins.RetrieveModelMixin,
                                           mixins.CreateModelMixin,
                                           mixins.DestroyModelMixin,
                                           viewsets.GenericViewSet):
    pass
