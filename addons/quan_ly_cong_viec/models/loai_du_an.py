# -*- coding: utf-8 -*-
from odoo import models, fields, api

class LoaiDuAn(models.Model):
    _name = 'loai_du_an'
    _description = 'Loại Dự Án'
    _rec_name = 'ten_loai'

    ma_loai = fields.Char(string='Mã Loại', required=True)
    ten_loai = fields.Char(string='Tên Loại Dự Án', required=True)
    mo_ta = fields.Text(string='Mô Tả')
    
    # Many2many với chuc_vu: Mỗi loại dự án cần những chức vụ nào
    chuc_vu_ids = fields.Many2many(
        'chuc_vu',
        'loai_du_an_chuc_vu_rel',
        'loai_du_an_id',
        'chuc_vu_id',
        string='Chức Vụ Yêu Cầu',
        help='Danh sách chức vụ cần thiết cho loại dự án này'
    )
    
    # One2many với loai_du_an_cong_viec: Danh sách công việc cấu hình sẵn
    cong_viec_cau_hinh_ids = fields.One2many(
        'loai_du_an_cong_viec',
        'loai_du_an_id',
        string='Danh Sách Công Việc Cấu Hình Sẵn',
        help='Danh sách công việc sẽ được tự động tạo khi tạo dự án thuộc loại này'
    )
    
    # One2many với du_an: Các dự án thuộc loại này
    du_an_ids = fields.One2many('du_an', 'loai_du_an_id', string='Dự Án')
    
    _sql_constraints = [
        ('ma_loai_unique', 'unique(ma_loai)', 'Mã loại dự án phải là duy nhất!'),
    ]

    def name_get(self):
        result = []
        for record in self:
            name = f"[{record.ma_loai}] {record.ten_loai}"
            result.append((record.id, name))
        return result

