# -*- coding: utf-8 -*-
from odoo import models, fields, api

class LoaiDuAnCongViec(models.Model):
    _name = 'loai_du_an_cong_viec'
    _description = 'Công Việc Cấu Hình Sẵn Cho Loại Dự Án'
    _rec_name = 'ten_cong_viec'
    _order = 'sequence, id'

    loai_du_an_id = fields.Many2one(
        'loai_du_an',
        string='Loại Dự Án',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    ten_cong_viec = fields.Char(
        string='Tên Công Việc',
        required=True,
        help='Tên công việc sẽ được tạo tự động khi tạo dự án thuộc loại này'
    )
    
    mo_ta = fields.Text(
        string='Mô Tả',
        help='Mô tả chi tiết về công việc này'
    )
    
    chuc_vu_ids = fields.Many2many(
        'chuc_vu',
        'loai_du_an_cong_viec_chuc_vu_rel',
        'loai_du_an_cong_viec_id',
        'chuc_vu_id',
        string='Chức Vụ Phụ Trách',
        required=True,
        help='Các chức vụ sẽ được tự động phân công cho công việc này. Hệ thống sẽ tìm nhân viên có các chức vụ này trong dự án và gán cho công việc.'
    )
    
    sequence = fields.Integer(
        string='Thứ Tự',
        default=10,
        help='Thứ tự hiển thị của công việc trong danh sách'
    )
    
    active = fields.Boolean(
        string='Kích Hoạt',
        default=True,
        help='Nếu bỏ chọn, công việc này sẽ không được tạo tự động khi tạo dự án mới'
    )

