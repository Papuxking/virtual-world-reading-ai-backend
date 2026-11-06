"""Exportar campos de texto sin interpretarlos como fórmulas de hoja de cálculo."""
import csv


def safe_text(value):
    if not isinstance(value, str):
        return value
    probe = value.lstrip(" \t\r\n\ufeff")
    if value.startswith(("\t", "\r", "\n")) or probe.startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


class SafeWriter:
    def __init__(self, stream, *args, **kwargs):
        self.writer = csv.writer(stream, *args, **kwargs)

    def writerow(self, row):
        return self.writer.writerow([safe_text(value) for value in row])

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


class SafeDictWriter(csv.DictWriter):
    def writerow(self, rowdict):
        return super().writerow({key: safe_text(value) for key, value in rowdict.items()})

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


def secure_workbook(workbook):
    for sheet in workbook.worksheets:
        for row in sheet.iter_rows():
            for cell in row:
                if cell.data_type == "f":
                    cell.data_type = "s"
    return workbook
