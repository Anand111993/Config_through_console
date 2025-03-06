import sys
import openpyxl
from PyQt5.QtWidgets import QApplication, QGridLayout,QMainWindow, QTextEdit,QPushButton,QMessageBox , QWidget, QFileDialog, QLineEdit, QLabel
from PyQt5.QtCore import QThread, pyqtSignal
import paramiko
import time
import re
import pandas as pd
import os
from netmiko import ConnectHandler
import time
import logging
from PyQt5.QtCore import pyqtSignal, QObject

EXCEL_PATH = None

class DeviceConfigThread(QThread):
    update_signal = pyqtSignal(str)

    def __init__(self, server_ip, username, password, parent=None):
        QThread.__init__(self, parent)
        self.server_ip = server_ip
        self.username = username
        self.password = password
    
    def debug_output(self,ssh_shell):
        output = ssh_shell.recv(5000).decode("utf-8")
        return output.strip()
    


    def run(self):
        self.update_signal.emit("Starting configuration process...")
        df = pd.read_excel(EXCEL_PATH, engine='openpyxl')
        df = df.dropna(subset=['Device Config'])
        table_data = df.to_dict(orient='records')
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            ssh_client.connect(hostname=self.server_ip, username=self.username, password=self.password)
            ssh_shell = ssh_client.invoke_shell()
            console_output = self.debug_output(ssh_shell)
            self.update_signal.emit("My text: " + console_output.strip())

            if console_output.strip() == '#':
                self.update_signal.emit("This is opengear console")
                try:
                    for row in table_data:
                        device_config = row["Device Config"]
                        port = row["active_port"]
                        device = {
                            'device_type': 'generic_termserver',
                            'ip': self.server_ip,
                            'username': self.username,
                            'password': self.password,
                        }
                        connection = ConnectHandler(**device)

                        self.update_signal.emit(f'Connected To Port: {port}')
                        self.update_signal.emit(str(device_config))

                        connection.write_channel("pmshell\r")
                        time.sleep(2)
                        connection.write_channel(str(port) + "\r")
                        time.sleep(2)
                        connection.write_channel("\r")
                        time.sleep(1)
                        connection.write_channel("enable\r")
                        time.sleep(1)
                        connection.write_channel("config t\r")
                        time.sleep(1)

                        # if isinstance(device_config, str):
                        #     for command in device_config.split("\n"):
                        #         self.update_signal.emit(f"Sending command: {command}")
                        #         response = self.send_command_and_wait_for_response(ssh_shell, command)
                        #         self.update_signal.emit(f"Response from device: {response}")
                        #     self.update_signal.emit('Configuration completed')
                        # #ssh_client.close()
                        # connection.disconnect()


                        if isinstance(device_config, str):
                            config_commands = device_config.split('\n')
                            for cmd in config_commands:
                                self.update_signal.emit(f"Sending command: {cmd}")
                                output = connection.send_command_timing(cmd, delay_factor=2)
                                self.update_signal.emit(output)

                            self.update_signal.emit(output)
                        connection.disconnect()
                        self.update_signal.emit(f'Disconnected from Port: {port}')

                except Exception as e:
                    self.update_signal.emit(f"Error: {e}")           
                    if connection:
                       connection.disconnect()
            else:

                self.update_signal.emit("This is avocent console")
                for row in table_data:
                    port = row["active_port"]
                    device_config = row["Device Config"]
                    device_username = row["device_username"]        # code change
                    # print('device_username: ', device_username)
                    device_password = row["device_password"]        # code change
                    # print('device_password: ', device_password)
                    enable_pass = row["enable_password"]
                    self.update_signal.emit(str(device_config))
                    ssh_client = paramiko.SSHClient()
                    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    ssh_client.connect(hostname=self.server_ip, username=self.username, password=self.password)
                    ssh_shell = ssh_client.invoke_shell()

                    # Navigate to the desired section
                    ssh_shell.send("cd access\r ls\r")
                    time.sleep(2)
                    comm = "connect " + str(port)
                    # print('comm:', comm)
                    ssh_shell.send(comm)
                    ssh_shell.send("\r")
                    time.sleep(2)
                    ssh_shell.send(self.password)
                    time.sleep(1)
                    ssh_shell.send("\r")
                    self.update_signal.emit(f"Connected To , {port}")
                    #print('Connected To ', port)
                    ssh_shell.send("\r")
                    time.sleep(2)
                    self.debug_output(ssh_shell)
                    
                    # print('device_username1: ', device_username)        # code change
                    ssh_shell.send(str(device_username))
                    ssh_shell.send("\r")
                    time.sleep(2)
                    
                    # print('device_password1: ', device_password)
                    ssh_shell.send(str(device_password))         # code change
                    
                    ssh_shell.send("\r")
                    time.sleep(2)
                    ssh_shell.send("enable\r")
                    time.sleep(1)
                    ssh_shell.send(str(enable_pass))
                    ssh_shell.send("\r")
                    time.sleep(2)
                    ssh_shell.send("Config t\r")
                    time.sleep(1)
                    
                    
                    # ...

                    if isinstance(device_config, str):
                        for command in device_config.split("\n"):
                            self.update_signal.emit(f"Sending command: {command}")

                            # Check if the command is a TFTP copy command
                            is_tftp_command = "copy tftp:" in command
                            if is_tftp_command:
                                # Exit from config mode before executing TFTP copy command
                                ssh_shell.send("end\r")
                                time.sleep(1)

                            ssh_shell.send(command + "\r")
                            time.sleep(1)

                            response, is_data_received = "", False
                            start_time = time.time()

                            # Adjust timeout based on the command type
                            timeout = 600 if is_tftp_command else 10

                            while True:
                                time.sleep(0.5)
                                if ssh_shell.recv_ready():
                                    response += ssh_shell.recv(1024).decode('utf-8')
                                    is_data_received = True
                                    start_time = time.time()  # Reset the timer on data receipt

                                    # Check for errors in the response
                                    if "%Error" in response or "Error opening socket" in response:
                                        self.update_signal.emit(f"Error detected: {response}")
                                        # Handle the error as needed (e.g., log, alert, terminate)
                                        break

                                if is_data_received and (time.time() - start_time) > timeout:
                                    break

                            self.update_signal.emit(f"Response from device: {response}")

                            # If an error was detected in TFTP command, decide on the action
                            if is_tftp_command and ("%Error" in response or "Error opening socket" in response):
                                # Example: Log and skip to the next command
                                self.update_signal.emit("Skipping to the next command due to error.")
                                continue

                            # If we had exited config mode to run TFTP, re-enter config mode
                            if is_tftp_command:
                                ssh_shell.send("Config t\r")
                                time.sleep(1)

                        self.update_signal.emit('Configuration completed')

