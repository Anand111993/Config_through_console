import sys
import openpyxl
import datetime
from datetime import datetime
import json
from PyQt5.QtWidgets import QApplication,QGridLayout,QMainWindow, QVBoxLayout,QTableWidget,QInputDialog,QTextEdit,QPushButton,QMessageBox , QWidget, QFileDialog, QLineEdit, QLabel, QCheckBox
from PyQt5.QtCore import QThread, pyqtSignal,pyqtSlot
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
from datetime import datetime
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5 import QtWidgets
from PyQt5.QtCore import QTimer,Qt
from PyQt5.QtGui import QTextCursor, QColor, QTextCharFormat
from qc_code_and_commands import qc_commands, platform_codes
from qc_report_generator import generate_qc_report

log_dir_path = None
summary_file_path = None





class QTextBoxLogger(logging.Handler, QObject):   #This  class for UPdate Signals in Active Console Sever 
    log_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        QObject.__init__(self)

    def emit(self, record):
        msg = self.format(record)
        self.log_signal.emit(msg)

class SaveLocationDialog(QMainWindow):  #This class used for GUI design and button handler
    update_signal = pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self.threads = []
        self.port_batches = []
        self.current_batch_index = 0  # Keep track of the current batch being processed
        self.active_threads = 0  # Counter for active threads in the current batch

        self.setWindowTitle('CTC_Application')
        self.setGeometry(100, 100, 800, 600)  # Adjust the window size as needed
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        log_handler = QTextBoxLogger()
        self.logger.addHandler(log_handler)
        self.log_file = None # Initialize log_file attribute
        self.error_file = None # Initialize error_file attribute
        self.selected_config_files = []
        self.check_button = QCheckBox('Save Logs')
        self.check_button.setEnabled(False)  # Disable the check_button by default
        self.check_button.clicked.connect(self.openLogPathDialog)  # Connect the clicked signal to openLogPathDialog slot

        self.initUI()

        log_handler.log_signal.connect(self.updateLogTextBox)

        # Disable buttons initially
        self.get_config_button.setEnabled(False)
        self.get_reload_button.setEnabled(False)

        # Connect signals
        self.Switch_username.textChanged.connect(self.validate_input)
        self.Switch_password_input.textChanged.connect(self.validate_input)
    
    

    def initUI(self):
        mainLayout = QGridLayout()

        # Server IP Section
        self.server_ip_label = QLabel('Server IP:')
        self.Switch_username_label = QLabel('Switch_Username:')
        self.server_ip_input = QLineEdit()
        self.server_ip_input.textChanged.connect(self.onInputTextChanged)  # Connect textChanged signal
        self.Switch_username = QLineEdit()
        mainLayout.addWidget(self.server_ip_label, 0, 0)  # Row 0, Column 0
        mainLayout.addWidget(self.server_ip_input, 0, 1)  # Row 0, Column 1
        mainLayout.addWidget(self.Switch_username_label, 0, 2)  # Row 0, Column 2
        mainLayout.addWidget(self.Switch_username, 0, 3)  # Row 0, Column 3

        # Username Section
        self.username_label = QLabel('Username:')
        self.Switch_password_label = QLabel('Switch_Password:')
        self.username_input = QLineEdit()
        self.username_input.textChanged.connect(self.onInputTextChanged) # Connect textChanged signal

        self.Switch_password_input = QLineEdit()
        self.Switch_password_input.setEchoMode(QLineEdit.Password)
        self.get_config_button = QPushButton('Get Running Config')
        self.get_config_button.clicked.connect(self.getRunningConfig)
        self.get_reload_button = QPushButton('Reload Device')
        self.get_reload_button.clicked.connect(self.reload_device)
        mainLayout.addWidget(self.username_label, 1, 0)  # Row 1, Column 0
        mainLayout.addWidget(self.username_input, 1, 1)  # Row 1, Column 1
        mainLayout.addWidget(self.Switch_password_label, 1, 2)  # Row 1, Column 2
        mainLayout.addWidget(self.Switch_password_input, 1, 3)  # Row 1, Column 3
        mainLayout.addWidget(self.get_config_button, 1, 4)  # Row 1, Column 4
        mainLayout.addWidget(self.get_reload_button, 0, 4)  # Row 1, Column 5

        # Password Section
        self.password_label = QLabel('Password:')
        self.password_input = QLineEdit()
        self.password_input.textChanged.connect(self.onInputTextChanged) 
        self.password_input.setEchoMode(QLineEdit.Password)
        self.connect_button = QPushButton('Connect To Server')
        self.connect_button.clicked.connect(self.connectToserver)
        self.browse_button = QPushButton('Browse Config')
        self.browse_button.clicked.connect(self.browseConfigFiles)
        self.push_config_button = QPushButton('Push Config')
        self.push_config_button.clicked.connect(self.pushConfig)
        self.qc_check_button = QPushButton('Get QC Checked')
        #self.qc_check_button.clicked.connect(self.getQCchecked)
        mainLayout.addWidget(self.password_label, 2, 0)  # Row 2, Column 0
        mainLayout.addWidget(self.password_input, 2, 1)  # Row 2, Column 1
        mainLayout.addWidget(self.connect_button, 2, 2)  # Row 2, Column 2
        mainLayout.addWidget(self.browse_button, 2, 3)  # Row 2, Column 3
        mainLayout.addWidget(self.push_config_button, 2, 4)  # Row 2, Column 4
        #mainLayout.addWidget(self.qc_check_button, 2, 5)

        # Check Button (After Password) and QC button 
        self.check_button = QCheckBox('Save Logs')
        self.check_button.clicked.connect(self.openLogPathDialog)
        mainLayout.addWidget(self.check_button, 3, 0, 1, 2)  # Row 3, Column 0, Span 1 row and 2 columns
        self.qc_check_button = QPushButton('Get QC Checked')
        self.qc_check_button.clicked.connect(self.getQCchecked)
        mainLayout.addWidget(self.qc_check_button,3, 4 , 1, 2)
        # Devices Console Section
        devicesConsoleLayout = QHBoxLayout()
        self.devices_table = QTableWidget(0, 2)  # Initially, the table will have 0 rows and 3 columns
        self.devices_table.setHorizontalHeaderLabels(['Connected Port', 'Hostname'])
        self.devices_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.devices_table.horizontalHeader().setStretchLastSection(True)
        devicesConsoleLayout.addWidget(self.devices_table)

        self.logTextBox = QTextEdit()
        self.logTextBox.setReadOnly(True)
        self.logTextBox.setText("Active Console\n")  # Set initial text
        devicesConsoleLayout.addWidget(self.logTextBox, 1)  # The '1' gives it a stretch factor to take up remaining space

        # Create a QWidget to hold the QHBoxLayout, then add it to the mainLayout
        devicesConsoleWidget = QWidget()
        devicesConsoleWidget.setLayout(devicesConsoleLayout)
        mainLayout.addWidget(devicesConsoleWidget, 4, 0, 1, 5)  # Span 5 columns

        # Set the main layout
        container = QWidget()
        container.setLayout(mainLayout)
        self.setCentralWidget(container)


    @pyqtSlot()
    def onInputTextChanged(self):
        # Enable Connect button only if all three input fields have values
        if self.server_ip_input.text() and self.username_input.text() and self.password_input.text():
            self.connect_button.setEnabled(True)
        else:
            self.connect_button.setEnabled(False)
    
    def validate_input(self):
        # Enable buttons if both input fields have values, otherwise disable them
        if self.Switch_username.text() and self.Switch_password_input.text():
            self.get_config_button.setEnabled(True)
            self.get_reload_button.setEnabled(True)
        else:
            self.get_config_button.setEnabled(False)
            self.get_reload_button.setEnabled(False)

    def openLogPathDialog(self):
        if self.check_button.isChecked():
            selected_log_dir_path = QFileDialog.getExistingDirectory(self, "Select Log Directory", "")
            if selected_log_dir_path:
                global log_dir_path
                log_dir_path = selected_log_dir_path
                QMessageBox.information(self, "Log Directory", f"Log directory is selected: {log_dir_path}")
                # Enable push_config_button, connect_button, and browse_button when log_dir_path is selected
                #self.update_signal.emit(self, "Log Directory", f"Log directory is selected: {log_dir_path}")
                self.push_config_button.setEnabled(True)
                self.connect_button.setEnabled(True)
                self.browse_button.setEnabled(True)
                # Enable check_button when log_dir_path is selected
                self.check_button.setEnabled(True)
            else:
                QMessageBox.information(self, "Log Directory", "Log directory selection is canceled, please select again")
                # Uncheck the check_button since no log directory is selected
                self.check_button.setChecked(False)
                # Disable push_config_button, connect_button, and browse_button if log_dir_path is not selected
                self.push_config_button.setEnabled(False)
                self.connect_button.setEnabled(False)
                self.browse_button.setEnabled(False)
                # Disable check_button if log_dir_path is not selected
                self.check_button.setEnabled(True)
        else:
            QMessageBox.information(self, "Log Directory", "Log directory selection is canceled.")
            # Disable push_config_button, connect_button, and browse_button if log_dir_path is not selected
            self.push_config_button.setEnabled(False)
            self.connect_button.setEnabled(False)
            self.browse_button.setEnabled(False)

    




    def updateLogTextBox(self, message, log_file=None, error_file=None):
        self.logTextBox.append(message)



    def clear_devices_table(self):
        # Clear all the contents of the table but keep the rows (headers remain intact)
        self.devices_table.clearContents()

        # If you also want to reset the row count to 0, effectively removing all rows
        self.devices_table.setRowCount(0)


    def update_devices_table(self, data):
        # Unpack the data tuple into port and hostname
        port, hostname = data

        # Determine the new row position
        row_position = self.devices_table.rowCount()
        self.devices_table.insertRow(row_position)

        # Create the table items for port and hostname
        port_item = QTableWidgetItem(port)
        hostname_item = QTableWidgetItem(hostname)

        # Set the items to be read-only
        port_item.setFlags(port_item.flags() & ~Qt.ItemIsEditable)
        hostname_item.setFlags(hostname_item.flags() & ~Qt.ItemIsEditable)

        # Add the items to the table at the specified row and column
        self.devices_table.setItem(row_position, 0, port_item)  # Column 0 for 'Connected Port'
        self.devices_table.setItem(row_position, 1, hostname_item)  # Column 1 for 'Hostname'



    def debug_output(self,ssh_shell):
        output = ssh_shell.recv(5000).decode("utf-8")
        return output.strip()
          

    def connectToserver(self):
            # Check if the devices table has entries and clear if not empty
            if self.update_devices_table:  # Assuming this is a method to update a table, you might need a different check here
                self.clear_devices_table()  # You might need to define this method to clear the devices table


            # Check if log directory path is selected
            if not log_dir_path:
                self.showWarning("Please select a log directory path before connecting to the server!")
                return

            server_ip = self.server_ip_input.text().strip()
            username = self.username_input.text().strip()
            password = self.password_input.text().strip()

            if not all([server_ip, username, password]):
                self.showWarning("Please fill in all the required fields before connecting to the server!")
                return

            self.main_process_thread = MainProcessThread(server_ip, username, password)
            self.main_process_thread.update_signal.connect(self.updateLogTextBox)
            self.main_process_thread.update_table_signal.connect(self.update_devices_table)
            self.main_process_thread.start()
   
    def browseConfigFiles(self):
        # This line opens the file dialog and filters for .txt, .cfg, and .xlsx files
        file_names, _ = QFileDialog.getOpenFileNames(self, "Select Config File", "", "Config Files (*.txt *.cfg *.xlsx);;All Files (*)")
        
        if file_names:
            # If a file is selected, do something with it. For example, store the file path in a class variable or print it.
            self.selected_config_files = file_names
            for file_name in file_names:
                self.logger.info(f"Selected config file: {file_name}")

    # def pushConfig(self):
    #     selected_ports = self.getSelectedPortsAndHostnames()
    #     print('ports: ', selected_ports)
        
    #     if not selected_ports:
    #         self.updateLogTextBox("Please select ports before fetching the config.")
    #         return

    #     if not self.selected_config_files:
    #         self.showWarning("Please select at least one configuration file.")
    #         return

    #     device_config_map = self.match_config_files_to_devices()  # Get the map of hostnames to config file paths
        
    #     # Assuming save_directory is chosen here or set elsewhere in your class
    #     # save_directory = self.chooseSaveDirectory()  # Implement this method to let the user choose a directory
        
    #     save_directory = log_dir_path

    #     if not save_directory:
    #         self.updateLogTextBox("No save directory specified for fetching the configurations.")
    #         return
        
    #     self.thread = DeviceConfigThread(
    #         server_ip=self.server_ip_input.text().strip(),
    #         username=self.username_input.text().strip(),
    #         password=self.password_input.text().strip(),
    #         selected_ports=selected_ports,
    #         save_directory=save_directory,
    #         switch_username = self.Switch_username.text().strip(),
    #         switch_password = self.Switch_password_input.text().strip(),
    #         device_config_map = device_config_map
    #     )
        
    #     self.thread.update_signal.connect(self.updateLogTextBox)
    #     self.thread.start()



    # def pushConfig(self):
    #     selected_ports = self.getSelectedPortsAndHostnames()
    #     print('ports: ', selected_ports)

    #     if not selected_ports:
    #         self.updateLogTextBox("Please select ports before pushing the config.")
    #         return

    #     if not self.selected_config_files:
    #         self.showWarning("Please select at least one configuration file.")
    #         return

    #     device_config_map = self.match_config_files_to_devices()
    #     save_directory = log_dir_path

    #     if not save_directory:
    #         self.updateLogTextBox("No save directory specified for saving the configurations.")
    #         return

    #     for port, hostname in selected_ports:
    #         if hostname in device_config_map:
    #             config_file = device_config_map[hostname]

    #             thread = DeviceConfigThread(
    #                 server_ip=self.server_ip_input.text().strip(),
    #                 username=self.username_input.text().strip(),
    #                 password=self.password_input.text().strip(),
    #                 selected_ports=[(port, hostname)],
    #                 save_directory=save_directory,
    #                 switch_username=self.Switch_username.text().strip(),
    #                 switch_password=self.Switch_password_input.text().strip(),
    #                 device_config_map={hostname: config_file}
    #             )

    #             # Store the thread reference in the list
    #             self.threads.append(thread)

    #             # Optional: Connect the thread's finished signal to a cleanup method
    #             thread.finished.connect(lambda thread=thread: self.onThreadFinished(thread))


    #             thread.update_signal.connect(self.updateLogTextBox)
    #             thread.start()

    # def onThreadFinished(self, thread):
    #     # Optional cleanup method called when a thread finishes
    #     # Remove the thread reference from the list
    #     self.threads.remove(thread)

    #     # Additional cleanup actions can be performed here


  
    def pushConfig(self):
        self.push_config_button.setDisabled(True)  # Disable the button
        selected_ports = self.getSelectedPortsAndHostnames()

        device_config_map = self.match_config_files_to_devices()
        save_directory = log_dir_path  # Assuming this is defined elsewhere in your class

        # Split the ports into batches of 5
        self.port_batches = [selected_ports[i:i + 5] for i in range(0, len(selected_ports), 5)]
        
        # Start processing the first batch if any
        if self.port_batches:
            self.processBatch(self.port_batches[self.current_batch_index], device_config_map,save_directory)

    def processBatch(self, ports_batch, device_config_map,save_directory):
        self.active_threads = len(ports_batch)  # Set the active threads counter to the size of the current batch
        for port, hostname in ports_batch:
            if hostname in device_config_map:
                config_file = device_config_map[hostname]

                thread = DeviceConfigThread(
                    server_ip=self.server_ip_input.text().strip(),
                    username=self.username_input.text().strip(),
                    password=self.password_input.text().strip(),
                    selected_ports=[(port, hostname)],
                    save_directory = save_directory,
                    switch_username=self.Switch_username.text().strip(),
                    switch_password=self.Switch_password_input.text().strip(),
                    device_config_map={hostname: config_file}
                )

                thread.finished.connect(lambda: self.onThreadFinished(device_config_map, save_directory))
                self.threads.append(thread)
                thread.update_signal.connect(self.updateLogTextBox)
                thread.start()

    def onThreadFinished(self):
        print("A thread has finished processing.")
        self.active_threads -= 1
        finished_thread = self.sender()  # Get the thread that just finished

        if finished_thread in self.threads:
            self.threads.remove(finished_thread)  # Cleanup finished thread
            finished_thread.deleteLater()  # Free resources properly

        print(f"Remaining active threads: {self.active_threads}")

        if self.active_threads == 0:
            self.current_batch_index += 1
            if self.current_batch_index >= len(self.port_batches):
                self.push_config_button.setEnabled(True)
                print("All batches have been processed.")
            else:
                print(f"Starting batch {self.current_batch_index + 1}")
                self.processBatch(self.port_batches[self.current_batch_index], self.device_config_map, self.save_directory)


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
    
    def getRunningConfig(self):
        selected_ports = self.getSelectedPortsAndHostnames()
        # print('ports: ', selected_ports)
        
        if not selected_ports:
            self.updateLogTextBox("Please select ports before fetching the config.")
            return
        
        # Assuming save_directory is chosen here or set elsewhere in your class
        save_directory = self.chooseSaveDirectory()  # Implement this method to let the user choose a directory
        
        if not save_directory:
            self.updateLogTextBox("No save directory specified for fetching the configurations.")
            return
        
        self.thread = ConfigFetchThread(
            server_ip=self.server_ip_input.text().strip(),
            username=self.username_input.text().strip(),
            password=self.password_input.text().strip(),
            selected_ports=selected_ports,
            save_directory=save_directory,
            switch_username = self.Switch_username.text().strip(),
            switch_password = self.Switch_password_input.text().strip()
        )
        
        self.thread.update_signal.connect(self.updateLogTextBox)
        self.thread.start()


    def reload_device(self):
        selected_ports = self.getSelectedPortsAndHostnames()
        
        if not selected_ports:
            self.updateLogTextBox("Please select ports before fetching the config.")
            return
        
        self.thread = ReloadDeviceThread(
            server_ip=self.server_ip_input.text().strip(),
            username=self.username_input.text().strip(),
            password=self.password_input.text().strip(),
            selected_ports=selected_ports,
            switch_username = self.Switch_username.text().strip(),
            switch_password = self.Switch_password_input.text().strip()
            
        )
        
        self.thread.update_signal.connect(self.updateLogTextBox)
        self.thread.start()



    def chooseSaveDirectory(self):
        # Open a dialog to choose a directory
        options = QFileDialog.Options()
        options |= QFileDialog.DontResolveSymlinks | QFileDialog.ShowDirsOnly
        directory = QFileDialog.getExistingDirectory(self, "Choose Save Directory", "", options=options)

        if directory:
            # If a directory is selected, print or use the directory path as needed
            # print(f"Selected directory: {directory}")
            return directory
        else:
            # If no directory is selected (dialog is cancelled), handle accordingly
            # print("No directory selected.")
            return None



    def showWarning(self, message):
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Warning)
        msgBox.setText(message)
        msgBox.setWindowTitle('Warning')
        msgBox.setStandardButtons(QMessageBox.Ok)
        msgBox.exec_()


    def getQCchecked(self):
        selected_ports = self.getSelectedPortsAndHostnames()
        # print('ports: ', selected_ports)
        
        if not selected_ports:
            self.updateLogTextBox("Please select ports before fetching the config.")
            return
        
        # Assuming save_directory is chosen here or set elsewhere in your class
        save_directory = self.chooseSaveDirectory()  # Implement this method to let the user choose a directory

        if not save_directory:
            self.updateLogTextBox("No save directory specified for fetching the configurations.")
            return
        
        self.thread = GetQCThread(
            server_ip=self.server_ip_input.text().strip(),
            username=self.username_input.text().strip(),
            password=self.password_input.text().strip(),
            selected_ports=selected_ports,
            save_directory=save_directory,
            switch_username = self.Switch_username.text().strip(),
            switch_password = self.Switch_password_input.text().strip()
        )
        
        self.thread.update_signal.connect(self.updateLogTextBox)
        self.thread.start()
            

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
  
   
    def debug_output(self, ssh_shell, timeout=2):
        end_time = time.time() + timeout
        output = ''
        while time.time() < end_time:
            if ssh_shell.recv_ready():
                output += ssh_shell.recv(1024).decode('utf-8')
                # Reset the timer because we're still receiving data
                end_time = time.time() + timeout
            else:
                # If no data is available, wait a bit before checking again
                time.sleep(0.1)
        return output





    def run(self):
        try:
            self.update_signal.emit("Connecting to the Server...")
            with paramiko.SSHClient() as ssh_client:
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh_client.connect(hostname=self.server_ip, username=self.username, password=self.password)
                ssh_shell = ssh_client.invoke_shell()
                time.sleep(2)

                self.update_signal.emit("Fetching the Active Ports.......")
                ssh_shell.send("pmshell\r")
                time.sleep(2)
                output = self.debug_output(ssh_shell)

                pattern = r'(\d+): (?:Port (\d+)|(\w+))'
                matches = re.findall(pattern, output)
                active_ports = [(number, name.strip()) for number, port, name in matches if name]
                active_ports = [f"{number}: {name}" for number, name in active_ports]
                print(active_ports)
                if not active_ports:
                    self.update_signal.emit("No active ports found.")
                    return

                self.update_signal.emit('Active ports: ' + ', '.join(active_ports))

                for port_info in active_ports:
                    port, hostname = port_info.split(": ")
                    print(port)
                    # Emit the data to update the table with port and hostname only
                    self.update_table_signal.emit((port, hostname))  # Using "N/A" for sn_value since we're not retrieving it

        except Exception as e:
            self.update_signal.emit(f"Error encountered: {str(e)}")
        finally:
            ssh_client.close()
            self.update_signal.emit("SSH client closed")




