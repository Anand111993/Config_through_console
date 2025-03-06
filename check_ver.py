
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
    if len(ok_statuses) == 11:
        return f"{hostname} - Environment Check: All components OK - QC Passed\n"
    else:
        return f"{hostname} - Environment Check: One or more components not OK - QC Failed\n"


