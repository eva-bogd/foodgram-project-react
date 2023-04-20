import django_filters
from django_filters import rest_framework as filters

from recipes.models import Recipe, Ingredient


class RecipeFilter(django_filters.FilterSet):
    tags = filters.CharFilter(field_name='tags__slug',
                              lookup_expr='exact')
    author = filters.CharFilter(field_name='author__username',
                                lookup_expr='exact')
    is_favorited = django_filters.BooleanFilter(
        method='filter_favorited')
    is_in_shopping_cart = django_filters.BooleanFilter(
        method='filter_shopping_cart')

    class Meta():
        model = Recipe
        fields = ['is_favorited', 'author', 'is_in_shopping_cart', 'tags']

    def filter_favorited(self, queryset, name, value):
        user = self.request.user
        if user.is_anonymous:
            return queryset.none()
        if value:
            return queryset.filter(favorite__user=user)
        else:
            return queryset.exclude(favorite__user=user)

    def filter_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if user.is_anonymous:
            return queryset.none()
        if value:
            return queryset.filter(shopping_cart__user=user)
        else:
            return queryset.exclude(shopping_cart__user=user)


class IngredientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name='name',
                                     lookup_expr='istartswith')
    name__icontains = django_filters.CharFilter(field_name='name',
                                                lookup_expr='icontains')

    # name - это имя поля, по которому нужно фильтровать,
    # а icontains - это оператор фильтрации, который говорит Django,
    #  что необходимо искать строки, содержащие данное значение
    # (в данном случае, частичное совпадение в начале строки),
    # без учета регистра.
    # __ - это специальный оператор, который используется в Django
    # для указания различных параметров фильтрации.
    # в данном случае, он используется для указания оператора фильтрации
    # (lookup_expr).

    class Meta:
        model = Ingredient
        fields = ['name']
