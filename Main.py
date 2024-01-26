import tkinter as tk
from tkinter import messagebox, font, PhotoImage
import re
import mysql.connector
from mysql.connector import Error
import hashlib
from PIL import Image, ImageTk

# Database configuration
db_config = {
    'user': 'root',
    'password': 'Srikar@123456',
    'host': '127.0.0.1',
    'database': 'RSM',
    'raise_on_warnings': True
}



# Style settings
bg_color = "lightblue"
button_color = "lightblue"
heading_font = ("Helvetica", 18, "bold")
label_font = ("Helvetica", 12)
entry_font = ("Helvetica", 12)



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
    if not is_valid_email(email):
        messagebox.showwarning("Invalid Email", "Please enter a valid email address.")
        return
    
# Check password criteria
    # Regex explanation:
    # ^(?=.*\d) - At least one digit
    # (?=.*[A-Z]) - At least one uppercase letter
    # (?=.*[!@#$%^&*()]) - At least one special character
    # .{8,12}$ - Length between 8 to 12 characters
    if not re.match(r"^(?=.*\d)(?=.*[A-Z])(?=.*[!@#$%^&*()]).{8,12}$", password):
        messagebox.showwarning(
            "Password Requirement",
            "Password must be 8-12 characters long, include an uppercase letter, a number, and a special character."
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
            

def is_valid_email(email):
    # Regular expression for validating an Email
    regex = r'^[a-zA-Z0-9._%-]+@(gmail\.com|cmich\.edu|outlook\.com)$'
    if re.match(regex, email):
        return True
    else:
        return False


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


# Function to create the Add Recipe window
def add_recipe_window():
    add_window = tk.Toplevel()
    add_window.geometry("1000x800")
    add_window.title("Add New Recipe")
    add_window.configure(bg=bg_color)
    
    
    center_frame = tk.Frame(add_window, bg=bg_color)
    center_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
    
    
    

    tk.Label(center_frame, text="Recipe Title",  font=label_font, bg=bg_color).pack()
    title_entry = tk.Entry(center_frame)
    title_entry.pack()

    tk.Label(center_frame, text="Ingredients", font=label_font, bg=bg_color).pack()
    ingredients_entry = tk.Entry(center_frame)
    ingredients_entry.pack()

    tk.Label(center_frame, text="Preparation Steps", font=label_font, bg=bg_color).pack()
    steps_entry = tk.Entry(center_frame)
    steps_entry.pack()

    tk.Button(center_frame, text="Submit", command=lambda: submit_recipe(title_entry.get(), ingredients_entry.get(), steps_entry.get())).pack(pady=10)



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







def view_update_recipes_window():
    view_window = tk.Toplevel()
    view_window.title("View/Update Recipes")
    view_window.configure(bg=bg_color)
    view_window.geometry("1000x800")
    
    
    center_frame = tk.Frame(view_window, bg=bg_color)
    center_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
    # Fetching recipes from the database
    conn = create_db_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT RecipeID, Title FROM recipes WHERE UserID = %s", (logged_in_user_id,))
            for recipe in cursor.fetchall():
                recipe_id = recipe[0]
                title = recipe[1]
                tk.Label(center_frame, text="Recipe Name: "+title, font=label_font, bg=bg_color).pack()
                tk.Button(center_frame, text="Edit",font=label_font, bg="lightgrey", command=lambda id=recipe_id: edit_recipe(id)).pack()
                tk.Button(center_frame, text="Delete",font=label_font, bg="lightgrey", command=lambda id=recipe_id: delete_recipe(id)).pack()
        except Error as e:
            messagebox.showerror("Error", f"Error fetching recipes from MySQL database: {e}")
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



def edit_recipe(recipe_id):
    # Open a window to edit the recipe
    edit_window = tk.Toplevel()
    edit_window.title("Edit Recipe")
    edit_window.configure(bg=bg_color)
    edit_window.geometry("1000x800")
    
    
    center_frame = tk.Frame(edit_window, bg=bg_color)
    center_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
    

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

                tk.Label(center_frame, text="Title:", font=label_font, bg=bg_color).pack()
                title_entry = tk.Entry(center_frame)
                title_entry.insert(0, title)
                title_entry.pack()

                tk.Label(center_frame, text="Ingredients:", font=label_font, bg=bg_color).pack()
                ingredients_entry = tk.Entry(center_frame)
                ingredients_entry.insert(0, ingredients)
                ingredients_entry.pack()

                tk.Label(center_frame, text="Preparation:", font=label_font, bg=bg_color).pack()
                preparation_entry = tk.Entry(center_frame)
                preparation_entry.insert(0, preparation)
                preparation_entry.pack()

                # Update button to save changes
                tk.Button(center_frame, text="Update", command=lambda: save_updated_recipe(recipe_id, title_entry.get(), ingredients_entry.get(), preparation_entry.get())).pack()

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
            # First, delete any related entries in the 'recipeingredients' table
            cursor.execute("DELETE FROM recipeingredients WHERE RecipeID = %s", (recipe_id,))
            # Now, it's safe to delete the recipe from the 'recipes' table
            cursor.execute("DELETE FROM recipes WHERE RecipeID = %s", (recipe_id,))
            conn.commit()
            messagebox.showinfo("Success", "Recipe deleted successfully.")
        except Error as e:
            # Rollback in case there is any error
            conn.rollback()
            messagebox.showerror("Error", f"Error deleting recipe: {e}")
        finally:
            cursor.close()
            conn.close()
    else:
        messagebox.showerror("Error", "Cannot connect to the database.")



def ingredient_input_window():
    ingredient_window = tk.Toplevel()
    ingredient_window.title("Input Ingredients")
    ingredient_window.configure(bg=bg_color)
    ingredient_window.geometry("1000x800")
    
    
    center_frame = tk.Frame(ingredient_window, bg=bg_color)
    center_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

    tk.Label(center_frame, text="Enter Ingredients (comma-separated):", bg= "lightblue").pack(fill='x', pady=10)
    ingredients_entry = tk.Entry(center_frame)
    ingredients_entry.pack()

    tk.Button(center_frame, text="Submit Ingredients", command=lambda: submit_user_ingredients(ingredients_entry.get(), ingredient_window)).pack(fill='x', pady=10)



def get_recipe_suggestions(ingredient_list):
    suggestion_window = tk.Toplevel()
    suggestion_window.title("Recipe Suggestions")
    suggestion_window.configure(bg=bg_color)
    suggestion_window.geometry("1000x800")
    
    
    center_frame = tk.Frame(suggestion_window, bg=bg_color)
    center_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

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
                tk.Label(center_frame, text=f"Title: {recipe_title}").pack()
                tk.Label(center_frame, text=f"Ingredients: {recipe_ingredients}").pack()
                tk.Label(center_frame, text=f"Preparation: {recipe_preparation}").pack()
                tk.Label(center_frame, text="----------------------------------").pack()
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




# Function for creating the main application window
def main_app_window():
    root.destroy()  # Close the login window
    main_window = tk.Tk()
    # Center frame
  
    
    
    main_window.geometry("1000x800")
    main_window.title("Culinary Canvas")
    main_window.configure(bg=bg_color)
    
    center_frame = tk.Frame(main_window, bg=bg_color)
    center_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
    
     # Heading label for the main application window
 

    # Buttons packed within the center frame
    tk.Button(center_frame, text="Add Recipe", command=add_recipe_window, bg='lightgrey').pack(fill='x', pady=10)
    tk.Button(center_frame, text="View/Update Recipe", command=view_update_recipes_window, bg='lightgrey').pack(fill='x', pady=10)
    tk.Button(center_frame, text="Get Suggestions", command=ingredient_input_window, bg='lightgrey').pack(fill='x', pady=10)
  
    

    main_window.mainloop()
  

# Function for creating the registration form
def show_registration_form():
    global new_username_entry, email_entry, new_password_entry, confirm_password_entry, bg_color, label_font
    
    # Create the top-level window
    register_window = tk.Toplevel()
    register_window.geometry("1000x800")  # Adjust size as needed
    register_window.configure(bg=bg_color)
    
    # Set window size
    window_width = 1000
    window_height = 800
    register_window.geometry(f"{window_width}x{window_height}")


    
    
    
    register_window.title("Register New User")

    
    # Center frame
    center_frame = tk.Frame(register_window, bg=bg_color)
    center_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
    
    # Heading
    heading_label = tk.Label(center_frame, text="User Registration", font=heading_font, bg=bg_color)
    heading_label.pack(pady=20)

    tk.Label(center_frame,text="Username:", font=label_font, bg=bg_color).pack()
    new_username_entry = tk.Entry(center_frame)
    new_username_entry.pack()

    tk.Label(center_frame,text="Email:", font=label_font, bg=bg_color).pack()
    email_entry = tk.Entry(center_frame)
    email_entry.pack()

    tk.Label(center_frame, text="Password:", font=label_font, bg=bg_color).pack()
    new_password_entry = tk.Entry(center_frame)
    new_password_entry.pack()

    tk.Label(center_frame, text="Confirm Password:", font=label_font, bg=bg_color).pack()
    confirm_password_entry = tk.Entry(center_frame, show="*")
    confirm_password_entry.pack()

    register_button = tk.Button(center_frame, text="Register", command=register_button_clicked)
    register_button.pack(pady=20)
   

# Tkinter GUI for Login
root = tk.Tk()
root.geometry("1000x800")
root.title("Culinary Canvas")
root.configure(bg=bg_color)


 # Heading
heading_label = tk.Label( text="Culinary Canvas", font=heading_font, bg=bg_color)
heading_label.pack(pady=20)

desired_width = 300
desired_height = 250

# Load the image
image = Image.open("Main_pic.jpeg")
# Resize the image to desired dimensions
image = image.resize((desired_width, desired_height))
    
logo_image = ImageTk.PhotoImage(image)
logo_label = tk.Label(root, image=logo_image, bg=bg_color)  # Assume the background of your image is white
logo_label.pack(pady=20)
    

tk.Label(root, text="Username:", font=label_font, bg=bg_color).pack()
username_entry = tk.Entry(root)
username_entry.pack()

tk.Label(root, text="Password:", font=label_font, bg=bg_color).pack()
password_entry = tk.Entry(root, show="*")
password_entry.pack()

login_button = tk.Button(root, text="Login", command=login_button_clicked)
login_button.pack(pady=10)

register_label = tk.Label(root, text="New user?",bg=bg_color, font=label_font)
register_label.pack(pady=10)

register_button = tk.Button(root, text="Register", command=show_registration_form)
register_button.pack(pady=10)

root.mainloop()
