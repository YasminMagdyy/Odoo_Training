from datetime import datetime, timedelta
from openerp import fields
from openerp import models
from openerp import api,_
import time
import unicodedata


try:
	from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
except ImportError:
	class ReportXlsx(object):
		def __init__(self, *args, **kwargs):
			pass


class xx_rep_forklift_report_wizard(models.TransientModel):

	_name = 'xx.product.template.wizard'
    
	xx_location_id= fields.Many2one('xx.location',string ="Depo Location",default=lambda self: self.env.user.xx_depo_location,required=True)

	@api.multi	
	def generate_excel_report(self):
                datas = {}
                datas['xx_location_id'] = self.xx_location_id.name

                query = """
                    select p.default_code,p.name_template,t.part_number,l.complete_name,t1.sqty from product_product p,
                    product_template t, stock_location l,(select product_id, location_id,sum(qty)sqty from stock_quant where 
                    location_id in (select id from stock_location where usage in ('transit','internal'))group by product_id,
                    location_id having sum (qty)>0) t1 where t1.product_id = p.id and t1.location_id=l.id and p.product_tmpl_id = t.id
                """

                self.env.cr.execute(query)
                result = self.env.cr.fetchall()
                datas['table'] = result

                return {
                        'type': 'ir.actions.report.xml',
                        'report_name': 'depo.product_template_report.xlsx',
                        'datas': datas,
                        'name': 'Product Template Report'
                        }	

class product_template_xls(ReportXlsx):
	
	def generate_xlsx_report(self, workbook, datas, lines):
            worksheet = workbook.add_worksheet('Product Template Report')
            date_format = workbook.add_format({'num_format': 'dd/mm/yyyy', 'align': 'center'})
            number_format = workbook.add_format({ 'align': 'right'})
            cell_format = workbook.add_format({ 'align': 'center'})
            cell_format.set_bg_color('yellow')
            cell_format.set_bold()
            cell_format2 = workbook.add_format()
            cell_format2.set_font_color('green')
            header_format = workbook.add_format({ 'align': 'center'})
            header_format.set_bold()
            header_format.set_font_size(16)
            row = 1
            col = 0
            char_format = workbook.add_format({ 'align': 'center'})	
            worksheet.set_row(0, 20)
            worksheet.set_column(0,0, 30)
            worksheet.set_column(1,20, 30)
            worksheet.merge_range(0, 0,0,11, 'Product Template Report',header_format)
            worksheet.write(2, 0, 'Product',cell_format)
            worksheet.write(2, 1, 'Description',cell_format)
            worksheet.write(2, 2, 'part number ',cell_format)
            worksheet.write(2, 3, 'Location',cell_format)
            worksheet.write(2, 4, 'Count',cell_format)
            
            table_data = datas['table']
            for i in range(len(table_data)):
                worksheet.write(2+i+1, 0, table_data[i][0])
                worksheet.write(2+i+1, 1, table_data[i][1])                                   
                worksheet.write(2+i+1, 2, table_data[i][2])                                   
                worksheet.write(2+i+1, 3, table_data[i][3])                                   
                worksheet.write(2+i+1, 4, table_data[i][4])                                  

product_template_xls('report.depo.product_template_report.xlsx', 'stock.quant')
