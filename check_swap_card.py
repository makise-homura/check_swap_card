#!/usr/bin/env python

from sys import argv, stdout
from glob import glob
from psd_tools import PSDImage, constants
from io import BytesIO
from PIL import ImageCms
from print_color import print
from colorama import just_fix_windows_console
just_fix_windows_console()

skip_ok = False
if '-s' in argv:
    argv.remove('-s')
    skip_ok = True

c_ok = u'\u2714' if "UTF-8" in stdout.encoding else '√'
c_err = u'\u2716' if "UTF-8" in stdout.encoding else 'x'

def ok(s):
    if not skip_ok:
        print(s, tag=c_ok, tag_color='green', tag_format='bold')

def err(noerr, s):
    if skip_ok and noerr:
        print()
    print(s, tag=c_err, tag_color='red', tag_format='bold')

def hdr(s):
    if skip_ok:
        print(s, color='white', format='bold', end='')
    else:
        print(s, color='white', format='bold')

def allok(noerr):
    if skip_ok and noerr:
        print(' OK', color='green', format='bold')
    else:
        print()

test_w = 791
test_h = 1087
test_r = 300
test_cm = 'CMYK'
test_icc = 'Coated FOGRA39 (ISO 12647-2:2004)'

for arg in argv[1:]:
    for psdfile in glob(arg):
        hdr(f'Проверяю файл {psdfile}:')
        noerr = True
        psd = PSDImage.open(psdfile)

        if psd.width == test_w and psd.height == test_h:
            ok(f'Размер изображения {test_w}x{test_h}.')
        else:
            err(noerr, f'Размер изображения {psd.width}x{psd.height} вместо {test_w}x{test_h}.')
            noerr = False

        if psd.color_mode.name == test_cm:
            ok(f'Цветовое пространство: {test_cm}')
        else:
            err(noerr, f'Цветовое пространство: {psd.color_mode.name} вместо {test_cm}.')
            noerr = False

        profile_data = psd.image_resources.get_data(constants.Resource.ICC_PROFILE)
        if profile_data == None:
            err(noerr, f'Цветовой профиль изображения не назначен.')
            noerr = False
        else:
            profile_io = BytesIO(profile_data)
            profile_obj = ImageCms.ImageCmsProfile(profile_io)
            profile = ImageCms.getProfileDescription(profile_obj).rstrip()
            if profile == test_icc:
                ok(f'Цветовой профиль изображения {profile}.')
            else:
                err(noerr, f'Цветовой профиль изображения: {profile} вместо {test_icc}.')
                noerr = False

        resolution_info = psd.image_resources.get_data(constants.Resource.RESOLUTION_INFO)
        res_x = resolution_info.horizontal / 0x10000
        res_y = resolution_info.vertical / 0x10000
        if res_x == test_r and res_y == test_r:
            ok(f'Разрешение изображения {test_r} DPI.')
        else:
            err(noerr, f'Разрешение изображения {res_x}x{res_y} вместо {test_r}x{test_r} DPI.')
            noerr = False
    
        if len(psd) == 0:
            err(noerr, f'В файле нет слоёв, не являющихся фоном.')
            noerr = False
        elif len(psd) == 1:
            if psd[0].is_visible():
                if psd[0].kind == 'pixel':
                    ok(f'В документе есть только один видимый растеризованный слой {psd[0].name}.')
                else:
                    err(noerr, f'Единственный слой {psd[0].name} не растеризован.')
                    noerr = False
            else:
                err(noerr, f'Единственный слой {psd[0].name} невидим.')
                noerr = False
        else:
            err(noerr, f'В документе более одного слоя: {", ".join((layer.name for layer in psd))}')
            noerr = False

        allok(noerr)