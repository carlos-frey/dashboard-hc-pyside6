import sys
import os
import json
import csv
import random
import pandas as pd
from datetime import date, datetime, timedelta
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QLineEdit, QComboBox, QPushButton, QCheckBox, QFormLayout, 
    QGroupBox, QScrollArea, QFileDialog, QMessageBox, QDialog, QDateEdit, QSpinBox,
    QGraphicsLineItem, QTabWidget, QStackedWidget, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, QDateTime, QEvent, QDate
from PySide6.QtGui import QColor, QPainter, QFont, QPen
from PySide6.QtCharts import QChart, QChartView, QPieSeries, QLineSeries, QDateTimeAxis, QValueAxis, QScatterSeries, QBarSeries, QBarSet, QBarCategoryAxis, QHorizontalBarSeries

from etl.transformation.os_migration import (
    migrar_dados_servico,
    obter_total_os_emitidas,
    obter_total_gasto_os,
    extrair_historico_os
)
from etl.transformation.inventory import integrar_dados_dashboard

def generate_mock_os(count, start_date=date(2018, 1, 1)):
    os_list = []
    current_date = start_date
    for _ in range(count):
        interval = random.randint(15, 60)
        current_date += timedelta(days=interval)
        if current_date > date.today() + timedelta(days=30): break
        os_list.append({
            "data": current_date.strftime("%Y-%m-%d"),
            "custo": random.uniform(500, 15000),
            "desc": random.choice(["Troca de peças", "Calibração", "Preventiva", "Corretiva", "Limpeza"])
        })
    return sorted(os_list, key=lambda x: x["data"])

MOCK_EQUIPMENT = [
    {"modelo": "MRI Signa HDx", "setor": "Radiologia", "criticidade": 3, "data_aquisicao": "2010-05-15", "status": "Inoperante", "valor": 1200000, "score": 95, "identificador": "HCPE-0001", "os": generate_mock_os(15)},
    {"modelo": "Ventilador PB 840", "setor": "UTI Adulto", "criticidade": 3, "data_aquisicao": "2012-03-10", "status": "Em uso", "valor": 45000, "score": 88, "identificador": "HCPE-0002", "os": generate_mock_os(12)},
    {"modelo": "Raio-X Digital", "setor": "Emergência", "criticidade": 2, "data_aquisicao": "2011-08-20", "status": "Inoperante", "valor": 250000, "score": 82, "identificador": "HCPE-0003", "os": generate_mock_os(10)},
    {"modelo": "Bomba Alaris", "setor": "Enfermaria", "criticidade": 1, "data_aquisicao": "2015-11-05", "status": "Disponível", "valor": 8000, "score": 35, "identificador": "HCPE-0004", "os": generate_mock_os(5)},
    {"modelo": "Monitor V24", "setor": "UTI Cardio", "criticidade": 2, "data_aquisicao": "2018-02-28", "status": "Em uso", "valor": 15000, "score": 42, "identificador": "HCPE-0005", "os": generate_mock_os(8)},
    {"modelo": "Lifepak 15", "setor": "Emergência", "criticidade": 3, "data_aquisicao": "2013-06-15", "status": "Disponível", "valor": 35000, "score": 75, "identificador": "HCPE-0006", "os": generate_mock_os(10)},
    {"modelo": "Tomógrafo CT660", "setor": "Radiologia", "criticidade": 3, "data_aquisicao": "2009-12-01", "status": "Em uso", "valor": 1800000, "score": 78, "identificador": "HCPE-0007", "os": generate_mock_os(20)},
    {"modelo": "Ultrassom Voluson", "setor": "Obstetrícia", "criticidade": 2, "data_aquisicao": "2020-04-10", "status": "Em uso", "valor": 400000, "score": 25, "identificador": "HCPE-0008", "os": generate_mock_os(6)},
    {"modelo": "Autoclave Sterivap", "setor": "CME", "criticidade": 2, "data_aquisicao": "2014-09-22", "status": "Disponível", "valor": 120000, "score": 55, "identificador": "HCPE-0009", "os": generate_mock_os(9)},
    {"modelo": "Foco LED", "setor": "Bloco Cirúrgico", "criticidade": 2, "data_aquisicao": "2012-10-15", "status": "Em uso", "valor": 60000, "score": 62, "identificador": "HCPE-0010", "os": generate_mock_os(7)},
]

DARK_THEME_QSS = """
QMainWindow, QWidget { background-color: #0F172A; color: #F8FAFC; font-family: 'Inter', 'Segoe UI', Arial; }
QGroupBox { border: 1px solid #1E293B; border-radius: 6px; margin-top: 15px; font-weight: bold; padding-top: 25px; }
QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 5px; left: 10px; color: #94A3B8; }
QCheckBox { color: #F8FAFC; spacing: 5px; }
QCheckBox::indicator { width: 15px; height: 15px; }
QLineEdit, QComboBox, QDateEdit, QSpinBox { background-color: #1E293B; border: 1px solid #334155; border-radius: 4px; padding: 6px; color: #F8FAFC; }
QPushButton { background-color: #2563EB; color: white; border-radius: 4px; padding: 8px 16px; font-weight: 600; border: none; }
QPushButton:hover { background-color: #3B82F6; }
QPushButton#ExportBtn { background-color: #1E293B; color: #94A3B8; font-size: 10px; padding: 2px 8px; border: 1px solid #334155; }
QPushButton#ExportBtn:hover { background-color: #334155; color: white; }
QTableWidget { background-color: #1E293B; gridline-color: #334155; border: 1px solid #334155; border-radius: 4px; }
QHeaderView::section { background-color: #334155; color: #F8FAFC; padding: 6px; border: none; font-weight: bold; }
"""

