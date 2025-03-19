def check_file_exists(file_path):
    import os
    return os.path.isfile(file_path)

def get_supported_formats():
    return ['jpg', 'png', 'bmp', 'tiff', 'gif', 'webp']