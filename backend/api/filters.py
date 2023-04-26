import django_filters
from django_filters import rest_framework as filters
from recipes.models import Ingredient, Recipe, Tag

QUERY_PARAM = (
    (1, 'true'),
    (0, 'false')
)


class RecipeFilter(django_filters.FilterSet):
    tags = filters.ModelMultipleChoiceFilter(queryset=Tag.objects.all(),
                                             field_name='tags__slug',
                                             to_field_name='slug')
    author = filters.CharFilter(field_name='author__id')
    is_favorited = filters.ChoiceFilter(
        method='filter_favorited', choices=(QUERY_PARAM)
    )
    is_in_shopping_cart = filters.ChoiceFilter(
        method='filter_shopping_cart', choices=(QUERY_PARAM)
    )

    class Meta():
        model = Recipe
        fields = ['tags', 'author', 'is_favorited', 'is_in_shopping_cart']

    def filter_by_field(self, queryset, value, field):
        user = self.request.user
        if user.is_anonymous:
            return queryset.none()
        if value == '1':
            return queryset.filter(**{field + '__user': user})
        elif value == '0':
            return queryset.exclude(**{field + '__user': user})
        return queryset

    def filter_favorited(self, queryset, name, value):
        return self.filter_by_field(queryset, value, 'favorites')

    def filter_shopping_cart(self, queryset, name, value):
        return self.filter_by_field(queryset, value, 'shopping_cart')


class IngredientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name='name',
                                     lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ['name']