# ... [rest of the code]


        # except Exception as e:
        #     self.update_signal.emit(f"Error encountered: {e}")


                    # if isinstance(device_config, str):
                    #     for command in device_config.split("\n"):
                    #         self.update_signal.emit(f"Sending command: {command}")
                    #         ssh_shell.send(command + "\r")
                    #         time.sleep(2)
                    #         response = ssh_shell.recv(1024).decode('utf-8')
                    #         self.update_signal.emit(f"Response from device: {response}")
                    #     self.update_signal.emit('Configuration completed')
                    # ssh_client.close()
                    # self.update_signal.emit(f'Disconnected from {port}')

        except paramiko.AuthenticationException as auth_error:
            self.update_signal.emit(f"Authentication failed: {str(auth_error)}")

        except paramiko.SSHException as ssh_error:
            self.update_signal.emit(f"SSH connection error: {str(ssh_error)}")

        except Exception as e:
            self.update_signal.emit(f"Error encountered: {str(e)}")

        finally:
            if ssh_client:
                ssh_client.close()
                self.update_signal.emit("SSH client closed")  


class MainProcessThread(QThread):
    update_signal = pyqtSignal(str)

    def __init__(self, server_ip, username, password, excel_path, parent=None):
        super(MainProcessThread, self).__init__(parent)
        self.server_ip = server_ip
        self.username = username
        self.password = password
        self.excel_path = excel_path

    def debug_output(self,ssh_shell):
        output = ssh_shell.recv(5000).decode("utf-8")
        return output.strip()    

    def run(self):
        try:
            self.update_signal.emit("Starting main process...")
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(hostname=self.server_ip, username=self.username, password=self.password)
            ssh_shell = ssh_client.invoke_shell()
            time.sleep(2)
            console_output = self.debug_output(ssh_shell)
            #print("My text: ", console_output.strip())
            self.update_signal.emit("My text: " + console_output.strip())                        
            if console_output.strip() == '#':
                #print("This is opengear console")
                self.update_signal.emit("This is opengear console")
                ssh_shell.send("pmshell\r")
                time.sleep(2)
                output = self.debug_output(ssh_shell)
                # print("Output: ", output)
                output_s = output.strip().split('\n')
                lines = output_s[2].strip().split('          ')
                # print("Lines: ", lines)
                pattern = r'Port (\d+)'

                # Initialize a list to store the matching patterns and associated output
                active_ports = []

                # Loop through the lines and find the pattern in each line
                for line in lines:
                    line_matches = re.findall(pattern, line)
                    active_ports.append(line_matches[0])
                self.update_signal.emit('active_ports: ' + ', '.join(active_ports))

                ssh_client.close()

                matches_with_output = []
                for port in active_ports:
                    # print('port:', port)
                    ssh_client = paramiko.SSHClient()
                    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    ssh_client.connect(hostname=self.server_ip, username=self.username, password=self.password)
                    ssh_shell = ssh_client.invoke_shell()
                    # print(self.debug_output(ssh_shell))
                    ssh_shell.send("pmshell\r")
                    # print(self.debug_output(ssh_shell))
                    time.sleep(2)
                    ssh_shell.send(port)
                    ssh_shell.send("\r")
                    time.sleep(2)
                    ssh_shell.send("\r")
                    # print(self.debug_output(ssh_shell))
                    ssh_shell.send("enable\r")
                    time.sleep(1)
                    ssh_shell.send("terminal length 0\r")
                    time.sleep(1)
                    ssh_shell.send("sh inventory\r")
                    time.sleep(5)
                    final_output = self.debug_output(ssh_shell)
                    # print('final_output: ', final_output)

                    # Define a regular expression pattern to match the PID line
                    pid_pattern = r'PID: (.*?)\s*,'

                    # Use re.search to find the first occurrence of the PID pattern
                    pid_match = re.search(pid_pattern, final_output)
                    pid_value = pid_match.group(1) if pid_match else None       # code change
                    # print('pid_value:', pid_value)

                    # Define a regular expression pattern to match the SN line
                    sn_pattern = r'SN:\s+([^\s,]+)'

                    # Use re.search to find the first occurrence of the SN pattern
                    sn_match = re.search(sn_pattern, final_output)
                    sn_value = sn_match.group(1) if sn_match else None      # code change
                    # print("sn value:", sn_value)

                    if pid_value is not None and sn_value is not None:      # code change
                        matches_with_output.append((port, sn_value, pid_value))

                    ssh_client.close()

                # Create a new Excel workbook and worksheet
                workbook = openpyxl.Workbook()
                worksheet = workbook.active

                # Set column names
                worksheet['A1'] = "active_port"
                worksheet['B1'] = "Serial number"
                worksheet['C1'] = "Device Type"
                worksheet['D1'] = "Device Config"
                worksheet['E1'] = "Output"


                # Write the matches and associated output to the worksheet
                #print('matches_with_output: ', matches_with_output)
                self.update_signal.emit('matches_with_output: ' + str(matches_with_output))
                for idx, (match, serial_number, device_type) in enumerate(matches_with_output, start=2):
                    worksheet[f'A{idx}'] = match
                    if serial_number:
                        worksheet[f'B{idx}'] = serial_number
                    if device_type:
                        worksheet[f'C{idx}'] = device_type

                workbook.save(self.excel_path)
                self.update_signal.emit("Completed")

            else:
                self.update_signal.emit("This is avocent console")
                ssh_shell.send("cd access\r ls\r")
                time.sleep(2)
                output_raw = str(self.debug_output(ssh_shell))
                #print("My output: ", output_raw)
                self.update_signal.emit("My output: " + output_raw)
                pattern = r'\d{2}-\w{1,2}-\w{1,2}-p-\d+/'
                output = [re.sub(r'\r\r', '', element) for element in output_raw.strip().split('\n')[3:] if
                          re.search(pattern, element)]
                #print("output: ", output)
                self.update_signal.emit("output: " + str(output))
                matches_with_output = []
                for port in output:
                    print('port:', port)
                    ssh_client = paramiko.SSHClient()
                    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    ssh_client.connect(hostname=self.server_ip, username=self.username, password=self.password)
                    ssh_shell = ssh_client.invoke_shell()
                    ssh_shell.send("cd access\r ls\r")
                    time.sleep(2)
                    comm = "connect " + str(port)
                    # print('comm:', comm)
                    ssh_shell.send(comm)

                    ssh_shell.send("\r")
                    time.sleep(2)
                    self.debug_output(ssh_shell)

                    ssh_shell.send(self.password)
                    time.sleep(1)

                    ssh_shell.send("\r")
                    time.sleep(2)

                    ssh_shell.send("\r")
                    time.sleep(2)

                    ssh_shell.send("show inventory\r")
                    time.sleep(2)
                    final_output_raw = self.debug_output(ssh_shell)
                    # print('final_output_raw: ', final_output_raw)

                    # Define a regular expression pattern to match the PID line
                    pid_pattern = r'PID: (.*?)\s*,'

                    # Use re.search to find the first occurrence of the PID pattern
                    pid_match = re.search(pid_pattern, final_output_raw)
                    pid_value = pid_match.group(1) if pid_match else None       # code change

                    # Define a regular expression pattern to match the SN line
                    sn_pattern = r'SN:\s+([^\s,]+)'

                    # Use re.search to find the first occurrence of the SN pattern
                    sn_match = re.search(sn_pattern, final_output_raw)
                    sn_value = sn_match.group(1) if sn_match else None          # code change
                    # print("sn value:", sn_value)

                    if pid_value is not None and sn_value is not None:      # code change
                        matches_with_output.append((port, sn_value, pid_value))

                    ssh_client.close()

                # Create a new Excel workbook and worksheet
                workbook = openpyxl.Workbook()
                worksheet = workbook.active

                # Set column names
                worksheet['A1'] = "active_port"
                worksheet['B1'] = "Serial number"
                worksheet['C1'] = "Device Type"
                worksheet['D1'] = "device_username"     # code change
                worksheet['E1'] = "device_password"     # code change
                worksheet['F1'] = "Device Config"
                worksheet['G1'] = "Output"

                # Write the matches and associated output to the worksheet
                #print('matches_with_output: ', matches_with_output)
                self.update_signal.emit('matches_with_output: ' + str(matches_with_output))
                for idx, (match, serial_number, device_type) in enumerate(matches_with_output, start=2):
                    worksheet[f'A{idx}'] = match
                    if serial_number:
                        worksheet[f'B{idx}'] = serial_number
                    if device_type:
                        worksheet[f'C{idx}'] = device_type

                workbook.save(self.excel_path)
                #print("Completed")
                self.update_signal.emit("Completed")

        except paramiko.AuthenticationException as auth_error:
            self.update_signal.emit(f"Authentication failed: {str(auth_error)}")
        except paramiko.SSHException as ssh_error:
            self.update_signal.emit(f"Could not establish SSH connection: {str(ssh_error)}")
        except Exception as e:
            self.update_signal.emit(f"Error encountered: {str(e)}")
        finally:
            ssh_client.close()
            self.update_signal.emit("SSH client closed") 

