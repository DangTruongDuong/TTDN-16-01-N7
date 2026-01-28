import logging
from odoo import models, fields, api
from datetime import date, timedelta

_logger = logging.getLogger(__name__)

class Contract(models.Model):
    _name = 'contract'
    _description = 'Bảng chứa thông tin hợp đồng'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    contract_id = fields.Char("Mã hợp đồng", required=True)
    contract_name = fields.Char("Tên hợp đồng")
    customer_id = fields.Many2one('customer', string="Khách hàng", required=True, ondelete='cascade')
    start_date = fields.Date("Ngày bắt đầu hợp đồng", required=True)
    end_date = fields.Date("Ngày kết thúc hợp đồng", required=True)
    state = fields.Selection([
        ('active', 'Đang hoạt động'),
        ('ended', 'Đã kết thúc')
    ], string="Trạng thái hợp đồng", required=True, tracking=True)
    
    # Trường tính toán để cảnh báo
    days_until_expiry = fields.Integer(
        string="Số ngày còn lại đến khi hết hạn",
        compute="_compute_days_until_expiry",
        store=True
    )
    is_expiring_soon = fields.Boolean(
        string="Sắp hết hạn",
        compute="_compute_days_until_expiry",
        store=True,
        help="True nếu hợp đồng còn < 30 ngày nữa hết hạn"
    )

    @api.depends('end_date', 'state')
    def _compute_days_until_expiry(self):
        """Tính số ngày còn lại đến khi hết hạn"""
        today = date.today()
        for record in self:
            if record.end_date and record.state == 'active':
                delta = record.end_date - today
                record.days_until_expiry = delta.days
                record.is_expiring_soon = 0 <= delta.days <= 30
            else:
                record.days_until_expiry = 0
                record.is_expiring_soon = False

    # Đặt tên hiển thị cho bản ghi
    def name_get(self):
        result = []
        for record in self:
            name = f"[{record.contract_id}] {record.contract_name}"
            result.append((record.id, name))
        return result
    
    @api.model
    def send_contract_expiry_warnings(self):
        """
        Tự động gửi cảnh báo hợp đồng sắp hết hạn (chạy bởi cron job)
        Gửi thông báo qua nhiều kênh:
        1. Mail Activity (hiển thị trong Odoo Inbox)
        2. Email notification
        3. In-app notification
        """
        today = date.today()
        warning_threshold = today + timedelta(days=30)
        
        # Tìm các hợp đồng sắp hết hạn (còn 30 ngày hoặc ít hơn)
        contracts = self.search([
            ('state', '=', 'active'),
            ('end_date', '>=', today),
            ('end_date', '<=', warning_threshold),
        ])
        
        warning_count = 0
        
        for contract in contracts:
            days_left = (contract.end_date - today).days
            
            # Tạo message chi tiết
            message = f"""
            <p><strong>Cảnh báo: Hợp đồng sắp hết hạn!</strong></p>
            <p>Hợp đồng <strong>{contract.contract_name}</strong> (Mã: {contract.contract_id}) 
            của khách hàng <strong>{contract.customer_id.customer_name}</strong> 
            sẽ hết hạn sau <strong>{days_left} ngày</strong> (Ngày hết hạn: {contract.end_date.strftime('%d/%m/%Y')}).</p>
            <p>Vui lòng liên hệ với khách hàng để gia hạn hợp đồng.</p>
            """
            
            # 1. Tạo Mail Activity (hiển thị trong Odoo Inbox)
            try:
                activity_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
                if not activity_type:
                    # Tạo activity type nếu chưa có
                    activity_type = self.env['mail.activity.type'].search([('name', '=', 'To Do')], limit=1)
                
                if activity_type:
                    # Tìm user để gán activity (có thể là admin hoặc user hiện tại)
                    assigned_user = self.env.user
                    
                    # Tạo activity
                    self.env['mail.activity'].create({
                        'res_model': 'contract',
                        'res_id': contract.id,
                        'activity_type_id': activity_type.id,
                        'summary': f'Cảnh báo: Hợp đồng sắp hết hạn ({days_left} ngày)',
                        'note': message,
                        'user_id': assigned_user.id,
                        'date_deadline': contract.end_date,
                    })
                    _logger.info(f"Đã tạo activity cảnh báo cho hợp đồng {contract.contract_id}")
            except Exception as e:
                _logger.error(f"Lỗi khi tạo activity cho hợp đồng {contract.contract_id}: {str(e)}")
            
            # 2. Gửi email notification (nếu có email template)
            try:
                template = self.env.ref('quan_ly_khach_hang.mail_template_contract_expiry_warning', raise_if_not_found=False)
                if template:
                    template.send_mail(contract.id, force_send=False)
                    _logger.info(f"Đã gửi email cảnh báo cho hợp đồng {contract.contract_id}")
            except Exception as e:
                _logger.warning(f"Không thể gửi email cho hợp đồng {contract.contract_id}: {str(e)}")
            
            # 3. Tạo message trong chatter (in-app notification)
            try:
                contract.message_post(
                    body=message,
                    subject=f'Cảnh báo: Hợp đồng sắp hết hạn ({days_left} ngày)',
                    message_type='notification',
                    subtype_xmlid='mail.mt_note',
                )
                _logger.info(f"Đã tạo message trong chatter cho hợp đồng {contract.contract_id}")
            except Exception as e:
                _logger.warning(f"Không thể tạo message cho hợp đồng {contract.contract_id}: {str(e)}")
            
            warning_count += 1
        
        _logger.info(f"Đã gửi cảnh báo cho {warning_count} hợp đồng sắp hết hạn")
        return warning_count
