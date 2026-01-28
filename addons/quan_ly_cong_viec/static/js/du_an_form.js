odoo.define('quan_ly_cong_viec.du_an_form', function (require) {
    'use strict';

    var FormController = require('web.FormController');

    FormController.include({
        /**
         * Override để tự động chuyển sang tab Công Việc sau khi tạo dự án mới
         */
        _onButtonClicked: function (event) {
            var self = this;
            var result = this._super.apply(this, arguments);
            
            // Kiểm tra nếu đây là dự án và vừa save
            if (this.modelName === 'du_an') {
                // Đợi form reload xong (nếu là create mới)
                var isNewRecord = !this.handle || this.handle === false;
                if (isNewRecord || event.data.attrs.name === 'save') {
                    setTimeout(function() {
                        // Tìm tab "Công Việc" và click vào
                        var notebook = document.querySelector('#notebook_du_an, .o_notebook');
                        if (notebook) {
                            // Thử nhiều cách tìm tab
                            var selectors = [
                                '.nav-link:contains("Công Việc")',
                                '.nav-item a:contains("Công Việc")',
                                '.o_notebook_headers .nav-item',
                                '[data-tab="Công Việc"]'
                            ];
                            
                            var found = false;
                            var tabs = notebook.querySelectorAll('.nav-link, .nav-item a, .o_notebook_headers .nav-item, [role="tab"]');
                            for (var i = 0; i < tabs.length; i++) {
                                var tabText = (tabs[i].textContent || tabs[i].innerText || '').trim();
                                if (tabText.indexOf('Công Việc') !== -1 || tabText === 'Công Việc') {
                                    tabs[i].click();
                                    found = true;
                                    break;
                                }
                            }
                            
                            // Nếu không tìm thấy, thử cách khác
                            if (!found) {
                                // Tìm bằng data attribute hoặc index
                                var pageElement = document.querySelector('#page_cong_viec');
                                if (pageElement) {
                                    // Tìm tab tương ứng
                                    var tabIndex = Array.from(notebook.querySelectorAll('.nav-item')).findIndex(function(item) {
                                        return item.querySelector('a') && (item.querySelector('a').textContent || '').trim() === 'Công Việc';
                                    });
                                    if (tabIndex !== -1) {
                                        var tabItems = notebook.querySelectorAll('.nav-item');
                                        if (tabItems[tabIndex]) {
                                            var tabLink = tabItems[tabIndex].querySelector('a');
                                            if (tabLink) tabLink.click();
                                        }
                                    }
                                }
                            }
                        }
                    }, 1500);
                }
            }
            
            return result;
        },
    });
});

