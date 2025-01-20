import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import json
import os

# Plantilla base para un modelo de LoopBack 3
MODEL_TEMPLATE = {
    "name": "",
    "plural": "",
    "base": "Model",
    "idInjection": True,
    "options": {
        "validateUpsert": True
    },
    "properties": {},
    "validations": [],
    "relations": {},
    "acls": [],
    "methods": {}
}

JS_TEMPLATE = "'use strict';\n\
module.exports = function({modelName}) { \n\
    // Nombre del modelo: {modelName}\n\
    {modelName}.CreateOne = function(modelData, callback) {\n\
        {modelName}.findOrCreate(\n\
            {\n\
                where: { id: modelData.id }\n\
            },\n\
            modelData,\n\
            (err, newModelData) => {\n\
                if (err) return callback(err);\n\
                return callback(null, newModelData);\n\
            }\n\
        );\n\
    };\n\
};\n"






class LoopbackModelGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("LoopBack 3 Model Manager")

         # Variables
        self.api_path = None
        self.model_config_path = None
        self.models_dir = None
        self.datasources = []

        # Interfaz principal
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        ttk.Button(self.main_frame, text="Select API Folder", command=self.select_api_folder).grid(row=0, column=0, sticky=tk.W)

        self.api_path_label = ttk.Label(self.main_frame, text="No API folder selected.")
        self.api_path_label.grid(row=0, column=1, sticky=tk.W)

        # Frame para el Treeview y el Scrollbar
        tree_frame = ttk.Frame(self.main_frame)
        tree_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Scrollbar vertical
        tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical")
        tree_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # Treeview para mostrar los modelos existentes
        self.tree = ttk.Treeview(tree_frame, columns=("Name", "Plural"), show="headings", yscrollcommand=tree_scroll.set)
        self.tree.heading("Name", text="Name")
        self.tree.heading("Plural", text="Plural")
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Vincular el scrollbar al Treeview
        tree_scroll.config(command=self.tree.yview)

        # Botones para acciones
        ttk.Button(self.main_frame, text="Create New Model", command=self.create_model).grid(row=2, column=0, sticky=tk.W)
        ttk.Button(self.main_frame, text="Edit Selected Model", command=self.edit_model).grid(row=2, column=1, sticky=tk.W)
        ttk.Button(self.main_frame, text="Delete Selected Model", command=self.delete_model).grid(row=2, column=2, sticky=tk.W)
        ttk.Button(self.main_frame, text="Refresh Models", command=self.load_models).grid(row=3, column=0, columnspan=3, sticky=tk.W)

    def select_api_folder(self):
        """Selecciona la carpeta principal de la API y verifica su estructura."""
        api_path = filedialog.askdirectory(title="Select LoopBack API Folder")
        if not api_path:
            return

        model_config_path = os.path.join(api_path, "server", "model-config.json")
        models_dir = os.path.join(api_path, "server", "models")
        datasources_path = os.path.join(api_path, "server", "datasources.json")

        if not os.path.exists(model_config_path) or not os.path.exists(models_dir) or not os.path.exists(datasources_path):
            messagebox.showerror("Error", "Invalid API folder. Ensure it contains 'server/model-config.json', 'server/models', and 'server/datasources.json'.")
            return

        self.api_path = api_path
        self.model_config_path = model_config_path
        self.models_dir = models_dir

        # Cargar datasources
        with open(datasources_path, "r") as f:
            self.datasources = list(json.load(f).keys())

        self.api_path_label.config(text=f"API Folder: {api_path}")
        self.load_models()

    def load_models(self):
        """Carga los modelos existentes desde model-config.json."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        with open(self.model_config_path, "r") as f:
            model_config = json.load(f)

        for model_name, config in model_config.items():
            if model_name != "_meta":
                self.tree.insert("", "end", values=(model_name, config.get("plural", "")))

    def create_model(self):
        """Abre una ventana para crear un nuevo modelo."""
        if not self.api_path:
            messagebox.showerror("Error", "Please select an API folder first.")
            return

        ModelEditor(self.root, self.model_config_path, self.models_dir, self.datasources, callback=self.load_models)

    def edit_model(self):
        """Edita el modelo seleccionado."""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a model to edit.")
            return

        model_name = self.tree.item(selected_item, "values")[0]
        ModelEditor(self.root, self.model_config_path, self.models_dir, self.datasources, model_name, callback=self.load_models)

    def delete_model(self):
        """Elimina el modelo seleccionado."""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a model to delete.")
            return

        model_name = self.tree.item(selected_item, "values")[0]
        confirm = messagebox.askyesno("Confirm", f"Are you sure you want to delete the model '{model_name}'?")
        if not confirm:
            return

        # Eliminar del model-config.json
        with open(self.model_config_path, "r") as f:
            model_config = json.load(f)

        if model_name in model_config:
            del model_config[model_name]

        with open(self.model_config_path, "w") as f:
            json.dump(model_config, f, indent=2)

        # Eliminar archivos del modelo
        model_json_path = os.path.join(self.models_dir, f"{model_name}.json")
        model_js_path = os.path.join(self.models_dir, f"{model_name}.js")
        if os.path.exists(model_json_path):
            os.remove(model_json_path)
        if os.path.exists(model_js_path):
            os.remove(model_js_path)

        self.load_models()
        messagebox.showinfo("Success", f"Model '{model_name}' deleted successfully.")

class ModelEditor:
    def __init__(self, parent, model_config_path, models_dir, datasources, model_name=None, callback=None):
        self.model_config_path = model_config_path
        self.models_dir = models_dir
        self.datasources = datasources
        self.model_name = model_name

        self.window = tk.Toplevel(parent)
        self.window.title("Model Editor")

        ttk.Label(self.window, text="Model Name:").grid(row=0, column=0, sticky=tk.W)
        self.model_name_var = tk.StringVar()
        self.model_name_entry = ttk.Entry(self.window, textvariable=self.model_name_var, width=30)
        self.model_name_entry.grid(row=0, column=1, sticky=tk.W)

        ttk.Label(self.window, text="Datasource:").grid(row=1, column=0, sticky=tk.W)
        self.datasource_var = tk.StringVar()
        self.datasource_combo = ttk.Combobox(self.window, textvariable=self.datasource_var, values=self.datasources, state="readonly")
        self.datasource_combo.grid(row=1, column=1, sticky=tk.W)

        ttk.Button(self.window, text="Add Property", command=self.add_property).grid(row=2, column=0, sticky=tk.W)
        ttk.Button(self.window, text="Add Relation", command=self.add_relation).grid(row=2, column=1, sticky=tk.W)
        ttk.Button(self.window, text="Add Method", command=self.add_method).grid(row=2, column=2, sticky=tk.W)
        ttk.Button(self.window, text="Save", command=self.save_model).grid(row=3, column=0, columnspan=3)

        self.properties_frame = ttk.LabelFrame(self.window, text="Properties")
        self.properties_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E))

        self.relations_frame = ttk.LabelFrame(self.window, text="Relations")
        self.relations_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E))

        self.methods_frame = ttk.LabelFrame(self.window, text="Methods")
        self.methods_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E))

        self.properties = {}
        self.relations = {}
        self.methods = {}

        if model_name:
            self.load_model()

    def load_model(self):
        """Carga los datos de un modelo existente."""
        model_path = os.path.join(self.models_dir, f"{self.model_name}.json")
        if os.path.exists(model_path):
            with open(model_path, "r") as f:
                model_data = json.load(f)

            self.model_name_var.set(model_data.get("name", ""))
            self.properties = model_data.get("properties", {})
            self.relations = model_data.get("relations", {})
            self.methods = model_data.get("methods", {})

            for prop_name, prop_data in self.properties.items():
                ttk.Label(self.properties_frame, text=f"{prop_name}: {prop_data}").pack(anchor=tk.W)

            for rel_name, rel_data in self.relations.items():
                ttk.Label(self.relations_frame, text=f"{rel_name}: {rel_data}").pack(anchor=tk.W)

            for method_name, method_data in self.methods.items():
                ttk.Label(self.methods_frame, text=f"{method_name}: {method_data}").pack(anchor=tk.W)

    def add_property(self):
        """Agrega una nueva propiedad al modelo."""
        prop_name = simpledialog.askstring("Property Name", "Enter property name:")
        prop_type = simpledialog.askstring("Property Type", "Enter property type (e.g., string, number, date):")
        if prop_name and prop_type:
            self.properties[prop_name] = {"type": prop_type}
            ttk.Label(self.properties_frame, text=f"{prop_name}: {prop_type}").pack(anchor=tk.W)

    def add_relation(self):
        """Agrega una nueva relación al modelo."""
        rel_name = simpledialog.askstring("Relation Name", "Enter relation name:")
        rel_type = simpledialog.askstring("Relation Type", "Enter relation type (e.g., belongsTo, hasMany):")
        rel_model = simpledialog.askstring("Related Model", "Enter related model:")
        foreign_key = simpledialog.askstring("Foreign Key", "Enter foreign key:")
        if rel_name and rel_type and rel_model:
            self.relations[rel_name] = {
                "type": rel_type,
                "model": rel_model,
                "foreignKey": foreign_key
            }
            ttk.Label(self.relations_frame, text=f"{rel_name}: {rel_type} -> {rel_model} ({foreign_key})").pack(anchor=tk.W)

    def add_method(self):
        """Agrega un nuevo método al modelo."""
        method_name = simpledialog.askstring("Method Name", "Enter method name:")
        http_path = simpledialog.askstring("HTTP Path", "Enter HTTP path (e.g., /custom-endpoint):")
        http_verb = simpledialog.askstring("HTTP Verb", "Enter HTTP verb (e.g., get, post):")

        if not method_name or not http_path or not http_verb:
            return

        args = []
        while True:
            arg_name = simpledialog.askstring("Argument Name", "Enter argument name (or leave blank to finish):")
            if not arg_name:
                break
            arg_type = simpledialog.askstring("Argument Type", "Enter argument type (e.g., string, object):")
            arg_source = simpledialog.askstring("Argument Source", "Enter argument source (e.g., body, query):")
            args.append({"arg": arg_name, "type": arg_type, "http": {"source": arg_source}})

        self.methods[method_name] = {
            "http": {
                "path": http_path,
                "verb": http_verb
            },
            "accepts": args,
            "returns": {"arg": "result", "type": "object", "root": True},
            "description": f"Custom method {method_name}"
        }

        ttk.Label(self.methods_frame, text=f"{method_name}: {http_verb.upper()} {http_path}").pack(anchor=tk.W)

    def save_model(self):
        """Guarda los datos del modelo."""
        model_name = self.model_name_var.get().strip()
        if not model_name:
            messagebox.showerror("Error", "Model name cannot be empty.")
            return

        plural_name = model_name + "s"
        new_model = MODEL_TEMPLATE.copy()
        new_model["name"] = model_name
        new_model["plural"] = plural_name
        new_model["properties"] = self.properties
        new_model["relations"] = self.relations
        new_model["methods"] = self.methods

        # Guardar el modelo en un archivo JSON
        model_path = os.path.join(self.models_dir, f"{model_name}.json")
        os.makedirs(self.models_dir, exist_ok=True)
        with open(model_path, "w") as f:
            json.dump(new_model, f, indent=2)

        # Guardar el archivo .js
        js_path = os.path.join(self.models_dir, f"{model_name}.js")
        
        # Usar concatenación de cadenas en lugar de str.format()
        js_content = "'use strict';\n\n" \
                    "module.exports = function(" + model_name + ") { \n" \
                    "    // Nombre del modelo: " + model_name + "\n" \
                    "};\n"

        # Guardar el contenido en el archivo .js
        with open(js_path, "w") as f:
            f.write(js_content)



        # Actualizar model-config.json
        with open(self.model_config_path, "r") as f:
            model_config = json.load(f)

        model_config[model_name] = {
            "dataSource": self.datasource_var.get(),
            "public": True
        }

        with open(self.model_config_path, "w") as f:
            json.dump(model_config, f, indent=2)

        messagebox.showinfo("Success", f"Model '{model_name}' saved successfully.")
        self.window.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = LoopbackModelGUI(root)
    root.mainloop()