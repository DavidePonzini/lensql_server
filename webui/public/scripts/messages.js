let CHAT_ID = 0;

class Message {
    constructor(content, is_from_assistant, chat, id = null) {
        this.content = content;
        this.is_from_assistant = is_from_assistant;
        this.chat = chat;
        this.msg_id = chat.last_message_id() + 1;
        this.id = id;
        this.feedback = null;

        this.html = $('<div></div>')
            .addClass('messagebox')
            .addClass(is_from_assistant ? 'messagebox-assistant' : 'messagebox-user');
            
        if (is_from_assistant)
            this.html.append(ICON_ASSISTANT);

        let message = $('<div></div>')
            .addClass('message')
            .html(content);
        
        this.html.append(message);
            
        if (!is_from_assistant)
            this.html.append(ICON_USER);

        // if we have an id, it's an ai-generated message
        if (id !== null) {
            this.ask_feedback();
        }
    }

    ask_feedback() {
        let feedback = $('<div></div>')
            .addClass('message-feedback')

        this.feedback_up = $('<span></span>')
            .addClass('feedback feedback-up')
            .attr('data-bs-toggle', 'tooltip')
            .attr('data-bs-placement', 'bottom')
            .attr('data-bs-title', 'Helpful')
            .html('<i class="far fa-thumbs-up"></i>');

            
        this.feedback_down = $('<span></span>')
            .addClass('feedback feedback-down')
            .attr('data-bs-toggle', 'tooltip')
            .attr('data-bs-placement', 'bottom')
            .attr('data-bs-title', 'Not helpful')
            .html('<i class="far fa-thumbs-down"></i>');
            
        new bootstrap.Tooltip(this.feedback_up[0]);
        new bootstrap.Tooltip(this.feedback_down[0]);
        
        feedback.append(this.feedback_up);
        feedback.append(this.feedback_down);

        this.feedback_up.on('click', () => {
            this.send_feedback(true);
        });

        this.feedback_down.on('click', () => {
            this.send_feedback(false);
        });

        $(this.html).find('.message').append(feedback);
    }

    send_feedback(feedback) {
        if (this.feedback !== null)
                return;

        this.feedback_up.addClass('disabled');
        this.feedback_down.addClass('disabled');
        
        let that = this;

        $.ajax({
            url: '/lensql/api/message-feedback',
            type: 'POST',
            data: {
                'msg_id': JSON.stringify(this.id),
                'feedback': JSON.stringify(feedback),
            },
            success: function(response) {
                if (response.success) {

                    that.feedback = true;
                    
                    if (feedback) {
                        that.feedback_up.addClass('selected');
                        that.feedback_up.find('i').removeClass('far').addClass('fas');
                    } else {
                        that.feedback_down.addClass('selected');
                        that.feedback_down.find('i').removeClass('far').addClass('fas');
                    }
                }
                else {
                    console.error('Error: ' + response.error);
                    that.feedback_up.removeClass('disabled');
                    that.feedback_down.removeClass('disabled');
                }
            },
            error: function(error) {
                console.error('Error: ' + error);
                that.feedback_up.removeClass('disabled');
                that.feedback_down.removeClass('disabled');
            }
        });
    }

    set_feedback(feedback) {
        this.feedback = feedback;
    }

    remove() {
        this.html.remove();
    }
}

class Chat {
    constructor(query, query_id, content, notices) {
        CHAT_ID += 1;
        this.id = CHAT_ID;
        this.query = query;
        this.query_id = query_id;
        this.content = content;
        this.messages = [];
        this.notices = notices;

        this.html = $('<div></div>')
            .addClass('chat')
            .addClass('alert')
            .attr('id', `chat-${CHAT_ID}`);

            
        this.add_title();
    }

    last_message_id() {
        if (this.messages.length == 0)
            return 0;
        
        return this.messages[this.messages.length - 1].msg_id;
    }

    show() {
        $('#result').append(this.html);
    }
    
    add_title() {
        let title = $('<div></div>').addClass('chat-title');
        this.html.append(title);
        this.html.append($('<hr></hr>'));

        // Quick fix: added notices here
        if (this.notices && this.notices.length > 0) {
            let ul = $('<ul style="list-style-type: none; padding-left: 0"></ul>');
            this.html.append(ul);
            for (let i = 0; i < this.notices.length; i++) {
                let notice = $('<li class="query-notice"></li>');
                let italic = $('<i></i>')
                italic.text(this.notices[i]);
                notice.append(italic);
                ul.append(notice);
            }

            this.html.append($('<hr></hr>'));
        }

        return title;
    }

