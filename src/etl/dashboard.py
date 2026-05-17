import sys
import csv
import random
from datetime import date, datetime, timedelta
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QLineEdit, QComboBox, QPushButton, QCheckBox, QFormLayout, 
    QGroupBox, QScrollArea, QFileDialog, QMessageBox, QDialog, QDateEdit, QSpinBox,
    QGraphicsLineItem, QTabWidget, QStackedWidget
)
from PySide6.QtCore import Qt, QDateTime, QEvent, QDate
from PySide6.QtGui import QColor, QPainter, QFont, QPen
from PySide6.QtCharts import QChart, QChartView, QPieSeries, QLineSeries, QDateTimeAxis, QValueAxis, QScatterSeries, QBarSeries, QBarSet, QBarCategoryAxis, QHorizontalBarSeries

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

class HospitalDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Gestão de Equipamentos")
        self.resize(1400, 980)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        self.setCentralWidget(scroll)
        
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
        
        # Tabs in header
        self.btn_analysis = QPushButton("Análise")
        self.btn_data = QPushButton("Dados")
        tab_style = """
            QPushButton { padding: 8px 16px; border-radius: 6px; background: transparent; color: #94A3B8; font-weight: bold; font-size: 16px; }
            QPushButton:checked { background: #38BDF8; color: #0F172A; }
        """
        self.btn_analysis.setStyleSheet(tab_style); self.btn_data.setStyleSheet(tab_style)
        self.btn_analysis.setCheckable(True); self.btn_data.setCheckable(True)
        self.btn_analysis.setChecked(True)
        
        self.btn_analysis.clicked.connect(lambda: self.switch_tab(0))
        self.btn_data.clicked.connect(lambda: self.switch_tab(1))
        
        header_layout.addWidget(self.btn_analysis)
        header_layout.addWidget(self.btn_data)
        
        self.main_layout.addLayout(header_layout)
        
        self.active_years = set(range(2018, 2025))
        if not hasattr(self, '_overlays'): self._overlays = []
        
        self.tabs = QStackedWidget()
        self.main_layout.addWidget(self.tabs)
        
        self.analysis_tab = QWidget()
        self.analysis_layout = QVBoxLayout(self.analysis_tab)
        self.analysis_layout.setContentsMargins(0,0,0,0)
        self.analysis_layout.setSpacing(24)
        self.tabs.addWidget(self.analysis_tab)
        
        self.data_tab = QWidget()
        self.data_layout = QVBoxLayout(self.data_tab)
        self.data_layout.setContentsMargins(0,0,0,0)
        self.tabs.addWidget(self.data_tab)
        
        self.setup_kpi_row()
        self.setup_insights_row()
        self.setup_history_row()
        self.setup_cost_analysis_row()
        self.setup_list_section()

    def switch_tab(self, index):
        self.tabs.setCurrentIndex(index)
        self.btn_analysis.setChecked(index == 0)
        self.btn_data.setChecked(index == 1)

    def setup_kpi_row(self):
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(24)
        
        total_equip = len(MOCK_EQUIPMENT)
        total_os = sum(len(equip.get("os", [])) for equip in MOCK_EQUIPMENT)
        total_cost = sum(os_data.get("custo", 0) for equip in MOCK_EQUIPMENT for os_data in equip.get("os", []))
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
        kpi_layout.addWidget(create_kpi_card("Total de OS Emitidas", total_os), 1)
        kpi_layout.addWidget(create_kpi_card("Total Gasto em OS", total_cost_str), 1)
        
        self.analysis_layout.addLayout(kpi_layout)

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
        self.update_age_donut()
        layout.addWidget(age_group, 1)

        # Risk / Priorities Row (2/3 width)
        top5_group = QGroupBox("Prioridades de Substituição")
        top5_group.setStyleSheet("QGroupBox { border: 1px solid #334155; border-radius: 12px; padding-top: 24px; font-weight: bold; }")
        top5_layout = QVBoxLayout(top5_group)
        top5_layout.setContentsMargins(24, 24, 24, 24)
        top5_layout.setSpacing(12)
        
        self.top5_chart_view = QChartView()
        self.top5_chart_view.setRenderHint(QPainter.Antialiasing)
        self.top5_chart_view.setStyleSheet("background: transparent;")
        self.top5_chart_view.setFixedHeight(280)
        self.populate_top5()
        top5_layout.addWidget(self.top5_chart_view)
        layout.addWidget(top5_group, 2)
        
        self.analysis_layout.addLayout(layout)

    def setup_history_row(self):
        # OS History (100% width)
        chart_container = QGroupBox("Histórico de Emissão de OS")
        chart_container.setStyleSheet("QGroupBox { border: 1px solid #334155; border-radius: 12px; padding-top: 24px; font-weight: bold; }")
        chart_vbox = QVBoxLayout(chart_container)
        chart_vbox.setContentsMargins(24, 24, 24, 24)
        
        self.global_chart_view = CrosshairChartView()
        self.global_chart_view.setRenderHint(QPainter.Antialiasing)
        self.global_chart_view.setStyleSheet("background: transparent;")
        self.global_chart_view.setFixedHeight(300)
        chart_vbox.addWidget(self.global_chart_view)
        
        self.update_global_chart()
        self.analysis_layout.addWidget(chart_container)

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

        for equip in MOCK_EQUIPMENT:
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
        over = sum(1 for i in MOCK_EQUIPMENT if (date.today().year - int(i["data_aquisicao"].split("-")[0])) >= threshold)
        under = len(MOCK_EQUIPMENT) - over
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
        
        all_years = list(range(2018, 2025))
        year_data = {y: {m: 0 for m in range(1, 13)} for y in all_years}
        for equip in MOCK_EQUIPMENT:
            for os in equip["os"]:
                dt = datetime.strptime(os["data"], "%Y-%m-%d").date()
                if dt.year in all_years: year_data[dt.year][dt.month] += 1
        
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
                if year in self.active_years:
                    averages[month] += val
                    if val > max_val: max_val = val
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
        axis_y.setRange(0, max_val + 2)
        
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

    def populate_top5(self):
        sorted_items = sorted(MOCK_EQUIPMENT, key=lambda x: x["score"], reverse=True)[:5]
        
        series = QHorizontalBarSeries()
        bar_set = QBarSet("Score")
        bar_set.setBrush(QColor("#CF6679"))
        
        # QHorizontalBarSeries appends from bottom to top on Y axis, so we reverse
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
        
        def show_details(index):
            # In reversed list, the index corresponds to reversing sorted_items
            item = list(reversed(sorted_items))[index]
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Detalhes - {item['modelo']}")
            dialog.setStyleSheet("QDialog { background-color: #121212; color: #E0E0E0; } QLabel { color: #E0E0E0; }")
            dialog.setFixedWidth(250)
            layout = QFormLayout(dialog)
            for k, v in item.items():
                layout.addRow(QLabel(str(k).capitalize() + ":"), QLabel(str(v)))
            btn = QPushButton("Fechar")
            btn.clicked.connect(dialog.accept)
            layout.addWidget(btn)
            dialog.exec()
            
        bar_set.clicked.connect(show_details)
        
        self.top5_chart_view.setChart(chart)

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
        layout.addWidget(self.main_table); self.apply_filters(); self.data_layout.addWidget(group)

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
