import sys
import openpyxl
from PyQt5.QtWidgets import QApplication,QGridLayout,QMainWindow, QVBoxLayout,QTableWidget,QInputDialog,QTextEdit,QPushButton,QMessageBox , QWidget, QFileDialog, QLineEdit, QLabel
from PyQt5.QtCore import QThread, pyqtSignal
import paramiko
import time
import re
from PyQt5.QtWidgets import (QMainWindow, QGridLayout, QLabel, QLineEdit, QPushButton,QComboBox,
                             QTextEdit, QWidget, QDialog,QTableWidget, QTableWidgetItem, QTableWidgetItem,QHBoxLayout)
import logging
import pandas as pd
import os
from netmiko import ConnectHandler
import logging
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5 import QtWidgets
from PyQt5.QtCore import QTimer,Qt
from PyQt5.QtGui import QTextCursor





class QTextBoxLogger(logging.Handler, QObject):   #This  class for UPdate Signals in Active Console Sever 
    log_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        QObject.__init__(self)

    def emit(self, record):
        msg = self.format(record)
        self.log_signal.emit(msg)

class SaveLocationDialog(QMainWindow):  #This class used for GUI design and button handler
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Save Location Dialog')
        self.setGeometry(100, 100, 800, 600)  # Adjust the window size as needed
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        log_handler = QTextBoxLogger()
        self.logger.addHandler(log_handler)

        self.initUI()

        log_handler.log_signal.connect(self.updateLogTextBox)

    def initUI(self):
        mainLayout = QGridLayout()

        # Server IP Input
        serverIpWidget = QWidget()
        serverIpLayout = QHBoxLayout(serverIpWidget)
        self.server_ip_label = QLabel('Server IP:')
        self.server_ip_input = QLineEdit()
        serverIpLayout.addWidget(self.server_ip_label)
        serverIpLayout.addWidget(self.server_ip_input)
        serverIpLayout.addStretch()
        mainLayout.addWidget(serverIpWidget, 0, 0, 1, 3)  # Span 3 columns

        # Username Input
        usernameWidget = QWidget()
        usernameLayout = QHBoxLayout(usernameWidget)
        self.username_label = QLabel('Username:')
        self.username_input = QLineEdit()
        usernameLayout.addWidget(self.username_label)
        usernameLayout.addWidget(self.username_input)
        usernameLayout.addStretch()
        mainLayout.addWidget(usernameWidget, 1, 0, 1, 3)  # Span 3 columns

        # Password Input and additional buttons
        passwordWidget = QWidget()
        passwordLayout = QHBoxLayout(passwordWidget)
        self.password_label = QLabel('Password:')
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.connect_button = QPushButton('Connect To Server')
        self.connect_button.clicked.connect(self.connectToserver)
        self.browse_button = QPushButton('Browse Config')
        self.browse_button.clicked.connect(self.browseConfigFiles)
        self.push_config_button = QPushButton('Push Config')
        self.push_config_button.clicked.connect(self.pushConfig)
        passwordLayout.addWidget(self.password_label)
        passwordLayout.addWidget(self.password_input)
        passwordLayout.addWidget(self.connect_button)
        passwordLayout.addWidget(self.browse_button)
        passwordLayout.addWidget(self.push_config_button)
        mainLayout.addWidget(passwordWidget, 2, 0, 1, 3)  # Span 3 columns

        devicesConsoleLayout = QHBoxLayout()
        self.devices_table = QTableWidget(0, 3)  # Initially, the table will have 0 rows and 2 columns
        self.devices_table.setHorizontalHeaderLabels(['Connected Port','Hostname' ,'Device SerialNo'])
        self.devices_table.setSelectionBehavior(QTableWidget.SelectRows)
        devicesConsoleLayout.addWidget(self.devices_table)

        self.logTextBox = QTextEdit()
        self.logTextBox.setReadOnly(True)
        self.logTextBox.setText("Active Console\n")  # Set initial text
        devicesConsoleLayout.addWidget(self.logTextBox, 1)  # The '1' gives it a stretch factor to take up remaining space

        # Create a QWidget to hold the QHBoxLayout, then add it to the mainLayout
        devicesConsoleWidget = QWidget()
        devicesConsoleWidget.setLayout(devicesConsoleLayout)
        mainLayout.addWidget(devicesConsoleWidget, 3, 0, 1, 3)  # Span 3 columns

        container = QWidget()
        container.setLayout(mainLayout)
        self.setCentralWidget(container)

        container = QWidget()
        container.setLayout(mainLayout)
        self.setCentralWidget(container)

        container = QWidget()
        container.setLayout(mainLayout)
        self.setCentralWidget(container)

    def updateLogTextBox(self, message):
        self.logTextBox.append(message)
        # self.logTextBox.moveCursor(QTextCursor.End)  # Ensure the cursor is at the end of the text
        # self.logTextBox.insertHtml(message)
        # self.logTextBox.append(message)  # Insert the HTML-formatted message
        # self.logTextBox.insertPlainText('\n')  # Add a newline after the message
        # self.logTextBox.moveCursor(QTextCursor.End)

   
    def update_devices_table(self, data):
        port,hostname,serial_no = data
        row_position = self.devices_table.rowCount()
        self.devices_table.insertRow(row_position)

        # Create the table items for port and serial number
        port_item = QTableWidgetItem(port)
        hostname_item = QTableWidgetItem(hostname)
        serial_no_item = QTableWidgetItem(serial_no)

        # Set the items to be read-only by adjusting their flags
        port_item.setFlags(port_item.flags() & ~Qt.ItemIsEditable)
        hostname_item.setFlags(hostname_item.flags() & ~Qt.ItemIsEditable)
        serial_no_item.setFlags(serial_no_item.flags() & ~Qt.ItemIsEditable)

        # Add the items to the table
        self.devices_table.setItem(row_position, 0, port_item)
        self.devices_table.setItem(row_position, 1, hostname_item)
        self.devices_table.setItem(row_position, 2, serial_no_item)


    def debug_output(self,ssh_shell):
        output = ssh_shell.recv(5000).decode("utf-8")
        return output.strip()
          

    def connectToserver(self):
        
        server_ip = self.server_ip_input.text().strip()
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not all([server_ip, username, password]):
            self.showWarning("Please fill in all the required fields before pushing the config!")
            return

        self.main_process_thread = MainProcessThread(server_ip, username, password)
        self.main_process_thread.update_signal.connect(self.updateLogTextBox)
        self.main_process_thread.update_table_signal.connect(self.update_devices_table)  # Add this line
        self.main_process_thread.start()
        
    
    def browseConfigFiles(self):
        # This line opens the file dialog and filters for .txt, .cfg, and .xlsx files
        file_names, _ = QFileDialog.getOpenFileNames(self, "Select Config File", "", "Config Files (*.txt *.cfg *.xlsx);;All Files (*)")
        
        if file_names:
            # If a file is selected, do something with it. For example, store the file path in a class variable or print it.
            self.selected_config_files = file_names
            for file_name in file_names:
                self.logger.info(f"Selected config file: {file_name}")


      
    def pushConfig(self):
        #selected_ports = self.getSelectedPortsAndSerials()
        selected_ports = self.getSelectedPortsAndHostnames()
        if not self.selected_config_files or not selected_ports:
            self.updateLogTextBox("Please select configuration files and ports before pushing the config.")
            return

        device_config_map = self.match_config_files_to_devices()  # Get the map of hostnames to config file paths
        self.thread = DeviceConfigThread(self.server_ip_input.text().strip(),
                                        self.username_input.text().strip(),
                                        self.password_input.text().strip(),
                                        device_config_map,  # Pass the map instead of the list
                                        selected_ports)
        self.thread.update_signal.connect(self.updateLogTextBox)
        self.thread.start()



    def getSelectedPortsAndHostnames(self):
        selected_ports_and_hostnames = []
        for selectionRange in self.devices_table.selectedRanges():
            for row in range(selectionRange.topRow(), selectionRange.bottomRow() + 1):
                port = self.devices_table.item(row, 0).text()  # Adjust port_column_index as necessary
                hostname = self.devices_table.item(row, 1).text()  # Adjust hostname_column_index as necessary
                selected_ports_and_hostnames.append((port, hostname))
        return selected_ports_and_hostnames





    def match_config_files_to_devices(self):
        device_config_map = {}  # Map of hostname to config file path
        for file_path in self.selected_config_files:
            hostname = self.parse_hostname_from_filename(file_path)  # Implement this function based on your file naming convention
            for row in range(self.devices_table.rowCount()):
                table_hostname = self.devices_table.item(row, 1).text()  # Assuming hostname is in the second column
                if hostname == table_hostname:
                    if hostname not in device_config_map:  # Assuming one config file per hostname
                        device_config_map[hostname] = file_path
                    break  # Stop searching after the first match
        return device_config_map

    

    def parse_hostname_from_filename(self,filename):
        base_name = os.path.basename(filename)  # Get the filename without the directory path
        hostname = base_name.split('_')[0]  # Assuming the format is hostname-DATE.txt
        return hostname




    def showWarning(self, message):
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Warning)
        msgBox.setText(message)
        msgBox.setWindowTitle('Warning')
        msgBox.setStandardButtons(QMessageBox.Ok)
        msgBox.exec_()


