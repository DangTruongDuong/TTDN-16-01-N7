from odoo import models, fields, api


class Customer(models.Model):
    _inherit = 'customer'

    # Liên kết dự án <-> khách hàng (du_an.khach_hang_id)
    du_an_ids = fields.One2many('du_an', 'khach_hang_id', string="Dự án")

    @api.depends('sale_order_ids', 'du_an_ids')
    def _compute_total_sale_orders(self):
        """
        Override để tổng số "đơn hàng" ở khách hàng phản ánh cả:
        - số giao dịch (sale_order_ids) và
        - số dự án gắn với khách hàng (du_an_ids)

        Làm ở module `quan_ly_cong_viec` để tránh phụ thuộc vòng lặp và đảm bảo
        inverse field `khach_hang_id` luôn tồn tại.
        """
        for record in self:
            record.total_sale_orders = len(record.sale_order_ids) + len(record.du_an_ids)


