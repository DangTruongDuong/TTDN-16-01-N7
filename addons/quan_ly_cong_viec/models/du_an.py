import random
from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import ValidationError

class DuAn(models.Model):
    _name = 'du_an'
    _description = 'Dự Án'
    _rec_name = 'ten_du_an'

    ten_du_an = fields.Char(string='Tên Dự Án', required=True)
    mo_ta = fields.Text(string='Mô Tả')
    # tien_do_du_an = fields.Float(string="Tiến Độ Dự Án (%)", compute="_compute_tien_do", store=True)
    
    # Trường loại dự án - BẮT BUỘC phải chọn
    loai_du_an_id = fields.Many2one(
        'loai_du_an', 
        string='Loại Dự Án', 
        required=True,
        help='Chọn loại dự án để hệ thống tự động đề xuất nhân viên phù hợp'
    )
    
    nguoi_phu_trach_id = fields.Many2one('nhan_vien', string='Người Phụ Trách', ondelete='set null')

    nhan_vien_ids = fields.Many2many('nhan_vien', 'du_an_nhan_vien_rel', 'du_an_id', 'nhan_vien_id', string='Nhân Viên Tham Gia')
    
    so_luong_nhan_vien_toi_da = fields.Integer(
        string='Số Lượng Nhân Viên Tối Đa',
        default=4,
        help='Số lượng nhân viên tối đa có thể tham gia vào dự án. Đặt 0 để không giới hạn.'
    )
    
    so_luong_nhan_vien_hien_tai = fields.Integer(
        string='Số Lượng Nhân Viên Hiện Tại',
        compute='_compute_so_luong_nhan_vien',
        store=False,
        help='Số lượng nhân viên hiện tại đang tham gia dự án'
    )
    
    @api.depends('nhan_vien_ids')
    def _compute_so_luong_nhan_vien(self):
        """Tính toán số lượng nhân viên hiện tại"""
        for record in self:
            record.so_luong_nhan_vien_hien_tai = len(record.nhan_vien_ids)

    tai_nguyen_ids = fields.One2many('tai_nguyen', 'du_an_id', string='Danh Sách Tài Nguyên')

    cong_viec_ids = fields.One2many('cong_viec', 'du_an_id', string='Công Việc')
        
    dashboard_id = fields.Many2one('dashboard', string="Dashboard")

    khach_hang_id = fields.Many2one('customer', string='Khách hàng', ondelete='set null')
    
    hop_dong_id = fields.Many2one('contract', string='Hợp đồng liên quan', domain="[('customer_id', '=', khach_hang_id)]")
    
    danh_gia_nhan_vien_ids = fields.One2many('danh_gia_nhan_vien', 'du_an_id', string='Đánh Giá Nhân Viên')
    tien_do_du_an = fields.Selection([
        ('chua_bat_dau', 'Chưa Bắt Đầu'),
        ('dang_thuc_hien', 'Đang Thực Hiện'),
        ('hoan_thanh', 'Hoàn Thành'),
        ('tam_dung', 'Tạm Dừng')
    ], string="Trạng Thái Dự Án", default='chua_bat_dau')
    phan_tram_du_an = fields.Float(string="Tiến Độ Dự Án (%)", default=0.0)
    deadline_du_an = fields.Date(string='Deadline Dự Án', help='Hạn chót hoàn thành dự án')
    nhat_ky_cong_viec_ids = fields.One2many('nhat_ky_cong_viec', 'du_an_id', string='Nhật Ký Công Việc')
    
    # Computed field để lấy danh sách chức vụ ID từ loại dự án (dùng cho domain)
    chuc_vu_ids_from_loai = fields.Many2many(
        'chuc_vu',
        string='Chức Vụ Từ Loại Dự Án',
        compute='_compute_chuc_vu_ids_from_loai',
        store=False,
        help='Danh sách chức vụ từ loại dự án, dùng cho domain filter'
    )
    
    @api.depends('loai_du_an_id', 'loai_du_an_id.chuc_vu_ids', 'loai_du_an_id.cong_viec_cau_hinh_ids.chuc_vu_ids')
    def _compute_chuc_vu_ids_from_loai(self):
        """Tính toán danh sách chức vụ từ loại dự án và công việc cấu hình"""
        for record in self:
            chuc_vu_ids = []
            if record.loai_du_an_id:
                # Lấy chức vụ từ chuc_vu_ids
                chuc_vu_ids = record.loai_du_an_id.chuc_vu_ids.ids if record.loai_du_an_id.chuc_vu_ids else []
                # Lấy chức vụ từ công việc cấu hình
                cong_viec_cau_hinh = record.loai_du_an_id.cong_viec_cau_hinh_ids.filtered(
                    lambda x: x.active and x.chuc_vu_ids
                )
                chuc_vu_tu_cong_viec = cong_viec_cau_hinh.mapped('chuc_vu_ids.id') if cong_viec_cau_hinh else []
                # Kết hợp và loại bỏ trùng lặp
                all_chuc_vu_ids = list(set(chuc_vu_ids + chuc_vu_tu_cong_viec))
                record.chuc_vu_ids_from_loai = [(6, 0, all_chuc_vu_ids)]
            else:
                record.chuc_vu_ids_from_loai = [(5, 0, 0)]

    @api.depends('tien_do_du_an')
    def _compute_phan_tram(self):
        """ Cập nhật phần trăm hoàn thành theo trạng thái dự án """
        for record in self:
            if record.tien_do_du_an == 'chua_bat_dau':
                record.phan_tram_du_an = 0.0  # Nếu "Chưa Bắt Đầu", phần trăm luôn là 0.
    
    def write(self, vals):
        """Override write để tự động cập nhật công việc khi chuyển trạng thái dự án"""
        result = super(DuAn, self).write(vals)
        
        # Kiểm tra sau khi cập nhật, nếu trạng thái dự án là 'hoan_thanh'
        for record in self:
            if record.tien_do_du_an == 'hoan_thanh':
                # Tìm giai đoạn "Hoàn Thành" hoặc tạo mới nếu chưa có
                giai_doan_hoan_thanh = self.env['giai_doan_cong_viec'].search([
                    ('ten_giai_doan', '=', 'Hoàn Thành')
                ], limit=1)
                
                if not giai_doan_hoan_thanh:
                    giai_doan_hoan_thanh = self.env['giai_doan_cong_viec'].create({
                        'ten_giai_doan': 'Hoàn Thành',
                        'thu_tu': 999
                    })
                
                # Cập nhật tất cả công việc trong dự án
                for cong_viec in record.cong_viec_ids:
                    # Cập nhật giai đoạn công việc
                    cong_viec.write({
                        'giai_doan_id': giai_doan_hoan_thanh.id,
                    })
                    
                    # Cập nhật tất cả nhật ký công việc lên 100%
                    if cong_viec.nhat_ky_cong_viec_ids:
                        cong_viec.nhat_ky_cong_viec_ids.write({
                            'muc_do': 100.0,
                            'trang_thai': 'hoan_thanh_xuat_sac'
                        })
                    else:
                        # Nếu công việc chưa có nhật ký, tạo nhật ký mới với mức độ 100%
                        self.env['nhat_ky_cong_viec'].create({
                            'cong_viec_id': cong_viec.id,
                            'nhan_vien_ids': [(6, 0, cong_viec.nhan_vien_ids.ids)] if cong_viec.nhan_vien_ids else [(6, 0, [])],
                            'muc_do': 100.0,
                            'trang_thai': 'hoan_thanh_xuat_sac',
                            'mo_ta': 'Tự động cập nhật khi dự án hoàn thành'
                        })
                
                # Cập nhật phần trăm dự án lên 100%
                if record.phan_tram_du_an != 100.0:
                    record.phan_tram_du_an = 100.0
        
        return result
    
    @api.constrains('phan_tram_du_an', 'tien_do_du_an')
    def _check_phan_tram_du_an(self):
        """ Kiểm tra điều kiện hợp lệ cho phần trăm hoàn thành """
        for record in self:
            if record.tien_do_du_an == 'chua_bat_dau' and record.phan_tram_du_an != 0:
                raise ValidationError("Tiến độ dự án phải là 0% khi dự án ở trạng thái 'Chưa Bắt Đầu'.")
            if record.phan_tram_du_an < 0 or record.phan_tram_du_an > 100:
                raise ValidationError("Tiến độ dự án phải nằm trong khoảng từ 0% đến 100%.")
    
    @api.constrains('nhan_vien_ids', 'so_luong_nhan_vien_toi_da')
    def _check_so_luong_nhan_vien(self):
        """ Kiểm tra số lượng nhân viên không vượt quá giới hạn """
        for record in self:
            if record.so_luong_nhan_vien_toi_da > 0:
                so_luong_hien_tai = len(record.nhan_vien_ids)
                if so_luong_hien_tai > record.so_luong_nhan_vien_toi_da:
                    raise ValidationError(
                        f"Số lượng nhân viên tham gia ({so_luong_hien_tai}) vượt quá giới hạn tối đa "
                        f"({record.so_luong_nhan_vien_toi_da}). Vui lòng giảm số lượng nhân viên hoặc tăng giới hạn."
                    )
            
    @api.onchange('nhan_vien_ids', 'so_luong_nhan_vien_toi_da')
    def _onchange_nhan_vien_ids(self):
        """Cảnh báo khi số lượng nhân viên vượt quá giới hạn"""
        if self.so_luong_nhan_vien_toi_da > 0:
            so_luong_hien_tai = len(self.nhan_vien_ids)
            if so_luong_hien_tai > self.so_luong_nhan_vien_toi_da:
                return {
                    'warning': {
                        'title': 'Vượt quá giới hạn nhân viên',
                        'message': f'Số lượng nhân viên hiện tại ({so_luong_hien_tai}) vượt quá giới hạn tối đa '
                                 f'({self.so_luong_nhan_vien_toi_da}). Vui lòng giảm số lượng nhân viên hoặc tăng giới hạn.'
                    }
                }
            elif so_luong_hien_tai == self.so_luong_nhan_vien_toi_da:
                return {
                    'warning': {
                        'title': 'Đã đạt giới hạn',
                        'message': f'Dự án đã đạt số lượng nhân viên tối đa ({self.so_luong_nhan_vien_toi_da}). '
                                 f'Không thể thêm nhân viên mới trừ khi tăng giới hạn.'
                    }
                }
    
    @api.onchange('loai_du_an_id')
    def _onchange_loai_du_an_id(self):
        """Tự động đề xuất nhân viên và công việc khi chọn loại dự án"""
        if self.loai_du_an_id:
            # Lấy danh sách chức vụ yêu cầu cho loại dự án này
            chuc_vu_ids = self.loai_du_an_id.chuc_vu_ids.ids

            # Lấy danh sách chức vụ từ công việc cấu hình sẵn
            cong_viec_cau_hinh = self.loai_du_an_id.cong_viec_cau_hinh_ids.filtered(
                lambda x: x.active and x.chuc_vu_ids
            )
            chuc_vu_tu_cong_viec = cong_viec_cau_hinh.mapped('chuc_vu_ids.id') if cong_viec_cau_hinh else []

            # Kết hợp chức vụ từ cả hai nguồn
            all_chuc_vu_ids = list(set(chuc_vu_ids + chuc_vu_tu_cong_viec))

            if all_chuc_vu_ids:
                # Với mỗi chức vụ, chọn 1 nhân viên phù hợp nhất (ít dự án nhất)
                nhan_vien_de_xuat = []

                for chuc_vu_id in all_chuc_vu_ids:
                    # Tìm nhân viên có chức vụ này và tham gia dưới 3 dự án
                    nhan_vien_cung_chuc_vu = self.env['nhan_vien'].search([
                        ('chuc_vu_id', '=', chuc_vu_id)
                    ])

                    # Lọc nhân viên tham gia dưới 3 dự án và sắp xếp theo số dự án (ít nhất trước)
                    nhan_vien_phu_hop = []
                    for nv in nhan_vien_cung_chuc_vu:
                        so_du_an = self.env['du_an'].search_count([
                            ('nhan_vien_ids', 'in', [nv.id])
                        ])
                        if so_du_an < 3:
                            nhan_vien_phu_hop.append((nv, so_du_an))

                    # Sắp xếp theo số dự án (ít nhất trước) và lấy nhân viên đầu tiên
                    if nhan_vien_phu_hop:
                        nhan_vien_phu_hop.sort(key=lambda x: x[1])  # Sắp xếp theo số dự án
                        nhan_vien_de_xuat.append(nhan_vien_phu_hop[0][0])  # Lấy nhân viên có ít dự án nhất

                if nhan_vien_de_xuat:
                    # Áp dụng giới hạn số lượng nếu có
                    if self.so_luong_nhan_vien_toi_da > 0 and len(nhan_vien_de_xuat) > self.so_luong_nhan_vien_toi_da:
                        nhan_vien_de_xuat = nhan_vien_de_xuat[:self.so_luong_nhan_vien_toi_da]

                    nhan_vien_list_ids = [nv.id for nv in nhan_vien_de_xuat]
                    self.nhan_vien_ids = [(6, 0, nhan_vien_list_ids)]

                    # Tự động chọn người phụ trách đầu tiên nếu chưa có
                    if not self.nguoi_phu_trach_id and nhan_vien_de_xuat:
                        self.nguoi_phu_trach_id = nhan_vien_de_xuat[0]
                    else:
                        # Không tìm thấy nhân viên phù hợp
                        self.nhan_vien_ids = [(5, 0, 0)]  # Xóa danh sách cũ
                        chuc_vu_names = []
                        if all_chuc_vu_ids:
                            chuc_vu_names = self.env["chuc_vu"].browse(all_chuc_vu_ids).mapped("ten_chuc_vu")
                        chuc_vu_str = ", ".join(chuc_vu_names) if chuc_vu_names else "Không có chức vụ nào được cấu hình"
                        return {
                            'warning': {
                                'title': 'Không tìm thấy nhân viên phù hợp',
                                'message': f'Không có nhân viên nào có chức vụ phù hợp với loại dự án "{self.loai_du_an_id.ten_loai}". '
                                         f'Các chức vụ yêu cầu: {chuc_vu_str}'
                            }
                        }
                else:
                    # Không tìm thấy nhân viên phù hợp
                    self.nhan_vien_ids = [(5, 0, 0)]  # Xóa danh sách cũ
                    chuc_vu_names = []
                    if all_chuc_vu_ids:
                        chuc_vu_names = self.env["chuc_vu"].browse(all_chuc_vu_ids).mapped("ten_chuc_vu")
                    chuc_vu_str = ", ".join(chuc_vu_names) if chuc_vu_names else "Không có chức vụ nào được cấu hình"
                    return {
                        'warning': {
                            'title': 'Không tìm thấy nhân viên phù hợp',
                            'message': f'Không có nhân viên nào có chức vụ phù hợp với loại dự án "{self.loai_du_an_id.ten_loai}". '
                                     f'Các chức vụ yêu cầu: {chuc_vu_str}'
                        }
                    }
            else:
                # Loại dự án chưa được cấu hình chức vụ
                self.nhan_vien_ids = [(5, 0, 0)]
                return {
                    'warning': {
                        'title': 'Loại dự án chưa được cấu hình',
                        'message': f'Loại dự án "{self.loai_du_an_id.ten_loai}" chưa được cấu hình chức vụ yêu cầu hoặc công việc. '
                                 f'Vui lòng cấu hình trong menu Loại Dự Án.'
                    }
                }
    
    @api.model
    def create(self, vals):
        """ Đảm bảo người phụ trách có trong danh sách nhân viên tham gia khi tạo dự án """
        nguoi_phu_trach_id = vals.get('nguoi_phu_trach_id')
        nhan_vien_ids = vals.get('nhan_vien_ids', [])
        loai_du_an_id = vals.get('loai_du_an_id')

        # Kiểm tra xem đã có nhân viên chưa
        has_nhan_vien = False
        if nhan_vien_ids:
            # Kiểm tra format của nhan_vien_ids
            if isinstance(nhan_vien_ids[0], (list, tuple)) and len(nhan_vien_ids[0]) > 2:
                has_nhan_vien = bool(nhan_vien_ids[0][2])

        # Tự động phân công nhân viên nếu có loại dự án nhưng chưa có nhân viên
        if loai_du_an_id and not has_nhan_vien:
            loai_du_an = self.env['loai_du_an'].browse(loai_du_an_id)
            
            # Lấy chức vụ từ cả chuc_vu_ids và công việc cấu hình
            chuc_vu_ids = loai_du_an.chuc_vu_ids.ids if loai_du_an.chuc_vu_ids else []
            cong_viec_cau_hinh = loai_du_an.cong_viec_cau_hinh_ids.filtered(lambda x: x.active and x.chuc_vu_ids)
            chuc_vu_tu_cong_viec = cong_viec_cau_hinh.mapped('chuc_vu_ids.id') if cong_viec_cau_hinh else []
            all_chuc_vu_ids = list(set(chuc_vu_ids + chuc_vu_tu_cong_viec))
            
            if all_chuc_vu_ids:
                nhan_vien_phu_hop = self.env['nhan_vien'].search([
                    ('chuc_vu_id', 'in', all_chuc_vu_ids)
                ])
                if nhan_vien_phu_hop:
                    nhan_vien_list = set(nhan_vien_phu_hop.ids)
                    # Thêm người phụ trách nếu có
                    if nguoi_phu_trach_id:
                        nhan_vien_list.add(nguoi_phu_trach_id)
                    
                    # Áp dụng giới hạn số lượng nếu có
                    so_luong_toi_da = vals.get('so_luong_nhan_vien_toi_da', 0)
                    if so_luong_toi_da > 0 and len(nhan_vien_list) > so_luong_toi_da:
                        # Giới hạn số lượng nhân viên
                        nhan_vien_list = list(nhan_vien_list)[:so_luong_toi_da]
                    
                    vals['nhan_vien_ids'] = [(6, 0, list(nhan_vien_list))]
                    # Tự động chọn người phụ trách đầu tiên nếu chưa có
                    if not nguoi_phu_trach_id and nhan_vien_phu_hop:
                        vals['nguoi_phu_trach_id'] = nhan_vien_phu_hop[0].id
                elif nguoi_phu_trach_id:
                    vals['nhan_vien_ids'] = [(6, 0, [nguoi_phu_trach_id])]
            elif nguoi_phu_trach_id:
                vals['nhan_vien_ids'] = [(6, 0, [nguoi_phu_trach_id])]
        elif nguoi_phu_trach_id:
            # Đảm bảo người phụ trách có trong danh sách
            nhan_vien_list = set()
            if nhan_vien_ids and isinstance(nhan_vien_ids[0], (list, tuple)) and len(nhan_vien_ids[0]) > 2:
                nhan_vien_list = set(nhan_vien_ids[0][2])
            nhan_vien_list.add(nguoi_phu_trach_id)
            vals['nhan_vien_ids'] = [(6, 0, list(nhan_vien_list))]

        record = super(DuAn, self).create(vals)
        
        # Tự động tạo công việc mặc định dựa trên loại dự án
        if loai_du_an_id:
            record._create_default_cong_viec()

        # Nếu dự án có deadline, tự động set hạn chót cho tất cả công việc
        # Dùng giờ 00:00:00 để tránh bị lệch sang ngày hôm sau do timezone
        if record.deadline_du_an and record.cong_viec_ids:
            deadline_datetime = datetime.combine(record.deadline_du_an, datetime.min.time())
            record.cong_viec_ids.write({'han_chot': deadline_datetime})
        
        # Nếu được tạo từ form view, tự động chuyển sang tab Công Việc
        if self.env.context.get('form_view_initial_mode') == 'edit' or self.env.context.get('default_du_an_id'):
            # Sẽ được xử lý bởi JavaScript trong view
            pass
        
        return record
    
    def action_view_cong_viec(self):
        """Action để chuyển sang tab Công Việc"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Công Việc - {self.ten_du_an}',
            'res_model': 'du_an',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_du_an_id': self.id,
                'active_tab': 'cong_viec',
            },
            'views': [(False, 'form')],
        }
    
    def _create_default_cong_viec(self):
        """Tự động tạo các công việc từ cấu hình loại dự án"""
        self.ensure_one()
        
        if not self.loai_du_an_id:
            return
        
        # Lấy danh sách công việc đã cấu hình sẵn cho loại dự án này
        # Không ép buộc phải có chức vụ (chuc_vu_ids), để vẫn tạo được công việc
        # ngay cả khi cấu hình cũ chưa chọn chức vụ.
        cong_viec_cau_hinh = self.loai_du_an_id.cong_viec_cau_hinh_ids.filtered(
            lambda x: x.active
        )
        
        if not cong_viec_cau_hinh:
            # Nếu không có cấu hình, không tạo công việc tự động
            return
        
        # Nhóm nhân viên theo chức vụ để dễ dàng phân công
        nhan_vien_theo_chuc_vu = {}
        for nhan_vien in self.nhan_vien_ids:
            if nhan_vien.chuc_vu_id:
                chuc_vu_id = nhan_vien.chuc_vu_id.id
                if chuc_vu_id not in nhan_vien_theo_chuc_vu:
                    nhan_vien_theo_chuc_vu[chuc_vu_id] = []
                nhan_vien_theo_chuc_vu[chuc_vu_id].append(nhan_vien)

        # Giai đoạn mặc định của dự án (nếu có)
        # Ưu tiên giai đoạn gắn với dự án; nếu không có thì dùng giai đoạn chung (du_an_id = False)
        default_stage = self.env['giai_doan_cong_viec'].search(
            [('du_an_id', '=', self.id)],
            order='thu_tu asc, id asc',
            limit=1,
        )
        if not default_stage:
            default_stage = self.env['giai_doan_cong_viec'].search(
                [('du_an_id', '=', False)],
                order='thu_tu asc, id asc',
                limit=1,
            )

        # Tạo công việc từ cấu hình
        for cong_viec_template in cong_viec_cau_hinh:
            nhan_vien_phu_hop = []

            # Nếu template có cấu hình chức vụ thì cố gắng gán nhân viên theo chức vụ
            if cong_viec_template.chuc_vu_ids:
                chuc_vu_ids = cong_viec_template.chuc_vu_ids.ids
                for chuc_vu_id in chuc_vu_ids:
                    if chuc_vu_id in nhan_vien_theo_chuc_vu:
                        # Thêm nhân viên vào danh sách, tránh trùng lặp
                        for nv in nhan_vien_theo_chuc_vu[chuc_vu_id]:
                            if nv not in nhan_vien_phu_hop:
                                nhan_vien_phu_hop.append(nv)
            
            # Tạo công việc mới (kể cả khi chưa tìm được nhân viên phù hợp)
            cong_viec_vals = {
                'ten_cong_viec': cong_viec_template.ten_cong_viec,
                'mo_ta': cong_viec_template.mo_ta or '',
                'du_an_id': self.id,
                'nhan_vien_ids': [(6, 0, [nv.id for nv in nhan_vien_phu_hop])] if nhan_vien_phu_hop else [],
            }

            # Gán giai đoạn mặc định nếu có
            if default_stage:
                cong_viec_vals['giai_doan_id'] = default_stage.id

            self.env['cong_viec'].create(cong_viec_vals)
    

    def write(self, vals):
        """ Đảm bảo người phụ trách có trong danh sách nhân viên tham gia khi cập nhật dự án """
        for record in self:
            nguoi_phu_trach_id = vals.get('nguoi_phu_trach_id', record.nguoi_phu_trach_id.id if record.nguoi_phu_trach_id else False)
            nhan_vien_ids = vals.get('nhan_vien_ids', [(6, 0, record.nhan_vien_ids.ids)])
            loai_du_an_id = vals.get('loai_du_an_id', record.loai_du_an_id.id if record.loai_du_an_id else False)

            # Nếu thay đổi loại dự án, tự động cập nhật nhân viên và tạo công việc
            if 'loai_du_an_id' in vals and loai_du_an_id:
                loai_du_an = self.env['loai_du_an'].browse(loai_du_an_id)
                
                # Lấy chức vụ từ cả chuc_vu_ids và công việc cấu hình
                chuc_vu_ids = loai_du_an.chuc_vu_ids.ids if loai_du_an.chuc_vu_ids else []
                cong_viec_cau_hinh = loai_du_an.cong_viec_cau_hinh_ids.filtered(
                    lambda x: x.active and x.chuc_vu_ids
                )
                chuc_vu_tu_cong_viec = cong_viec_cau_hinh.mapped('chuc_vu_ids.id') if cong_viec_cau_hinh else []
                all_chuc_vu_ids = list(set(chuc_vu_ids + chuc_vu_tu_cong_viec))
                
                if all_chuc_vu_ids:
                    nhan_vien_phu_hop = self.env['nhan_vien'].search([
                        ('chuc_vu_id', 'in', all_chuc_vu_ids)
                    ])
                    if nhan_vien_phu_hop:
                        nhan_vien_list = set(nhan_vien_phu_hop.ids)
                        if nguoi_phu_trach_id:
                            nhan_vien_list.add(nguoi_phu_trach_id)
                        
                        # Áp dụng giới hạn số lượng nếu có
                        so_luong_toi_da = vals.get('so_luong_nhan_vien_toi_da', record.so_luong_nhan_vien_toi_da if record.so_luong_nhan_vien_toi_da else 0)
                        if so_luong_toi_da > 0 and len(nhan_vien_list) > so_luong_toi_da:
                            # Giới hạn số lượng nhân viên
                            nhan_vien_list = list(nhan_vien_list)[:so_luong_toi_da]
                        
                        vals['nhan_vien_ids'] = [(6, 0, list(nhan_vien_list))]
                        # Tự động chọn người phụ trách đầu tiên nếu chưa có
                        if not nguoi_phu_trach_id and nhan_vien_phu_hop:
                            vals['nguoi_phu_trach_id'] = nhan_vien_phu_hop[0].id
                
            # Đảm bảo người phụ trách có trong danh sách
            if nguoi_phu_trach_id:
                current_nhan_vien_ids = vals.get('nhan_vien_ids', [(6, 0, record.nhan_vien_ids.ids)])
                nhan_vien_list = set()
                if current_nhan_vien_ids and isinstance(current_nhan_vien_ids[0], (list, tuple)) and len(current_nhan_vien_ids[0]) > 2:
                    nhan_vien_list = set(current_nhan_vien_ids[0][2])
                else:
                    nhan_vien_list = set(record.nhan_vien_ids.ids) if record.nhan_vien_ids else set()
                nhan_vien_list.add(nguoi_phu_trach_id)
                vals['nhan_vien_ids'] = [(6, 0, list(nhan_vien_list))]

        result = super(DuAn, self).write(vals)
        
        # Tự động tạo công việc từ cấu hình sau khi thay đổi loại dự án
        for record in self:
            if 'loai_du_an_id' in vals and record.loai_du_an_id:
                # Chỉ tạo công việc nếu chưa có công việc nào
                if not record.cong_viec_ids:
                    cong_viec_cau_hinh = record.loai_du_an_id.cong_viec_cau_hinh_ids.filtered(lambda x: x.active)
                    if cong_viec_cau_hinh:
                        record._create_default_cong_viec()

            # Nếu deadline dự án thay đổi, cập nhật lại hạn chót cho các công việc
            # Dùng giờ 00:00:00 để tránh bị lệch sang ngày hôm sau do timezone
            if 'deadline_du_an' in vals and record.deadline_du_an and record.cong_viec_ids:
                deadline_datetime = datetime.combine(record.deadline_du_an, datetime.min.time())
                record.cong_viec_ids.write({'han_chot': deadline_datetime})
        
        return result
    
    @api.depends('cong_viec_ids.phan_tram_cong_viec')
    def _compute_phan_tram_du_an(self):
        for record in self:
            if record.cong_viec_ids:
                total_progress = sum(record.cong_viec_ids.mapped('phan_tram_cong_viec'))
                record.phan_tram_du_an = total_progress / len(record.cong_viec_ids)
            else:
                record.phan_tram_du_an = 0.0