class DeviceConfigThread(QThread):
    update_signal = pyqtSignal(str)

    def __init__(self, server_ip, username, password, selected_ports, save_directory, switch_username, switch_password, device_config_map, parent=None):
        super().__init__(parent)
        self.server_ip = server_ip
        self.username = username
        self.password = password
        self.selected_ports = selected_ports
        self.save_directory = save_directory
        self.switch_username = switch_username
        self.switch_password = switch_password
        self.device_config_map = device_config_map
        self.ssh_client = None  # Initialize SSH client variable

    def read_shell_output(self, ssh_shell, timeout=2):
        """ Efficiently reads SSH output without blocking the UI. Windows-compatible. """
        output = ""
        end_time = time.time() + timeout
        while time.time() < end_time:
            if ssh_shell.recv_ready():
                output += ssh_shell.recv(4096).decode('utf-8')
                end_time = time.time() + timeout  # Reset timeout when receiving data
            else:
                QThread.msleep(200)  # Prevents high CPU usage, uses Qt's msleep
        return output

    def wait_for_prompt(self, ssh_shell, hostname_pattern, timeout=10):
        """ Waits for device prompt after sending a command. """
        compiled_pattern = re.compile(hostname_pattern)
        output = ''
        end_time = time.time() + timeout
        while time.time() < end_time:
            if ssh_shell.recv_ready():
                received = ssh_shell.recv(4096).decode('utf-8')
                output += received
                if compiled_pattern.search(output):
                    return output, True
            QThread.msleep(100)  # Prevents UI freezing
        return output, False  # Return False if timeout occurs

    def run(self):
        try:
            self.update_signal.emit("Connecting to the Server...")

            timestamp = datetime.now().strftime('%d_%m_%Y_%H_%M_%S')
            summary_file_path = os.path.join(self.save_directory, f'summary_log_{timestamp}.log')

            # Create summary log file
            with open(summary_file_path, "w") as log:
                log.write("Summary Report:\n")

            for port, hostname in self.selected_ports:
                device_username = "admin"
                device_password = "T-Mobile123"
                formatted_port = f"port{int(port):02d}"
                self.update_signal.emit(f"Connecting to device on {formatted_port}...")

                device_directory = os.path.join(self.save_directory, f'{hostname}_{timestamp}')
                os.makedirs(device_directory, exist_ok=True)  # Efficient directory creation
                self.update_signal.emit(f"Created log directory for {hostname}.")

                log_file = os.path.join(device_directory, "log_file.log")
                error_file = os.path.join(device_directory, "error.log")

                with open(log_file, "w") as log:
                    log.write(f"Logs for {hostname}\n")

                with open(error_file, "w") as error:
                    error.write(f"Errors for {hostname}\n")

                # Establish SSH Connection
                self.ssh_client = paramiko.SSHClient()
                self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                port_specific_username = f"{self.username}:{formatted_port}"

                try:
                    self.ssh_client.connect(hostname=self.server_ip, username=port_specific_username,
                                            password=self.password, look_for_keys=False, allow_agent=False, timeout=10)
                except paramiko.AuthenticationException:
                    self.update_signal.emit(f"Authentication failed for {hostname}")
                    continue
                except paramiko.SSHException as e:
                    self.update_signal.emit(f"SSH error for {hostname}: {str(e)}")
                    continue
                except Exception as e:
                    self.update_signal.emit(f"Unexpected error for {hostname}: {str(e)}")
                    continue

                ssh_shell = self.ssh_client.invoke_shell()
                QThread.msleep(2000)
                ssh_shell.send("\r")
                QThread.msleep(2000)

                hostname_pattern = r"(\S+)[>#](\s*|\s+\S*)\Z"
                initial_output, prompt_detected = self.wait_for_prompt(ssh_shell, hostname_pattern)

                if not prompt_detected:
                        if "Username:" in initial_output or "login:" in initial_output:
                            self.update_signal.emit("Username/login prompt detected")
                            ssh_shell.send(f"{device_username}\r")
                            QThread.msleep(1000)  # Wait a bit for the password prompt to appear
                            ssh_shell.send(f"{device_password}\r")
                            output, prompt_detected = self.wait_for_prompt(ssh_shell, hostname_pattern, timeout=15)

                            if "Login incorrect" in output:
                                self.update_signal.emit(f"Incorrect username/password, Can't Push the config for {hostname}")
                                self.ssh_client.close()
                                continue

                            if not prompt_detected:
                                self.update_signal.emit(f"Hostname prompt not detected after login for port {port}. Skipping.")
                                self.ssh_client.close()
                                
                                continue

                        else:
                            self.update_signal.emit(f"No username/login prompt detected for port {port}. Skipping.")
                            self.ssh_client.close()
                            continue

                if hostname in self.device_config_map:
                    config_file = self.device_config_map[hostname]
                    ssh_shell.send("conf t\r")
                    QThread.msleep(2000)

                    with open(config_file, 'r') as file:
                        device_config = file.readlines()

                    batch_size = 100  # Adjust based on network device's capability
                    log = open(log_file, "a")
                    error_log = open(error_file, "a")

                    for i in range(0, len(device_config), batch_size):
                        command_batch = ''.join(device_config[i:i+batch_size]) + '\n'
                        self.update_signal.emit(f"Sending batch of commands to {hostname}...")
                        ssh_shell.send(command_batch)
                        ssh_shell.send("\r")
                        QThread.msleep(2000)

                        response = self.read_shell_output(ssh_shell)
                        log.write(response)

                        # Log errors if found
                        if '%' in response or "% Invalid input detected" in response:
                            error_log.write(response)

                    log.close()
                    error_log.close()

                    self.ssh_client.close()
                    self.update_signal.emit(f"Configuration completed for {hostname}.")

            self.update_signal.emit("All selected hosts configured successfully.")
        
        except Exception as e:
            self.update_signal.emit(f"Error: {str(e)}")

        finally:
            if self.ssh_client:
                self.ssh_client.close()
            self.update_signal.emit("SSH client closed")




















