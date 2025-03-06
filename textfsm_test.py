import re
import json

bgp_config = """
router bgp 65138
 bgp router-id 10.169.2.113
 bgp log-neighbor-changes
 timers bgp 1 3
 neighbor 10.177.27.234 remote-as 65138
 neighbor 10.177.27.234 description ASBNVL02
 neighbor 10.177.27.234 password 7 105A0416071E1E0E
 neighbor 10.177.27.234 update-source Vlan111
 neighbor 10.177.27.241 remote-as 65137
 neighbor 10.177.27.241 description DRCNVL51_Global
 neighbor 10.177.27.241 password 7 0612022E
 !
 address-family ipv4
  network 10.166.56.0 mask 255.255.255.192
  network 10.166.56.204 mask 255.255.255.252
  network 10.168.152.0 mask 255.255.255.192
  network 10.168.152.204 mask 255.255.255.252
 exit-address-family
 !
 address-family ipv4 vrf METROE-E
  neighbor 10.177.27.238 remote-as 65138
  neighbor 10.177.27.238 description ASBNVL02_VRF_METROE-E
  neighbor 10.177.27.238 password 7 120D081810020001
  neighbor 10.177.27.238 activate
  neighbor 10.177.27.245 remote-as 65137
  neighbor 10.177.27.245 description DRCNVL51_VRF_METROE-E
  neighbor 10.177.27.245 password 7 0612022E
 exit-address-family
 !
"""

# result = {
#     "bgp_as": "",
#     "bgp_router_id": "",
#     "neighbors": [],
#     "address_family_ipv4": {
#         "networks": []
#     },
#     "address_family_ipv4_vrf_METROE-E": {
#         "neighbors": []
#     }
# }

# # Extract BGP AS and Router ID
# bgp_as_match = re.search(r"router bgp (\d+)", bgp_config)
# router_id_match = re.search(r"bgp router-id (\d+\.\d+\.\d+\.\d+)", bgp_config)

# if bgp_as_match:
#     result["bgp_as"] = bgp_as_match.group(1)
# if router_id_match:
#     result["bgp_router_id"] = router_id_match.group(1)

# # Extract neighbors from address-family ipv4 vrf METROE-E with loop logic
# vrf_family_match = re.search(r"address-family ipv4 vrf METROE-E(.*?)exit-address-family", bgp_config, re.DOTALL)
# if vrf_family_match:
#     vrf_family_block = vrf_family_match.group(1)
#     vrf_neighbor_ips = set(re.findall(r"neighbor (\d+\.\d+\.\d+\.\d+)", vrf_family_block))
    
#     for neighbor_ip in vrf_neighbor_ips:
#         neighbor_data = {
#             "neighbor_ip": neighbor_ip,
#             "remote_as": "",
#             "description": "",
#             "password": ""
#         }
        
#         neighbor_block_pattern = rf"(neighbor {neighbor_ip} .*?)(?=\n\s*neighbor|\n\s*!)"
#         neighbor_blocks = re.findall(neighbor_block_pattern, vrf_family_block, re.DOTALL)
        
#         for block in neighbor_blocks:
#             remote_as_match = re.search(r"remote-as (\d+)", block)
#             description_match = re.search(r"description (.+)", block)
#             password_match = re.search(r"password (\d+ \S+)", block)
            
#             if remote_as_match:
#                 neighbor_data["remote_as"] = remote_as_match.group(1)
#             if description_match:
#                 neighbor_data["description"] = description_match.group(1).strip()
#             if password_match:
#                 neighbor_data["password"] = password_match.group(1)
        
#         result["address_family_ipv4_vrf_METROE-E"]["neighbors"].append(neighbor_data)

# # Extract global neighbors, skipping those already in address-family ipv4 vrf METROE-E
# vrf_neighbors = {n["neighbor_ip"] for n in result["address_family_ipv4_vrf_METROE-E"]["neighbors"]}
# neighbor_ips = set(re.findall(r"neighbor (\d+\.\d+\.\d+\.\d+)", bgp_config)) - vrf_neighbors
# for neighbor_ip in neighbor_ips:
#     neighbor_data = {
#         "neighbor_ip": neighbor_ip,
#         "remote_as": "",
#         "description": "",
#         "password": "",
#         "update_source": ""
#     }
    
