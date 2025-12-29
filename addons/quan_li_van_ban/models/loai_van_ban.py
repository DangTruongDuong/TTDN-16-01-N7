# -*- coding: utf-8 -*-
from odoo import models, fields


class LoaiVanBan(models.Model):
    _name = 'loai_van_ban'
    _description = 'Bảng chứa thông tin loại văn bản'

    name = fields.Char("Tên loại văn bản", required=True)
    mo_ta = fields.Text("Mô tả")
    ma_loai = fields.Char("Mã loại", required=True)
    active = fields.Boolean("Hoạt động", default=True)