# class DeviceConfigThread(QThread):   #this class is being use for push the config to the devices.
#     update_signal = pyqtSignal(str)

#     def __init__(self, server_ip, username, password, selected_ports, save_directory,switch_username,switch_password, device_config_map,parent=None):
#         super().__init__(parent)
#         self.server_ip = server_ip
#         self.username = username
#         self.password = password
#         self.selected_ports = selected_ports
#         self.save_directory = save_directory
#         self.switch_username = switch_username
#         self.switch_password = switch_password
#         self.device_config_map = device_config_map


#     def debug_output(self, ssh_shell, timeout=0.5):
#             output = ""
#             end_time = time.time() + timeout
#             while time.time() < end_time:
#                 if ssh_shell.recv_ready():
#                     output += ssh_shell.recv(1024).decode('utf-8')
#                     end_time = time.time() + timeout  # Extend waiting time if data is still coming in
#                 else:
#                     time.sleep(0.1)  # Short sleep to prevent high CPU usage
#             return output

#     def wait_for_hostname_prompt(self, ssh_shell, hostname_pattern, timeout=15):
#         compiled_pattern = re.compile(hostname_pattern)
#         end_time = time.time() + timeout
#         output = ''
#         while time.time() < end_time:
#             if ssh_shell.recv_ready():
#                 received = ssh_shell.recv(1024).decode('utf-8')
#                 output += received
#                 if compiled_pattern.search(output):
#                     self.update_signal.emit("Hostname prompt detected")
#                     return True  # Hostname prompt found
#             else:
#                 time.sleep(0.1)  # If no data, wait a bit before retrying
#         self.update_signal.emit("Hostname prompt not detected within the timeout")
#         return False  # Hostname prompt not found within the timeout period

    

