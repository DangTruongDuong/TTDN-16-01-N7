# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import date
from odoo.exceptions import ValidationError

class NhanVien(models.Model):
    _name = 'nhan_vien'
    _description = 'Bảng chứa thông tin nhân viên'
    _rec_name = 'ho_va_ten'
    _order = 'ten asc, tuoi desc'

    ma_dinh_danh = fields.Char("Mã định danh", required=True)
    ho_ten_dem = fields.Char("Họ tên đệm", required=True)
    ten = fields.Char("Tên", required=True)
    ho_va_ten = fields.Char("Họ và tên", compute="_compute_ho_va_ten", store=True)
    
    ngay_sinh = fields.Date("Ngày sinh")
    que_quan = fields.Char("Quê quán")
    email = fields.Char("Email")
    so_dien_thoai = fields.Char("Số điện thoại")
    
    # Trường chức vụ hiện tại
    chuc_vu_id = fields.Many2one('chuc_vu', string='Chức vụ hiện tại', help='Chức vụ hiện tại của nhân viên')
    
    lich_su_cong_tac_ids = fields.One2many(
        "lich_su_cong_tac", 
        inverse_name="nhan_vien_id", 
        string="Danh sách lịch sử công tác"
    )
    tuoi = fields.Integer("Tuổi", compute="_compute_tuoi", store=True)
    anh = fields.Binary("Ảnh")
    danh_sach_chung_chi_bang_cap_ids = fields.One2many(
        "danh_sach_chung_chi_bang_cap", 
        inverse_name="nhan_vien_id", 
        string="Danh sách chứng chỉ bằng cấp"
    )
    so_nguoi_bang_tuoi = fields.Integer(
        "Số người bằng tuổi", 
        compute="_compute_so_nguoi_bang_tuoi",
        store=True
    )
    
    # Computed field để hiển thị tên + chức vụ
    display_name_with_chuc_vu = fields.Char(
        string="Tên hiển thị",
        compute="_compute_display_name_with_chuc_vu",
        store=False
    )
    
    _sql_constraints = [
        ('ma_dinh_danh_unique', 'unique(ma_dinh_danh)', 'Mã định danh phải là duy nhất')
    ]
    
    def _compute_display_name_with_chuc_vu(self):
        """Tính toán tên hiển thị kèm chức vụ"""
        for record in self:
            if record.ho_va_ten:
                if record.chuc_vu_id:
                    record.display_name_with_chuc_vu = f"{record.ho_va_ten} ({record.chuc_vu_id.ten_chuc_vu})"
                else:
                    record.display_name_with_chuc_vu = record.ho_va_ten
            else:
                record.display_name_with_chuc_vu = record.ma_dinh_danh or "N/A"
    
    def name_get(self):
        """Override name_get để hiển thị tên + chức vụ + số dự án đang tham gia"""
        result = []
        for record in self:
            # Xây dựng tên cơ bản
            if record.ho_va_ten:
                if record.chuc_vu_id:
                    name = f"{record.ho_va_ten} ({record.chuc_vu_id.ten_chuc_vu})"
                else:
                    name = record.ho_va_ten
            else:
                name = record.ma_dinh_danh or "N/A"

            # Thêm thông tin số dự án đang tham gia
            so_luong_du_an = self.env['du_an'].search_count([
                ('nhan_vien_ids', 'in', [record.id])
            ])

            if so_luong_du_an > 0:
                name += f" [{so_luong_du_an} dự án]"
            else:
                name += " [0 dự án]"

            result.append((record.id, name))
        return result

    @api.depends("ho_ten_dem", "ten")
    def _compute_ho_va_ten(self):
        for record in self:
            if record.ho_ten_dem and record.ten:
                record.ho_va_ten = record.ho_ten_dem + ' ' + record.ten
            else:
                record.ho_va_ten = ''
                
    @api.onchange("ten", "ho_ten_dem")
    def _default_ma_dinh_danh(self):
        for record in self:
            if record.ho_ten_dem and record.ten and not record.ma_dinh_danh:
                chu_cai_dau = ''.join([tu[0][0] for tu in record.ho_ten_dem.lower().split() if tu])
                record.ma_dinh_danh = record.ten.lower() + chu_cai_dau
    
    @api.depends("ngay_sinh")
    def _compute_tuoi(self):
        today = date.today()
        for record in self:
            if record.ngay_sinh:
                record.tuoi = today.year - record.ngay_sinh.year - (
                    (today.month, today.day) < (record.ngay_sinh.month, record.ngay_sinh.day)
                )
            else:
                record.tuoi = 0

    @api.depends("tuoi")
    def _compute_so_nguoi_bang_tuoi(self):
        for record in self:
            if record.tuoi:
                records = self.env['nhan_vien'].search(
                    [
                        ('tuoi', '=', record.tuoi),
                        ('ma_dinh_danh', '!=', record.ma_dinh_danh)
                    ]
                )
                record.so_nguoi_bang_tuoi = len(records)
            else:
                record.so_nguoi_bang_tuoi = 0

    @api.constrains('ngay_sinh', 'tuoi')
    def _check_tuoi(self):
        for record in self:
            if record.ngay_sinh and record.tuoi < 18:
                raise ValidationError("Tuổi không được nhỏ hơn 18. Vui lòng kiểm tra lại ngày sinh!")
    
    @api.model
    def create(self, vals):
        """Tự động tạo mã định danh khi tạo nhân viên nếu chưa có"""
        if not vals.get('ma_dinh_danh') and vals.get('ho_ten_dem') and vals.get('ten'):
            ho_ten_dem = vals.get('ho_ten_dem', '')
            ten = vals.get('ten', '')
            chu_cai_dau = ''.join([tu[0][0] for tu in ho_ten_dem.lower().split() if tu])
            ma_dinh_danh = ten.lower() + chu_cai_dau
            
            # Kiểm tra mã định danh có trùng không
            base_ma = ma_dinh_danh
            counter = 1
            while self.search([('ma_dinh_danh', '=', ma_dinh_danh)], limit=1):
                ma_dinh_danh = f"{base_ma}{counter}"
                counter += 1
            
            vals['ma_dinh_danh'] = ma_dinh_danh
        
        return super(NhanVien, self).create(vals)

