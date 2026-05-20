import sys
from cx_Freeze import setup, Executable

build_exe_options = {
    "packages": ["pandas", "PySide6"],
    "include_files": [("src/etl/data", "etl/data")],
}

setup(
    name="DashboardEngenhariaClinica",
    version="0.1",
    description="Dashboard ETL",
    options={"build_exe": build_exe_options},
    executables=[Executable("src/etl/dashboard.py", base="gui")]
)
