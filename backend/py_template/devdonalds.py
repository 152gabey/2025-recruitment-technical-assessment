from dataclasses import dataclass
from typing import List, Dict, Union
from flask import Flask, request, jsonify
import re

# ==== Type Definitions, feel free to add or modify ===========================
@dataclass
class CookbookEntry:
	name: str

@dataclass
class RequiredItem():
	name: str
	quantity: int

@dataclass
class Recipe(CookbookEntry):
	required_items: List[RequiredItem]

@dataclass
class Ingredient(CookbookEntry):
	cook_time: int


# =============================================================================
# ==== HTTP Endpoint Stubs ====================================================
# =============================================================================
app = Flask(__name__)

# Store your recipes here!
cookbook = {"recipes": [], "ingredients": []}

# Task 1 helper (don't touch)
@app.route("/parse", methods=['POST'])
def parse():
	data = request.get_json()
	recipe_name = data.get('input', '')
	parsed_name = parse_handwriting(recipe_name)
	if parsed_name is None:
		return 'Invalid recipe name', 400
	return jsonify({'msg': parsed_name}), 200

# [TASK 1] ====================================================================
# Takes in a recipeName and returns it in a form that 
def parse_handwriting(recipeName: str) -> Union[str | None]:
    result = ""

    # treat - and _ as whitespaces
    for word in re.findall(r'[^ _-]+[ _-]*', recipeName):
        res_word = ""

        # remove all characters that are not letters
        for letter in word:
            if letter.isalpha():
                # Make the first letter be uppercase and the rest lowercase
                if len(res_word) == 0:
                    res_word += letter.upper()
                else:
                    res_word += letter.lower()

		# Add only one space between each word
        result += res_word + ' '
    
    if len(result) == 0:
        return None
    else:
        return result.strip()


# [TASK 2] ====================================================================
# Endpoint that adds a CookbookEntry to your magical cookbook
@app.route('/entry', methods=['POST'])
def create_entry():
	data = request.get_json()
	entry_type = data.get('type', '')
	name = data.get('name', '')

	# Check for valid data type
	if entry_type == "recipe":
		required_items = data.get('requiredItems', '')
		result = Recipe(name, required_items)

		# Checks unique entry name
		if not [recipe for recipe in cookbook["recipes"] if recipe.name == name]:
			cookbook["recipes"].append(result)
		else:
			return 'Invalid entry type', 400
	
	elif entry_type == "ingredient":
		cook_time = data.get('cookTime', '')
		if cook_time < 0:
			return f'Invalid cook time for {name}', 400
		result = Ingredient(name, cook_time)

		# Checks unique entry name
		if [ingredient for ingredient in cookbook["ingredients"] if ingredient.name == name]:
			return 'Enter unique names', 400

		cookbook["recipes"].append(result)	
	else:
		return 'Invalid entry type', 400
	
	return jsonify({}), 200

# [TASK 3] ====================================================================
# Endpoint that returns a summary of a recipe that corresponds to a query name
@app.route('/summary', methods=['GET'])
def summary():
	name = request.args.get('name', default='', type=str)
	recipe = [i for i in cookbook["recipes"] if i.name == name]
	ingredient = [i for i in cookbook["ingredients"] if i.name == name]

	if recipe:
		result = get_summary(recipe[0], 1, {"name": recipe[0].name, "cookTime": 0, "ingredients": []})
	elif ingredient:
		result = {"name": ingredient[0].name, "cookTime": ingredient[0].cookTime}
	else:
		return 'Entry not found', 400

	return jsonify(result), 200

# A recursive function that identifies all base ingredients and their specific quantities
def get_summary(recipe, quantity, result):
	for item in recipe.required_items:
		# Finds base ingredients in the item if it is a recipe
		new_recipe = [recipe for recipe in cookbook["recipes"] if recipe.name == item.name]
		if new_recipe:
			result = get_summary(new_recipe[0], quantity * item.quantity, result)
			continue

		# Adds to ingredient quantity if already on the ingredients list
		existing_ingredient = [ingredient for ingredient in result["ingredients"] if ingredient["name"] == item.name]
		if existing_ingredient:
			existing_ingredient["quantity"] += item.quantity * quantity
			continue

		# Checks if ingredient exists in the cookbook
		new_ingredient = [ingredient for ingredient in cookbook["ingredients"] if ingredient.name == item.name]
		if new_ingredient:
			# Adds recipe to the cookbook and its specific quantity and time
			result["ingredients"].append({
				"name": new_ingredient[0].name,
				"quantity": item.quantity * quantity
			}) 
			result["cookTime"] += new_ingredient[0].cook_time * item.quantity * quantity
		else:
			return f'Required item {item.name} does not exist', 400
	return result
# =============================================================================
# ==== DO NOT TOUCH ===========================================================
# =============================================================================

if __name__ == '__main__':
	app.run(debug=True, port=8080)
