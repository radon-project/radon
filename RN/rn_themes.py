from core.models import RN_Themes
import os


# Private functions for internal work only

def _name_decoder(name: str):
    name = name.lower().strip().replace(' ', '')
    return name


# Global functions for developers

def rn_active_theme():
    '''To get active theme.'''
    theme = RN_Themes.objects.get(is_active=True)
    return theme


def rn_all_theme():
    '''To get all theme.'''
    theme = RN_Themes.objects.all()
    return theme


def rn_theme_get():
    theme = rn_active_theme().name
    name = _name_decoder(theme)
    location = os.path.join('core/themes/', name)
    return location
