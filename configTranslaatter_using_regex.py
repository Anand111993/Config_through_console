import sys
import os
import re
import logging
import json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QTextEdit, QFileDialog, QVBoxLayout,
    QWidget, QLabel, QHBoxLayout, QMessageBox,QGridLayout
)
from jinja2 import Environment, FileSystemLoader

# Configure Logging
logging.basicConfig(filename='config_converter.log', level=logging.ERROR,
format='%(asctime)s - %(levelname)s - %(message)s')


# Parsing Function for Hostname using Regex
def parse_hostname(config_text):
    match = re.search(r"^hostname (\S+)", config_text, re.MULTILINE)
    return match.group(1) if match else "N/A"


def parse_4900_config(config_lines):
    parsed_data = {
        "hostname": "",
        "interfaces": {},
        "ospf_details": {
            "ospf_id": "N/A",
            "router_id": "N/A",
            "passive_interfaces": [],
            "areas": []
        },
        "bgp_details": {}
    }

    # Convert config_lines (list) to a single string for regex operations
    config_text = "".join(config_lines)

    # Parse hostname (if parse_hostname exists)
    parsed_data["hostname"] = parse_hostname(config_text)

    # Split configuration into blocks based on "!"
    blocks = config_text.strip().split("!")

    # Parse each block using regex
    for block in blocks:
        if "interface" in block:
            # Extract the interface name
            intf_match = re.search(r"interface (\S+)", block)
            interface = intf_match.group(1) if intf_match else "N/A"

            if interface not in parsed_data["interfaces"]:
                parsed_data["interfaces"][interface] = {
                    "description": "N/A",
                    "vrf": "N/A",
                    "ip_address": "N/A",
                    "subnet_mask": "N/A",
                    "hsrp_ip": "N/A",
                    "hsrp_priority": "N/A"
                }

            # Extract description, VRF, IP, subnet mask, and HSRP details
            desc_match = re.search(r"description ([^\n]+)", block)
            if desc_match:
                parsed_data["interfaces"][interface]["description"] = desc_match.group(1).strip()

            vrf_match = re.search(r"vrf forwarding ([^\n]+)", block)
            if vrf_match:
                parsed_data["interfaces"][interface]["vrf"] = vrf_match.group(1).strip()

            ip_match = re.search(r"ip address (\d{1,3}(?:\.\d{1,3}){3}) (\d{1,3}(?:\.\d{1,3}){3})", block)
            if ip_match:
                parsed_data["interfaces"][interface]["ip_address"] = ip_match.group(1)
                parsed_data["interfaces"][interface]["subnet_mask"] = ip_match.group(2)

            if "Vlan" in interface:
                hsrp_ip_match = re.search(r"standby \d+ ip (\d+\.\d+\.\d+\.\d+)", block)
                if hsrp_ip_match:
                    parsed_data["interfaces"][interface]["hsrp_ip"] = hsrp_ip_match.group(1)

                hsrp_priority_match = re.search(r"standby \d+ priority (\d+)", block)
                if hsrp_priority_match:
                    parsed_data["interfaces"][interface]["hsrp_priority"] = hsrp_priority_match.group(1)

    # Convert interfaces dictionary to a list for JSON serialization
    parsed_data["interfaces"] = [{"name": intf, **details} for intf, details in parsed_data["interfaces"].items()]

    # Parse OSPF details
    parsed_data["ospf_details"] = parse_ospf_details(config_text)

    # Parse BGP details
    parsed_data["bgp_details"] = parse_bgp_config(config_text)

    # Save structured data to a local file
    # with open("parsed_config.json", "w") as json_file:
    #     json.dump(parsed_data, json_file, indent=4)

    # Print parsed interface data
    # print("\n--- Parsed Interface Details ---")
    # for intf in parsed_data["interfaces"]:
    #     print(f"Interface: {intf['name']}")
    #     print(f"  Description: {intf['description']}")
    #     print(f"  VRF: {intf['vrf']}")
    #     print(f"  IP Address: {intf['ip_address']}")
    #     print(f"  Subnet Mask: {intf['subnet_mask']}")
    #     print(f"  HSRP IP: {intf['hsrp_ip']}")
    #     print(f"  HSRP Priority: {intf['hsrp_priority']}\n")

    # print("\n--- OSPF Details ---")
    # print(f"OSPF ID: {parsed_data['ospf_details']['ospf_id']}")
    # print(f"Router ID: {parsed_data['ospf_details']['router_id']}")
    # print(f"Passive Interfaces: {', '.join(parsed_data['ospf_details']['passive_interfaces'])}")
    # print(f"Areas: {', '.join(parsed_data['ospf_details']['areas'])}")

    return parsed_data