#     neighbor_block_pattern = rf"(neighbor {neighbor_ip} .*?)(?=\n\s*neighbor|\n\s*!)"
#     neighbor_blocks = re.findall(neighbor_block_pattern, bgp_config, re.DOTALL)
    
#     for block in neighbor_blocks:
#         remote_as_match = re.search(r"remote-as (\d+)", block)
#         description_match = re.search(r"description (.+)", block)
#         password_match = re.search(r"password (\d+ \S+)", block)
#         update_source_match = re.search(r"update-source (.+)", block)
        
#         if remote_as_match:
#             neighbor_data["remote_as"] = remote_as_match.group(1)
#         if description_match:
#             neighbor_data["description"] = description_match.group(1).strip()
#         if password_match:
#             neighbor_data["password"] = password_match.group(1)
#         if update_source_match:
#             neighbor_data["update_source"] = update_source_match.group(1).strip()
    
#     result["neighbors"].append(neighbor_data)

# # Extract networks from address-family ipv4
# address_family_ipv4_match = re.search(r"address-family ipv4(.*?)exit-address-family", bgp_config, re.DOTALL)
# if address_family_ipv4_match:
#     address_family_ipv4_block = address_family_ipv4_match.group(1)
#     network_pattern = re.compile(r"network (\d+\.\d+\.\d+\.\d+) mask (\d+\.\d+\.\d+\.\d+)")
#     for match in network_pattern.finditer(address_family_ipv4_block):
#         result["address_family_ipv4"]["networks"].append({
#             "network": match.group(1),
#             "mask": match.group(2)
#         })

# # Print the result as JSON
# print(json.dumps(result, indent=2))

# import re
# import json

