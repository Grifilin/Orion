from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock, mainthread
from jnius import autoclass, PythonJavaClass, java_method
from android.runnable import run_on_ui_thread
from downloads import DownloadTask, needs_mobile_permission
from ui.dialogs import ask_mobile_download

PythonActivity = autoclass('org.kivy.android.PythonActivity')
WebView = autoclass('android.webkit.WebView')
WebViewClient = autoclass('android.webkit.WebViewClient')
DownloadListener = autoclass('android.webkit.DownloadListener')
ViewGroup = autoclass('android.view.ViewGroup')

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
    def build(self):
        root = BoxLayout(orientation='vertical')
        top = BoxLayout(size_hint_y=None, height=48, spacing=4)
        self.addr = TextInput(text='https://ya.ru', multiline=False)
        go = Button(text='->', size_hint_x=None, width=56)
        go.bind(on_release=lambda *_: self.load(self.addr.text))
        top.add_widget(self.addr)
        top.add_widget(go)
        root.add_widget(top)
        root.add_widget(BoxLayout())
        self.progress = ProgressBar(max=100, size_hint_y=None, height=6)
        root.add_widget(self.progress)
        Clock.schedule_once(lambda dt: self._attach_webview(), 0)
        return root

    @run_on_ui_thread
    def _attach_webview(self):
        activity = PythonActivity.mActivity
        self.webview = WebView(activity)
        self.webview.getSettings().setJavaScriptEnabled(True)
        self.webview.getSettings().setDomStorageEnabled(True)
        self.webview.setWebViewClient(WebViewClient())
        self.webview.setDownloadListener(PyDownloadListener(self))
        self.webview.loadUrl('https://ya.ru')
        content = activity.findViewById(activity.getResources().getIdentifier('content', 'id', activity.getPackageName()))
        content.addView(self.webview, ViewGroup.LayoutParams(-1, -1))

    def load(self, url):
        if not url.startswith('http'): url = 'https://' + url
        self.webview.loadUrl(url)

    @mainthread
    def handle_download(self, url, mimetype, content_length):
        size = int(content_length)
        if needs_mobile_permission(size):
            ask_mobile_download(size, on_allow=lambda: self._start_download(url, mimetype), on_deny=lambda: None)
        else:
            self._start_download(url, mimetype)

    def _start_download(self, url, mimetype):
        fname = url.split('/')[-1].split('?')[0] or 'download.bin'
        dest = f'/sdcard/Download/{fname}'
        task = DownloadTask(url, dest, on_progress=self._on_progress, on_done=lambda p: print('OK', p), on_error=lambda e: print('Err', e))
        import threading
        threading.Thread(target=task.start, daemon=True).start()

    @mainthread
    def _on_progress(self, done, total):
        if total: self.progress.value = 100 * done / total

if __name__ == '__main__':
    BrowserApp().run()
