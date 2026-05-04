import sys
import csv
import random
from datetime import date, datetime, timedelta
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QLineEdit, QComboBox, QPushButton, QCheckBox, QFormLayout, 
    QGroupBox, QScrollArea, QFileDialog, QMessageBox, QDialog, QDateEdit, QSpinBox
)
from PySide6.QtCore import Qt, QDateTime, QEvent, QDate
from PySide6.QtGui import QColor, QPainter, QFont
from PySide6.QtCharts import QChart, QChartView, QPieSeries, QLineSeries, QDateTimeAxis, QValueAxis, QScatterSeries, QBarSeries, QBarSet, QBarCategoryAxis

def generate_mock_os(count, start_date=date(2023, 1, 1)):
    os_list = []
    current_date = start_date
    for _ in range(count):
        interval = random.randint(30, 90)
        current_date += timedelta(days=interval)
        if current_date > date.today() + timedelta(days=30): break
        os_list.append({
            "data": current_date.strftime("%Y-%m-%d"),
            "custo": random.uniform(500, 15000),
            "desc": random.choice(["Troca de peças", "Calibração", "Preventiva", "Corretiva", "Limpeza"])
        })
    return sorted(os_list, key=lambda x: x["data"])

MOCK_EQUIPMENT = [
    {"modelo": "MRI Signa HDx", "setor": "Radiologia", "criticidade": 3, "data_aquisicao": "2010-05-15", "status": "Inoperante", "valor": 1200000, "score": 95, "os": generate_mock_os(15)},
    {"modelo": "Ventilador PB 840", "setor": "UTI Adulto", "criticidade": 3, "data_aquisicao": "2012-03-10", "status": "Em uso", "valor": 45000, "score": 88, "os": generate_mock_os(12)},
    {"modelo": "Raio-X Digital", "setor": "Emergência", "criticidade": 2, "data_aquisicao": "2011-08-20", "status": "Inoperante", "valor": 250000, "score": 82, "os": generate_mock_os(10)},
    {"modelo": "Bomba Alaris", "setor": "Enfermaria", "criticidade": 1, "data_aquisicao": "2015-11-05", "status": "Disponível", "valor": 8000, "score": 35, "os": generate_mock_os(5)},
    {"modelo": "Monitor V24", "setor": "UTI Cardio", "criticidade": 2, "data_aquisicao": "2018-02-28", "status": "Em uso", "valor": 15000, "score": 42, "os": generate_mock_os(8)},
    {"modelo": "Lifepak 15", "setor": "Emergência", "criticidade": 3, "data_aquisicao": "2013-06-15", "status": "Disponível", "valor": 35000, "score": 75, "os": generate_mock_os(10)},
    {"modelo": "Tomógrafo CT660", "setor": "Radiologia", "criticidade": 3, "data_aquisicao": "2009-12-01", "status": "Em uso", "valor": 1800000, "score": 78, "os": generate_mock_os(20)},
    {"modelo": "Ultrassom Voluson", "setor": "Obstetrícia", "criticidade": 2, "data_aquisicao": "2020-04-10", "status": "Em uso", "valor": 400000, "score": 25, "os": generate_mock_os(6)},
    {"modelo": "Autoclave Sterivap", "setor": "CME", "criticidade": 2, "data_aquisicao": "2014-09-22", "status": "Disponível", "valor": 120000, "score": 55, "os": generate_mock_os(9)},
    {"modelo": "Foco LED", "setor": "Bloco Cirúrgico", "criticidade": 2, "data_aquisicao": "2012-10-15", "status": "Em uso", "valor": 60000, "score": 62, "os": generate_mock_os(7)},
]

