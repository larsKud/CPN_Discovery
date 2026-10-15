import json


def swap_position_coordinates(data):
  """Recursively traverses a dictionary or list to find keys named 'position'

  and swaps their 'x' and 'y' values.
  """
  if isinstance(data, dict):
    for key, value in data.items():
      if key == "position" and isinstance(value, dict):
        if "x" in value and "y" in value:
          value["x"], value["y"] = value["y"], value["x"]
      else:
        swap_position_coordinates(value)
  elif isinstance(data, list):
    for item in data:
      swap_position_coordinates(item)

  return data


def process_json_file(input_path, output_path=None):
  """Loads a JSON file, swaps all position coordinates, and saves the result."""
  # 1. Load the JSON file
  with open(input_path, "r", encoding="utf-8") as f:
    data = json.load(f)

  # 2. Process/swap the coordinates
  swap_position_coordinates(data)

  # 3. Determine output path (overwrite input if none provided)
  if output_path is None:
    output_path = input_path

  # 4. Save the updated data back to JSON
  with open(output_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4)

  print(f"Successfully processed {input_path} and saved to {output_path}")


# --- Example Usage ---
# Replace 'model.json' with your actual file path
process_json_file("/home/user/Documents/_MA/Data/Evaluation/OM_lessOT_example_flipped.ocpn", '/home/user/Documents/_MA/Data/Evaluation/OM_lessOT_example_flipped2.ocpn')
