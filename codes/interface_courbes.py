import sys
from PyQt5.QtWidgets import QLineEdit, QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QFileDialog, QLabel, QComboBox, QListWidget, QDialog, QGridLayout, QDesktopWidget
from PyQt5.QtCore import Qt
from functools import partial
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QDialog, QGridLayout, QMessageBox, QHBoxLayout, QDialogButtonBox, QTextEdit, QSlider
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QComboBox, QDialog, QVBoxLayout, QListWidget, QDialogButtonBox
from PyQt5.QtGui import QFont, QPixmap
import os
import random
import re
import numpy as np

def charger_donnees(nom_fichier, selected_file): # importer la fonction charger_donnees  

    altitudes, t1, t2, t3, d1, d2 = [], [], [], [], [], []
    with open(nom_fichier, 'r') as fichier:
        lignes = fichier.readlines()
        for ligne in lignes:
            valeurs = ligne.strip().split('\t')
            altitudes.append(float(valeurs[0]))
            t1.append(float(valeurs[1]))
            t2.append(float(valeurs[2]))
            t3.append(float(valeurs[3]))
            d1.append(float(valeurs[4]))
            d2.append(float(valeurs[5]))

    return {"altitudes" : altitudes, "t1"+selected_file : t1, "t2"+selected_file : t2, "t3"+selected_file : t3, "d1"+selected_file : d1, "d2"+selected_file : d2}

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Chargement de données et tracé de courbes")
        self.setGeometry(100, 100, 600, 400)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        layout = QVBoxLayout()

        self.label = QLabel("Aucun fichier sélectionné")
        layout.addWidget(self.label)

        self.selected_files_text = QTextEdit()
        self.selected_files_text.setReadOnly(True)
        self.selected_files_text.setStyleSheet("background-color: #f0f0f0;")
        layout.addWidget(self.selected_files_text)

        self.button_select_file = QPushButton("Sélectionner un ou des fichiers")
        self.button_select_file.setMaximumWidth(300)  
        self.button_select_file.clicked.connect(self.open_file_dialog)
        layout.addWidget(self.button_select_file)

        self.plot_button = QPushButton("Visualiser les options d'affichage")
        self.plot_button.setMaximumWidth(300)  
        self.plot_button.clicked.connect(self.show_graph_window)
        self.plot_button.hide()  
        layout.addWidget(self.plot_button)

        self.central_widget.setLayout(layout)
        self.files = {}
        self.add_images()

    def add_images(self):
        hbox_layout = QHBoxLayout()  
        hbox_layout.setAlignment(Qt.AlignRight | Qt.AlignBottom)  

        
        pixmap1 = QPixmap("photo1.png").scaled(70, 70, Qt.KeepAspectRatio)
        label1 = QLabel()
        label1.setPixmap(pixmap1)
        hbox_layout.addWidget(label1)

        pixmap2 = QPixmap("photo2.png").scaled(70, 70, Qt.KeepAspectRatio)
        label2 = QLabel()
        label2.setPixmap(pixmap2)
        hbox_layout.addWidget(label2)

        
        self.central_widget.layout().addLayout(hbox_layout)

    def open_file_dialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_names, _ = QFileDialog.getOpenFileNames(self, "Sélectionner un ou plusieurs fichiers", "", "Fichiers texte (*.txt)", options=options)
        if file_names:
            self.label.setText("Fichiers sélectionnés")
            for file_name in file_names:
                file_base_name = os.path.splitext(os.path.basename(file_name))[0]  # nom de fichier sans l'extension
                self.files[file_base_name] = file_name

            selected_files_text = "\n".join(self.files.keys())
            self.selected_files_text.setPlainText(selected_files_text)

            self.plot_button.show()

    def show_graph_window(self):
        selected_files = list(self.files.keys())
        if selected_files:
            graph_window = GraphWindow(selected_files, self.files)
            graph_window.exec_()
        else:
            # aucun fichier n'a été sélectionné
            pass
   
