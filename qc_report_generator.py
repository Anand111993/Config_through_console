
import re

# Existing platform_codes dictionary
platform_codes = {
    "C9407R": "16.12.05",
    "C9410R": "16.12.05",
    "N9K-C93180YC-FX3": "10.2(5)",
    "ASR1002-HX": "17.03.04a", 
    "31108PCV": "9.3(11)",
    "C9396PX": "7.0(3)",
    "ASR1000":"17.03.04a",
    "C9300-48P":"17.09.05",
    "C93180YC-FX3":"9.3(8)",
    "N9K-C9336C-FX2":"10.2(5)"
}

def process_sh_version(hostname, output, platform_codes):
    # Updated regular expression for Nexus devices to be more inclusive
    nexus_model_re = re.compile(r'cisco Nexus\s*([0-9A-Za-z\- ]+?)\s+Chassis', re.IGNORECASE)
    nexus_version_re = re.compile(r'NXOS: version (\S+)', re.IGNORECASE)
    
    # Regular expression for IOS XE devices remains the same
    ios_xe_model_re = re.compile(r'cisco (\S+) \(\S+\) processor', re.IGNORECASE)
    ios_xe_version_re = re.compile(r'Cisco IOS XE Software, Version (\S+)', re.IGNORECASE)

    # Try matching Nexus devices first
    nexus_model_match = nexus_model_re.search(output)
    nexus_version_match = nexus_version_re.search(output)

    if nexus_model_match and nexus_version_match:
        # Capture the model, process it to match the platform_codes format
        model_raw = nexus_model_match.group(1).strip()
        # Split the model string by spaces and take the last element for models like "Nexus9000 C93180YC-FX3"
        model = model_raw.split()[-1] if ' ' in model_raw else model_raw
        version = nexus_version_match.group(1).strip()

        # Adjust for prefix in model names like "N9K-"
        model = model.replace("N9K-", "")

        # Check against known platform codes
        expected_version = platform_codes.get(model)
        if expected_version and version == expected_version:
            return f"{hostname} - Nexus {model} Version: {version} - QC Passed\n"
        elif expected_version:
            return f"{hostname} - Nexus {model} Version: {version} - QC Failed (Expected: {expected_version})\n"
        else:
            return f"{hostname} - Nexus {model} Version: {version} - QC feature not integrated for this model; check manually.\n"
    
    # If not Nexus, try matching IOS XE devices
    ios_xe_model_match = ios_xe_model_re.search(output)
    ios_xe_version_match = ios_xe_version_re.search(output)

    if ios_xe_model_match and ios_xe_version_match:
        model = ios_xe_model_match.group(1).strip()
        version = ios_xe_version_match.group(1).strip()

        # Check against known platform codes for IOS XE models
        expected_version = platform_codes.get(model)
        if expected_version and version.startswith(expected_version):
            return f"{hostname} - {model} Version: {version} - QC Passed\n"
        elif expected_version:
            return f"{hostname} - {model} Version: {version} - QC Failed (Expected: {expected_version})\n"
        else:
            return f"{hostname} - {model} Version: {version} - QC feature not integrated for this model; check manually.\n"

    # If no matches found, report as unable to determine model or version
    return f"{hostname} - Unable to determine model or version\n"


# Define other processing functions as needed...




# Process 'show environment' command output
# def process_show_environment(hostname, output):
#     status_re = re.compile(r'(\bOk\b)')
#     ok_statuses = status_re.findall(output)
#     # Assuming 6 fans, 2 power supplies, and 3 temperature sensors should report "Ok"
#     if len(ok_statuses) == 11:
#         return f"{hostname} - Environment Check: All components OK - QC Passed\n"
#     else:
#         return f"{hostname} - Environment Check: One or more components not OK - QC Failed\n"

def process_show_environment(hostname, output):
    # Regular expressions for IOS XE alarm checks
    critical_alarms_re = re.compile(r'Number of Critical alarms:\s+(\d+)', re.IGNORECASE)
    major_alarms_re = re.compile(r'Number of Major alarms:\s+(\d+)', re.IGNORECASE)
    minor_alarms_re = re.compile(r'Number of Minor alarms:\s+(\d+)', re.IGNORECASE)
    
    # Try matching IOS XE environment checks first
    critical_alarms_match = critical_alarms_re.search(output)
    major_alarms_match = major_alarms_re.search(output)
    minor_alarms_match = minor_alarms_re.search(output)
    
    if critical_alarms_match and major_alarms_match and minor_alarms_match:
        critical_alarms = int(critical_alarms_match.group(1))
        major_alarms = int(major_alarms_match.group(1))
        minor_alarms = int(minor_alarms_match.group(1))
        
        if critical_alarms != 0 or major_alarms != 0 or minor_alarms != 0:
            return f"{hostname} - Environment Check: One or more components not OK - QC Failed\n"
        return f"{hostname} - Environment Check: All components OK - QC Passed\n"
    
    # If not IOS XE, check Nexus environment statuses
    status_re = re.compile(r'\bOk\b', re.IGNORECASE)
    ok_statuses = status_re.findall(output)
    # Assuming 6 fans, 2 power supplies, and 3 temperature sensors should report "Ok"
    if len(ok_statuses) <= 15:
        return f"{hostname} - Environment Check: All components OK - QC Passed\n"
    else:
        return f"{hostname} - Environment Check: One or more components not OK - QC Failed\n"



# def process_sh_int_status(output):
#     report_lines = []
#     # Regex pattern adjusted to match interface lines excluding those with Type as '--'
#     int_status_re = re.compile(r'(\bEth\d+/\d+\b)\s+--\s+\S+\s+\d+\s+\S+\s+\S+\s+([^-]+)')

#     for line in output.splitlines():
#         match = int_status_re.search(line)
#         if match:
#             port, port_type = match.groups()
#             report_lines.append(f"Port: {port}, Type: {port_type}")

#     if report_lines:
#         return "\n".join(report_lines)
#     else:
#         return "No interfaces found or unable to parse."



def process_sh_int_status(output):
    return output.strip() 
    # report_lines = []
    # # Regex pattern to match each port line and capture all elements, with a focus on the Type
    # int_status_re = re.compile(
    #     r'(\bEth\d+/\d+(\.\d+)?\b)\s+[^-]+\s+\S+\s+\S+\s+\S+\s+\S+\s+(\S+)')

    # for line in output.splitlines():
    #     match = int_status_re.search(line)
    #     if match:
    #         port, _, port_type = match.groups()
    #         report_lines.append(f"Port: {port}, Type: {port_type}")

    # if report_lines:
    #     return "\n".join(report_lines)
    # else:
    #     return "No interfaces found or unable to parse."





# Command-to-processing function mapping
command_processing_map = {
    'sh version': lambda hostname, output: process_sh_version(hostname, output, platform_codes),
    'show environment': lambda hostname, output: process_show_environment(hostname, output),
    'sh int status': lambda hostname, output: process_sh_int_status(output),

    # Add other command mappings here...
}

def generate_qc_report(hostname, command_outputs):
    qc_report = ""
    # Iterate over the command outputs and process them using the corresponding function from command_processing_map
    for command, output in command_outputs.items():
        processing_func = command_processing_map.get(command)
        if processing_func:
            qc_report += processing_func(hostname, output)
        # else:
        #     qc_report += f"Processing function for command '{command}' is not defined.\n"
    return qc_report


