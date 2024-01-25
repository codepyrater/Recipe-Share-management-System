import tkinter as tk
from tkinter import messagebox
import re
import mysql.connector
from mysql.connector import Error
import hashlib

# Database configuration
db_config = {
    'user': 'root',
    'password': 'Srikar@123456',
    'host': '127.0.0.1',
    'database': 'RSM',
    'raise_on_warnings': True
}

# Function to create a database connection
def create_db_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        return connection
    except Error as e:
        messagebox.showerror("Database Connection Error", str(e))
        return None

# Function to register a new user
def register_user(username, email, password, confirm_password):
    if password != confirm_password:
        messagebox.showwarning("Password Mismatch", "The passwords do not match.")
        return
    
    # Check password criteria
    if not re.match(r'(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{8,}', password):
        messagebox.showwarning(
            "Password Requirement",
            "Password must be at least 8 characters long, include an uppercase letter, a lowercase letter, and a number."
        )
        return
  

    # Hash the password before storing it
    password_hash = hashlib.sha256(password.strip().encode()).hexdigest()
    print(f"Register Hash: {password_hash}")
    conn = create_db_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO Users (Username, Email, PasswordHash) VALUES (%s, %s, %s)",
                (username, email, password_hash)
            )
            conn.commit()
            messagebox.showinfo("Success", "Registration successful.")
        except Error as e:
            messagebox.showerror("Error", str(e))
        finally:
            cursor.close()
            conn.close()

# Function to verify user login
def verify_login(username, password):
    conn = create_db_connection()
    
    if conn is not None:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT UserID, PasswordHash FROM Users WHERE Username = %s", (username,))
            user = cursor.fetchone()
            cursor.close()
            
            # Hash the input password to compare
            password_hash = hashlib.sha256(password.strip().encode()).hexdigest()
            print(f"Login Hash: {password_hash}")
            print(f"Stored Hash: {user['PasswordHash'] if user else 'No user found'}")

            if user and user['PasswordHash'] == password_hash:
                return user['UserID']
            else:
                return False
        except Error as e:
            messagebox.showerror("Database Query Error", str(e))
        finally:
            conn.close()
    return False


# Function to handle the login button click
logged_in_user_id = None  # Global variable to store the logged-in user's ID

def login_button_clicked():
    global logged_in_user_id
    username = username_entry.get()
    password = password_entry.get()
    user_id = verify_login(username, password)
    if user_id:
        logged_in_user_id = user_id  # Store the UserID
        messagebox.showinfo("Login Success", "You have successfully logged in.")
        main_app_window()  # Redirect to the main application window
    else:
        messagebox.showerror("Login Failed", "The username or password is incorrect.")
        
# Function to handle the register button click
def register_button_clicked():
    username = new_username_entry.get()
    email = email_entry.get()
    password = new_password_entry.get()
    confirm_password = confirm_password_entry.get()
    register_user(username, email, password, confirm_password)
    
    
    
def parse_ingredients(ingredients_str):
    return [ingredient.strip() for ingredient in ingredients_str.split(',')]

    
# Function to submit a recipe to the database
def submit_recipe(title, ingredients_str, steps):
    global logged_in_user_id  # Use the global variable
    conn = create_db_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            query = "INSERT INTO recipes (UserID,  title, ingredients, preparation) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (logged_in_user_id, title, ingredients_str, steps))
            recipe_id = cursor.lastrowid

            # Handle ingredients
            ingredients_list = parse_ingredients(ingredients_str)

            # Filter out numeric values and keep only text
            filtered_ingredients = [re.sub(r'[^a-zA-Z\s]', '', ingredient).strip() for ingredient in ingredients_list]

            # Remove empty strings from the list
            filtered_ingredients = [ingredient for ingredient in filtered_ingredients if ingredient]

            for ingredient in filtered_ingredients:
                # Check if the ingredient exists in the 'Ingredients' table, if not, add it
                cursor.execute("SELECT IngredientID FROM ingredients WHERE Name = %s", (ingredient,))
                result = cursor.fetchone()
                if result:
                    ingredient_id = result[0]
                else:
                    cursor.execute("INSERT INTO ingredients (Name) VALUES (%s)", (ingredient,))
                    ingredient_id = cursor.lastrowid

                # Link the recipe to this ingredient in 'RecipeIngredients'
                cursor.execute("INSERT INTO recipeingredients (RecipeID, IngredientID) VALUES (%s, %s)", (recipe_id, ingredient_id))

            conn.commit()
            messagebox.showinfo("Success", "Recipe submitted successfully.")
        except Error as e:
            messagebox.showerror("Error", f"Error submitting recipe to MySQL database: {e}")
        finally:
            cursor.close()
            conn.close()
    else:
        messagebox.showerror("Error", "Cannot connect to the database.")

