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
    QGraphicsLineItem, QTabWidget, QStackedWidget, QListWidget, QListWidgetItem,
    QStyle, QProgressDialog
)
from PySide6.QtCore import Qt, QDateTime, QEvent, QDate
from PySide6.QtGui import QColor, QPainter, QFont, QPen, QIcon
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
    {"modelo": "Ventilador PB 840", "setor": "UTI Adulto (Clínica e Cirúrgica)", "criticidade": 3, "data_aquisicao": "2012-03-10", "status": "Em uso", "valor": 45000, "score": 88, "identificador": "HCPE-0002", "os": generate_mock_os(12)},
    {"modelo": "Raio-X Digital", "setor": "Emergência", "criticidade": 2, "data_aquisicao": "2011-08-20", "status": "Inoperante", "valor": 250000, "score": 82, "identificador": "HCPE-0003", "os": generate_mock_os(10)},
    {"modelo": "Bomba Alaris", "setor": "UTI Neonatal", "criticidade": 1, "data_aquisicao": "2015-11-05", "status": "Disponível", "valor": 8000, "score": 35, "identificador": "HCPE-0004", "os": generate_mock_os(5)},
    {"modelo": "Monitor V24", "setor": "UTI Cardio", "criticidade": 2, "data_aquisicao": "2018-02-28", "status": "Em uso", "valor": 15000, "score": 42, "identificador": "HCPE-0005", "os": generate_mock_os(8)},
    {"modelo": "Lifepak 15", "setor": "Bloco Cirúrgico", "criticidade": 3, "data_aquisicao": "2013-06-15", "status": "Disponível", "valor": 35000, "score": 75, "identificador": "HCPE-0006", "os": generate_mock_os(10)},
    {"modelo": "Tomógrafo CT660", "setor": "Radiologia", "criticidade": 3, "data_aquisicao": "2009-12-01", "status": "Em uso", "valor": 1800000, "score": 78, "identificador": "HCPE-0007", "os": generate_mock_os(20)},
    {"modelo": "Ultrassom Voluson", "setor": "Centro Obstétrico", "criticidade": 2, "data_aquisicao": "2020-04-10", "status": "Em uso", "valor": 400000, "score": 25, "identificador": "HCPE-0008", "os": generate_mock_os(6)},
    {"modelo": "Autoclave Sterivap", "setor": "CME", "criticidade": 2, "data_aquisicao": "2014-09-22", "status": "Disponível", "valor": 120000, "score": 55, "identificador": "HCPE-0009", "os": generate_mock_os(9)},
    {"modelo": "Foco LED", "setor": "Bloco Cirúrgico", "criticidade": 2, "data_aquisicao": "2012-10-15", "status": "Em uso", "valor": 60000, "score": 62, "identificador": "HCPE-0010", "os": generate_mock_os(7)},
]

