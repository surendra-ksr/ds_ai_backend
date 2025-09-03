from rest_framework import serializers
from .models import MutualFundHouse, MutualFundScheme, MutualFundNAV

class MutualFundHouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = MutualFundHouse
        fields = ['name']

class MutualFundNAVSerializer(serializers.ModelSerializer):
    class Meta:
        model = MutualFundNAV
        fields = ['date', 'nav']

class MutualFundSchemeDetailSerializer(serializers.ModelSerializer):
    fund_house = MutualFundHouseSerializer(read_only=True)
    navs = MutualFundNAVSerializer(many=True, read_only=True)

    class Meta:
        model = MutualFundScheme
        fields = ['scheme_code', 'name', 'category', 'isin', 'fund_house', 'navs']

class MutualFundSchemeListSerializer(serializers.ModelSerializer):
    fund_house = serializers.StringRelatedField()

    class Meta:
        model = MutualFundScheme
        fields = ['scheme_code', 'name', 'category', 'fund_house']
