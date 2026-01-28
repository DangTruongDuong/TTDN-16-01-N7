# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ChatbotConfig(models.Model):
    _name = 'chatbot.config'
    _description = 'Cấu hình Chatbot Gemini'
    
    name = fields.Char(string='Tên cấu hình', default='Cấu hình Chatbot', required=True)
    gemini_api_key = fields.Char(string='Gemini API Key', required=True, help='API key từ Google Gemini')
    active = fields.Boolean(string='Kích hoạt', default=True)
    
    @api.model
    def get_active_config(self):
        """Lấy cấu hình đang hoạt động"""
        return self.search([('active', '=', True)], limit=1)

