# Copyright 2026 The Kubernetes Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Apply Proxmox NoCloud network data staged as NETWORK_CONFIG."""

import logging
import os
import sys

from cloudbaseinit.plugins.common import networkconfig
from cloudbaseinit.metadata.services.nocloudservice import NoCloudNetworkConfigParser
from cloudbaseinit.utils import serialization

try:
    from oslo_log import log as oslo_logging

    LOG = oslo_logging.getLogger(__name__)
except Exception:  # pragma: no cover - fallback when oslo logging is unavailable
    logging.basicConfig(level=logging.INFO)
    LOG = logging.getLogger(__name__)


NETWORK_DATA_PATH = r"D:\NETWORK_CONFIG"


def main():
    try:
        if not os.path.exists(NETWORK_DATA_PATH):
            LOG.info("No Proxmox network data found at %s", NETWORK_DATA_PATH)
            return 0

        with open(NETWORK_DATA_PATH, "r", encoding="utf-8") as network_data_file:
            raw_network_data = network_data_file.read()
    except Exception:
        LOG.exception("Failed to load Proxmox network data from %s", NETWORK_DATA_PATH)
        return 0

    try:
        network_data = serialization.parse_json_yaml(raw_network_data)
    except serialization.YamlParserConfigError:
        LOG.exception("Proxmox network data could not be parsed as YAML or JSON")
        return 0

    if not isinstance(network_data, dict):
        LOG.error("Proxmox network data parsed into %r, expected dict", type(network_data))
        return 0

    network_details = NoCloudNetworkConfigParser.parse(network_data)
    if not network_details:
        LOG.warning("NoCloud network parser returned no interfaces")
        return 0

    plugin = networkconfig.NetworkConfigPlugin()
    if not hasattr(plugin, "_process_network_details_v2"):
        LOG.error("Cloudbase-Init network plugin is missing _process_network_details_v2")
        return 0

    LOG.info("Applying Proxmox network data from %s", NETWORK_DATA_PATH)
    plugin._process_network_details_v2(network_details)
    return 0


if __name__ == "__main__":
    sys.exit(main())
