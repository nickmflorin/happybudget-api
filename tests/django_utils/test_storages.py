import pytest

from greenbudget.lib.django_utils.storages import (
    get_image_filename_extension,
    get_filename_extension,
    get_image_filename,
    get_filename,
    FileNameError,
    FileExtensionError,
    MissingFileExtension,
    UnsupportedImageExtension
)


@pytest.mark.parametrize('filename,expected,strict', [
    ('testfile.jpg', 'jpg', False),
    ('testfile.docx', 'docx', False),
    ('testfile.pdf', 'pdf', False),
    ('testfile', MissingFileExtension, True),
    ('testimage.', MissingFileExtension, True),
    ('test.image.gif', FileNameError, True),
    ('testfile', None, False),
    ('testfile.', None, False),
    ('testfile.gif', 'gif', False),
])
def test_get_filename_extension(filename, expected, strict):
    if isinstance(expected, type):
        with pytest.raises(expected):
            get_filename_extension(filename, strict=strict)
    else:
        assert get_filename_extension(filename, strict=strict) == expected


@pytest.mark.parametrize('filename,expected,strict', [
    ('testimage.jpg', 'jpg', False),
    ('testimage.png', 'png', False),
    ('testimage.jpeg', 'jpeg', False),
    ('testimage', MissingFileExtension, True),
    ('testimage.', MissingFileExtension, True),
    ('testimage.gif', UnsupportedImageExtension, True),
    ('test.image.gif', FileNameError, True),
    ('testimage', None, False),
    ('testimage.', None, False),
    ('testimage.gif', None, False),
])
def test_get_image_filename_extension(filename, expected, strict):
    if isinstance(expected, type):
        with pytest.raises(expected):
            get_image_filename_extension(filename, strict=strict)
    else:
        assert get_image_filename_extension(filename, strict=strict) == expected


@pytest.mark.parametrize('filename,expected,new_name', [
    ('testimage.jpg', 'newtestimage.jpg', 'newtestimage'),
    ('testimage.png', 'newtestimage.png', 'newtestimage'),
    ('testimage.jpg', FileExtensionError, 'newtestimage.png'),
    ('testimage.jpg.jpg', FileNameError, 'newtestimage.png'),
    ('testimage', MissingFileExtension, None),
    ('testimage', MissingFileExtension, 'newtestimage.png'),
    ('testimage.', MissingFileExtension, None),
    ('testimage.gif', UnsupportedImageExtension, None),
])
def test_get_image_filename(filename, expected, new_name):
    if isinstance(expected, type):
        with pytest.raises(expected):
            get_image_filename(filename, new_filename=new_name)
    else:
        assert get_image_filename(filename, new_filename=new_name) == expected


@pytest.mark.parametrize('filename,expected,new_name', [
    ('testfile.pdf', 'newtestfile.pdf', 'newtestfile'),
    ('testfile.png', 'newtestfile.png', 'newtestfile'),
    ('testfile.docx', FileExtensionError, 'newtestfile.pdf'),
    ('testfile', MissingFileExtension, None),
    ('testfile', MissingFileExtension, 'newtestfile.png'),
    ('testfile.', MissingFileExtension, None),
    ('testfile.gif', 'testfile.gif', None),
])
def test_get_filename(filename, expected, new_name):
    if isinstance(expected, type):
        with pytest.raises(expected):
            get_filename(filename, new_filename=new_name)
    else:
        assert get_filename(filename, new_filename=new_name) == expected