class MainProcessThread(QThread):     #this class is being use for Connect to Server and get Port Number and Serial Number
    update_signal = pyqtSignal(str)
    update_table_signal = pyqtSignal(tuple)
    prompt_detected_signal = pyqtSignal(object)
    ssh_shell_created = pyqtSignal(object)

    def __init__(self, server_ip, username, password, parent=None):
        super(MainProcessThread, self).__init__(parent)
        self.server_ip = server_ip
        self.username = username
        self.password = password
        #self.excel_path = excel_path

    # def debug_output(self,ssh_shell):
    #     output = ssh_shell.recv(5000).decode("utf-8")
    #     return output.strip()    
    def debug_output(self,ssh_shell):
    # Wait for data to be available
        time.sleep(2)
        output = ""
        while True:
            if ssh_shell.recv_ready():
                output += ssh_shell.recv(1024).decode('utf-8')
                time.sleep(0.5)  # Allow time for data to accumulate in the buffer
            else:
                break  # Exit the loop if there's no more data to read
        return output    



    def run(self):
        try:
            self.update_signal.emit("Connecting to the Server...")
            with paramiko.SSHClient() as ssh_client:
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh_client.connect(hostname=self.server_ip, username=self.username, password=self.password)
                ssh_shell = ssh_client.invoke_shell()
                time.sleep(2)

                self.update_signal.emit("Starting configuration process...")
                ssh_shell.send("pmshell\r")
                time.sleep(2)
                output = self.debug_output(ssh_shell)

                pattern = r'Port (\d+)'
                active_ports = re.findall(pattern, output)

                if not active_ports:
                    self.update_signal.emit("No active ports found.")
                    return

                self.update_signal.emit('Active ports: ' + ', '.join(active_ports))
                #hostname_pattern = r"\n(\S+)>"
                hostname_pattern = r"(\S+)[>#]\s*$"

                for port in active_ports:
                    port_specific_username = f"{self.username}:port{port}"
                    self.update_signal.emit(f"Connecting to device on port {port}...")

                    # Re-initialize the SSH client for each port connection
                    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    ssh_client.connect(hostname=self.server_ip, username=port_specific_username, password=self.password)
                    ssh_shell = ssh_client.invoke_shell()
                    time.sleep(2)

                    # Clear the buffer and send a newline to get the prompt
                    self.debug_output(ssh_shell)  # Clear any existing output
                    ssh_shell.send("\r")
                    time.sleep(1)  # Wait for the prompt to appear
                    prompt_output = self.debug_output(ssh_shell)
                    #print(f"Prompt output for port {port}:\n{prompt_output}")  # Debug print

                    hostname_match = re.search(hostname_pattern, prompt_output)
                    if hostname_match:
                        hostname = hostname_match.group(1).strip()  # Strip in case of any whitespace
                        self.update_signal.emit(f"Hostname: {hostname} for Port: {port}")
                    else:
                        self.update_signal.emit(f"Hostname not found for Port: {port}")
                        hostname = "Unknown"

                    # ssh_shell.send("enable\r")
                    # time.sleep(1)
                    ssh_shell.send("sh inventory\r")
                    time.sleep(5)  # Wait for the output
                    final_output = self.debug_output(ssh_shell)
                    #print(f"Final output for port {port}:\n{final_output}")  # Debug print

                    sn_pattern = r'SN:\s+([^\s,]+)'
                    sn_match = re.search(sn_pattern, final_output)
                    if sn_match:
                        sn_value = sn_match.group(1)
                    else:
                        self.update_signal.emit(f"No SN found for Port: {port}")
                        sn_value = "Unknown"

                    # Emit the data to update the table
                    self.update_table_signal.emit((port, hostname, sn_value))

                    # Cleanly exit from the device session
                    ssh_shell.send("exit\r")
                    time.sleep(1)  # Ensure command 'exit' is processed
                    ssh_client.close()
                # Re-initialize for the next port, if there is one
                    ssh_client = paramiko.SSHClient()
                    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        except Exception as e:
            self.update_signal.emit(f"Error encountered: {str(e)}")
        finally:
            ssh_client.close()
            self.update_signal.emit("SSH client closed")

     
    def handle_avocent_console_getdetails(self,ssh_shell):
        self.update_signal.emit("This is Avocent console")
        self.update_signal.emit("Starting configuration process...")
        # ssh_client = paramiko.SSHClient()
        # ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:                      
            ssh_shell.send("cd access\r ls\r")
            time.sleep(2)
            output_raw = str(self.debug_output(ssh_shell))
            self.update_signal.emit("My output: " + output_raw)

            # Capture all lines from the command output, starting from the fourth line
            output = [element.strip() for element in output_raw.strip().split('\n')[3:]]

            self.update_signal.emit("output: " + str(output))

            matches_with_output = []
            for port in output:
                #ssh_shell = ssh_client.invoke_shell()
                #time.sleep(2)  # Wait for the initial shell to be ready

                self.update_signal.emit(f"Connecting to port: {port}")
                ssh_shell.send("cd access\r")
                time.sleep(2)
                comm = "connect " + str(port)
                # print('comm:', comm)
                ssh_shell.send(comm)
                ssh_shell.send("\r")
                time.sleep(2)
                ssh_shell.send(self.password)
                time.sleep(2)
                ssh_shell.send("\r")
                time.sleep(2)
                ssh_shell.send("\r")
                time.sleep(2)
                ssh_shell.send(f"connect {port}\n")
                time.sleep(2)  # Adjust sleep time as needed
                ssh_shell.send("show inventory\r")
                time.sleep(2)
                final_output_raw = self.debug_output(ssh_shell)

                # Regular expressions to match PID and SN lines
                #pid_pattern = r'PID: (.*?)\s*,'
                sn_pattern = r'SN:\s+([^\s,]+)'

                # Searching for PID and SN values
                #pid_match = re.search(pid_pattern, final_output_raw)
                sn_match = re.search(sn_pattern, final_output_raw)
                #pid_value = pid_match.group(1) if pid_match else None
                sn_value = sn_match.group(1) if sn_match else None

                #if pid_value and sn_value:
                if sn_value:
                    matches_with_output.append((port, sn_value))
                    self.update_table_signal.emit((port, sn_value))  

                ssh_shell.send('\x1A')  # Control+Z ASCII code
                time.sleep(5)

                    # Navigate back to the access directory
                ssh_shell.send("cd ..\n")
                time.sleep(2)
        except Exception as e:
            self.update_signal.emit(f"Error encountered: {str(e)}")
        finally:
            ssh_shell.close()
            self.update_signal.emit("SSH client closed")



