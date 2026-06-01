import sys
import os
import json
import csv
import uuid
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
from PySide6.QtCore import Qt, QDateTime, QEvent, QDate, QSize
from PySide6.QtGui import QColor, QPainter, QFont, QPen, QIcon, QPixmap
from PySide6.QtCharts import QChart, QChartView, QPieSeries, QLineSeries, QDateTimeAxis, QValueAxis, QScatterSeries, QBarSet, QBarCategoryAxis, QHorizontalBarSeries

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

        self.saved_analyses_file = os.path.join(os.path.dirname(__file__), 'data', 'saved_analyses.json')
        self.setup_home_page()   # index 0
        self.setup_import_page() # index 1
        
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
                background: #0A1628;
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
        sub_header.setStyleSheet("font-size: 12px; color: #8FB4DC; border: none; background: transparent;")
        self.lbl_loaded_files = QLabel("")
        self.lbl_loaded_files.setStyleSheet("font-size: 11px; color: #5A8AB8; border: none; background: transparent;")
        self.lbl_loaded_files.setTextInteractionFlags(Qt.TextSelectableByMouse)
        title_block.addWidget(header)
        title_block.addWidget(sub_header)
        title_block.addWidget(self.lbl_loaded_files)
        header_layout.addLayout(title_block)
        header_layout.addStretch()

        _icon_btn_qss = """
            QPushButton { background: #0D1E35; color: #7BA8D8; border-radius: 7px;
                          border: 1px solid #1E3A5F; font-size: 18px;
                          min-width: 42px; min-height: 40px;
                          max-width: 42px; max-height: 40px;
                          padding: 0px; }
            QPushButton:hover { background: #122038; color: #E2EDF8; }
        """
        btn_settings = QPushButton("⚙")
        btn_settings.setStyleSheet(_icon_btn_qss)
        btn_settings.setToolTip("Configurações")
        btn_settings.clicked.connect(self.open_settings)
        header_layout.addWidget(btn_settings)

        btn_save_analysis = QPushButton()
        btn_save_analysis.setStyleSheet(_icon_btn_qss)
        btn_save_analysis.setIcon(QIcon(self._action_icon("save", 22, "#7BA8D8")))
        btn_save_analysis.setIconSize(QSize(22, 22))
        btn_save_analysis.setToolTip("Salvar análise")
        btn_save_analysis.clicked.connect(self.save_analysis)
        header_layout.addWidget(btn_save_analysis)

        btn_back = QPushButton("←")
        btn_back.setStyleSheet(_icon_btn_qss)
        btn_back.setToolTip("Voltar à tela inicial")
        btn_back.clicked.connect(self.go_back_with_confirmation)
        header_layout.addWidget(btn_back)

        self.main_layout.addWidget(header_card)
        
        self.active_years = set(range(2018, 2026))
        self.selected_setores = []
        self._excluir_custo_zero = False
        # Pesos do algoritmo de priorização de substituição (pontos máximos por critério)
        self._peso_idade = 20
        self._peso_criticidade = 50
        self._peso_custo = 30
        self._pending_filters = None
        self._auto_confirm_next_load = False
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
        self._all_os_flat = []
        self._chart_data = {}

        self.setup_kpi_row()
        self.setup_insights_row()
        self.setup_history_row()
        self.setup_cost_analysis_row()
        self.setup_data_tab()

    def _action_icon(self, kind, px=20, color="#7BA8D8"):
        """Ícone vetorial desenhado (não depende de glifos de fonte, que bugam
        em alguns ambientes). kind: 'play' | 'close' | 'save'."""
        from PySide6.QtCore import QPointF, QRectF
        from PySide6.QtGui import QPolygonF, QPainterPath
        pm = QPixmap(px, px)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        col = QColor(color)

        if kind == "play":
            p.setPen(Qt.NoPen)
            p.setBrush(col)
            m = px * 0.30
            tri = QPolygonF([QPointF(m, m), QPointF(m, px - m), QPointF(px - m, px / 2)])
            p.drawPolygon(tri)
        elif kind == "close":
            pen = QPen(col)
            pen.setWidthF(max(2.0, px * 0.11))
            pen.setCapStyle(Qt.RoundCap)
            p.setPen(pen)
            m = px * 0.30
            p.drawLine(QPointF(m, m), QPointF(px - m, px - m))
            p.drawLine(QPointF(px - m, m), QPointF(m, px - m))
        elif kind == "save":
            # Disquete (metáfora clássica de "salvar")
            pen = QPen(col)
            pen.setWidthF(max(1.6, px * 0.075))
            pen.setJoinStyle(Qt.RoundJoin)
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)
            m = px * 0.20
            x0, y0, x1, y1 = m, m, px - m, px - m
            cut = (x1 - x0) * 0.26
            body = QPainterPath()
            body.moveTo(x0, y0)
            body.lineTo(x1 - cut, y0)
            body.lineTo(x1, y0 + cut)
            body.lineTo(x1, y1)
            body.lineTo(x0, y1)
            body.closeSubpath()
            p.drawPath(body)
            w = x1 - x0
            h = y1 - y0
            # obturador (topo) e etiqueta (base)
            p.drawRect(QRectF(x0 + w * 0.26, y0, w * 0.40, h * 0.30))
            p.drawRect(QRectF(x0 + w * 0.20, y1 - h * 0.34, w * 0.60, h * 0.34))
        p.end()
        return pm

    def _make_chart_card(self, title, export_key=None):
        """Returns (QFrame, content_QVBoxLayout). The header holds the title and,
        quando export_key é informado, botões para Copiar/Exportar os dados do gráfico."""
        frame = QFrame()
        frame.setStyleSheet(
            "QFrame { background: #0A1628; border: 1px solid #1A2D45; border-radius: 12px; }"
        )
        vbox = QVBoxLayout(frame)
        vbox.setContentsMargins(20, 16, 20, 16)
        vbox.setSpacing(10)

        header = QHBoxLayout()
        header.setSpacing(8)
        lbl = QLabel(title.upper())
        lbl.setStyleSheet(
            "color: #5A8AB8; font-size: 11px; font-weight: bold; "
            "letter-spacing: 1.5px; border: none; background: transparent;"
        )
        header.addWidget(lbl)
        header.addStretch()

        if export_key:
            btn_copy = QPushButton("⧉  Copiar")
            btn_copy.setObjectName("ExportBtn")
            btn_copy.setCursor(Qt.PointingHandCursor)
            btn_copy.setToolTip("Copiar os dados deste gráfico (colável em planilha)")
            btn_copy.clicked.connect(lambda _=False, k=export_key: self._copy_chart_data(k))
            btn_exp = QPushButton("⭳  Exportar")
            btn_exp.setObjectName("ExportBtn")
            btn_exp.setCursor(Qt.PointingHandCursor)
            btn_exp.setToolTip("Exportar os dados deste gráfico para planilha (CSV)")
            btn_exp.clicked.connect(lambda _=False, k=export_key: self._export_chart_data(k))
            header.addWidget(btn_copy)
            header.addWidget(btn_exp)

        vbox.addLayout(header)
        return frame, vbox

    def _set_chart_data(self, key, headers, rows):
        """Registra a tabela subjacente de um gráfico para Copiar/Exportar."""
        if not hasattr(self, '_chart_data'):
            self._chart_data = {}
        self._chart_data[key] = (headers, rows)

    def _copy_chart_data(self, key):
        data = getattr(self, '_chart_data', {}).get(key)
        if not data or not data[1]:
            QMessageBox.information(self, "Sem dados", "Não há dados para copiar neste gráfico.")
            return
        headers, rows = data
        linhas = ["\t".join(str(c) for c in headers)]
        linhas += ["\t".join(str(c) for c in r) for r in rows]
        QApplication.clipboard().setText("\n".join(linhas))
        self.statusBar().showMessage("  Dados copiados para a área de transferência.", 4000)

    def _export_chart_data(self, key):
        data = getattr(self, '_chart_data', {}).get(key)
        if not data or not data[1]:
            QMessageBox.information(self, "Sem dados", "Não há dados para exportar neste gráfico.")
            return
        headers, rows = data
        path, _ = QFileDialog.getSaveFileName(self, "Exportar dados", f"{key}.csv", "CSV (*.csv)")
        if not path:
            return
        try:
            df = pd.DataFrame(rows, columns=headers)
            # utf-8-sig garante acentuação correta ao abrir no Excel
            df.to_csv(path, index=False, sep=';', encoding='utf-8-sig')
            self.statusBar().showMessage(f"  Dados exportados para {os.path.basename(path)}.", 5000)
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Não foi possível exportar: {e}")

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
        top_accent.setStyleSheet("background: #1D4ED8; border-radius: 14px 14px 0 0; border: none;")
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
            QPushButton { background: #1D4ED8;
                          color: white; padding: 14px; border-radius: 8px; font-size: 14px; font-weight: 700; }
            QPushButton:hover { background: #2563EB; }
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
        if not equip and not os_antiga and not os_atual:
            return
            
        history = []
        if os.path.exists(self.history_path_file):
            try:
                with open(self.history_path_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Aviso: histórico corrompido, iniciando novo histórico. Detalhes: {e}")
                
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
        self._is_demo = True
        self.root_stack.setCurrentIndex(2)
        self.update_dashboard_data()

    def _update_loaded_files_label(self):
        """Mostra no cabeçalho da análise quais planilhas estão carregadas."""
        if getattr(self, '_is_demo', False):
            self.lbl_loaded_files.setText("📄  Dados de demonstração")
            return
        rotulos = [
            ("Equipamentos", self.equip_path.text()),
            ("Criticidade", self.crit_path.text()),
            ("OS Antiga", self.os_antiga_path.text()),
            ("OS Atual", self.os_atual_path.text()),
        ]
        partes = [f"{nome}: {os.path.basename(caminho)}" for nome, caminho in rotulos if caminho]
        if partes:
            self.lbl_loaded_files.setText("📄  " + "   ·   ".join(partes))
            self.lbl_loaded_files.setToolTip(
                "\n".join(f"{nome}: {caminho}" for nome, caminho in rotulos if caminho)
            )
        else:
            self.lbl_loaded_files.setText("")
            self.lbl_loaded_files.setToolTip("")

    def load_data(self):
        progress = QProgressDialog("Processando dados, aguarde...", None, 0, 0, self)
        progress.setWindowTitle("Carregando")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        QApplication.processEvents()

        proceed = True
        self._is_demo = False
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
                if self._auto_confirm_next_load:
                    self._auto_confirm_next_load = False
                else:
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
            self.root_stack.setCurrentIndex(2)
            self.update_dashboard_data()

    def go_back_with_confirmation(self):
        reply = QMessageBox.question(
            self, "Voltar para Tela Inicial",
            "Deseja voltar para a tela inicial?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.root_stack.setCurrentIndex(0)
            self.populate_saved_analyses()

    def open_settings(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Configurações de Análise")
        dialog.setMinimumWidth(440)
        dialog.setMinimumHeight(640)
        dialog.setStyleSheet("QDialog { background-color: #060D18; } QLabel { color: #E2EDF8; }")

        lay = QVBoxLayout(dialog)
        lay.setContentsMargins(22, 20, 22, 18)
        lay.setSpacing(14)

        lbl_title = QLabel("Configurações de Análise")
        lbl_title.setStyleSheet("font-size: 16px; font-weight: 800; color: #F0F6FF;")
        lay.addWidget(lbl_title)

        # ── Opções gerais ─────────────────────────────────────────────
        lbl_opts = QLabel("OPÇÕES GERAIS")
        lbl_opts.setStyleSheet("font-size: 10px; font-weight: bold; color: #3D5A78; letter-spacing: 1.5px;")
        lay.addWidget(lbl_opts)

        cb_excluir = QCheckBox("Excluir OS com custo = 0 do histórico")
        cb_excluir.setChecked(self._excluir_custo_zero)
        cb_excluir.setStyleSheet(
            "QCheckBox { color: #C4D8EE; padding: 7px 10px; font-size: 13px; border-radius: 5px; }"
            "QCheckBox:hover { background: #0D1E35; }"
        )
        lay.addWidget(cb_excluir)

        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setStyleSheet("border: none; background: #1A2D45; max-height: 1px;")
        lay.addWidget(div)

        # ── Pesos do algoritmo de priorização ─────────────────────────
        lbl_pesos = QLabel("PESOS DA PRIORIZAÇÃO DE SUBSTITUIÇÃO")
        lbl_pesos.setStyleSheet("font-size: 10px; font-weight: bold; color: #3D5A78; letter-spacing: 1.5px;")
        lay.addWidget(lbl_pesos)

        lbl_pesos_hint = QLabel("Pontos máximos de cada critério no score de prioridade.")
        lbl_pesos_hint.setStyleSheet("font-size: 11px; color: #5A8AB8;")
        lay.addWidget(lbl_pesos_hint)

        pesos_lay = QHBoxLayout()
        pesos_lay.setSpacing(10)

        def _mk_peso(label, valor):
            box = QVBoxLayout()
            box.setSpacing(3)
            l = QLabel(label)
            l.setStyleSheet("font-size: 12px; color: #C4D8EE; border: none;")
            sp = QSpinBox()
            sp.setRange(0, 100)
            sp.setValue(valor)
            sp.setFixedHeight(34)
            box.addWidget(l)
            box.addWidget(sp)
            return box, sp

        box_i, sp_idade = _mk_peso("Idade (≥ corte)", self._peso_idade)
        box_c, sp_crit = _mk_peso("Criticidade", self._peso_criticidade)
        box_k, sp_custo = _mk_peso("Custo de OS", self._peso_custo)
        for b in (box_i, box_c, box_k):
            pesos_lay.addLayout(b)
        lay.addLayout(pesos_lay)

        lbl_total = QLabel()
        lbl_total.setStyleSheet("font-size: 11px; color: #5A8AB8;")
        def _atualizar_total():
            total = sp_idade.value() + sp_crit.value() + sp_custo.value()
            lbl_total.setText(f"Score máximo possível: {total} pontos")
        for sp in (sp_idade, sp_crit, sp_custo):
            sp.valueChanged.connect(_atualizar_total)
        _atualizar_total()
        lay.addWidget(lbl_total)

        div2 = QFrame()
        div2.setFrameShape(QFrame.HLine)
        div2.setStyleSheet("border: none; background: #1A2D45; max-height: 1px;")
        lay.addWidget(div2)

        # ── Setores ───────────────────────────────────────────────────
        lbl_setores = QLabel("SETORES DA ANÁLISE")
        lbl_setores.setStyleSheet("font-size: 10px; font-weight: bold; color: #3D5A78; letter-spacing: 1.5px;")
        lay.addWidget(lbl_setores)

        search = QLineEdit()
        search.setPlaceholderText("🔍  Pesquisar setor...")
        search.setStyleSheet("QLineEdit { font-size: 13px; padding: 9px 12px; }")
        lay.addWidget(search)

        bulk_lay = QHBoxLayout()
        bulk_lay.setSpacing(8)
        _bqss = "QPushButton { background: #0D1E35; color: #7BA8D8; border: 1px solid #1E3A5F; font-size: 12px; padding: 6px 14px; border-radius: 5px; } QPushButton:hover { background: #122038; color: #E2EDF8; }"
        btn_all = QPushButton("Marcar todos")
        btn_all.setStyleSheet(_bqss)
        btn_none = QPushButton("Desmarcar todos")
        btn_none.setStyleSheet(_bqss)
        bulk_lay.addWidget(btn_all)
        bulk_lay.addWidget(btn_none)
        bulk_lay.addStretch()
        lay.addLayout(bulk_lay)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: 1px solid #1A2D45; border-radius: 8px; background: #0A1628; }")
        sc_content = QWidget()
        sc_lay = QVBoxLayout(sc_content)
        sc_lay.setContentsMargins(8, 8, 8, 8)
        sc_lay.setSpacing(2)

        all_setores = sorted(list(set(i.get("setor", "Desconhecido") for i in self.equipment_data)))
        selected_first = [s for s in all_setores if s in self.selected_setores]
        rest = [s for s in all_setores if s not in self.selected_setores]
        checkboxes = []
        for s in selected_first + rest:
            cb = QCheckBox(s)
            cb.setStyleSheet("QCheckBox { color: #C4D8EE; padding: 7px 10px; font-size: 13px; border-radius: 5px; } QCheckBox:hover { background: #0D1E35; }")
            cb.setChecked(s in self.selected_setores)
            sc_lay.addWidget(cb)
            checkboxes.append((s, cb))
        sc_lay.addStretch()
        scroll.setWidget(sc_content)
        lay.addWidget(scroll)

        search.textChanged.connect(lambda t: [cb.setVisible(not t or t.lower() in s.lower()) for s, cb in checkboxes])
        btn_all.clicked.connect(lambda: [cb.setChecked(True) for s, cb in checkboxes if cb.isVisible()])
        btn_none.clicked.connect(lambda: [cb.setChecked(False) for s, cb in checkboxes if cb.isVisible()])

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setStyleSheet("QPushButton { background: #0D1E35; color: #5A8AB8; border: 1px solid #1A2D45; padding: 10px 20px; border-radius: 6px; } QPushButton:hover { background: #122038; }")
        btn_cancel.clicked.connect(dialog.reject)
        btn_ok = QPushButton("Aplicar")
        btn_ok.setStyleSheet("QPushButton { background: #1D4ED8; color: white; padding: 10px 24px; border-radius: 6px; font-weight: 700; border: none; } QPushButton:hover { background: #2563EB; }")
        btn_ok.clicked.connect(dialog.accept)
        btn_ok.setDefault(True)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_ok)
        lay.addLayout(btn_row)

        if dialog.exec() == QDialog.Accepted:
            self._excluir_custo_zero = cb_excluir.isChecked()
            self._peso_idade = sp_idade.value()
            self._peso_criticidade = sp_crit.value()
            self._peso_custo = sp_custo.value()
            self.selected_setores = [s for s, cb in checkboxes if cb.isChecked()]
            self.update_dashboard_data_filtered()

    def _equip_os(self, equip):
        """OS de um equipamento respeitando o filtro 'Excluir OS com custo = 0'
        das Configurações. Usado por todos os componentes da aba Análise para
        manter a reatividade consistente com os filtros."""
        os_list = equip.get("os", [])
        if self._excluir_custo_zero:
            return [o for o in os_list if o.get("custo", 0) != 0]
        return os_list

    def _build_os_cache(self):
        self._all_os_flat = [
            {
                "id": eq.get("identificador", "N/A"),
                "modelo": eq["modelo"],
                "setor": eq.get("setor", ""),
                "data": os_item["data"],
                "custo": os_item["custo"],
                "desc": os_item["desc"],
            }
            for eq in self.equipment_data
            for os_item in eq.get("os", [])
        ]

    def update_dashboard_data(self):
        self._build_os_cache()
        self._update_loaded_files_label()
        all_setores = sorted(list(set(i.get("setor", "Desconhecido") for i in self.equipment_data)))

        pending = self._pending_filters
        self._pending_filters = None

        if pending:
            saved_setores = pending.get("selected_setores", [])
            self.selected_setores = [s for s in saved_setores if s in all_setores]

        if not pending or not self.selected_setores:
            defaults = ["UTI Neonatal", "UTI Adulto", "Bloco Cirúrgico", "Centro Obstétrico"]
            self.selected_setores = [s for s in all_setores if any(d.lower() in s.lower() for d in defaults)]
            if not self.selected_setores:
                self.selected_setores = all_setores

        self.update_dashboard_data_filtered()

        if pending:
            base_widgets = [self.age_threshold,
                            self.f_modelo, self.f_setor, self.f_os_id, self.f_os_min_cost]
            extra_widgets = [w for w in [
                getattr(self, 'f_crit', None), getattr(self, 'f_status', None),
                getattr(self, 'f_os_modelo', None), getattr(self, 'f_os_desc', None),
            ] if w is not None]
            for w in base_widgets + extra_widgets:
                w.blockSignals(True)

            self.age_threshold.setValue(pending.get("age_threshold", 10))
            self.active_years = set(pending.get("active_years", list(range(2018, 2026))))
            self._excluir_custo_zero = pending.get("cb_excluir_custo_zero", False)
            self._peso_idade = pending.get("peso_idade", 20)
            self._peso_criticidade = pending.get("peso_criticidade", 50)
            self._peso_custo = pending.get("peso_custo", 30)
            self.f_modelo.setText(pending.get("f_modelo", ""))
            idx = self.f_setor.findText(pending.get("f_setor", "Todos Setores"))
            if idx >= 0:
                self.f_setor.setCurrentIndex(idx)
            self.f_os_id.setText(pending.get("f_os_id", ""))
            self.f_os_min_cost.setValue(pending.get("f_os_min_cost", 0))

            self._eq_setores_filter = pending.get("eq_setores_filter", [])
            self._os_setores_filter = pending.get("os_setores_filter", [])
            self._update_eq_setor_btn_label()
            self._update_os_setor_btn_label()

            if hasattr(self, 'f_crit'):
                i = self.f_crit.findText(pending.get("f_crit", "Todas criticidades"))
                if i >= 0: self.f_crit.setCurrentIndex(i)
            if hasattr(self, 'f_status'):
                i = self.f_status.findText(pending.get("f_status", "Todos status"))
                if i >= 0: self.f_status.setCurrentIndex(i)
            if hasattr(self, 'f_os_modelo'):
                self.f_os_modelo.setText(pending.get("f_os_modelo", ""))
            if hasattr(self, 'f_os_desc'):
                self.f_os_desc.setText(pending.get("f_os_desc", ""))

            for w in base_widgets + extra_widgets:
                w.blockSignals(False)
            self.update_age_donut()
            self.update_global_chart()
            self.apply_filters()

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
            self.analysis_layout.removeWidget(self.kpi_layout_widget)
            self.kpi_layout_widget.deleteLater()
            
        self.kpi_layout_widget = QWidget()
        kpi_layout = QHBoxLayout(self.kpi_layout_widget)
        kpi_layout.setContentsMargins(0,0,0,0)
        kpi_layout.setSpacing(24)
        
        total_equip = len(self.filtered_equipment_data)
        total_os = sum(len(self._equip_os(equip)) for equip in self.filtered_equipment_data)
        total_cost = sum(os_data.get("custo", 0) for equip in self.filtered_equipment_data for os_data in self._equip_os(equip))

        total_cost_str = f"R$ {total_cost:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        def create_kpi_card(title, value, icon, icon_color):
            card = QFrame()
            card.setStyleSheet("""
                QFrame { background-color: #0A1628; border-radius: 12px; border: 1px solid #1A2D45; }
            """)
            card_vbox = QVBoxLayout(card)
            card_vbox.setContentsMargins(22, 18, 22, 20)
            card_vbox.setSpacing(8)

            top_row = QHBoxLayout()
            lbl_title = QLabel(title.upper())
            lbl_title.setStyleSheet(
                "color: #5A8AB8; font-size: 11px; font-weight: bold; "
                "letter-spacing: 1.5px; border: none;"
            )
            lbl_icon = QLabel(icon)
            lbl_icon.setStyleSheet(f"color: {icon_color}; font-size: 22px; border: none;")
            lbl_icon.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            top_row.addWidget(lbl_title)
            top_row.addStretch()
            top_row.addWidget(lbl_icon)
            card_vbox.addLayout(top_row)

            lbl_val = QLabel(str(value))
            lbl_val.setStyleSheet("color: #F0F6FF; font-size: 30px; font-weight: 800; border: none;")
            card_vbox.addWidget(lbl_val)

            return card

        kpi_layout.addWidget(create_kpi_card("Total de Equipamentos", total_equip,    "⚕", "#60A5FA"), 1)
        kpi_layout.addWidget(create_kpi_card("Total de OS Emitidas",  total_os,       "◈", "#93C5FD"), 1)
        kpi_layout.addWidget(create_kpi_card("Total Gasto em OS",     total_cost_str, "◉", "#BFDBFE"), 1)
        
        self.analysis_layout.insertWidget(0, self.kpi_layout_widget)

    def setup_insights_row(self):
        layout = QHBoxLayout()
        layout.setSpacing(24)

        # ── Age Distribution card ─────────────────────────────────────
        age_card, age_vbox = self._make_chart_card("Distribuição por Idade", export_key="idade")

        age_ctrl_row = QHBoxLayout()
        age_ctrl_row.addStretch()
        lbl_age = QLabel("Corte (anos):")
        lbl_age.setStyleSheet("font-size: 11px; color: #3D5A78; border: none; background: transparent;")
        self.age_threshold = QSpinBox()
        self.age_threshold.setRange(1, 30)
        self.age_threshold.setValue(10)
        self.age_threshold.setFixedWidth(64)
        self.age_threshold.valueChanged.connect(self.update_age_donut)
        age_ctrl_row.addWidget(lbl_age)
        age_ctrl_row.addWidget(self.age_threshold)
        age_vbox.addLayout(age_ctrl_row)

        self.age_donut_view = QChartView()
        self.age_donut_view.setRenderHint(QPainter.Antialiasing)
        self.age_donut_view.setStyleSheet("background: transparent;")
        self.age_donut_view.setMinimumHeight(260)
        age_vbox.addWidget(self.age_donut_view)

        # ── Priorities card ───────────────────────────────────────────
        top5_card, top5_vbox = self._make_chart_card("Prioridades de Substituição", export_key="prioridades")
        self.top5_group = top5_card  # kept for eventFilter compat

        # Toggle inline, right-aligned, with proper sizing
        toggle_row = QHBoxLayout()

        btn_budget = QPushButton("Distribuir orçamento")
        btn_budget.setStyleSheet("""
            QPushButton { background: #0D1E35; color: #7BA8D8; border: 1px solid #1E3A5F;
                          padding: 6px 14px; border-radius: 6px; font-size: 12px; font-weight: 600; }
            QPushButton:hover { background: #122038; color: #E2EDF8; }
        """)
        btn_budget.clicked.connect(self.show_budget_distribution_dialog)
        toggle_row.addWidget(btn_budget)
        toggle_row.addStretch()

        toggle_frame = QFrame()
        toggle_frame.setStyleSheet("""
            QFrame { background: #0A1628; border-radius: 8px; border: 1px solid #1A2D45; }
            QPushButton {
                background: transparent; border: none;
                padding: 6px 22px; border-radius: 6px;
                color: #5A8AB8; font-weight: bold; font-size: 12px;
                min-width: 90px;
            }
            QPushButton:checked { background: #1A3A6E; color: #93C5FD; border: 1px solid #2A5A9F; }
            QPushButton:hover:!checked { color: #C4D8EE; }
        """)
        toggle_lay = QHBoxLayout(toggle_frame)
        toggle_lay.setContentsMargins(3, 3, 3, 3)
        toggle_lay.setSpacing(2)

        self.btn_show_chart = QPushButton("Gráfico")
        self.btn_show_chart.setCheckable(True)
        self.btn_show_chart.setChecked(True)
        self.btn_show_table = QPushButton("Tabela")
        self.btn_show_table.setCheckable(True)
        toggle_lay.addWidget(self.btn_show_chart)
        toggle_lay.addWidget(self.btn_show_table)
        toggle_row.addWidget(toggle_frame)
        top5_vbox.addLayout(toggle_row)

        self.top5_stack = QStackedWidget()
        self.top5_stack.setStyleSheet("QStackedWidget { background: transparent; border: none; }")

        self.top5_chart_view = QChartView()
        self.top5_chart_view.setRenderHint(QPainter.Antialiasing)
        self.top5_chart_view.setStyleSheet("background: transparent;")
        self.top5_chart_view.setMinimumHeight(260)

        self.top5_table_view = QTableWidget()
        self.top5_table_view.setColumnCount(3)
        self.top5_table_view.setHorizontalHeaderLabels(["Modelo", "Score", "Identificador"])
        self.top5_table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.top5_table_view.setAlternatingRowColors(True)

        self.top5_stack.addWidget(self.top5_chart_view)
        self.top5_stack.addWidget(self.top5_table_view)
        top5_vbox.addWidget(self.top5_stack)

        self.btn_show_chart.clicked.connect(lambda: self.set_top5_view(0))
        self.btn_show_table.clicked.connect(lambda: self.set_top5_view(1))

        self.update_age_donut()

        layout.addWidget(age_card, 1)
        layout.addWidget(top5_card, 2)
        self.analysis_layout.addLayout(layout)

    def set_top5_view(self, index):
        self.top5_stack.setCurrentIndex(index)
        self.btn_show_chart.setChecked(index == 0)
        self.btn_show_table.setChecked(index == 1)

    def setup_history_row(self):
        layout = QHBoxLayout()
        layout.setSpacing(24)

        # ── Esquerda: Custo por Setor (stretch 1) ────────────────────
        sector_card, sector_layout = self._make_chart_card("Custo por Setor (Top 5)", export_key="custo_setor")
        self.sector_chart_view = QChartView()
        self.sector_chart_view.setRenderHint(QPainter.Antialiasing)
        self.sector_chart_view.setStyleSheet("background: transparent;")
        self.sector_chart_view.setMinimumHeight(300)
        sector_layout.addWidget(self.sector_chart_view)
        layout.addWidget(sector_card, 1)

        # ── Direita: Histórico de Emissão de OS (stretch 2) ──────────
        hist_card, chart_vbox = self._make_chart_card("Histórico de Emissão de OS", export_key="historico_os")
        self.history_group = hist_card

        self.global_chart_view = CrosshairChartView()
        self.global_chart_view.setRenderHint(QPainter.Antialiasing)
        self.global_chart_view.setStyleSheet("background: transparent;")
        self.global_chart_view.setMinimumHeight(300)
        chart_vbox.addWidget(self.global_chart_view)

        layout.addWidget(hist_card, 2)

        self.update_global_chart()
        self.analysis_layout.addLayout(layout)

    def setup_cost_analysis_row(self):
        layout = QHBoxLayout()
        layout.setSpacing(24)

        # ── Esquerda: Evolução de Custo (stretch 1) ──────────────────
        evol_card, evol_layout = self._make_chart_card("Evolução do Custo Total por Ano", export_key="evolucao_custo")
        self.cost_evol_chart_view = QChartView()
        self.cost_evol_chart_view.setRenderHint(QPainter.Antialiasing)
        self.cost_evol_chart_view.setStyleSheet("background: transparent;")
        self.cost_evol_chart_view.setMinimumHeight(320)
        evol_layout.addWidget(self.cost_evol_chart_view)
        layout.addWidget(evol_card, 1)

        # ── Direita: Top 10 Equipamentos (stretch 2) ─────────────────
        top10_card, top10_layout = self._make_chart_card("Top 10 Equipamentos — Custo", export_key="top10_custo")
        self.top10_chart_view = QChartView()
        self.top10_chart_view.setRenderHint(QPainter.Antialiasing)
        self.top10_chart_view.setStyleSheet("background: transparent;")
        self.top10_chart_view.setMinimumHeight(320)
        top10_layout.addWidget(self.top10_chart_view)
        layout.addWidget(top10_card, 2)

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
            for os in self._equip_os(equip):
                try:
                    year = datetime.strptime(os["data"], "%Y-%m-%d").year
                except (ValueError, KeyError):
                    continue
                c = os["custo"]
                e_cost += c
                cost_by_year[year] = cost_by_year.get(year, 0) + c
            equip_cost[modelo] = equip_cost.get(modelo, 0) + e_cost
            sector_cost[setor] = sector_cost.get(setor, 0) + e_cost

        # 1. Evolution Chart
        chart_evol = QChart()
        chart_evol.setAnimationOptions(QChart.SeriesAnimations)
        chart_evol.setBackgroundVisible(False)
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

        self._set_chart_data("evolucao_custo", ["Ano", "Custo total (R$)"],
                             [[y, round(cost_by_year[y], 2)] for y in years])

        # 2. Top 10 Equip — horizontal bars with click-to-detail
        top10_equip = sorted(equip_cost.items(), key=lambda x: x[1], reverse=True)[:10]
        top10_equip_reversed = list(reversed(top10_equip))

        self._set_chart_data("top10_custo", ["Modelo", "Custo total (R$)"],
                             [[m, round(c, 2)] for m, c in top10_equip])

        bar_set_top10 = QBarSet("Custo")
        bar_set_top10.setBrush(QColor("#1D4ED8"))
        bar_set_top10.setSelectedColor(QColor("#60A5FA"))
        categories_top10 = []
        for mod, c in top10_equip_reversed:
            bar_set_top10.append(c)
            categories_top10.append(mod)

        series_hbar = QHorizontalBarSeries()
        series_hbar.append(bar_set_top10)

        chart_top10 = QChart()
        chart_top10.setAnimationOptions(QChart.SeriesAnimations)
        chart_top10.setBackgroundVisible(False)
        chart_top10.addSeries(series_hbar)

        axis_y_cat = QBarCategoryAxis()
        axis_y_cat.append(categories_top10)
        axis_y_cat.setLabelsColor(QColor("#7BA8D8"))
        axis_y_cat.setTruncateLabels(False)
        chart_top10.addAxis(axis_y_cat, Qt.AlignLeft)
        series_hbar.attachAxis(axis_y_cat)

        axis_x_val = QValueAxis()
        axis_x_val.setLabelsColor(QColor("#4A6A8A"))
        axis_x_val.setLabelFormat("%.0f")
        max_c = max([c for m, c in top10_equip]) if top10_equip else 1000
        axis_x_val.setRange(0, max_c * 1.1)
        chart_top10.addAxis(axis_x_val, Qt.AlignBottom)
        series_hbar.attachAxis(axis_x_val)
        chart_top10.legend().setVisible(False)

        top10_lookup = {eq["modelo"]: eq for eq in self.filtered_equipment_data}

        def on_top10_bar_clicked(index, barset=None):
            real_index = index if isinstance(index, int) else 0
            if 0 <= real_index < len(top10_equip_reversed):
                model_name = top10_equip_reversed[real_index][0]
                eq = top10_lookup.get(model_name)
                if eq:
                    self.show_equipment_modal(eq)

        bar_set_top10.clicked.connect(on_top10_bar_clicked)
        self.top10_chart_view.setChart(chart_top10)

        # 3. Sector Cost
        top10_sectors = sorted(sector_cost.items(), key=lambda x: x[1], reverse=True)[:5]
        self._set_chart_data("custo_setor", ["Setor", "Custo total (R$)"],
                             [[s, round(c, 2)] for s, c in top10_sectors])
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
        chart_sec.setBackgroundVisible(False)
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

        self._set_chart_data("idade", ["Faixa", "Equipamentos", "Percentual"],
                             [[f"≥ {threshold} anos", over, f"{pct_over:.1f}%"],
                              [f"< {threshold} anos", under, f"{pct_under:.1f}%"]])

        series = QPieSeries()
        series.setHoleSize(0.58)
        s1 = series.append(f"≥ {threshold} anos  ·  {over} equip. ({pct_over:.1f}%)", over)
        s1.setBrush(QColor("#EF4444"))  # vermelho = urgência (equipamentos mais antigos)
        s1.setExploded(True)
        s1.setExplodeDistanceFactor(0.07)
        s1.setLabelVisible(True)
        s1.setLabelColor(QColor("#F87171"))
        s2 = series.append(f"< {threshold} anos  ·  {under} equip. ({pct_under:.1f}%)", under)
        s2.setBrush(QColor("#1E3A5F"))
        s2.setLabelVisible(True)
        s2.setLabelColor(QColor("#3D5A78"))
        chart = QChart()
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.addSeries(series)
        chart.setTitle(f"Corte: {threshold} anos")
        chart.setBackgroundVisible(False)
        chart.setTitleBrush(QColor("#C4D8EE"))
        chart.legend().setAlignment(Qt.AlignBottom)
        chart.legend().setLabelColor(QColor("#C4D8EE"))
        self.age_donut_view.setChart(chart)
        
        # Recalcula scores aplicando o algoritmo de priorização sobre o dataframe
        # JÁ FILTRADO pelos setores das Configurações: a normalização de custo
        # passa a ser relativa ao maior custo dentro dos setores selecionados.
        scored_data = self.filtered_equipment_data
        max_custo = 0
        for eq in scored_data:
            tot = sum(o.get('custo', 0) for o in self._equip_os(eq))
            if tot > max_custo: max_custo = tot

        for eq in scored_data:
            try:
                anos = current_year - int(eq["data_aquisicao"].split("-")[0])
            except:
                anos = 0
            idade_pts = self._peso_idade if anos >= threshold else 0
            crit_pts = (eq.get('criticidade', 1) / 3.0) * self._peso_criticidade
            tot = sum(o.get('custo', 0) for o in self._equip_os(eq))
            custo_pts = (tot / max_custo * self._peso_custo) if max_custo > 0 else 0
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
        chart = QChart(); chart.setAnimationOptions(QChart.SeriesAnimations); chart.setBackgroundVisible(False); chart.setTitleBrush(QColor("#C4D8EE"))
        colors = ["#34D399", "#60A5FA", "#FBBF24", "#F87171", "#A78BFA", "#F472B6", "#2DD4BF", "#FB923C"]
        
        all_years = list(range(2018, 2026))
        
        # Re-populating year_data from filtered_equipment_data
        year_data = {y: {m: 0 for m in range(1, 13)} for y in all_years}
        for equip in self.filtered_equipment_data:
            for os in equip["os"]:
                try:
                    dt = datetime.strptime(os["data"], "%Y-%m-%d").date()
                except (ValueError, KeyError):
                    continue  # OS sem data válida não entra no histórico temporal
                if dt.year in all_years:
                    if not (self._excluir_custo_zero and os.get("custo", 0) == 0):
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

        meses_nomes = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
        n_ativos = len(self.active_years)
        hist_rows = []
        for month in range(1, 13):
            linha = [meses_nomes[month - 1]] + [year_data[y][month] for y in all_years]
            linha.append(round(averages[month] / n_ativos, 2) if n_ativos else 0)
            hist_rows.append(linha)
        self._set_chart_data(
            "historico_os",
            ["Mês"] + [str(y) for y in all_years] + ["Média (anos ativos)"],
            hist_rows,
        )

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

    def populate_top5(self):
        sorted_items = sorted(self.filtered_equipment_data, key=lambda x: x["score"], reverse=True)[:5]

        self._set_chart_data("prioridades", ["Posição", "Modelo", "Score", "Identificador"],
                             [[i + 1, it["modelo"], round(it["score"], 1), it.get("identificador", "N/A")]
                              for i, it in enumerate(sorted_items)])

        # Update Table
        self.top5_table_view.setRowCount(len(sorted_items))
        for r, item in enumerate(sorted_items):
            self.top5_table_view.setItem(r, 0, QTableWidgetItem(item["modelo"]))
            self.top5_table_view.setItem(r, 1, QTableWidgetItem(f"{item['score']:.1f}"))
            self.top5_table_view.setItem(r, 2, QTableWidgetItem(item.get("identificador", "N/A")))
            
        # Update Chart
        series = QHorizontalBarSeries()
        bar_set = QBarSet("Score")
        bar_set.setBrush(QColor("#2563EB"))
        bar_set.setSelectedColor(QColor("#60A5FA"))

        categories = []
        for item in reversed(sorted_items):
            bar_set.append(item["score"])
            categories.append(item["modelo"])

        series.append(bar_set)

        chart = QChart()
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.setBackgroundVisible(False)
        chart.addSeries(series)
        chart.legend().setVisible(False)

        axis_y = QBarCategoryAxis()
        axis_y.append(categories)
        axis_y.setLabelsColor(QColor("#7BA8D8"))
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)

        axis_x = QValueAxis()
        axis_x.setLabelsColor(QColor("#4A6A8A"))
        score_max = self._peso_idade + self._peso_criticidade + self._peso_custo
        axis_x.setRange(0, score_max if score_max > 0 else 100)
        axis_x.setLabelFormat("%.0f")
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)

        reversed_items = list(reversed(sorted_items))

        def on_bar_clicked(index, barset=None):
            real_index = index if isinstance(index, int) else 0
            if 0 <= real_index < len(reversed_items):
                self.show_equipment_modal(reversed_items[real_index])

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

    def show_budget_distribution_dialog(self):
        sorted_equip = sorted(self.filtered_equipment_data, key=lambda x: x.get("score", 0), reverse=True)
        if not sorted_equip:
            QMessageBox.warning(self, "Sem dados", "Não há equipamentos nos setores filtrados.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Distribuição de Orçamento por Prioridade")
        dialog.resize(760, 540)
        dialog.setStyleSheet("QDialog { background-color: #060D18; }")

        layout = QVBoxLayout(dialog)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 20, 24, 20)

        # Header
        lbl_title = QLabel("Distribuição de Orçamento por Prioridade de Substituição")
        lbl_title.setStyleSheet("font-size: 16px; font-weight: 800; color: #F0F6FF;")
        lbl_sub = QLabel(
            f"Setores incluídos: {', '.join(self.selected_setores) if self.selected_setores else 'Todos'}  |  "
            f"{len(sorted_equip)} equipamento(s) disponíveis"
        )
        lbl_sub.setStyleSheet("font-size: 11px; color: #3D5A78;")
        lbl_sub.setWordWrap(True)
        layout.addWidget(lbl_title)
        layout.addWidget(lbl_sub)

        # Inputs row
        input_frame = QFrame()
        input_frame.setStyleSheet("QFrame { background: #0A1628; border: 1px solid #1A2D45; border-radius: 8px; }")
        input_lay = QHBoxLayout(input_frame)
        input_lay.setContentsMargins(16, 12, 16, 12)
        input_lay.setSpacing(16)

        lbl_budget = QLabel("Orçamento total:")
        lbl_budget.setStyleSheet("color: #C4D8EE; font-size: 13px; border: none; background: transparent;")
        budget_input = QLineEdit("1000000.00")
        budget_input.setPlaceholderText("Ex: 500000.00")
        budget_input.setFixedWidth(160)

        lbl_n = QLabel("Nº de equipamentos:")
        lbl_n.setStyleSheet("color: #C4D8EE; font-size: 13px; border: none; background: transparent;")
        n_spin = QSpinBox()
        n_spin.setRange(1, len(sorted_equip))
        n_spin.setValue(min(10, len(sorted_equip)))
        n_spin.setFixedWidth(70)

        btn_calc = QPushButton("Calcular")
        btn_calc.setFixedWidth(100)

        input_lay.addWidget(lbl_budget)
        input_lay.addWidget(budget_input)
        input_lay.addSpacing(8)
        input_lay.addWidget(lbl_n)
        input_lay.addWidget(n_spin)
        input_lay.addSpacing(8)
        input_lay.addWidget(btn_calc)
        input_lay.addStretch()
        layout.addWidget(input_frame)

        # Summary label
        lbl_summary = QLabel("")
        lbl_summary.setStyleSheet("color: #FBBF24; font-size: 12px; font-weight: 600;")
        layout.addWidget(lbl_summary)

        # Results table
        result_table = QTableWidget()
        result_table.setColumnCount(5)
        result_table.setHorizontalHeaderLabels(["Modelo", "Setor", "Score", "Orçamento Alocado", "Participação %"])
        result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        result_table.setAlternatingRowColors(True)
        result_table.verticalHeader().setVisible(False)
        result_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(result_table)

        def _fmt_brl(val):
            return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        def calc():
            try:
                budget = float(budget_input.text().replace(",", ".").replace("R$", "").strip())
            except ValueError:
                QMessageBox.warning(dialog, "Valor inválido", "Digite um valor numérico para o orçamento.")
                return
            if budget <= 0:
                QMessageBox.warning(dialog, "Valor inválido", "O orçamento deve ser maior que zero.")
                return

            n = n_spin.value()
            top_n = sorted_equip[:n]
            total_score = sum(e.get("score", 0) for e in top_n)

            result_table.setRowCount(len(top_n))
            for i, eq in enumerate(top_n):
                score = eq.get("score", 0)
                if total_score > 0:
                    allocation = (score / total_score) * budget
                    pct = (score / total_score) * 100
                else:
                    allocation = budget / len(top_n)
                    pct = 100.0 / len(top_n)

                result_table.setItem(i, 0, QTableWidgetItem(eq["modelo"]))
                result_table.setItem(i, 1, QTableWidgetItem(eq.get("setor", "")))

                score_item = QTableWidgetItem(f"{score:.1f}")
                score_item.setForeground(QColor("#F472B6"))
                score_item.setTextAlignment(Qt.AlignCenter)
                result_table.setItem(i, 2, score_item)

                budget_item = QTableWidgetItem(_fmt_brl(allocation))
                budget_item.setForeground(QColor("#34D399"))
                budget_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                result_table.setItem(i, 3, budget_item)

                pct_item = QTableWidgetItem(f"{pct:.1f}%")
                pct_item.setTextAlignment(Qt.AlignCenter)
                result_table.setItem(i, 4, pct_item)

            allocated_total = budget
            lbl_summary.setText(
                f"Orçamento de {_fmt_brl(allocated_total)} distribuído entre {n} equipamento(s) "
                f"com base no score de prioridade de substituição."
            )

        btn_calc.clicked.connect(calc)
        calc()

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
        while self.data_layout.count():
            item = self.data_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        self.data_layout.setSpacing(20)

        self._eq_page = 0
        self._eq_page_size = 20
        self._os_page = 0
        self._os_page_size = 20
        self._filtered_eq_cache = []
        self._filtered_os_cache = []
        self._eq_setores_filter = []
        self._os_setores_filter = []

        _filter_btn_qss = """
            QPushButton { background: #0D1E35; color: #7BA8D8; border: 1px solid #1E3A5F;
                          padding: 8px 12px; border-radius: 6px; font-size: 12px;
                          font-weight: 600; text-align: left; }
            QPushButton:hover { background: #122038; color: #E2EDF8; }
        """
        _page_btn_qss = """
            QPushButton { background: #0D1E35; color: #7BA8D8; border: 1px solid #1E3A5F;
                          border-radius: 5px; font-size: 13px; padding: 3px 10px; }
            QPushButton:hover { background: #122038; }
            QPushButton:disabled { color: #1E3A5F; border-color: #0D1A28; background: #08111E; }
        """

        # ── Equipment section ─────────────────────────────────────────
        eq_frame, eq_vbox = self._make_chart_card("Listagem de Equipamentos")

        filters_eq = QHBoxLayout()
        filters_eq.setSpacing(8)

        self.f_modelo = QLineEdit()
        self.f_modelo.setPlaceholderText("🔍  Modelo ou identificador...")
        self.f_modelo.textChanged.connect(self.apply_filters)

        self.btn_eq_setor = QPushButton("Setor: Todos  ▾")
        self.btn_eq_setor.setStyleSheet(_filter_btn_qss)
        self.btn_eq_setor.clicked.connect(self._open_eq_setor_picker)

        self.f_crit = QComboBox()
        self.f_crit.addItems(["Todas criticidades", "● Baixa", "●● Média", "●●● Alta"])
        self.f_crit.setMinimumWidth(150)
        self.f_crit.currentIndexChanged.connect(self.apply_filters)

        self.f_status = QComboBox()
        self.f_status.addItems(["Todos status", "Em uso", "Inoperante", "Disponível"])
        self.f_status.setMinimumWidth(120)
        self.f_status.currentIndexChanged.connect(self.apply_filters)

        # Hidden f_setor for backward compat with update_dashboard_data_filtered + save/load
        self.f_setor = QComboBox()
        self.f_setor.setVisible(False)

        filters_eq.addWidget(self.f_modelo, 3)
        filters_eq.addWidget(self.btn_eq_setor, 2)
        filters_eq.addWidget(self.f_crit, 2)
        filters_eq.addWidget(self.f_status, 2)
        eq_vbox.addLayout(filters_eq)

        self.equip_table = QTableWidget()
        self.equip_table.setColumnCount(6)
        self.equip_table.setHorizontalHeaderLabels(["Identificador", "Modelo", "Setor", "Crit.", "Aquisição", "Status"])
        self.equip_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.equip_table.setMinimumHeight(260)
        self.equip_table.setAlternatingRowColors(True)
        self.equip_table.setSortingEnabled(True)
        self.equip_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.equip_table.setToolTip("Clique duas vezes para ver detalhes do equipamento")
        self.equip_table.cellDoubleClicked.connect(self.on_equip_table_double_click)
        eq_vbox.addWidget(self.equip_table)

        eq_page_bar = QHBoxLayout()
        eq_page_bar.setSpacing(6)
        self.lbl_equip_count = QLabel("0 equipamentos")
        self.lbl_equip_count.setStyleSheet("color: #3D5A78; font-size: 11px; border: none; background: transparent;")
        self.btn_eq_prev = QPushButton("←")
        self.btn_eq_prev.setFixedSize(32, 26)
        self.btn_eq_prev.setStyleSheet(_page_btn_qss)
        self.btn_eq_prev.clicked.connect(lambda: self._goto_eq_page(self._eq_page - 1))
        self.lbl_eq_page = QLabel("Pág. 1 de 1")
        self.lbl_eq_page.setStyleSheet("color: #5A8AB8; font-size: 11px; border: none; background: transparent;")
        self.lbl_eq_page.setAlignment(Qt.AlignCenter)
        self.lbl_eq_page.setFixedWidth(90)
        self.btn_eq_next = QPushButton("→")
        self.btn_eq_next.setFixedSize(32, 26)
        self.btn_eq_next.setStyleSheet(_page_btn_qss)
        self.btn_eq_next.clicked.connect(lambda: self._goto_eq_page(self._eq_page + 1))
        eq_page_bar.addWidget(self.lbl_equip_count)
        eq_page_bar.addStretch()
        eq_page_bar.addWidget(self.btn_eq_prev)
        eq_page_bar.addWidget(self.lbl_eq_page)
        eq_page_bar.addWidget(self.btn_eq_next)
        eq_vbox.addLayout(eq_page_bar)

        self.data_layout.addWidget(eq_frame)

        # ── OS section ─────────────────────────────────────────────────
        os_frame, os_vbox = self._make_chart_card("Listagem de Ordens de Serviço")

        filters_os1 = QHBoxLayout()
        filters_os1.setSpacing(8)
        self.f_os_id = QLineEdit()
        self.f_os_id.setPlaceholderText("🔍  Identificador do equipamento...")
        self.f_os_id.textChanged.connect(self.apply_filters)
        self.f_os_modelo = QLineEdit()
        self.f_os_modelo.setPlaceholderText("🔍  Modelo...")
        self.f_os_modelo.textChanged.connect(self.apply_filters)
        self.btn_os_setor = QPushButton("Setor: Todos  ▾")
        self.btn_os_setor.setStyleSheet(_filter_btn_qss)
        self.btn_os_setor.clicked.connect(self._open_os_setor_picker)
        filters_os1.addWidget(self.f_os_id, 2)
        filters_os1.addWidget(self.f_os_modelo, 2)
        filters_os1.addWidget(self.btn_os_setor, 2)
        os_vbox.addLayout(filters_os1)

        filters_os2 = QHBoxLayout()
        filters_os2.setSpacing(8)
        self.f_os_desc = QLineEdit()
        self.f_os_desc.setPlaceholderText("🔍  Descrição da OS (ex: Calibração, Preventiva)...")
        self.f_os_desc.textChanged.connect(self.apply_filters)
        self.f_os_min_cost = QSpinBox()
        self.f_os_min_cost.setRange(0, 1000000)
        self.f_os_min_cost.setPrefix("Custo mín: R$ ")
        self.f_os_min_cost.setMinimumWidth(190)
        self.f_os_min_cost.valueChanged.connect(self.apply_filters)
        filters_os2.addWidget(self.f_os_desc, 3)
        filters_os2.addWidget(self.f_os_min_cost, 2)
        os_vbox.addLayout(filters_os2)

        self.os_table = QTableWidget()
        self.os_table.setColumnCount(6)
        self.os_table.setHorizontalHeaderLabels(["ID Equip.", "Modelo", "Setor", "Data", "Custo", "Descrição"])
        self.os_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.os_table.setMinimumHeight(260)
        self.os_table.setAlternatingRowColors(True)
        self.os_table.setSortingEnabled(True)
        self.os_table.setSelectionBehavior(QTableWidget.SelectRows)
        os_vbox.addWidget(self.os_table)

        os_page_bar = QHBoxLayout()
        os_page_bar.setSpacing(6)
        self.lbl_os_count = QLabel("0 ordens de serviço")
        self.lbl_os_count.setStyleSheet("color: #3D5A78; font-size: 11px; border: none; background: transparent;")
        self.btn_os_prev = QPushButton("←")
        self.btn_os_prev.setFixedSize(32, 26)
        self.btn_os_prev.setStyleSheet(_page_btn_qss)
        self.btn_os_prev.clicked.connect(lambda: self._goto_os_page(self._os_page - 1))
        self.lbl_os_page = QLabel("Pág. 1 de 1")
        self.lbl_os_page.setStyleSheet("color: #5A8AB8; font-size: 11px; border: none; background: transparent;")
        self.lbl_os_page.setAlignment(Qt.AlignCenter)
        self.lbl_os_page.setFixedWidth(90)
        self.btn_os_next = QPushButton("→")
        self.btn_os_next.setFixedSize(32, 26)
        self.btn_os_next.setStyleSheet(_page_btn_qss)
        self.btn_os_next.clicked.connect(lambda: self._goto_os_page(self._os_page + 1))
        os_page_bar.addWidget(self.lbl_os_count)
        os_page_bar.addStretch()
        os_page_bar.addWidget(self.btn_os_prev)
        os_page_bar.addWidget(self.lbl_os_page)
        os_page_bar.addWidget(self.btn_os_next)
        os_vbox.addLayout(os_page_bar)

        self.data_layout.addWidget(os_frame)
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
        # ── Equipment ─────────────────────────────────────────────────
        filtered_eq = self.equipment_data
        if self.f_modelo.text():
            t = self.f_modelo.text().lower()
            filtered_eq = [i for i in filtered_eq
                           if t in i["modelo"].lower() or t in i.get("identificador", "").lower()]
        eq_setores = getattr(self, '_eq_setores_filter', [])
        if eq_setores:
            filtered_eq = [i for i in filtered_eq if i.get("setor") in eq_setores]
        CRIT_MAP = {"● Baixa": 1, "●● Média": 2, "●●● Alta": 3}
        crit_text = self.f_crit.currentText() if hasattr(self, 'f_crit') else ""
        if crit_text in CRIT_MAP:
            filtered_eq = [i for i in filtered_eq if i.get("criticidade") == CRIT_MAP[crit_text]]
        status_text = self.f_status.currentText() if hasattr(self, 'f_status') else "Todos status"
        if status_text != "Todos status":
            filtered_eq = [i for i in filtered_eq if i.get("status") == status_text]

        self._filtered_eq_cache = filtered_eq
        self._eq_page = 0
        self._render_eq_page()

        # ── OS ────────────────────────────────────────────────────────
        filtered_os = self._all_os_flat
        if self.f_os_id.text():
            filtered_os = [i for i in filtered_os if self.f_os_id.text().lower() in i["id"].lower()]
        if hasattr(self, 'f_os_modelo') and self.f_os_modelo.text():
            t = self.f_os_modelo.text().lower()
            filtered_os = [i for i in filtered_os if t in i["modelo"].lower()]
        os_setores = getattr(self, '_os_setores_filter', [])
        if os_setores:
            filtered_os = [i for i in filtered_os if i.get("setor") in os_setores]
        if self.f_os_min_cost.value() > 0:
            filtered_os = [i for i in filtered_os if i["custo"] >= self.f_os_min_cost.value()]
        if hasattr(self, 'f_os_desc') and self.f_os_desc.text():
            t = self.f_os_desc.text().lower()
            filtered_os = [i for i in filtered_os if t in i["desc"].lower()]

        self._filtered_os_cache = filtered_os
        self._os_page = 0
        self._render_os_page()

    # ── Sector picker (reusável) ────────────────────────────────────────

    def _open_sector_picker_dialog(self, current_selected, all_setores, title="Filtrar por Setor"):
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setMinimumWidth(420)
        dialog.setMinimumHeight(480)
        dialog.setStyleSheet("QDialog { background-color: #060D18; } QLabel { color: #E2EDF8; }")

        lay = QVBoxLayout(dialog)
        lay.setContentsMargins(22, 20, 22, 18)
        lay.setSpacing(12)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-size: 16px; font-weight: 800; color: #F0F6FF;")
        lay.addWidget(lbl_title)

        search = QLineEdit()
        search.setPlaceholderText("🔍  Pesquisar setor...")
        search.setStyleSheet("QLineEdit { font-size: 13px; padding: 9px 12px; }")
        lay.addWidget(search)

        bulk_lay = QHBoxLayout()
        bulk_lay.setSpacing(8)
        _bulk_btn = "QPushButton { background: #0D1E35; color: #7BA8D8; border: 1px solid #1E3A5F; font-size: 12px; padding: 6px 14px; border-radius: 5px; } QPushButton:hover { background: #122038; color: #E2EDF8; }"
        btn_all = QPushButton("Marcar todos")
        btn_all.setStyleSheet(_bulk_btn)
        btn_none = QPushButton("Desmarcar todos")
        btn_none.setStyleSheet(_bulk_btn)
        bulk_lay.addWidget(btn_all)
        bulk_lay.addWidget(btn_none)
        bulk_lay.addStretch()
        lay.addLayout(bulk_lay)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: 1px solid #1A2D45; border-radius: 8px; background: #0A1628; }")
        sc_content = QWidget()
        sc_lay = QVBoxLayout(sc_content)
        sc_lay.setContentsMargins(8, 8, 8, 8)
        sc_lay.setSpacing(2)

        selected_first = [s for s in all_setores if s in current_selected]
        rest = [s for s in all_setores if s not in current_selected]
        checkboxes = []
        for s in selected_first + rest:
            cb = QCheckBox(s)
            cb.setStyleSheet("QCheckBox { color: #C4D8EE; padding: 7px 10px; font-size: 13px; border-radius: 5px; } QCheckBox:hover { background: #0D1E35; }")
            cb.setChecked(s in current_selected)
            sc_lay.addWidget(cb)
            checkboxes.append((s, cb))
        sc_lay.addStretch()
        scroll.setWidget(sc_content)
        lay.addWidget(scroll)

        search.textChanged.connect(lambda t: [cb.setVisible(not t or t.lower() in s.lower()) for s, cb in checkboxes])
        btn_all.clicked.connect(lambda: [cb.setChecked(True) for s, cb in checkboxes if cb.isVisible()])
        btn_none.clicked.connect(lambda: [cb.setChecked(False) for s, cb in checkboxes if cb.isVisible()])

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setStyleSheet("QPushButton { background: #0D1E35; color: #5A8AB8; border: 1px solid #1A2D45; padding: 10px 20px; border-radius: 6px; } QPushButton:hover { background: #122038; }")
        btn_cancel.clicked.connect(dialog.reject)
        btn_ok = QPushButton("Aplicar")
        btn_ok.setStyleSheet("QPushButton { background: #1D4ED8; color: white; padding: 10px 24px; border-radius: 6px; font-weight: 700; border: none; } QPushButton:hover { background: #2563EB; }")
        btn_ok.clicked.connect(dialog.accept)
        btn_ok.setDefault(True)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_ok)
        lay.addLayout(btn_row)

        if dialog.exec() != QDialog.Accepted:
            return None
        return [s for s, cb in checkboxes if cb.isChecked()]

    def _open_eq_setor_picker(self):
        all_setores = sorted(list(set(i.get("setor", "") for i in self.equipment_data if i.get("setor"))))
        result = self._open_sector_picker_dialog(self._eq_setores_filter, all_setores, "Filtrar Equipamentos por Setor")
        if result is not None:
            self._eq_setores_filter = result
            self._update_eq_setor_btn_label()
            self.apply_filters()

    def _open_os_setor_picker(self):
        all_setores = sorted(list(set(i.get("setor", "") for i in self._all_os_flat if i.get("setor"))))
        result = self._open_sector_picker_dialog(self._os_setores_filter, all_setores, "Filtrar OS por Setor")
        if result is not None:
            self._os_setores_filter = result
            self._update_os_setor_btn_label()
            self.apply_filters()

    def _update_eq_setor_btn_label(self):
        if not hasattr(self, 'btn_eq_setor'): return
        n = len(self._eq_setores_filter)
        self.btn_eq_setor.setText(f"Setor: {n} selecionado(s)  ▾" if n else "Setor: Todos  ▾")

    def _update_os_setor_btn_label(self):
        if not hasattr(self, 'btn_os_setor'): return
        n = len(self._os_setores_filter)
        self.btn_os_setor.setText(f"Setor: {n} selecionado(s)  ▾" if n else "Setor: Todos  ▾")

    # ── Pagination helpers ──────────────────────────────────────────────

    def _render_eq_page(self):
        if not hasattr(self, 'equip_table'): return
        total = len(self._filtered_eq_cache)
        total_pages = max(1, (total + self._eq_page_size - 1) // self._eq_page_size)
        self._eq_page = max(0, min(self._eq_page, total_pages - 1))
        start = self._eq_page * self._eq_page_size
        page_items = self._filtered_eq_cache[start:start + self._eq_page_size]

        STATUS_COLORS = {"Em uso": "#34D399", "Inoperante": "#F87171", "Disponível": "#FBBF24"}
        CRIT_LABELS = {1: "● Baixa", 2: "●● Média", 3: "●●● Alta"}
        CRIT_COLORS = {1: "#4A6A8A", 2: "#FBBF24", 3: "#F87171"}

        self.equip_table.setSortingEnabled(False)
        self.equip_table.setRowCount(len(page_items))
        for r, item in enumerate(page_items):
            self.equip_table.setItem(r, 0, QTableWidgetItem(item.get("identificador", "N/A")))
            self.equip_table.setItem(r, 1, QTableWidgetItem(item["modelo"]))
            self.equip_table.setItem(r, 2, QTableWidgetItem(item["setor"]))
            crit_val = item["criticidade"]
            ci = QTableWidgetItem(CRIT_LABELS.get(crit_val, str(crit_val)))
            ci.setForeground(QColor(CRIT_COLORS.get(crit_val, "#E2EDF8")))
            self.equip_table.setItem(r, 3, ci)
            self.equip_table.setItem(r, 4, QTableWidgetItem(item["data_aquisicao"]))
            status = item["status"]
            si = QTableWidgetItem(status)
            si.setForeground(QColor(STATUS_COLORS.get(status, "#C4D8EE")))
            self.equip_table.setItem(r, 5, si)
        self.equip_table.setSortingEnabled(True)

        self.lbl_equip_count.setText(f"{total} equipamento(s)")
        self.lbl_eq_page.setText(f"Pág. {self._eq_page + 1} de {total_pages}")
        self.btn_eq_prev.setEnabled(self._eq_page > 0)
        self.btn_eq_next.setEnabled(self._eq_page < total_pages - 1)

    def _render_os_page(self):
        if not hasattr(self, 'os_table'): return
        total = len(self._filtered_os_cache)
        total_pages = max(1, (total + self._os_page_size - 1) // self._os_page_size)
        self._os_page = max(0, min(self._os_page, total_pages - 1))
        start = self._os_page * self._os_page_size
        page_items = self._filtered_os_cache[start:start + self._os_page_size]

        self.os_table.setSortingEnabled(False)
        self.os_table.setRowCount(len(page_items))
        for r, item in enumerate(page_items):
            self.os_table.setItem(r, 0, QTableWidgetItem(item["id"]))
            self.os_table.setItem(r, 1, QTableWidgetItem(item["modelo"]))
            self.os_table.setItem(r, 2, QTableWidgetItem(item.get("setor", "")))
            self.os_table.setItem(r, 3, QTableWidgetItem(item["data"]))
            cost_item = QTableWidgetItem(f"R$ {item['custo']:,.2f}")
            cost_item.setForeground(QColor("#34D399"))
            self.os_table.setItem(r, 4, cost_item)
            self.os_table.setItem(r, 5, QTableWidgetItem(item["desc"]))
        self.os_table.setSortingEnabled(True)

        self.lbl_os_count.setText(f"{total} ordem(ns) de serviço")
        self.lbl_os_page.setText(f"Pág. {self._os_page + 1} de {total_pages}")
        self.btn_os_prev.setEnabled(self._os_page > 0)
        self.btn_os_next.setEnabled(self._os_page < total_pages - 1)

    def _goto_eq_page(self, page):
        total_pages = max(1, (len(self._filtered_eq_cache) + self._eq_page_size - 1) // self._eq_page_size)
        self._eq_page = max(0, min(page, total_pages - 1))
        self._render_eq_page()

    def _goto_os_page(self, page):
        total_pages = max(1, (len(self._filtered_os_cache) + self._os_page_size - 1) // self._os_page_size)
        self._os_page = max(0, min(page, total_pages - 1))
        self._render_os_page()

    # ── Home page (tela inicial com análises salvas) ────────────────────

    def setup_home_page(self):
        page = QWidget()
        page.setStyleSheet("QWidget { background-color: #060D18; }")
        outer = QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

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

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        content = QWidget()
        content_lay = QVBoxLayout(content)
        content_lay.setContentsMargins(60, 40, 60, 40)
        content_lay.setSpacing(28)
        content_lay.setAlignment(Qt.AlignTop)

        # Hero card
        hero = QFrame()
        hero.setStyleSheet("""
            QFrame { background: #0A1628;
                     border: 1px solid #1A2D45; border-radius: 14px; }
        """)
        top_bar = QFrame()
        top_bar.setFixedHeight(4)
        top_bar.setStyleSheet("background: #1D4ED8; border-radius: 14px 14px 0 0; border: none;")
        hero_inner = QHBoxLayout()
        hero_inner.setContentsMargins(32, 24, 32, 28)
        hero_text = QVBoxLayout()
        hero_text.setSpacing(6)
        lbl_welcome = QLabel("Bem-vindo ao Dashboard")
        lbl_welcome.setStyleSheet("font-size: 26px; font-weight: 800; color: #F0F6FF; border: none;")
        lbl_sub = QLabel("Carregue uma análise salva ou inicie uma nova análise com seus dados.")
        lbl_sub.setStyleSheet("font-size: 13px; color: #3D5A78; border: none;")
        hero_text.addWidget(lbl_welcome)
        hero_text.addWidget(lbl_sub)
        hero_inner.addLayout(hero_text, 1)
        btn_nova = QPushButton("＋  Nova Análise")
        btn_nova.setFixedSize(190, 48)
        btn_nova.setStyleSheet("""
            QPushButton { background: #1D4ED8;
                          color: white; border-radius: 8px; font-size: 14px; font-weight: 700; border: none; }
            QPushButton:hover { background: #2563EB; }
        """)
        btn_nova.clicked.connect(lambda: self.root_stack.setCurrentIndex(1))
        hero_inner.addWidget(btn_nova, 0, Qt.AlignRight | Qt.AlignVCenter)
        hero_vbox = QVBoxLayout(hero)
        hero_vbox.setContentsMargins(0, 0, 0, 0)
        hero_vbox.setSpacing(0)
        hero_vbox.addWidget(top_bar)
        hero_vbox.addLayout(hero_inner)
        content_lay.addWidget(hero)

        # Saved analyses header
        saved_header = QHBoxLayout()
        lbl_saved = QLabel("ANÁLISES SALVAS")
        lbl_saved.setStyleSheet("font-size: 10px; font-weight: bold; color: #2A4A6E; letter-spacing: 1px; border: none;")
        saved_header.addWidget(lbl_saved)
        saved_header.addStretch()
        content_lay.addLayout(saved_header)

        self.saved_analyses_container = QWidget()
        self.saved_analyses_layout = QVBoxLayout(self.saved_analyses_container)
        self.saved_analyses_layout.setContentsMargins(0, 0, 0, 0)
        self.saved_analyses_layout.setSpacing(10)
        content_lay.addWidget(self.saved_analyses_container)
        content_lay.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll, 1)
        self.root_stack.addWidget(page)
        self.populate_saved_analyses()

    def _load_saved_analyses(self):
        if os.path.exists(self.saved_analyses_file):
            try:
                with open(self.saved_analyses_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Erro ao ler análises salvas: {e}")
        return []

    def populate_saved_analyses(self):
        while self.saved_analyses_layout.count():
            item = self.saved_analyses_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        analyses = self._load_saved_analyses()
        if not analyses:
            lbl_empty = QLabel("Nenhuma análise salva ainda. Clique em \"Nova Análise\" para começar.")
            lbl_empty.setStyleSheet("color: #2D4A68; font-size: 13px; font-style: italic; padding: 24px; border: none;")
            lbl_empty.setAlignment(Qt.AlignCenter)
            self.saved_analyses_layout.addWidget(lbl_empty)
        else:
            for analysis in reversed(analyses):
                card = self._make_saved_analysis_item(analysis)
                self.saved_analyses_layout.addWidget(card)

    def _make_saved_analysis_item(self, analysis):
        card = QFrame()
        card.setStyleSheet("""
            QFrame { background: #0A1628; border: 1px solid #1A2D45; border-radius: 10px; }
            QFrame:hover { border-color: #2A4A6E; }
        """)
        lay = QHBoxLayout(card)
        lay.setContentsMargins(20, 16, 16, 16)
        lay.setSpacing(16)

        lbl_icon = QLabel("📊")
        lbl_icon.setStyleSheet("font-size: 24px; border: none; background: transparent;")
        lbl_icon.setFixedWidth(34)
        lay.addWidget(lbl_icon)

        info_lay = QVBoxLayout()
        info_lay.setSpacing(4)

        lbl_name = QLabel(analysis.get("name", "Sem nome"))
        lbl_name.setStyleSheet("font-size: 15px; font-weight: 700; color: #E2EDF8; border: none; background: transparent;")
        info_lay.addWidget(lbl_name)

        files = analysis.get("files", {})
        file_names = [os.path.basename(v) for v in files.values() if v]
        date_str = analysis.get("date_saved", "")
        meta_text = f"Salvo em {date_str}"
        if file_names:
            meta_text += f"  ·  {', '.join(file_names[:3])}{'...' if len(file_names) > 3 else ''}"
        lbl_meta = QLabel(meta_text)
        lbl_meta.setStyleSheet("font-size: 11px; color: #2D4A68; border: none; background: transparent;")
        info_lay.addWidget(lbl_meta)

        setores = analysis.get("filters", {}).get("selected_setores", [])
        if setores:
            setores_text = f"Setores: {', '.join(setores[:3])}{'...' if len(setores) > 3 else ''}"
            lbl_filters = QLabel(setores_text)
            lbl_filters.setStyleSheet("font-size: 11px; color: #3D5A78; border: none; background: transparent;")
            info_lay.addWidget(lbl_filters)

        lay.addLayout(info_lay, 1)

        btn_play = QPushButton()
        btn_play.setFixedSize(40, 40)
        btn_play.setToolTip("Carregar análise")
        btn_play.setIcon(QIcon(self._action_icon("play", 18, "#60A5FA")))
        btn_play.setIconSize(QSize(18, 18))
        btn_play.setStyleSheet("""
            QPushButton { background: #0D1E35; border: 1px solid #1E3A5F; border-radius: 20px; }
            QPushButton:hover { background: #1D4ED8; border-color: #1D4ED8; }
        """)
        btn_play.clicked.connect(lambda checked, a=analysis: self.load_saved_analysis(a))
        lay.addWidget(btn_play)

        btn_del = QPushButton()
        btn_del.setFixedSize(40, 40)
        btn_del.setToolTip("Excluir análise")
        btn_del.setIcon(QIcon(self._action_icon("close", 18, "#7E9BB8")))
        btn_del.setIconSize(QSize(18, 18))
        btn_del.setStyleSheet("""
            QPushButton { background: #0D1E35; border: 1px solid #1E3A5F; border-radius: 20px; }
            QPushButton:hover { background: #EF4444; border-color: #EF4444; }
        """)
        btn_del.clicked.connect(lambda checked, a=analysis: self.delete_saved_analysis(a))
        lay.addWidget(btn_del)

        return card

    def save_analysis(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Salvar Análise")
        dialog.setMinimumWidth(420)
        dialog.setStyleSheet("QDialog { background-color: #0A1628; }")

        lay = QVBoxLayout(dialog)
        lay.setContentsMargins(28, 28, 28, 24)
        lay.setSpacing(18)

        lbl_title = QLabel("Salvar Análise")
        lbl_title.setStyleSheet("font-size: 18px; font-weight: 800; color: #F0F6FF;")
        lbl_sub = QLabel("Dê um nome para identificar esta análise posteriormente.")
        lbl_sub.setStyleSheet("font-size: 12px; color: #3D5A78;")
        lay.addWidget(lbl_title)
        lay.addWidget(lbl_sub)

        name_input = QLineEdit()
        name_input.setPlaceholderText(f"Ex: Análise UTI Adulto — {datetime.now().strftime('%B %Y')}")
        name_input.setStyleSheet("QLineEdit { font-size: 14px; padding: 12px 14px; border-radius: 8px; }")
        lay.addWidget(name_input)

        btn_lay = QHBoxLayout()
        btn_lay.setSpacing(10)
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setStyleSheet("""
            QPushButton { background: #0D1E35; color: #5A8AB8; border: 1px solid #1A2D45;
                          padding: 10px 20px; border-radius: 6px; font-weight: 600; }
            QPushButton:hover { background: #122038; color: #C4D8EE; }
        """)
        btn_cancel.clicked.connect(dialog.reject)
        btn_ok = QPushButton("Salvar")
        btn_ok.setStyleSheet("""
            QPushButton { background: #1D4ED8; color: white; padding: 10px 24px;
                          border-radius: 6px; font-weight: 700; border: none; }
            QPushButton:hover { background: #2563EB; }
        """)
        btn_ok.clicked.connect(dialog.accept)
        btn_ok.setDefault(True)
        btn_lay.addStretch()
        btn_lay.addWidget(btn_cancel)
        btn_lay.addWidget(btn_ok)
        lay.addLayout(btn_lay)

        if dialog.exec() != QDialog.Accepted:
            return

        name = name_input.text().strip() or f"Análise {datetime.now().strftime('%d/%m/%Y %H:%M')}"

        analyses = self._load_saved_analyses()
        new_entry = {
            "id": str(uuid.uuid4()),
            "name": name,
            "date_saved": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "files": {
                "equip": self.equip_path.text(),
                "crit": self.crit_path.text(),
                "os_antiga": self.os_antiga_path.text(),
                "os_atual": self.os_atual_path.text(),
            },
            "filters": {
                "selected_setores": list(self.selected_setores),
                "age_threshold": self.age_threshold.value(),
                "active_years": list(self.active_years),
                "cb_excluir_custo_zero": self._excluir_custo_zero,
                "peso_idade": self._peso_idade,
                "peso_criticidade": self._peso_criticidade,
                "peso_custo": self._peso_custo,
                "f_modelo": self.f_modelo.text(),
                "f_setor": self.f_setor.currentText(),
                "eq_setores_filter": list(getattr(self, '_eq_setores_filter', [])),
                "os_setores_filter": list(getattr(self, '_os_setores_filter', [])),
                "f_crit": self.f_crit.currentText() if hasattr(self, 'f_crit') else "Todas criticidades",
                "f_status": self.f_status.currentText() if hasattr(self, 'f_status') else "Todos status",
                "f_os_id": self.f_os_id.text(),
                "f_os_modelo": self.f_os_modelo.text() if hasattr(self, 'f_os_modelo') else "",
                "f_os_desc": self.f_os_desc.text() if hasattr(self, 'f_os_desc') else "",
                "f_os_min_cost": self.f_os_min_cost.value(),
            }
        }
        analyses.append(new_entry)
        os.makedirs(os.path.dirname(self.saved_analyses_file), exist_ok=True)
        with open(self.saved_analyses_file, 'w', encoding='utf-8') as f:
            json.dump(analyses, f, indent=4, ensure_ascii=False)

        QMessageBox.information(self, "Salvo", f"Análise \"{name}\" salva com sucesso!")

    def load_saved_analysis(self, analysis):
        files = analysis.get("files", {})
        self.equip_path.setText(files.get("equip", ""))
        self.crit_path.setText(files.get("crit", ""))
        self.os_antiga_path.setText(files.get("os_antiga", ""))
        self.os_atual_path.setText(files.get("os_atual", ""))
        self._pending_filters = analysis.get("filters")
        self._auto_confirm_next_load = True
        self.load_data()

    def delete_saved_analysis(self, analysis):
        reply = QMessageBox.question(
            self, "Excluir Análise",
            f"Deseja excluir a análise \"{analysis.get('name', '')}\"?\nEsta ação não pode ser desfeita.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            analyses = self._load_saved_analyses()
            analyses = [a for a in analyses if a.get("id") != analysis.get("id")]
            with open(self.saved_analyses_file, 'w', encoding='utf-8') as f:
                json.dump(analyses, f, indent=4, ensure_ascii=False)
            self.populate_saved_analyses()

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_THEME_QSS)
    window = HospitalDashboard()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
