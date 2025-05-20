TMP_CHATS = [];

function display(json_data) {
    clear_result();
    
    let data = JSON.parse(json_data);
    
    for (let i = 0; i < data.length; i++) {
        let item        = data[i];
        let success     = item['success'];
        let builtin     = item['builtin'];
        let type        = item['type'];
        let query       = item['query'];
        let query_id    = item['id'];
        let item_data   = item['data'];
        let notices     = item['notices'];

        let chat;
        if (builtin) {
            chat = new BuiltinChat(query, query_id, item_data, notices);
        } else if (success) {
            chat = new ResultChat(query, query_id, item_data, notices);
        } else {
            chat = new ErrorChat(query, query_id, item_data, notices);
        }

        TMP_CHATS.push(chat);

        if (type === 'message') {
            chat.display_content_as_text();
        } else if (type === 'dataset') {
            chat.display_content_as_table();
        } else {
            console.error(item);
        }

        chat.show_buttons();
        chat.show();
    }
}

function clear_result() {
    let result = $('#result');
    result.empty();
}