def save_updated_recipe(recipe_id, title, ingredients, preparation):
    conn = create_db_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            
            # Step 1: Update recipe details in the 'recipes' table
            cursor.execute("UPDATE recipes SET Title = %s, Ingredients = %s, Preparation = %s WHERE RecipeID = %s",
                           (title, ingredients, preparation, recipe_id))
            
            # Step 2: Delete existing records in 'RecipeIngredients' for the updated recipe
            cursor.execute("DELETE FROM recipeingredients WHERE RecipeID = %s", (recipe_id,))
            
            # Step 3: Split and parse the new ingredients
            new_ingredients = parse_ingredients(ingredients)
            
            for ingredient in new_ingredients:
                # Step 4: Check if the ingredient exists in the 'Ingredients' table, if not, add it
                cursor.execute("SELECT IngredientID FROM ingredients WHERE Name = %s", (ingredient,))
                result = cursor.fetchone()
                if result:
                    ingredient_id = result[0]
                else:
                    cursor.execute("INSERT INTO ingredients (Name) VALUES (%s)", (ingredient,))
                    ingredient_id = cursor.lastrowid

                # Link the recipe to this ingredient in 'RecipeIngredients'
                cursor.execute("INSERT INTO recipeingredients (RecipeID, IngredientID) VALUES (%s, %s)", (recipe_id, ingredient_id))
            
            conn.commit()
            messagebox.showinfo("Success", "Recipe updated successfully.")
        except Error as e:
            messagebox.showerror("Error", f"Error updating recipe: {e}")
        finally:
            cursor.close()
            conn.close()
    else:
        messagebox.showerror("Error", "Cannot connect to the database.")


def update_recipe_window(recipe_id):
    # Fetching the current details of the recipe
    conn = create_db_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT Title, Ingredients, Preparation FROM recipes WHERE RecipeID = %s", (recipe_id,))
            
            recipe = cursor.fetchone()
            cursor.close()

            # Creating a new window for updating the recipe
            update_window = tk.Toplevel()
            update_window.title("Update Recipe")

            tk.Label(update_window, text="Title:").pack()
            title_entry = tk.Entry(update_window)
            title_entry.insert(0, recipe[0])  # Pre-fill with current title
            title_entry.pack()

            tk.Label(update_window, text="Ingredients:").pack()
            ingredients_entry = tk.Entry(update_window)
            ingredients_entry.insert(0, recipe[1])  # Pre-fill with current ingredients
            ingredients_entry.pack()

            tk.Label(update_window, text="Preparation:").pack()
            preparation_entry = tk.Entry(update_window)
            preparation_entry.insert(0, recipe[2])  # Pre-fill with current preparation steps
            preparation_entry.pack()

            # Save Changes Button
            tk.Button(update_window, text="Save Changes", command=lambda: save_updated_recipe(recipe_id, title_entry.get(), ingredients_entry.get(), preparation_entry.get())).pack()

            # Delete Button
            tk.Button(update_window, text="Delete Recipe", command=lambda: delete_recipe(recipe_id)).pack()
        except Error as e:
            messagebox.showerror("Error", f"Error fetching recipe details: {e}")
        finally:
            conn.close()
    else:
        messagebox.showerror("Error", "Cannot connect to the database.")

# Function to delete a recipe
def delete_recipe(recipe_id):
    conn = create_db_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM recipes WHERE RecipeID = %s", (recipe_id,))
            conn.commit()
            messagebox.showinfo("Success", "Recipe deleted successfully.")
        except Error as e:
            messagebox.showerror("Error", f"Error deleting recipe: {e}")
        finally:
            cursor.close()
            conn.close()
    else:
        messagebox.showerror("Error", "Cannot connect to the database.")
     




