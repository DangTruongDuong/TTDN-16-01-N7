# -*- coding: utf-8 -*-
from odoo import models, fields


class VanBanDen(models.Model):
    _name = 'van_ban_den'
    _description = 'Bảng chứa thông tin văn bản đến'

    so_den = fields.Char("Số đến", required=True)
    so_ky_hieu = fields.Char("Số ký hiệu")
    ngay_den = fields.Date("Ngày đến", required=True)
    ngay_ban_hanh = fields.Date("Ngày ban hành")
    co_quan_ban_hanh = fields.Char("Cơ quan ban hành")
    trich_yeu = fields.Text("Trích yếu")
    loai_van_ban_id = fields.Many2one('loai_van_ban', string="Loại văn bản")
    nguoi_nhan = fields.Char("Người nhận")
    trang_thai = fields.Selection([
        ('moi', 'Mới'),
        ('dang_xu_ly', 'Đang xử lý'),
        ('hoan_thanh', 'Hoàn thành'),
        ('huy', 'Hủy')
    ], string="Trạng thái", default='moi')
    ghi_chu = fields.Text("Ghi chú")