def parse_bgp_config(bgp_config):
    result = {
        "bgp_as": "",
        "bgp_router_id": "",
        "neighbors": [],
        "address_family_ipv4": {
            "networks": []
        },
        "address_family_ipv4_vrf_METROE-E": {
            "neighbors": []
        }
    }

    # Extract BGP AS and Router ID
    bgp_as_match = re.search(r"router bgp (\d+)", bgp_config)
    router_id_match = re.search(r"bgp router-id (\d+\.\d+\.\d+\.\d+)", bgp_config)

    if bgp_as_match:
        result["bgp_as"] = bgp_as_match.group(1)
    if router_id_match:
        result["bgp_router_id"] = router_id_match.group(1)

    # Extract networks from address-family ipv4
    address_family_ipv4_match = re.search(r"address-family ipv4(.*?)exit-address-family", bgp_config, re.DOTALL)
    if address_family_ipv4_match:
        address_family_ipv4_block = address_family_ipv4_match.group(1)
        network_pattern = re.compile(r"network (\d+\.\d+\.\d+\.\d+) mask (\d+\.\d+\.\d+\.\d+)")
        for match in network_pattern.finditer(address_family_ipv4_block):
            result["address_family_ipv4"]["networks"].append({
                "network": match.group(1),
                "mask": match.group(2)
            })

    # Extract neighbors from address-family ipv4 vrf METROE-E
    vrf_family_match = re.search(r"address-family ipv4 vrf METROE-E(.*?)exit-address-family", bgp_config, re.DOTALL)
    if vrf_family_match:
        vrf_family_block = vrf_family_match.group(1)
        vrf_neighbor_ips = set(re.findall(r"neighbor (\d+\.\d+\.\d+\.\d+)", vrf_family_block))
        
        for neighbor_ip in vrf_neighbor_ips:
            neighbor_data = {
                "neighbor_ip": neighbor_ip,
                "remote_as": "",
                "description": "",
                "password": ""
            }
            
            neighbor_block_pattern = rf"(neighbor {neighbor_ip} .*?)(?=\n\s*neighbor|\n\s*!)"
            neighbor_blocks = re.findall(neighbor_block_pattern, vrf_family_block, re.DOTALL)
            
            for block in neighbor_blocks:
                remote_as_match = re.search(r"remote-as (\d+)", block)
                description_match = re.search(r"description (.+)", block)
                password_match = re.search(r"password (\d+ \S+)", block)
                
                if remote_as_match:
                    neighbor_data["remote_as"] = remote_as_match.group(1)
                if description_match:
                    neighbor_data["description"] = description_match.group(1).strip()
                if password_match:
                    neighbor_data["password"] = password_match.group(1)
            
            result["address_family_ipv4_vrf_METROE-E"]["neighbors"].append(neighbor_data)

    # Extract global neighbors (not in VRF)
    vrf_neighbors = {n["neighbor_ip"] for n in result["address_family_ipv4_vrf_METROE-E"]["neighbors"]}
    neighbor_ips = set(re.findall(r"neighbor (\d+\.\d+\.\d+\.\d+)", bgp_config)) - vrf_neighbors
    for neighbor_ip in neighbor_ips:
        neighbor_data = {
            "neighbor_ip": neighbor_ip,
            "remote_as": "",
            "description": "",
            "password": "",
            "update_source": ""
        }
        
        neighbor_block_pattern = rf"(neighbor {neighbor_ip} .*?)(?=\n\s*neighbor|\n\s*!)"
        neighbor_blocks = re.findall(neighbor_block_pattern, bgp_config, re.DOTALL)
        
        for block in neighbor_blocks:
            remote_as_match = re.search(r"remote-as (\d+)", block)
            description_match = re.search(r"description (.+)", block)
            password_match = re.search(r"password (\d+ \S+)", block)
            update_source_match = re.search(r"update-source (.+)", block)
            
            if remote_as_match:
                neighbor_data["remote_as"] = remote_as_match.group(1)
            if description_match:
                neighbor_data["description"] = description_match.group(1).strip()
            if password_match:
                neighbor_data["password"] = password_match.group(1)
            if update_source_match:
                neighbor_data["update_source"] = update_source_match.group(1).strip()
        
        result["neighbors"].append(neighbor_data)

    return result

parsed_bgp = parse_bgp_config(bgp_config)
print(json.dumps(parsed_bgp, indent=2))




import re
import json

def parse_bgp_config(bgp_config):
    result = {
        "bgp_as": "",
        "bgp_router_id": "",
        "neighbors": [],
        "address_family_ipv4": {
            "networks": []
        },
        "address_family_ipv4_vrf_METROE-E": {
            "neighbors": []
        }
    }

    # Extract BGP AS and Router ID
    bgp_as_match = re.search(r"router bgp (\d+)", bgp_config)
    router_id_match = re.search(r"bgp router-id (\d+\.\d+\.\d+\.\d+)", bgp_config)

    if bgp_as_match:
        result["bgp_as"] = bgp_as_match.group(1)
    if router_id_match:
        result["bgp_router_id"] = router_id_match.group(1)

    # Extract networks from address-family ipv4 (more robust regex)
    address_family_ipv4_match = re.search(r"address-family\s+ipv4(.*?)exit-address-family", bgp_config, re.DOTALL)
    if address_family_ipv4_match:
        address_family_ipv4_block = address_family_ipv4_match.group(1)
        network_pattern = re.compile(r"\s*network\s+(\d+\.\d+\.\d+\.\d+)\s+mask\s+(\d+\.\d+\.\d+\.\d+)")
        for match in network_pattern.finditer(address_family_ipv4_block):
            result["address_family_ipv4"]["networks"].append({
                "network": match.group(1),
                "mask": match.group(2)
            })

    # Debugging to ensure the networks are captured
    print("Networks found:", result["address_family_ipv4"]["networks"])

    return result

# Sample config to test


# Test the function
parsed_result = parse_bgp_config(bgp_config)
print(json.dumps(parsed_result, indent=2))
