"""
Draft Exporter for Jigyokei Electronic Application
Exports the current plan to an Excel sheet with severity-based highlighting.
"""
from io import BytesIO
from typing import Dict, Any
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from src.api.schemas import ApplicationRoot


class DraftExporter:
    """Export ApplicationRoot to Excel draft sheet"""
    
    @staticmethod
    def export_to_excel(plan: ApplicationRoot, result: Dict[str, Any]) -> BytesIO:
        """
        Create Excel draft sheet with severity-based highlighting.
        
        Args:
            plan: ApplicationRoot instance
            result: Analysis result from CompletionChecker
        
        Returns:
            BytesIO object containing Excel file
        """
        wb = Workbook()
        ws = wb.active
        ws.title = "電子申請下書き"
        
        # Define styles
        header_fill = PatternFill(start_color="2F75B5", end_color="2F75B5", fill_type="solid")
        critical_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
        warning_fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
        complete_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
        
        header_font = Font(color="FFFFFF", bold=True)
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        # Helper: Get severity for a field
        missing_map = {m['section']: m.get('severity', 'complete') for m in result.get('missing_mandatory', [])}
        
        def write_row(row_num, label, value, section_key):
            ws.cell(row=row_num, column=1, value=label)
            ws.cell(row=row_num, column=2, value=value if value else "")
            
            # Apply severity-based highlighting
            severity = missing_map.get(section_key, 'complete')
            fill = complete_fill
            if severity == 'critical':
                fill = critical_fill
            elif severity == 'warning':
                fill = warning_fill
            
            for col in [1, 2]:
                cell = ws.cell(row=row_num, column=col)
                cell.fill = fill
                cell.border = border
        
        row = 1
        
        # Header
        ws.merge_cells(f'A{row}:B{row}')
        cell = ws.cell(row=row, column=1, value="事業継続力強化計画 申請下書きシート")
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center')
        row += 2
        
        # Section 1: Basic Info
        ws.merge_cells(f'A{row}:B{row}')
        ws.cell(row=row, column=1, value="【様式第1】 基本情報").font = Font(bold=True)
        row += 1
        
        bi = plan.basic_info
        write_row(row, "会社名", bi.corporate_name, "BasicInfo"); row += 1
        write_row(row, "代表者", f"{bi.representative_title or ''} {bi.representative_name or ''}".strip(), "BasicInfo"); row += 1
        write_row(row, "郵便番号", bi.address_zip, "BasicInfo"); row += 1
        write_row(row, "住所", f"{bi.address_pref or ''}{bi.address_city or ''}{bi.address_street or ''}{bi.address_building or ''}", "BasicInfo"); row += 1
        write_row(row, "資本金 (円)", bi.capital, "BasicInfo"); row += 1
        write_row(row, "従業員数 (人)", bi.employees, "BasicInfo"); row += 1
        row += 1
        
        # Section 2: Goals
        ws.merge_cells(f'A{row}:B{row}')
        ws.cell(row=row, column=1, value="【様式第2】 事業概要・目標").font = Font(bold=True)
        row += 1
        
        write_row(row, "事業活動の概要", plan.goals.business_overview, "Goals"); row += 1
        write_row(row, "取組目的", plan.goals.business_purpose, "Goals"); row += 1
        row += 1
        
        # Section 3: Disaster
        ws.merge_cells(f'A{row}:B{row}')
        ws.cell(row=row, column=1, value="【様式第3】 災害想定").font = Font(bold=True)
        row += 1
        
        write_row(row, "想定する災害", plan.goals.disaster_scenario.disaster_assumption, "Goals"); row += 1
        row += 1
        
        # Section 4: Response
        ws.merge_cells(f'A{row}:B{row}')
        ws.cell(row=row, column=1, value="【様式第4】 初動対応").font = Font(bold=True)
        row += 1
        
        for i, proc in enumerate(plan.response_procedures, 1):
            write_row(row, f"{i}. カテゴリ", proc.category, "ResponseProcedures"); row += 1
            write_row(row, f"   内容", proc.action_content, "ResponseProcedures"); row += 1
        row += 1
        
        # Section 5: Measures
        ws.merge_cells(f'A{row}:B{row}')
        ws.cell(row=row, column=1, value="【様式第5】 事前対策").font = Font(bold=True)
        row += 1
        
        for i, m in enumerate(plan.measures, 1):
            write_row(row, f"{i}. カテゴリ", m.category, "Measures"); row += 1
            write_row(row, f"   内容", m.current_measure, "Measures"); row += 1
        row += 1
        
        # Section 6: Finance
        ws.merge_cells(f'A{row}:B{row}')
        ws.cell(row=row, column=1, value="【様式第6】 資金計画").font = Font(bold=True)
        row += 1
        
        for i, f in enumerate(plan.financial_plan.items, 1):
            write_row(row, f"{i}. 項目", f.item, "FinancialPlan"); row += 1
            write_row(row, f"   金額 (円)", f.amount, "FinancialPlan"); row += 1
            write_row(row, f"   調達方法", f.method, "FinancialPlan"); row += 1
        row += 1
        
        # PDCA
        ws.merge_cells(f'A{row}:B{row}')
        ws.cell(row=row, column=1, value="【推進体制】").font = Font(bold=True)
        row += 1
        
        write_row(row, "管理体制", plan.pdca.management_system, "PDCA"); row += 1
        write_row(row, "訓練・教育", plan.pdca.training_education, "PDCA"); row += 1
        
        # Adjust column widths
        ws.column_dimensions['A'].width = 30
        ws.column_dimensions['B'].width = 60
        
        # Save to BytesIO
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        return output
