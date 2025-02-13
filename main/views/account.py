from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.contrib.auth.models import update_last_login
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from main.serializers.account import PasswordUpdateSerializer


class PasswordUpdateView(APIView):
    """로그인된 사용자가 비밀번호 변경"""
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="비밀번호 변경",
        operation_description="현재 비밀번호를 확인한 후 새 비밀번호로 변경합니다.",
        request_body=PasswordUpdateSerializer,
        responses={
            200: openapi.Response(description="비밀번호 변경 성공", schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={"message": openapi.Schema(type=openapi.TYPE_STRING)}
            )),
            400: openapi.Response(description="비밀번호 변경 실패", schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={"message": openapi.Schema(type=openapi.TYPE_STRING)}
            )),
        }
    )
    def post(self, request):
        user = request.user
        serializer = PasswordUpdateSerializer(data=request.data, context={'user': user})

        if serializer.is_valid():
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            update_last_login(None, user)
            return Response({"message": "비밀번호가 성공적으로 변경되었습니다."}, status=status.HTTP_200_OK)

        return Response({"message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
