from rest_framework import generics, viewsets
from rest_framework.pagination import PageNumberPagination
from ..models import  HazardFeeds, HazardLevels
from ..serializers import HazardWarningsSerializer, HazardLevelModelSerializer
from django_filters.rest_framework import DjangoFilterBackend

class MyPageNumberPagination(PageNumberPagination):
    page_size = 10

class HazardLevelsViewset(viewsets.ReadOnlyModelViewSet):
    queryset = HazardLevels.objects.all()
    serializer_class = HazardLevelModelSerializer


class HazardListAPIView(generics.ListAPIView):
    queryset = HazardFeeds.objects.all()
    serializer_class = HazardWarningsSerializer
    # pagination_class = MyPageNumberPagination
    # filter_backends =  [DjangoFilterBackend]

