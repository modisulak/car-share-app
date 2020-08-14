import bluetooth


class BluetoothService:
    @staticmethod
    def search():
        '''
        Search for bluetooth devices using bluetooth module

        :return: a list of discovered bluetooth devices

        :rtype: list(tuple(str(`bd_addr`), str(`device_name`)))
        '''
        return bluetooth.discover_devices(lookup_names=True)


class BluetoothSearch(BluetoothService):
    def __init__(self, searchlist_callback, matchfound_callback):
        '''
        :param searchlist_callback: returns a list of bd_addrs

        :param matchfound_callback: used when matching bd_addr found by search

        Searches for bluetooth devices matching those returned by
        searchlist_callback until the list is empty
        '''
        self.searchlist_callback = searchlist_callback
        self.matchfound_callback = matchfound_callback

    def run(self):
        searchlist = self.searchlist_callback()
        while searchlist:
            # search for bluetooth devices
            # find matching addresses, if found, use matchfound_callback on them
            results = [d[0] for d in self.search()]
            matches = list(set(results) & set(searchlist))
            for match in matches:
                self.matchfound_callback(match)
            searchlist = self.searchlist_callback()
