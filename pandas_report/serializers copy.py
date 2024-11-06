from rest_framework import serializers

class RevenueReportSerializer(serializers.Serializer):
    property_name = serializers.CharField()
    Total = serializers.DecimalField(max_digits=10, decimal_places=2)
    # Ajoutez des champs supplémentaires pour chaque mois si nécessaire
    # Par exemple :
    # Janvier_2024 = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    # Février_2024 = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    # ...

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ajoutez dynamiquement des champs pour chaque mois présent dans les données
        if 'data' in kwargs:
            for key in kwargs['data'][0].keys():
                if key not in ['property_name', 'Total']:
                    self.fields[key] = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)

                    

class RevenueReportSerializer(serializers.Serializer):
    property_name = serializers.CharField()
    revenues = serializers.DictField(child=serializers.DecimalField(max_digits=10, decimal_places=2))
    total = serializers.DecimalField(max_digits=10, decimal_places=2)

    
## 
class RevenuesSerializer(serializers.Serializer):
    def to_representation(self, instance):
        return {key: float(value) for key, value in instance.items()}

class PropertyRevenueSerializer(serializers.Serializer):
    property_name = serializers.CharField()
    revenues = RevenuesSerializer()
    total = serializers.FloatField()

class RevenueReportSerializer(serializers.Serializer):
    dataset = PropertyRevenueSerializer(many=True)