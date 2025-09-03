from rest_framework import serializers
from .models import MutualFundHouse, MutualFundScheme, MutualFundNAV, MutualFundPerformance
from apps.core.models import Category

class CategorySerializer(serializers.StringRelatedField):
    pass

class MutualFundHouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = MutualFundHouse
        fields = ['name']

class MutualFundNAVSerializer(serializers.ModelSerializer):
    class Meta:
        model = MutualFundNAV
        fields = ['date', 'nav']

class MutualFundPerformanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = MutualFundPerformance
        fields = ['return_1y', 'return_3y', 'return_5y', 'ytd_return']

class MutualFundSchemeDetailSerializer(serializers.ModelSerializer):
    fund_house = MutualFundHouseSerializer(read_only=True)
    navs = MutualFundNAVSerializer(many=True, read_only=True)
    categories = CategorySerializer(many=True, read_only=True)
    performance = MutualFundPerformanceSerializer(read_only=True)

    class Meta:
        model = MutualFundScheme
        fields = ['scheme_code', 'name', 'isin', 'fund_house', 'categories', 'navs', 'performance']

class MutualFundSchemeListSerializer(serializers.ModelSerializer):
    fund_house = serializers.StringRelatedField()
    categories = CategorySerializer(many=True, read_only=True)

    class Meta:
        model = MutualFundScheme
        fields = ['scheme_code', 'name', 'fund_house', 'categories']
