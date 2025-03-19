import unittest
from src.converter import ImageConverter

class TestImageConverter(unittest.TestCase):

    def setUp(self):
        self.converter = ImageConverter()

    def test_convert_image_valid(self):
        input_path = 'resources/sample_images/test_image.jpg'
        output_path = 'resources/sample_images/test_image.png'
        output_format = 'png'
        result = self.converter.convert_image(input_path, output_path, output_format)
        self.assertTrue(result)

    def test_convert_image_invalid_format(self):
        input_path = 'resources/sample_images/test_image.jpg'
        output_path = 'resources/sample_images/test_image.invalid'
        output_format = 'invalid_format'
        with self.assertRaises(ValueError):
            self.converter.convert_image(input_path, output_path, output_format)

    def test_convert_image_nonexistent_file(self):
        input_path = 'resources/sample_images/nonexistent.jpg'
        output_path = 'resources/sample_images/test_image.png'
        output_format = 'png'
        with self.assertRaises(FileNotFoundError):
            self.converter.convert_image(input_path, output_path, output_format)

if __name__ == '__main__':
    unittest.main()