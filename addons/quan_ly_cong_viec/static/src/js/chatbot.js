/** @odoo-module **/

// Prevent duplicate definition using global flag
if (!window._quan_ly_cong_viec_chatbot_defined) {
    window._quan_ly_cong_viec_chatbot_defined = true;
    
    odoo.define('quan_ly_cong_viec.chatbot_widget', function (require) {
        'use strict';

        var core = require('web.core');
        var Widget = require('web.Widget');
        var ajax = require('web.ajax');
        var _t = core._t;

        var ChatbotWidget = Widget.extend({
            events: {
                'click .o_chatbot_button': '_onToggleChat',
                'click .o_chatbot_close': '_onToggleChat',
                'click .o_chatbot_send': '_onSendMessage',
                'keydown .o_chatbot_input': '_onKeyPress',
            },

            init: function (parent) {
                this._super.apply(this, arguments);
                this.isOpen = false;
                this.messages = [{
                    type: 'bot',
                    content: 'Xin chào! Tôi là trợ lý AI hỗ trợ quản lý công việc. Tôi có thể giúp bạn tìm hiểu về các dự án, nhân viên phụ trách, hạn chót và tiến độ. Bạn muốn hỏi gì?'
                }];
                this.isLoading = false;
            },

            start: function () {
                var self = this;
                // Render HTML manually
                this.$el.html(this._renderHTML());
                this.$chatContainer = this.$('.o_chatbot_messages');
                this.$input = this.$('.o_chatbot_input');
                this._renderMessages();
                return this._super.apply(this, arguments);
            },

            _renderHTML: function () {
                return '<div class="o_chatbot_widget">' +
                    '<button class="o_chatbot_button" type="button">' +
                    '<i class="fa fa-comments"/></button>' +
                    '<div class="o_chatbot_window" style="display: none;">' +
                    '<div class="o_chatbot_header">' +
                    '<h3>Trợ lý AI</h3>' +
                    '<button class="o_chatbot_close" type="button">' +
                    '<i class="fa fa-times"/></button>' +
                    '</div>' +
                    '<div class="o_chatbot_messages"></div>' +
                    '<div class="o_chatbot_input_area">' +
                    '<textarea class="o_chatbot_input" placeholder="Nhập câu hỏi của bạn..." rows="1"/>' +
                    '<button class="o_chatbot_send" type="button">' +
                    '<i class="fa fa-paper-plane"/></button>' +
                    '</div>' +
                    '</div>' +
                    '</div>';
            },

            _onToggleChat: function () {
                this.isOpen = !this.isOpen;
                this.$('.o_chatbot_window').toggle(this.isOpen);
                if (this.isOpen) {
                    this._scrollToBottom();
                    this.$input.focus();
                }
            },

            _onKeyPress: function (ev) {
                if (ev.key === 'Enter' && !ev.shiftKey) {
                    ev.preventDefault();
                    this._onSendMessage();
                }
            },

            _onSendMessage: function () {
                var self = this;
                var message = this.$input.val().trim();
                
                if (!message || this.isLoading) {
                    return;
                }

                // Add user message
                this.messages.push({
                    type: 'user',
                    content: message
                });
                
                this.$input.val('');
                this.isLoading = true;
                this._renderMessages();
                this._scrollToBottom();

                // Call backend API
                ajax.jsonRpc('/quan_ly_cong_viec/chatbot/chat', 'call', {
                    message: message
                }).then(function (response) {
                    self.isLoading = false;
                    self.messages.push({
                        type: 'bot',
                        content: response.success ? response.message : ('Lỗi: ' + response.message)
                    });
                    self._renderMessages();
                    self._scrollToBottom();
                }).catch(function (error) {
                    self.isLoading = false;
                    self.messages.push({
                        type: 'bot',
                        content: 'Đã xảy ra lỗi: ' + (error.message || error)
                    });
                    self._renderMessages();
                    self._scrollToBottom();
                });
            },

            _renderMessages: function () {
                var self = this;
                var $messagesContainer = this.$chatContainer;
                $messagesContainer.empty();

                _.each(this.messages, function (msg) {
                    var $message = $('<div>').addClass('o_chatbot_message ' + msg.type);
                    var $content = $('<div>').addClass('o_chatbot_message_content').text(msg.content);
                    $message.append($content);
                    $messagesContainer.append($message);
                });

                if (this.isLoading) {
                    var $loading = $('<div>').addClass('o_chatbot_message bot');
                    var $loadingContent = $('<div>').addClass('o_chatbot_message_content');
                    var $loadingDots = $('<div>').addClass('o_chatbot_loading')
                        .append($('<span>'))
                        .append($('<span>'))
                        .append($('<span>'));
                    $loadingContent.append($loadingDots);
                    $loading.append($loadingContent);
                    $messagesContainer.append($loading);
                }
            },

            _scrollToBottom: function () {
                var self = this;
                setTimeout(function () {
                    if (self.$chatContainer) {
                        self.$chatContainer.scrollTop(self.$chatContainer[0].scrollHeight);
                    }
                }, 100);
            },
        });

        // Auto-initialize chatbot when DOM is ready
        // Only initialize once to avoid duplicate
        if (!window._chatbot_initialized) {
            window._chatbot_initialized = true;
            $(document).ready(function () {
                // Check if chatbot already exists
                if ($('.o_chatbot_widget').length === 0) {
                    var chatbot = new ChatbotWidget();
                    chatbot.appendTo($('body'));
                }
            });
        }

        return ChatbotWidget;
    });
}
