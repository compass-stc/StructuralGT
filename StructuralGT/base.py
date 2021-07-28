def Q_img(name):
    if (name.endswith('.tiff') or 
        name.endswith('.tif') or
        name.endswith('.jpg') or
        name.endswith('.jpeg') or
        name.endswith('.png') or
        name.endswith('.gif')):
        return True
    else:
        return False