DARK_THEME_QSS = """
QMainWindow, QWidget {
    background-color: #060D18;
    color: #E2EDF8;
    font-family: 'Inter', 'Segoe UI', Arial;
    font-size: 13px;
}
QGroupBox {
    border: 1px solid #1A2D45;
    border-radius: 10px;
    margin-top: 18px;
    font-weight: bold;
    padding-top: 22px;
    background-color: #0A1628;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    left: 14px;
    color: #5A8AB8;
    font-size: 10px;
    text-transform: uppercase;
}
QCheckBox { color: #C4D8EE; spacing: 8px; }
QCheckBox::indicator {
    width: 16px; height: 16px;
    border-radius: 4px;
    border: 1px solid #2A4A6E;
    background: #0D1E35;
}
QCheckBox::indicator:checked { background: #2563EB; border-color: #60A5FA; }
QLineEdit, QComboBox, QDateEdit, QSpinBox {
    background-color: #0D1E35;
    border: 1px solid #1E3A5F;
    border-radius: 6px;
    padding: 8px 10px;
    color: #E2EDF8;
    selection-background-color: #2563EB;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus { border-color: #3B82F6; }
QComboBox::drop-down { border: none; width: 20px; }
QComboBox QAbstractItemView {
    background: #0D1E35;
    border: 1px solid #1E3A5F;
    color: #E2EDF8;
    selection-background-color: #2563EB;
}
QPushButton {
    background-color: #1D4ED8;
    color: white;
    border-radius: 6px;
    padding: 9px 18px;
    font-weight: 600;
    border: none;
    font-size: 13px;
}
QPushButton:hover { background-color: #2563EB; }
QPushButton:pressed { background-color: #1E40AF; }
QPushButton#ExportBtn {
    background-color: #0D1E35;
    color: #5A8AB8;
    font-size: 10px;
    padding: 2px 8px;
    border: 1px solid #1E3A5F;
    border-radius: 4px;
}
QPushButton#ExportBtn:hover { background-color: #122038; color: white; }
QTableWidget {
    background-color: #0A1628;
    gridline-color: #111E30;
    border: 1px solid #1A2D45;
    border-radius: 8px;
    alternate-background-color: #0D1E35;
}
QTableWidget::item { padding: 6px 10px; }
QTableWidget::item:selected { background-color: #1D4ED8; color: white; }
QHeaderView::section {
    background-color: #0D1E35;
    color: #5A8AB8;
    padding: 8px 10px;
    border: none;
    border-bottom: 2px solid #1E3A5F;
    font-weight: bold;
    font-size: 10px;
    text-transform: uppercase;
}
QHeaderView::section:hover { background-color: #122038; color: #93C5FD; }
QTabBar::tab {
    padding: 11px 28px;
    background: transparent;
    color: #3D5A78;
    font-weight: 700;
    font-size: 13px;
    margin-right: 2px;
    border-bottom: 3px solid transparent;
}
QTabBar::tab:selected { color: #60A5FA; border-bottom: 3px solid #3B82F6; background: transparent; }
QTabBar::tab:hover { color: #93C5FD; }
QTabWidget::pane { border: 1px solid #1A2D45; border-radius: 8px; top: -1px; background: #08111E; }
QStatusBar { background-color: #04080F; color: #2D4A68; border-top: 1px solid #111E30; font-size: 11px; padding: 0 8px; }
QScrollBar:vertical { background: #060D18; width: 6px; border: none; }
QScrollBar::handle:vertical { background: #1E3A5F; border-radius: 3px; min-height: 20px; }
QScrollBar::handle:vertical:hover { background: #2A4A6E; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QScrollBar:horizontal { background: #060D18; height: 6px; border: none; }
QScrollBar::handle:horizontal { background: #1E3A5F; border-radius: 3px; min-width: 20px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }
QToolTip {
    background-color: #0D1E35;
    color: #E2EDF8;
    border: 1px solid #2A4A6E;
    padding: 6px 10px;
    border-radius: 6px;
    font-size: 12px;
}
QDialog { background-color: #060D18; }
QScrollArea { border: none; background: transparent; }
QListWidget {
    background: #0A1628;
    border: 1px solid #1A2D45;
    border-radius: 8px;
    color: #C4D8EE;
    outline: none;
}
QListWidget::item { padding: 7px 10px; border-radius: 4px; }
QListWidget::item:selected { background: #1D4ED8; color: white; }
QListWidget::item:hover { background: #122038; }
QProgressDialog { background: #0A1628; color: #E2EDF8; }
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
        
        header_card = QFrame()
        header_card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #0A1628,stop:0.6 #0A1628,stop:1 #060D18);
                border-radius: 12px;
                border: 1px solid #1A2D45;
            }
        """)
        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(22, 16, 22, 16)
        header_layout.setSpacing(14)

        lbl_icon = QLabel("⚕")
        lbl_icon.setStyleSheet("font-size: 32px; color: #3B82F6; border: none; background: transparent;")
        header_layout.addWidget(lbl_icon)

        title_block = QVBoxLayout()
        title_block.setSpacing(2)
        header = QLabel("Dashboard de Engenharia Clínica")
        header.setStyleSheet("font-size: 20px; font-weight: 800; color: #F0F6FF; border: none; background: transparent;")
        sub_header = QLabel("Gestão e monitoramento de equipamentos hospitalares")
        sub_header.setStyleSheet("font-size: 11px; color: #2D4A68; border: none; background: transparent;")
        title_block.addWidget(header)
        title_block.addWidget(sub_header)
        header_layout.addLayout(title_block)
        header_layout.addStretch()

        btn_settings = QPushButton("⚙  Configurações")
        btn_settings.setStyleSheet("""
            QPushButton { background: #0D1E35; color: #7BA8D8; padding: 9px 16px; border-radius: 7px;
                          font-weight: 600; border: 1px solid #1E3A5F; font-size: 12px; }
            QPushButton:hover { background: #122038; color: #E2EDF8; }
        """)
        btn_settings.clicked.connect(self.open_settings)
        header_layout.addWidget(btn_settings)

        btn_back = QPushButton("← Voltar")
        btn_back.setStyleSheet("""
            QPushButton { background: #0D1E35; color: #5A8AB8; padding: 9px 16px; border-radius: 7px;
                          font-weight: 600; border: 1px solid #1A2D45; font-size: 12px; }
            QPushButton:hover { background: #122038; color: #C4D8EE; }
        """)
        btn_back.clicked.connect(self.go_back_with_confirmation)
        header_layout.addWidget(btn_back)

        self.main_layout.addWidget(header_card)
        
        self.active_years = set(range(2018, 2026))
        self.selected_setores = []
        if not hasattr(self, '_overlays'): self._overlays = []
        
        self.tabs = QTabWidget()
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
        self.filtered_equipment_data = self.equipment_data
        self.df_os = pd.DataFrame()
        
        self.setup_kpi_row()
        self.setup_insights_row()
        self.setup_history_row()
        self.setup_cost_analysis_row()
        self.setup_data_tab()

    def _make_file_row(self, placeholder, dialog_title, icon="📄", optional=False):
        row_frame = QFrame()
        row_frame.setStyleSheet("""
            QFrame {
                background-color: #0A1628;
                border: 1px solid #1A2D45;
                border-radius: 8px;
            }
            QFrame:hover { border-color: #2A4A6E; }
        """)
        row_lay = QHBoxLayout(row_frame)
        row_lay.setContentsMargins(12, 10, 12, 10)
        row_lay.setSpacing(10)

        lbl_icon = QLabel(icon)
        lbl_icon.setStyleSheet("font-size: 18px; border: none; background: transparent;")
        lbl_icon.setFixedWidth(26)

        path_edit = QLineEdit()
        label_text = placeholder + (" (opcional)" if optional else "")
        path_edit.setPlaceholderText(label_text)
        path_edit.setReadOnly(True)
        path_edit.setStyleSheet("QLineEdit { background: transparent; border: none; color: #C4D8EE; font-size: 12px; }")

        btn = QPushButton("Procurar")
        btn.setFixedWidth(80)
        btn.setStyleSheet("""
            QPushButton { background: #122038; color: #7BA8D8; border: 1px solid #1E3A5F;
                          border-radius: 5px; padding: 5px 10px; font-size: 11px; font-weight: bold; }
            QPushButton:hover { background: #1E3A5F; color: #E2EDF8; }
        """)
        btn.clicked.connect(lambda: path_edit.setText(
            QFileDialog.getOpenFileName(self, dialog_title, "", "CSV Files (*.csv)")[0]
        ))

        row_lay.addWidget(lbl_icon)
        row_lay.addWidget(path_edit, 1)
        row_lay.addWidget(btn)
        return row_frame, path_edit

    def setup_import_page(self):
        page = QWidget()
        page.setStyleSheet("QWidget { background-color: #060D18; }")
        outer = QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)

        # ── Top branding strip ──────────────────────────────────────────
        brand_bar = QFrame()
        brand_bar.setFixedHeight(64)
        brand_bar.setStyleSheet("QFrame { background-color: #0A1628; border-bottom: 1px solid #1A2D45; }")
        brand_lay = QHBoxLayout(brand_bar)
        brand_lay.setContentsMargins(32, 0, 32, 0)

        lbl_cross = QLabel("⚕")
        lbl_cross.setStyleSheet("font-size: 26px; color: #3B82F6; border: none;")
        lbl_brand = QLabel("Sistema de Gestão de Equipamentos Hospitalares")
        lbl_brand.setStyleSheet("font-size: 16px; font-weight: 800; color: #E2EDF8; border: none; letter-spacing: 0.3px;")
        brand_lay.addWidget(lbl_cross)
        brand_lay.addSpacing(10)
        brand_lay.addWidget(lbl_brand)
        brand_lay.addStretch()

        outer.addWidget(brand_bar)

        # ── Centered content ────────────────────────────────────────────
        center_lay = QVBoxLayout()
        center_lay.setAlignment(Qt.AlignCenter)
        outer.addLayout(center_lay, 1)

        card = QFrame()
        card.setFixedWidth(580)
        card.setStyleSheet("""
            QFrame {
                background-color: #0A1628;
                border-radius: 14px;
                border: 1px solid #1A2D45;
            }
        """)
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(0, 0, 0, 0)
        card_lay.setSpacing(0)

        # Accent top bar
        top_accent = QFrame()
        top_accent.setFixedHeight(4)
        top_accent.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1D4ED8, stop:1 #06B6D4); border-radius: 14px 14px 0 0; border: none;")
        card_lay.addWidget(top_accent)

        inner = QWidget()
        inner.setStyleSheet("background: transparent; border: none;")
        inner_lay = QVBoxLayout(inner)
        inner_lay.setContentsMargins(32, 28, 32, 32)
        inner_lay.setSpacing(20)

        # Title section
        title_lbl = QLabel("Importação de Dados")
        title_lbl.setStyleSheet("font-size: 22px; font-weight: 800; color: #F0F6FF; border: none;")
        title_lbl.setAlignment(Qt.AlignCenter)
        sub_lbl = QLabel("Selecione as planilhas para carregar o dashboard")
        sub_lbl.setStyleSheet("font-size: 13px; color: #3D5A78; border: none;")
        sub_lbl.setAlignment(Qt.AlignCenter)
        inner_lay.addWidget(title_lbl)
        inner_lay.addWidget(sub_lbl)

        # Divider
        div = QFrame(); div.setFrameShape(QFrame.HLine)
        div.setStyleSheet("border: none; background: #1A2D45; max-height: 1px;")
        inner_lay.addWidget(div)

        # File rows
        equip_row, self.equip_path = self._make_file_row("Planilha de Equipamentos", "Selecionar Planilha de Equipamentos", "🗂")
        crit_row,  self.crit_path  = self._make_file_row("Planilha de Criticidade", "Selecionar Planilha de Criticidade", "⚖", optional=True)
        os_ant_row, self.os_antiga_path = self._make_file_row("OS — Formato Antigo", "Selecionar Planilha OS Antiga", "🗃")
        os_atu_row, self.os_atual_path  = self._make_file_row("OS — Formato Atual",  "Selecionar Planilha OS Atual",  "📋")

        for row in (equip_row, crit_row, os_ant_row, os_atu_row):
            inner_lay.addWidget(row)

        # Action buttons
        btn_run = QPushButton("▶  Carregar Dados e Acessar Dashboard")
        btn_run.setStyleSheet("""
            QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #1D4ED8,stop:1 #0E7490);
                          color: white; padding: 14px; border-radius: 8px; font-size: 14px; font-weight: 700; }
            QPushButton:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #2563EB,stop:1 #0891B2); }
        """)
        btn_run.clicked.connect(self.load_data)
        inner_lay.addWidget(btn_run)

        btn_row = QHBoxLayout()
        btn_export = QPushButton("⬇  Exportar CSV")
        btn_export.setStyleSheet("""
            QPushButton { background: #0D1E35; color: #34D399; border: 1px solid #065F46;
                          padding: 10px; border-radius: 7px; font-size: 12px; font-weight: 600; }
            QPushButton:hover { background: #0A2E1E; }
        """)
        btn_export.clicked.connect(self.export_data)

        btn_demo = QPushButton("◈  Dados de Demonstração")
        btn_demo.setToolTip("Abre o dashboard com dados fictícios de exemplo.")
        btn_demo.setStyleSheet("""
            QPushButton { background: #0D1E35; color: #7BA8D8; border: 1px solid #1E3A5F;
                          padding: 10px; border-radius: 7px; font-size: 12px; font-weight: 600; }
            QPushButton:hover { background: #122038; color: #C4D8EE; }
        """)
        btn_demo.clicked.connect(self.load_demo_data)

        btn_row.addWidget(btn_export)
        btn_row.addWidget(btn_demo)
        inner_lay.addLayout(btn_row)

        card_lay.addWidget(inner)
        center_lay.addWidget(card, 0, Qt.AlignHCenter)

        # ── History section ─────────────────────────────────────────────
        hist_card = QFrame()
        hist_card.setFixedWidth(580)
        hist_card.setStyleSheet("QFrame { background: #0A1628; border: 1px solid #1A2D45; border-radius: 10px; }")
        hist_lay = QVBoxLayout(hist_card)
        hist_lay.setContentsMargins(20, 16, 20, 16)
        hist_lay.setSpacing(8)

        self.history_path_file = os.path.join(os.path.dirname(__file__), 'data', 'history.json')
        hist_title = QLabel("IMPORTAÇÕES RECENTES")
        hist_title.setStyleSheet("color: #2A4A6E; font-size: 10px; font-weight: bold; border: none;")
        hist_lay.addWidget(hist_title)

        self.history_list = QListWidget()
        self.history_list.setFixedHeight(110)
        self.history_list.itemClicked.connect(self.load_history_item)
        hist_lay.addWidget(self.history_list)

        self.populate_history()
        center_lay.addSpacing(16)
        center_lay.addWidget(hist_card, 0, Qt.AlignHCenter)

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
                        tooltip_parts = []
                        if equip and equip != 'N/A': tooltip_parts.append(f"Equipamentos: {equip}")
                        if os_antiga: tooltip_parts.append(f"OS Antiga: {os_antiga}")
                        if os_atual: tooltip_parts.append(f"OS Atual: {os_atual}")
                        list_item.setToolTip("\n".join(tooltip_parts))
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

    def load_demo_data(self):
        self.equipment_data = MOCK_EQUIPMENT
        self.df_os = pd.DataFrame()
        self.root_stack.setCurrentIndex(1)
        self.update_dashboard_data()

    def load_data(self):
        progress = QProgressDialog("Processando dados, aguarde...", None, 0, 0, self)
        progress.setWindowTitle("Carregando")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        QApplication.processEvents()

        proceed = True
        try:
            self.df_os = migrar_dados_servico(
                caminho_os_antiga=self.os_antiga_path.text() or None,
                caminho_os_atual=self.os_atual_path.text() or None
            )
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
                progress.close()
                dialog = DataPreviewDialog(self.df_os, self)
                if dialog.exec() != QDialog.Accepted:
                    proceed = False

        except Exception as e:
            QMessageBox.warning(self, "Aviso", f"Não foi possível carregar os dados OS.\nUsando dados MOCK.\n\nDetalhe: {e}")
            self.df_os = pd.DataFrame()
            self.equipment_data = MOCK_EQUIPMENT
        finally:
            progress.close()

        if proceed:
            self.root_stack.setCurrentIndex(1)
            self.update_dashboard_data()

    def go_back_with_confirmation(self):
        reply = QMessageBox.question(
            self, "Voltar para Importação",
            "Deseja voltar para a tela de importação?\nOs dados carregados serão mantidos.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.root_stack.setCurrentIndex(0)

    def open_settings(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Configurações de Análise")
        dialog.setMinimumWidth(400)
        dialog.setStyleSheet("QDialog { background-color: #0F172A; } QLabel { color: #F8FAFC; }")
        
        layout = QVBoxLayout(dialog)
        
        lbl = QLabel("Selecione os setores para incluir na análise:")
        lbl.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 5px;")
        layout.addWidget(lbl)

        bulk_btn_layout = QHBoxLayout()
        btn_select_all = QPushButton("Marcar Todos")
        btn_select_all.setStyleSheet("QPushButton { background-color: #1E293B; border: 1px solid #334155; font-size: 12px; padding: 4px; }")
        btn_deselect_all = QPushButton("Desmarcar Todos")
        btn_deselect_all.setStyleSheet("QPushButton { background-color: #1E293B; border: 1px solid #334155; font-size: 12px; padding: 4px; }")
        bulk_btn_layout.addWidget(btn_select_all)
        bulk_btn_layout.addWidget(btn_deselect_all)
        layout.addLayout(bulk_btn_layout)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: 1px solid #334155; border-radius: 4px; background: #1E293B; }")
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        all_setores = sorted(list(set(i.get("setor", "Desconhecido") for i in self.equipment_data)))
        checkboxes = []
        for s in all_setores:
            cb = QCheckBox(s)
            cb.setStyleSheet("QCheckBox { color: #F8FAFC; padding: 5px; font-size: 14px; }")
            if s in self.selected_setores:
                cb.setChecked(True)
            scroll_layout.addWidget(cb)
            checkboxes.append((s, cb))
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        def set_all_checkboxes(state):
            for _, cb in checkboxes:
                cb.setChecked(state)

        btn_select_all.clicked.connect(lambda: set_all_checkboxes(True))
        btn_deselect_all.clicked.connect(lambda: set_all_checkboxes(False))
        
        btn_layout = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setStyleSheet("QPushButton { background-color: #334155; }")
        btn_cancel.clicked.connect(dialog.reject)
        
        btn_apply = QPushButton("Aplicar")
        btn_apply.clicked.connect(dialog.accept)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_apply)
        layout.addLayout(btn_layout)
        
        if dialog.exec() == QDialog.Accepted:
            self.selected_setores = [s for s, cb in checkboxes if cb.isChecked()]
            self.update_dashboard_data_filtered()

    def update_dashboard_data(self):
        # Initialize selected sectors with defaults
        all_setores = sorted(list(set(i.get("setor", "Desconhecido") for i in self.equipment_data)))
        defaults = ["UTI Neonatal", "UTI Adulto", "Bloco Cirúrgico", "Centro Obstétrico"]
        
        self.selected_setores = [s for s in all_setores if any(d.lower() in s.lower() for d in defaults)]
        
        # If no defaults match, select all
        if not self.selected_setores:
            self.selected_setores = all_setores

        self.update_dashboard_data_filtered()

    def update_dashboard_data_filtered(self):
        if not self.selected_setores:
            self.filtered_equipment_data = self.equipment_data
        else:
            self.filtered_equipment_data = [i for i in self.equipment_data if i.get("setor") in self.selected_setores]

        self.setup_kpi_row()
        self.update_global_chart()
        self.update_cost_analysis_charts()

        self.f_setor.blockSignals(True)
        self.f_setor.clear()
        self.f_setor.addItems(["Todos Setores"] + sorted(list(set(i.get("setor", "Desconhecido") for i in self.equipment_data))))
        self.f_setor.blockSignals(False)

        self.update_age_donut()
        self.apply_filters()

        n_equip = len(self.filtered_equipment_data)
        n_os = sum(len(e.get("os", [])) for e in self.filtered_equipment_data)
        n_setores = len(self.selected_setores) if self.selected_setores else len(set(i.get("setor") for i in self.equipment_data))
        self.statusBar().showMessage(f"  {n_equip} equipamentos  |  {n_os} OS  |  {n_setores} setor(es) selecionado(s)")

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
        
        total_equip = len(self.filtered_equipment_data)
        
        # Calculate OS and Cost based on filtered equipment
        total_os = sum(len(equip.get("os", [])) for equip in self.filtered_equipment_data)
        total_cost = sum(os_data.get("custo", 0) for equip in self.filtered_equipment_data for os_data in equip.get("os", []))
        
        total_cost_str = f"R$ {total_cost:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        def create_kpi_card(title, value, icon, accent):
            card = QFrame()
            card.setStyleSheet(f"QFrame {{ background-color: #0A1628; border-radius: 12px; border: 1px solid #1A2D45; }}")
            card_vbox = QVBoxLayout(card)
            card_vbox.setContentsMargins(0, 0, 0, 0)
            card_vbox.setSpacing(0)

            accent_bar = QFrame()
            accent_bar.setFixedHeight(4)
            accent_bar.setStyleSheet(f"background: {accent}; border-radius: 12px 12px 0 0; border: none;")
            card_vbox.addWidget(accent_bar)

            inner = QWidget()
            inner.setStyleSheet("background: transparent; border: none;")
            inner_vbox = QVBoxLayout(inner)
            inner_vbox.setContentsMargins(22, 16, 22, 20)
            inner_vbox.setSpacing(6)

            top_row = QHBoxLayout()
            lbl_title = QLabel(title.upper())
            lbl_title.setStyleSheet("color: #2D4A68; font-size: 10px; font-weight: bold; letter-spacing: 1px; border: none;")
            lbl_icon = QLabel(icon)
            lbl_icon.setStyleSheet(f"color: {accent}; font-size: 22px; border: none;")
            lbl_icon.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            top_row.addWidget(lbl_title)
            top_row.addStretch()
            top_row.addWidget(lbl_icon)
            inner_vbox.addLayout(top_row)

            lbl_val = QLabel(str(value))
            lbl_val.setStyleSheet(f"color: #F0F6FF; font-size: 30px; font-weight: 800; border: none;")
            inner_vbox.addWidget(lbl_val)

            card_vbox.addWidget(inner)
            return card

        kpi_layout.addWidget(create_kpi_card("Total de Equipamentos", total_equip,  "⚕",  "#3B82F6"), 1)
        kpi_layout.addWidget(create_kpi_card("Total de OS Emitidas",  total_os,     "◈",  "#F59E0B"), 1)
        kpi_layout.addWidget(create_kpi_card("Total Gasto em OS",     total_cost_str, "◉", "#10B981"), 1)
        
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
        self.top5_group.setStyleSheet("QGroupBox { border: 1px solid #334155; border-radius: 12px; padding-top: 15px; font-weight: bold; }")
        top5_layout = QVBoxLayout(self.top5_group)
        top5_layout.setContentsMargins(24, 15, 24, 24)
        top5_layout.setSpacing(5)
        
        # Segmented-style toggle
        toggle_frame = QFrame(self.top5_group)
        toggle_frame.setStyleSheet("""
            QFrame { background: #0D1E35; border-radius: 8px; border: 1px solid #1E3A5F; }
            QPushButton { background: transparent; border: none; padding: 5px 14px; border-radius: 6px; color: #3D5A78; font-weight: bold; font-size: 11px; }
            QPushButton:checked { background: #1D4ED8; color: white; }
        """)
        toggle_lay = QHBoxLayout(toggle_frame)
        toggle_lay.setContentsMargins(2, 2, 2, 2)
        toggle_lay.setSpacing(0)

        self.btn_show_chart = QPushButton("Gráfico")
        self.btn_show_chart.setCheckable(True)
        self.btn_show_chart.setChecked(True)
        self.btn_show_table = QPushButton("Tabela")
        self.btn_show_table.setCheckable(True)
        
        toggle_lay.addWidget(self.btn_show_chart)
        toggle_lay.addWidget(self.btn_show_table)
        
        self._overlays.append((self.top5_group, toggle_frame))
        self.top5_group.installEventFilter(self)
        
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
        
        group_style = "QGroupBox { border: 1px solid #1A2D45; border-radius: 12px; padding-top: 24px; font-weight: bold; background: #0A1628; }"

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

        for equip in self.filtered_equipment_data:
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
        chart_evol.setBackgroundBrush(QColor("#0A1628"))
        chart_evol.setTitleBrush(QColor("#C4D8EE"))
        series_evol = QLineSeries()
        series_evol.setColor(QColor("#FBBF24"))
        series_evol.setPointsVisible(True)
        pen_evol = series_evol.pen(); pen_evol.setWidth(2); series_evol.setPen(pen_evol)
        
        years = sorted(cost_by_year.keys())
        axis_x_evol = QBarCategoryAxis()
        axis_x_evol.append([str(y) for y in years])
        axis_x_evol.setLabelsColor(QColor("#4A6A8A"))
        chart_evol.addAxis(axis_x_evol, Qt.AlignBottom)

        axis_y_evol = QValueAxis()
        axis_y_evol.setLabelsColor(QColor("#4A6A8A"))
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
        bar_set.setBrush(QColor("#F87171"))
        categories_top10 = []
        for mod, c in top10_equip:
            bar_set.append(c)
            categories_top10.append(mod.split(" ")[0])
        
        series_bar = QBarSeries()
        series_bar.append(bar_set)
        
        chart_top10 = QChart()
        chart_top10.setAnimationOptions(QChart.SeriesAnimations)
        chart_top10.setBackgroundBrush(QColor("#0A1628"))
        chart_top10.addSeries(series_bar)
        
        axis_x_bar = QBarCategoryAxis()
        axis_x_bar.append(categories_top10)
        axis_x_bar.setLabelsColor(QColor("#4A6A8A"))
        chart_top10.addAxis(axis_x_bar, Qt.AlignBottom)
        series_bar.attachAxis(axis_x_bar)
        
        axis_y_bar = QValueAxis()
        axis_y_bar.setLabelsColor(QColor("#4A6A8A"))
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
        colors = ["#60A5FA", "#34D399", "#FBBF24", "#F87171", "#A78BFA", "#F472B6", "#2DD4BF", "#FB923C", "#38BDF8", "#818CF8"]
        
        for i, (sec, c) in enumerate(top10_sectors):
            slice_ = series_sec.append(sec, c)
            slice_.setBrush(QColor(colors[i % len(colors)]))
            slice_.setLabelVisible(True)
            slice_.setLabelColor(QColor("#4A6A8A"))
            
        chart_sec = QChart()
        chart_sec.setAnimationOptions(QChart.SeriesAnimations)
        chart_sec.setBackgroundBrush(QColor("#0A1628"))
        chart_sec.addSeries(series_sec)
        chart_sec.legend().setAlignment(Qt.AlignBottom)
        chart_sec.legend().setLabelColor(QColor("#C4D8EE"))
        self.sector_chart_view.setChart(chart_sec)

    def update_age_donut(self):
        threshold = self.age_threshold.value()
        data_source = self.filtered_equipment_data
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
        s1 = series.append(f"≥ {threshold} Anos ({over} - {pct_over:.1f}%)", over); s1.setBrush(QColor("#F87171"))
        s2 = series.append(f"< {threshold} Anos ({under} - {pct_under:.1f}%)", under); s2.setBrush(QColor("#60A5FA"))
        for slice in series.slices(): slice.setLabelVisible(True); slice.setLabelColor(QColor("#4A6A8A"))
        chart = QChart(); chart.setAnimationOptions(QChart.SeriesAnimations); chart.addSeries(series); chart.setTitle(f"Corte: {threshold} anos")
        chart.setBackgroundBrush(QColor("#0A1628")); chart.setTitleBrush(QColor("#C4D8EE"))
        chart.legend().setAlignment(Qt.AlignBottom); chart.legend().setLabelColor(QColor("#C4D8EE"))
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
        chart = QChart(); chart.setAnimationOptions(QChart.SeriesAnimations); chart.setBackgroundBrush(QColor("#0A1628")); chart.setTitleBrush(QColor("#C4D8EE"))
        colors = ["#34D399", "#60A5FA", "#FBBF24", "#F87171", "#A78BFA", "#F472B6", "#2DD4BF", "#FB923C"]
        
        all_years = list(range(2018, 2026))
        
        # Re-populating year_data from filtered_equipment_data
        year_data = {y: {m: 0 for m in range(1, 13)} for y in all_years}
        for equip in self.filtered_equipment_data:
            for os in equip["os"]:
                dt = datetime.strptime(os["data"], "%Y-%m-%d").date()
                if dt.year in all_years:
                    if not (self.cb_excluir_custo_zero.isChecked() and os.get("custo", 0) == 0):
                        year_data[dt.year][dt.month] += 1

        axis_x = QBarCategoryAxis()
        axis_x.append(["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"])
        axis_x.setLabelsColor(QColor("#4A6A8A"))
        axis_x.setGridLineVisible(True)
        axis_x.setGridLineColor(QColor("#1A2D45"))
        chart.addAxis(axis_x, Qt.AlignBottom)
        
        axis_y = QValueAxis(); axis_y.setLabelsColor(QColor("#4A6A8A")); axis_y.setLabelFormat("%d")
        axis_y.setGridLineVisible(True)
        axis_y.setGridLineColor(QColor("#1A2D45"))
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
            avg_series.setColor(QColor("#C4D8EE")); avg_series.setPointsVisible(True)
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
        chart.legend().setLabelColor(QColor("#C4D8EE"))
        
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
        sorted_items = sorted(self.filtered_equipment_data, key=lambda x: x["score"], reverse=True)[:5]
        
        # Update Table
        self.top5_table_view.setRowCount(len(sorted_items))
        for r, item in enumerate(sorted_items):
            self.top5_table_view.setItem(r, 0, QTableWidgetItem(item["modelo"]))
            self.top5_table_view.setItem(r, 1, QTableWidgetItem(f"{item['score']:.1f}"))
            self.top5_table_view.setItem(r, 2, QTableWidgetItem(item.get("identificador", "N/A")))
            
        # Update Chart
        series = QHorizontalBarSeries()
        bar_set = QBarSet("Score")
        bar_set.setBrush(QColor("#F472B6"))
        
        categories = []
        for item in reversed(sorted_items):
            bar_set.append(item["score"])
            categories.append(item["modelo"])
            
        series.append(bar_set)
        
        chart = QChart()
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.setBackgroundBrush(QColor("#0A1628"))
        chart.addSeries(series)
        chart.legend().setVisible(False)
        
        axis_y = QBarCategoryAxis()
        axis_y.append(categories)
        axis_y.setLabelsColor(QColor("#4A6A8A"))
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)
        
        axis_x = QValueAxis()
        axis_x.setLabelsColor(QColor("#4A6A8A"))
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
            
        self.data_layout.setSpacing(15)
        
        # 1. Equipments Section
        equip_group = QGroupBox("Listagem de Equipamentos")
        equip_group.setStyleSheet("QGroupBox { padding-top: 15px; }")
        equip_vbox = QVBoxLayout(equip_group)
        equip_vbox.setContentsMargins(15, 5, 15, 15)
        equip_vbox.setSpacing(2)
        
        filters_eq = QHBoxLayout()
        filters_eq.setContentsMargins(0, 0, 0, 0)
        filters_eq.setSpacing(10)
        self.f_modelo = QLineEdit(); self.f_modelo.setPlaceholderText("Filtrar modelo...")
        self.f_modelo.textChanged.connect(self.apply_filters)
        self.f_setor = QComboBox()
        self.f_setor.currentIndexChanged.connect(self.apply_filters)
        filters_eq.addWidget(self.f_modelo)
        filters_eq.addWidget(self.f_setor)
        equip_vbox.addLayout(filters_eq)
        
        self.lbl_equip_count = QLabel("0 equipamentos")
        self.lbl_equip_count.setStyleSheet("color: #64748B; font-size: 11px;")
        equip_vbox.addWidget(self.lbl_equip_count)

        self.equip_table = QTableWidget()
        self.equip_table.setColumnCount(6)
        self.equip_table.setHorizontalHeaderLabels(["Identificador", "Modelo", "Setor", "Crit.", "Aquisição", "Status"])
        self.equip_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.equip_table.setFixedHeight(300)
        self.equip_table.setAlternatingRowColors(True)
        self.equip_table.setSortingEnabled(True)
        self.equip_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.equip_table.setToolTip("Clique duas vezes em um equipamento para ver detalhes")
        self.equip_table.cellDoubleClicked.connect(self.on_equip_table_double_click)
        equip_vbox.addWidget(self.equip_table)
        
        self.data_layout.addWidget(equip_group)
        
        # 2. OS Section
        os_group = QGroupBox("Listagem de Ordens de Serviço")
        os_group.setStyleSheet("QGroupBox { padding-top: 15px; }")
        os_vbox = QVBoxLayout(os_group)
        os_vbox.setContentsMargins(15, 5, 15, 15)
        os_vbox.setSpacing(2)
        
        filters_os = QHBoxLayout()
        filters_os.setContentsMargins(0, 0, 0, 0)
        filters_os.setSpacing(10)
        self.f_os_id = QLineEdit(); self.f_os_id.setPlaceholderText("Filtrar Identificador...")
        self.f_os_id.textChanged.connect(self.apply_filters)
        self.f_os_min_cost = QSpinBox(); self.f_os_min_cost.setRange(0, 1000000); self.f_os_min_cost.setPrefix("Custo Min: R$ ")
        self.f_os_min_cost.valueChanged.connect(self.apply_filters)
        
        filters_os.addWidget(self.f_os_id)
        filters_os.addWidget(self.f_os_min_cost)
        os_vbox.addLayout(filters_os)
        
        self.lbl_os_count = QLabel("0 ordens de serviço")
        self.lbl_os_count.setStyleSheet("color: #64748B; font-size: 11px;")
        os_vbox.addWidget(self.lbl_os_count)

        self.os_table = QTableWidget()
        self.os_table.setColumnCount(5)
        self.os_table.setHorizontalHeaderLabels(["ID Equip.", "Modelo", "Data", "Custo", "Descrição"])
        self.os_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.os_table.setFixedHeight(300)
        self.os_table.setAlternatingRowColors(True)
        self.os_table.setSortingEnabled(True)
        self.os_table.setSelectionBehavior(QTableWidget.SelectRows)
        os_vbox.addWidget(self.os_table)
        
        self.data_layout.addWidget(os_group)
        self.data_layout.addStretch()

    def on_equip_table_double_click(self, row, _col):
        id_item = self.equip_table.item(row, 0)
        if not id_item:
            return
        identifier = id_item.text()
        for eq in self.equipment_data:
            if eq.get("identificador") == identifier:
                self.show_equipment_modal(eq)
                break

    def apply_filters(self):
        # 1. Filter Equipments
        filtered_eq = self.equipment_data
        if self.f_modelo.text():
            filtered_eq = [i for i in filtered_eq if self.f_modelo.text().lower() in i["modelo"].lower()]
        if self.f_setor.currentText() != "Todos Setores":
            filtered_eq = [i for i in filtered_eq if i["setor"] == self.f_setor.currentText()]

        STATUS_COLORS = {"Em uso": "#34D399", "Inoperante": "#F87171", "Disponível": "#FBBF24"}
        CRIT_LABELS = {1: "● Baixa", 2: "●● Média", 3: "●●● Alta"}
        CRIT_COLORS = {1: "#4A6A8A", 2: "#FBBF24", 3: "#F87171"}

        self.equip_table.setSortingEnabled(False)
        self.equip_table.setRowCount(len(filtered_eq))
        for r, item in enumerate(filtered_eq):
            self.equip_table.setItem(r, 0, QTableWidgetItem(item.get("identificador", "N/A")))
            self.equip_table.setItem(r, 1, QTableWidgetItem(item["modelo"]))
            self.equip_table.setItem(r, 2, QTableWidgetItem(item["setor"]))

            crit_val = item["criticidade"]
            crit_item = QTableWidgetItem(CRIT_LABELS.get(crit_val, str(crit_val)))
            crit_item.setForeground(QColor(CRIT_COLORS.get(crit_val, "#E2EDF8")))
            self.equip_table.setItem(r, 3, crit_item)

            self.equip_table.setItem(r, 4, QTableWidgetItem(item["data_aquisicao"]))

            status = item["status"]
            status_item = QTableWidgetItem(status)
            status_item.setForeground(QColor(STATUS_COLORS.get(status, "#C4D8EE")))
            self.equip_table.setItem(r, 5, status_item)
        self.equip_table.setSortingEnabled(True)
        self.lbl_equip_count.setText(f"{len(filtered_eq)} equipamento(s) encontrado(s)")

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

        self.os_table.setSortingEnabled(False)
        self.os_table.setRowCount(len(filtered_os))
        for r, item in enumerate(filtered_os):
            self.os_table.setItem(r, 0, QTableWidgetItem(item["id"]))
            self.os_table.setItem(r, 1, QTableWidgetItem(item["modelo"]))
            self.os_table.setItem(r, 2, QTableWidgetItem(item["data"]))
            self.os_table.setItem(r, 3, QTableWidgetItem(f"R$ {item['custo']:,.2f}"))
            self.os_table.setItem(r, 4, QTableWidgetItem(item["desc"]))
        self.os_table.setSortingEnabled(True)
        self.lbl_os_count.setText(f"{len(filtered_os)} ordem(ns) de serviço encontrada(s)")

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_THEME_QSS)
    window = HospitalDashboard()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
