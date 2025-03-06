import json

def fix_interface_data(parsed_data):
    corrected_interfaces = []
    last_valid_name = None

    for entry in parsed_data["interfaces"]:
        if entry["name"]:
            last_valid_name = entry["name"]  # Store the valid interface name
            corrected_interfaces.append(entry)
        else:
            if last_valid_name:
                entry["name"] = last_valid_name  # Assign the missing name
                last_valid_name = None  # Reset to avoid duplicating for the wrong entry
            corrected_interfaces.append(entry)

    # Update the parsed data
    parsed_data["interfaces"] = corrected_interfaces
    return parsed_data

# Step 1: Read the original JSON file
with open("parsed_config.json", "r") as infile:
    parsed_data = json.load(infile)

# Step 2: Fix the misaligned data
fixed_data = fix_interface_data(parsed_data)

# Step 3: Write the corrected data into a new JSON file
with open("corrected_config.json", "w") as outfile:
    json.dump(fixed_data, outfile, indent=4)

print("Corrected JSON file has been saved as 'corrected_config.json'")