class QTextBoxLogger(logging.Handler, QObject):
    log_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        QObject.__init__(self)

    def emit(self, record):
        msg = self.format(record)
        self.log_signal.emit(msg)

class SaveLocationDialog(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Save Location Dialog')
        self.setGeometry(100, 100, 300, 250)
        self.initUI()
        self.excel_path = None
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        log_handler = QTextBoxLogger()
        self.logger.addHandler(log_handler)

        self.initUI()

        log_handler.log_signal.connect(self.updateLogTextBox)

    def updateTextBox(self, message):
        self.logTextBox.append(message)


    def initUI(self):
        layout = QGridLayout()

        # Server IP Input
        self.server_ip_label = QLabel('Server IP:', self)
        self.server_ip_input = QLineEdit(self)
        layout.addWidget(self.server_ip_label, 0, 0)
        layout.addWidget(self.server_ip_input, 0, 1)

        # Username Input
        self.username_label = QLabel('Username:', self)
        self.username_input = QLineEdit(self)
        layout.addWidget(self.username_label, 1, 0)
        layout.addWidget(self.username_input, 1, 1)

        # Password Input
        self.password_label = QLabel('Password:', self)
        self.password_input = QLineEdit(self)
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_label, 2, 0)
        layout.addWidget(self.password_input, 2, 1)

        self.save_button = QPushButton('Choose Save Location', self)
        self.save_button.clicked.connect(self.showDialog)
        layout.addWidget(self.save_button, 3, 0)

        self.activate_button = QPushButton('Get Serial Number', self)
        self.activate_button.clicked.connect(self.activateProcess)
        layout.addWidget(self.activate_button, 3, 1)

        self.browse_button = QPushButton('Browse Excel', self)
        self.browse_button.clicked.connect(self.browseExcel)
        layout.addWidget(self.browse_button, 4, 0)

        self.push_config_button = QPushButton('Push Config to Devices', self)
        self.push_config_button.clicked.connect(self.pushConfig)
        layout.addWidget(self.push_config_button, 4, 1)

        self.logTextBox = QTextEdit(self)
        self.logTextBox.setReadOnly(True)
        layout.addWidget(QLabel("Activity Console:"), 5, 0, 1, 2)
        layout.addWidget(self.logTextBox, 6, 0, 1, 2)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)



    def updateLogTextBox(self, message):
        self.logTextBox.append(message) # Update the QTextBox with the log message


    def showDialog(self):
        #global EXCEL_PATH
        options = QFileDialog.Options()
        save_file, _ = QFileDialog.getSaveFileName(self, "Save File", "", "Excel Files (*.xlsx);;All Files (*)", options=options)

        if save_file:
            if not save_file.endswith('.xlsx'):
                save_file += '.xlsx'
            #EXCEL_PATH = save_file
            self.excel_path = save_file
    
    def browseExcel(self):
       global EXCEL_PATH
       options = QFileDialog.Options()
       file_name, _ = QFileDialog.getOpenFileName(self, "Open Excel File", "", "Excel Files (*.xlsx);;All Files (*)", options=options)
        
       if file_name:
           EXCEL_PATH = file_name

    def debug_output(self,ssh_shell):
        output = ssh_shell.recv(5000).decode("utf-8")
        return output.strip()


          

    def activateProcess(self):
        
        server_ip = self.server_ip_input.text().strip()
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not all([server_ip, username, password]):
            self.showWarning("Please fill in all the required fields before pushing the config!")
            return
        #if not EXCEL_PATH:
        if not self.excel_path:    
            self.showWarning("Please select a save location first!")
            return

        self.main_process_thread = MainProcessThread(server_ip, username, password,self.excel_path)
        self.main_process_thread.update_signal.connect(self.updateLogTextBox)
        self.main_process_thread.start()






    def activate_Process(self):
        server_ip = self.server_ip_input.text().strip()
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not all([server_ip, username, password]):
            # Show a warning message to the user (assuming there's a message box or some kind of notification system in your GUI framework)
            self.showWarning("Please fill in all the required fields before pushing the config!")
            return False
        if not EXCEL_PATH or not os.path.exists(EXCEL_PATH):
            self.showWarning("Please Import Excel file first!")
            return False
        
        return True

    def pushConfig(self):

        self.thread = DeviceConfigThread(self.server_ip_input.text().strip(), 
                                         self.username_input.text().strip(), 
                                         self.password_input.text().strip())
        self.thread.update_signal.connect(self.updateLogTextBox)
        self.thread.start()   
    
    def showWarning(self, message):
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Warning)
        msgBox.setText(message)
        msgBox.setWindowTitle('Warning')
        msgBox.setStandardButtons(QMessageBox.Ok)
        msgBox.exec_()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWin = SaveLocationDialog()
    mainWin.show()
    sys.exit(app.exec_())
       

        



        

    

    





                    

                    


                     
                    
                
                
                    

        


