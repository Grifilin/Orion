from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button

def human_size(n):
    for unit in ['Б', 'КБ', 'МБ', 'ГБ']:
        if n < 1024: return f'{n:.1f} {unit}'
        n /= 1024
    return f'{n:.1f} ТБ'

def ask_mobile_download(size_bytes, on_allow, on_deny):
    box = BoxLayout(orientation='vertical', padding=16, spacing=12)
    box.add_widget(Label(text=f'Вы подключены к мобильному интернету.\n\nРазмер файла: {human_size(size_bytes)}\n\nПродолжить загрузку?', halign='center'))
    row = BoxLayout(size_hint_y=None, height=48, spacing=12)
    btn_no = Button(text='Отмена')
    btn_yes = Button(text='Продолжить')
    row.add_widget(btn_no)
    row.add_widget(btn_yes)
    box.add_widget(row)
    popup = Popup(title='Мобильный трафик', content=box, size_hint=(0.9, 0.5), auto_dismiss=False)
    btn_no.bind(on_release=lambda *_: (popup.dismiss(), on_deny()))
    btn_yes.bind(on_release=lambda *_: (popup.dismiss(), on_allow()))
    popup.open()