def parse_ospf_details(config_lines):
    ospf_details = {
        "ospf_id": "N/A",
        "router_id": "N/A",
        "passive_interfaces": [],
        "areas": []
    }
    
   
    config_text = "".join(config_lines)
    
    # Extract OSPF details using regex
    ospf_id_pattern = re.search(r"router ospf (\d+)", config_text)
    router_id_pattern = re.search(r"router-id (\d+\.\d+\.\d+\.\d+)", config_text)
    passive_interfaces_pattern = re.findall(r"no passive-interface (\S+)", config_text)
    area_pattern = re.findall(r"network \d+\.\d+\.\d+\.\d+ \d+\.\d+\.\d+\.\d+ area (\d+\.\d+\.\d+\.\d+)", config_text)

    ospf_details["ospf_id"] = ospf_id_pattern.group(1) if ospf_id_pattern else "N/A"
    ospf_details["router_id"] = router_id_pattern.group(1) if router_id_pattern else "N/A"
    ospf_details["passive_interfaces"] = passive_interfaces_pattern if passive_interfaces_pattern else []
    ospf_details["areas"] = list(set(area_pattern)) if area_pattern else ["N/A"]

    # # Print the parsed OSPF details for debugging
    # print("\n--- Parsed OSPF Details ---")
    # print(f"OSPF ID: {ospf_details['ospf_id']}")
    # print(f"Router ID: {ospf_details['router_id']}")
    # print(f"Passive Interfaces: {', '.join(ospf_details['passive_interfaces'])}")
    # print(f"Areas: {', '.join(ospf_details['areas'])}")

    return ospf_details



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
    bgp_config = bgp_config.replace("\r\n", "\n")
    bgp_as_match = re.search(r"router bgp (\d+)", bgp_config)
    router_id_match = re.search(r"bgp router-id (\d+\.\d+\.\d+\.\d+)", bgp_config)
    # print(f"Config length: {len(bgp_config)}")
    # print(f"Config content: {repr(bgp_config[:500])}...")

    if bgp_as_match:
        result["bgp_as"] = bgp_as_match.group(1)
    if router_id_match:
        result["bgp_router_id"] = router_id_match.group(1)

    # Extract networks from address-family ipv4
    # address_family_ipv4_match = re.search(r"address-family ipv4(.*?)exit-address-family", bgp_config, re.DOTALL)
    # if address_family_ipv4_match:
    #     print("Address-family IPv4 block found.")
        
    #     address_family_ipv4_block = address_family_ipv4_match.group(1)
    #     network_pattern = re.compile(r"network (\d+\.\d+\.\d+\.\d+) mask (\d+\.\d+\.\d+\.\d+)")
    #     print(repr(address_family_ipv4_block[:500]))
    #     for match in network_pattern.finditer(address_family_ipv4_block):
    #         result["address_family_ipv4"]["networks"].append({
    #             "network": match.group(1),
    #             "mask": match.group(2)
    #         })
    # else:
    #     print("No address-family IPv4 block found.")
 
    lines = bgp_config.splitlines()
    inside_address_family_ipv4 = False
    for line in lines:
        if "address-family ipv4" in line:
            inside_address_family_ipv4 = True
            continue
        if "exit-address-family" in line and inside_address_family_ipv4:
            inside_address_family_ipv4 = False
            continue
        if inside_address_family_ipv4 and "network" in line:
            network_match = re.match(r"\s*network\s+(\d+\.\d+\.\d+\.\d+)\s+mask\s+(\d+\.\d+\.\d+\.\d+)", line)
            if network_match:
                result["address_family_ipv4"]["networks"].append({
                    "network": network_match.group(1),
                    "mask": network_match.group(2)
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


# Jinja2 Template Rendering Function
def generate_nexus_config(parsed_data, jinja_file):
    env = Environment(loader=FileSystemLoader("/"))
    template = env.get_template(jinja_file)
    return template.render(parsed_data)


# PyQt5 GUI Application
class ConfigConverterApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Cisco 4900 to Nexus Config Converter")
        self.setGeometry(100, 100, 1000, 600)

        layout = QVBoxLayout()
        grid_layout = QGridLayout()

        # Buttons Layout
        btn_layout = QHBoxLayout()
        self.btn_load = QPushButton("Load Config")
        self.btn_load.clicked.connect(self.load_config)
        btn_layout.addWidget(self.btn_load)

        self.btn_import_jinja = QPushButton("Import Jinja Template")
        self.btn_import_jinja.clicked.connect(self.import_jinja)
        btn_layout.addWidget(self.btn_import_jinja)

        self.btn_convert = QPushButton("Convert")
        self.btn_convert.clicked.connect(self.convert_config)
        btn_layout.addWidget(self.btn_convert)

        self.btn_save = QPushButton("Save Converted Config")
        self.btn_save.clicked.connect(self.save_config)
        btn_layout.addWidget(self.btn_save)

        layout.addLayout(btn_layout)

        # Labels and Text Areas in Grid Layout (1:1, 2:1, 1:2, 2:2)
        self.label_orig = QLabel("Original Cisco 4900 Configuration:")
        grid_layout.addWidget(self.label_orig, 0, 0)
        self.original_config_text = QTextEdit()
        self.original_config_text.setReadOnly(False)
        grid_layout.addWidget(self.original_config_text, 1, 0)

        self.label_conv = QLabel("Converted Nexus Configuration:")
        grid_layout.addWidget(self.label_conv, 0, 1)
        self.converted_config_text = QTextEdit()
        grid_layout.addWidget(self.converted_config_text, 1, 1)

        layout.addLayout(grid_layout)

        self.status_label = QLabel("Status: Ready")
        layout.addWidget(self.status_label)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.config_lines = []  # Store file lines
        self.jinja_file = "nexus_config.j2"  # Default Jinja Template

    #     self.setWindowTitle("Cisco 4900 to Nexus Config Converter")
    #     self.setGeometry(100, 100, 1000, 600)

    #     layout = QVBoxLayout()

    #     # Buttons Layout
    #     btn_layout = QHBoxLayout()
    #     self.btn_load = QPushButton("Load Config")
    #     self.btn_load.clicked.connect(self.load_config)
    #     btn_layout.addWidget(self.btn_load)

    #     self.btn_import_jinja = QPushButton("Import Jinja Template")
    #     self.btn_import_jinja.clicked.connect(self.import_jinja)
    #     btn_layout.addWidget(self.btn_import_jinja)

    #     self.btn_convert = QPushButton("Convert")
    #     self.btn_convert.clicked.connect(self.convert_config)
    #     btn_layout.addWidget(self.btn_convert)

    #     self.btn_save = QPushButton("Save Converted Config")
    #     self.btn_save.clicked.connect(self.save_config)
    #     btn_layout.addWidget(self.btn_save)

    #     layout.addLayout(btn_layout)

    #     # Labels and Text Areas Layout
    #     self.label_orig = QLabel("Original Cisco 4900 Configuration:")
    #     layout.addWidget(self.label_orig)
    #     self.original_config_text = QTextEdit()
    #     self.original_config_text.setReadOnly(True)
    #     layout.addWidget(self.original_config_text)

    #     self.label_conv = QLabel("Converted Nexus Configuration:")
    #     layout.addWidget(self.label_conv)
    #     self.converted_config_text = QTextEdit()
    #     layout.addWidget(self.converted_config_text)

    #     self.status_label = QLabel("Status: Ready")
    #     layout.addWidget(self.status_label)

    #     container = QWidget()
    #     container.setLayout(layout)
    #     self.setCentralWidget(container)

    #     self.config_lines = []  # Store file lines
    #     self.jinja_file = "nexus_config.j2"  # Default Jinja Template
  
    



    # def load_config(self):
    #     file_name, _ = QFileDialog.getOpenFileName(self, "Open Cisco 4900 Config", "", "Text Files (*.txt);;All Files (*)")
    #     if file_name:
    #         with open(file_name, 'r') as file:
    #             self.config_lines = file.readlines()
    #             self.original_config_text.setPlainText("".join(self.config_lines))
    #             self.status_label.setText("Status: File Loaded Successfully")


    def load_config(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Cisco 4900 Config", "", "Text Files (*.txt);;All Files (*)")
        if file_name:
            try:
                with open(file_name, 'r', encoding='utf-8') as file:
                    self.config_lines = file.readlines()
                    self.original_config_text.setPlainText("".join(self.config_lines))
                    if not self.config_lines:
                        QMessageBox.warning(self, "Error", "The selected file is empty.")
                        return
                    self.status_label.setText("Status: File Loaded Successfully")
            except Exception as e:
                logging.error(f"File error: {str(e)}")
                QMessageBox.critical(self, "File Error", f"Error loading file: {str(e)}")

    # def import_jinja(self):
    #     file_name, _ = QFileDialog.getOpenFileName(self, "Import Jinja Template", "", "Jinja2 Templates (*.j2);;All Files (*)")
    #     if file_name:
    #         self.jinja_file = file_name
    #         self.status_label.setText(f"Status: Jinja Template '{file_name}' Imported Successfully")

    def import_jinja(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Import Jinja Template", "", "Jinja2 Templates (*.j2);;All Files (*)")
        if file_name:
            self.jinja_file = file_name
            self.status_label.setText(f"Status: Jinja Template '{file_name}' Imported Successfully")


    # def save_config(self):
    #     file_name, _ = QFileDialog.getSaveFileName(self, "Save Nexus Config", "", "Text Files (*.txt);;All Files (*)")
    #     if file_name:
    #         with open(file_name, 'w') as file:
    #             file.write(self.converted_config_text.toPlainText())
    #             self.status_label.setText("Status: Configuration Saved")

    def save_config(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Nexus Config", "", "Text Files (*.txt);;All Files (*)")
        if file_name:
            try:
                with open(file_name, 'w', encoding='utf-8') as file:
                    file.write(self.converted_config_text.toPlainText())
                    self.status_label.setText("Status: Configuration Saved")
            except Exception as e:
                logging.error(f"File save error: {str(e)}")
                QMessageBox.critical(self, "File Error", f"Error saving file: {str(e)}")

    # def convert_config(self):
    #     if not self.config_lines:
    #         QMessageBox.warning(self, "Error", "No configuration file loaded!")
    #         return

    #     parsed_data = parse_4900_config(self.config_lines)
    #     converted_config = generate_nexus_config(parsed_data, self.jinja_file)
    #     self.converted_config_text.setPlainText(converted_config)
    #     self.status_label.setText(f"Status: Conversion Completed (Hostname: {parsed_data['hostname']})")

    def convert_config(self):
        try:
            if not self.config_lines:
                QMessageBox.warning(self, "Error", "No configuration file loaded!")
                return
            
            parsed_data = parse_4900_config(self.config_lines)
            if not parsed_data:
                QMessageBox.warning(self, "Error", "Parsing failed. No data extracted.")
                return
            
            converted_config = generate_nexus_config(parsed_data, self.jinja_file)
            if "Error" in converted_config:
                QMessageBox.critical(self, "Conversion Error", converted_config)
                return
            
            self.converted_config_text.setPlainText(converted_config)
            self.status_label.setText(f"Status: Conversion Completed (Hostname: {parsed_data.get('hostname', 'Unknown')})")
        except Exception as e:
            logging.error(f"Critical error during conversion: {str(e)}")
            QMessageBox.critical(self, "Critical Error", f"Unexpected error: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWin = ConfigConverterApp()
    mainWin.show()
    sys.exit(app.exec_())
