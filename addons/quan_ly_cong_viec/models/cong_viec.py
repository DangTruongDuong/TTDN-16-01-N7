from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError

class CongViec(models.Model):
    _name = 'cong_viec'
    _description = 'Công Việc Dự Án'
    _rec_name = 'ten_cong_viec'

    ten_cong_viec = fields.Char(string='Tên Công Việc' )
    mo_ta = fields.Text(string='Mô Tả')
    du_an_id = fields.Many2one('du_an', string='Dự Án', required=True, ondelete='restrict')

    nhan_vien_ids = fields.Many2many('nhan_vien', 'cong_viec_nhan_vien_rel', 'cong_viec_id', 'nhan_vien_id', string='Nhân Viên Tham Gia')

    han_chot = fields.Datetime(string='Hạn Chót')
    giai_doan_id = fields.Many2one('giai_doan_cong_viec', string='Giai Đoạn')

    nhat_ky_cong_viec_ids = fields.One2many('nhat_ky_cong_viec', 'cong_viec_id', string='Nhật Ký Công Việc')

    thoi_gian_con_lai = fields.Char(string="Thời Gian Còn Lại", compute="_compute_thoi_gian_con_lai", store=True)
    
    danh_gia_nhan_vien_ids = fields.One2many('danh_gia_nhan_vien', 'cong_viec_id', string='Đánh Giá Nhân Viên')
    
    nhan_vien_display = fields.Char(string="Nhân Viên Tham Gia (Tên + Mã Định Danh)", compute="_compute_nhan_vien_display")

    phan_tram_cong_viec = fields.Float(
        string="Phần Trăm Hoàn Thành", 
        compute="_compute_phan_tram_cong_viec", 
        store=True
    )

    @api.depends('nhat_ky_cong_viec_ids.muc_do')
    def _compute_phan_tram_cong_viec(self):
        for record in self:
            if record.nhat_ky_cong_viec_ids:
                total_progress = sum(record.nhat_ky_cong_viec_ids.mapped('muc_do'))
                record.phan_tram_cong_viec = total_progress / len(record.nhat_ky_cong_viec_ids)
            else:
                record.phan_tram_cong_viec = 0.0

    
    @api.depends('nhan_vien_ids')
    def _compute_nhan_vien_display(self):
        for record in self:
            record.nhan_vien_display = ', '.join(record.nhan_vien_ids.mapped('display_name'))

    @api.depends('han_chot', 'du_an_id.create_date')
    def _compute_thoi_gian_con_lai(self):
        for record in self:
            if record.han_chot:
                # Nếu có dự án, tính số ngày từ ngày tạo dự án đến hạn chót
                if record.du_an_id and record.du_an_id.create_date:
                    start_date = record.du_an_id.create_date.date()
                else:
                    # Fallback: nếu không có dự án hoặc không có create_date thì dùng ngày hiện tại
                    start_date = datetime.now().date()

                deadline_date = record.han_chot.date()
                delta_days = (deadline_date - start_date).days

                if delta_days >= 0:
                    record.thoi_gian_con_lai = f"{delta_days} ngày"
                else:
                    record.thoi_gian_con_lai = "Đã quá hạn"
            else:
                record.thoi_gian_con_lai = "Chưa có hạn chót"

    
    @api.onchange('du_an_id')
    def _onchange_du_an_id(self):
        if self.du_an_id:
            self.nhan_vien_ids = [(6, 0, self.du_an_id.nhan_vien_ids.ids)]

            
    @api.constrains('du_an_id')
    def _check_du_an_tien_do(self):
        for record in self:
            if record.du_an_id and record.du_an_id.tien_do_du_an == 'hoan_thanh':
                raise ValidationError("Không thể thêm công việc vào dự án đã hoàn thành.")
    
    

    @api.constrains('nhan_vien_ids')
    def _check_nhan_vien_trong_du_an(self):
        for record in self:
            if record.du_an_id:
                nhan_vien_du_an_ids = record.du_an_id.nhan_vien_ids.ids
                for nhan_vien in record.nhan_vien_ids:
                    if nhan_vien.id not in nhan_vien_du_an_ids:
                        raise ValidationError(f"Nhân viên {nhan_vien.display_name} không thuộc dự án này.")

    @api.model
    def send_deadline_warnings(self):
        """Tự động gửi cảnh báo cho công việc sắp hết hạn (chạy bởi cron job)"""
        now = datetime.now()
        # Tìm các công việc còn < 3 ngày nữa hết hạn
        deadline_threshold = now + timedelta(days=3)
        
        # Tìm công việc có hạn chót trong vòng 3 ngày tới và chưa hoàn thành 100%
        cong_viecs = self.search([
            ('han_chot', '!=', False),
            ('han_chot', '<=', deadline_threshold),
            ('han_chot', '>', now),
            ('phan_tram_cong_viec', '<', 100)
        ])
        
        warning_count = 0
        for cong_viec in cong_viecs:
            # Tạo activity/reminder cho các nhân viên tham gia
            days_left = (cong_viec.han_chot - now).days
            message = f'Công việc "{cong_viec.ten_cong_viec}" của dự án "{cong_viec.du_an_id.ten_du_an if cong_viec.du_an_id else "N/A"}" sẽ hết hạn sau {days_left} ngày (Hạn chót: {cong_viec.han_chot.strftime("%d/%m/%Y %H:%M")}). Tiến độ hiện tại: {cong_viec.phan_tram_cong_viec:.1f}%'
            
            # Tạo activity cho từng nhân viên tham gia
            for nhan_vien in cong_viec.nhan_vien_ids:
                # Tạo activity reminder
                self.env['mail.activity'].create({
                    'res_model_id': self.env['ir.model']._get('cong_viec').id,
                    'res_id': cong_viec.id,
                    'activity_type_id': self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False).id or False,
                    'summary': f'Cảnh báo: Công việc sắp hết hạn ({days_left} ngày)',
                    'note': message,
                    'user_id': self.env.user.id,  # Gán cho user hiện tại hoặc có thể map với nhan_vien
                    'date_deadline': cong_viec.han_chot.date() if cong_viec.han_chot else fields.Date.today(),
                })
                warning_count += 1
        
        return warning_count