# -*- coding: utf-8 -*-
from odoo import models, fields


class VanBanDi(models.Model):
    _name = 'van_ban_di'
    _description = 'Bảng chứa thông tin văn bản đi'

    so_di = fields.Char("Số đi", required=True)
    so_ky_hieu = fields.Char("Số ký hiệu")
    ngay_di = fields.Date("Ngày đi", required=True)
    ngay_ban_hanh = fields.Date("Ngày ban hành")
    nguoi_ky = fields.Char("Người ký")
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