class GraphWindow(QDialog):
    def __init__(self, selected_files, files_dict):
        super().__init__()

        self.setWindowTitle("Affichage des courbes")
        desktop = QDesktopWidget().screenGeometry()
        width, height = desktop.width(), desktop.height()
        self.setGeometry(50,50, int(width*0.9), int(height*0.9))

        self.main_layout = QHBoxLayout()
        self.column_layouts = []

        # 3 colonnes layouts verticaux
        for _ in range(3):
            column_layout = QVBoxLayout()
            self.column_layouts.append(column_layout)
            self.main_layout.addLayout(column_layout)

        # Définir les proportions de redimensionnement des colonnes
        self.main_layout.setStretch(0, 1)  # colonne 1
        self.main_layout.setStretch(1, 2)  # colonne 2
        self.main_layout.setStretch(2, 1)  # colonne 3


        self.setLayout(self.main_layout)

        self.selected_files = selected_files
        self.files_dict = files_dict

        label = QLabel("Sélectionner un fichier")
        self.column_layouts[0].addWidget(label)
        self.file_list = QListWidget()
        self.file_list.addItems(selected_files)
        self.file_list.itemClicked.connect(self.show_variable_selection)
        self.column_layouts[0].addWidget(self.file_list)

        self.x_combo = QComboBox()

        label = QLabel("Liste des paramètres")
        self.column_layouts[0].addWidget(label)
        self.y_list = QListWidget()
        self.y_list.setSelectionMode(QListWidget.MultiSelection)
        self.column_layouts[0].addWidget(self.y_list)

        self.fig = Figure()
        self.canvas = FigureCanvas(self.fig)
        self.column_layouts[1].addWidget(self.canvas)

        self.equation_label = QLabel("Entrez l'équation de la combinaison linéaire:")
        self.equation_input = QLineEdit()
        self.calculate_button = QPushButton("Calculer")
        self.result_label = QLabel()

        self.column_layouts[0].addWidget(self.equation_label)
        self.column_layouts[0].addWidget(self.equation_input)
        self.column_layouts[0].addWidget(self.calculate_button)
        self.column_layouts[0].addWidget(self.result_label)

        self.equation_label.hide()  # masquer le bouton initialement
        self.equation_input.hide()  # masquer le bouton initialement
        self.calculate_button.hide()  # masquer le bouton initialement


        self.calculate_button.clicked.connect(self.calculate_linear_combination)

        self.plot_button = QPushButton("Tracer les courbes")
        self.plot_button.clicked.connect(lambda i : self.plot_curves([], ""))
        self.column_layouts[0].addWidget(self.plot_button)

        self.add_delete_button = QPushButton("Effacer la figure")
        self.add_delete_button.clicked.connect(self.delete_fig)
        #self.add_subplot_button.hide()  # masquer le bouton initialement 

        self.column_layouts[0].addWidget(self.add_delete_button)
       

        self.add_subplot_button = QPushButton("Sauvegarder la figure")
        self.add_subplot_button.clicked.connect(self.add_subplot)
        self.add_subplot_button.hide()  # masquer le bouton initialement

        self.column_layouts[0].addWidget(self.add_subplot_button)

        self.create_subplot_button = QPushButton("Créer un subplot")
        self.create_subplot_button.clicked.connect(self.create_subplot_window)
        self.column_layouts[0].addWidget(self.create_subplot_button)


        label = QLabel("Figures sauvegardées")
        self.column_layouts[2].addWidget(label)

        self.graphs = []
        self.graphs_data = []
        self.new_graph = 0

        self.compteur = 0
        self.ax_current = None
        self.axes = [self.ax_current]
        self.lines = None
        self.graphs_names = []
        self.first = True
        self.all_graphs = {}
        self.all_figures_names = []  
        self.var_equation = []
        self.var_histo = []
        self.leg = []
        self.colors = ['b','g','r','m','c','y', 'w', 'black' ]

    def delete_fig(self):
        while self.column_layouts[1].count():
            item = self.column_layouts[1].takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.first = False
        self.new_graph = 0
        self.fig = Figure()
        self.canvas = FigureCanvas(self.fig)
        self.column_layouts[1].addWidget(self.canvas)
        self.var_histo = []

    def calculate_linear_combination(self):
        equation = self.equation_input.text()
        self.plot_curves(self.get_variables_from_equation(equation),equation)
        # try:
        #     result = eval(equation, self.graphs_data[-1][0])
        #     print("Résultat: " + str(result))
        # except Exception as e:
        #     print("Erreur de calcul: " + str(e))


    def create_subplot_window(self):

        if not self.graphs:
            return

        dialog = SubplotSelectionDialog(self.graphs_names)
        if dialog.exec_():
            selected_figures = dialog.get_selected_figures()
            if selected_figures:
                subplot_window = SubplotWindow(selected_figures, self.all_graphs)
                subplot_window.exec_()

    def get_variables_from_equation(self,equation):
        # expression régulière pour les noms de variables
        pattern = r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'
        variables = re.findall(pattern, equation)
        # supprimer doublons
        return list(set(variables))
    
    def add_subplot(self):
        self.first = False
        self.new_graph = 0
        self.leg.append(True)
        if len(self.graphs) < 10:
            fig, ax = plt.subplots()
            self.graphs.append((fig, ax))
            self.axes.append(ax)
            self.update_graphs()


    def update_graphs(self):
        self.ax_current.clear()
        self.ax_current.axis('off')
        #self.ax_current.grid(True)
        for i in reversed(range(self.column_layouts[2].count())):
            widget = self.column_layouts[2].itemAt(i).widget()
            if isinstance(widget, QPushButton):
                widget.deleteLater()
        for ax in self.axes[1:]:
            self.column_layouts[1].removeWidget(ax.figure.canvas)
            ax.figure.canvas.setParent(None)

        dialog = GraphNameDialog()
        dialog.exec_()
        graph_name = dialog.get_graph_name()
        self.graphs_names.append(graph_name)

        for i, (fig, ax) in enumerate(self.graphs):
            ax.grid(True)
            ax.set_xlabel("Altitude - km")
            ax.set_ylabel("Température")
            data = self.graphs_data[i]
            for j, y_data_name in enumerate(data[2]):
                y_data = data[0][str(y_data_name)]
                ax.plot(data[0]['altitudes'], y_data, label=y_data_name, color = self.colors[j])
                if self.leg[i] :
                    ax.legend()

            self.leg[i] = False
            self.column_layouts[2].addWidget(ax.figure.canvas)

            ax.set_title(f"{self.graphs_names[i]}")
            self.all_graphs.setdefault(self.graphs_names[i], ax)

            button = QPushButton("Récupérer la figure")
            button.clicked.connect(partial(self.retrieve_figure, i))
            self.column_layouts[2].addWidget(button)
        self.add_subplot_button.hide()
        self.var_histo = []
        self.canvas.draw()

    def retrieve_figure(self, index):
        fig, ax = self.graphs[index]
        self.ax_current.clear()
        self.ax_current.axis('off')

        # recherche de l'axe spécifique dans les layouts et suppression
        for i, (fig, ax_) in enumerate(self.graphs):
            if i == index:
                # retirer l'axe de la colonne
                self.column_layouts[1].removeWidget(ax_.figure.canvas)
                ax_.figure.canvas.setParent(None)

                # supprimer le bouton de la colonne
                button = self.sender()  # récup le bouton qui a déclenché l'événement
                self.column_layouts[2].removeWidget(button)
                button.deleteLater()  # supprimer le bouton de la mémoire

        # ajouter l'axe récup à la colonne centrale
        self.column_layouts[1].removeWidget(self.ax_current.figure.canvas)        
        self.column_layouts[1].addWidget(ax.figure.canvas)

        #self.update_graphs()
        self.canvas.draw()


    def show_variable_selection(self, item):
        file_name = self.files_dict[item.text()]
        file_base_name = os.path.basename(file_name)
        file_name_without_extension = os.path.splitext(file_base_name)[0]
        data = charger_donnees(file_name, file_name_without_extension)
        self.x_combo.clear()
        self.y_list.clear()
        self.x_combo.addItems(data.keys())
        self.y_list.addItems(data.keys())
        self.equation_label.show()  
        self.equation_input.show()  
        self.calculate_button.show()

    def plot_curves(self, var_equation, equation):
        if self.new_graph ==0 :
            self.ax_current = self.fig.add_subplot(111)
        selected_file = self.file_list.currentItem().text()
        file_name = self.files_dict[selected_file]
        data = charger_donnees(file_name, selected_file)

        x_data_name = self.x_combo.currentText()
        
        selected_y_items = self.y_list.selectedItems()
        y_data_names = [item.text() for item in selected_y_items if item.text() not in self.var_histo]
        self.var_histo+=y_data_names

        if equation != "":
            try:
                result = eval(equation, {key: np.array(value) for key, value in data.copy().items()})
                data[equation] = result.tolist()
                y_data_names.append(str(equation))
            except Exception as e:
                print("Erreur de calcul: " + str(e))
        #print(y_data_names, data.keys(), data.values())
        for y_data_name in y_data_names:
            y_data = data[str(y_data_name)]
            self.ax_current.plot(data[x_data_name], y_data, label=y_data_name)
        self.ax_current.set_xlabel("Altitude - km")
        self.ax_current.set_ylabel("Température")
        self.ax_current.legend()
        self.lines = self.ax_current.get_lines()
        if self.new_graph ==0:
            self.graphs_data.append([data, data[x_data_name],y_data_names ])
            self.new_graph+=1
        else :
            self.graphs_data[-1][0].update({key: value for key, value in data.items() if key not in self.graphs_data[-1][0]})

            self.graphs_data[-1][2]+=y_data_names
        self.add_subplot_button.show()
        self.canvas.draw()


class GraphNameDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Nom du graphique")
        self.layout = QVBoxLayout()

        self.label = QLabel("Entrez le nom du graphique:")
        self.layout.addWidget(self.label)

        self.graph_name_input = QLineEdit()
        self.graph_name_input.setPlaceholderText("Nom du graphique")
        self.layout.addWidget(self.graph_name_input)

        self.button_valider = QPushButton("Valider")
        self.button_valider.clicked.connect(self.accept)
        self.layout.addWidget(self.button_valider)

        self.setLayout(self.layout)

    def get_graph_name(self):
        return self.graph_name_input.text()
    

class SubplotSelectionDialog(QDialog):
    def __init__(self, figures_names):
        super().__init__()

        self.setWindowTitle("Sélectionner les figures pour le subplot")

        layout = QVBoxLayout()

        self.figure_list = QListWidget()
        self.figure_list.addItems(figures_names)
        self.figure_list.setSelectionMode(QListWidget.MultiSelection)
        layout.addWidget(self.figure_list)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.setLayout(layout)

    def get_selected_figures(self):
        selected_items = self.figure_list.selectedItems()
        return [item.text() for item in selected_items]

    
class SubplotWindow(QDialog):
    def __init__(self, selected_figures, all_figures):
        super().__init__()

        # configuration de la fenêtre
        self.setWindowTitle("Subplot")

        # mise en place du layout
        layout = QGridLayout()
        self.setLayout(layout)

        # sélection des figures à afficher
        self.figures = {key: value for key, value in all_figures.items() if key in selected_figures}

        # ajout des figures dans la grille du layout
        for i, (figure_name, ax) in enumerate(self.figures.items()):
            layout.addWidget(ax.figure.canvas, i // 3, i % 3)

        # bouton enregistrer l'image
        save_button = QPushButton("Enregistrer l'image")
        save_button.clicked.connect(self.save_subplot)
        layout.addWidget(save_button, len(self.figures) // 3 + 1, 0, 1, 3)

        # slider taille des sous-graphiques
        resize_slider = QSlider(Qt.Horizontal)
        resize_slider.setMinimum(1)
        resize_slider.setMaximum(10)
        resize_slider.setValue(5)  
        resize_slider.setTickInterval(1)
        resize_slider.setTickPosition(QSlider.TicksBelow)
        resize_slider.valueChanged.connect(self.resize_subplot)
        layout.addWidget(resize_slider, len(self.figures) // 3 + 2, 0, 1, 3)

        # ajustement de la taille de la fenêtre selon le contenu
        self.adjustSize()

    # enregistrer l'image du subplot
    def save_subplot(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Enregistrer le subplot", "", "Images (*.png)", options=options)
        if file_name:
            # nouvelle figure pour enregistrer le subplot avec les modifications
            self.fig = plt.figure()
            for ax in self.figures.values():
                ax.set_xlabel("Altitude - km")
                ax.set_ylabel("Température")
                ax.legend()
                ax.figure.canvas.draw()
            # sauvegarde de la figure au format PNG
            self.fig.savefig(file_name, format='png')

    # ajuster la taille des sous-graphiques
    def resize_subplot(self, value):
        for ax in self.figures.values():
            ax.figure.set_size_inches(value, value)



if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(open("style.css").read())  
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())