import unittest
from src.utils.file_utils import check_file_exists, get_supported_formats

class TestFileUtils(unittest.TestCase):

    def test_check_file_exists(self):
        # Test with a valid file path
        self.assertTrue(check_file_exists('resources/sample_images/sample_image.jpg'))
        
        # Test with an invalid file path
        self.assertFalse(check_file_exists('invalid/path/to/file.jpg'))

    def test_get_supported_formats(self):
        # Test if the supported formats are returned correctly
        expected_formats = ['jpg', 'png', 'tiff', 'bmp', 'gif']
        self.assertEqual(get_supported_formats(), expected_formats)

if __name__ == '__main__':
    unittest.main()