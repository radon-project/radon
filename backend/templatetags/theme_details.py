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
        theme = 'Broken Theme'
    return theme
