
# Dictionary to store platform and code information
platform_codes = {
    "C9407R": "16.12.05",
    "C9410R": "16.12.05",
    "C9300-48P-A": "16.12.05",
    "N9K-C93180YC-FX3": "9.3(8)",
    "ASR1002-HX": "17.03.04a",  
    "31108PCV": "9.3(11)"  ,
    "C9396PX": "7.0(3)I4(5)"
}

# List to store QC commands
qc_commands = [
    "ter len 0",
    "sh version",
    "sh license all",
    "show environment",
    "sh int status",
    "sh vlan brief",
    "sh inventory all",
    "show environment",
    "sh cdp nei",
    "sh ip arp",
    "sh ip int brief",
    "sh hsrp brief",
    "sh int trunk",
    "sh spanning-tree",
    "sh ip ospf nei",
    "sh ip bgp sum",
    "sh ip bgp vrf all all sum",
    "Show run | inc hardware",
    "show snmp user",
    "sh run"    
]
