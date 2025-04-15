from rest_framework import generics
# from rest_framework.response import Response
# from rest_framework import status
# from rest_framework.views import APIView
from .models import Permissao
from .serializers import PermissaoSerializer

class PermissaoCreateView(generics.CreateAPIView):

 

    queryset = Permissao.objects.all()
 

    serializer_class = PermissaoSerializer

# class PermissaoCreateView(APIView):
#     def post(self, request, *args, **kwargs):
#         serializer = PermissaoSerializer(data=request.data)
#         if serializer.is_valid():
#             permissao = serializer.save()
#             return Response({
#                 "id": permissao.id,  # Retorna o ID da permissão criada
#                 "nome": permissao.nome
#             }, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)