#     def read_shell_output(self, ssh_shell, timeout=2):
#         output = ""
#         end_time = time.time() + timeout
#         while time.time() < end_time:
#             if ssh_shell.recv_ready():  # Check if data is available
#                 data = ssh_shell.recv(4096).decode('utf-8')
#                 output += data
#                 end_time = time.time() + timeout  # Reset timeout when receiving data
#             else:
#                 QThread.msleep(200)  # Prevent CPU overuse, small wait instead of time.sleep()
#         return output




#     def run(self):
#         try:
#             self.update_signal.emit("Connecting to the Server...")

#             if log_dir_path:
#                 timestamp = datetime.now().strftime('%d_%m_%Y_%H_%M_%S')
#                 global summary_file_path
#                 summary_file_path = os.path.join(log_dir_path, f'summary_log_{timestamp}.log')
#                 with open(summary_file_path, "w") as log:
#                     log.write(f"Summary Report:")
#             else:
#                 self.update_signal.emit("Log directory path not provided.")

#             for port, hostname in self.selected_ports:
#                 device_username = "admin"
#                 device_password = "T-Mobile123"
#                 formatted_port = f"port{int(port):02d}"
#                 self.update_signal.emit(f"Connecting to device on port {formatted_port}...")

#                 device_directory = os.path.join(log_dir_path, f'{hostname}_{timestamp}')
#                 if not os.path.exists(device_directory):
#                     os.makedirs(device_directory)
#                 self.update_signal.emit(f"Created directory '{device_directory}' for device '{hostname}'.")

#                 log_file = os.path.join(device_directory, "log_file.log")
#                 error_file = os.path.join(device_directory, "error.log")

