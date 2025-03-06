import sys
import os
import re
from datetime import datetime
import subprocess
import pandas as pd
from netmiko import ConnectHandler, NetMikoTimeoutException
from pathlib import Path, PureWindowsPath
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QColor, QDesktopServices
from PyQt5.QtWidgets import QApplication, QWidget, QInputDialog, QLineEdit, QTextEdit, QFileDialog, QMessageBox, \
    QPushButton, \
    QLabel, QCheckBox
from PyQt5.QtCore import pyqtSlot, QThreadPool, QTimer, QUrl

import device_grouping
from help import Ui_Dialog
from gui import Ui_MainWindow

from Crypto.Util.Padding import unpad
from base64 import b64decode
import platform
import threading
from Crypto.Cipher import AES
from auto_word_search import WordSearchApp
from compair_file import FileImportApp
from encryptXLin256AES import App
from device_grouping import GroupingApp
#from configThroughconsole import SaveLocationDialog
from config_generator import MainWindow
from DevLatest_CTC_V3_port_mapping import SaveLocationDialog

global method_selection
global folder_path
global cred_path
global data
global is_button_clicked

cred_path = ''
folder_path = ''
data = ''
selected_devices = []
filepath_list = []
command_list = []
path2 = ''
is_closeEvent = False
is_button_clicked = False
platform_path = ''
slt_method = ''
combo_box_method = 'Send Show Commands'
radioButtonValue = ''
radioButtonSelected = ''
custom_string = ''
is_error = ''
activity_log_path = ''


class MyWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.grouping_app = None  # Initialize the attribute

    def closeEvent(self, event):
        choice = QMessageBox.question(self, "Quit", "Do you want to quit app?", QMessageBox.Yes | QMessageBox.No)
        if choice == QMessageBox.Yes:
            print("The program was shut down.")
            sys.stdout = sys.__stdout__

            # Check if the grouping_app object exists and close it if it does
            if self.grouping_app is not None:
                self.grouping_app.close()

            # Quit the application when the main window is closed
            QtWidgets.QApplication.quit()

            event.accept()
            global is_closeEvent
            is_closeEvent = True
            print("App is closed forcefully !")
        else:
            event.ignore()


class Stream(QtCore.QObject):
    newText = QtCore.pyqtSignal(str)

    def write(self, text):
        if activity_log_path:
            with open(activity_log_path, "a") as f:
                f.write(str(text))
        self.newText.emit(str(text))


