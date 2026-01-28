# -*- coding: utf-8 -*-
import json
import logging
import urllib.request
import urllib.parse
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

class ChatbotController(http.Controller):
    
    @http.route('/quan_ly_cong_viec/chatbot/chat', type='json', auth='user', csrf=False)
    def chatbot_chat(self, message=None, **kwargs):
        """Xử lý tin nhắn từ chatbot và gọi Gemini API"""
        try:
            if not message or not message.strip():
                return {
                    'success': False,
                    'message': 'Vui lòng nhập câu hỏi.'
                }
            
            # Lấy cấu hình chatbot
            config = request.env['chatbot.config'].get_active_config()
            if not config or not config.gemini_api_key:
                return {
                    'success': False,
                    'message': 'Chatbot chưa được cấu hình. Vui lòng cấu hình API key Gemini trong menu Cấu hình Chatbot.'
                }
            
            # Lấy tất cả dữ liệu từ 3 modules để cung cấp context cho Gemini
            all_data = self._get_all_data()
            
            # Tạo prompt với context dữ liệu
            system_prompt = self._create_system_prompt(all_data)
            full_prompt = f"{system_prompt}\n\nNgười dùng hỏi: {message.strip()}\n\nHãy trả lời dựa trên dữ liệu trên."
            
            # Gọi Gemini API
            gemini_response = self._call_gemini_api(config.gemini_api_key, full_prompt)
            
            return {
                'success': True,
                'message': gemini_response
            }
            
        except Exception as e:
            _logger.error(f"Lỗi chatbot: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': f'Có lỗi xảy ra: {str(e)}'
            }
    
    def _get_nhan_vien_name(self, nhan_vien):
        """Helper method để lấy tên nhân viên"""
        if not nhan_vien:
            return "Chưa có"
        try:
            return nhan_vien.display_name or nhan_vien.ho_va_ten or "Chưa có"
        except:
            return "Chưa có"
    
    def _get_all_data(self):
        """Lấy tất cả dữ liệu từ 3 modules: quan_ly_cong_viec, quan_ly_khach_hang, nhan_su"""
        all_data = {
            'du_an': [],
            'cong_viec': [],
            'nhan_vien': [],
            'khach_hang': [],
            'don_hang': [],
            'hop_dong': [],
            'co_hoi': [],
            'dashboard_stats': {},  # Thêm thống kê từ dashboard
        }
        
        try:
            # ========== LẤY THỐNG KÊ TỪ DASHBOARD ==========
            try:
                dashboard = request.env['dashboard'].sudo().get_or_create_dashboard()
                # Force compute để đảm bảo có dữ liệu mới nhất
                dashboard._compute_tong_quan()
                all_data['dashboard_stats'] = {
                    'so_luong_du_an': dashboard.so_luong_du_an or 0,
                    'so_luong_cong_viec': dashboard.so_luong_cong_viec or 0,
                    'so_luong_nhan_vien': dashboard.so_luong_nhan_vien or 0,
                    'du_an_hoan_thanh': dashboard.du_an_hoan_thanh or 0,
                    'du_an_dang_thuc_hien': dashboard.du_an_dang_thuc_hien or 0,
                    'du_an_chua_bat_dau': dashboard.du_an_chua_bat_dau or 0,
                    'du_an_tam_dung': dashboard.du_an_tam_dung or 0,
                }
                _logger.info(f"Dashboard stats - Số lượng dự án: {all_data['dashboard_stats']['so_luong_du_an']}")
            except Exception as e:
                _logger.error(f"Lỗi khi lấy thống kê từ dashboard: {str(e)}", exc_info=True)
            
            # ========== MODULE QUAN_LY_CONG_VIEC ==========
            
            # 1. Dự án (du_an) - Lấy chi tiết tất cả dự án
            try:
                # Sử dụng sudo() để đảm bảo có quyền đọc tất cả dữ liệu
                # Lấy tất cả dự án không có điều kiện filter
                du_an_records = request.env['du_an'].sudo().search([])
                _logger.info(f"Tìm thấy {len(du_an_records)} dự án trong hệ thống (sau khi search)")
                
                # So sánh với dashboard
                dashboard_count = all_data.get('dashboard_stats', {}).get('so_luong_du_an', 0)
                if len(du_an_records) != dashboard_count:
                    _logger.warning(f"Số lượng dự án không khớp: search()={len(du_an_records)}, dashboard={dashboard_count}")
                
                count_added = 0
                for du_an in du_an_records:
                    try:
                        nhan_vien_phu_trach = self._get_nhan_vien_name(du_an.nguoi_phu_trach_id)
                        nhan_vien_tham_gia = ', '.join([self._get_nhan_vien_name(nv) for nv in du_an.nhan_vien_ids]) or "Chưa có"
                        
                        deadline = "Chưa có"
                        if du_an.deadline_du_an:
                            try:
                                deadline = du_an.deadline_du_an.strftime('%d/%m/%Y')
                            except:
                                pass
                        
                        tien_do = "Chưa có"
                        try:
                            tien_do = dict(du_an._fields['tien_do_du_an'].selection).get(du_an.tien_do_du_an, str(du_an.tien_do_du_an) if du_an.tien_do_du_an else "Chưa có")
                        except:
                            tien_do = str(du_an.tien_do_du_an) if du_an.tien_do_du_an else "Chưa có"
                        
                        loai_du_an = du_an.loai_du_an_id.ten_loai_du_an if du_an.loai_du_an_id else "Chưa có"
                        
                        all_data['du_an'].append({
                            'ten_du_an': du_an.ten_du_an or 'Chưa có tên',
                            'loai_du_an': loai_du_an,
                            'nhan_vien_phu_trach': nhan_vien_phu_trach,
                            'nhan_vien_tham_gia': nhan_vien_tham_gia,
                            'deadline': deadline,
                            'tien_do': tien_do,
                            'phan_tram': du_an.phan_tram_du_an or 0.0,
                            'mo_ta': du_an.mo_ta or '',
                            'so_cong_viec': len(du_an.cong_viec_ids),
                        })
                        count_added += 1
                    except Exception as e:
                        _logger.error(f"Lỗi khi lấy dữ liệu dự án {du_an.id}: {str(e)}", exc_info=True)
                        continue
                _logger.info(f"Đã thêm {count_added} dự án vào all_data (tổng: {len(all_data['du_an'])})")
            except Exception as e:
                _logger.error(f"Lỗi khi lấy danh sách dự án: {str(e)}", exc_info=True)
            
            # 2. Công việc (cong_viec)
            try:
                cong_viec_records = request.env['cong_viec'].sudo().search([])
                for cong_viec in cong_viec_records:
                    try:
                        nhan_vien_tham_gia = ', '.join([self._get_nhan_vien_name(nv) for nv in cong_viec.nhan_vien_ids]) or "Chưa có"
                        
                        han_chot = "Chưa có"
                        if cong_viec.han_chot:
                            try:
                                han_chot = cong_viec.han_chot.strftime('%d/%m/%Y %H:%M')
                            except:
                                pass
                        
                        giai_doan = cong_viec.giai_doan_id.ten_giai_doan if cong_viec.giai_doan_id else "Chưa có"
                        
                        all_data['cong_viec'].append({
                            'ten_cong_viec': cong_viec.ten_cong_viec or 'Chưa có tên',
                            'du_an': cong_viec.du_an_id.ten_du_an if cong_viec.du_an_id else "Chưa có",
                            'nhan_vien_tham_gia': nhan_vien_tham_gia,
                            'han_chot': han_chot,
                            'giai_doan': giai_doan,
                            'phan_tram': cong_viec.phan_tram_cong_viec or 0.0,
                            'mo_ta': cong_viec.mo_ta or '',
                        })
                    except Exception as e:
                        _logger.error(f"Lỗi khi lấy dữ liệu công việc {cong_viec.id}: {str(e)}")
                        continue
            except Exception as e:
                _logger.error(f"Lỗi khi lấy danh sách công việc: {str(e)}")
            
            # ========== MODULE NHAN_SU ==========
            
            # 3. Nhân viên (nhan_vien)
            try:
                nhan_vien_records = request.env['nhan_vien'].sudo().search([])
                for nv in nhan_vien_records:
                    try:
                        chuc_vu = nv.chuc_vu_id.ten_chuc_vu if nv.chuc_vu_id else "Chưa có"
                        
                        ngay_sinh = "Chưa có"
                        if nv.ngay_sinh:
                            try:
                                ngay_sinh = nv.ngay_sinh.strftime('%d/%m/%Y')
                            except:
                                pass
                        
                        all_data['nhan_vien'].append({
                            'ma_dinh_danh': nv.ma_dinh_danh or 'Chưa có',
                            'ho_va_ten': nv.ho_va_ten or 'Chưa có',
                            'chuc_vu': chuc_vu,
                            'tuoi': nv.tuoi or 0,
                            'ngay_sinh': ngay_sinh,
                            'que_quan': nv.que_quan or 'Chưa có',
                            'email': nv.email or 'Chưa có',
                            'so_dien_thoai': nv.so_dien_thoai or 'Chưa có',
                        })
                    except Exception as e:
                        _logger.error(f"Lỗi khi lấy dữ liệu nhân viên {nv.id}: {str(e)}")
                        continue
            except Exception as e:
                _logger.error(f"Lỗi khi lấy danh sách nhân viên: {str(e)}")
            
            # ========== MODULE QUAN_LY_KHACH_HANG ==========
            
            # 4. Khách hàng (customer)
            try:
                customer_records = request.env['customer'].sudo().search([])
                for customer in customer_records:
                    try:
                        ngay_sinh = "Chưa có"
                        if customer.date_of_birth:
                            try:
                                ngay_sinh = customer.date_of_birth.strftime('%d/%m/%Y')
                            except:
                                pass
                        
                        gioi_tinh = dict(customer._fields['gender'].selection).get(customer.gender, customer.gender or "Chưa có") if customer.gender else "Chưa có"
                        loai_khach_hang = dict(customer._fields['customer_type'].selection).get(customer.customer_type, customer.customer_type or "Chưa có") if customer.customer_type else "Chưa có"
                        muc_thu_nhap = dict(customer._fields['income_level'].selection).get(customer.income_level, customer.income_level or "Chưa có") if customer.income_level else "Chưa có"
                        trang_thai = dict(customer._fields['customer_status'].selection).get(customer.customer_status, customer.customer_status or "Chưa có") if customer.customer_status else "Chưa có"
                        
                        all_data['khach_hang'].append({
                            'customer_id': customer.customer_id or 'Chưa có',
                            'customer_name': customer.customer_name or 'Chưa có',
                            'loai_khach_hang': loai_khach_hang,
                            'email': customer.email or 'Chưa có',
                            'phone': customer.phone or 'Chưa có',
                            'address': customer.address or 'Chưa có',
                            'gioi_tinh': gioi_tinh,
                            'ngay_sinh': ngay_sinh,
                            'tuoi': customer.age or 0,
                            'muc_thu_nhap': muc_thu_nhap,
                            'trang_thai': trang_thai,
                            'is_potential': customer.is_potential or False,
                            'company_name': customer.company_name or 'Chưa có',
                            'tax_code': customer.tax_code or 'Chưa có',
                            'total_contracts': customer.total_contracts or 0,
                            'total_sale_orders': customer.total_sale_orders or 0,
                            'total_amount': customer.total_amount or 0.0,
                        })
                    except Exception as e:
                        _logger.error(f"Lỗi khi lấy dữ liệu khách hàng {customer.id}: {str(e)}")
                        continue
            except Exception as e:
                _logger.error(f"Lỗi khi lấy danh sách khách hàng: {str(e)}")
            
            # 5. Đơn hàng (sale_order)
            try:
                sale_order_records = request.env['sale_order'].sudo().search([])
                for order in sale_order_records:
                    try:
                        customer_name = order.customer_id.customer_name if order.customer_id else "Chưa có"
                        ngay_dat = "Chưa có"
                        if order.date_order:
                            try:
                                ngay_dat = order.date_order.strftime('%d/%m/%Y %H:%M')
                            except:
                                pass
                        
                        all_data['don_hang'].append({
                            'order_id': order.sale_order_id or 'Chưa có',
                            'order_name': order.sale_order_name or 'Chưa có tên',
                            'customer_name': customer_name,
                            'date_order': ngay_dat,
                            'amount_total': order.amount_total or 0.0,
                        })
                    except Exception as e:
                        _logger.error(f"Lỗi khi lấy dữ liệu đơn hàng {order.id}: {str(e)}")
                        continue
            except Exception as e:
                _logger.error(f"Lỗi khi lấy danh sách đơn hàng: {str(e)}")
            
            # 6. Hợp đồng (contract)
            try:
                contract_records = request.env['contract'].sudo().search([])
                for contract in contract_records:
                    try:
                        customer_name = contract.customer_id.customer_name if contract.customer_id else "Chưa có"
                        ngay_bat_dau = "Chưa có"
                        if contract.start_date:
                            try:
                                ngay_bat_dau = contract.start_date.strftime('%d/%m/%Y')
                            except:
                                pass
                        
                        ngay_ket_thuc = "Chưa có"
                        if contract.end_date:
                            try:
                                ngay_ket_thuc = contract.end_date.strftime('%d/%m/%Y')
                            except:
                                pass
                        
                        trang_thai = dict(contract._fields['state'].selection).get(contract.state, contract.state or "Chưa có") if hasattr(contract, 'state') and contract.state else "Chưa có"
                        
                        all_data['hop_dong'].append({
                            'contract_id': contract.contract_id or 'Chưa có',
                            'contract_name': contract.contract_name or 'Chưa có tên',
                            'customer_name': customer_name,
                            'start_date': ngay_bat_dau,
                            'end_date': ngay_ket_thuc,
                            'state': trang_thai,
                        })
                    except Exception as e:
                        _logger.error(f"Lỗi khi lấy dữ liệu hợp đồng {contract.id}: {str(e)}")
                        continue
            except Exception as e:
                _logger.error(f"Lỗi khi lấy danh sách hợp đồng: {str(e)}")
            
            # 7. Cơ hội (crm_lead)
            try:
                lead_records = request.env['crm_lead'].sudo().search([])
                for lead in lead_records:
                    try:
                        customer_name = lead.customer_id.customer_name if lead.customer_id else "Chưa có"
                        stage_name = lead.stage_id.name if lead.stage_id else "Chưa có"
                        
                        all_data['co_hoi'].append({
                            'lead_id': lead.crm_lead_id or 'Chưa có',
                            'lead_name': lead.crm_lead_name or 'Chưa có tên',
                            'customer_name': customer_name,
                            'expected_revenue': lead.expected_revenue or 0.0,
                            'probability': lead.probability or 0.0,
                            'stage_name': stage_name,
                        })
                    except Exception as e:
                        _logger.error(f"Lỗi khi lấy dữ liệu cơ hội {lead.id}: {str(e)}")
                        continue
            except Exception as e:
                _logger.error(f"Lỗi khi lấy danh sách cơ hội: {str(e)}")
            
        except Exception as e:
            _logger.error(f"Lỗi tổng quát khi lấy dữ liệu: {str(e)}", exc_info=True)
        
        # Log tổng số dữ liệu đã lấy được
        _logger.info(f"Tổng số dự án đã lấy được (chi tiết): {len(all_data['du_an'])}")
        _logger.info(f"Tổng số dự án từ dashboard: {all_data.get('dashboard_stats', {}).get('so_luong_du_an', 0)}")
        _logger.info(f"Tổng số công việc đã lấy được: {len(all_data['cong_viec'])}")
        _logger.info(f"Tổng số nhân viên đã lấy được: {len(all_data['nhan_vien'])}")
        
        # Đảm bảo số lượng dự án từ dashboard được ưu tiên
        dashboard_count = all_data.get('dashboard_stats', {}).get('so_luong_du_an', 0)
        actual_count = len(all_data['du_an'])
        if dashboard_count > 0 and actual_count == 0:
            _logger.error(f"LỖI NGHIÊM TRỌNG: Dashboard có {dashboard_count} dự án nhưng không lấy được dữ liệu chi tiết!")
        elif dashboard_count != actual_count:
            _logger.warning(f"Cảnh báo: Số lượng dự án không khớp - Dashboard: {dashboard_count}, Chi tiết: {actual_count}")
        
        return all_data
    
    def _create_system_prompt(self, all_data):
        """Tạo system prompt với tất cả dữ liệu từ 3 modules"""
        # Ưu tiên lấy số lượng từ dashboard (chính xác hơn)
        dashboard_stats = all_data.get('dashboard_stats', {})
        so_du_an_dashboard = dashboard_stats.get('so_luong_du_an', 0)
        so_du_an_chi_tiet = len(all_data.get('du_an', []))
        
        # Sử dụng số lượng từ dashboard nếu có, nếu không thì dùng số lượng chi tiết
        so_du_an = so_du_an_dashboard if so_du_an_dashboard > 0 else so_du_an_chi_tiet
        
        so_cong_viec = len(all_data.get('cong_viec', []))
        so_nhan_vien = len(all_data.get('nhan_vien', []))
        so_khach_hang = len(all_data.get('khach_hang', []))
        so_don_hang = len(all_data.get('don_hang', []))
        so_hop_dong = len(all_data.get('hop_dong', []))
        so_co_hoi = len(all_data.get('co_hoi', []))
        
        # Thống kê chi tiết từ dashboard
        du_an_hoan_thanh = dashboard_stats.get('du_an_hoan_thanh', 0)
        du_an_dang_thuc_hien = dashboard_stats.get('du_an_dang_thuc_hien', 0)
        du_an_chua_bat_dau = dashboard_stats.get('du_an_chua_bat_dau', 0)
        du_an_tam_dung = dashboard_stats.get('du_an_tam_dung', 0)
        
        prompt = f"""Bạn là trợ lý AI hỗ trợ quản lý hệ thống. Bạn có thể trả lời các câu hỏi về:
- Dự án và công việc
- Nhân viên và chức vụ
- Khách hàng, đơn hàng, hợp đồng và cơ hội bán hàng

THỐNG KÊ TỔNG QUAN HỆ THỐNG (Từ Dashboard - Dữ liệu chính xác):
- Tổng số dự án: {so_du_an}
  + Dự án đã hoàn thành: {du_an_hoan_thanh}
  + Dự án đang thực hiện: {du_an_dang_thuc_hien}
  + Dự án chưa bắt đầu: {du_an_chua_bat_dau}
  + Dự án tạm dừng: {du_an_tam_dung}
- Tổng số công việc: {so_cong_viec}
- Tổng số nhân viên: {so_nhan_vien}
- Tổng số khách hàng: {so_khach_hang}
- Tổng số đơn hàng: {so_don_hang}
- Tổng số hợp đồng: {so_hop_dong}
- Tổng số cơ hội bán hàng: {so_co_hoi}

Dưới đây là toàn bộ dữ liệu chi tiết trong hệ thống:

"""
        
        # ========== DỰ ÁN ==========
        # Hiển thị số lượng từ dashboard (chính xác hơn)
        prompt += f"\n=== DỰ ÁN (Tổng: {so_du_an} dự án - từ Dashboard) ===\n"
        if all_data.get('du_an') and len(all_data['du_an']) > 0:
            for idx, du_an in enumerate(all_data['du_an'], 1):
                prompt += f"""
{idx}. {du_an['ten_du_an']}
   - Loại dự án: {du_an['loai_du_an']}
   - Người phụ trách: {du_an['nhan_vien_phu_trach']}
   - Nhân viên tham gia: {du_an['nhan_vien_tham_gia']}
   - Hạn chót: {du_an['deadline']}
   - Trạng thái: {du_an['tien_do']}
   - Tiến độ: {du_an['phan_tram']}%
   - Số công việc: {du_an['so_cong_viec']}
   - Mô tả: {du_an['mo_ta']}
"""
            # Cảnh báo nếu số lượng không khớp
            if so_du_an > len(all_data['du_an']):
                prompt += f"\n⚠️ LƯU Ý: Dashboard báo có {so_du_an} dự án nhưng chỉ lấy được {len(all_data['du_an'])} dự án chi tiết ở trên.\n"
        else:
            if so_du_an > 0:
                prompt += f"⚠️ LƯU Ý: Dashboard báo có {so_du_an} dự án nhưng không lấy được danh sách chi tiết. Vui lòng kiểm tra lại hệ thống.\n"
            else:
                prompt += "Chưa có dự án nào trong hệ thống.\n"
        
        # ========== CÔNG VIỆC ==========
        if all_data.get('cong_viec'):
            prompt += f"\n=== CÔNG VIỆC (Tổng: {len(all_data['cong_viec'])} công việc) ===\n"
            for idx, cong_viec in enumerate(all_data['cong_viec'], 1):
                prompt += f"""
{idx}. {cong_viec['ten_cong_viec']}
   - Dự án: {cong_viec['du_an']}
   - Nhân viên tham gia: {cong_viec['nhan_vien_tham_gia']}
   - Hạn chót: {cong_viec['han_chot']}
   - Giai đoạn: {cong_viec['giai_doan']}
   - Tiến độ: {cong_viec['phan_tram']}%
   - Mô tả: {cong_viec['mo_ta']}
"""
        else:
            prompt += "\n=== CÔNG VIỆC: Chưa có dữ liệu ===\n"
        
        # ========== NHÂN VIÊN ==========
        if all_data.get('nhan_vien'):
            prompt += f"\n=== NHÂN VIÊN (Tổng: {len(all_data['nhan_vien'])} nhân viên) ===\n"
            for idx, nv in enumerate(all_data['nhan_vien'], 1):
                prompt += f"""
{idx}. {nv['ho_va_ten']} (Mã: {nv['ma_dinh_danh']})
   - Chức vụ: {nv['chuc_vu']}
   - Tuổi: {nv['tuoi']}
   - Ngày sinh: {nv['ngay_sinh']}
   - Quê quán: {nv['que_quan']}
   - Email: {nv['email']}
   - Số điện thoại: {nv['so_dien_thoai']}
"""
        else:
            prompt += "\n=== NHÂN VIÊN: Chưa có dữ liệu ===\n"
        
        # ========== KHÁCH HÀNG ==========
        if all_data.get('khach_hang'):
            prompt += f"\n=== KHÁCH HÀNG (Tổng: {len(all_data['khach_hang'])} khách hàng) ===\n"
            for idx, kh in enumerate(all_data['khach_hang'], 1):
                prompt += f"""
{idx}. {kh['customer_name']} (Mã: {kh['customer_id']})
   - Loại: {kh['loai_khach_hang']}
   - Email: {kh['email']}
   - Số điện thoại: {kh['phone']}
   - Địa chỉ: {kh['address']}
   - Giới tính: {kh['gioi_tinh']}
   - Tuổi: {kh['tuoi']}
   - Mức thu nhập: {kh['muc_thu_nhap']}
   - Trạng thái: {kh['trang_thai']}
   - Khách hàng tiềm năng: {'Có' if kh['is_potential'] else 'Không'}
   - Tên công ty: {kh['company_name']}
   - Mã số thuế: {kh['tax_code']}
   - Tổng hợp đồng: {kh['total_contracts']}
   - Tổng đơn hàng: {kh['total_sale_orders']}
   - Tổng giá trị: {kh['total_amount']:,.0f} VNĐ
"""
        else:
            prompt += "\n=== KHÁCH HÀNG: Chưa có dữ liệu ===\n"
        
        # ========== ĐƠN HÀNG ==========
        if all_data.get('don_hang'):
            prompt += f"\n=== ĐƠN HÀNG (Tổng: {len(all_data['don_hang'])} đơn hàng) ===\n"
            for idx, order in enumerate(all_data['don_hang'], 1):
                prompt += f"""
{idx}. {order['order_id']} - {order['order_name']}
   - Khách hàng: {order['customer_name']}
   - Ngày đặt: {order['date_order']}
   - Tổng tiền: {order['amount_total']:,.0f} VNĐ
"""
        else:
            prompt += "\n=== ĐƠN HÀNG: Chưa có dữ liệu ===\n"
        
        # ========== HỢP ĐỒNG ==========
        if all_data.get('hop_dong'):
            prompt += f"\n=== HỢP ĐỒNG (Tổng: {len(all_data['hop_dong'])} hợp đồng) ===\n"
            for idx, contract in enumerate(all_data['hop_dong'], 1):
                prompt += f"""
{idx}. {contract['contract_id']} - {contract['contract_name']}
   - Khách hàng: {contract['customer_name']}
   - Ngày bắt đầu: {contract['start_date']}
   - Ngày kết thúc: {contract['end_date']}
   - Trạng thái: {contract['state']}
"""
        else:
            prompt += "\n=== HỢP ĐỒNG: Chưa có dữ liệu ===\n"
        
        # ========== CƠ HỘI ==========
        if all_data.get('co_hoi'):
            prompt += f"\n=== CƠ HỘI BÁN HÀNG (Tổng: {len(all_data['co_hoi'])} cơ hội) ===\n"
            for idx, lead in enumerate(all_data['co_hoi'], 1):
                prompt += f"""
{idx}. {lead['lead_id']} - {lead['lead_name']}
   - Khách hàng: {lead['customer_name']}
   - Doanh thu dự kiến: {lead['expected_revenue']:,.0f} VNĐ
   - Xác suất thành công: {lead['probability']}%
   - Giai đoạn: {lead['stage_name']}
"""
        else:
            prompt += "\n=== CƠ HỘI BÁN HÀNG: Chưa có dữ liệu ===\n"
        
        prompt += f"""
\nHãy trả lời các câu hỏi một cách ngắn gọn, rõ ràng và thân thiện bằng tiếng Việt. 
Bạn có thể trả lời các câu hỏi về:
- Thông tin dự án, công việc, tiến độ, hạn chót
- Thông tin nhân viên, chức vụ, liên hệ
- Thông tin khách hàng, đơn hàng, hợp đồng, cơ hội bán hàng
- Thống kê, tổng hợp dữ liệu

⚠️ QUY TẮC QUAN TRỌNG KHI TRẢ LỜI VỀ SỐ LƯỢNG DỰ ÁN:
1. Khi người dùng hỏi về "số lượng dự án", "có bao nhiêu dự án", "tổng số dự án", "liệt kê các dự án", "danh sách dự án":
   - BẮT BUỘC phải sử dụng số liệu từ phần "THỐNG KÊ TỔNG QUAN HỆ THỐNG (Từ Dashboard - Dữ liệu chính xác)" ở đầu prompt.
   - Số lượng dự án hiện tại từ Dashboard là: {so_du_an} (ĐÂY LÀ SỐ LIỆU CHÍNH XÁC NHẤT)
   - Nếu {so_du_an} > 0: 
     * Trả lời: "Hiện tại có {so_du_an} dự án trong hệ thống."
     * Sau đó liệt kê TẤT CẢ tên các dự án từ phần "=== DỰ ÁN ===" ở trên.
     * Nếu phần "=== DỰ ÁN ===" có ít dự án hơn {so_du_an}, vẫn phải liệt kê tất cả những gì có và nói rõ "Danh sách trên có thể chưa đầy đủ."
   - Nếu {so_du_an} == 0: Trả lời "Hiện tại chưa có dự án nào trong hệ thống."

2. Khi liệt kê dự án, hãy liệt kê TẤT CẢ các dự án có trong phần "=== DỰ ÁN ===" ở trên, không được bỏ sót.

3. KHÔNG BAO GIỜ trả lời "0 dự án" hoặc "chưa có dự án nào" nếu phần THỐNG KÊ TỔNG QUAN cho thấy có {so_du_an} dự án (với {so_du_an} > 0).

4. Luôn kiểm tra lại phần THỐNG KÊ TỔNG QUAN (từ Dashboard) trước khi trả lời bất kỳ câu hỏi nào về số lượng.

5. Số lượng dự án từ Dashboard ({so_du_an}) là nguồn dữ liệu chính xác nhất, luôn ưu tiên sử dụng số này.

VÍ DỤ CÁCH TRẢ LỜI ĐÚNG:
- Câu hỏi: "Có bao nhiêu dự án?"
- Trả lời: "Hiện tại có {so_du_an} dự án trong hệ thống. {'Danh sách các dự án:' if so_du_an > 0 else ''}" + (liệt kê tên các dự án từ phần "=== DỰ ÁN ===" nếu có)

Nếu không có thông tin trong dữ liệu trên, hãy nói rõ là bạn không có thông tin đó.
"""
        return prompt
    
    def _list_available_models(self, api_key):
        """Lấy danh sách models available từ Gemini API"""
        try:
            # Thử cả v1beta và v1
            for api_version in ['v1beta', 'v1']:
                try:
                    url = f"https://generativelanguage.googleapis.com/{api_version}/models?key={api_key}"
                    req = urllib.request.Request(url, headers={'Content-Type': 'application/json'})
                    
                    with urllib.request.urlopen(req, timeout=10) as response:
                        result = json.loads(response.read().decode('utf-8'))
                        if 'models' in result:
                            models = [m['name'].split('/')[-1] for m in result['models'] if 'generateContent' in m.get('supportedGenerationMethods', [])]
                            _logger.info(f"Tìm thấy {len(models)} models available từ {api_version}")
                            return models, api_version
                except:
                    continue
        except Exception as e:
            _logger.warning(f"Không thể lấy danh sách models: {str(e)}")
        return None, None
    
    def _call_gemini_api(self, api_key, prompt):
        """Gọi Gemini API - tự động tìm model available"""
        # Danh sách models free tier theo thứ tự ưu tiên (theo documentation mới nhất)
        models_to_try = [
            'gemini-1.5-flash',      # Model free tier chính thức, ổn định nhất
            'gemini-1.5-flash-8b',   # Model nhẹ free tier
            'gemini-2.0-flash',      # Model mới free tier
            'gemini-2.0-flash-lite', # Model lite free tier
        ]
        
        # Thử lấy danh sách models available từ API
        available_models, working_api_version = self._list_available_models(api_key)
        if available_models and len(available_models) > 0:
            # Ưu tiên dùng models có trong danh sách available và trong danh sách mặc định
            priority_models = [m for m in models_to_try if m in available_models]
            other_available = [m for m in available_models if m not in models_to_try and 'flash' in m.lower()]
            # Kết hợp: ưu tiên models trong danh sách mặc định, sau đó là các models khác từ API
            models_to_try = priority_models + other_available
            if working_api_version:
                api_versions = [working_api_version, 'v1beta', 'v1']
            else:
                api_versions = ['v1beta', 'v1']
        else:
            # Nếu không lấy được, dùng danh sách mặc định
            api_versions = ['v1beta', 'v1']
        
        # Đảm bảo có ít nhất một model để thử
        if not models_to_try or len(models_to_try) == 0:
            models_to_try = ['gemini-1.5-flash']  # Fallback về model cơ bản nhất
        
        data = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }]
        }
        
        # Convert data to JSON bytes
        json_data = json.dumps(data).encode('utf-8')
        
        last_error = None
        tried_combinations = []
        
        # Thử từng model với từng API version
        for model_name in models_to_try:
            for api_version in api_versions:
                tried_combinations.append(f"{api_version}/{model_name}")
                try:
                    # Sử dụng Gemini API với model free
                    url = f"https://generativelanguage.googleapis.com/{api_version}/models/{model_name}:generateContent?key={api_key}"
                    
                    # Create request
                    req = urllib.request.Request(url, data=json_data, headers={
                        'Content-Type': 'application/json',
                    })
                    
                    # Make request
                    with urllib.request.urlopen(req, timeout=30) as response:
                        result = json.loads(response.read().decode('utf-8'))
                        
                        if 'candidates' in result and len(result['candidates']) > 0:
                            content = result['candidates'][0]['content']['parts'][0]['text']
                            _logger.info(f"Gemini API thành công với {api_version}/{model_name}")
                            return content
                        else:
                            _logger.warning(f"Gemini API không trả về kết quả với {api_version}/{model_name}")
                            if not last_error:
                                last_error = f"Model {api_version}/{model_name} không trả về kết quả"
                            continue  # Thử API version tiếp theo
                            
                except urllib.error.HTTPError as e:
                    error_body = ""
                    try:
                        if hasattr(e, 'read'):
                            error_body = e.read().decode('utf-8')
                        else:
                            error_body = str(e)
                    except:
                        error_body = str(e)
                    
                    # Nếu là lỗi 404, thử model/version tiếp theo
                    if e.code == 404:
                        _logger.debug(f"Model {api_version}/{model_name} không tồn tại (404), thử tiếp...")
                        if not last_error:
                            last_error = f"Model {api_version}/{model_name} không tồn tại (404)"
                        continue
                    # Nếu là lỗi khác (401, 403), có thể là API key sai, dừng lại
                    elif e.code in [401, 403]:
                        _logger.error(f"Lỗi xác thực với Gemini API (mã {e.code})")
                        return f"Lỗi xác thực với Gemini API (mã {e.code}). Vui lòng kiểm tra API key tại https://aistudio.google.com/app/apikey"
                    else:
                        last_error = f"HTTP {e.code}: {error_body[:200]}"
                        _logger.warning(f"Gemini API HTTP error với {api_version}/{model_name}: {e.code}")
                        continue  # Thử tiếp
                        
                except urllib.error.URLError as e:
                    _logger.warning(f"URL error với {api_version}/{model_name}: {str(e)}")
                    last_error = f"URL Error: {str(e)}"
                    continue  # Thử tiếp
                    
                except Exception as e:
                    _logger.warning(f"Unexpected error với {api_version}/{model_name}: {str(e)}")
                    last_error = f"Error: {str(e)}"
                    continue  # Thử tiếp
        
        # Nếu tất cả đều thất bại
        error_msg = f"Không thể kết nối với Gemini API. Đã thử {len(tried_combinations)} combinations: {', '.join(tried_combinations[:5])}{'...' if len(tried_combinations) > 5 else ''}"
        if last_error:
            error_msg += f" Lỗi cuối: {last_error}"
        error_msg += " Vui lòng kiểm tra API key tại https://aistudio.google.com/app/apikey"
        _logger.error(error_msg)
        return error_msg

