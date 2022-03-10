import koji


def get_koji_session(config):

    session = koji.ClientSession(config.koji_host)

    return session
