
# LocalScripts helper for Cloudbase-Init to handle NETWORK_CONFIG
# (uppercase) on a NoCloud config-drive. As currrently IONOS/CAPI PROXMOX
# uses go-diskfs.go in inject.go to apply network-config but gets renamed to NETWORK_CONFIG
import sys

from cloudbaseinit.metadata import factory as meta_factory
from cloudbaseinit.metadata.services import nocloudservice
from cloudbaseinit.plugins.common import networkconfig
from cloudbaseinit.utils import serialization
from cloudbaseinit import exception as cb_exception

try:
    from oslo_log import log as oslo_logging
    LOG = oslo_logging.getLogger(__name__)
except Exception:
    import logging
    logging.basicConfig(level=logging.INFO)
    LOG = logging.getLogger(__name__)


networkdata_file = "NETWORK_CONFIG"


def main():
    # Get the currently-selected metadata service (from config)
    service = meta_factory.get_metadata_service()

    # We only care if it's NoCloudConfigDriveService, as cloudbase config is set Nocloud
    if not isinstance(service, nocloudservice.NoCloudConfigDriveService):
        LOG.info("Active metadata service is not NoCloudConfigDriveService; "
                 "skipping networkdata_file handling")
        return 0

    # Try to read networkdata_file from the config drive cache
    try:
        raw_network_data = service._get_cache_data(
            networkdata_file,
            decode=True,
        )
    except cb_exception.NotExistingMetadataException:
        LOG.info("networkdata_file not found in NoCloud cache")
        return 0
    except Exception:
        LOG.exception("Error while reading networkdata_file via _get_cache_data")
        return 0

    # Parse YAML / JSON to a dict
    try:
        network_data = serialization.parse_json_yaml(raw_network_data)
    except serialization.YamlParserConfigError:
        LOG.exception("networkdata_file could not be parsed as YAML / JSON")
        return 0

    if not isinstance(network_data, dict):
        LOG.error("networkdata_file parsed into %r, expected dict",
                  type(network_data))
        return 0

    # Use Cloudbase-Init's official NoCloud parser
    network_details = NoCloudNetworkConfigParser.parse(network_data)
    if not network_details:
        LOG.warning("NoCloudNetworkConfigV1Parser returned empty details")
        return 0

    # Apply via the standard NetworkConfigPlugin
    plugin = networkconfig.NetworkConfigPlugin()
    if hasattr(plugin, "_process_network_details_v2"):
        LOG.info("Applying static network configuration from networkdata_file")
        plugin._process_network_details_v2(network_details)
    else:
        LOG.error("NetworkConfigPlugin has no _process_network_details_v2; "
                  "cannot apply networkdata_file")

    return 0


if __name__ == "__main__":
    sys.exit(main())
