import os
import json
import tkinter as tk
from tkinter import ttk, messagebox

# Chemins vers les fichiers JSON et dossiers
dir_script = os.path.dirname(os.path.abspath(__file__))
dir_data = os.path.join(dir_script, 'data')
file_rules = os.path.join(dir_data, 'disease_rules.json')
file_symptoms = os.path.join(dir_data, 'disease_symptoms.json')
file_questions = os.path.join(dir_data, 'symptom_questions.json')
dir_desc = os.path.join(dir_data, 'disease_descriptions')
dir_treat = os.path.join(dir_data, 'disease_treatments')

# Assurer l'existence des dossiers
os.makedirs(dir_desc, exist_ok=True)
os.makedirs(dir_treat, exist_ok=True)

# Charger ou initialiser les données JSON
for path in (file_rules, file_symptoms, file_questions):
    if not os.path.exists(path):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({}, f, indent=2, ensure_ascii=False)

with open(file_rules, 'r', encoding='utf-8') as f:
    disease_rules = json.load(f)
with open(file_symptoms, 'r', encoding='utf-8') as f:
    disease_symptoms = json.load(f)
with open(file_questions, 'r', encoding='utf-8') as f:
    symptom_questions = json.load(f)

class ExpertApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Medical Expert ADK - Gestion maladies")
        self.geometry('585x400')
        self.resizable(False, False)

        notebook = ttk.Notebook(self)
        self.frame_add = ttk.Frame(notebook, padding=10)
        self.frame_symp = ttk.Frame(notebook, padding=10)
        notebook.add(self.frame_add, text='Ajouter maladie')
        notebook.add(self.frame_symp, text='Ajouter symptôme')
        notebook.pack(expand=True, fill='both')

        self.build_add_disease()
        self.build_add_symptom()

    def build_add_disease(self):
        # Nom
        ttk.Label(self.frame_add, text="Nom de la maladie:").grid(row=0, column=0, sticky='w')
        self.entry_name = ttk.Entry(self.frame_add, width=30)
        self.entry_name.grid(row=0, column=1, sticky='w')
        # Description
        ttk.Label(self.frame_add, text="Description:").grid(row=1, column=0, sticky='nw', pady=(10,0))
        self.text_desc = tk.Text(self.frame_add, width=50, height=5)
        self.text_desc.grid(row=1, column=1, pady=(10,0))
        # Traitement
        ttk.Label(self.frame_add, text="Traitement:").grid(row=2, column=0, sticky='nw', pady=(10,0))
        self.text_treat = tk.Text(self.frame_add, width=50, height=5)
        self.text_treat.grid(row=2, column=1, pady=(10,0))
        # Symptômes
        ttk.Label(self.frame_add, text="Symptômes:").grid(row=3, column=0, sticky='nw', pady=(10,0))
        self.symp_frame = ttk.Frame(self.frame_add)
        self.symp_frame.grid(row=3, column=1, sticky='w')
        self.symp_vars = {}
        self.refresh_symptoms()
        # Bouton sauvegarder
        btn = ttk.Button(self.frame_add, text="Enregistrer maladie", command=self.save_disease)
        btn.grid(row=4, column=1, pady=20, sticky='e')

    def refresh_symptoms(self):
        # Vider
        for w in self.symp_frame.winfo_children():
            w.destroy()
        # Checkbuttons
        for i, (symp, q) in enumerate(symptom_questions.items()):
            var = tk.BooleanVar()
            chk = ttk.Checkbutton(self.symp_frame, text=symp.replace('_', ' '), variable=var)
            chk.grid(row=i//3, column=i%3, sticky='w', padx=5, pady=2)
            self.symp_vars[symp] = var

    def save_disease(self):
        name = self.entry_name.get().strip()
        desc = self.text_desc.get('1.0', 'end').strip()
        treat = self.text_treat.get('1.0', 'end').strip()
        if not name or not desc or not treat:
            messagebox.showerror("Erreur", "Remplissez tous les champs (nom, description, traitement).")
            return
        # Symptômes sélectionnés
        sel = [s for s, v in self.symp_vars.items() if v.get()]
        # Construire rule
        rule = {s: ('yes' if s in sel else 'no') for s in symptom_questions}
        # Sauvegarder JSON
        disease_rules[name] = rule
        disease_symptoms[name] = sel
        with open(file_rules, 'w', encoding='utf-8') as f:
            json.dump(disease_rules, f, indent=2, ensure_ascii=False)
        with open(file_symptoms, 'w', encoding='utf-8') as f:
            json.dump(disease_symptoms, f, indent=2, ensure_ascii=False)
        # Fichiers txt
        with open(os.path.join(dir_desc, f"{name}.txt"), 'w', encoding='utf-8') as f:
            f.write(desc)
        with open(os.path.join(dir_treat, f"{name}.txt"), 'w', encoding='utf-8') as f:
            f.write(treat)
        messagebox.showinfo("Succès", f"Maladie '{name}' enregistrée.")
        # Réinitialiser
        self.entry_name.delete(0, 'end')
        self.text_desc.delete('1.0', 'end')
        self.text_treat.delete('1.0', 'end')
        for v in self.symp_vars.values():
            v.set(False)

    def build_add_symptom(self):
        ttk.Label(self.frame_symp, text="Clé symptôme (ex: nausea):").grid(row=0, column=0, sticky='w')
        self.entry_symp_key = ttk.Entry(self.frame_symp, width=30)
        self.entry_symp_key.grid(row=0, column=1, sticky='w')
        ttk.Label(self.frame_symp, text="Question (ex: Avez-vous ...?):").grid(row=1, column=0, sticky='nw', pady=(10,0))
        self.text_symp_q = tk.Text(self.frame_symp, width=50, height=3)
        self.text_symp_q.grid(row=1, column=1, pady=(10,0))
        btn2 = ttk.Button(self.frame_symp, text="Enregistrer symptôme", command=self.save_symptom)
        btn2.grid(row=2, column=1, pady=20, sticky='e')

    def save_symptom(self):
        key = self.entry_symp_key.get().strip()
        q = self.text_symp_q.get('1.0', 'end').strip()
        if not key or not q:
            messagebox.showerror("Erreur", "Clé et question obligatoires.")
            return
        if key in symptom_questions:
            messagebox.showerror("Erreur", "Symptôme existant.")
            return
        # Mise à jour questions JSON
        symptom_questions[key] = q
        with open(file_questions, 'w', encoding='utf-8') as f:
            json.dump(symptom_questions, f, indent=2, ensure_ascii=False)
        # Ajouter dans rules par défaut no
        for d in disease_rules:
            disease_rules[d][key] = 'no'
        with open(file_rules, 'w', encoding='utf-8') as f:
            json.dump(disease_rules, f, indent=2, ensure_ascii=False)
        messagebox.showinfo("Succès", f"Symptôme '{key}' ajouté.")
        # Réinitialiser et rafraîchir
        self.entry_symp_key.delete(0, 'end')
        self.text_symp_q.delete('1.0', 'end')
        self.refresh_symptoms()

if __name__ == '__main__':
    app = ExpertApp()
    app.mainloop()