DARK_THEME_QSS = """
QMainWindow, QWidget { background-color: #0F172A; color: #F8FAFC; font-family: 'Inter', 'Segoe UI', Arial; }
QGroupBox { border: 1px solid #1E293B; border-radius: 6px; margin-top: 15px; font-weight: bold; padding-top: 25px; }
QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 5px; left: 10px; color: #94A3B8; }
QLineEdit, QComboBox, QDateEdit, QSpinBox { background-color: #1E293B; border: 1px solid #334155; border-radius: 4px; padding: 6px; color: #F8FAFC; }
QPushButton { background-color: #2563EB; color: white; border-radius: 4px; padding: 8px 16px; font-weight: 600; border: none; }
QPushButton:hover { background-color: #3B82F6; }
QPushButton#ExportBtn { background-color: #1E293B; color: #94A3B8; font-size: 10px; padding: 2px 8px; border: 1px solid #334155; }
QPushButton#ExportBtn:hover { background-color: #334155; color: white; }
QTableWidget { background-color: #1E293B; gridline-color: #334155; border: 1px solid #334155; border-radius: 4px; }
QHeaderView::section { background-color: #334155; color: #F8FAFC; padding: 6px; border: none; font-weight: bold; }
"""

class HospitalDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Gestão de Equipamentos")
        self.resize(1400, 980)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        self.setCentralWidget(scroll)
        container = QWidget()
        self.main_layout = QVBoxLayout(container)
        self.main_layout.setContentsMargins(30, 30, 30, 30)
        self.main_layout.setSpacing(20)
        scroll.setWidget(container)
        
        header_layout = QHBoxLayout()
        header = QLabel("Dashboard de Engenharia Clínica")
        header.setStyleSheet("font-size: 26px; font-weight: 700; color: #F8FAFC;")
        header_layout.addWidget(header)
        header_layout.addStretch()
        self.main_layout.addLayout(header_layout)
        
        if not hasattr(self, '_overlays'): self._overlays = []
        
        self.setup_insights_row()
        self.setup_risk_row()
        self.setup_list_section()

    def setup_insights_row(self):
        layout = QHBoxLayout()
        layout.setSpacing(25)
        
        # Age Distribution with Overlay Filter
        age_group = QGroupBox("Distribuição por Idade")
        age_vbox = QVBoxLayout(age_group)
        self.age_donut_view = QChartView()
        self.age_donut_view.setRenderHint(QPainter.Antialiasing)
        self.age_donut_view.setStyleSheet("background: transparent;")
        self.age_donut_view.setFixedHeight(230)
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
        self.update_age_donut()
        layout.addWidget(age_group, 1)
        
        # OS History with Overlay Filter
        chart_container = QGroupBox("Histórico de Emissão de OS")
        chart_vbox = QVBoxLayout(chart_container)
        self.global_chart_view = QChartView()
        self.global_chart_view.setRenderHint(QPainter.Antialiasing)
        self.global_chart_view.setStyleSheet("background: transparent;")
        self.global_chart_view.setFixedHeight(230)
        chart_vbox.addWidget(self.global_chart_view)
        
        filter_widget = QWidget(chart_container)
        filter_layout = QHBoxLayout(filter_widget)
        filter_layout.setContentsMargins(5, 0, 5, 0); filter_layout.setSpacing(8)
        self.chart_start_date = QDateEdit(QDate(2023, 1, 1)); self.chart_start_date.setCalendarPopup(True)
        self.chart_start_date.setFixedWidth(100); self.chart_start_date.setStyleSheet("font-size: 10px;")
        self.chart_start_date.dateChanged.connect(self.update_global_chart)
        self.chart_end_date = QDateEdit(QDate.currentDate()); self.chart_end_date.setCalendarPopup(True)
        self.chart_end_date.setFixedWidth(100); self.chart_end_date.setStyleSheet("font-size: 10px;")
        self.chart_end_date.dateChanged.connect(self.update_global_chart)
        filter_layout.addWidget(QLabel("De:")); filter_layout.addWidget(self.chart_start_date)
        filter_layout.addWidget(QLabel("Até:")); filter_layout.addWidget(self.chart_end_date)
        filter_widget.setFixedWidth(280)
        
        self._overlays.append((chart_container, filter_widget))
        chart_container.installEventFilter(self)
        self.update_global_chart()
        layout.addWidget(chart_container, 2)
        
        self.main_layout.addLayout(layout)

    def setup_risk_row(self):
        layout = QHBoxLayout()
        layout.setSpacing(25)
        risk_group = QGroupBox("Risco de Quebra Iminente (Dias p/ Falha Estimada)")
        risk_vbox = QVBoxLayout(risk_group)
        self.risk_chart_view = QChartView()
        self.risk_chart_view.setRenderHint(QPainter.Antialiasing)
        self.risk_chart_view.setStyleSheet("background: transparent;")
        self.risk_chart_view.setFixedHeight(250)
        self.update_risk_chart()
        risk_vbox.addWidget(self.risk_chart_view)
        layout.addWidget(risk_group, 2)
        top5_group = QGroupBox("Prioridades de Substituição (Score Risco)")
        top5_layout = QVBoxLayout(top5_group)
        self.top5_table = QTableWidget()
        self.top5_table.setColumnCount(3)
        self.top5_table.setHorizontalHeaderLabels(["Modelo", "Setor", "Score"])
        self.top5_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.top5_table.setFixedHeight(200); self.top5_table.verticalHeader().setVisible(False)
        self.populate_top5()
        top5_layout.addWidget(self.top5_table)
        layout.addWidget(top5_group, 1)
        self.main_layout.addLayout(layout)

    def update_age_donut(self):
        threshold = self.age_threshold.value()
        over = sum(1 for i in MOCK_EQUIPMENT if (date.today().year - int(i["data_aquisicao"].split("-")[0])) >= threshold)
        under = len(MOCK_EQUIPMENT) - over
        series = QPieSeries(); series.setHoleSize(0.6)
        s1 = series.append(f"≥ {threshold} Anos ({over})", over); s1.setBrush(QColor("#475569"))
        s2 = series.append(f"< {threshold} Anos ({under})", under); s2.setBrush(QColor("#2563EB"))
        for slice in series.slices(): slice.setLabelVisible(True); slice.setLabelColor(QColor("#CBD5E1"))
        chart = QChart(); chart.addSeries(series); chart.setTitle(f"Corte: {threshold} anos")
        chart.setBackgroundBrush(QColor("#1E293B")); chart.setTitleBrush(QColor("#F8FAFC"))
        chart.legend().setAlignment(Qt.AlignBottom); chart.legend().setLabelColor(QColor("#F8FAFC"))
        self.age_donut_view.setChart(chart)

    def update_risk_chart(self):
        risk_data = []
        for equip in MOCK_EQUIPMENT:
            if len(equip["os"]) < 2: continue
            dates = [datetime.strptime(os["data"], "%Y-%m-%d") for os in equip["os"]]
            intervals = [(dates[i] - dates[i-1]).days for i in range(1, len(dates))]
            mtbf = sum(intervals) / len(intervals)
            last_os = max(dates)
            days_since_last = (datetime.now() - last_os).days
            days_to_next = max(0, int(mtbf - days_since_last))
            if days_to_next < 60: risk_data.append((equip["modelo"], days_to_next))
        risk_data = sorted(risk_data, key=lambda x: x[1])[:7]
        bar_set = QBarSet("Dias para falha"); bar_set.setBrush(QColor("#EF4444"))
        categories = []
        for modelo, days in risk_data: bar_set.append(days); categories.append(modelo.split(" ")[0])
        series = QBarSeries(); series.append(bar_set)
        chart = QChart(); chart.addSeries(series); chart.setTitle("Previsão de Quebra (Próximos 60 dias)")
        chart.setBackgroundBrush(QColor("#1E293B")); chart.setTitleBrush(QColor("#F8FAFC"))
        axis_x = QBarCategoryAxis(); axis_x.append(categories); axis_x.setLabelsColor(QColor("#CBD5E1"))
        chart.addAxis(axis_x, Qt.AlignBottom); series.attachAxis(axis_x)
        axis_y = QValueAxis(); axis_y.setTitleText("Dias"); axis_y.setLabelsColor(QColor("#CBD5E1"))
        chart.addAxis(axis_y, Qt.AlignLeft); series.attachAxis(axis_y)
        self.risk_chart_view.setChart(chart)

    def update_global_chart(self):
        start_dt = self.chart_start_date.date().toPython(); end_dt = self.chart_end_date.date().toPython()
        os_counts = {}
        for equip in MOCK_EQUIPMENT:
            for os in equip["os"]:
                dt = datetime.strptime(os["data"], "%Y-%m-%d").date()
                if start_dt <= dt <= end_dt: key = dt.strftime("%Y-%m"); os_counts[key] = os_counts.get(key, 0) + 1
        series = QLineSeries(); series.setColor(QColor("#10B981")); series.setPointsVisible(True)
        sorted_keys = sorted(os_counts.keys())
        for key in sorted_keys:
            dt = datetime.strptime(key, "%Y-%m"); series.append(QDateTime(dt).toMSecsSinceEpoch(), os_counts[key])
        chart = QChart(); chart.addSeries(series); chart.setBackgroundBrush(QColor("#1E293B")); chart.setTitleBrush(QColor("#F8FAFC"))
        axis_x = QDateTimeAxis(); axis_x.setFormat("MMM yy"); axis_x.setLabelsColor(QColor("#CBD5E1"))
        chart.addAxis(axis_x, Qt.AlignBottom); series.attachAxis(axis_x)
        axis_y = QValueAxis(); axis_y.setLabelsColor(QColor("#CBD5E1")); axis_y.setLabelFormat("%d")
        max_val = max(os_counts.values()) if os_counts else 10
        axis_y.setRange(0, max_val + 2); chart.addAxis(axis_y, Qt.AlignLeft); series.attachAxis(axis_y)
        self.global_chart_view.setChart(chart)

    def populate_top5(self):
        sorted_items = sorted(MOCK_EQUIPMENT, key=lambda x: x["score"], reverse=True)[:5]
        self.top5_table.setRowCount(len(sorted_items))
        for i, item in enumerate(sorted_items):
            self.top5_table.setItem(i, 0, QTableWidgetItem(item["modelo"]))
            self.top5_table.setItem(i, 1, QTableWidgetItem(item["setor"]))
            score_item = QTableWidgetItem(str(item["score"]))
            score_item.setForeground(QColor("#CF6679") if item["score"] >= 80 else QColor("#FFB74D"))
            self.top5_table.setItem(i, 2, score_item)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Resize:
            if hasattr(self, '_overlays'):
                for gbox, widget in self._overlays:
                    if gbox == obj: widget.move(gbox.width() - widget.width() - 15, 0)
        return super().eventFilter(obj, event)

    def setup_list_section(self):
        group = QGroupBox("Gestão Detalhada de Ativos")
        layout = QVBoxLayout(group)
        filters = QHBoxLayout(); self.f_modelo = QLineEdit(); self.f_modelo.setPlaceholderText("Filtrar modelo...")
        self.f_modelo.textChanged.connect(self.apply_filters); self.f_setor = QComboBox()
        self.f_setor.addItems(["Todos Setores"] + sorted(list(set(i["setor"] for i in MOCK_EQUIPMENT))))
        self.f_setor.currentIndexChanged.connect(self.apply_filters)
        filters.addWidget(self.f_modelo); filters.addWidget(self.f_setor); layout.addLayout(filters)
        self.main_table = QTableWidget(); self.main_table.setColumnCount(5)
        self.main_table.setHorizontalHeaderLabels(["Modelo", "Setor", "Crit.", "Aquisição", "Status"])
        self.main_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.main_table.setFixedHeight(300); self.main_table.verticalHeader().setVisible(False)
        layout.addWidget(self.main_table); self.apply_filters(); self.main_layout.addWidget(group)

    def apply_filters(self):
        filtered = MOCK_EQUIPMENT
        if self.f_modelo.text(): filtered = [i for i in filtered if self.f_modelo.text().lower() in i["modelo"].lower()]
        if self.f_setor.currentText() != "Todos Setores": filtered = [i for i in filtered if i["setor"] == self.f_setor.currentText()]
        self.main_table.setRowCount(len(filtered))
        for r, item in enumerate(filtered):
            self.main_table.setItem(r, 0, QTableWidgetItem(item["modelo"])); self.main_table.setItem(r, 1, QTableWidgetItem(item["setor"]))
            self.main_table.setItem(r, 2, QTableWidgetItem(str(item["criticidade"]))); self.main_table.setItem(r, 3, QTableWidgetItem(item["data_aquisicao"]))
            self.main_table.setItem(r, 4, QTableWidgetItem(item["status"]))

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_THEME_QSS)
    window = HospitalDashboard()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