class DeviceConfigThread(QThread):   #this class is being use for push the config to the devices.
    update_signal = pyqtSignal(str)

    def __init__(self, server_ip, username, password,device_config_map,selected_ports,parent=None):
        QThread.__init__(self, parent)
        self.server_ip = server_ip
        self.username = username
        self.password = password
        #self.config_files = config_files  # List of file paths selected by the user
        self.selected_ports = selected_ports
        self.device_config_map = device_config_map
        #self.port_file_mapping = port_file_mapping
        print(device_config_map)

    def debug_output(self,ssh_shell):
        output = ssh_shell.recv(5000).decode("utf-8")
        return output.strip()
    
    # Assuming other parts of your class definition remain the same

    def run(self):
        try:
            self.update_signal.emit("Connecting to the Server...")

            for port, hostname in self.selected_ports:  # Assuming selected_ports includes (port, hostname) tuples
                with paramiko.SSHClient() as ssh_client:
                    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    formatted_port = f"port{int(port):02d}"
                    self.update_signal.emit(f"Connecting to device on port {formatted_port}...")

                    port_specific_username = f"{self.username}:{formatted_port}"
                    ssh_client.connect(hostname=self.server_ip, username=port_specific_username, password=self.password, look_for_keys=False, allow_agent=False)
                    transport = ssh_client.get_transport()
                    transport.set_keepalive(30)
                    ssh_shell = ssh_client.invoke_shell()
                    time.sleep(5)
                    ssh_shell.send('\r')
                    time.sleep(2)

                    if hostname in self.device_config_map:
                        config_file = self.device_config_map[hostname]
                        config_file_name = os.path.basename(config_file)

                        self.update_signal.emit(f"For port {formatted_port}, hostname '{hostname}', sending config file '{config_file_name}'")

                        with open(config_file, 'r') as file:
                            device_config = file.readlines()

                        batch_size = 100  # Adjust based on your device's capability
                        for i in range(0, len(device_config), batch_size):
                            command_batch = ''.join(device_config[i:i+batch_size]) + '\n'
                            self.update_signal.emit(f"Sending batch of commands to port {port} from file {config_file}")
                            ssh_shell.send(command_batch)
                            ssh_shell.send("\r")
                            time.sleep(2)  # Wait for the commands to be processed

                            # Wait for the device to process the batch and display the prompt
                            while not ssh_shell.recv_ready():
                                time.sleep(5)  # Adjust as needed
                            response = ""
                            while True:
                                if ssh_shell.recv_ready():
                                    response += ssh_shell.recv(4096).decode('utf-8')
                                   
                                    
                                    if response.strip().endswith('#'):  
                                        break
                                else:
                                    ssh_shell.send("\r")
                                    time.sleep(2)

                            self.update_signal.emit(f"Batch processed, response: {response}")

                self.update_signal.emit("Configuration process completed")

        except Exception as e:
            self.update_signal.emit(f"Error encountered: {str(e)}")
        finally:
            if ssh_client:
                ssh_client.close()  # Ensure the client is closed even if an exception occurs
            self.update_signal.emit("SSH client closed")

    
    def handle_avocent_console(self, ssh_shell):
        self.update_signal.emit("This is Avocent console")
        self.update_signal.emit("Starting configuration process...")
        ssh_client = paramiko.SSHClient()
        #ssh_client = paramiko.Channel()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            ssh_client.connect(hostname=self.server_ip, username=self.username, password=self.password)
            for port in self.selected_ports:
                ssh_shell = ssh_client.invoke_shell()
                time.sleep(2)  # Wait for the initial shell to be ready

                for config_file in self.config_files:
                    with open(config_file, 'r') as file:
                        device_config = file.readlines()

                    self.update_signal.emit(f"Connecting to port: {port}")
                    ssh_shell.send("cd access\r")
                    time.sleep(2)
                    comm = "connect " + str(port)
                    # print('comm:', comm)
                    ssh_shell.send(comm)
                    ssh_shell.send("\r")
                    time.sleep(2)
                    ssh_shell.send(self.password)
                    time.sleep(2)
                    ssh_shell.send("\r")
                    time.sleep(2)
                    ssh_shell.send("\r")
                    time.sleep(2)
                    ssh_shell.send(f"connect {port}\n")
                    time.sleep(2)  # Adjust sleep time as needed

                    batch_size = 100  # Number of commands to group together, adjust based on your device's capability
                    for i in range(0, len(device_config), batch_size):
                        # Join a batch of commands into a single string separated by newline characters
                        command_batch = ''.join(device_config[i:i+batch_size]) + '\n'
                        self.update_signal.emit(f"Sending batch of commands to port {port} from file {config_file}")
                        ssh_shell.send(command_batch)
                        time.sleep(2)  # Adjust sleep time as needed for the device to process the batch

                        # Optionally, read the output after each batch to ensure commands are being processed
                        if ssh_shell.recv_ready():
                            response = ssh_shell.recv(4096).decode('utf-8')
                            self.update_signal.emit(f"Response: {response}")

                    # Exit the session with the escape sequence <enter>~.
                    #ssh_shell.send("\n~.\n")
                    ssh_shell.send('\x1A')  # Control+Z ASCII code
                    time.sleep(5)

                    # Navigate back to the access directory
                    ssh_shell.send("cd ..\n")
                    time.sleep(2)
                    # ssh_shell.send("cd ..\n")
                    # time.sleep(1)
                    # ssh_shell.send("cd access\n")
                    # time.sleep(1)

                    self.update_signal.emit(f"Disconnected from device on port {port}.")
        

            self.update_signal.emit("Configuration process completed")
        except Exception as e:
            self.update_signal.emit(f"Error encountered: {str(e)}")
        finally:
            ssh_client.close()
            self.update_signal.emit("SSH client closed")



if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWin = SaveLocationDialog()
    mainWin.show()
    sys.exit(app.exec_())