#                 with open(log_file, "w") as log:
#                     log.write(f"Logs for device: {hostname}\n")

#                 with open(error_file, "w") as error:
#                     error.write(f"Errors for device: {hostname}\n")

#                 with paramiko.SSHClient() as ssh_client:
#                     ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#                     port_specific_username = f"{self.username}:{formatted_port}"
#                     ssh_client.connect(hostname=self.server_ip, username=port_specific_username, password=self.password, look_for_keys=False, allow_agent=False)

#                     ssh_shell = ssh_client.invoke_shell()
#                     QThread.msleep(2000)
#                     ssh_shell.send('\r')
#                     QThread.msleep(2000)

#                     hostname_pattern = r"(\S+)[>#](\s*|\s+\S*)\Z"
#                     initial_output, prompt_detected = self.wait_for_prompt(ssh_shell, hostname_pattern)

#                     if not prompt_detected:
#                         if "Username:" in initial_output or "login:" in initial_output:
#                             self.update_signal.emit("Username/login prompt detected")
#                             ssh_shell.send(f"{device_username}\r")
#                             QThread.msleep(1000)  # Wait a bit for the password prompt to appear
#                             ssh_shell.send(f"{device_password}\r")
#                             output, prompt_detected = self.wait_for_prompt(ssh_shell, hostname_pattern, timeout=15)

#                             if "Login incorrect" in output:
#                                 self.update_signal.emit(f"Incorrect username/password, Can't Push the config for {hostname}")
#                                 ssh_client.close()
#                                 continue

#                             if not prompt_detected:
#                                 self.update_signal.emit(f"Hostname prompt not detected after login for port {port}. Skipping.")
#                                 ssh_client.close()
#                                 continue

#                         else:
#                             self.update_signal.emit(f"No username/login prompt detected for port {port}. Skipping.")
#                             ssh_client.close()
#                             continue


#                     if hostname in self.device_config_map:
#                         config_file = self.device_config_map[hostname]
#                         ssh_shell.send("conf t\r")
#                         QThread.msleep(2000)
#                         #self.send_config_in_batches(ssh_shell, config_file, port)
#                         with open(config_file, 'r') as file:
#                             device_config = file.readlines()

#                         batch_size = 100  # Adjust based on your device's capability
#                         for i in range(0, len(device_config), batch_size):
#                             command_batch = ''.join(device_config[i:i+batch_size]) + '\n'
#                             self.update_signal.emit(f"Sending batch of commands to port {port} from file {config_file}")
#                             ssh_shell.send(command_batch)
#                             ssh_shell.send("\r")
#                             QThread.msleep(2000)  # Wait for the commands to be processed

#                             # Wait for the device to process the batch and display the prompt
#                             while not ssh_shell.recv_ready():
#                                 QThread.msleep(5000)  # Adjust as needed
#                             response = ""
#                             while True:
#                                 if ssh_shell.recv_ready():
#                                     response += ssh_shell.recv(4096).decode('utf-8')
                                   
                                    
#                                     if response.strip().endswith('#'):  
#                                         break
#                                 else:
#                                     ssh_shell.send("\r")
#                                     QThread.msleep(2000)

#                             self.update_signal.emit(f"Batch processed, response: {response}")

#                             with open(log_file, "a") as log:
#                                 log.write(response)

#                             if error_file:
#                                 self.error_file = error_file
#                                 # Write lines containing '%' or '^' to error log file
#                                 with open(error_file, "a") as error_log:
#                                     lines = response.split('\n')
#                                     for i, line in enumerate(lines):
#                                         if '%' in line or "% Invalid input detected at '^' marker." in line:
#                                             # Write the previous line if it exists and is not a duplicate
#                                             if i > 0 and lines[i-1] != line:
#                                                 error_log.write(lines[i-1] + '\n')
#                                             # Write the current line
#                                             error_log.write(line + '\n')
#                                             # Write the next line if it exists and is not a duplicate
#                                             if i < len(lines) - 1 and lines[i+1] != line:
#                                                 error_log.write(lines[i+1] + '\n')

#                             if error_file and summary_file_path:
#                                 self.error_file = error_file
#                                 # Check the number of lines in error.log
#                                 with open(error_file, "r") as error_log:
#                                     lines = error_log.readlines()  # Read all lines
#                                     num_lines = len(lines)
#                                     first_line = lines[0].strip() if lines else ""  # Read the first line from the list of lines
#                                     # print("first_line: ", first_line)
#                                     last_word = first_line.split()[-1] if first_line else ""
#                                     # print("last_word: ", last_word)

#                                     # Determine success or failure based on the number of lines
#                                     summary = f"{last_word} - Errors encountered, see log ({self.error_file})" if num_lines > 1 else f"{last_word} - Config completed"
#                                     # print("summary: ", summary)
                                    
#                                     # Write the summary to the summary file
#                                     if summary_file_path:
#                                         # Read existing contents of summary.log
#                                         with open(summary_file_path, "r") as summary_file:
#                                             existing_lines = summary_file.readlines()
#                                         # Flag to check if a matching line is found
#                                         found_matching_line = False
#                                         # Replace any line with the same last_word
#                                         updated_lines = []
#                                         for line in existing_lines:
#                                             if line.strip().startswith(last_word):
#                                                 # Replace with the new summary
#                                                 updated_lines.append(summary)
#                                                 found_matching_line = True
#                                             else:
#                                                 updated_lines.append(line.strip())
#                                         # If no matching line found, append the new summary line
#                                         if not found_matching_line:
#                                             updated_lines.append(summary)
#                                         # Write the updated lines back to summary.log
#                                         with open(summary_file_path, "w") as summary_file:
#                                             summary_file.write("\n".join(updated_lines) + '\n')



#                         # ssh_shell.send("copy running-config startup-config\r")
#                         # ssh_shell.send("\r")  # Confirm the save operation if prompted
#                         # time.sleep(2)    
#                     ssh_client.close()
#                     self.update_signal.emit(f"Configuration process completed for Host {hostname}.")
#                 self.update_signal.emit("Configuration process completed for all selected Host.")
#         except Exception as e:
#             self.update_signal.emit(f"Error encountered: {str(e)}")

#         finally:
#             if ssh_client:
#                 ssh_client.close()  # Ensure the client is closed even if an exception occurs
#             self.update_signal.emit("SSH client closed")    
   


    def send_config_in_batches(self, ssh_shell, config_file, port):
        config_file_name = os.path.basename(config_file)
        self.update_signal.emit(f"Sending config file '{config_file_name}' to port {port}")

        with open(config_file, 'r') as file:
            device_config = file.readlines()

        batch_size = 100  # Adjust based on your device's capability
        for i in range(0, len(device_config), batch_size):
            command_batch = ''.join(device_config[i:i+batch_size]) + '\n'
            command_batch_1 = command_batch.strip()
            self.update_signal.emit(f"Sending batch of commands to port {port} from file {config_file}")
            ssh_shell.send(command_batch_1)
            #ssh_shell.send("\r")
            QThread.msleep(2000)  # Wait for the commands to be processed

            # Wait for the device to process the batch and display the prompt
            while not ssh_shell.recv_ready():
                QThread.msleep(5000)  # Adjust as needed
            response = ""
            while True:
                if ssh_shell.recv_ready():
                    response += ssh_shell.recv(4096).decode('utf-8')
                    if response.strip().endswith('#'):  
                        break
                else:
                    ssh_shell.send("\r")
                    QThread.msleep(2000)

            self.update_signal.emit(f"Batch processed, response: {response}")


