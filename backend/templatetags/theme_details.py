from django import template
# import os
import glob
import json

register = template.Library()


def theme_details(name):
    theme = glob.glob1(dirname=f'rn-themes/{name}/', pattern='theme.json')
    if theme is not []:
        with open(f'rn-themes/{name}/theme.json', 'r') as js:
            js = js.read()
        theme = json.loads(js)
    else:
        theme = None
    return theme

# os.chdir('../')
# print(os.getcwd())
# t = theme_details('radonone')
# print(t['RN_THEME']['NAME'])


@register.filter(name='theme_name')
def theme_name(name):
    try:
        theme = theme_details(name)['RN_THEME']['NAME']
    except:
        theme = name
    return theme


@register.filter(name='theme_description')
def theme_description(name):
    try:
        theme = theme_details(name)['RN_THEME']['DESCRIPTION']
    except:
        theme = 'No description found !'
    return theme


@register.filter(name='theme_short_description')
def theme_short_description(name):
    try:
        theme = theme_details(name)['RN_THEME']['DESCRIPTION'][:50]+'...'
    except:
        theme = 'No description found !'
    return theme


@register.filter(name='theme_image')
def theme_image(name):
    try:
        theme = f'{name}/static/img/screenshot.png'
    except:
        theme = 'No image found !'
    return theme


@register.filter(name='theme_author')
def theme_author(name):
    try:
        theme = theme_details(name)['RN_THEME']['AUTHOR']
    except:
        theme = 'No author found !'
    return theme


@register.filter(name='theme_author_uri')
def theme_author_uri(name):
    try:
        theme = theme_details(name)['RN_THEME']['AUTHOR_URI']
    except:
        theme = '#'
    return theme


@register.filter(name='theme_version')
def theme_version(name):
    try:
        theme = theme_details(name)['RN_THEME']['VERSION']
    except:
        theme = 'No version code found !'
    return theme


@register.filter(name='theme_license')
def theme_license(name):
    try:
        theme = theme_details(name)['RN_THEME']['LICENSE']
    except:
        theme = 'No license found !'
    return theme


@register.filter(name='theme_license_uri')
def theme_license_uri(name):
    try:
        theme = theme_details(name)['RN_THEME']['LICENSE_URI']
    except:
        theme = '#'
    return theme