    add_message(content, is_from_assistant, id = null) {
        let message = new Message(content, is_from_assistant, this, id);
        this.messages.push(message);
        
        this.html.append(message.html);
        this.html.children().last()[0].scrollIntoView({ behavior: 'smooth', block: 'start' });

        return message;
    }

    display_content_as_table() {
        this.html.append($(this.content));
        return;
        let data = JSON.parse(this.content);
    
        let columns = data['columns'];
        // let row_idx = data['index'];
        let rows = data['data'];
    
        let table = $('<table></table>').addClass('table table-bordered table-hover table-responsive');
        let thead = $('<thead></thead>').addClass('table-dark');
        let header_row = $('<tr></tr>');
        // let header = $('<th></th>').text('#');
        // header_row.append(header);
    
        for (let i = 0; i < columns.length; i++) {
            let th = $('<th></th>').text(columns[i]);
            header_row.append(th);
        }
        thead.append(header_row);
        table.append(thead);
    
        let tbody = $('<tbody></tbody>').addClass('table-group-divider');
        for (let i = 0; i < rows.length; i++) {
            let row = $('<tr></tr>');
            // let index_cell = $('<td></td>').text(row_idx[i]);
            // row.append(index_cell);
    
            for (let j = 0; j < rows[i].length; j++) {
                let text = rows[i][j];
                if (text === null) {
                    text = 'NULL';
                }

                let cell = $('<td></td>').text(text);
                row.append(cell);
            }
            tbody.append(row);
        }
    
        table.append(tbody);
        
        this.html.append(table);
        this.html[0].scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    
    display_content_as_text() {
        let pre = $('<pre></pre>').text(this.content);
        this.html.append(pre);
        this.html[0].scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    show_buttons() {
        // To be implemented in subclasses
    }
}

class UserChat extends Chat {
    constructor(query, query_id, content, notices) {
        super(query, query_id, content, notices);

        this.thiking_message = null;
    }

    add_title() {
        let title = super.add_title();
        let icon = $('<i></i>').addClass('fas fa-user');
        title.append(icon);
        title.append('<b>User query</b>');
        let pre = $('<pre></pre>').text(this.query);
        title.append(pre);

        return title;
    }

    show_buttons() {
        if (this.buttons)
            return;
    
        let buttons = $('<div></div>').addClass('buttons');
        
        this.buttons = buttons;
        let msg = this.messages[this.messages.length - 1];
        $(msg.html).find('.message').append(buttons);
    }

    add_button(text, onclick, disabled = false) {
        if (!this.buttons)
            return;

        let button = $('<button></button>')
            .addClass('btn btn-primary')
            .text(text)
            .on('click', onclick);

        if (disabled)
            button.prop('disabled', true);
        
        this.buttons.append(button);
    }

    remove_buttons() {
        if (!this.buttons)
            return;

        this.buttons.remove();
        this.buttons = null;
    }

    start_thinking() {
        if (this.thiking_message)
            return;

        this.thiking_message = this.add_message('Thinking...', true);
        this.thiking_message.html.addClass('thinking');
    }

    stop_thinking() {
        if (this.thiking_message) {
            this.thiking_message.remove();
            this.thiking_message = null;
        }
    }
}

class ErrorChat extends UserChat {
    constructor(query, query_id, content, notices) {
        super(query, query_id, content, notices);

        this.html.addClass('alert-danger');
    }

    show_buttons() {
        this.add_message('Would you like to ask me something about this error?', true);
        super.show_buttons();

        this.add_button('Explain error', () => {
            let msg = this.add_message('Explain the error', false);
            this.remove_buttons();
            this.start_thinking();
            
            $.ajax({
                url: '/lensql/api/explain-error-message',
                type: 'POST',
                data: {
                    'query_id': JSON.stringify(this.query_id),
                    'exception': JSON.stringify(this.content),
                    'chat_id': JSON.stringify(this.id),
                    'msg_id': JSON.stringify(msg.msg_id),
                },
                success: (response) => {
                    this.stop_thinking();
                    this.add_message(response.answer, true, response.id);
                    this.show_buttons();
                },
                error: (error) => {
                    this.stop_thinking();
                    this.add_message('Error: ' + error, true);
                    this.show_buttons();
                }
            });
        });

        this.add_button('Show example', () => {
            let msg = this.add_message('Show me a simpler example that can cause this error', false);
            this.remove_buttons();
            this.start_thinking();

            $.ajax({
                url: '/lensql/api/provide-error-example',
                type: 'POST',
                data: {
                    'query_id': JSON.stringify(this.query_id),
                    'exception': JSON.stringify(this.content),
                    'chat_id': JSON.stringify(this.id),
                    'msg_id': JSON.stringify(msg.msg_id),
                },
                success: (response) => {
                    this.stop_thinking();
                    this.add_message(response.answer, true, response.id);
                    this.show_buttons();
                },
                error: (error) => {
                    this.stop_thinking();
                    this.add_message('Error: ' + error, true);
                    this.show_buttons();
                }
            });
        }, true);

        this.add_button('Where to look', () => {
            let msg = this.add_message('Locate the error in the code', false);
            this.remove_buttons();
            this.start_thinking();

            $.ajax({
                url: '/lensql/api/locate-error-cause',
                type: 'POST',
                data: {
                    'query_id': JSON.stringify(this.query_id),
                    'exception': JSON.stringify(this.content),
                    'chat_id': JSON.stringify(this.id),
                    'msg_id': JSON.stringify(msg.msg_id),
                },
                success: (response) => {
                    this.stop_thinking();
                    this.add_message(response.answer, true, response.id);
                    this.show_buttons();
                },
                error: (error) => {
                    this.stop_thinking();
                    this.add_message('Error: ' + error, true);
                    this.show_buttons();
                }
            });
        });

        this.add_button('Suggest fix', () => {
            let msg = this.add_message('Suggest a fix for the error', false);
            this.remove_buttons();
            this.start_thinking();

            $.ajax({
                url: '/lensql/api/fix-query',
                type: 'POST',
                data: {
                    'query_id': JSON.stringify(this.query_id),
                    'exception': JSON.stringify(this.content),
                    'chat_id': JSON.stringify(this.id),
                    'msg_id': JSON.stringify(msg.msg_id),
                },
                success: (response) => {
                    this.stop_thinking();
                    this.add_message(response.answer, true, response.id);
                    this.show_buttons();
                },
                error: (error) => {
                    this.stop_thinking();
                    this.add_message('Error: ' + error, true);
                    this.show_buttons();
                }
            });
        });
    }
}

class ResultChat extends UserChat {
    constructor(query, query_id, content, notices) {
        super(query, query_id, content, notices);

        this.html.addClass('alert-primary');
    }

    show_buttons() {
        let msg = this.add_message('Would you like to ask me something about this result?', true);
        super.show_buttons();

        this.add_button('Describe query', () => {
            let msg = this.add_message('Describe what this query does', false);
            this.remove_buttons();
            this.start_thinking();

            $.ajax({
                url: '/lensql/api/describe-my-query',
                type: 'POST',
                data: {
                    'query_id': JSON.stringify(this.query_id),
                    'chat_id': JSON.stringify(this.id),
                    'msg_id': JSON.stringify(msg.msg_id),
                },
                success: (response) => {
                    this.stop_thinking();
                    this.add_message(response.answer, true, response.id);
                    this.show_buttons();
                },
                error: (error) => {
                    this.stop_thinking();
                    this.add_message('Error: ' + error, true);
                    this.show_buttons();
                }
            });
        });

        this.add_button('Explain query', () => {
            let msg = this.add_message('Explain step by step how this query works', false);
            this.remove_buttons();
            this.start_thinking();

            $.ajax({
                url: '/lensql/api/explain-my-query',
                type: 'POST',
                data: {
                    'query_id': JSON.stringify(this.query_id),
                    'chat_id': JSON.stringify(this.id),
                    'msg_id': JSON.stringify(msg.msg_id),
                },
                success: (response) => {
                    this.stop_thinking();
                    this.add_message(response.answer, true, response.id);
                    this.show_buttons();
                },
                error: (error) => {
                    this.stop_thinking();
                    this.add_message('Error: ' + error, true);
                    this.show_buttons();
                }
            });
        });
    }
}

class BuiltinChat extends Chat {
    constructor(query, query_id, content) {
        super(query, query_id, content);

        this.html.addClass('alert-secondary');
    }

    add_title() {
        let title = super.add_title();
        let icon = $('<i></i>').addClass('fas fa-search');
        title.append(icon);
        title.append('<b>LensQL builtin function</b>');
        title.append('<br/>');
        let span = $('<span></span>').text(this.query);
        title.append(span);

        return title;
    }
}

ICON_USER = `
    <div class="icon">
        <i class="fas fa-user"></i>
        <br>
        You 
    </div>
`

ICON_ASSISTANT = `
    <div class="icon">
        <i class="fas fa-search"></i>
        <br>
        LensQL
    </div>
`
