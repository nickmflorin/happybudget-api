import mock

from greenbudget.app.io.serializers import ImageFileSerializer


def test_image_file_serializer_local(test_image_file):
    image_file = test_image_file("test.jpeg", "jpeg")
    serializer = ImageFileSerializer(image_file)
    assert serializer.data == {
        'size': 823,
        'width': 100,
        'height': 100,
        'extension': 'jpeg'
    }


def test_image_file_serializer_local_not_found(test_image_file):
    image_file = test_image_file("test.jpeg", "jpeg")
    image_file.name = "/hoopla/test.jpg"
    serializer = ImageFileSerializer(image_file)
    assert serializer.data == {
        'size': 823,
        'width': 100,
        'height': 100,
        'extension': None
    }


def test_image_file_serializer_remote(test_image_file):
    image_file = test_image_file("test.jpeg", "jpeg")

    # The only difference when the file is stored in S3 is that we do not use
    # imghr to determine the extension based on where the file is saved locally.
    # So all we have to do is mock the `using_s3_storage` function to return
    # True and the extension will be determined based on the filepath, not the
    # actually locally saved file.
    with mock.patch('greenbudget.app.io.serializers.using_s3_storage') as m:
        m.return_value = True
        serializer = ImageFileSerializer(image_file)
        assert serializer.data == {
            'size': 823,
            'width': 100,
            'height': 100,
            'extension': 'jpeg'
        }
