import django_filters
from django_filters import rest_framework as filters

from recipes.models import Recipe, Tag, Ingredient


from django_filters.filters import BaseCSVFilter


QUERY_PARAM = (
    (1, 'true'),
    (0, 'false')
)


class RecipeFilter(django_filters.FilterSet):
    tags = filters.ModelMultipleChoiceFilter(queryset=Tag.objects.all(),
                                             field_name='tags__slug',
                                             to_field_name='slug')
    author = filters.CharFilter(field_name='author__username',
                                lookup_expr='exact')
    is_favorited = filters.ChoiceFilter(
        method='filter_favorited', choices=(QUERY_PARAM)
    )
    is_in_shopping_cart = filters.ChoiceFilter(
        method='filter_shopping_cart', choices=(QUERY_PARAM)
    )

    class Meta():
        model = Recipe
        fields = ['tags', 'author', 'is_favorited', 'is_in_shopping_cart']

    def filter_favorited(self, queryset, name, value):
        user = self.request.user
        if user.is_anonymous:
            return queryset.none()
        if value == '1':
            return queryset.filter(favorites__user=user)
        elif value == '0':
            return queryset.exclude(favorites__user=user)
        return queryset

    def filter_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if user.is_anonymous:
            return queryset.none()
        if value == '1':
            return queryset.filter(favorites__user=user)
        elif value == '0':
            return queryset.exclude(favorites__user=user)
        return queryset


class IngredientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name='name',
                                     lookup_expr='istartswith')
    # name__icontains = django_filters.CharFilter(field_name='name',
    #                                             lookup_expr='icontains')
    # name = django_filters.CharFilter(field_name='name',
    #                                  lookup_expr='icontains')

    class Meta:
        model = Ingredient
        fields = ['name']