def view_update_recipes_window():
    view_window = tk.Toplevel()
    view_window.title("View/Update Recipes")

    # Fetching recipes from the database
    conn = create_db_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT RecipeID, Title FROM recipes WHERE UserID = %s", (logged_in_user_id,))
            for recipe in cursor.fetchall():
                recipe_id = recipe[0]
                title = recipe[1]
                tk.Label(view_window, text=title).pack()
                tk.Button(view_window, text="Edit", command=lambda id=recipe_id: edit_recipe(id)).pack()
                tk.Button(view_window, text="Delete", command=lambda id=recipe_id: delete_recipe(id)).pack()
        except Error as e:
            messagebox.showerror("Error", f"Error fetching recipes from MySQL database: {e}")
        finally:
            cursor.close()
            conn.close()
    else:
        messagebox.showerror("Error", "Cannot connect to the database.")

def edit_recipe(recipe_id):
    # Open a window to edit the recipe
    edit_window = tk.Toplevel()
    edit_window.title("Edit Recipe")

    # Fetch and display the existing recipe details
    conn = create_db_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT Title, Ingredients, Preparation FROM recipes WHERE RecipeID = %s", (recipe_id,))
            recipe = cursor.fetchone()
            if recipe:
                title = recipe[0]
                ingredients = recipe[1]
                preparation = recipe[2]

                tk.Label(edit_window, text="Title:").pack()
                title_entry = tk.Entry(edit_window)
                title_entry.insert(0, title)
                title_entry.pack()

                tk.Label(edit_window, text="Ingredients:").pack()
                ingredients_entry = tk.Entry(edit_window)
                ingredients_entry.insert(0, ingredients)
                ingredients_entry.pack()

                tk.Label(edit_window, text="Preparation:").pack()
                preparation_entry = tk.Entry(edit_window)
                preparation_entry.insert(0, preparation)
                preparation_entry.pack()

                # Update button to save changes
                tk.Button(edit_window, text="Update", command=lambda: save_updated_recipe(recipe_id, title_entry.get(), ingredients_entry.get(), preparation_entry.get())).pack()

            else:
                messagebox.showerror("Error", "Recipe not found.")
        except Error as e:
            messagebox.showerror("Error", f"Error fetching recipe details from MySQL database: {e}")
        finally:
            cursor.close()
            conn.close()
    else:
        messagebox.showerror("Error", "Cannot connect to the database.")

def delete_recipe(recipe_id):
    # Delete the recipe with the given recipe_id
    conn = create_db_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM recipes WHERE RecipeID = %s", (recipe_id,))
            conn.commit()
            messagebox.showinfo("Success", "Recipe deleted successfully.")
        except Error as e:
            messagebox.showerror("Error", f"Error deleting recipe from MySQL database: {e}")
        finally:
            cursor.close()
            conn.close()
    else:
        messagebox.showerror("Error", "Cannot connect to the database.")


def ingredient_input_window():
    ingredient_window = tk.Toplevel()
    ingredient_window.title("Input Ingredients")

    tk.Label(ingredient_window, text="Enter Ingredients (comma-separated):").pack()
    ingredients_entry = tk.Entry(ingredient_window)
    ingredients_entry.pack()

    tk.Button(ingredient_window, text="Submit Ingredients", command=lambda: submit_user_ingredients(ingredients_entry.get(), ingredient_window)).pack()



def get_recipe_suggestions(ingredient_list):
    suggestion_window = tk.Toplevel()
    suggestion_window.title("Recipe Suggestions")

    conn = create_db_connection()
    if conn is not None:
        try:
            cursor = conn.cursor(dictionary=True)
            format_strings = ','.join(['%s'] * len(ingredient_list))
            query = f"""
            SELECT DISTINCT r.RecipeID, r.Title, r.Preparation, r.Ingredients
            FROM Recipes r
            JOIN RecipeIngredients ri ON r.RecipeID = ri.RecipeID
            JOIN Ingredients i ON ri.IngredientID = i.IngredientID
            WHERE ri.IngredientID IN (SELECT IngredientID FROM Ingredients WHERE Name IN ({format_strings}))
            GROUP BY r.RecipeID, r.Title, r.Preparation, r.Ingredients
            """
            cursor.execute(query, tuple(ingredient_list))

            for recipe in cursor.fetchall():
                recipe_title = recipe['Title']
                recipe_preparation = recipe['Preparation']
                recipe_ingredients = recipe['Ingredients']
                tk.Label(suggestion_window, text=f"Title: {recipe_title}").pack()
                tk.Label(suggestion_window, text=f"Ingredients: {recipe_ingredients}").pack()
                tk.Label(suggestion_window, text=f"Preparation: {recipe_preparation}").pack()
                tk.Label(suggestion_window, text="----------------------------------").pack()
        except Error as e:
            messagebox.showerror("Error", f"Error fetching recipe suggestions: {e}")
        finally:
            cursor.close()
            conn.close()
    else:
        messagebox.showerror("Error", "Cannot connect to the database.")

