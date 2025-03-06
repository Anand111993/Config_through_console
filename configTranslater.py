import sys
import shutil
import os
import re
import json
from io import StringIO
import textfsm
from io import StringIO
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QTextEdit, QFileDialog, QVBoxLayout,
    QWidget, QLabel, QHBoxLayout, QMessageBox
)
from jinja2 import Environment, FileSystemLoader



# Parsing Function for Hostname
def parse_hostname(config_text):
    textfsm_template = """Value HOSTNAME (\S+)

Start
  ^hostname\s+${HOSTNAME} -> Record
"""
    
    fsm = textfsm.TextFSM(StringIO(textfsm_template))
    result = fsm.ParseText(config_text)
    
    return result[0][0] if result else None

# # Main Parsing Function
def parse_4900_config(config_lines):
    parsed_data = {
        "hostname": "",
        "interfaces": []
    }

    config_text = "".join(config_lines)
    parsed_data["hostname"] = parse_hostname(config_text)  # ✅ Uses fixed TextFSM parsing
    parsed_data.update(parse_interfaces(config_text))  # ✅ Parses interfaces dynamically

    # Save structured data to a local file
    with open("parsed_config.json", "w") as json_file:
        json.dump(parsed_data, json_file, indent=4)
    
    return parsed_data


def parse_interfaces(config_text):
    textfsm_template = """Value INTF (\S+)
Value DESC (.*)
Value VRF (\S*)
Value IPADDR (\d+\.\d+\.\d+\.\d+|N/A)
Value SUBNET (\d+\.\d+\.\d+\.\d+|N/A)

Start
  ^interface ${INTF} -> Continue
  ^ description ${DESC} -> Continue
  ^ vrf forwarding ${VRF} -> Continue
  ^ ip address ${IPADDR} ${SUBNET} -> Continue
  ^interface \S+ -> Record Start
  ^! -> Record



"""

    fsm = textfsm.TextFSM(StringIO(textfsm_template))
    result = fsm.ParseText(config_text)

    interfaces = []
    for entry in result:
        interface = {"name": entry[0]}

        # Handle optional fields safely
        if len(entry) > 1 and entry[1]:
            interface["description"] = entry[1]
        if len(entry) > 2 and entry[2]:
            interface["vrf"] = entry[2]

        # Validate and process IP/Subnet safely
        if len(entry) > 3 and entry[3] and len(entry) > 4 and entry[4]:
            try:
                subnet_mask = entry[4]
                cidr = sum(bin(int(x)).count('1') for x in subnet_mask.split('.'))
                interface["ip"] = f"{entry[3]}/{cidr}"
            except ValueError:
                print(f"Warning: Invalid subnet mask '{subnet_mask}' for interface {interface['name']}")
                interface["ip"] = entry[3]  # Store IP without subnet if parsing fails

        interfaces.append(interface)

    return {"interfaces": interfaces}



def generate_nexus_config(parsed_data, jinja_file):
    env = Environment(loader=FileSystemLoader("/"))  # Allow loading from any directory
    template = env.get_template(jinja_file)  # Use full file path
    return template.render(parsed_data)




# PyQt5 GUI Application
class ConfigConverterApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Cisco 4900 to Nexus Config Converter")
        self.setGeometry(100, 100, 1000, 600)

        layout = QVBoxLayout()

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

        # Labels and Text Areas Layout (Vertical Alignment)
        self.label_orig = QLabel("Original Cisco 4900 Configuration:")
        layout.addWidget(self.label_orig)
        self.original_config_text = QTextEdit()
        self.original_config_text.setReadOnly(True)
        layout.addWidget(self.original_config_text)

        self.label_conv = QLabel("Converted Nexus Configuration:")
        layout.addWidget(self.label_conv)
        self.converted_config_text = QTextEdit()
        layout.addWidget(self.converted_config_text)

        # Status Bar
        self.status_label = QLabel("Status: Ready")
        layout.addWidget(self.status_label)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.config_lines = []  # Store file lines
        self.jinja_file = "nexus_config.j2"  # Default Jinja Template

    def load_config(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Cisco 4900 Config", "", "Text Files (*.txt);;All Files (*)")
        if file_name:
            with open(file_name, 'r') as file:
                self.config_lines = file.readlines()
                self.original_config_text.setPlainText("".join(self.config_lines))
                self.status_label.setText("Status: File Loaded Successfully")

    # def import_jinja(self):
    #     file_name, _ = QFileDialog.getOpenFileName(self, "Import Jinja Template", "", "Jinja2 Templates (*.j2);;All Files (*)")
    #     if file_name:
    #         self.jinja_file = file_name.split('/')[-1]  # Extract filename
    #         self.status_label.setText(f"Status: Jinja Template '{self.jinja_file}' Imported Successfully")
            



    def import_jinja(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Import Jinja Template", "", "Jinja2 Templates (*.j2);;All Files (*)")
        if file_name:
            self.jinja_file = file_name  # Store full path instead of just filename
            self.status_label.setText(f"Status: Jinja Template '{file_name}' Imported Successfully")


    def save_config(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Nexus Config", "", "Text Files (*.txt);;All Files (*)")
        if file_name:
            with open(file_name, 'w') as file:
                file.write(self.converted_config_text.toPlainText())
                self.status_label.setText("Status: Configuration Saved")


    def convert_config(self):
        if not self.config_lines:
            QMessageBox.warning(self, "Error", "No configuration file loaded!")
            return

        parsed_data = parse_4900_config(self.config_lines)
        converted_config = generate_nexus_config(parsed_data, self.jinja_file)
        self.converted_config_text.setPlainText(converted_config)
        self.status_label.setText(f"Status: Conversion Completed (Hostname: {parsed_data['hostname']})")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWin = ConfigConverterApp()
    mainWin.show()
    sys.exit(app.exec_())