class ConfigFetchThread(QThread):    #this class is being used for fatching configuration of the device.
    update_signal = pyqtSignal(str)

    def __init__(self, server_ip, username, password, selected_ports, save_directory,switch_username,switch_password, parent=None):
        super().__init__(parent)
        self.server_ip = server_ip
        self.username = username
        self.password = password
        self.selected_ports = selected_ports
        self.save_directory = save_directory
        self.switch_username = switch_username
        self.switch_password = switch_password
        #self.device_config_map = device_config_map
        # print(switch_password)
        # print(switch_username) 
    
    def debug_output(self, ssh_shell, timeout=0.5):
        output = ""
        end_time = time.time() + timeout
        while time.time() < end_time:
            if ssh_shell.recv_ready():
                output += ssh_shell.recv(1024).decode('utf-8')
                end_time = time.time() + timeout  # Extend waiting time if data is still coming in
            else:
                time.sleep(0.1)  # Short sleep to prevent high CPU usage
        return output
    
    def wait_for_prompt(self, ssh_shell, hostname_pattern, timeout=10):
        compiled_pattern = re.compile(hostname_pattern)
        output = ''
        end_time = time.time() + timeout
        while time.time() < end_time:
            if ssh_shell.recv_ready():
                received = ssh_shell.recv(1024).decode('utf-8')
                output += received
                if compiled_pattern.search(output):
                    return output, True
                end_time = time.time() + timeout
            else:
                time.sleep(0.1)
        return output, False

    
    # def read_shell_output(self, ssh_shell, timeout=2):
    #     output = ""
    #     end_time = time.time() + timeout
    #     while time.time() < end_time:
    #         if ssh_shell.recv_ready():
    #             output += ssh_shell.recv(65535).decode('utf-8')  # Increase buffer size for large outputs
    #             end_time = time.time() + timeout  # Extend waiting time if data is still coming in
    #         else:
    #             time.sleep(0.1)  # Short sleep to prevent high CPU usage
    #     return output


    # def send_shell_commands(self, ssh_shell, commands, timeout=2):
    #     for cmd in commands:
    #         ssh_shell.send(f"{cmd}\r")
    #         time.sleep(timeout)


    def run(self):
        try:
            self.update_signal.emit("Connecting to the Server...")

            for port, hostname in self.selected_ports:
                #device_username = "admin"
                #device_password = "WWTwwt1!"  # Assuming selected_ports includes (port, hostname) tuples
                with paramiko.SSHClient() as ssh_client:
                    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    formatted_port = f"port{int(port):02d}"
                    self.update_signal.emit(f"Connecting to {hostname} on port {port}...")

                    port_specific_username = f"{self.username}:{formatted_port}"
                    ssh_client.connect(hostname=self.server_ip, username=port_specific_username, password=self.password, look_for_keys=False, allow_agent=False)
                    transport = ssh_client.get_transport()
                    transport.set_keepalive(30)
                    ssh_shell = ssh_client.invoke_shell()
                    time.sleep(5)
                    ssh_shell.send('\r')
                    time.sleep(2)
        
                    #hostname_pattern = r"\s*(\S+)#"
                    hostname_pattern = r"(\S+)[>#](\s*|\s+\S*)\Z"
                    initial_output, prompt_detected = self.wait_for_prompt(ssh_shell, hostname_pattern)

                    if not prompt_detected:
                        if "Username:" in initial_output or "login:" in initial_output:
                            self.update_signal.emit("Username/login prompt detected")
                            ssh_shell.send(f"{self.switch_username}\r")
                            time.sleep(1)  # Wait a bit for the password prompt to appear
                            ssh_shell.send(f"{self.switch_password}\r")
                            output, prompt_detected = self.wait_for_prompt(ssh_shell, hostname_pattern, timeout=15)

                            if "Login incorrect" in output:
                                self.update_signal.emit(f"Incorrect username/password, Can't take the back-up for {hostname}")
                                ssh_client.close()
                                continue

                            if not prompt_detected:
                                self.update_signal.emit(f"Hostname prompt not detected after login for port {port}. Skipping.")
                                ssh_client.close()
                                continue

                        else:
                            self.update_signal.emit(f"No username/login prompt detected for port {port}. Skipping.")
                            ssh_client.close()
                            continue


                    match = re.search(hostname_pattern, initial_output)
                    if match:
                        hostname_prompt = match.group(0)
                        if hostname_prompt.endswith('>'):
                            self.update_signal.emit("Sending enable command")
                            ssh_shell.send("enable\r")
                            time.sleep(1)
                            enable_output, enable_prompt_detected = self.wait_for_prompt(ssh_shell, hostname_pattern, timeout=5)
                            if "Password:" in enable_output:
                                self.update_signal.emit("Sending enable password")
                                ssh_shell.send("NGUeWs@eKufI!G6C8!Z1u1PuI\r")
                                output, prompt_detected = self.wait_for_prompt(ssh_shell, hostname_pattern, timeout=15)
                                if not prompt_detected:
                                    self.update_signal.emit(f"Enable mode prompt not detected for {hostname}. Skipping.")
                                    ssh_client.close()
                                    return
                            elif not enable_prompt_detected:
                                self.update_signal.emit(f"Enable mode prompt not detected for {hostname}. Skipping.")
                                ssh_client.close()
                                return

                    self.update_signal.emit(f"Successfully connected to {hostname}") 

                    # Proceed with further actions after successful prompt detection
                    #self.update_signal.emit(f"Hostname prompt detected for {hostname} on port {port}. Proceeding with actions.")

                    self.update_signal.emit(f"Taking Backup of {hostname} ...")

                    # ssh_shell.send('enable\r')
                    # time.sleep(1) 
                    ssh_shell.send('terminal length 0\r')
                    time.sleep(1)  # Wait for the command to be processed

                    # Send the 'show run' command
                    ssh_shell.send('show run\r')
                    time.sleep(2)  # Wait for the command to be processed

                    ssh_shell.send('exit\r')
                    time.sleep(1)

                    # Capture the response
                    response = ""
                    last_read_time = time.time()

                    # Keep reading until no more data or timeout after last read
                    while True:
                        if ssh_shell.recv_ready():
                            data = ssh_shell.recv(65535).decode('utf-8')  # Increase buffer size
                            response += data
                            last_read_time = time.time()
                        elif time.time() - last_read_time > 5:  # 5 seconds timeout after last read
                            break
                        else:
                            time.sleep(0.1) 

                    # Save the response to a file
                    #date_str = datetime.datetime.now().strftime("%Y-%m-%d")
                    date_str = datetime.now().strftime("%Y-%m-%d")
                    filename = f"{hostname}_{date_str}.txt"
                    filepath = os.path.join(self.save_directory, filename)
                    with open(filepath, 'w') as file:
                        file.write(response)
                    self.update_signal.emit(f"Successfully fetched and saved config for {hostname}.")
                    ssh_client.close()
                    

        except Exception as e:
            self.update_signal.emit(f"Failed to process port {port} for {hostname}: {e}")

        self.update_signal.emit("Completed processing selected ports.")        


