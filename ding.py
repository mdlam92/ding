"""CLI interface."""
#!/usr/bin/python3
from dataclasses import dataclass, field
from dns.resolver import (
    resolve,
    NoNameservers,
    NXDOMAIN,
    get_default_resolver,
    Resolver,
)
import netifaces
import platform
from pprint import pprint, pformat
from psutil import net_if_stats
import subprocess
import sys


def get_default_route_interface_name() -> str:
    """Get the default interface name."""
    gateways = netifaces.gateways()
    if netifaces.AF_INET in gateways["default"]:
        default_gateway = gateways["default"][netifaces.AF_INET][1]
        return default_gateway
    else:
        print(f"no default gateway in: {gateways=}, internet is probably broken")
        print("network interfaces: ")
        pprint(net_if_stats())
        sys.exit("No default gateway!")


def get_interface_ip_address(interface: str) -> str:
    """Get the IP address of an interface."""
    return netifaces.ifaddresses(interface)[netifaces.AF_INET][0]["addr"]


def get_default_gateway() -> str:
    """Get the default gateway."""
    default_gateway = netifaces.gateways()["default"][netifaces.AF_INET][0]
    return default_gateway


def is_host_reachable(host: str) -> bool:
    """Check if the default gateway and DNS are reachable."""
    param = "-n" if platform.system().lower() == "windows" else "-c"
    command = ["ping", param, "1", host]
    result = (
        subprocess.call(command, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        == 0
    )
    if not result:
        print(f"{host=} was not reachable...")
    return result


def is_host_resolvable(host: str) -> bool:
    """Check if the default name servers are reachable."""
    try:
        resolve(host)
        return True
    except NXDOMAIN:
        # The DNS query name does not exist
        print(f"nameserver claims that {host=} does not exist")
        return False
    except NoNameservers:
        # All nameservers failed to answer the query
        print(f"all nameservers failed to answer for {host=}")
        return False


@dataclass
class DingResult:

    interface_name: str = get_default_route_interface_name()
    default_gateway: str = get_default_gateway()
    default_resolver: Resolver = get_default_resolver()
    default_gateway_reachable: bool = field(default=False)
    google_reachable: bool = field(default=False)
    default_resolver_reachable: bool = field(default=False)
    google_resolvable: bool = field(default=False)
    good: bool = field(default=False)

    def __post_init__(self):
        self.default_gateway_reachable = is_host_reachable(self.default_gateway)
        self.google_reachable = is_host_reachable(host="8.8.8.8")
        self.default_resolver_reachable = is_host_reachable(
            host=self.default_resolver.nameservers[0]
        )
        self.google_resolvable = is_host_resolvable(host="google.com")
        self.good = all(
            [
                self.default_gateway_reachable,
                self.google_reachable,
                self.default_resolver_reachable,
                self.google_resolvable,
            ]
        )

    def __str__(self):
        d = self.__dict__
        d['default_resolver'] = self.default_resolver.__dict__
        return pformat(d)


def execute() -> None:
    """CLI entrypoint."""
    ding_result = DingResult()
    if not ding_result.good:
        print(ding_result)
        sys.exit("DOWN")
    else:
        print(ding_result)
        print("UP")


if __name__ == "__main__":
    execute()
