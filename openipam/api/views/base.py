from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status


class UserAuthenticated(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        data = {
            "detail": "User is authenticated",
            "username": request.user.username,
            "is_superuser": request.user.is_superuser,
            "is_ipamadmin": request.user.is_ipamadmin,
        }
        return Response(data, status=status.HTTP_200_OK)