def submit_user_ingredients(ingredients, window):
    ingredient_list = [ingredient.strip() for ingredient in ingredients.split(',')]
    conn = create_db_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            for ingredient in ingredient_list:
                # Assuming you have a function to get IngredientID from ingredient name
                ingredient_id = get_ingredient_id(ingredient, cursor)
                if ingredient_id:
                    cursor.execute("INSERT INTO UserIngredients (UserID, IngredientID) VALUES (%s, %s)", (logged_in_user_id, ingredient_id))
            conn.commit()
            messagebox.showinfo("Success", "Ingredients submitted successfully.")
            window.destroy()
            get_recipe_suggestions(ingredient_list)
        except Error as e:
            messagebox.showerror("Error", f"Error submitting ingredients: {e}")
        finally:
            cursor.close()
            conn.close()
    else:
        messagebox.showerror("Error", "Cannot connect to the database.")

def get_ingredient_id(ingredient_name, cursor):
    cursor.execute("SELECT IngredientID FROM Ingredients WHERE Name = %s", (ingredient_name,))
    result = cursor.fetchone()
    return result[0] if result else None



# Function to create the Add Recipe window
def add_recipe_window():
    add_window = tk.Toplevel()
    add_window.geometry("1000x800")
    add_window.title("Add New Recipe")
    

    tk.Label(add_window, text="Recipe Title").pack()
    title_entry = tk.Entry(add_window)
    title_entry.pack()

    tk.Label(add_window, text="Ingredients").pack()
    ingredients_entry = tk.Entry(add_window)
    ingredients_entry.pack()

    tk.Label(add_window, text="Preparation Steps").pack()
    steps_entry = tk.Entry(add_window)
    steps_entry.pack()

    tk.Button(add_window, text="Submit", command=lambda: submit_recipe(title_entry.get(), ingredients_entry.get(), steps_entry.get())).pack()


# Function for creating the main application window
def main_app_window():
    root.destroy()  # Close the login window
    main_window = tk.Tk()
    main_window.geometry("1000x800")
    main_window.title("Recipe Share Management System")

    tk.Button(main_window, text="Add Recipe", command=add_recipe_window).pack(pady=50)
    tk.Button(main_window, text="View/Update Recipe", command=view_update_recipes_window).pack(pady=50)
    tk.Button(main_window, text="Get Suggestions", command=ingredient_input_window).pack(pady=50)
    
    

    main_window.mainloop()
  

# Function for creating the registration form
def show_registration_form():
    global new_username_entry, email_entry, new_password_entry, confirm_password_entry
    
    register_window = tk.Toplevel()
    register_window.title("Register New User")

    tk.Label(register_window, text="Username:").pack()
    new_username_entry = tk.Entry(register_window)
    new_username_entry.pack()

    tk.Label(register_window, text="Email:").pack()
    email_entry = tk.Entry(register_window)
    email_entry.pack()

    tk.Label(register_window, text="Password:").pack()
    new_password_entry = tk.Entry(register_window)
    new_password_entry.pack()

    tk.Label(register_window, text="Confirm Password:").pack()
    confirm_password_entry = tk.Entry(register_window, show="*")
    confirm_password_entry.pack()

    register_button = tk.Button(register_window, text="Register", command=register_button_clicked)
    register_button.pack()

# Tkinter GUI for Login
root = tk.Tk()
root.geometry("1000x800")
root.title("Login")

tk.Label(root, text="Username:").pack()
username_entry = tk.Entry(root)
username_entry.pack()

tk.Label(root, text="Password:").pack()
password_entry = tk.Entry(root, show="*")
password_entry.pack()

login_button = tk.Button(root, text="Login", command=login_button_clicked)
login_button.pack()

register_label = tk.Label(root, text="New user?")
register_label.pack()

register_button = tk.Button(root, text="Register", command=show_registration_form)
register_button.pack()

root.mainloop()
