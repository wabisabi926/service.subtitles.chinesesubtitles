from providers.subhd import SubHDAgent
from providers.zimuku import ZimukuAgent


def build_agents(temp_dir, logger, unpacker):
    return {
        "subhd": SubHDAgent(None, temp_dir, logger, unpacker),
        "zimuku": ZimukuAgent(None, temp_dir, logger, unpacker),
    }
