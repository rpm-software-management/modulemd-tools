import koji


def mbs_valid(mbs_id):
    return mbs_id.isdigit()


def get_koji_session(config):

    session = koji.ClientSession(config.koji_host)

    return session