class CrosshairChartView(QChartView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setMouseTracking(True)
        self._h_line = None
        self._v_line = None
        self._pinned = False

    def init_lines(self):
        if not self._h_line and self.scene():
            self._h_line = QGraphicsLineItem()
            self._v_line = QGraphicsLineItem()
            pen = QPen(QColor("#EF4444"))
            pen.setWidth(1)
            pen.setStyle(Qt.DashLine)
            self._h_line.setPen(pen)
            self._v_line.setPen(pen)
            self._h_line.setZValue(10)
            self._v_line.setZValue(10)
            self.scene().addItem(self._h_line)
            self.scene().addItem(self._v_line)
            self._h_line.hide()
            self._v_line.hide()

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            chart = self.chart()
            if chart and chart.plotArea().contains(event.position()):
                self._pinned = not self._pinned

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        if self._pinned:
            return
        self.init_lines()
        pos = event.position()
        chart = self.chart()
        if chart and self._h_line and chart.plotArea().contains(pos):
            rect = chart.plotArea()
            self._h_line.setLine(rect.left(), pos.y(), rect.right(), pos.y())
            self._v_line.setLine(pos.x(), rect.top(), pos.x(), rect.bottom())
            self._h_line.show()
            self._v_line.show()
        elif self._h_line:
            self._h_line.hide()
            self._v_line.hide()

    def leaveEvent(self, event):
        if self._h_line and not self._pinned:
            self._h_line.hide()
            self._v_line.hide()
        super().leaveEvent(event)

class DataPreviewDialog(QDialog):
    def __init__(self, df, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pré-visualização dos Dados")
        self.resize(1000, 600)
        self.setStyleSheet("QDialog { background-color: #0F172A; }")
        
        layout = QVBoxLayout(self)
        
        lbl = QLabel("Verifique se os dados abaixo estão corretos antes de acessar o dashboard:")
        lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #F8FAFC;")
        layout.addWidget(lbl)
        
        table = QTableWidget()
        table.setStyleSheet("QTableWidget { background-color: #1E293B; color: #F8FAFC; gridline-color: #334155; } QHeaderView::section { background-color: #334155; color: #F8FAFC; }")
        
        display_df = df.head(100) # Mostrar apenas as primeiras 100 linhas para não travar
        table.setRowCount(len(display_df))
        table.setColumnCount(len(df.columns))
        table.setHorizontalHeaderLabels([str(c) for c in df.columns])
        
        for i, row in display_df.reset_index(drop=True).iterrows():
            for j, col in enumerate(df.columns):
                val = row[col]
                item = QTableWidgetItem("" if pd.isna(val) else str(val))
                table.setItem(i, j, item)
                
        table.resizeColumnsToContents()
        layout.addWidget(table)
        
        btn_layout = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setStyleSheet("QPushButton { background-color: #EF4444; color: white; padding: 10px 20px; border-radius: 4px; font-weight: bold; } QPushButton:hover { background-color: #DC2626; }")
        btn_cancel.clicked.connect(self.reject)
        
        btn_confirm = QPushButton("Confirmar")
        btn_confirm.setStyleSheet("QPushButton { background-color: #10B981; color: white; padding: 10px 20px; border-radius: 4px; font-weight: bold; } QPushButton:hover { background-color: #059669; }")
        btn_confirm.clicked.connect(self.accept)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_confirm)
        layout.addLayout(btn_layout)

class HospitalDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Gestão de Equipamentos")
        self.resize(1400, 980)
        
        self.root_stack = QStackedWidget()
        self.setCentralWidget(self.root_stack)
        
        self.setup_import_page()
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        self.root_stack.addWidget(scroll)
        
        wrapper = QWidget()
        wrapper_layout = QHBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        
        container = QWidget()
        container.setMaximumWidth(1600)
        
        wrapper_layout.addStretch()
        wrapper_layout.addWidget(container, stretch=1)
        wrapper_layout.addStretch()
        
        self.main_layout = QVBoxLayout(container)
        self.main_layout.setContentsMargins(24, 24, 24, 24)
        self.main_layout.setSpacing(24)
        scroll.setWidget(wrapper)
        
        header_layout = QHBoxLayout()
        header = QLabel("Dashboard de Engenharia Clínica")
        header.setStyleSheet("font-size: 30px; font-weight: 700; color: #F8FAFC;")
        header_layout.addWidget(header)
        header_layout.addStretch()
        
        btn_back = QPushButton("Voltar para Importação")
        btn_back.setStyleSheet("QPushButton { background: #334155; color: #F8FAFC; padding: 10px 15px; border-radius: 6px; font-weight: bold; } QPushButton:hover { background: #475569; }")
        btn_back.clicked.connect(lambda: self.root_stack.setCurrentIndex(0))
        header_layout.addWidget(btn_back)
        
        self.main_layout.addLayout(header_layout)
        
        self.active_years = set(range(2018, 2026))
        if not hasattr(self, '_overlays'): self._overlays = []
        
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabBar::tab { padding: 10px 20px; background: #1E293B; color: #94A3B8; border-top-left-radius: 6px; border-top-right-radius: 6px; font-weight: bold; font-size: 14px; margin-right: 2px; }
            QTabBar::tab:selected { background: #38BDF8; color: #0F172A; }
            QTabWidget::pane { border: 1px solid #334155; border-radius: 6px; top: -1px; }
        """)
        self.main_layout.addWidget(self.tabs)
        
        self.analysis_tab = QWidget()
        self.analysis_layout = QVBoxLayout(self.analysis_tab)
        self.analysis_layout.setContentsMargins(10,10,10,10)
        self.analysis_layout.setSpacing(24)
        self.tabs.addTab(self.analysis_tab, "Análise")
        
        self.data_tab = QWidget()
        self.data_layout = QVBoxLayout(self.data_tab)
        self.data_layout.setContentsMargins(10,10,10,10)
        self.tabs.addTab(self.data_tab, "Dados")
        
        self.equipment_data = MOCK_EQUIPMENT
        self.df_os = pd.DataFrame()
        
        self.setup_kpi_row()
        self.setup_insights_row()
        self.setup_history_row()
        self.setup_cost_analysis_row()
        self.setup_data_tab()

    def setup_import_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        
        layout.addStretch()
        
        container = QFrame()
        container.setStyleSheet("QFrame { background-color: #1E293B; border-radius: 12px; border: 1px solid #334155; }")
        container.setFixedWidth(550)
        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(30, 30, 30, 30)
        c_layout.setSpacing(15)
        
        title = QLabel("Importação de Dados")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #F8FAFC; border: none;")
        title.setAlignment(Qt.AlignCenter)
        c_layout.addWidget(title)
        
        subtitle = QLabel("Selecione as planilhas para carregar o sistema.")
        subtitle.setStyleSheet("font-size: 14px; color: #94A3B8; border: none;")
        subtitle.setAlignment(Qt.AlignCenter)
        c_layout.addWidget(subtitle)
        
        # Equipamentos row
        equip_lay = QHBoxLayout()
        self.equip_path = QLineEdit()
        self.equip_path.setPlaceholderText("Planilha de Equipamentos...")
        self.equip_path.setReadOnly(True)
        self.equip_path.setStyleSheet("QLineEdit { background: #0F172A; border: 1px solid #334155; padding: 10px; border-radius: 6px; color: #E2E8F0; }")
        btn_equip = QPushButton("Procurar")
        btn_equip.setStyleSheet("QPushButton { background: #334155; color: #F8FAFC; padding: 10px 15px; border-radius: 6px; font-weight: bold; } QPushButton:hover { background: #475569; }")
        btn_equip.clicked.connect(lambda: self.equip_path.setText(QFileDialog.getOpenFileName(self, "Selecionar Planilha Equipamentos", "", "CSV Files (*.csv)")[0]))
        equip_lay.addWidget(self.equip_path)
        equip_lay.addWidget(btn_equip)
        c_layout.addLayout(equip_lay)
        
        # Criticidade row
        crit_lay = QHBoxLayout()
        self.crit_path = QLineEdit()
        self.crit_path.setPlaceholderText("Planilha de Criticidade (Opcional)...")
        self.crit_path.setReadOnly(True)
        self.crit_path.setStyleSheet("QLineEdit { background: #0F172A; border: 1px solid #334155; padding: 10px; border-radius: 6px; color: #E2E8F0; }")
        btn_crit = QPushButton("Procurar")
        btn_crit.setStyleSheet("QPushButton { background: #334155; color: #F8FAFC; padding: 10px 15px; border-radius: 6px; font-weight: bold; } QPushButton:hover { background: #475569; }")
        btn_crit.clicked.connect(lambda: self.crit_path.setText(QFileDialog.getOpenFileName(self, "Selecionar Planilha de Criticidade", "", "CSV Files (*.csv)")[0]))
        crit_lay.addWidget(self.crit_path)
        crit_lay.addWidget(btn_crit)
        c_layout.addLayout(crit_lay)
        
        # OS row (Antigo)
        os_antiga_lay = QHBoxLayout()
        self.os_antiga_path = QLineEdit()
        self.os_antiga_path.setPlaceholderText("Planilha de OS (Formato Antigo)...")
        self.os_antiga_path.setReadOnly(True)
        self.os_antiga_path.setStyleSheet("QLineEdit { background: #0F172A; border: 1px solid #334155; padding: 10px; border-radius: 6px; color: #E2E8F0; }")
        btn_os_antiga = QPushButton("Procurar")
        btn_os_antiga.setStyleSheet("QPushButton { background: #334155; color: #F8FAFC; padding: 10px 15px; border-radius: 6px; font-weight: bold; } QPushButton:hover { background: #475569; }")
        btn_os_antiga.clicked.connect(lambda: self.os_antiga_path.setText(QFileDialog.getOpenFileName(self, "Selecionar Planilha OS Antiga", "", "CSV Files (*.csv)")[0]))
        os_antiga_lay.addWidget(self.os_antiga_path)
        os_antiga_lay.addWidget(btn_os_antiga)
        c_layout.addLayout(os_antiga_lay)
        
        # OS row (Atual)
        os_atual_lay = QHBoxLayout()
        self.os_atual_path = QLineEdit()
        self.os_atual_path.setPlaceholderText("Planilha de OS (Formato Atual)...")
        self.os_atual_path.setReadOnly(True)
        self.os_atual_path.setStyleSheet("QLineEdit { background: #0F172A; border: 1px solid #334155; padding: 10px; border-radius: 6px; color: #E2E8F0; }")
        btn_os_atual = QPushButton("Procurar")
        btn_os_atual.setStyleSheet("QPushButton { background: #334155; color: #F8FAFC; padding: 10px 15px; border-radius: 6px; font-weight: bold; } QPushButton:hover { background: #475569; }")
        btn_os_atual.clicked.connect(lambda: self.os_atual_path.setText(QFileDialog.getOpenFileName(self, "Selecionar Planilha OS Atual", "", "CSV Files (*.csv)")[0]))
        os_atual_lay.addWidget(self.os_atual_path)
        os_atual_lay.addWidget(btn_os_atual)
        c_layout.addLayout(os_atual_lay)
        
        # Run button
        btn_run = QPushButton("Carregar Dados e Acessar Dashboard")
        btn_run.setStyleSheet("QPushButton { background: #0284C7; color: white; padding: 15px; border-radius: 6px; font-size: 16px; font-weight: bold; } QPushButton:hover { background: #0369A1; }")
        btn_run.clicked.connect(self.load_data)
        c_layout.addWidget(btn_run)
        
        # Export button
        btn_export = QPushButton("Exportar Dados Consolidados (CSV)")
        btn_export.setStyleSheet("QPushButton { background: #10B981; color: white; padding: 15px; border-radius: 6px; font-size: 16px; font-weight: bold; } QPushButton:hover { background: #059669; }")
        btn_export.clicked.connect(self.export_data)
        c_layout.addWidget(btn_export)
        
        # Histórico
        self.history_path_file = os.path.join(os.path.dirname(__file__), 'data', 'history.json')
        history_title = QLabel("Histórico de Importações Recentes:")
        history_title.setStyleSheet("color: #94A3B8; font-weight: bold; margin-top: 20px;")
        c_layout.addWidget(history_title)
        
        self.history_list = QListWidget()
        self.history_list.setStyleSheet(
            "QListWidget { background: #0F172A; border: 1px solid #334155; border-radius: 6px; color: #E2E8F0; padding: 5px; }"
            "QListWidget::item:selected { background: #38BDF8; color: #0F172A; }"
        )
        self.history_list.setFixedHeight(120)
        self.history_list.itemClicked.connect(self.load_history_item)
        c_layout.addWidget(self.history_list)
        
        self.populate_history()
        
        layout.addWidget(container, alignment=Qt.AlignHCenter)
        layout.addStretch()
        self.root_stack.addWidget(page)
        
    def populate_history(self):
        self.history_list.clear()
        if os.path.exists(self.history_path_file):
            try:
                with open(self.history_path_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                    for item in reversed(history):  # Mostrar mais recentes primeiro
                        equip = item.get('equip', '')
                        os_antiga = item.get('os_antiga', '')
                        os_atual = item.get('os_atual', '')
                        d = item.get('date', '')
                        
                        nomes = []
                        if os_atual: nomes.append(os.path.basename(os_atual))
                        if os_antiga: nomes.append(os.path.basename(os_antiga))
                        if equip and equip != 'N/A': nomes.append(os.path.basename(equip))
                        
                        nome_display = " + ".join(nomes) if nomes else "Arquivos não especificados"
                        display_text = f"[{d}] {nome_display}"
                        
                        list_item = QListWidgetItem(display_text)
                        list_item.setData(Qt.UserRole, item)
                        self.history_list.addItem(list_item)
            except Exception as e:
                print(f"Erro ao ler histórico: {e}")

    def load_history_item(self, item):
        data = item.data(Qt.UserRole)
        self.equip_path.setText(data.get('equip', ''))
        self.crit_path.setText(data.get('crit', ''))
        self.os_antiga_path.setText(data.get('os_antiga', ''))
        self.os_atual_path.setText(data.get('os_atual', ''))

    def save_history(self):
        equip = self.equip_path.text()
        crit = self.crit_path.text()
        os_antiga = self.os_antiga_path.text()
        os_atual = self.os_atual_path.text()
        if not equip and not os_antiga and not os_atual and not crit:
            return
            
        history = []
        if os.path.exists(self.history_path_file):
            try:
                with open(self.history_path_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except:
                pass
                
        new_entry = {
            'equip': equip,
            'crit': crit,
            'os_antiga': os_antiga,
            'os_atual': os_atual,
            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Evitar duplicata consecutiva exata
        if not history or history[-1].get('os_atual') != os_atual or history[-1].get('os_antiga') != os_antiga or history[-1].get('equip') != equip or history[-1].get('crit') != crit:
            history.append(new_entry)
            # Manter apenas as últimas 10
            history = history[-10:]
            
            with open(self.history_path_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=4, ensure_ascii=False)
            self.populate_history()

    def export_data(self):
        try:
            df_os = migrar_dados_servico(
                caminho_os_antiga=self.os_antiga_path.text() or None,
                caminho_os_atual=self.os_atual_path.text() or None
            )
            if df_os.empty:
                QMessageBox.warning(self, "Aviso", "Nenhum dado retornado para exportação.")
                return
                
            save_path, _ = QFileDialog.getSaveFileName(self, "Salvar Dados Consolidados", "dados_consolidados.csv", "CSV Files (*.csv)")
            if save_path:
                df_os.to_csv(save_path, index=False, sep=';', encoding='utf-8')
                QMessageBox.information(self, "Sucesso", f"Dados exportados com sucesso para:\n{save_path}")
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Ocorreu um erro ao exportar: {e}")

    def load_data(self):
        try:
            self.df_os = migrar_dados_servico(
                caminho_os_antiga=self.os_antiga_path.text() or None,
                caminho_os_atual=self.os_atual_path.text() or None
            )
            print(f"DEBUG: df_os size after migration: {len(self.df_os)}")
            self.save_history()

            valid_equipment = False
            if self.equip_path.text():
                try:
                    df_eq = integrar_dados_dashboard(self.equip_path.text(), self.df_os, self.crit_path.text() or None)
                    if df_eq is not None and len(df_eq) > 0:
                        self.equipment_data = df_eq
                        valid_equipment = True
                except Exception as e:
                    print(f"Erro processando equipamentos: {e}")
            
            if not valid_equipment:
                self.equipment_data = MOCK_EQUIPMENT

            if not self.df_os.empty:
                dialog = DataPreviewDialog(self.df_os, self)
                if dialog.exec() != QDialog.Accepted:
                    return

        except Exception as e:
            QMessageBox.warning(self, "Aviso", f"Não foi possível carregar os dados OS.\nUsando dados MOCK.\n\nDetalhe: {e}")
            self.df_os = pd.DataFrame()
            self.equipment_data = MOCK_EQUIPMENT
            
        self.root_stack.setCurrentIndex(1)
        self.update_dashboard_data()

    def update_dashboard_data(self):
        self.setup_kpi_row()
        self.update_global_chart()
        self.update_cost_analysis_charts()
        
        self.f_setor.blockSignals(True)
        self.f_setor.clear()
        data_source = getattr(self, 'equipment_data', MOCK_EQUIPMENT)
        self.f_setor.addItems(["Todos Setores"] + sorted(list(set(i.get("setor", "Desconhecido") for i in data_source))))
        self.f_setor.blockSignals(False)
        
        self.update_age_donut() # includes populate_top5 and recalculating scores dynamically
        self.apply_filters()

    def switch_tab(self, index):
        self.tabs.setCurrentIndex(index)

    def setup_kpi_row(self):
        # Limpar layout anterior se existir
        if hasattr(self, 'kpi_layout_widget'):
            self.kpi_layout_widget.deleteLater()
            
        self.kpi_layout_widget = QWidget()
        kpi_layout = QHBoxLayout(self.kpi_layout_widget)
        kpi_layout.setContentsMargins(0,0,0,0)
        kpi_layout.setSpacing(24)
        
        total_equip = len(self.equipment_data)
        
        if hasattr(self, 'df_os') and not self.df_os.empty:
            total_os = obter_total_os_emitidas(self.df_os)
            total_cost = obter_total_gasto_os(self.df_os)
            os_title = "Total de OS Emitidas"
            cost_title = "Total Gasto em OS"
        else:
            total_os = sum(len(equip.get("os", [])) for equip in self.equipment_data)
            total_cost = sum(os_data.get("custo", 0) for equip in self.equipment_data for os_data in equip.get("os", []))
            os_title = "Total de OS Emitidas (Mockado)"
            cost_title = "Total Gasto em OS (Mockado)"
            
        total_cost_str = f"R$ {total_cost:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        def create_kpi_card(title, value):
            card = QFrame()
            card.setStyleSheet("QFrame { background-color: #1E293B; border-radius: 12px; border: 1px solid #334155; }")
            layout = QVBoxLayout(card)
            layout.setContentsMargins(24, 24, 24, 24)
            lbl_title = QLabel(title)
            lbl_title.setStyleSheet("color: #94A3B8; font-size: 14px; font-weight: bold; border: none;")
            lbl_title.setAlignment(Qt.AlignCenter)
            lbl_val = QLabel(str(value))
            lbl_val.setStyleSheet("color: #38BDF8; font-size: 36px; font-weight: bold; border: none;")
            lbl_val.setAlignment(Qt.AlignCenter)
            layout.addWidget(lbl_title)
            layout.addWidget(lbl_val)
            return card

        kpi_layout.addWidget(create_kpi_card("Total de Equipamentos", total_equip), 1)
        kpi_layout.addWidget(create_kpi_card(os_title, total_os), 1)
        kpi_layout.addWidget(create_kpi_card(cost_title, total_cost_str), 1)
        
        self.analysis_layout.insertWidget(0, self.kpi_layout_widget)

    def setup_insights_row(self):
        layout = QHBoxLayout()
        layout.setSpacing(24)
        
        # Age Distribution
        age_group = QGroupBox("Distribuição por Idade")
        age_group.setStyleSheet("QGroupBox { border: 1px solid #334155; border-radius: 12px; padding-top: 24px; font-weight: bold; }")
        age_vbox = QVBoxLayout(age_group)
        age_vbox.setContentsMargins(24, 24, 24, 24)
        
        self.age_donut_view = QChartView()
        self.age_donut_view.setRenderHint(QPainter.Antialiasing)
        self.age_donut_view.setStyleSheet("background: transparent;")
        self.age_donut_view.setFixedHeight(280)
        age_vbox.addWidget(self.age_donut_view)
        
        age_overlay = QWidget(age_group)
        age_overlay_lay = QHBoxLayout(age_overlay)
        age_overlay_lay.setContentsMargins(5, 0, 5, 0)
        age_overlay_lay.setSpacing(5)
        
        lbl_age = QLabel("Corte (Anos):")
        lbl_age.setStyleSheet("font-size: 10px; color: #94A3B8; font-weight: bold;")
        self.age_threshold = QSpinBox()
        self.age_threshold.setRange(1, 30); self.age_threshold.setValue(10)
        self.age_threshold.setFixedWidth(50)
        self.age_threshold.setStyleSheet("font-size: 10px; padding: 2px;")
        self.age_threshold.valueChanged.connect(self.update_age_donut)
        age_overlay_lay.addWidget(lbl_age); age_overlay_lay.addWidget(self.age_threshold)
        age_overlay.setFixedWidth(120)
        
        self._overlays.append((age_group, age_overlay))
        age_group.installEventFilter(self)

        # Risk / Priorities Row (2/3 width)
        self.top5_group = QGroupBox("Prioridades de Substituição")
        self.top5_group.setStyleSheet("QGroupBox { border: 1px solid #334155; border-radius: 12px; padding-top: 24px; font-weight: bold; }")
        top5_layout = QVBoxLayout(self.top5_group)
        top5_layout.setContentsMargins(24, 24, 24, 24)
        top5_layout.setSpacing(12)
        
        # Header for toggle
        top5_header = QHBoxLayout()
        top5_header.addStretch()
        self.btn_show_chart = QPushButton("Gráfico")
        self.btn_show_chart.setCheckable(True)
        self.btn_show_chart.setChecked(True)
        self.btn_show_table = QPushButton("Tabela")
        self.btn_show_table.setCheckable(True)
        
        top5_header.addWidget(self.btn_show_chart)
        top5_header.addWidget(self.btn_show_table)
        top5_layout.addLayout(top5_header)
        
        self.top5_stack = QStackedWidget()
        
        self.top5_chart_view = QChartView()
        self.top5_chart_view.setRenderHint(QPainter.Antialiasing)
        self.top5_chart_view.setStyleSheet("background: transparent;")
        self.top5_chart_view.setFixedHeight(280)
        
        self.top5_table_view = QTableWidget()
        self.top5_table_view.setColumnCount(3)
        self.top5_table_view.setHorizontalHeaderLabels(["Modelo", "Score", "Identificador"])
        self.top5_table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.top5_table_view.setStyleSheet("QTableWidget { background-color: #1E293B; color: #F8FAFC; gridline-color: #334155; } QHeaderView::section { background-color: #334155; color: #F8FAFC; }")
        
        self.top5_stack.addWidget(self.top5_chart_view)
        self.top5_stack.addWidget(self.top5_table_view)
        top5_layout.addWidget(self.top5_stack)
        
        self.btn_show_chart.clicked.connect(lambda: self.set_top5_view(0))
        self.btn_show_table.clicked.connect(lambda: self.set_top5_view(1))
        
        self.update_age_donut()
        
        layout.addWidget(age_group, 1)
        layout.addWidget(self.top5_group, 2)
        
        self.analysis_layout.addLayout(layout)

    def set_top5_view(self, index):
        self.top5_stack.setCurrentIndex(index)
        self.btn_show_chart.setChecked(index == 0)
        self.btn_show_table.setChecked(index == 1)

    def setup_history_row(self):
        # OS History (100% width)
        self.history_group = QGroupBox("Histórico de Emissão de OS")
        self.history_group.setStyleSheet("QGroupBox { border: 1px solid #334155; border-radius: 12px; padding-top: 24px; font-weight: bold; }")
        chart_vbox = QVBoxLayout(self.history_group)
        chart_vbox.setContentsMargins(24, 24, 24, 24)
        
        # Filtro de Custo
        filter_layout = QHBoxLayout()
        self.cb_excluir_custo_zero = QCheckBox("Excluir OS com Custo = 0")
        self.cb_excluir_custo_zero.setStyleSheet("color: #94A3B8; font-weight: normal;")
        self.cb_excluir_custo_zero.stateChanged.connect(self.update_global_chart)
        filter_layout.addStretch()
        filter_layout.addWidget(self.cb_excluir_custo_zero)
        chart_vbox.addLayout(filter_layout)
        
        self.global_chart_view = CrosshairChartView()
        self.global_chart_view.setRenderHint(QPainter.Antialiasing)
        self.global_chart_view.setStyleSheet("background: transparent;")
        self.global_chart_view.setFixedHeight(300)
        chart_vbox.addWidget(self.global_chart_view)

        # Table for the time-series data
        self.history_table = QTableWidget()
        self.history_table.setStyleSheet("QTableWidget { background-color: #1E293B; gridline-color: #334155; border: 1px solid #334155; border-radius: 4px; color: #F8FAFC; } QHeaderView::section { background-color: #334155; color: #F8FAFC; border: none; font-weight: bold; padding: 4px; }")
        self.history_table.setFixedHeight(200)
        chart_vbox.addWidget(self.history_table)
        
        self.update_global_chart()
        self.analysis_layout.addWidget(self.history_group)

    def setup_cost_analysis_row(self):
        layout = QHBoxLayout()
        layout.setSpacing(24)
        
        group_style = "QGroupBox { border: 1px solid #334155; border-radius: 12px; padding-top: 24px; font-weight: bold; }"

        evol_group = QGroupBox("Evolução do Custo Total por Ano")
        evol_group.setStyleSheet(group_style)
        evol_layout = QVBoxLayout(evol_group)
        evol_layout.setContentsMargins(24, 24, 24, 24)
        self.cost_evol_chart_view = QChartView()
        self.cost_evol_chart_view.setRenderHint(QPainter.Antialiasing)
        self.cost_evol_chart_view.setStyleSheet("background: transparent;")
        self.cost_evol_chart_view.setFixedHeight(250)
        evol_layout.addWidget(self.cost_evol_chart_view)
        layout.addWidget(evol_group, 1)

        top10_group = QGroupBox("Top 10 Equipamentos Custo")
        top10_group.setStyleSheet(group_style)
        top10_layout = QVBoxLayout(top10_group)
        top10_layout.setContentsMargins(24, 24, 24, 24)
        self.top10_chart_view = QChartView()
        self.top10_chart_view.setRenderHint(QPainter.Antialiasing)
        self.top10_chart_view.setStyleSheet("background: transparent;")
        self.top10_chart_view.setFixedHeight(250)
        top10_layout.addWidget(self.top10_chart_view)
        layout.addWidget(top10_group, 1)

        sector_group = QGroupBox("Custos por Setor (Top 10)")
        sector_group.setStyleSheet(group_style)
        sector_layout = QVBoxLayout(sector_group)
        sector_layout.setContentsMargins(24, 24, 24, 24)
        self.sector_chart_view = QChartView()
        self.sector_chart_view.setRenderHint(QPainter.Antialiasing)
        self.sector_chart_view.setStyleSheet("background: transparent;")
        self.sector_chart_view.setFixedHeight(250)
        sector_layout.addWidget(self.sector_chart_view)
        layout.addWidget(sector_group, 1)

        self.analysis_layout.addLayout(layout)
        self.analysis_layout.addStretch()
        self.update_cost_analysis_charts()

    def update_cost_analysis_charts(self):
        cost_by_year = {}
        equip_cost = {}
        sector_cost = {}

        for equip in self.equipment_data:
            modelo = equip["modelo"]
            setor = equip["setor"]
            e_cost = 0
            for os in equip["os"]:
                year = datetime.strptime(os["data"], "%Y-%m-%d").year
                c = os["custo"]
                e_cost += c
                cost_by_year[year] = cost_by_year.get(year, 0) + c
            equip_cost[modelo] = equip_cost.get(modelo, 0) + e_cost
            sector_cost[setor] = sector_cost.get(setor, 0) + e_cost

        # 1. Evolution Chart
        chart_evol = QChart()
        chart_evol.setAnimationOptions(QChart.SeriesAnimations)
        chart_evol.setBackgroundBrush(QColor("#1E293B"))
        chart_evol.setTitleBrush(QColor("#F8FAFC"))
        series_evol = QLineSeries()
        series_evol.setColor(QColor("#F59E0B"))
        series_evol.setPointsVisible(True)
        
        years = sorted(cost_by_year.keys())
        axis_x_evol = QBarCategoryAxis()
        axis_x_evol.append([str(y) for y in years])
        axis_x_evol.setLabelsColor(QColor("#CBD5E1"))
        chart_evol.addAxis(axis_x_evol, Qt.AlignBottom)

        axis_y_evol = QValueAxis()
        axis_y_evol.setLabelsColor(QColor("#CBD5E1"))
        axis_y_evol.setLabelFormat("%.0f")
        max_cost_y = max(cost_by_year.values()) if cost_by_year else 1000
        axis_y_evol.setRange(0, max_cost_y * 1.1)
        chart_evol.addAxis(axis_y_evol, Qt.AlignLeft)

        for i, y in enumerate(years):
            series_evol.append(i, cost_by_year[y])

        chart_evol.addSeries(series_evol)
        series_evol.attachAxis(axis_x_evol)
        series_evol.attachAxis(axis_y_evol)
        chart_evol.legend().setVisible(False)
        self.cost_evol_chart_view.setChart(chart_evol)

        # 2. Top 10 Equip
        top10_equip = sorted(equip_cost.items(), key=lambda x: x[1], reverse=True)[:10]
        bar_set = QBarSet("Custo")
        bar_set.setBrush(QColor("#EF4444"))
        categories_top10 = []
        for mod, c in top10_equip:
            bar_set.append(c)
            categories_top10.append(mod.split(" ")[0])
        
        series_bar = QBarSeries()
        series_bar.append(bar_set)
        
        chart_top10 = QChart()
        chart_top10.setAnimationOptions(QChart.SeriesAnimations)
        chart_top10.setBackgroundBrush(QColor("#1E293B"))
        chart_top10.addSeries(series_bar)
        
        axis_x_bar = QBarCategoryAxis()
        axis_x_bar.append(categories_top10)
        axis_x_bar.setLabelsColor(QColor("#CBD5E1"))
        chart_top10.addAxis(axis_x_bar, Qt.AlignBottom)
        series_bar.attachAxis(axis_x_bar)
        
        axis_y_bar = QValueAxis()
        axis_y_bar.setLabelsColor(QColor("#CBD5E1"))
        axis_y_bar.setLabelFormat("%.0f")
        max_c = max([c for m, c in top10_equip]) if top10_equip else 1000
        axis_y_bar.setRange(0, max_c * 1.1)
        chart_top10.addAxis(axis_y_bar, Qt.AlignLeft)
        series_bar.attachAxis(axis_y_bar)
        chart_top10.legend().setVisible(False)
        self.top10_chart_view.setChart(chart_top10)

        # 3. Sector Cost
        top10_sectors = sorted(sector_cost.items(), key=lambda x: x[1], reverse=True)[:10]
        series_sec = QPieSeries()
        series_sec.setHoleSize(0.4)
        colors = ["#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6", "#EC4899", "#14B8A6", "#F97316", "#06B6D4", "#6366F1"]
        
        for i, (sec, c) in enumerate(top10_sectors):
            slice_ = series_sec.append(sec, c)
            slice_.setBrush(QColor(colors[i % len(colors)]))
            slice_.setLabelVisible(True)
            slice_.setLabelColor(QColor("#CBD5E1"))
            
        chart_sec = QChart()
        chart_sec.setAnimationOptions(QChart.SeriesAnimations)
        chart_sec.setBackgroundBrush(QColor("#1E293B"))
        chart_sec.addSeries(series_sec)
        chart_sec.legend().setAlignment(Qt.AlignBottom)
        chart_sec.legend().setLabelColor(QColor("#F8FAFC"))
        self.sector_chart_view.setChart(chart_sec)

    def update_age_donut(self):
        threshold = self.age_threshold.value()
        data_source = getattr(self, 'equipment_data', MOCK_EQUIPMENT)
        current_year = date.today().year
        
        over = 0
        for i in data_source:
            try:
                if (current_year - int(i["data_aquisicao"].split("-")[0])) >= threshold:
                    over += 1
            except:
                pass
                
        under = len(data_source) - over
        total = over + under
        pct_over = (over / total) * 100 if total else 0
        pct_under = (under / total) * 100 if total else 0
        series = QPieSeries(); series.setHoleSize(0.6)
        s1 = series.append(f"≥ {threshold} Anos ({over} - {pct_over:.1f}%)", over); s1.setBrush(QColor("#475569"))
        s2 = series.append(f"< {threshold} Anos ({under} - {pct_under:.1f}%)", under); s2.setBrush(QColor("#2563EB"))
        for slice in series.slices(): slice.setLabelVisible(True); slice.setLabelColor(QColor("#CBD5E1"))
        chart = QChart(); chart.setAnimationOptions(QChart.SeriesAnimations); chart.addSeries(series); chart.setTitle(f"Corte: {threshold} anos")
        chart.setBackgroundBrush(QColor("#1E293B")); chart.setTitleBrush(QColor("#F8FAFC"))
        chart.legend().setAlignment(Qt.AlignBottom); chart.legend().setLabelColor(QColor("#F8FAFC"))
        self.age_donut_view.setChart(chart)
        
        # Recalcula dinamicamente a priorização com o novo corte da UI e propaga para o gráfico Top 5
        max_custo = 0
        for eq in data_source:
            tot = sum(o.get('custo', 0) for o in eq.get('os', []))
            if tot > max_custo: max_custo = tot
            
        for eq in data_source:
            try:
                anos = current_year - int(eq["data_aquisicao"].split("-")[0])
            except:
                anos = 0
            idade_pts = 20 if anos >= threshold else 0
            crit_pts = (eq.get('criticidade', 1) / 3.0) * 50
            tot = sum(o.get('custo', 0) for o in eq.get('os', []))
            custo_pts = (tot / max_custo * 30) if max_custo > 0 else 0
            eq['score'] = idade_pts + crit_pts + custo_pts
            
        self.populate_top5()

    def handle_year_legend_click(self):
        marker = self.sender()
        if marker:
            try:
                year = int(marker.series().name())
                if year in self.active_years:
                    self.active_years.remove(year)
                else:
                    self.active_years.add(year)
                self.update_global_chart()
            except ValueError:
                pass

    def update_global_chart(self):
        chart = QChart(); chart.setAnimationOptions(QChart.SeriesAnimations); chart.setBackgroundBrush(QColor("#1E293B")); chart.setTitleBrush(QColor("#F8FAFC"))
        colors = ["#10B981", "#3B82F6", "#F59E0B", "#EF4444", "#8B5CF6", "#EC4899", "#14B8A6"]
        
        all_years = list(range(2018, 2026))
        
        usando_mock = True
        if hasattr(self, 'df_os') and not self.df_os.empty:
            excluir_zero = hasattr(self, 'cb_excluir_custo_zero') and self.cb_excluir_custo_zero.isChecked()
            dict_hist = extrair_historico_os(self.df_os, excluir_zero)
            if dict_hist:
                usando_mock = False
                all_years = sorted(dict_hist.keys())
                
                if not hasattr(self, '_current_data_years') or self._current_data_years != all_years:
                    self.active_years = set(all_years)
                    self._current_data_years = all_years
                    
                year_data = {y: {m: 0 for m in range(1, 13)} for y in all_years}
                for y, m_data in dict_hist.items():
                    for m, c in m_data.items():
                        year_data[y][m] = c
                        
        if usando_mock:
            all_years = list(range(2018, 2026))
            if not hasattr(self, '_current_data_years') or self._current_data_years != all_years:
                self.active_years = set(all_years)
                self._current_data_years = all_years
                
            year_data = {y: {m: 0 for m in range(1, 13)} for y in all_years}
            
            self.history_group.setTitle("Histórico de Emissão de OS (Mockado)")
            for equip in self.equipment_data:
                for os in equip["os"]:
                    dt = datetime.strptime(os["data"], "%Y-%m-%d").date()
                    if dt.year in all_years: year_data[dt.year][dt.month] += 1
        else:
            self.history_group.setTitle("Histórico de Emissão de OS")
        
        axis_x = QBarCategoryAxis()
        axis_x.append(["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"])
        axis_x.setLabelsColor(QColor("#CBD5E1"))
        axis_x.setGridLineVisible(True)
        axis_x.setGridLineColor(QColor("#334155"))
        chart.addAxis(axis_x, Qt.AlignBottom)
        
        axis_y = QValueAxis(); axis_y.setLabelsColor(QColor("#CBD5E1")); axis_y.setLabelFormat("%d")
        axis_y.setGridLineVisible(True)
        axis_y.setGridLineColor(QColor("#334155"))
        max_val = 5
        
        averages = {m: 0 for m in range(1, 13)}
        
        for i, year in enumerate(all_years):
            series = QLineSeries(); series.setName(str(year))
            series.setColor(QColor(colors[i % len(colors)])); series.setPointsVisible(True)
            for month in range(1, 13):
                val = year_data[year][month]
                series.append(month - 1, val)
                if val > max_val: max_val = val
                if year in self.active_years:
                    averages[month] += val
            chart.addSeries(series); series.attachAxis(axis_x)
            if year not in self.active_years:
                series.setVisible(False)
        
        if self.active_years:
            avg_series = QLineSeries(); avg_series.setName("Média")
            avg_series.setColor(QColor("#F8FAFC")); avg_series.setPointsVisible(True)
            pen = avg_series.pen(); pen.setStyle(Qt.DashLine); pen.setWidth(2); avg_series.setPen(pen)
            for month in range(1, 13):
                avg_val = averages[month] / len(self.active_years)
                avg_series.append(month - 1, avg_val)
                if avg_val > max_val: max_val = avg_val
            chart.addSeries(avg_series); avg_series.attachAxis(axis_x)
        
        chart.addAxis(axis_y, Qt.AlignLeft)
        for series in chart.series():
            series.attachAxis(axis_y)
            
        teto_grafico = max(5, int(max_val * 1.15))
        axis_y.setRange(0, teto_grafico)
        
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)
        chart.legend().setLabelColor(QColor("#F8FAFC"))
        
        for marker in chart.legend().markers():
            if marker.series().name() == "Média":
                continue
            if not marker.series().isVisible():
                marker.setVisible(True)
                label_brush = marker.labelBrush()
                color = label_brush.color(); color.setAlpha(80)
                label_brush.setColor(color); marker.setLabelBrush(label_brush)
                
                brush = marker.brush()
                color = brush.color(); color.setAlpha(80)
                brush.setColor(color); marker.setBrush(brush)
                
                pen = marker.pen()
                color = pen.color(); color.setAlpha(80)
                pen.setColor(color); marker.setPen(pen)
            marker.clicked.connect(self.handle_year_legend_click)
        
        self.global_chart_view.setChart(chart)
        
        # Populate history table
        meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
        self.history_table.setColumnCount(len(meses) + 2) # Meses + Total + Média
        self.history_table.setHorizontalHeaderLabels(meses + ["Total", "Média"])
        self.history_table.setRowCount(len(all_years))
        self.history_table.setVerticalHeaderLabels([str(y) for y in all_years])
        
        for i, year in enumerate(all_years):
            total_ano = sum(year_data[year][m] for m in range(1, 13))
            media_ano = total_ano / 12
            for m in range(1, 13):
                item = QTableWidgetItem(str(year_data[year][m]))
                item.setTextAlignment(Qt.AlignCenter)
                self.history_table.setItem(i, m - 1, item)
            
            # Total
            item_total = QTableWidgetItem(str(total_ano))
            item_total.setTextAlignment(Qt.AlignCenter)
            self.history_table.setItem(i, 12, item_total)
            
            # Media
            item_media = QTableWidgetItem(f"{media_ano:.1f}")
            item_media.setTextAlignment(Qt.AlignCenter)
            self.history_table.setItem(i, 13, item_media)

    def populate_top5(self):
        sorted_items = sorted(self.equipment_data, key=lambda x: x["score"], reverse=True)[:5]
        
        # Update Table
        self.top5_table_view.setRowCount(len(sorted_items))
        for r, item in enumerate(sorted_items):
            self.top5_table_view.setItem(r, 0, QTableWidgetItem(item["modelo"]))
            self.top5_table_view.setItem(r, 1, QTableWidgetItem(f"{item['score']:.1f}"))
            self.top5_table_view.setItem(r, 2, QTableWidgetItem(item.get("identificador", "N/A")))
            
        # Update Chart
        series = QHorizontalBarSeries()
        bar_set = QBarSet("Score")
        bar_set.setBrush(QColor("#CF6679"))
        
        categories = []
        for item in reversed(sorted_items):
            bar_set.append(item["score"])
            categories.append(item["modelo"])
            
        series.append(bar_set)
        
        chart = QChart()
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.setBackgroundBrush(QColor("#1E293B"))
        chart.addSeries(series)
        chart.legend().setVisible(False)
        
        axis_y = QBarCategoryAxis()
        axis_y.append(categories)
        axis_y.setLabelsColor(QColor("#CBD5E1"))
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)
        
        axis_x = QValueAxis()
        axis_x.setLabelsColor(QColor("#CBD5E1"))
        axis_x.setRange(0, 100)
        axis_x.setLabelFormat("%.0f")
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)
        
        def on_bar_clicked(index):
            item = list(reversed(sorted_items))[index]
            self.show_equipment_modal(item)
            
        bar_set.clicked.connect(on_bar_clicked)
        self.top5_chart_view.setChart(chart)

    def show_equipment_modal(self, item):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Equipamento: {item['modelo']}")
        dialog.setStyleSheet("QDialog { background-color: #0F172A; color: #F8FAFC; border: 1px solid #334155; } QLabel { color: #F8FAFC; }")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        
        lbl_style = "font-weight: bold; color: #38BDF8;"
        
        def add_row(label, value):
            l = QLabel(label); l.setStyleSheet(lbl_style)
            v = QLabel(str(value))
            form.addRow(l, v)
            
        add_row("Modelo:", item.get("modelo"))
        add_row("Setor:", item.get("setor"))
        add_row("Identificador:", item.get("identificador", "N/A"))
        add_row("Criticidade:", item.get("criticidade"))
        add_row("Data Aquisição:", item.get("data_aquisicao"))
        add_row("Status:", item.get("status"))
        add_row("Score de Substituição:", f"{item.get('score', 0):.2f}")
        
        layout.addLayout(form)
        
        if item.get("os"):
            os_title = QLabel(f"\nHistórico de OS ({len(item['os'])}):")
            os_title.setStyleSheet("font-weight: bold; color: #F59E0B;")
            layout.addWidget(os_title)
            
            os_table = QTableWidget()
            os_table.setColumnCount(3)
            os_table.setHorizontalHeaderLabels(["Data", "Custo", "Descrição"])
            os_table.setRowCount(len(item["os"]))
            os_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            os_table.setFixedHeight(150)
            os_table.verticalHeader().setVisible(False)
            os_table.setStyleSheet("QTableWidget { background: #1E293B; }")
            
            for i, os_item in enumerate(item["os"]):
                os_table.setItem(i, 0, QTableWidgetItem(os_item["data"]))
                os_table.setItem(i, 1, QTableWidgetItem(f"R$ {os_item['custo']:,.2f}"))
                os_table.setItem(i, 2, QTableWidgetItem(os_item["desc"]))
                
            layout.addWidget(os_table)
            
        btn_close = QPushButton("Fechar")
        btn_close.clicked.connect(dialog.accept)
        layout.addWidget(btn_close)
        
        dialog.exec()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Resize:
            if hasattr(self, '_overlays'):
                for gbox, widget in self._overlays:
                    if gbox == obj: widget.move(gbox.width() - widget.width() - 15, 0)
        return super().eventFilter(obj, event)

    def setup_data_tab(self):
        # Clear layout
        while self.data_layout.count():
            item = self.data_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        self.data_layout.setSpacing(20)
        
        # 1. Equipments Section
        equip_group = QGroupBox("Listagem de Equipamentos")
        equip_vbox = QVBoxLayout(equip_group)
        
        filters_eq = QHBoxLayout()
        self.f_modelo = QLineEdit(); self.f_modelo.setPlaceholderText("Filtrar modelo...")
        self.f_modelo.textChanged.connect(self.apply_filters)
        self.f_setor = QComboBox()
        self.f_setor.currentIndexChanged.connect(self.apply_filters)
        filters_eq.addWidget(self.f_modelo)
        filters_eq.addWidget(self.f_setor)
        equip_vbox.addLayout(filters_eq)
        
        self.equip_table = QTableWidget()
        self.equip_table.setColumnCount(6)
        self.equip_table.setHorizontalHeaderLabels(["Identificador", "Modelo", "Setor", "Crit.", "Aquisição", "Status"])
        self.equip_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.equip_table.setFixedHeight(300)
        equip_vbox.addWidget(self.equip_table)
        
        self.data_layout.addWidget(equip_group)
        
        # 2. OS Section
        os_group = QGroupBox("Listagem de Ordens de Serviço")
        os_vbox = QVBoxLayout(os_group)
        
        filters_os = QHBoxLayout()
        self.f_os_id = QLineEdit(); self.f_os_id.setPlaceholderText("Filtrar Identificador...")
        self.f_os_id.textChanged.connect(self.apply_filters)
        self.f_os_min_cost = QSpinBox(); self.f_os_min_cost.setRange(0, 1000000); self.f_os_min_cost.setPrefix("Custo Min: R$ ")
        self.f_os_min_cost.valueChanged.connect(self.apply_filters)
        
        filters_os.addWidget(self.f_os_id)
        filters_os.addWidget(self.f_os_min_cost)
        os_vbox.addLayout(filters_os)
        
        self.os_table = QTableWidget()
        self.os_table.setColumnCount(5)
        self.os_table.setHorizontalHeaderLabels(["ID Equip.", "Modelo", "Data", "Custo", "Descrição"])
        self.os_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.os_table.setFixedHeight(300)
        os_vbox.addWidget(self.os_table)
        
        self.data_layout.addWidget(os_group)
        self.data_layout.addStretch()

    def apply_filters(self):
        # 1. Filter Equipments
        filtered_eq = self.equipment_data
        if self.f_modelo.text():
            filtered_eq = [i for i in filtered_eq if self.f_modelo.text().lower() in i["modelo"].lower()]
        if self.f_setor.currentText() != "Todos Setores":
            filtered_eq = [i for i in filtered_eq if i["setor"] == self.f_setor.currentText()]
            
        self.equip_table.setRowCount(len(filtered_eq))
        for r, item in enumerate(filtered_eq):
            self.equip_table.setItem(r, 0, QTableWidgetItem(item.get("identificador", "N/A")))
            self.equip_table.setItem(r, 1, QTableWidgetItem(item["modelo"]))
            self.equip_table.setItem(r, 2, QTableWidgetItem(item["setor"]))
            self.equip_table.setItem(r, 3, QTableWidgetItem(str(item["criticidade"])))
            self.equip_table.setItem(r, 4, QTableWidgetItem(item["data_aquisicao"]))
            self.equip_table.setItem(r, 5, QTableWidgetItem(item["status"]))

        # 2. Filter OS
        all_os = []
        for eq in self.equipment_data:
            for os_item in eq.get("os", []):
                all_os.append({
                    "id": eq.get("identificador", "N/A"),
                    "modelo": eq["modelo"],
                    "data": os_item["data"],
                    "custo": os_item["custo"],
                    "desc": os_item["desc"]
                })
                
        filtered_os = all_os
        if self.f_os_id.text():
            filtered_os = [i for i in filtered_os if self.f_os_id.text().lower() in i["id"].lower()]
        if self.f_os_min_cost.value() > 0:
            filtered_os = [i for i in filtered_os if i["custo"] >= self.f_os_min_cost.value()]
            
        self.os_table.setRowCount(len(filtered_os))
        for r, item in enumerate(filtered_os):
            self.os_table.setItem(r, 0, QTableWidgetItem(item["id"]))
            self.os_table.setItem(r, 1, QTableWidgetItem(item["modelo"]))
            self.os_table.setItem(r, 2, QTableWidgetItem(item["data"]))
            self.os_table.setItem(r, 3, QTableWidgetItem(f"R$ {item['custo']:,.2f}"))
            self.os_table.setItem(r, 4, QTableWidgetItem(item["desc"]))

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_THEME_QSS)
    window = HospitalDashboard()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
