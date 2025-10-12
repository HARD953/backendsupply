# views.py
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.models import User
from .serializers3 import UserProfileDetailSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_user_profile(request):
    """
    Endpoint pour récupérer les informations de l'utilisateur connecté
    """
    try:
        user = request.user
        serializer = UserProfileDetailSerializer(user)
        return Response(serializer.data)
    
    except User.DoesNotExist:
        return Response(
            {"error": "Utilisateur non trouvé"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"error": f"Erreur serveur: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )