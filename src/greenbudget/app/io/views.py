from rest_framework import response, generics

from .serializers import TempImageSerializer, TempFileSerializer


class TempUploadView(generics.GenericAPIView):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        file_url = serializer.save()
        return response.Response({'fileUrl': file_url})


class TempUploadImageView(TempUploadView):
    serializer_class = TempImageSerializer


class TempUploadFileView(TempUploadView):
    serializer_class = TempFileSerializer
