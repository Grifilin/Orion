from jnius import autoclass
Context = autoclass('android.content.Context')
ConnectivityManager = autoclass('android.net.ConnectivityManager')
NetworkCapabilities = autoclass('android.net.NetworkCapabilities')
PythonActivity = autoclass('org.kivy.android.PythonActivity')

def get_network_type():
    activity = PythonActivity.mActivity
    cm = activity.getSystemService(Context.CONNECTIVITY_SERVICE)
    if cm is None: return 'none'
    network = cm.getActiveNetwork()
    if network is None: return 'none'
    caps = cm.getNetworkCapabilities(network)
    if caps is None: return 'none'
    if caps.hasTransport(NetworkCapabilities.TRANSPORT_WIFI): return 'wifi'
    if caps.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR): return 'cellular'
    return 'unknown'

def is_metered():
    return get_network_type() == 'cellular'
