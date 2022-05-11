class Config():

    def __init__(self, koji_host, koji_storage_host, mbs_host, arch, result_dir):
        self.koji_host = koji_host
        self.koji_storage_host = koji_storage_host
        self.mbs_host = mbs_host
        self.arch = arch
        self.result_dir = result_dir
