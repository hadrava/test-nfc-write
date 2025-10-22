class TagCreator:
    def __init__(self, mdb_path):
        self._mdb_path = mdb_path

    def create_tag(self, spool_info):
        return b'\x043dtag.org/s/' + spool_info.spool_unique_id.encode();