# class MainWindow_EXEC(QMainWindow, Ui_MainWindow):
class MainWindow_EXEC():  #
    def __init__(self):
        super().__init__()
        self.thread_manager = QThreadPool()

        sys.stdout = Stream(newText=self.onUpdateText)
        app = QtWidgets.QApplication(sys.argv)
        MainWindow = QtWidgets.QMainWindow()
        MainWindow = MyWindow()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(MainWindow)
        self.browse_File_handler()
        self.save_File_handler()
        self.save_output()
        self.select_cmd_option()
        self.clear_all_data()
        self.help_button_handler()
        self.device_ping()
        self.go_saved_file_location()
        self.open_to_word_search()
        self.selected_combobox_items()
        self.open_to_compare_file()
        self.open_to_device_grouping()
        self.file_encrypt()
        self.open_to_check_button()
        self.configthu_console()
        self.config_gen()
        MainWindow.show()
        sys.exit(app.exec_())

    # Browse File and printing path of the file
    def browse_File_handler(self):
        self.ui.pushButton_Browse_device_detail.clicked.connect(self.open_dialog_box)
        self.ui.pushButton_2_Browse_cmd_File.clicked.connect(self.open_dialog_box5)

    def go_saved_file_location(self):
        self.ui.pushButton_2_open_Saved_File.clicked.connect(self.open_file_location)

    def sh_info_messagebox(self, message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText(message)
        msg.setWindowTitle('Info')
        msg.exec_()

    def decrypt(self, data, cipher):
        try:
            decoded_data = b64decode(data)
            decrypted_data = unpad(cipher.decrypt(decoded_data), 16)
            return decrypted_data.decode('utf-8')

        except Exception as e:
            return data

    def open_dialog_box(self):
        filename = QFileDialog.getOpenFileName()
        global cred_path
        cred_path = filename[0]
        if len(cred_path) > 0:
            if re.search(r'.xlsx$', cred_path, re.I | re.M):
                if platform.system() == 'Windows':
                    print("Device credential file path: ", cred_path.replace('/', '\\'), end='')
                else:
                    print("Device credential file path: ", cred_path, end='')

                global data
                data = pd.read_excel(cred_path)
                columns_to_decrypt = ['host', 'password', 'username']
                reply = QMessageBox.question(None, 'Encryption',
                                             "Is the Excel sheet encrypted?",
                                             QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    key_string, ok = QInputDialog.getText(None, "Enter your encryption key:", "Key:")
                    if ok and key_string:
                        try:
                            key = b64decode(key_string)
                            cipher = AES.new(key, AES.MODE_CBC)

                            for col in columns_to_decrypt:
                                if col in data.columns:
                                    data[col] = data[col].apply(
                                        lambda x: self.decrypt(x, cipher) if not pd.isna(x) and x != data[col].iloc[
                                            0] else self.decrypt(x, cipher))
                                else:
                                    QMessageBox.critical(self, "Error", f"Column {col} not found in the excel file")
                            data = data.iloc[1:]
                            #print("The decrypt data: ", data)
                        except Exception as e:
                            QMessageBox.critical(self, "Error", f"An error occurred: {e}")
                else:
                    print("Data appears to be unencrypted. No decryption needed.")
                    #print("My Data is ", data)
                self.device_population()
                self.device_selection()
            else:
                self.sh_info_messagebox("Only excel file is supported, please upload an excel file.")
                print("Only excel file is supported, please upload an excel file.")
        else:
            print("File path can't be empty")
            self.sh_info_messagebox("Please upload an excel file.")

    def device_population(self):
        try:
            _translate = QtCore.QCoreApplication.translate
            self.ui.listWidget.setSortingEnabled(False)
            count = 0
            for index, row in data.iterrows():
                device_name = row.get('device_name', '')
                item = QtWidgets.QListWidgetItem()
                self.ui.listWidget.addItem(item)
                item = self.ui.listWidget.item(count)
                text = device_name
                item.setText(_translate("MainWindow", text))
                count += 1
            self.ui.pushButton_10_device_grouping.setDisabled(False)
        except Exception:
            print("Some error occurred")

    def device_selection(self):
        self.ui.listWidget.itemClicked.connect(self.select_device)

    def select_device(self):
        self.open_device_grouping = GroupingApp(data)
        self.open_device_grouping.close_subwindow()
        global is_button_clicked
        is_button_clicked = False
        global selected_devices
        selected_devices = []
        items = self.ui.listWidget.selectedItems()

        for i in range(len(items)):
            selected_devices.append(str(self.ui.listWidget.selectedItems()[i].text()))
        print("selected_devices:", selected_devices)

        if len(selected_devices) > 0:
            self.ui.pushButton_2_Ping.setDisabled(False)
        elif len(selected_devices) == 0:
            self.show_info_messagebox("Please select atleast one device or select from device grouping to proceed")
            self.ui.pushButton_2_Ping.setDisabled(True)

    def save_output(self):
        self.ui.pushButton_4_Submit.clicked.connect(self.submit_button)

    def submit_button(self):
        if cred_path:
            if len(selected_devices) > 0 or len(device_grouping.selected_items_list) > 0:
                if slt_method:
                    if len(filepath_list) > 0 or (len(command_list) > 0 and len(command_list[0]) > 0):
                        if folder_path:
                            self.thread_manager.start(self.tool_action_config)
                        else:
                            self.show_info_messagebox("Please select the output folder")
                    else:
                        self.show_info_messagebox("Please upload or write some commands")
                else:
                    self.show_info_messagebox("Select Command or Config Mode")
            else:
                self.show_info_messagebox("Please select atleast one device or select from device grouping to proceed")
        else:
            self.show_info_messagebox("Please upload the device credential file.")

    def add_commands(self):
        global command_list
        textInput = self.ui.textEdit.toPlainText().strip()
        command_list = textInput.split('\n')
        if len(command_list[0]) > 0:
            pass

    def select_cmd_option(self):
        self.ui.radioButton_2_Select_cmd_File.setCheckable(True)
        self.ui.radioButton_Enter_cmd.setCheckable(True)
        self.ui.radioButton_2_Select_cmd_File.toggled.connect(
            lambda: self.radioButton_state(self.ui.radioButton_2_Select_cmd_File.sender()))
        self.ui.radioButton_Enter_cmd.toggled.connect(
            lambda: self.radioButton_state(self.ui.radioButton_Enter_cmd.sender()))
        self.ui.textEdit.textChanged.connect(lambda: self.add_commands())
        self.ui.radioButton_2_Select_cmd_File.clicked.connect(self.combobox_state)
        self.ui.radioButton_Enter_cmd.clicked.connect(self.combobox_state)

    def radioButton_state(self, b):
        global command_list
        global radioButtonValue
        global radioButtonSelected
        radioButtonValue = b.text()
        radioButtonSelected = b.isChecked()

        if (b.isChecked()) and (b.text() == 'Select Command File' and combo_box_method == 'Send Show Commands'):
            self.ui.pushButton_2_Browse_cmd_File.setHidden(False)
            self.ui.pushButton_2_Browse_cmd_File.setDisabled(False)
            self.ui.textEdit.setHidden(True)
            self.ui.textEdit.setDisabled(True)
            self.set_stl_method()

        elif (b.isChecked()) and (b.text() == 'Enter Commands' and combo_box_method == 'Send Show Commands'):
            self.ui.textEdit.setHidden(False)
            self.ui.textEdit.setDisabled(False)
            self.ui.textEdit.clear()
            self.ui.pushButton_2_Browse_cmd_File.setHidden(True)
            self.ui.pushButton_2_Browse_cmd_File.setDisabled(True)
            self.set_stl_method()

        elif (b.isChecked()) and (b.text() == 'Enter Commands' and combo_box_method == 'Send Config Commands'):
            self.ui.textEdit.setHidden(False)
            self.ui.textEdit.setDisabled(False)
            self.ui.textEdit.clear()
            self.ui.pushButton_2_Browse_cmd_File.setHidden(True)
            self.ui.pushButton_2_Browse_cmd_File.setDisabled(True)
            self.set_stl_method()
        elif (b.isChecked()) and (b.text() == 'Select Command File' and combo_box_method == 'Send Config Commands'):
            self.ui.pushButton_2_Browse_cmd_File.setHidden(False)
            self.ui.pushButton_2_Browse_cmd_File.setDisabled(False)
            self.ui.textEdit.setHidden(True)
            self.ui.textEdit.setDisabled(True)
            self.set_stl_method()

    def open_dialog_box5(self):
        filename = QFileDialog.getOpenFileNames()  # SoumyaDev
        filepath_list1 = filename[0]
        global filepath_list
        filepath_list = []
        for filepath in filepath_list1:
            if re.search(r'.txt$', filepath, re.I | re.M):
                if platform.system() == 'Windows':
                    filepath1 = filepath.replace('/', '\\')
                    filepath_list.append(filepath1)
                else:
                    filepath_list.append(filepath)

        if len(filepath_list) > 0:
            print("My File paths are: ", filepath_list)
        else:
            self.show_info_messagebox("Only text files are supported, please upload a text file")

    def command_file_selection(self, d_name, custom_string):
        global command_list
        filepath = ""
        d_name_filepath = next((s for s in filepath_list if d_name in s), None)
        custom_filepath = next((s for s in filepath_list if custom_string in s), None)

        if d_name_filepath:
            filepath = d_name_filepath
            print("File path for the device " + d_name + ':', filepath)
        elif custom_filepath:
            filepath = custom_filepath
            print("File path for the custom string " + custom_string + ':', filepath)
        else:
            pass

        if filepath:
            with open(filepath) as f:
                lines = f.readlines()
                command_list = []
                count = 0
                for line in lines:
                    count += 1
                    command_list.append(line.strip())
                command_list = [x for x in command_list if x]

    def save_File_handler(self):
        self.ui.pushButton_3_opt_File_Location.clicked.connect(self.file_save)

    def file_save(self):
        global folder_path
        # print("Button_Pressed")
        name = QFileDialog()
        folder_path = name.getExistingDirectory(None, "Select Folder")
        if folder_path:
            if platform.system() == 'Windows':
                print("Output Folder Path: ", folder_path.replace('/', '\\'))
            else:
                print("Output Folder Path: ", folder_path)

        else:
            self.show_info_messagebox("Please select or create a folder")
            print("Folder is not selected")

    def tool_action_config(self):
        global device_chunks
        try:
            # col = data.columns.values.tolist()[1:8]
            device_dict = dict(zip(data.device_name,
                                   zip(data.device_type, data.host, data.username, data.password, data.port,
                                       data.secret)))
            selected_device_dict = {}
            for dev in device_dict:
                if dev in selected_devices:
                    selected_device_dict.update({dev: device_dict[dev]})
            # print("selected_device_dict: ", selected_device_dict)

            chunk_size = 5
            device_chunks = {}
            current_chunk = []
            chunk_counter = 1

            for device_name, device_details in selected_device_dict.items():
                current_chunk.append((device_name, device_details))

                if len(current_chunk) == chunk_size:
                    chunk_name = f'Chunk{chunk_counter}'
                    device_chunks[chunk_name] = current_chunk
                    current_chunk = []
                    chunk_counter += 1

            # Append the last chunk if it's not empty
            if current_chunk:
                chunk_name = f'Chunk{chunk_counter}'
                device_chunks[chunk_name] = current_chunk

            if is_button_clicked:
                device_chunks = device_grouping.device_chunks

            #print("device_chunks: ", device_chunks)

            print("#####################Task started###########################")
            threads = []
            for i, chunk in enumerate(device_chunks.values()):
                thread_name = f"Thread-{i}"
                thread = threading.Thread(target=self.process_chunk, args=(chunk, thread_name))
                threads.append(thread)
                thread.start()

            # Wait for all threads to complete
            for thread in threads:
                thread.join()

        except Exception:
            print("Some error occurred !")
            exc_info = sys.exc_info()
            print('Outer try block error', exc_info)
        finally:
            print("############################ Task completed ############################")
            print()
            device_chunks.clear()
            is_error = False
            self.ui.pushButton_4_Submit.setDisabled(False)
            self.ui.pushButton.setDisabled(False)

    def process_chunk(self, chunk, thread_id):
        for d_name, d_cred in chunk:
            self.ui.pushButton_4_Submit.setDisabled(True)
            self.ui.pushButton_2_Ping.setDisabled(True)
            self.ui.pushButton.setDisabled(True)
            if not is_closeEvent:
                global is_error
                is_error = False
                col = data.columns.values.tolist()[1:9]
                d_details = dict(zip(col, d_cred))
                # print(d_name, ':', d_details)
                # print(f"{thread_id}: {d_name}: {d_details}")
                print(f"{thread_id}: Process start for the device {d_name}")
                if len(filepath_list) > 0 and radioButtonValue == 'Select Command File':
                    self.command_file_selection(d_name, custom_string)
                if radioButtonValue == 'Enter Commands':
                    self.add_commands()
                if len(command_list) > 0 and len(command_list[0]) > 0:
                    print(f"{thread_id}: Command list to be pushed: {command_list}")
                    print(f"{thread_id}: {d_name} is trying to connect !!!")
                    try:
                        # global is_error
                        if d_details['secret'] == None:
                            net_connect = ConnectHandler(**d_details)
                        else:
                            net_connect = ConnectHandler(**d_details)
                            net_connect.enable()
                        if net_connect:
                            print(f"{thread_id}: {d_name} is connected successfully !!!")
                            timestamp = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
                            directory_name = d_name + "_" + timestamp
                            directory_path = os.path.join(folder_path, directory_name)
                            if slt_method in ['send_config_from_file', 'send_config_set']:
                                if not os.path.exists(directory_path):
                                    os.makedirs(directory_path)

                            pre_file_name = d_name + "_pre_" + timestamp + ".txt"
                            pre_file_path = os.path.join(directory_path, pre_file_name)

                            file_name = d_name + "_" + timestamp + ".txt"
                            file_path = os.path.join(directory_path, file_name)

                            post_file_name = d_name + "_post_" + timestamp + ".txt"
                            post_file_path = os.path.join(directory_path, post_file_name)

                            if (platform.system() == 'Windows' and slt_method == 'send_command'):
                                # print('Inside Windows and Send Command section')
                                folder_path1 = Path(folder_path)
                                file_path = folder_path1 / file_name
                                path_on_windows = PureWindowsPath(file_path)
                                with open(path_on_windows, "a") as dump_file:
                                    print(f"{thread_id}: Start pushing the command to the device {d_name}")
                                    for command in command_list:
                                        dump_file.write("####" + " " + command + " " + "####")
                                        dump_file.write("\n")
                                        output = net_connect.send_command(command)
                                        dump_file.write(output)
                                        dump_file.write("\n\n")
                                    print(f"{thread_id}: Commands are pushed to the device {d_name} successfully.")
                                    net_connect.disconnect()
                                    print(f"{thread_id}: {d_name} is disconnected successfully !!!")

                            elif (platform.system() != 'Windows' and slt_method == 'send_command'):
                                file_path = folder_path + "/" + file_name
                                with open(file_path, "a") as dump_file:
                                    print(f"{thread_id}: Start pushing the command to the device {d_name}")
                                    for command in command_list:
                                        dump_file.write("####" + " " + command + " " + "####")
                                        dump_file.write("\n")
                                        output = net_connect.send_command(command)
                                        dump_file.write(output)
                                        dump_file.write("\n\n")
                                    print(f"{thread_id}: Commands are pushed to the device {d_name} successfully.")
                                    net_connect.disconnect()
                                    print(f"{thread_id}: {d_name} is disconnected successfully !!!")

                        # code change for window devices so that pre and post can be saved
                            elif (platform.system() == 'Windows' and (slt_method == 'send_config_from_file' or slt_method == 'send_config_set')):
                                device_type = d_details['device_type']

                                command_map = {
                                    'cisco_ios': 'show run',
                                    'juniper': 'show configuration',
                                    'arista': 'show run',
                                    'cisco_xr': 'show run'
                                }
                                if device_type in command_map:
                                    with open(PureWindowsPath(pre_file_path), "a") as dump_file:
                                        output = net_connect.send_command(command_map[device_type])
                                        dump_file.write(output)
                                        dump_file.write("\n\n")

                                with open(PureWindowsPath(file_path), "a") as dump_file:
                                    print(f"{thread_id}: Start pushing the configuration to the device from the file {d_name}")
                                    dump_file.write("####" + " " + "Pushing below config " + " " + "####")
                                    dump_file.write("\n")
                                    output = net_connect.send_config_set(command_list)
                                    dump_file.write(output)
                                    dump_file.write("\n\n")
                                    print(f"{thread_id}: Configs are pushed to the device {d_name} successfully from the file")

                                with open(PureWindowsPath(post_file_path), "a") as dump_file:
                                    output = net_connect.send_command(command_map[device_type])
                                    dump_file.write(output)
                                    dump_file.write("\n\n")

                                net_connect.disconnect()
                                print(f"{thread_id}: {d_name} is disconnected successfully !!!")

                            elif (platform.system() != 'Windows' and (
                                    slt_method == 'send_config_from_file' or slt_method == 'send_config_set')):
                                print(directory_path, "is created")
                                if not os.path.exists(directory_path):
                                    os.makedirs(directory_path)

                                device_type = d_details['device_type']

                                command_map = {
                                    'cisco_ios': 'show run',
                                    'juniper': 'show configuration',
                                    'arista_eos': 'show run',
                                    'cisco_xr': 'show run'
                                }
                                if device_type in command_map:
                                    with open(pre_file_path, "a") as dump_file:
                                        output = net_connect.send_command(command_map[device_type])
                                        dump_file.write(output)
                                        dump_file.write("\n\n")

                                with open(file_path, "a") as dump_file:
                                    print(f"{thread_id}: Start pushing the command to the device {d_name}")
                                    dump_file.write("####" + " " + "Pushing the below config" + " " + "####")
                                    dump_file.write("\n")
                                    output = net_connect.send_config_set(command_list)
                                    # print(output)
                                    dump_file.write(output)
                                    dump_file.write("\n\n")
                                    print(
                                        f"{thread_id}: Configs are pushed to the device {d_name} successfully from the file.")

                                with open(post_file_path, "a") as dump_file:
                                    output = net_connect.send_command(command_map[device_type])
                                    # print(output)
                                    dump_file.write(output)
                                    dump_file.write("\n\n")
                                net_connect.disconnect()
                                print(f"{thread_id}: {d_name} is disconnected successfully !!!")
                            else:
                                print('Some error occured. Either OSPlatform or Method selection is not available')
                            global is_complete
                            is_complete = True
                        else:
                            print(d_name, "is not reachable")
                            continue
                    except NetMikoTimeoutException as e:

                        is_error = True

                        print("Netmiko Timeout Exception occurred:", str(e))
                        print(d_name, "is not reachable")
                    except Exception as e:

                        is_error = True
                        print("Netmiko Timeout Exception occurred:", str(e))
                    else:

                        is_error = False

                    finally:
                        if radioButtonValue == 'Select Command File':
                            command_list.clear()
                else:
                    print("No command/config file is found for the device: " + d_name)
                print("\n")
            else:
                print("Close triggered")
                break

    def device_ping(self):
        self.ui.pushButton_2_Ping.clicked.connect(self.ping2)

    def ping2(self):
        if data.items:
            self.thread_manager.start(self.device_ping_action)

    def device_ping_action(self):
        self.ui.pushButton_2_Ping.setDisabled(True)
        self.ui.pushButton_4_Submit.setDisabled(True)
        self.ui.pushButton.setDisabled(True)
        all_dev_dict = dict(zip(data.device_name, data.host))
        for dev_name in all_dev_dict:
            if dev_name in selected_devices:
                print('Please wait!!! ', 'RNAT is trying to ping ', dev_name)
                if platform.system() == 'Windows':
                    response = subprocess.getoutput(f"ping -n 3 " + all_dev_dict[dev_name])
                else:
                    response = subprocess.getoutput(f"ping -c 3 " + all_dev_dict[dev_name])
                print(response)
                print()
        self.ui.pushButton_2_Ping.setDisabled(False)
        self.ui.pushButton_4_Submit.setDisabled(False)
        self.ui.pushButton.setDisabled(False)

    def show_info_messagebox(self, error_msg):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText(error_msg)
        msg.setWindowTitle("Information MessageBox")
        msg.setStandardButtons(QMessageBox.Ok)
        # msg.buttonClicked.connect(self.Ok)  # connect clicked signal
        return_value = msg.exec_()  # get the return value

    def clear_all_data(self):
        self.ui.pushButton.clicked.connect(self.buttonClear_handler)

    def buttonClear_handler(self):
        print("Clearing the data ...")
        global cred_path
        global folder_path
        global data
        global selected_devices
        global command_list
        global path2
        global filepath_list
        global slt_method
        global activity_log_path

        cred_path = ''
        folder_path = ''
        data = ''
        command_list = []
        filepath_list = []
        path2 = ""
        slt_method = ""
        activity_log_path = ""
        global selected_devices
        selected_devices.clear()
        device_grouping.selected_items_list.clear()
        self.open_device_grouping = GroupingApp(data)
        self.open_device_grouping.close_subwindow()
        self.ui.pushButton_10_device_grouping.setDisabled(True)
        self.ui.listWidget.clear()
        self.ui.textEdit.clear()
        self.ui.pushButton_2_Ping.setHidden(False)
        self.ui.pushButton_2_Ping.setDisabled(True)
        self.ui.check_button.setChecked(False)  # Assuming this sets the check button to unchecked
        self.ui.check_button.setText('Activity Console:Unchecked')
        self.checked = False

        print("Data has been cleared !")

    def onUpdateText(self, text):
        global color
        cursor = self.ui.textEdit_2.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)

        if is_error:
            color = "red"
        else:
            color = "black"

        lines = text.split('\n')
        for line in lines:
            html_text = f'<span style="color:{color}">{line}</span>'
            self.ui.textEdit_2.insertHtml(html_text + '<br>')
        self.ui.textEdit_2.setTextCursor(cursor)
        self.ui.textEdit_2.ensureCursorVisible()

    def help_button_handler(self):
        self.ui.toolButton_help.clicked.connect(self.display_msg)

    def display_msg(self):
        Dialog = QtWidgets.QDialog()
        ui = Ui_Dialog()
        ui.setupUi(Dialog)
        Dialog.show()
        rsp = Dialog.exec_()

    def check_platform(self):
        platform.system() == 'Windows'

    def selected_combobox_items(self):
        self.ui.comboBox.activated.connect(self.combobox_state)
        self.ui.comboBox.activated.connect(self.set_stl_method)

    def combobox_state(self):
        global combo_box_method
        combo_box_method = self.ui.comboBox.currentText()

    def set_stl_method(self):
        global radioButtonValue
        global radioButtonSelected
        global slt_method

        if (combo_box_method == 'Send Config Commands'):
            if (radioButtonSelected):
                if (radioButtonValue == 'Select Command File'):
                    slt_method = 'send_config_from_file'
                elif (radioButtonValue == 'Enter Commands'):
                    slt_method = 'send_config_set'
            else:
                slt_method = 'send_command'
        else:
            slt_method = 'send_command'

    def open_file_location(self):
        global folder_path
        if folder_path:
            file_info = QUrl.fromLocalFile(folder_path)
            QDesktopServices.openUrl(file_info)

    def open_to_word_search(self):
        self.ui.pushButton_7_word_search.clicked.connect(self.open_word_search)

    def open_word_search(self):
        global folder_path
        # app = QApplication(sys.argv)
        self.word_search_window = WordSearchApp(folder_path)
        self.word_search_window.show()

    def open_to_compare_file(self):
        self.ui.pushButton_8_compare_file.clicked.connect(self.open_compare_file)

    def open_compare_file(self):
        self.open_compare_window = FileImportApp()
        self.open_compare_window.show()

    def file_encrypt(self):

        self.ui.pushButton_9_encrypt_file.clicked.connect(self.open_encrypt_file)

    def open_encrypt_file(self):
        self.open_encrypt_window = App()
        self.open_encrypt_window.show()

    def configthu_console(self):
        self.ui.pushButton_11_config_by_console.clicked.connect(self.open_ctc)

    def open_ctc(self):
        self.open_ctc_window = SaveLocationDialog()
        self.open_ctc_window.show()

    def config_gen(self):
        self.ui.pushButton_12_config_generator.clicked.connect(self.open_config_gen_gui)

    def open_config_gen_gui(self):
        self.open_config_gen_window = MainWindow()
        self.open_config_gen_window.show()

    def open_to_device_grouping(self):
        self.ui.pushButton_10_device_grouping.clicked.connect(self.open_device_grouping)

    def open_device_grouping(self):
        self.ui.listWidget.clearSelection()
        global is_button_clicked
        is_button_clicked = True
        self.open_device_grouping = GroupingApp(data)
        self.open_device_grouping.show()

    def open_to_check_button(self):
        self.ui.check_button.clicked.connect(self.toggle_check_button)
        self.folder_path = None
        self.checked = False
        self.folder_dialog = None  # Create a class-level variable to store the folder dialog instance

    def toggle_check_button(self):
        if self.checked:
            self.ui.check_button.setText('Activity Console:Unchecked')
            self.checked = False
            self.folder_path = None
        else:
            self.ui.check_button.setText('Activity Console:Checked')
            self.checked = True
            if self.checked:
                self.open_folder_dialog()

    def open_folder_dialog(self):
        if not self.folder_dialog:  # If the folder dialog doesn't exist, create it
            self.folder_dialog = QFileDialog()
            self.folder_dialog.setFileMode(QFileDialog.Directory)
            self.folder_dialog.setViewMode(QFileDialog.List)
            self.folder_dialog.setOption(QFileDialog.ShowDirsOnly)

        timestamp = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
        file_name = "activity_log" + "_" + str(timestamp) + ".txt"
        if self.folder_dialog.exec_():
            selected_folder = self.folder_dialog.selectedFiles()
            if selected_folder:
                self.folder_path = selected_folder[0]
                global activity_log_path
                activity_log_path = self.folder_path + "/" + file_name
                if platform.system() == 'Windows':
                    activity_log_path = PureWindowsPath(activity_log_path)
                print("activity_log_path: ", activity_log_path)
        else:
            
            self.ui.check_button.setChecked(False)  
            self.ui.check_button.setText('Activity Console:Unchecked')
            self.checked = False


if __name__ == "__main__":
    MainWindow_EXEC()