class ReloadDeviceThread(QThread):    #this class is being used for relod the device.
    update_signal = pyqtSignal(str)

    def __init__(self, server_ip, username, password,switch_username, switch_password,selected_ports,parent=None):
        super().__init__(parent)
        self.server_ip = server_ip
        self.username = username
        self.password = password
        self.selected_ports = selected_ports
        self.switch_username = switch_username
        self.switch_password = switch_password

    def send_shell_commands(self, ssh_shell, commands, timeout=2):
        for cmd in commands:
            ssh_shell.send(f"{cmd}\r")
            time.sleep(timeout)

    def debug_output(self, ssh_shell, timeout=0.5):
            output = ""
            end_time = time.time() + timeout
            while time.time() < end_time:
                if ssh_shell.recv_ready():
                    output += ssh_shell.recv(1024).decode('utf-8')
                    end_time = time.time() + timeout  # Extend waiting time if data is still coming in
                else:
                    time.sleep(0.1)  # Short sleep to prevent high CPU usage
            return output
    
    def wait_for_prompt(self, ssh_shell, hostname_pattern, timeout=10):
        compiled_pattern = re.compile(hostname_pattern)
        output = ''
        end_time = time.time() + timeout
        while time.time() < end_time:
            if ssh_shell.recv_ready():
                received = ssh_shell.recv(1024).decode('utf-8')
                output += received
                if compiled_pattern.search(output):
                    return output, True
                end_time = time.time() + timeout
            else:
                time.sleep(0.1)
        return output, False


    def wait_for_hostname_prompt(self, ssh_shell, hostname_pattern, timeout=15):
        compiled_pattern = re.compile(hostname_pattern)
        end_time = time.time() + timeout
        output = ''
        while time.time() < end_time:
            if ssh_shell.recv_ready():
                received = ssh_shell.recv(1024).decode('utf-8')
                output += received
                if compiled_pattern.search(output):
                    self.update_signal.emit("Hostname prompt detected")
                    return True  # Hostname prompt found
            else:
                time.sleep(0.1)  # If no data, wait a bit before retrying
        self.update_signal.emit("Hostname prompt not detected within the timeout")
        return False  # Hostname prompt not found within the timeout period



    def read_shell_output(self, ssh_shell, timeout=2):
        output = ""
        end_time = time.time() + timeout
        while time.time() < end_time:
            if ssh_shell.recv_ready():
                output += ssh_shell.recv(1024).decode('utf-8')
                end_time = time.time() + timeout  # Extend waiting time if data is still coming in
            else:
                time.sleep(0.1)  # Short sleep to prevent high CPU usage
        return output

    def run(self):
        try:
            self.update_signal.emit("Connecting to the Server...")

            for port, hostname in self.selected_ports:
                with paramiko.SSHClient() as ssh_client:
                    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    formatted_port = f"port{int(port):02d}"
                    self.update_signal.emit(f"Connecting to {hostname} on port {port}...")

                    port_specific_username = f"{self.username}:{formatted_port}"
                    ssh_client.connect(hostname=self.server_ip, username=port_specific_username, password=self.password, look_for_keys=False, allow_agent=False)
                    transport = ssh_client.get_transport()
                    transport.set_keepalive(30)
                    ssh_shell = ssh_client.invoke_shell()
                    time.sleep(5)
                    ssh_shell.send('\r')
                    time.sleep(2)
                    hostname_pattern = r"(\S+)[>#](\s*|\s+\S*)$"

                    output = ""     # Initialize output variable
                    # Ensure we have a prompt before continuing
                    while not ssh_shell.recv_ready():
                        time.sleep(0.1)
                    output += ssh_shell.recv(9999).decode('utf-8')

                    if "Username:" in output or "login:" in output:
                        self.update_signal.emit("Username/login prompt detected")
                        
                        # Send username and password
                        ssh_shell.send(f"{self.switch_username}\r")
                        time.sleep(1)  # Wait a bit for the password prompt to appear
                        ssh_shell.send(f"{self.switch_password}\r")
                        time.sleep(1)  # Wait for a moment after sending the password
                        
                        # Read output to check if we're at the prompt
                        output = self.read_shell_output(ssh_shell)

                        # Check if the login is incorrect after providing the switch username and password
                        if "Login incorrect" in output:
                            self.update_signal.emit(f"Incorrect username/password, Can't reload the device {hostname}")
                            continue  # Skip to the next iteration if the login is incorrect
                        
                        # Wait for the hostname prompt
                        hostname_pattern = r"(\S+)[>#](\s*|\s+\S*)$"
                        compiled_pattern = re.compile(hostname_pattern)
                        end_time = time.time() + 15  # 15 seconds timeout
                        prompt_detected = False

                        output = ''  # Initialize output variable to accumulate received data
                        while time.time() < end_time:
                            if ssh_shell.recv_ready():
                                # Decode and strip carriage returns from the received data
                                received = ssh_shell.recv(1024).decode('utf-8').replace('\r', '')
                                output += received
                                # Check for hostname prompt in the accumulated output
                                if compiled_pattern.search(output):
                                    self.update_signal.emit("Hostname prompt detected")
                                    prompt_detected = True
                                    break  # Exit loop once the hostname prompt is detected
                            else:
                                time.sleep(0.1)
                        if not prompt_detected:
                            # Hostname prompt not found within the timeout
                            self.update_signal.emit("Hostname prompt not detected after login.")


                    match = re.search(hostname_pattern, output)
                    if match:
                        hostname_prompt = match.group(0)
                        if hostname_prompt.endswith('>'):
                            self.update_signal.emit("Sending enable command")
                            ssh_shell.send("enable\r")
                            time.sleep(1)
                            enable_output, enable_prompt_detected = self.wait_for_prompt(ssh_shell, hostname_pattern, timeout=5)
                            if "Password:" in enable_output:
                                self.update_signal.emit("Sending enable password")
                                ssh_shell.send("NGUeWs@eKufI!G6C8!Z1u1PuI\r")
                                output, prompt_detected = self.wait_for_prompt(ssh_shell, hostname_pattern, timeout=15)
                                if not prompt_detected:
                                    self.update_signal.emit(f"Enable mode prompt not detected for {hostname}. Skipping.")
                                    ssh_client.close()
                                    return
                            elif not enable_prompt_detected:
                                self.update_signal.emit(f"Enable mode prompt not detected for {hostname}. Skipping.")
                                ssh_client.close()
                                return

                    self.update_signal.emit(f"Successfully connected to {hostname}")        
                            
                    time.sleep(1)
                    ssh_shell.send('reload\r')
                    time.sleep(5)  # Give some time for the prompt to appear

                    # Initial waiting for prompt
                    #response = ssh_shell.recv(65535).decode('utf-8')
                    response = ssh_shell.recv(65535).decode('utf-8', errors='replace')

                    if "This command will reboot the system. (y/n)?  [n]" or "Proceed with reload? [confirm]" in response:
                        ssh_shell.send('y\r')  # Send 'yes' to save configuration
                        time.sleep(1)
                        ssh_shell.send('\r')  # Send enter to confirm reload
                        time.sleep(1)
                    # Continue to capture the rest of the response
                    last_read_time = time.time()
                    while True:
                        if ssh_shell.recv_ready():
                            data = ssh_shell.recv(65535).decode('utf-8')
                            response += data
                            last_read_time = time.time()
                        elif time.time() - last_read_time > 5:
                            break
                        else:
                            time.sleep(0.1)

                    self.update_signal.emit(f"Successfully Pushed reload command To {hostname}.")

        except Exception as e:
            self.update_signal.emit(f"Failed to Pushed reload command To {hostname}: {e}")

        self.update_signal.emit("Completed reload command to the selected Devices.")
   


