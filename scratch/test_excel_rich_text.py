import openpyxl
from openpyxl.cell.rich_text import CellRichText, TextBlock, InlineFont

wb = openpyxl.Workbook()
ws = wb.active
ws.title = "RichText Test"

# Define inline fonts
red_font = InlineFont(color='FF0000', rFont='Arial', sz=10, b=True)
green_font = InlineFont(color='008000', rFont='Arial', sz=10, b=True)
norm_font = InlineFont(rFont='Arial', sz=10)

# Build a rich text cell value
rt = CellRichText()
rt.append(TextBlock(norm_font, "If you feel "))
rt.append(TextBlock(red_font, "paint"))
rt.append(TextBlock(norm_font, " ➡️ [DB: "))
rt.append(TextBlock(green_font, "pain"))
rt.append(TextBlock(norm_font, "] stop exercising immediately."))

ws['A1'] = rt
ws.column_dimensions['A'].width = 60

wb.save("outputs/test_rich_text.xlsx")
print("Rich text Excel saved to outputs/test_rich_text.xlsx")
