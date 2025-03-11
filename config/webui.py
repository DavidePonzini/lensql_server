from enum import Enum
from IPython.display import display, HTML
import ipywidgets as widgets
import llm
import webui_html
from sql_errors import SQLException
from llm import MessageRole

CHAT_ID = 0
MSG_ID = 0

def show_result(code: str, result) -> None:
    display(result)

    chat = Chat()
    chat.code = code
    chat.result = result
    chat.show_expected_output_buttons()

def show_error(code: str, exception: Exception) -> None:
    """Creates a new chat instance for each error."""
    exception = SQLException(exception)
    message = webui_html.exception_to_html(exception)

    chat = Chat()
    chat.code = code
    chat.exception = exception
    chat.show_message(MessageRole.ASSISTANT, message)
    chat.show_error_buttons()


class Buttons(Enum):
    ERROR_EXPLAIN_ERROR = 'Explain error'
    ERROR_IDENTIFY_CAUSE = 'Identify cause'
    ERROR_FIX_HINT = 'How do I fix this?'
    SUCCESS_WRONG_OUTPUT = 'The output is not what I expected'
    MANUAL_PROMPT = 'Other'


class Message:
    def __init__(self, role: MessageRole, content: str):
        global MSG_ID
        MSG_ID += 1
        self.msg_id = MSG_ID
        self.role = role
        self.content = content
        self.html = webui_html.Message(role, content, self.msg_id)


class Chat:
    def __init__(self):
        global CHAT_ID
        CHAT_ID += 1
        self.chat_id = CHAT_ID
        self.messages = []

        self.code = None
        self.exception = None
        self.result = None

        self.output_widget = widgets.Output()  # Capture output in Jupyter cell
        display(self.output_widget)  # Ensure output appears inside the correct cell

        html = webui_html.Chat(self.chat_id)
        self.display_html(html)

    def display_html(self, content: str):
        with self.output_widget:
            display(HTML(str(content)))

    def display_box(self, content: list[widgets.Widget]):
        with self.output_widget:
            display(widgets.HBox(content))

    def show_message(self, role: MessageRole, text: str) -> Message:
        message = Message(role, text)
        self.messages.append(message)

        message_html = str(message.html)
        message_html = message_html.replace('`', '\\`') #.replace('\n', '<br>')

        append_script = f'''
            <script>
                var target = document.getElementById('chat{self.chat_id}');
                target.insertAdjacentHTML('beforeend', `{message_html}`);
                target.scrollTop = target.scrollHeight;
            </script>
        '''

        self.display_html(append_script)
        return message
    
    def delete_message(self, msg_id: int) -> None:
        delete_script = f'''
            <script>
                var target = document.getElementById('msg{msg_id}');
                target.remove();
            </script>
        '''
        self.display_html(delete_script)

    def start_thinking(self) -> Message:
        '''Displays a `Thinking...` message in the chat.'''
        return self.show_message(MessageRole.ASSISTANT, 'Thinking...')

    def show_expected_output_buttons(self):
        options = [
            Buttons.SUCCESS_WRONG_OUTPUT.value,
        ]
        buttons = [widgets.Button(description=option) for option in options]

        buttons[0].layout.margin = '2px 2px 2px 62px'
        for button in buttons[1:]:
            button.layout.margin = '2px 2px 2px 2px'

        # Define the on_click event
        def on_button_click(b):
            button_text = b.description

            for button in buttons:
                button.close()

            self.show_message(MessageRole.USER, button_text)
            self.show_message(MessageRole.ASSISTANT, 'What were you expecting?')

            def provide_help(user_text):
                self.show_message(MessageRole.USER, user_text)
                self.show_message(MessageRole.ASSISTANT, 'I see. Let me help you with that.')
                # self.show_error_buttons()

            self.get_input(provide_help)
        # -- End of on_button_click event --

        # Assign on_click event to each button
        for button in buttons:
            button.on_click(on_button_click)

        self.display_box(buttons)


    def show_error_buttons(self):
        """Creates a set of buttons for the user to choose from."""
        options = [
            Buttons.ERROR_EXPLAIN_ERROR.value,
            Buttons.ERROR_IDENTIFY_CAUSE.value,
            Buttons.ERROR_FIX_HINT.value,
            Buttons.MANUAL_PROMPT.value,
        ]
        buttons = [widgets.Button(description=option) for option in options]
        
        buttons[0].layout.margin = '2px 2px 2px 62px'
        for button in buttons[1:]:
            button.layout.margin = '2px 2px 2px 2px'

        # Define the on_click event
        def on_button_click(b):
            button_text = b.description

            for button in buttons:
                button.close()

            if button_text == Buttons.MANUAL_PROMPT.value:
                self.show_free_input()
                return

            self.show_message(MessageRole.USER, button_text)
            thinking_msg = self.start_thinking()

            if button_text == Buttons.ERROR_EXPLAIN_ERROR.value:
                response = llm.explain_error_message(code=self.code, exception=self.exception)
            elif button_text == Buttons.ERROR_IDENTIFY_CAUSE.value:
                response = llm.identify_error_cause(code=self.code, exception=self.exception)
            else:
                response = 'Action not implemented yet.'

            self.delete_message(thinking_msg.msg_id)
            self.show_message(MessageRole.ASSISTANT, response)
            self.show_error_buttons()

        # -- End of on_button_click event --

        # Assign on_click event to each button
        for button in buttons:
            button.on_click(on_button_click)

        self.display_box(buttons)

    def get_input(self, cb):
        """Creates a text input field for the user to type in."""
        text_input = widgets.Text(placeholder='Type here...', layout=widgets.Layout(width='100%'))
        send_button = widgets.Button(description='Send')

        # Define the on_submit event
        def on_submit(b):
            user_text = text_input.value.strip()
            if user_text:
                cb(user_text)
                text_input.close()
                send_button.close()
        # -- End of on_submit event --

        text_input.on_submit(on_submit)
        send_button.on_click(on_submit)

        self.display_box([text_input, send_button])

    def show_free_input(self):
        """Creates an interactive text input field with a send button."""
        text_input = widgets.Text(placeholder='Type here...', layout=widgets.Layout(width='100%'))
        send_button = widgets.Button(description='Send')
        back_button = widgets.Button(description='Back')

        # Define the on_submit event
        def on_submit(b):
            user_text = text_input.value.strip()
            if user_text:
                self.show_message(MessageRole.USER, user_text)
                text_input.close()
                send_button.close()
                back_button.close()

                tmp = self.start_thinking()

                conversation = [{'role': msg.role, 'content': msg.content} for msg in self.messages]
                response = llm.free_prompt(user_text, self.code, conversation)
                
                self.delete_message(tmp.msg_id)
                self.show_message(MessageRole.ASSISTANT, response)
                self.show_free_input()
        # -- End of on_submit event --

        text_input.on_submit(on_submit)
        send_button.on_click(on_submit)

        def back_to_quick_answers(b):
            text_input.close()
            send_button.close()
            back_button.close()
            self.show_error_buttons()

        back_button.on_click(back_to_quick_answers)

        self.display_box([text_input, send_button, back_button])