class GetQCThread(QThread):    #this class is being used for QC CHECKS.
    update_signal = pyqtSignal(str)

    def __init__(self, server_ip, username, password, selected_ports, save_directory,switch_username,switch_password, parent=None):
        super().__init__(parent)
        self.server_ip = server_ip
        self.username = username
        self.password = password
        self.selected_ports = selected_ports
        self.save_directory = save_directory
        self.switch_username = switch_username
        self.switch_password = switch_password
        #self.device_config_map = device_config_map
        # print(switch_password)
        # print(switch_username) 
    
    def debug_output(self, ssh_shell, timeout=0.5):
        output = ""
        end_time = time.time() + timeout
        while time.time() < end_time:
            if ssh_shell.recv_ready():
                output += ssh_shell.recv(1024).decode('utf-8')
                end_time = time.time() + timeout  # Extend waiting time if data is still coming in
            else:
                time.sleep(0.1)  # Short sleep to prevent high CPU usage
        return output


    def wait_for_prompt(self, ssh_shell, hostname_pattern, timeout=10):
        compiled_pattern = re.compile(hostname_pattern)
        output = ''
        end_time = time.time() + timeout
        while time.time() < end_time:
            if ssh_shell.recv_ready():
                received = ssh_shell.recv(1024).decode('utf-8')
                output += received
                if compiled_pattern.search(output):
                    return output, True
                end_time = time.time() + timeout
            else:
                time.sleep(0.1)
        return output, False


    def read_shell_output(self, ssh_shell, timeout=2):
        output = ""
        end_time = time.time() + timeout
        while time.time() < end_time:
            if ssh_shell.recv_ready():
                output += ssh_shell.recv(1024).decode('utf-8')
                end_time = time.time() + timeout  # Extend waiting time if data is still coming in
            else:
                time.sleep(0.1)  # Short sleep to prevent high CPU usage
        return output

    def send_shell_commands(self, ssh_shell, commands, timeout=2):
        for cmd in commands:
            ssh_shell.send(f"{cmd}\r")
            time.sleep(timeout)

    def run(self):       
            try:
                self.update_signal.emit("Connecting to the Server...")

                # Initialize the summary report file
                date_str = datetime.now().strftime("%Y-%m-%d")
                summary_report_path = os.path.join(self.save_directory, f"QC_Summary_Report_{date_str}.txt")

                # Initialize the summary report file with headers
                with open(summary_report_path, 'w') as summary_file:
                    summary_file.write("Device QC Summary Report......\n\n\n")
                    summary_file.write("Hostname\t\tQC Status\n")
                    summary_file.write("-" * 50 + "\n")


                for port, hostname in self.selected_ports:
                    #device_username = "admin"
                    #device_password = "WWTwwt1!"  # Assuming selected_ports includes (port, hostname) tuples
                    with paramiko.SSHClient() as ssh_client:
                        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                        formatted_port = f"port{int(port):02d}"
                        self.update_signal.emit(f"Connecting to {hostname} on port {port}...")

                        port_specific_username = f"{self.username}:{formatted_port}"
                        ssh_client.connect(hostname=self.server_ip, username=port_specific_username, password=self.password, look_for_keys=False, allow_agent=False)
                        transport = ssh_client.get_transport()
                        transport.set_keepalive(30)
                        ssh_shell = ssh_client.invoke_shell()
                        time.sleep(5)
                        ssh_shell.send('\r')
                        time.sleep(2)
                        #output = self.read_shell_output(ssh_shell)  # Assuming this method reads the SSH shell output
                        hostname_pattern = r"(\S+)[>#](\s*|\s+\S*)\Z"
                        initial_output, prompt_detected = self.wait_for_prompt(ssh_shell, hostname_pattern)

                        if not prompt_detected:
                            if "Username:" in initial_output or "login:" in initial_output:
                                self.update_signal.emit("Username/login prompt detected")
                                ssh_shell.send(f"{self.switch_username}\r")
                                time.sleep(1)  # Wait a bit for the password prompt to appear
                                ssh_shell.send(f"{self.switch_password}\r")
                                output, prompt_detected = self.wait_for_prompt(ssh_shell, hostname_pattern, timeout=15)

                                if "Login incorrect" in output:
                                    self.update_signal.emit(f"Incorrect username/password, Can't take the back-up for {hostname}")
                                    ssh_client.close()
                                    continue

                                if not prompt_detected:
                                    self.update_signal.emit(f"Hostname prompt not detected after login for port {port}. Skipping.")
                                    ssh_client.close()
                                    continue

                            else:
                                self.update_signal.emit(f"No username/login prompt detected for port {port}. Skipping.")
                                ssh_client.close()
                                continue

                        # Proceed with further actions after successful prompt detection
                        self.update_signal.emit(f"Hostname prompt detected for {hostname} on port {port}. Proceeding with actions.")

                        match = re.search(hostname_pattern, initial_output)
                        if match:
                            hostname_prompt = match.group(0)
                            if hostname_prompt.endswith('>'):
                                self.update_signal.emit("Sending enable command")
                                ssh_shell.send("enable\r")
                                time.sleep(1)
                                enable_output, enable_prompt_detected = self.wait_for_prompt(ssh_shell, hostname_pattern, timeout=5)
                                if "Password:" in enable_output:
                                    self.update_signal.emit("Sending enable password")
                                    ssh_shell.send("NGUeWs@eKufI!G6C8!Z1u1PuI\r")
                                    output, prompt_detected = self.wait_for_prompt(ssh_shell, hostname_pattern, timeout=15)
                                    if not prompt_detected:
                                        self.update_signal.emit(f"Enable mode prompt not detected for {hostname}. Skipping.")
                                        ssh_client.close()
                                        return
                                elif not enable_prompt_detected:
                                    self.update_signal.emit(f"Enable mode prompt not detected for {hostname}. Skipping.")
                                    ssh_client.close()
                                    return

                        self.update_signal.emit(f"Successfully connected to {hostname}")

                        commands_output = " "
                        command_outputs = {} 
                        qc_report = ""

                        for command in qc_commands:
                            self.update_signal.emit(f"Sending command: {command}")
                            ssh_shell.send(f"{command}\r")
                            time.sleep(2)


                            command_output = self.read_shell_output(ssh_shell)
                            commands_output += f"Command: {command}\n{command_output}\n\n"
                            command_outputs[command] = command_output

                        # Generate QC report for all collected command outputs
                        qc_report = generate_qc_report(hostname, command_outputs)  # Pass the dictionary to the function
                        # After executing all commands and generating the QC report, send the 'exit' command
                        self.update_signal.emit("Exiting the session...")
                        ssh_shell.send("exit\r")
                        time.sleep(1)  # Give some time for the session to close gracefully
                            

                        # Create a directory for the full report within the save_directory
                        report_dir_name = f"{hostname}_QC_full_report"
                        report_dir = os.path.join(self.save_directory, report_dir_name)
                        os.makedirs(report_dir, exist_ok=True)
                        
                        # Define file paths
                        date_str = datetime.now().strftime("%Y-%m-%d")
                        commands_output_file = os.path.join(report_dir, f"QC_commands_output_{date_str}.txt")
                        report_file = os.path.join(report_dir, f"QC_report_{date_str}.txt")



                        with open(commands_output_file, 'w') as file:
                            file.write(commands_output)
                
                        # Write the QC report to the file
                        with open(report_file, 'w') as file:
                            file.write(qc_report)   


                        # Analyze the QC report to determine overall QC status
                        qc_status = self.analyze_qc_report(qc_report)    

                        #qc_status = "Passed" if "QC Failed" not in qc_report else "Failed"
                            # Update the summary report with the hostname and QC status
                        with open(summary_report_path, 'a') as summary_file:
                            summary_file.write(f"{hostname}\t\t{qc_status}\n")

                        self.update_signal.emit(f"QC process completed for {hostname} with status: {qc_status}.")


                        self.update_signal.emit(f"Successfully fetched and saved config for {hostname}.")
                        ssh_shell.send(f"Exit\r")
                        ssh_client.close()
            except Exception as e:
                self.update_signal.emit(f"Failed to fetch config for {hostname}: {e}")

            self.update_signal.emit("Completed fetching configurations.")

    
    def analyze_qc_report(self,qc_report):
        """
        Analyze the QC report to determine the overall QC status.
        If 'QC Passed' is found for all checks that contain 'QC Passed' or 'QC Failed', return 'Passed',
        if 'Unable to determine' is found, return a message indicating manual check is needed,
        otherwise return 'Failed'.
        """
        # Define specific error messages or indicators
        unable_to_determine_indicator = "Unable to determine model or version"
        
        # Split the report into sections
        sections = qc_report.split('\n')[2:]
        
        # Check for any specific phrases that indicate a manual check is needed
        if any(unable_to_determine_indicator in section for section in sections):
            return f"QC feature is not integrated for this model; check manually."
        
        # Check for failure phrases
        for section in sections:
            if "QC Failed" in section:
                return "Failed"
        
        # If no failure conditions met, ensure every check contains 'QC Passed'
        if all("QC Passed" in section for section in sections if 'QC Passed' in section):
            return "Passed"
        
        # Default to 'Failed' if none of the above conditions are met
        return "Failed"



    



if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWin = SaveLocationDialog()
    mainWin.show()
    sys.exit(app.exec_())






