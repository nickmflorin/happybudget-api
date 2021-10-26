from rest_framework import response, generics

from .serializers import TempImageSerializer, TempFileSerializer


class TempUploadImageView(generics.GenericAPIView):
    serializer_class = TempImageSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        file_url = serializer.save()
        return response.Response({'fileUrl': file_url})


class TempUploadFileView(generics.GenericAPIView):
    serializer_class = TempFileSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        file_url = serializer.save()
        return response.Response({'fileUrl': file_url})
