import re
import logging
from odoo import models, fields, api, tools
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta, date

_logger = logging.getLogger(__name__)

class Customer(models.Model):
    _name = 'customer'
    _description = 'Bảng chứa thông tin khách hàng'
    _sql_constraints = [
        ('customer_id_unique', 'unique(customer_id)', 'Mã khách hàng phải là duy nhất!'),
    ]
    near_birthday = fields.Boolean(
    "Gần tới sinh nhật",
    compute="_compute_near_birthday",
    store=False,
    help="Kiểm tra xem có gần tới sinh nhật khách hàng (trong vòng 7 ngày) hay không"
    )

    # Các trường cơ bản
    customer_id = fields.Char("Mã khách hàng", required=True, index=True, copy=False, default="New")
    customer_name = fields.Char("Tên khách hàng")
    email = fields.Char("Email")
    phone = fields.Char("Số điện thoại")
    address = fields.Char("Địa chỉ")
    gender = fields.Selection([
        ('male', 'Nam'),
        ('female', 'Nữ'),
        ('other', 'Khác')
    ], string="Giới tính")
    date_of_birth = fields.Date("Ngày sinh")
    age = fields.Integer("Tuổi", compute="_compute_age", store=True)
    income_level = fields.Selection([
        ('0-20tr', '0-20 triệu/tháng'),
        ('20-50tr', '20-50 triệu/tháng'),
        ('50-70tr', '50-70 triệu/tháng'),
        ('70-100tr', '70-100 triệu/tháng'),
        ('100tr+', '100 triệu trở lên')
    ], string="Mức thu nhập")
    is_potential = fields.Boolean("Khách hàng tiềm năng", compute="_compute_is_potential", store=True)
    image = fields.Binary("Ảnh", attachment=True)
    company_name = fields.Char("Tên công ty")
    tax_code = fields.Char("Mã số thuế")
    customer_type = fields.Selection([
        ('individual', 'Cá nhân'),
        ('company', 'Công ty')
    ], string="Loại khách hàng", default="individual")
    active = fields.Boolean("Active", default=True)
    customer_status = fields.Selection([
        ('new', 'Mới'),
        ('active', 'Đang hoạt động'),
        ('inactive', 'Không hoạt động')
    ], string="Trạng thái", default="new")

    # Trường liên kết với các model khác
    sale_order_ids = fields.One2many('sale_order', inverse_name='customer_id', string="Đơn hàng")
    interact_ids = fields.One2many('crm_interact', inverse_name='customer_id', string="Tương tác")
    contract_ids = fields.One2many('contract', inverse_name='customer_id', string="Hợp đồng")
    lead_ids = fields.One2many('crm_lead', inverse_name='customer_id', string="Cơ hội")
    feedback_ids = fields.One2many('feedback', inverse_name='customer_id', string="Phản hồi")
    task_ids = fields.One2many('project_task', inverse_name='customer_id', string="Nhiệm vụ dự án")
    note_ids = fields.One2many('note', inverse_name='customer_id', string="Ghi chú")

    # Trường tính toán (computed fields)
    total_contracts = fields.Integer("Tổng số hợp đồng", compute="_compute_total_contracts", store=True)
    total_interactions = fields.Integer("Tổng số tương tác", compute="_compute_total_interactions", store=True)
    total_sale_orders = fields.Integer("Tổng số đơn hàng", compute="_compute_total_sale_orders", store=True)
    total_amount = fields.Float("Tổng số tiền đơn hàng", compute="_compute_total_amount", store=True)
    recent_interactions = fields.Integer("Số tương tác trong tháng", compute="_compute_recent_interactions", store=True)

    age_group = fields.Selection([
        ('0-20', '0-20 tuổi'),
        ('20-30', '20-30 tuổi'),
        ('30-40', '30-40 tuổi'),
        ('40-50', '40-50 tuổi'),
        ('50+', 'Trên 50 tuổi')
    ], string="Nhóm độ tuổi", compute="_compute_age_group", store=True)

    # Trường mới: Nhóm số đơn hàng
    sale_order_group = fields.Selection([
        ('0', '0 đơn hàng'),
        ('1-5', '1-5 đơn hàng'),
        ('5-10', '5-10 đơn hàng'),
        ('10+', 'Trên 10 đơn hàng')
    ], string="Nhóm số đơn hàng", compute="_compute_sale_order_group", store=True)

    @api.depends('age')
    def _compute_age_group(self):
        for record in self:
            age = record.age
            if age <= 20:
                record.age_group = '0-20'
            elif 20 < age <= 30:
                record.age_group = '20-30'
            elif 30 < age <= 40:
                record.age_group = '30-40'
            elif 40 < age <= 50:
                record.age_group = '40-50'
            else:
                record.age_group = '50+'

    @api.depends('total_sale_orders')
    def _compute_sale_order_group(self):
        for record in self:
            orders = record.total_sale_orders
            if orders == 0:
                record.sale_order_group = '0'
            elif 1 <= orders <= 5:
                record.sale_order_group = '1-5'
            elif 5 < orders <= 10:
                record.sale_order_group = '5-10'
            else:
                record.sale_order_group = '10+'

    # Ràng buộc cho email
    @api.constrains('email')
    def _check_email(self):
        email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        for record in self:
            if record.email and not re.match(email_pattern, record.email):
                raise ValidationError("Email không hợp lệ: %s" % record.email)
            
    @api.constrains('phone')
    def _check_phone(self):
        phone_pattern = r'^(\+84|0)[1-9]\d{8,9}$'  # Ví dụ: +84981234567 hoặc 0981234567
        for record in self:
            if record.phone and not re.match(phone_pattern, record.phone):
                raise ValidationError("Số điện thoại không hợp lệ! Ví dụ hợp lệ: 0987654321 hoặc +84987654321")
            
    # Tính toán tổng số hợp đồng
    @api.depends('contract_ids')
    def _compute_total_contracts(self):
        for record in self:
            record.total_contracts = len(record.contract_ids)

    # Tính toán tổng số tương tác
    @api.depends('interact_ids')
    def _compute_total_interactions(self):
        for record in self:
            record.total_interactions = len(record.interact_ids)

    # Tính toán tổng số đơn hàng
    @api.depends('sale_order_ids')
    def _compute_total_sale_orders(self):
        """
        Tổng số "đơn hàng" hiển thị ở khách hàng.
        - Tính số bản ghi trong model custom `sale_order` (lịch sử giao dịch).
        Ghi chú: phần cộng thêm số dự án theo khách hàng sẽ được implement ở module `quan_ly_cong_viec`
        (bằng cách `_inherit` model `customer`) để tránh phụ thuộc vòng lặp và đảm bảo recompute chuẩn.
        """
        for record in self:
            record.total_sale_orders = len(record.sale_order_ids)

    @api.depends('sale_order_ids')
    def _compute_total_amount(self):
        for record in self:
            record.total_amount = sum(record.sale_order_ids.mapped('amount_total')) or 0.0

    @api.constrains('date_of_birth')
    def _check_date_of_birth(self):
        today = fields.Date.today()
        for record in self:
            if record.date_of_birth:
            # Kiểm tra ngày trong tương lai
                if record.date_of_birth > today:
                    raise ValidationError("Ngày sinh không được vượt quá ngày hiện tại!")
            # Kiểm tra ngày hợp lệ
                try:
                    date(record.date_of_birth.year, record.date_of_birth.month, record.date_of_birth.day)
                except ValueError:
                    raise ValidationError("Ngày sinh không hợp lệ!")

    @api.depends('date_of_birth')
    def _compute_age(self):
        today = fields.Date.today()
        for record in self:
            record.age = 0
            if record.date_of_birth:
                record.age = (today - record.date_of_birth).days // 365

    @api.depends('date_of_birth')
    def _compute_near_birthday(self):
        today = fields.Date.today()
        for record in self:
            if record.date_of_birth:
                birthday = record.date_of_birth.replace(year=today.year)
                # Nếu sinh nhật đã qua trong năm nay, chuyển sang năm sau
                if birthday < today:
                    birthday = birthday.replace(year=today.year + 1)
                days_until_birthday = (birthday - today).days
                record.near_birthday = 0 <= days_until_birthday <= 7
            else:
                record.near_birthday = False

    @api.depends('income_level')
    def _compute_is_potential(self):
        for record in self:
            record.is_potential = record.income_level == '100tr+'

    @api.constrains('customer_name', 'email', 'phone', 'customer_type', 'company_name', 'tax_code')
    def _check_required_fields(self):
        for record in self:
            # Kiểm tra các trường bắt buộc cố định
            if not record.customer_name:
                raise ValidationError("Vui lòng nhập Tên khách hàng!")
            if not record.email:
                raise ValidationError("Vui lòng nhập Email!")
            if not record.phone:
                raise ValidationError("Vui lòng nhập Số điện thoại!")
            
            # Kiểm tra các trường bắt buộc động (khi customer_type là company)
            if record.customer_type == 'company':
                if not record.company_name:
                    raise ValidationError("Vui lòng nhập Tên công ty!")
                if not record.tax_code:
                    raise ValidationError("Vui lòng nhập Mã số thuế!")
                
    # Đặt tên hiển thị cho bản ghi
    def name_get(self):
        result = []
        for record in self:
            if record.customer_type == 'company':
                name = f"[{record.customer_id}] {record.customer_name} (Công ty)"
            else:
                name = f"[{record.customer_id}] {record.customer_name}"
            result.append((record.id, name))
        return result

    @api.model
    def create(self, vals):
        if vals.get('customer_id', 'New') == 'New':
            sequence = self.env['ir.sequence'].search([('code', '=', 'customer.id')], limit=1)
        # Lấy mã lớn nhất hiện có
            max_record = self.search([], order='customer_id desc', limit=1)
            max_code = max_record.customer_id if max_record else 'KH00000'
        # Kiểm tra và lấy số tiếp theo
            try:
                next_num = int(max_code.replace('KH', '')) + 1
            except ValueError:
                next_num = 1  # Bắt đầu từ 1 nếu không có mã hợp lệ
            sequence.write({'number_next': next_num})
            vals['customer_id'] = self.env['ir.sequence'].next_by_code('customer.id') or 'New'
        
        # Tạo khách hàng
        record = super(Customer, self).create(vals)
        
        # Tự động gửi email chào mừng khi tạo khách hàng mới
        if record.email:
            try:
                record._send_welcome_email()
                _logger.info(f"Đã tự động gửi email chào mừng cho khách hàng {record.customer_id} ({record.email})")
            except Exception as e:
                # Không làm gián đoạn quá trình tạo nếu gửi email thất bại
                # Log lỗi nhưng không raise exception
                _logger.warning(f"Không thể gửi email chào mừng cho khách hàng {record.customer_id}: {str(e)}")
        
        return record
    
    def action_send_birthday_email(self):
        """Gửi email chúc mừng sinh nhật cho khách hàng"""
        self.ensure_one()  # Đảm bảo chỉ xử lý một bản ghi
    
        if not self.email:
            raise ValidationError("Khách hàng này chưa có email!")
    
    # Tạo template email nếu chưa tồn tại
        template = self.env.ref('quan_ly_khach_hang.mail_template_customer_birthday', raise_if_not_found=False)
        if not template:
            template = self.env['mail.template'].create({
                'name': 'Chúc mừng sinh nhật khách hàng',
                'subject': 'Chúc mừng sinh nhật - {{ object.customer_name }}',
                'model_id': self.env['ir.model']._get('customer').id,
                'email_from': '${user.email_formatted | safe}',
                'email_to': '${object.email | safe}',
                'body_html': """
                    <div style="margin: 0px; padding: 0px;">
                        <p>Kính gửi <strong>${object.customer_name}</strong>,</p>
                        <p>Chúng tôi xin gửi lời chúc mừng sinh nhật tốt đẹp nhất đến bạn! 
                        Chúc bạn một ngày sinh nhật thật vui vẻ, hạnh phúc và thành công.</p>
                        <p>Cảm ơn bạn đã luôn đồng hành cùng chúng tôi.</p>
                        <p>Trân trọng,<br/>
                        Đội ngũ công ty chúng tôi</p>
                    </div>
                """,
            })
    
    # Gửi email
        template.send_mail(self.id, force_send=True)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Thành công',
                'message': f'Email chúc mừng sinh nhật đã được gửi tới {self.email}',
                'type': 'success',
                'sticky': False,
            }
        }

    def _send_welcome_email(self):
        """Gửi email chào mừng cho khách hàng (method nội bộ, không return action)"""
        self.ensure_one()
    
        if not self.email:
            _logger.warning(f"Khách hàng {self.customer_id} không có email, không thể gửi email chào mừng")
            return False  # Không có email, không gửi
    
        # Tìm hoặc tạo template email
        template = self.env.ref('quan_ly_khach_hang.mail_template_customer_welcome', raise_if_not_found=False)
        if not template:
            # Tạo template email nếu chưa tồn tại
            IrModel = self.env['ir.model'].search([('model', '=', 'customer')], limit=1)
            if not IrModel:
                _logger.error("Không tìm thấy model 'customer' để tạo email template")
                return False
                
            template = self.env['mail.template'].create({
                'name': 'Chào mừng khách hàng mới',
                'model_id': IrModel.id,
                'subject': 'Chào mừng bạn đến với Công ty chúng tôi - {{ object.customer_name }}',
                'email_from': '${user.email_formatted | safe}',
                'email_to': '${object.email | safe}',
                'body_html': """
                    <div style="margin: 0px; padding: 0px; font-family: Arial, sans-serif;">
                        <p>Kính gửi <strong>${object.customer_name}</strong>,</p>
                        <p>Chào mừng bạn đến với Công ty chúng tôi! 
                        Chúng tôi rất vui được đồng hành cùng bạn trong hành trình sắp tới.</p>
                        <p>Nếu bạn có bất kỳ câu hỏi nào, đừng ngần ngại liên hệ với chúng tôi qua email này hoặc số điện thoại ${user.company_id.phone or 'N/A'}.</p>
                        <p>Trân trọng,<br/>
                        <strong>Đội ngũ Công ty chúng tôi</strong></p>
                    </div>
                """,
            })
            _logger.info(f"Đã tạo email template mới: {template.name} (ID: {template.id})")
    
        # Kiểm tra cấu hình mail server
        mail_server = self.env['ir.mail_server'].search([], limit=1)
        if not mail_server:
            _logger.warning("Chưa cấu hình mail server trong Odoo. Email sẽ không được gửi đi.")
            _logger.warning("Vui lòng cấu hình mail server tại: Settings > Technical > Email > Outgoing Mail Servers")
    
    # Gửi email
        try:
            mail_id = template.send_mail(self.id, force_send=True)
            _logger.info(f"Đã tạo mail.mail với ID: {mail_id} cho khách hàng {self.customer_id}")
            
            # Kiểm tra xem email có được gửi thành công không
            if mail_id:
                mail_record = self.env['mail.mail'].browse(mail_id)
                _logger.info(f"Trạng thái email: {mail_record.state}, Email to: {mail_record.email_to}, Email from: {mail_record.email_from}")
                
                # Nếu force_send=True nhưng state vẫn là 'outgoing', có thể mail server chưa được cấu hình
                if mail_record.state == 'outgoing':
                    _logger.warning("Email đang ở trạng thái 'outgoing' - có thể mail server chưa được cấu hình hoặc đang trong queue")
                elif mail_record.state == 'exception':
                    _logger.error(f"Email gửi thất bại: {mail_record.failure_reason}")
                elif mail_record.state == 'sent':
                    _logger.info("Email đã được gửi thành công!")
            
            return True
        except Exception as e:
            _logger.error(f"Lỗi khi gửi email cho khách hàng {self.customer_id}: {str(e)}", exc_info=True)
            return False

    def action_send_welcome_email(self):
        """Gửi email chào mừng cho khách hàng (dùng cho button/action trong UI)"""
        self.ensure_one()
        
        if not self.email:
            raise ValidationError("Khách hàng này chưa có email!")
        
        # Kiểm tra cấu hình mail server trước
        mail_server = self.env['ir.mail_server'].search([], limit=1)
        if not mail_server:
            raise ValidationError(
                "Chưa cấu hình mail server!\n\n"
                "Vui lòng cấu hình mail server tại:\n"
                "Settings > Technical > Email > Outgoing Mail Servers\n\n"
                "Hoặc kiểm tra log để xem chi tiết lỗi."
            )
        
        # Gọi method nội bộ để gửi email
        success = self._send_welcome_email()
        
        if success:
            # Kiểm tra lại trạng thái email
            mail_messages = self.env['mail.mail'].search([
                ('model', '=', 'customer'),
                ('res_id', '=', self.id),
                ('email_to', '=', self.email)
            ], order='create_date desc', limit=1)
            
            if mail_messages:
                state_msg = {
                    'sent': 'đã được gửi thành công',
                    'outgoing': 'đang trong hàng đợi chờ gửi',
                    'exception': f'gửi thất bại: {mail_messages.failure_reason or "Lỗi không xác định"}',
                    'cancel': 'đã bị hủy'
                }.get(mail_messages.state, f'có trạng thái: {mail_messages.state}')
                
                message = f'Email chào mừng {state_msg}. Kiểm tra log để xem chi tiết.'
            else:
                message = f'Email chào mừng đã được tạo. Kiểm tra log để xem chi tiết.'
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Thông báo',
                    'message': message,
                    'type': 'info' if mail_messages and mail_messages.state == 'outgoing' else 'success',
                    'sticky': True,
                }
            }
        else:
            raise ValidationError(
                "Không thể gửi email!\n\n"
                "Vui lòng kiểm tra:\n"
                "1. Cấu hình mail server tại Settings > Technical > Email > Outgoing Mail Servers\n"
                "2. Kiểm tra log để xem chi tiết lỗi\n"
                "3. Đảm bảo email của khách hàng hợp lệ"
            )
    
    def action_check_email_config(self):
        """Kiểm tra cấu hình email (helper method)"""
        self.ensure_one()
        
        issues = []
        info = []
        
        # Kiểm tra mail server
        mail_servers = self.env['ir.mail_server'].search([])
        if not mail_servers:
            issues.append("❌ Chưa cấu hình mail server")
        else:
            info.append(f"✅ Đã cấu hình {len(mail_servers)} mail server(s)")
            for server in mail_servers:
                info.append(f"   - {server.name} ({server.smtp_host}:{server.smtp_port})")
        
        # Kiểm tra email template
        template = self.env.ref('quan_ly_khach_hang.mail_template_customer_welcome', raise_if_not_found=False)
        if not template:
            issues.append("❌ Chưa có email template 'Chào mừng khách hàng mới'")
        else:
            info.append(f"✅ Email template đã tồn tại (ID: {template.id})")
        
        # Kiểm tra email của khách hàng
        if not self.email:
            issues.append("❌ Khách hàng chưa có email")
        else:
            info.append(f"✅ Email khách hàng: {self.email}")
        
        message = "\n".join(info + issues) if info or issues else "✅ Tất cả cấu hình đều OK"
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Kiểm tra cấu hình email',
                'message': message,
                'type': 'warning' if issues else 'success',
                'sticky': True,
            }
    }

    @api.depends('interact_ids')
    def _compute_recent_interactions(self):
        today = fields.Date.today()
        start_of_month = today.replace(day=1)
        for record in self:
            recent = record.interact_ids.filtered(
                lambda x: x.date and x.date.date() >= start_of_month
            )
            record.recent_interactions = len(recent)

    @api.onchange('income_level')
    def _onchange_income_level(self):
        """Tự động chuyển khách hàng có thu nhập cao sang tiềm năng"""
        # NOTE:
        # Trước đây code cố chuyển qua model 'potential_customer' (không tồn tại) => KeyError + RPC_ERROR.
        # Module hiện đã có field computed `is_potential` dựa trên `income_level == '100tr+'`,
        # và các view/action lọc khách hàng tiềm năng theo `is_potential`.
        # Vì vậy chỉ cần thông báo cho người dùng, không tạo record/model khác và không unlink.
        if self.income_level == '100tr+':
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                    'title': 'Khách hàng tiềm năng',
                    'message': (
                        f'Khách hàng "{self.customer_name or self.customer_id}" được đánh dấu là khách hàng tiềm năng '
                        'vì mức thu nhập >= 100 triệu/tháng.'
                    ),
                            'type': 'success',
                            'sticky': False,
                        }
                    }

    @api.model
    def convert_high_income_customers(self):
        """Cron job: đảm bảo khách hàng thu nhập cao được đánh dấu tiềm năng (không phụ thuộc model khác)."""
        _logger.info("Cron: kiểm tra khách hàng thu nhập cao để đánh dấu tiềm năng...")

        # `is_potential` là computed từ income_level, nên cron chỉ cần "touch" để trigger recompute nếu cần.
        high_income_customers = self.search([('income_level', '=', '100tr+'), ('active', '=', True)])
        if not high_income_customers:
            _logger.info("Cron: không có khách hàng thu nhập cao.")
            return 0

        # Trigger recompute an toàn (không thay đổi business data ngoài việc đảm bảo computed cập nhật)
        # Nếu sau này muốn chuyển trạng thái, có thể update thêm `customer_status` tại đây.
        high_income_customers.invalidate_recordset(['income_level'])

        _logger.info(f"Cron: đã kiểm tra {len(high_income_customers)} khách hàng thu nhập cao (tự động là tiềm năng).")
        return len(high_income_customers)