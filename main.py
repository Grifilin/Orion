from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.progressbar import ProgressBar
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.clock import mainthread
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from jnius import autoclass, PythonJavaClass, java_method
from android.runnable import run_on_ui_thread
from downloads import DownloadTask, needs_mobile_permission
from ui.dialogs import ask_mobile_download

PythonActivity = autoclass('org.kivy.android.PythonActivity')
WebView = autoclass('android.webkit.WebView')
WebViewClient = autoclass('android.webkit.WebViewClient')
DownloadListener = autoclass('android.webkit.DownloadListener')
ViewGroup = autoclass('android.view.ViewGroup')
CookieManager = autoclass('android.webkit.CookieManager')
LayoutParams = autoclass('android.view.ViewGroup$LayoutParams')

LIGHT_THEME = {'bg': get_color_from_hex('#F2F2F7'), 'text': get_color_from_hex('#000000'), 'input': get_color_from_hex('#FFFFFF'), 'btn': get_color_from_hex('#E5E5EA')}
DARK_THEME = {'bg': get_color_from_hex('#1C1C1E'), 'text': get_color_from_hex('#FFFFFF'), 'input': get_color_from_hex('#2C2C2E'), 'btn': get_color_from_hex('#3A3A3C')}

class PyDownloadListener(PythonJavaClass):
    __javainterfaces__ = ['android/webkit/DownloadListener']
    __javacontext__ = 'app'
    def __init__(self, app):
        super().__init__()
        self.app = app
    @java_method('(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;J)V')
    def onDownloadStart(self, url, user_agent, content_disposition, mimetype, content_length):
        self.app.handle_download(url, mimetype, content_length)

class BrowserApp(App):
    current_theme = LIGHT_THEME
    home_url = 'https://ya.ru'

    def build(self):
        Window.clearcolor = self.current_theme['bg']
        self.root_layout = BoxLayout(orientation='vertical')
        
        # Тулбар
        self.toolbar = BoxLayout(size_hint_y=None, height=56, spacing=4, padding=4)
        self.btn_back = Button(text='<', size_hint_x=None, width=40, background_color=self.current_theme['btn'])
        self.btn_forward = Button(text='>', size_hint_x=None, width=40, background_color=self.current_theme['btn'])
        self.btn_reload = Button(text='⟳', size_hint_x=None, width=40, background_color=self.current_theme['btn'])
        self.addr = TextInput(text=self.home_url, multiline=False, background_color=self.current_theme['input'], foreground_color=self.current_theme['text'])
        self.btn_menu = Button(text='≡', size_hint_x=None, width=40, background_color=self.current_theme['btn'])
        
        self.toolbar.add_widget(self.btn_back)
        self.toolbar.add_widget(self.btn_forward)
        self.toolbar.add_widget(self.btn_reload)
        self.toolbar.add_widget(self.addr)
        self.toolbar.add_widget(self.btn_menu)
        self.root_layout.add_widget(self.toolbar)
        
        self.progress = ProgressBar(max=100, size_hint_y=None, height=4)
        self.root_layout.add_widget(self.progress)
        self.root_layout.add_widget(BoxLayout()) # Spacer для WebView
        
        self.btn_back.bind(on_release=lambda *_: self.webview.goBack())
        self.btn_forward.bind(on_release=lambda *_: self.webview.goForward())
        self.btn_reload.bind(on_release=lambda *_: self.webview.reload())
        self.addr.bind(on_text_validate=self.load_url)
        self.btn_menu.bind(on_release=lambda *_: self.show_menu())
        
        self._attach_webview()
        return self.root_layout

    @run_on_ui_thread
    def _attach_webview(self):
        activity = PythonActivity.mActivity
        self.webview = WebView(activity)
        self.webview.getSettings().setJavaScriptEnabled(True)
        self.webview.getSettings().setDomStorageEnabled(True)
        self.webview.setDownloadListener(PyDownloadListener(self))
        
        # Отслеживание смены URL
        class Client(WebViewClient):
            @java_method('(Landroid/webkit/WebView;Ljava/lang/String;)V')
            def onPageStarted(self, view, url):
                self.app.update_url(url)
        client = Client()
        client.app = self
        self.webview.setWebViewClient(client)
        self.webview.loadUrl(self.home_url)
        
        # Добавляем WebView на экран
        content = activity.findViewById(activity.getResources().getIdentifier('content', 'id', activity.getPackageName()))
        params = LayoutParams(-1, -1)
        params.topMargin = int(56 * activity.getResources().getDisplayMetrics().density) # Отступ сверху для тулбара Kivy
        content.addView(self.webview, params)

    @mainthread
    def update_url(self, url):
        self.addr.text = url

    def load_url(self, instance):
        url = self.addr.text.strip()
        if not url.startswith('http'):
            url = 'https://' + url if '.' in url else 'https://yandex.ru/search/?text=' + url
        self.addr.text = url
        self.webview.loadUrl(url)

    def show_menu(self):
        layout = BoxLayout(orientation='vertical', padding=16, spacing=12)
        btn_theme = Button(text='Сменить тему', size_hint_y=None, height=48)
        btn_theme.bind(on_release=lambda *_: self.toggle_theme())
        btn_clear = Button(text='Очистить кэш и Cookies', size_hint_y=None, height=48)
        btn_clear.bind(on_release=lambda *_: self.clear_data())
        layout.add_widget(Label(text='Меню', color=self.current_theme['text']))
        layout.add_widget(btn_theme)
        layout.add_widget(btn_clear)
        Popup(title='Настройки', content=layout, size_hint=(0.8, 0.5)).open()

    def toggle_theme(self):
        self.current_theme = DARK_THEME if self.current_theme == LIGHT_THEME else LIGHT_THEME
        Window.clearcolor = self.current_theme['bg']
        self.addr.background_color = self.current_theme['input']
        self.addr.foreground_color = self.current_theme['text']
        for btn in [self.btn_back, self.btn_forward, self.btn_reload, self.btn_menu]:
            btn.background_color = self.current_theme['btn']

    @mainthread
    def clear_data(self):
        CookieManager.getInstance().removeAllCookies(None)
        self.webview.clearCache(True)
        self.webview.clearHistory()

    @mainthread
    def handle_download(self, url, mimetype, content_length):
        size = int(content_length)
        if needs_mobile_permission(size):
            ask_mobile_download(size, on_allow=lambda: self._start_download(url), on_deny=lambda: None)
        else:
            self._start_download(url)

    def _start_download(self, url):
        fname = url.split('/')[-1].split('?')[0] or 'download.bin'
        task = DownloadTask(url, f'/sdcard/Download/{fname}', on_progress=self._on_progress)
        import threading
        threading.Thread(target=task.start, daemon=True).start()

    @mainthread
    def _on_progress(self, done, total):
        if total: self.progress.value = 100 * done / total

if __name__ == '__main__':
    BrowserApp().run()
